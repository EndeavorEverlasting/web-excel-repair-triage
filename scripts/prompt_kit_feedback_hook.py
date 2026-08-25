#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path

EVENT_SCHEMA='prompt-feedback-event/v1'
EXPORT_SCHEMA='prompt-feedback-export/v1'
REPORT_SCHEMA='prompt-feedback-maintenance-report/v1'

def load_events(root: Path) -> list[dict]:
    events=[]
    if not root.exists(): return events
    for path in sorted(root.glob('*.json')):
        payload=json.loads(path.read_text(encoding='utf-8'))
        if payload.get('schema_version')!=EXPORT_SCHEMA: raise SystemExit(f'unsupported export schema: {path}')
        rows=payload.get('events')
        if not isinstance(rows,list): raise SystemExit(f'events must be a list: {path}')
        events.extend(rows)
    return events

def validate_event(event: dict) -> None:
    required={'event_id','prompt_id','event_type','value','timestamp','schema_version','source'}
    if not required.issubset(event): raise SystemExit(f'malformed feedback event: {event.get("event_id","unknown")}')
    if event['schema_version']!=EVENT_SCHEMA: raise SystemExit('unsupported feedback event schema')
    if event['event_type'] not in {'prompt_vote','prompt_feedback'}: raise SystemExit('unsupported feedback event type')
    if event['event_type']=='prompt_vote' and event['value'] not in {'like','dislike'}: raise SystemExit('unsupported vote')
    forbidden=('prompt_body','clipboard','secret','token','password','credential')
    for key in event:
        if any(marker in key.lower() for marker in forbidden): raise SystemExit(f'sensitive feedback field rejected: {key}')

def aggregate(events: list[dict], minimum_dislikes: int) -> dict:
    seen={}; latest_votes={}; comments=defaultdict(list)
    for event in events:
        validate_event(event)
        eid=str(event['event_id'])
        canonical=json.dumps(event,sort_keys=True,separators=(',',':'))
        if eid in seen:
            if seen[eid]!=canonical: raise SystemExit(f'event id conflict: {eid}')
            continue
        seen[eid]=canonical
        pid=str(event['prompt_id']).upper(); source=str(event['source'])
        if event['event_type']=='prompt_vote': latest_votes[(pid,source)]=event
        else: comments[pid].append(event)
    prompt_ids=sorted({pid for pid,_ in latest_votes}|set(comments))
    rows=[]
    for pid in prompt_ids:
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
