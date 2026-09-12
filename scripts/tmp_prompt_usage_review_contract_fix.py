#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


runtime_path = "docs/prompt-kit-feedback-production.js"
runtime = read(runtime_path)
runtime = replace_once(
    runtime,
    "if(type==='prompt_usage'){var usageEvent={event_id:eventId(),prompt_id:promptId,event_type:type,value:value,timestamp:new Date().toISOString(),schema_version:EVENT_SCHEMA,source:source};if(input.context!=null)usageEvent.context=normalizeUsageContext(input.context,promptId);writeUsageEvent(usageEvent);",
    "if(type==='prompt_usage'){var usageEvent={event_id:eventId(),prompt_id:promptId,event_type:type,value:value,timestamp:new Date().toISOString(),schema_version:EVENT_SCHEMA,source:source};if(input.context!=null){if(value!=='open'&&value!=='copy')throw new Error('INVALID_USAGE_CONTEXT_ACTION');usageEvent.context=normalizeUsageContext(input.context,promptId)}writeUsageEvent(usageEvent);",
    "runtime contextual usage action gate",
)
write(runtime_path, runtime)

hook_path = "scripts/prompt_kit_feedback_hook.py"
hook = read(hook_path)
hook = replace_once(
    hook,
    "USAGE_VALUES={'open','copy','invoke','favorite'}\n",
    "USAGE_VALUES={'open','copy','invoke','favorite'}\nUSAGE_EVENT_FIELDS={'event_id','prompt_id','event_type','value','timestamp','schema_version','source','context','sequence'}\n",
    "hook usage event allowlist constant",
)
old_validate = '''def validate_event(event: dict, prompt_ids: set[str]) -> dict:
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
'''
new_validate = '''def validate_event(event: dict, prompt_ids: set[str]) -> dict:
    if not isinstance(event,dict): raise SystemExit('feedback event must be an object')
    reject_sensitive_payload(event)
    required={'event_id','prompt_id','event_type','value','timestamp','schema_version','source'}
    if not required.issubset(event): raise SystemExit(f'malformed feedback event: {event.get("event_id","unknown")}')
    event_type=require_text(event['event_type'],'event_type',40)
    if event_type not in {'prompt_vote','prompt_feedback','prompt_usage'}: raise SystemExit('unsupported feedback event type')
    if event_type=='prompt_usage':
        unknown=set(event)-USAGE_EVENT_FIELDS
        if unknown: raise SystemExit(f'unsupported prompt_usage fields: {sorted(unknown)}')
    normalized=dict(event)
    normalized['event_id']=require_text(event['event_id'],'event_id',160)
    normalized['prompt_id']=require_text(event['prompt_id'],'prompt_id',40).upper()
    if normalized['prompt_id'] not in prompt_ids: raise SystemExit(f'unknown prompt identity: {normalized["prompt_id"]}')
    normalized['source']=require_text(event['source'],'source',120)
    normalized['event_type']=event_type
    normalized['_timestamp']=parse_timestamp(event['timestamp'])
    if event['schema_version']!=EVENT_SCHEMA: raise SystemExit('unsupported feedback event schema')
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
            if event['value'] not in {'open','copy'}: raise SystemExit('prompt finder selection intent must be open or copy')
            normalized['context']=validate_usage_context(event['context'],normalized['prompt_id'],prompt_ids)
    sequence=event.get('sequence',0)
    if sequence is not None and (not isinstance(sequence,int) or sequence<0): raise SystemExit('sequence must be a non-negative integer')
    normalized['_sequence']=sequence or 0
    supersedes=event.get('supersedes_event_id')
    if supersedes is not None: normalized['supersedes_event_id']=require_text(supersedes,'supersedes_event_id',160)
    return normalized
'''
hook = replace_once(hook, old_validate, new_validate, "hook prompt_usage validation")
write(hook_path, hook)

test_path = "tests/test_prompt_finder_observation_pipeline.py"
test = read(test_path)
anchor = '''    def test_guided_finder_records_selection_intent_without_claiming_gold(self) -> None:
'''
new_tests = '''    def test_contextual_usage_is_limited_to_finder_selection_actions(self) -> None:
        script = r'''global.window=global;const m=new Map();global.localStorage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k),key:i=>Array.from(m.keys())[i]??null,get length(){return m.size}};global.crypto={randomUUID:(()=>{let i=0;return()=>`id-${++i}`})()};global.PROMPTS=[{id:'P07'}];global.dispatchEvent=()=>{};global.CustomEvent=function(){};const api=require('./docs/prompt-kit-feedback-production.js');const context={surface:'prompt_finder',measurement:'selection_intent',session_id:'finder-actions',answers:{startingPoint:'in-repo',problemKnown:'known-task',goal:'build',shape:'one-sprint'},recommendations:['P07']};for(const value of ['invoke','favorite']){let rejected=false;try{api.append({prompt_id:'P07',event_type:'prompt_usage',value,context})}catch(e){rejected=String(e.message)==='INVALID_USAGE_CONTEXT_ACTION'}if(!rejected)process.exit(2)}for(const value of ['invoke','favorite'])api.append({prompt_id:'P07',event_type:'prompt_usage',value});const events=api.readUsageEvents();if(events.length!==2||events.some(e=>e.context))process.exit(3);console.log(JSON.stringify(events.map(e=>e.value).sort()));'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout), ["favorite", "invoke"])

    def test_hook_rejects_unknown_usage_fields_and_contextual_non_selection_actions(self) -> None:
        base_context = {
            "surface": "prompt_finder",
            "measurement": "selection_intent",
            "session_id": "finder-review",
            "answers": {"startingPoint":"in-repo","problemKnown":"known-task","goal":"build","shape":"one-sprint"},
            "recommendations": ["P07"],
        }
        base_event = {
            "event_id":"usage-review",
            "prompt_id":"P07",
            "event_type":"prompt_usage",
            "value":"open",
            "timestamp":"2026-09-12T04:55:00Z",
            "schema_version":"prompt-feedback-event/v1",
            "source":"browser-review",
        }
        invalid = [
            {**base_event, "raw_query":"private query"},
            {**base_event, "unexpected":"field"},
            {**base_event, "value":"invoke", "context":base_context},
            {**base_event, "value":"favorite", "context":base_context},
        ]
        for event in invalid:
            with self.subTest(event=event), tempfile.TemporaryDirectory() as td:
                root = Path(td); inbox = root / "inbox"; inbox.mkdir(); out = root / "report.json"
                (inbox / "batch.json").write_text(json.dumps({"schema_version":"prompt-feedback-export/v1","events":[event]}), encoding="utf-8")
                result = subprocess.run(["python", str(HOOK), "--input", str(inbox), "--output", str(out)], cwd=ROOT, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0, result.stderr or result.stdout)
                self.assertFalse(out.exists())
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); inbox = root / "inbox"; inbox.mkdir(); out = root / "report.json"
            valid = [{**base_event, "event_id":"invoke-ok", "value":"invoke"}, {**base_event, "event_id":"favorite-ok", "value":"favorite"}]
            (inbox / "batch.json").write_text(json.dumps({"schema_version":"prompt-feedback-export/v1","events":valid}), encoding="utf-8")
            result = subprocess.run(["python", str(HOOK), "--input", str(inbox), "--output", str(out)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["usage_stats"]["action_counts"]["invoke"], 1)
            self.assertEqual(report["usage_stats"]["action_counts"]["favorite"], 1)
            self.assertEqual(report["usage_stats"]["prompt_finder_candidate_count"], 0)

'''
test = replace_once(test, anchor, new_tests + anchor, "review contract regression tests")
write(test_path, test)

design_path = "docs/PROMPT_KIT_FEEDBACK_POLLING_DESIGN.md"
design = read(design_path)
needle = "The first production measurement is **selection intent** (`open` / `copy` selected from a recommendation card), not proof that the downstream prompt succeeded or that clipboard completion occurred."
replacement = "Only `open` and `copy` may carry Prompt Finder `selection_intent` context. Generic `invoke` and `favorite` usage remain valid information-only events only when context-free; they cannot enter the candidate-eval path. Prompt-usage ingest also enforces an explicit top-level field allow-list, so undeclared fields fail closed before normalization.\n\n" + needle
design = replace_once(design, needle, replacement, "selection-intent review boundary")
write(design_path, design)

commands = [
    ["node", "--check", runtime_path],
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

report_path = ROOT / "Outputs" / "prompt-finder-classifier-eval.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
metrics = report.get("metrics", {})
if report.get("verdict") != "pass" or metrics.get("case_pass_rate") != 1 or metrics.get("primary_accuracy") != 1 or metrics.get("required_recall_at_3") != 1 or metrics.get("deterministic_cases") != metrics.get("case_count"):
    raise SystemExit(f"classifier regression after review contract fix: {metrics}")
report_path.unlink(missing_ok=True)

print(json.dumps({"status":"PASS","classifier_metrics":metrics,"usage_context_actions":["open","copy"],"unknown_usage_fields":"fail-closed"}, sort_keys=True))
