from __future__ import annotations

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
        script = r'''global.window=global;const m=new Map();global.localStorage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k),key:i=>Array.from(m.keys())[i]??null,get length(){return m.size}};global.crypto={randomUUID:(()=>{let i=0;return()=>`id-${++i}`})()};global.PROMPTS=[{id:'P07'},{id:'P13'},{id:'P65'}];global.dispatchEvent=()=>{};global.CustomEvent=function(){};const api=require('./docs/prompt-kit-feedback-production.js');const context={surface:'prompt_finder',measurement:'selection_intent',session_id:'finder-test',answers:{startingPoint:'in-repo',problemKnown:'known-task',goal:'build',shape:'one-sprint'},recommendations:['P07','P13']};const event=api.append({prompt_id:'P07',event_type:'prompt_usage',value:'open',context});if(event.event_type!=='prompt_usage'||event.context.answers.goal!=='build'||event.context.recommendations[0]!=='P07')process.exit(2);let rejected=false;try{api.append({prompt_id:'P07',event_type:'prompt_usage',value:'open',context:{...context,raw_query:'secret'}})}catch(e){rejected=String(e.message)==='INVALID_USAGE_CONTEXT_FIELD'}if(!rejected)process.exit(3);console.log(api.exportBundle());'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        bundle = json.loads(result.stdout)
        self.assertEqual(bundle["events"][0]["context"]["measurement"], "selection_intent")
        self.assertNotIn("raw_query", bundle["events"][0]["context"])

    def test_usage_ledger_is_cross_tab_safe_bounded_and_cursor_independent(self) -> None:
        script = r'''const fs=require('fs'),vm=require('vm');const code=fs.readFileSync('./docs/prompt-kit-feedback-production.js','utf8');const m=new Map();const storage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k),key:i=>Array.from(m.keys())[i]??null,get length(){return m.size}};function tab(prefix){let i=0;const c={localStorage:storage,crypto:{randomUUID:()=>`${prefix}-${++i}`},PROMPTS:[{id:'P07'}],dispatchEvent:()=>{},CustomEvent:function(){}};c.window=c;c.globalThis=c;vm.createContext(c);vm.runInContext(code,c);return c}const a=tab('a'),b=tab('b');const context={surface:'prompt_finder',measurement:'selection_intent',session_id:'finder-tabs',answers:{startingPoint:'in-repo',problemKnown:'known-task',goal:'build',shape:'one-sprint'},recommendations:['P07']};a.PromptKitFeedback.append({prompt_id:'P07',event_type:'prompt_usage',value:'open',context});b.PromptKitFeedback.append({prompt_id:'P07',event_type:'prompt_usage',value:'copy',context});let usageKeys=Array.from(m.keys()).filter(k=>k.startsWith('promptKit.feedbackUsage.v1.'));if(usageKeys.length!==2)process.exit(2);let bundle=JSON.parse(a.PromptKitFeedback.exportBundle());if(bundle.events.length!==2||new Set(bundle.events.map(e=>e.event_id)).size!==2)process.exit(3);if(a.PromptKitFeedback.pollSince('prompt-feedback-cursor/v1:0',10).events.length!==0)process.exit(4);for(let i=0;i<600;i++){const api=i%2?a.PromptKitFeedback:b.PromptKitFeedback;api.append({prompt_id:'P07',event_type:'prompt_usage',value:i%2?'open':'copy',context})}usageKeys=Array.from(m.keys()).filter(k=>k.startsWith('promptKit.feedbackUsage.v1.'));bundle=JSON.parse(a.PromptKitFeedback.exportBundle());if(usageKeys.length!==a.PromptKitFeedback.MAX_USAGE_EVENTS||bundle.events.length!==a.PromptKitFeedback.MAX_USAGE_EVENTS)process.exit(5);if(a.PromptKitFeedback.pollSince('prompt-feedback-cursor/v1:0',10).events.length!==0)process.exit(6);console.log(JSON.stringify({usage_keys:usageKeys.length,exported:bundle.events.length,poll_events:0}));'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["usage_keys"], 500)
        self.assertEqual(report["exported"], 500)
        self.assertEqual(report["poll_events"], 0)

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
