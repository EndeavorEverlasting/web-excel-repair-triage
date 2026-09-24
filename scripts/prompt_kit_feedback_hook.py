#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path: sys.path.insert(0,str(REPO_ROOT))
from scripts import build_prompt_kit_registry as registry

EVENT_SCHEMA='prompt-feedback-event/v1'
EXPORT_SCHEMA='prompt-feedback-export/v1'
REPORT_SCHEMA='prompt-feedback-maintenance-report/v1'
SENSITIVE_MARKERS=('prompt_body','clipboard','secret','token','password','credential')

def canonical_prompt_ids() -> set[str]:
    return {str(prompt.get('id','')).strip().upper() for prompt in registry.load_prompt_kit_registry() if isinstance(prompt,dict) and str(prompt.get('id','')).strip()}

def require_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value,str) or not value.strip(): raise SystemExit(f'{field} must be a non-empty string')
    text=value.strip()
    if len(text)>maximum: raise SystemExit(f'{field} exceeds {maximum} characters')
    return text

def parse_timestamp(value: object) -> datetime:
    text=require_text(value,'timestamp',64)
    try: return datetime.fromisoformat(text.replace('Z','+00:00'))
    except ValueError as exc: raise SystemExit(f'invalid timestamp: {text}') from exc

def reject_sensitive_payload(value: object, path: str='event') -> None:
    if isinstance(value,dict):
        for key,item in value.items():
            key_text=str(key)
            if any(marker in key_text.lower() for marker in SENSITIVE_MARKERS): raise SystemExit(f'sensitive feedback field rejected: {path}.{key_text}')
            reject_sensitive_payload(item,f'{path}.{key_text}')
    elif isinstance(value,list):
        for index,item in enumerate(value): reject_sensitive_payload(item,f'{path}[{index}]')

def load_events(root: Path) -> list[dict]:
    events=[]
    if not root.exists(): return events
    for path in sorted(root.glob('*.json')):
        payload=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(payload,dict) or payload.get('schema_version')!=EXPORT_SCHEMA: raise SystemExit(f'unsupported export schema: {path}')
        rows=payload.get('events')
        if not isinstance(rows,list): raise SystemExit(f'events must be a list: {path}')
        for row in rows:
            if not isinstance(row,dict): raise SystemExit(f'event rows must be objects: {path}')
            events.append(row)
    return events

def validate_event(event: dict, prompt_ids: set[str]) -> dict:
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
    if normalized['event_type'] not in {'prompt_vote','prompt_feedback'}: raise SystemExit('unsupported feedback event type')
    if normalized['event_type']=='prompt_vote':
        if event['value'] not in {'like','dislike'}: raise SystemExit('unsupported vote')
        normalized['value']=event['value']
    else:
        if event['value']!='comment': raise SystemExit('prompt_feedback value must be comment')
        normalized['comment']=require_text(event.get('comment'),'comment',1000)
        normalized['value']='comment'
    sequence=event.get('sequence',0)
    if sequence is not None and (not isinstance(sequence,int) or sequence<0): raise SystemExit('sequence must be a non-negative integer')
    normalized['_sequence']=sequence or 0
    supersedes=event.get('supersedes_event_id')
    if supersedes is not None: normalized['supersedes_event_id']=require_text(supersedes,'supersedes_event_id',160)
    return normalized

def aggregate(events: list[dict], minimum_dislikes: int, prompt_ids: set[str] | None=None) -> dict:
    prompt_ids=prompt_ids or canonical_prompt_ids()
    seen={}; latest_votes={}; comments=defaultdict(list); normalized_events=[]
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
        if event['event_type']=='prompt_vote': latest_votes[(pid,source)]=event
        else: comments[pid].append(event)
    prompt_ids_with_evidence=sorted({pid for pid,_ in latest_votes}|set(comments))
    rows=[]
    for pid in prompt_ids_with_evidence:
        votes=[e for (p,_),e in latest_votes.items() if p==pid]
        row={'prompt_id':pid,'likes':sum(e['value']=='like' for e in votes),'dislikes':sum(e['value']=='dislike' for e in votes),'feedback_count':len(comments[pid])}
        if row['dislikes']>=minimum_dislikes: row['disposition']='REVIEW_CANDIDATE'
        rows.append(row)
    return {'schema_version':REPORT_SCHEMA,'event_count':len(seen),'minimum_dislikes':minimum_dislikes,'candidates':[r for r in rows if r.get('disposition')=='REVIEW_CANDIDATE'],'summaries':rows,'mutation_authority':False}

def main() -> int:
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=Path('feedback/inbox'));p.add_argument('--output',type=Path,default=Path('Outputs/prompt-kit-feedback-maintenance.json'));p.add_argument('--minimum-dislikes',type=int,default=2);a=p.parse_args()
    if a.minimum_dislikes<1: raise SystemExit('minimum dislikes must be positive')
    report=aggregate(load_events(a.input),a.minimum_dislikes);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','events':report['event_count'],'candidates':len(report['candidates']),'output':a.output.as_posix()}));return 0
if __name__=='__main__': raise SystemExit(main())
