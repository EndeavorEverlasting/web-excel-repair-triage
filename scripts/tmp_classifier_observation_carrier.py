#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def regex_replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, found {count}")
    return updated


# 1) Production feedback runtime: admit bounded prompt_usage events and a privacy-bounded
# Prompt Finder context. Usage remains information-only and never gains mutation authority.
feedback_path = "docs/prompt-kit-feedback-production.js"
feedback = read(feedback_path)
feedback = replace_once(
    feedback,
    "  function latestSequence(events){var latest=0;for(var i=0;i<events.length;i++){var sequence=Number(events[i]&&events[i].sequence);if(Number.isInteger(sequence)&&sequence>latest)latest=sequence}return latest}\n",
    "  function latestSequence(events){var latest=0;for(var i=0;i<events.length;i++){var sequence=Number(events[i]&&events[i].sequence);if(Number.isInteger(sequence)&&sequence>latest)latest=sequence}return latest}\n"
    "  var PROMPT_USAGE_VALUES={open:true,copy:true,invoke:true,favorite:true};\n"
    "  var FINDER_ANSWER_VALUES={startingPoint:['new-repo','in-repo','app-open'],problemKnown:['known-failure','known-task','repeated-stall','not-yet'],goal:['ad-campaign','plan','coordinate','build','ai-level-up','prove','ship','teach','close'],shape:['one-sprint','parallel','sequential','runtime-proof']};\n"
    "  function normalizeUsageContext(value,promptId){if(value==null)return null;if(typeof value!=='object'||Array.isArray(value))throw new Error('INVALID_USAGE_CONTEXT');var allowed={surface:true,measurement:true,session_id:true,answers:true,recommendations:true};Object.keys(value).forEach(function(key){if(!allowed[key])throw new Error('INVALID_USAGE_CONTEXT_FIELD')});if(value.surface!=='prompt_finder'||value.measurement!=='selection_intent')throw new Error('INVALID_USAGE_CONTEXT');var sessionId=String(value.session_id||'').trim();if(!sessionId||sessionId.length>160)throw new Error('INVALID_USAGE_SESSION');var answers=value.answers;if(!answers||typeof answers!=='object'||Array.isArray(answers))throw new Error('INVALID_USAGE_ANSWERS');var answerKeys=Object.keys(FINDER_ANSWER_VALUES);if(Object.keys(answers).length!==answerKeys.length)throw new Error('INVALID_USAGE_ANSWERS');var normalizedAnswers={};answerKeys.forEach(function(key){var answer=String(answers[key]||'').trim();if(FINDER_ANSWER_VALUES[key].indexOf(answer)<0)throw new Error('INVALID_USAGE_ANSWER');normalizedAnswers[key]=answer});var recommendations=value.recommendations;if(!Array.isArray(recommendations)||recommendations.length<1||recommendations.length>3)throw new Error('INVALID_USAGE_RECOMMENDATIONS');var normalizedRecommendations=recommendations.map(function(id){var prompt=String(id||'').trim().toUpperCase();if(!knownPrompt(prompt))throw new Error('UNKNOWN_USAGE_RECOMMENDATION');return prompt});if(normalizedRecommendations.indexOf(promptId)<0)throw new Error('USAGE_PROMPT_NOT_RECOMMENDED');return{surface:'prompt_finder',measurement:'selection_intent',session_id:sessionId,answers:normalizedAnswers,recommendations:normalizedRecommendations}}\n",
    "feedback usage helpers",
)
feedback = regex_replace_once(
    feedback,
    r"  function append\(input\)\{.*?\n  \}\n  function encodeCursor",
    "  function append(input){var promptId=String(input.prompt_id||'').trim().toUpperCase();if(!knownPrompt(promptId))throw new Error('UNKNOWN_PROMPT');var type=input.event_type;if(type!=='prompt_vote'&&type!=='prompt_feedback'&&type!=='prompt_usage')throw new Error('INVALID_EVENT_TYPE');var value=type==='prompt_vote'?String(input.value||'').toLowerCase():(type==='prompt_feedback'?'comment':String(input.value||'').toLowerCase());if(type==='prompt_vote'&&value!=='like'&&value!=='dislike')throw new Error('INVALID_VOTE');if(type==='prompt_usage'&&!PROMPT_USAGE_VALUES[value])throw new Error('INVALID_USAGE');var events=readEvents();var source=sourceId();var previous=null;if(type==='prompt_vote'){for(var i=events.length-1;i>=0;i--){if(events[i].event_type==='prompt_vote'&&events[i].prompt_id===promptId&&events[i].source===source){previous=events[i];break}}}\n"
    "    var event={event_id:eventId(),prompt_id:promptId,event_type:type,value:value,timestamp:new Date().toISOString(),schema_version:EVENT_SCHEMA,source:source,sequence:latestSequence(events)+1};\n"
    "    if(previous)event.supersedes_event_id=previous.event_id;\n"
    "    if(type==='prompt_feedback')event.comment=normalizeComment(input.comment);\n"
    "    if(type==='prompt_usage'&&input.context!=null)event.context=normalizeUsageContext(input.context,promptId);\n"
    "    events.push(event);writeEvents(events);\n"
    "    try{root.dispatchEvent(new root.CustomEvent('prompt-kit-feedback',{detail:event}))}catch(e){}\n"
    "    return event;\n"
    "  }\n  function encodeCursor",
    "feedback append",
)
write(feedback_path, feedback)


# 2) Prompt Finder: attach bounded questionnaire answer IDs + recommendation IDs to
# information-only selection observations. No arbitrary user text is collected.
guided_path = "docs/prompt-kit-guided-recommendations.js"
guided = read(guided_path)
guided = replace_once(
    guided,
    "var S={step:0,answers:{},origin:null};",
    "var S={step:0,answers:{},origin:null,sessionId:null};",
    "guided session state",
)
guided = replace_once(
    guided,
    "function scorePromptFinderAnswers(answers){var scores={},reasons={};Object.keys(answers).forEach(function(questionId){var question=questionById(questionId),option=optionById(question,answers[questionId]);if(!option)return;option.queries.forEach(function(query){sharedSearch(query).slice(0,5).forEach(function(prompt,index){var id=prompt.id;if(id===PROMPT_FINDER_SELF_ID)return;var points=10-(index*2);scores[id]=(scores[id]||0)+Math.max(points,2);(reasons[id]||(reasons[id]=[])).push(option.label)})})});return Object.keys(scores).map(function(id){var prompt=PROMPTS.find(function(p){return p.id===id});return prompt?{prompt:prompt,score:scores[id],reasons:Array.from(new Set(reasons[id]))}:null}).filter(Boolean).sort(function(a,b){return b.score-a.score||rank(a.prompt)-rank(b.prompt)}).slice(0,3)}\n",
    "function scorePromptFinderAnswers(answers){var scores={},reasons={};Object.keys(answers).forEach(function(questionId){var question=questionById(questionId),option=optionById(question,answers[questionId]);if(!option)return;option.queries.forEach(function(query){sharedSearch(query).slice(0,5).forEach(function(prompt,index){var id=prompt.id;if(id===PROMPT_FINDER_SELF_ID)return;var points=10-(index*2);scores[id]=(scores[id]||0)+Math.max(points,2);(reasons[id]||(reasons[id]=[])).push(option.label)})})});return Object.keys(scores).map(function(id){var prompt=PROMPTS.find(function(p){return p.id===id});return prompt?{prompt:prompt,score:scores[id],reasons:Array.from(new Set(reasons[id]))}:null}).filter(Boolean).sort(function(a,b){return b.score-a.score||rank(a.prompt)-rank(b.prompt)}).slice(0,3)}\n"
    "function promptFinderSessionId(){if(window.crypto&&typeof window.crypto.randomUUID==='function')return'finder-'+window.crypto.randomUUID();return'finder-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2)}\n"
    "function recordPromptFinderUsage(promptId,value,results){var api=window.PromptKitFeedback;if(!api||typeof api.append!=='function')return;try{api.append({prompt_id:promptId,event_type:'prompt_usage',value:value,context:{surface:'prompt_finder',measurement:'selection_intent',session_id:S.sessionId,answers:Object.assign({},S.answers),recommendations:results.map(function(item){return item.prompt.id})}})}catch(e){}}\n",
    "guided usage recorder",
)
guided = replace_once(
    guided,
    "el.querySelectorAll('[data-finder-open]').forEach(function(b){b.onclick=function(){showPromptDetail(b.getAttribute('data-finder-open'),S.origin)}});el.querySelectorAll('[data-finder-copy]').forEach(function(b){b.onclick=function(){copyPrompt(b.getAttribute('data-finder-copy'));b.textContent='Copied!';setTimeout(function(){b.textContent='Copy'},1200)}});document.getElementById('finderRestart').onclick=function(){S.step=0;S.answers={};renderPromptFinderQuestion()};",
    "el.querySelectorAll('[data-finder-open]').forEach(function(b){b.onclick=function(){var id=b.getAttribute('data-finder-open');recordPromptFinderUsage(id,'open',results);showPromptDetail(id,S.origin)}});el.querySelectorAll('[data-finder-copy]').forEach(function(b){b.onclick=function(){var id=b.getAttribute('data-finder-copy');recordPromptFinderUsage(id,'copy',results);copyPrompt(id);b.textContent='Copied!';setTimeout(function(){b.textContent='Copy'},1200)}});document.getElementById('finderRestart').onclick=function(){S.step=0;S.answers={};S.sessionId=promptFinderSessionId();renderPromptFinderQuestion()};",
    "guided result instrumentation",
)
guided = replace_once(
    guided,
    "function openPromptFinder(origin){S={step:0,answers:{},origin:origin||document.getElementById('addPromptBtn')};",
    "function openPromptFinder(origin){S={step:0,answers:{},origin:origin||document.getElementById('addPromptBtn'),sessionId:promptFinderSessionId()};",
    "guided session initialization",
)
write(guided_path, guided)


# 3) Feedback hook: validate prompt_usage without making it actionable, project bounded
# statistics, and emit candidate-only Prompt Finder observations for later manual eval curation.
hook_path = "scripts/prompt_kit_feedback_hook.py"
hook = read(hook_path)
hook = replace_once(hook, "import argparse, json, sys\n", "import argparse, hashlib, json, sys\n", "hook hashlib import")
hook = replace_once(
    hook,
    "SENSITIVE_MARKERS=('prompt_body','clipboard','secret','token','password','credential')\n",
    "SENSITIVE_MARKERS=('prompt_body','clipboard','secret','token','password','credential')\n"
    "USAGE_VALUES={'open','copy','invoke','favorite'}\n"
    "FINDER_ANSWER_VALUES={\n"
    "    'startingPoint': {'new-repo','in-repo','app-open'},\n"
    "    'problemKnown': {'known-failure','known-task','repeated-stall','not-yet'},\n"
    "    'goal': {'ad-campaign','plan','coordinate','build','ai-level-up','prove','ship','teach','close'},\n"
    "    'shape': {'one-sprint','parallel','sequential','runtime-proof'},\n"
    "}\n",
    "hook usage constants",
)
validate_block = '''def validate_usage_context(value: object, prompt_id: str, prompt_ids: set[str]) -> dict:
    if not isinstance(value,dict): raise SystemExit('usage context must be an object')
    reject_sensitive_payload(value,'event.context')
    allowed={'surface','measurement','session_id','answers','recommendations'}
    unknown=set(value)-allowed
    if unknown: raise SystemExit(f'unsupported usage context fields: {sorted(unknown)}')
    if value.get('surface')!='prompt_finder' or value.get('measurement')!='selection_intent': raise SystemExit('unsupported usage context')
    session_id=require_text(value.get('session_id'),'context.session_id',160)
    answers=value.get('answers')
    if not isinstance(answers,dict) or set(answers)!=set(FINDER_ANSWER_VALUES): raise SystemExit('invalid prompt finder answers')
    normalized_answers={}
    for key, allowed_values in FINDER_ANSWER_VALUES.items():
        answer=require_text(answers.get(key),f'context.answers.{key}',80)
        if answer not in allowed_values: raise SystemExit(f'invalid prompt finder answer: {key}={answer}')
        normalized_answers[key]=answer
    recommendations=value.get('recommendations')
    if not isinstance(recommendations,list) or not 1<=len(recommendations)<=3: raise SystemExit('invalid prompt finder recommendations')
    normalized_recommendations=[]
    for raw in recommendations:
        recommendation=require_text(raw,'context.recommendations[]',40).upper()
        if recommendation not in prompt_ids: raise SystemExit(f'unknown prompt finder recommendation: {recommendation}')
        normalized_recommendations.append(recommendation)
    if prompt_id not in normalized_recommendations: raise SystemExit('usage prompt must be one of the recorded recommendations')
    return {'surface':'prompt_finder','measurement':'selection_intent','session_id':session_id,'answers':normalized_answers,'recommendations':normalized_recommendations}

'''
hook = replace_once(hook, "def validate_event(event: dict, prompt_ids: set[str]) -> dict:\n", validate_block + "def validate_event(event: dict, prompt_ids: set[str]) -> dict:\n", "hook usage context validator")
hook = regex_replace_once(
    hook,
    r"def validate_event\(event: dict, prompt_ids: set\[str\]\) -> dict:\n.*?\n    return normalized\n\ndef aggregate",
    '''def validate_event(event: dict, prompt_ids: set[str]) -> dict:
    if not isinstance(event,dict): raise SystemExit('feedback event must be an object')
    reject_sensitive_payload(event)
    required={'event_id','prompt_id','event_type','value','timestamp','schema_version','source'}
    if not required.issubset(event): raise SystemExit(f'malformed feedback event: {event.get("event_id","unknown")}')
    normalized=dict(event)
    normalized['event_id']=require_text(event['event_id'],'event_id',160)
    normalized['prompt_id']=require_text(event['prompt_id'],'prompt_id',40).upper()
    if normalized['prompt_id'] not in prompt_ids: raise SystemExit(f'unknown prompt identity: {normalized["prompt_id"]}')
    normalized['source']=require_text(event['source'],'source',120)
    normalized['event_type']=require_text(event['event_type'],'event_type',40)
    normalized['_timestamp']=parse_timestamp(event['timestamp'])
    if event['schema_version']!=EVENT_SCHEMA: raise SystemExit('unsupported feedback event schema')
    if normalized['event_type'] not in {'prompt_vote','prompt_feedback','prompt_usage'}: raise SystemExit('unsupported feedback event type')
    if normalized['event_type']=='prompt_vote':
        if event['value'] not in {'like','dislike'}: raise SystemExit('unsupported vote')
        normalized['value']=event['value']
    elif normalized['event_type']=='prompt_feedback':
        if event['value']!='comment': raise SystemExit('prompt_feedback value must be comment')
        normalized['comment']=require_text(event.get('comment'),'comment',1000)
        normalized['value']='comment'
    else:
        if event['value'] not in USAGE_VALUES: raise SystemExit('unsupported prompt_usage value')
        normalized['value']=event['value']
        if event.get('context') is not None:
            normalized['context']=validate_usage_context(event['context'],normalized['prompt_id'],prompt_ids)
    sequence=event.get('sequence',0)
    if sequence is not None and (not isinstance(sequence,int) or sequence<0): raise SystemExit('sequence must be a non-negative integer')
    normalized['_sequence']=sequence or 0
    supersedes=event.get('supersedes_event_id')
    if supersedes is not None: normalized['supersedes_event_id']=require_text(supersedes,'supersedes_event_id',160)
    return normalized

def aggregate''',
    "hook validate_event",
)
hook = regex_replace_once(
    hook,
    r"def aggregate\(events: list\[dict\], minimum_dislikes: int, prompt_ids: set\[str\] \| None=None\) -> dict:\n.*?\n    return \{'schema_version':REPORT_SCHEMA,'event_count':len\(seen\),'minimum_dislikes':minimum_dislikes,'candidates':\[r for r in rows if r.get\('disposition'\)=='REVIEW_CANDIDATE'\],'summaries':rows,'mutation_authority':False\}\n",
    '''def aggregate(events: list[dict], minimum_dislikes: int, prompt_ids: set[str] | None=None) -> dict:
    prompt_ids=prompt_ids or canonical_prompt_ids()
    seen={}; latest_votes={}; comments=defaultdict(list); usage=defaultdict(lambda: defaultdict(int)); finder_sessions={}; normalized_events=[]
    for raw in events:
        event=validate_event(raw,prompt_ids)
        eid=event['event_id']
        canonical=json.dumps(raw,sort_keys=True,separators=(',',':'))
        if eid in seen:
            if seen[eid]!=canonical: raise SystemExit(f'event id conflict: {eid}')
            continue
        seen[eid]=canonical; normalized_events.append(event)
    normalized_events.sort(key=lambda e:(e['_timestamp'],e['_sequence'],e['event_id']))
    for event in normalized_events:
        pid=event['prompt_id']; source=event['source']
        if event['event_type']=='prompt_vote':
            latest_votes[(pid,source)]=event
        elif event['event_type']=='prompt_feedback':
            comments[pid].append(event)
        else:
            usage[pid][event['value']]+=1
            context=event.get('context')
            if context and context.get('surface')=='prompt_finder':
                key=(source,context['session_id'])
                existing=finder_sessions.get(key)
                snapshot={'answers':context['answers'],'recommendations':context['recommendations']}
                if existing is None:
                    existing={'snapshot':snapshot,'actions':[]}; finder_sessions[key]=existing
                elif existing['snapshot']!=snapshot:
                    raise SystemExit('prompt finder session context changed within one session')
                existing['actions'].append({'prompt_id':pid,'value':event['value']})
    prompt_ids_with_evidence=sorted({pid for pid,_ in latest_votes}|set(comments)|set(usage))
    rows=[]
    for pid in prompt_ids_with_evidence:
        votes=[e for (p,_),e in latest_votes.items() if p==pid]
        row={'prompt_id':pid,'likes':sum(e['value']=='like' for e in votes),'dislikes':sum(e['value']=='dislike' for e in votes),'feedback_count':len(comments[pid]),'usage':dict(sorted(usage[pid].items()))}
        if row['dislikes']>=minimum_dislikes: row['disposition']='REVIEW_CANDIDATE'
        rows.append(row)
    eval_candidates=[]
    for (source,session_id), session in sorted(finder_sessions.items(),key=lambda item:(item[0][0],item[0][1])):
        candidate_id=hashlib.sha256(f'{source}\\0{session_id}'.encode('utf-8')).hexdigest()[:20]
        actions=[]
        for action in session['actions']:
            if action not in actions: actions.append(action)
        eval_candidates.append({
            'candidate_id':candidate_id,
            'surface':'prompt_finder',
            'measurement':'selection_intent',
            'answers':session['snapshot']['answers'],
            'recommendations':session['snapshot']['recommendations'],
            'observed_actions':actions,
            'candidate_only':True,
            'gold_eval_authority':False,
            'promotion_required':'manual_review_into_harness/evals/fixtures/prompt-finder-classifier-cases.v1.json',
        })
    action_counts={value:sum(row.get(value,0) for row in usage.values()) for value in sorted(USAGE_VALUES)}
    return {
        'schema_version':REPORT_SCHEMA,
        'event_count':len(seen),
        'minimum_dislikes':minimum_dislikes,
        'candidates':[r for r in rows if r.get('disposition')=='REVIEW_CANDIDATE'],
        'summaries':rows,
        'usage_stats':{'event_count':sum(action_counts.values()),'action_counts':action_counts,'prompt_finder_candidate_count':len(eval_candidates)},
        'eval_sample_candidates':eval_candidates,
        'mutation_authority':False,
        'gold_eval_authority':False,
    }
''',
    "hook aggregate",
)
write(hook_path, hook)


# 4) Focused regression for runtime privacy, usage stats, and candidate-vs-gold boundary.
test_path = "tests/test_prompt_finder_observation_pipeline.py"
test_text = r'''from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "docs" / "prompt-kit-feedback-production.js"
GUIDED = ROOT / "docs" / "prompt-kit-guided-recommendations.js"
HOOK = ROOT / "scripts" / "prompt_kit_feedback_hook.py"


class PromptFinderObservationPipelineTests(unittest.TestCase):
    def test_runtime_accepts_only_bounded_prompt_finder_usage_context(self) -> None:
        script = r'''global.window=global;const m=new Map();global.localStorage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v)};global.crypto={randomUUID:(()=>{let i=0;return()=>`id-${++i}`})()};global.PROMPTS=[{id:'P07'},{id:'P13'},{id:'P65'}];global.dispatchEvent=()=>{};global.CustomEvent=function(){};const api=require('./docs/prompt-kit-feedback-production.js');const context={surface:'prompt_finder',measurement:'selection_intent',session_id:'finder-test',answers:{startingPoint:'in-repo',problemKnown:'known-task',goal:'build',shape:'one-sprint'},recommendations:['P07','P13']};const event=api.append({prompt_id:'P07',event_type:'prompt_usage',value:'open',context});if(event.event_type!=='prompt_usage'||event.context.answers.goal!=='build'||event.context.recommendations[0]!=='P07')process.exit(2);let rejected=false;try{api.append({prompt_id:'P07',event_type:'prompt_usage',value:'open',context:{...context,raw_query:'secret'}})}catch(e){rejected=String(e.message)==='INVALID_USAGE_CONTEXT_FIELD'}if(!rejected)process.exit(3);console.log(api.exportBundle());'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        bundle = json.loads(result.stdout)
        self.assertEqual(bundle["events"][0]["context"]["measurement"], "selection_intent")
        self.assertNotIn("raw_query", bundle["events"][0]["context"])

    def test_guided_finder_records_selection_intent_without_claiming_gold(self) -> None:
        text = GUIDED.read_text(encoding="utf-8")
        for marker in (
            "recordPromptFinderUsage",
            "event_type:'prompt_usage'",
            "measurement:'selection_intent'",
            "recommendations:results.map",
            "recordPromptFinderUsage(id,'open',results);showPromptDetail",
            "recordPromptFinderUsage(id,'copy',results);copyPrompt",
        ):
            self.assertIn(marker, text)
        self.assertNotIn("raw_query", text)
        self.assertNotIn("question_text", text)

    def test_hook_projects_usage_stats_and_candidate_only_eval_samples(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inbox = root / "inbox"
            inbox.mkdir()
            out = root / "report.json"
            context = {
                "surface": "prompt_finder",
                "measurement": "selection_intent",
                "session_id": "finder-session-1",
                "answers": {
                    "startingPoint": "in-repo",
                    "problemKnown": "known-task",
                    "goal": "build",
                    "shape": "one-sprint",
                },
                "recommendations": ["P07", "P13"],
            }
            events = [
                {"event_id":"usage-open","prompt_id":"P07","event_type":"prompt_usage","value":"open","timestamp":"2026-09-12T04:00:00Z","schema_version":"prompt-feedback-event/v1","source":"browser-a","context":context},
                {"event_id":"usage-copy","prompt_id":"P13","event_type":"prompt_usage","value":"copy","timestamp":"2026-09-12T04:00:01Z","schema_version":"prompt-feedback-event/v1","source":"browser-a","context":context},
                {"event_id":"dislike","prompt_id":"P07","event_type":"prompt_vote","value":"dislike","timestamp":"2026-09-12T04:00:02Z","schema_version":"prompt-feedback-event/v1","source":"browser-a"},
            ]
            (inbox / "batch.json").write_text(json.dumps({"schema_version":"prompt-feedback-export/v1","events":events}), encoding="utf-8")
            result = subprocess.run(["python", str(HOOK), "--input", str(inbox), "--output", str(out), "--minimum-dislikes", "1"], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertFalse(report["mutation_authority"])
            self.assertFalse(report["gold_eval_authority"])
            self.assertEqual(report["usage_stats"]["event_count"], 2)
            self.assertEqual(report["usage_stats"]["action_counts"]["open"], 1)
            self.assertEqual(report["usage_stats"]["action_counts"]["copy"], 1)
            self.assertEqual(report["usage_stats"]["prompt_finder_candidate_count"], 1)
            candidate = report["eval_sample_candidates"][0]
            self.assertTrue(candidate["candidate_only"])
            self.assertFalse(candidate["gold_eval_authority"])
            self.assertEqual(candidate["answers"]["goal"], "build")
            self.assertEqual(candidate["recommendations"], ["P07", "P13"])
            self.assertNotIn("source", candidate)
            self.assertNotIn("session_id", candidate)
            self.assertIn("manual_review_into_harness/evals/fixtures/prompt-finder-classifier-cases.v1.json", candidate["promotion_required"])
            self.assertEqual(report["candidates"][0]["disposition"], "REVIEW_CANDIDATE")

    def test_hook_rejects_unbounded_or_changed_classifier_context(self) -> None:
        base = {
            "surface": "prompt_finder",
            "measurement": "selection_intent",
            "session_id": "finder-session-1",
            "answers": {"startingPoint":"in-repo","problemKnown":"known-task","goal":"build","shape":"one-sprint"},
            "recommendations": ["P07", "P13"],
        }
        cases = [
            {**base, "raw_query": "do not persist me"},
            {**base, "answers": {**base["answers"], "goal": "made-up-goal"}},
            {**base, "recommendations": ["P404"]},
        ]
        for context in cases:
            with self.subTest(context=context), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                inbox = root / "inbox"
                inbox.mkdir()
                out = root / "report.json"
                event = {"event_id":"usage","prompt_id":"P07","event_type":"prompt_usage","value":"open","timestamp":"2026-09-12T04:00:00Z","schema_version":"prompt-feedback-event/v1","source":"browser-a","context":context}
                (inbox / "batch.json").write_text(json.dumps({"schema_version":"prompt-feedback-export/v1","events":[event]}), encoding="utf-8")
                result = subprocess.run(["python", str(HOOK), "--input", str(inbox), "--output", str(out)], cwd=ROOT, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0, result.stderr or result.stdout)
                self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
'''
write(test_path, test_text)


# 5) Documentation: preserve the intended learning loop without contaminating gold evals.
design_path = "docs/PROMPT_KIT_FEEDBACK_POLLING_DESIGN.md"
design = read(design_path)
appendix = '''\n\n## Production Prompt Finder observation candidates\n\nThe production feedback runtime also accepts `prompt_usage` as an **information-only** event class. Prompt Finder result selections may attach a bounded `context` containing only:\n\n- `surface=prompt_finder`;\n- `measurement=selection_intent`;\n- an opaque local `session_id`;\n- the four questionnaire **option IDs** (`startingPoint`, `problemKnown`, `goal`, `shape`);\n- up to three canonical recommended prompt IDs.\n\nThe browser does **not** persist arbitrary finder query text, question text, prompt bodies, clipboard contents, credentials, or a general-purpose metadata bag for this path. Invalid option IDs, unknown recommendations, extra context fields, or a selected prompt outside the recorded recommendation set fail closed.\n\nThe maintenance hook projects two distinct products from the same append-only export:\n\n1. **statistics** — information-only action counts by prompt/action; and\n2. **`eval_sample_candidates`** — privacy-bounded Prompt Finder answer/recommendation/action observations.\n\n`eval_sample_candidates` are deliberately **not gold eval cases**. They carry `candidate_only=true`, `gold_eval_authority=false`, omit raw browser/source/session identity, and require manual review before any case may be promoted into `harness/evals/fixtures/prompt-finder-classifier-cases.v1.json`. This prevents popularity or one user's behavior from silently redefining classifier correctness. Dedicated eval sprints retain ownership of labels, expected routes, adversarial cases, scoring policy, and regression gates.\n\nThe first production measurement is **selection intent** (`open` / `copy` selected from a recommendation card), not proof that the downstream prompt succeeded or that clipboard completion occurred. A later semantic-completion sprint may strengthen the usage ledger once the production command kernel exposes truthful terminal outcomes; until then, stats and eval mining must preserve this proof ceiling.\n'''
if "## Production Prompt Finder observation candidates" not in design:
    design = design.rstrip() + appendix + "\n"
write(design_path, design)


# 6) Feedback workflow must rerun when either the producer or focused regression changes.
workflow_path = ".github/workflows/prompt-kit-feedback-hook.yml"
workflow = read(workflow_path)
workflow = replace_once(
    workflow,
    "      - docs/prompt-kit-feedback-production.js\n",
    "      - docs/prompt-kit-feedback-production.js\n      - docs/prompt-kit-guided-recommendations.js\n",
    "feedback workflow guided path",
)
workflow = replace_once(
    workflow,
    "      - tests/test_prompt_kit_feedback_production.py\n",
    "      - tests/test_prompt_kit_feedback_production.py\n      - tests/test_prompt_finder_observation_pipeline.py\n",
    "feedback workflow observation test path",
)
workflow = replace_once(
    workflow,
    "          python -m unittest tests.test_prompt_kit_feedback_production tests.test_operant_friction_repository_dispatch_adapter tests.test_operant_upgrade -v\n",
    "          python -m unittest tests.test_prompt_kit_feedback_production tests.test_prompt_finder_observation_pipeline tests.test_operant_friction_repository_dispatch_adapter tests.test_operant_upgrade -v\n",
    "feedback workflow observation test command",
)
write(workflow_path, workflow)


# 7) Run bounded proof and regenerate only through the canonical builder.
commands = [
    ["node", "--check", "docs/prompt-kit-feedback-production.js"],
    ["node", "--check", "docs/prompt-kit-guided-recommendations.js"],
    ["python", "-m", "unittest", "tests.test_prompt_kit_feedback_production", "tests.test_prompt_finder_observation_pipeline", "-v"],
    ["python", "scripts/prompt_kit_classifier_eval.py", "--output", "Outputs/prompt-finder-classifier-eval.json"],
    ["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html"],
    ["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"],
    ["python", "scripts/prompt_registry_ops.py", "validate"],
    ["python", "scripts/validate_prompt_kit_discovery.py", "--summary"],
    ["git", "diff", "--check"],
]
for command in commands:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)

# Existing classifier gate must remain exactly green after instrumentation.
report_path = ROOT / "Outputs" / "prompt-finder-classifier-eval.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
metrics = report.get("metrics", {})
if metrics.get("case_accuracy") != 1 or metrics.get("primary_route_accuracy") != 1 or metrics.get("recall_at_3") != 1 or metrics.get("determinism") != 1:
    raise SystemExit(f"classifier regression after observation instrumentation: {metrics}")
report_path.unlink(missing_ok=True)

# Temporary execution carrier self-removes; the workflow commits only durable surfaces.
(ROOT / "scripts" / "tmp_classifier_observation_carrier.py").unlink(missing_ok=True)
(ROOT / ".github" / "workflows" / "tmp-classifier-observation-carrier.yml").unlink(missing_ok=True)

print(json.dumps({
    "status": "PASS",
    "classifier_metrics": metrics,
    "durable_files": [
        feedback_path,
        guided_path,
        hook_path,
        test_path,
        design_path,
        workflow_path,
        "web/prompt-kit/index.html",
    ],
    "proof_ceiling": "selection-intent observations and candidate eval mining; not terminal prompt success or gold-label authority",
}, sort_keys=True))
