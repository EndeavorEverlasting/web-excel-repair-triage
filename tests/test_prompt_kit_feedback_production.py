from __future__ import annotations
import json, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'docs/prompt-kit-feedback-production.js'
HOOK=ROOT/'scripts/prompt_kit_feedback_hook.py'

class PromptKitFeedbackProductionTests(unittest.TestCase):
    def test_runtime_contract_and_ui_are_present(self):
        text=RUNTIME.read_text(encoding='utf-8')
        for marker in ('promptKit.feedbackEvents.v1','promptKit.feedbackSource.v1','prompt-feedback-event/v1','prompt-feedback-cursor/v1','data-prompt-kit-feedback-ui','👍 Like','👎 Dislike','Copy feedback export','localStorage','supersedes_event_id','STALE_CURSOR','latestSequence','FEEDBACK_STORAGE_FULL'):
            self.assertIn(marker,text)
        self.assertNotIn('slice(-MAX_EVENTS)',text)
        self.assertNotIn('fetch(',text)
        self.assertNotIn('Authorization',text)
    def test_runtime_executes_with_browser_storage_shim(self):
        script=r'''global.window=global;const m=new Map();global.localStorage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v)};global.crypto={randomUUID:(()=>{let i=0;return()=>`id-${++i}`})()};global.PROMPTS=[{id:'P99'}];global.dispatchEvent=()=>{};global.CustomEvent=function(){};const api=require('./docs/prompt-kit-feedback-production.js');api.append({prompt_id:'P99',event_type:'prompt_vote',value:'like'});api.append({prompt_id:'P99',event_type:'prompt_vote',value:'dislike'});api.append({prompt_id:'P99',event_type:'prompt_feedback',comment:'too long'});const page=api.pollSince('prompt-feedback-cursor/v1:0',10);if(page.events.length!==3||page.events[1].supersedes_event_id!==page.events[0].event_id||api.currentVote('P99')!=='dislike')process.exit(2);console.log(JSON.stringify(page));'''
        r=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr or r.stdout)
        self.assertEqual(len(json.loads(r.stdout)['events']),3)
    def test_large_log_remains_append_only_and_sequences_stay_absolute(self):
        script=r'''global.window=global;const m=new Map();global.localStorage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v)};global.crypto={randomUUID:()=>`id-new`};global.PROMPTS=[{id:'P99'}];global.dispatchEvent=()=>{};global.CustomEvent=function(){};const rows=[];for(let seq=1;seq<=2100;seq++){rows.push({event_id:`old-${seq}`,prompt_id:'P99',event_type:'prompt_feedback',value:'comment',comment:'x',timestamp:'2026-08-25T00:00:00.000Z',schema_version:'prompt-feedback-event/v1',source:'seed',sequence:seq})}m.set('promptKit.feedbackEvents.v1',JSON.stringify(rows));const api=require('./docs/prompt-kit-feedback-production.js');const e=api.append({prompt_id:'P99',event_type:'prompt_feedback',comment:'new'});const all=api.readEvents();if(e.sequence!==2101||all.length!==2101||all[0].event_id!=='old-1')process.exit(2);const page=api.pollSince('prompt-feedback-cursor/v1:2100',10);if(page.events.length!==1||page.events[0].sequence!==2101)process.exit(3);console.log(JSON.stringify({sequence:e.sequence,count:all.length}));'''
        r=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr or r.stdout)
        report=json.loads(r.stdout); self.assertEqual(report['sequence'],2101); self.assertEqual(report['count'],2101)
    def test_scheduled_hook_aggregates_without_mutation_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inbox=root/'inbox'; inbox.mkdir(); out=root/'report.json'
            payload={'schema_version':'prompt-feedback-export/v1','events':[
                {'event_id':'1','prompt_id':'P99','event_type':'prompt_vote','value':'dislike','timestamp':'2026-08-25T00:00:00Z','schema_version':'prompt-feedback-event/v1','source':'a'},
                {'event_id':'2','prompt_id':'P99','event_type':'prompt_vote','value':'dislike','timestamp':'2026-08-25T00:00:01Z','schema_version':'prompt-feedback-event/v1','source':'b'}]}
            (inbox/'batch.json').write_text(json.dumps(payload),encoding='utf-8')
            r=subprocess.run(['python',str(HOOK),'--input',str(inbox),'--output',str(out)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr or r.stdout)
            report=json.loads(out.read_text())
            self.assertFalse(report['mutation_authority']); self.assertEqual(report['candidates'][0]['disposition'],'REVIEW_CANDIDATE')
    def test_hook_uses_event_chronology_not_batch_order_for_vote_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inbox=root/'inbox'; inbox.mkdir(); out=root/'report.json'
            newer={'event_id':'new','prompt_id':'P99','event_type':'prompt_vote','value':'dislike','timestamp':'2026-08-25T12:00:02Z','schema_version':'prompt-feedback-event/v1','source':'a','sequence':2,'supersedes_event_id':'old'}
            older={'event_id':'old','prompt_id':'P99','event_type':'prompt_vote','value':'like','timestamp':'2026-08-25T12:00:01Z','schema_version':'prompt-feedback-event/v1','source':'a','sequence':1}
            (inbox/'batch.json').write_text(json.dumps({'schema_version':'prompt-feedback-export/v1','events':[newer,older]}),encoding='utf-8')
            r=subprocess.run(['python',str(HOOK),'--input',str(inbox),'--output',str(out)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr or r.stdout)
            row=json.loads(out.read_text())['summaries'][0]; self.assertEqual(row['likes'],0); self.assertEqual(row['dislikes'],1)
    def test_hook_rejects_malformed_and_nested_sensitive_feedback(self):
        cases=[
            [None],
            [{'event_id':'x','prompt_id':'P99','event_type':'prompt_feedback','value':'comment','comment':'','timestamp':'2026-08-25T12:00:00Z','schema_version':'prompt-feedback-event/v1','source':'a'}],
            [{'event_id':'x','prompt_id':'P99','event_type':'prompt_feedback','value':'comment','comment':'ok','timestamp':'not-a-time','schema_version':'prompt-feedback-event/v1','source':'a'}],
            [{'event_id':'x','prompt_id':'P99','event_type':'prompt_feedback','value':'comment','comment':'ok','timestamp':'2026-08-25T12:00:00Z','schema_version':'prompt-feedback-event/v1','source':'a','metadata':{'credential':'nope'}}],
        ]
        for events in cases:
            with self.subTest(events=events), tempfile.TemporaryDirectory() as td:
                root=Path(td); inbox=root/'inbox'; inbox.mkdir(); out=root/'report.json'
                (inbox/'batch.json').write_text(json.dumps({'schema_version':'prompt-feedback-export/v1','events':events}),encoding='utf-8')
                r=subprocess.run(['python',str(HOOK),'--input',str(inbox),'--output',str(out)],cwd=ROOT,text=True,capture_output=True)
                self.assertNotEqual(r.returncode,0,r.stderr or r.stdout)
                self.assertFalse(out.exists())

if __name__=='__main__': unittest.main()
