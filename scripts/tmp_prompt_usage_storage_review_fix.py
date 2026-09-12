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
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, found {count}")
    return updated


# Runtime: keep the existing append-only feedback/vote cursor log intact, but move the
# newly-added Prompt Finder usage observations into their own bounded event-per-key
# ledger. Independent event keys remove whole-array lost-update races across tabs;
# usage is export/candidate input and deliberately does not participate in pollSince.
runtime_path = "docs/prompt-kit-feedback-production.js"
runtime = read(runtime_path)
runtime = replace_once(
    runtime,
    "  var SOURCE_KEY='promptKit.feedbackSource.v1';\n",
    "  var SOURCE_KEY='promptKit.feedbackSource.v1';\n"
    "  var USAGE_STORAGE_PREFIX='promptKit.feedbackUsage.v1.';\n"
    "  var MAX_USAGE_EVENTS=500;\n",
    "usage storage constants",
)
runtime = replace_once(
    runtime,
    "  function writeEvents(events){var storage=safeStorage();if(!storage)throw new Error('FEEDBACK_PERSISTENCE_UNAVAILABLE');try{storage.setItem(STORAGE_KEY,JSON.stringify(events))}catch(e){throw new Error('FEEDBACK_STORAGE_FULL')}}\n",
    "  function writeEvents(events){var storage=safeStorage();if(!storage)throw new Error('FEEDBACK_PERSISTENCE_UNAVAILABLE');try{storage.setItem(STORAGE_KEY,JSON.stringify(events))}catch(e){throw new Error('FEEDBACK_STORAGE_FULL')}}\n"
    "  function storageKeys(storage){var length=Number(storage&&storage.length);if(!Number.isInteger(length)||length<0||typeof storage.key!=='function')throw new Error('FEEDBACK_PERSISTENCE_UNAVAILABLE');var keys=[];for(var i=0;i<length;i++){var key=storage.key(i);if(typeof key==='string')keys.push(key)}return keys}\n"
    "  function usageChronology(a,b){var at=String(a&&a.timestamp||''),bt=String(b&&b.timestamp||'');if(at<bt)return-1;if(at>bt)return 1;var aid=String(a&&a.event_id||''),bid=String(b&&b.event_id||'');return aid<bid?-1:(aid>bid?1:0)}\n"
    "  function readUsageEvents(){var storage=safeStorage();if(!storage)return[];var keys=storageKeys(storage).filter(function(key){return key.indexOf(USAGE_STORAGE_PREFIX)===0});var events=[];for(var i=0;i<keys.length;i++){var raw;try{raw=storage.getItem(keys[i])}catch(e){throw new Error('FEEDBACK_PERSISTENCE_UNAVAILABLE')}if(raw===null)continue;var event;try{event=JSON.parse(raw)}catch(e){throw new Error('FEEDBACK_STORAGE_CORRUPT')}if(!event||typeof event!=='object'||Array.isArray(event)||event.event_type!=='prompt_usage'||!event.event_id)throw new Error('FEEDBACK_STORAGE_CORRUPT');events.push(event)}events.sort(usageChronology);return events}\n"
    "  function writeUsageEvent(event){var storage=safeStorage();if(!storage)throw new Error('FEEDBACK_PERSISTENCE_UNAVAILABLE');try{storage.setItem(USAGE_STORAGE_PREFIX+event.event_id,JSON.stringify(event))}catch(e){throw new Error('FEEDBACK_STORAGE_FULL')}var events=readUsageEvents();var excess=events.length-MAX_USAGE_EVENTS;if(excess<=0)return;try{for(var i=0;i<excess;i++)storage.removeItem(USAGE_STORAGE_PREFIX+events[i].event_id)}catch(e){throw new Error('FEEDBACK_PERSISTENCE_UNAVAILABLE')}}\n",
    "usage storage helpers",
)
runtime = regex_once(
    runtime,
    r"  function append\(input\)\{.*?\n  \}\n  function encodeCursor",
    "  function append(input){var promptId=String(input.prompt_id||'').trim().toUpperCase();if(!knownPrompt(promptId))throw new Error('UNKNOWN_PROMPT');var type=input.event_type;if(type!=='prompt_vote'&&type!=='prompt_feedback'&&type!=='prompt_usage')throw new Error('INVALID_EVENT_TYPE');var value=type==='prompt_vote'?String(input.value||'').toLowerCase():(type==='prompt_feedback'?'comment':String(input.value||'').toLowerCase());if(type==='prompt_vote'&&value!=='like'&&value!=='dislike')throw new Error('INVALID_VOTE');if(type==='prompt_usage'&&!PROMPT_USAGE_VALUES[value])throw new Error('INVALID_USAGE');var source=sourceId();\n"
    "    if(type==='prompt_usage'){var usageEvent={event_id:eventId(),prompt_id:promptId,event_type:type,value:value,timestamp:new Date().toISOString(),schema_version:EVENT_SCHEMA,source:source};if(input.context!=null)usageEvent.context=normalizeUsageContext(input.context,promptId);writeUsageEvent(usageEvent);try{root.dispatchEvent(new root.CustomEvent('prompt-kit-feedback',{detail:usageEvent}))}catch(e){}return usageEvent}\n"
    "    var events=readEvents();var previous=null;if(type==='prompt_vote'){for(var i=events.length-1;i>=0;i--){if(events[i].event_type==='prompt_vote'&&events[i].prompt_id===promptId&&events[i].source===source){previous=events[i];break}}}\n"
    "    var event={event_id:eventId(),prompt_id:promptId,event_type:type,value:value,timestamp:new Date().toISOString(),schema_version:EVENT_SCHEMA,source:source,sequence:latestSequence(events)+1};\n"
    "    if(previous)event.supersedes_event_id=previous.event_id;\n"
    "    if(type==='prompt_feedback')event.comment=normalizeComment(input.comment);\n"
    "    events.push(event);writeEvents(events);\n"
    "    try{root.dispatchEvent(new root.CustomEvent('prompt-kit-feedback',{detail:event}))}catch(e){}\n"
    "    return event;\n"
    "  }\n  function encodeCursor",
    "usage-specific append",
)
runtime = replace_once(
    runtime,
    "  function exportBundle(){return JSON.stringify({schema_version:'prompt-feedback-export/v1',exported_at:new Date().toISOString(),events:readEvents()},null,2)}\n",
    "  function exportBundle(){var events=readEvents().concat(readUsageEvents()).sort(usageChronology);return JSON.stringify({schema_version:'prompt-feedback-export/v1',exported_at:new Date().toISOString(),events:events},null,2)}\n",
    "merged export",
)
runtime = replace_once(
    runtime,
    "  var api={EVENT_SCHEMA:EVENT_SCHEMA,CURSOR_SCHEMA:CURSOR_SCHEMA,append:append,pollSince:pollSince,exportBundle:exportBundle,readEvents:readEvents,currentVote:currentVote,install:install};",
    "  var api={EVENT_SCHEMA:EVENT_SCHEMA,CURSOR_SCHEMA:CURSOR_SCHEMA,MAX_USAGE_EVENTS:MAX_USAGE_EVENTS,append:append,pollSince:pollSince,exportBundle:exportBundle,readEvents:readEvents,readUsageEvents:readUsageEvents,currentVote:currentVote,install:install};",
    "runtime api",
)
write(runtime_path, runtime)


# Focused regression: model two browser tabs sharing one storage area, prove independent
# event keys preserve both observations, prove retention is bounded, and prove the
# feedback polling cursor is unaffected by usage observations.
test_path = "tests/test_prompt_finder_observation_pipeline.py"
test = read(test_path)
test = replace_once(
    test,
    "global.localStorage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v)};",
    "global.localStorage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k),key:i=>Array.from(m.keys())[i]??null,get length(){return m.size}};",
    "usage test storage shim",
)
new_test = r'''    def test_usage_ledger_is_cross_tab_safe_bounded_and_cursor_independent(self) -> None:
        script = r'''const fs=require('fs'),vm=require('vm');const code=fs.readFileSync('./docs/prompt-kit-feedback-production.js','utf8');const m=new Map();const storage={getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k),key:i=>Array.from(m.keys())[i]??null,get length(){return m.size}};function tab(prefix){let i=0;const c={localStorage:storage,crypto:{randomUUID:()=>`${prefix}-${++i}`},PROMPTS:[{id:'P07'}],dispatchEvent:()=>{},CustomEvent:function(){}};c.window=c;c.globalThis=c;vm.createContext(c);vm.runInContext(code,c);return c}const a=tab('a'),b=tab('b');const context={surface:'prompt_finder',measurement:'selection_intent',session_id:'finder-tabs',answers:{startingPoint:'in-repo',problemKnown:'known-task',goal:'build',shape:'one-sprint'},recommendations:['P07']};a.PromptKitFeedback.append({prompt_id:'P07',event_type:'prompt_usage',value:'open',context});b.PromptKitFeedback.append({prompt_id:'P07',event_type:'prompt_usage',value:'copy',context});let usageKeys=Array.from(m.keys()).filter(k=>k.startsWith('promptKit.feedbackUsage.v1.'));if(usageKeys.length!==2)process.exit(2);let bundle=JSON.parse(a.PromptKitFeedback.exportBundle());if(bundle.events.length!==2||new Set(bundle.events.map(e=>e.event_id)).size!==2)process.exit(3);if(a.PromptKitFeedback.pollSince('prompt-feedback-cursor/v1:0',10).events.length!==0)process.exit(4);for(let i=0;i<600;i++){const api=i%2?a.PromptKitFeedback:b.PromptKitFeedback;api.append({prompt_id:'P07',event_type:'prompt_usage',value:i%2?'open':'copy',context})}usageKeys=Array.from(m.keys()).filter(k=>k.startsWith('promptKit.feedbackUsage.v1.'));bundle=JSON.parse(a.PromptKitFeedback.exportBundle());if(usageKeys.length!==a.PromptKitFeedback.MAX_USAGE_EVENTS||bundle.events.length!==a.PromptKitFeedback.MAX_USAGE_EVENTS)process.exit(5);if(a.PromptKitFeedback.pollSince('prompt-feedback-cursor/v1:0',10).events.length!==0)process.exit(6);console.log(JSON.stringify({usage_keys:usageKeys.length,exported:bundle.events.length,poll_events:0}));'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["usage_keys"], 500)
        self.assertEqual(report["exported"], 500)
        self.assertEqual(report["poll_events"], 0)

'''
test = replace_once(
    test,
    "    def test_guided_finder_records_selection_intent_without_claiming_gold(self) -> None:\n",
    new_test + "    def test_guided_finder_records_selection_intent_without_claiming_gold(self) -> None:\n",
    "cross-tab usage regression",
)
write(test_path, test)


# Design truth: make the separate storage/cursor/retention boundary explicit.
design_path = "docs/PROMPT_KIT_FEEDBACK_POLLING_DESIGN.md"
design = read(design_path)
needle = "The first production measurement is **selection intent** (`open` / `copy` selected from a recommendation card), not proof that the downstream prompt succeeded or that clipboard completion occurred."
addition = "Prompt Finder usage observations are persisted separately from the append-only vote/comment cursor log: one `localStorage` key per usage event under `promptKit.feedbackUsage.v1.*`, with a bounded retention window of 500 observations. Independent event keys prevent concurrent browser tabs from overwriting each other's Finder observations. `pollSince` remains scoped to the sequenced vote/comment log; `exportBundle` merges the bounded usage ledger back in for statistics and candidate-eval ingestion.\n\n" + needle
design = replace_once(design, needle, addition, "usage storage design boundary")
write(design_path, design)


# Proof loop. Regenerate the canonical static surface through the owner builder only.
commands = [
    ["node", "--check", runtime_path],
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

report_path = ROOT / "Outputs" / "prompt-finder-classifier-eval.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
metrics = report.get("metrics", {})
if report.get("verdict") != "pass" or metrics.get("case_pass_rate") != 1 or metrics.get("primary_accuracy") != 1 or metrics.get("required_recall_at_3") != 1 or metrics.get("deterministic_cases") != metrics.get("case_count"):
    raise SystemExit(f"classifier regression after storage review fix: {metrics}")
report_path.unlink(missing_ok=True)

print(json.dumps({
    "status": "PASS",
    "classifier_metrics": metrics,
    "usage_retention": 500,
    "usage_storage": "event-per-key",
    "polling_scope": "sequenced vote/comment log only",
}, sort_keys=True))
