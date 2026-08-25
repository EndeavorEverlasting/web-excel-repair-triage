#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def git_head() -> str:
    return subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--candidate',required=True); p.add_argument('--base',default=''); p.add_argument('--target',default='github-pages'); p.add_argument('--output',type=Path,default=Path('Outputs/prompt-kit-promotion-receipt.json')); a=p.parse_args()
    if a.target!='github-pages': raise SystemExit('target not allowed')
    actual=git_head()
    if actual!=a.candidate: raise SystemExit(f'stale candidate: checkout={actual} requested={a.candidate}')
    artifact=Path('web/prompt-kit/index.html'); digest=hashlib.sha256(artifact.read_bytes()).hexdigest()
    receipt={'schema_version':'prompt-kit-promotion-receipt/v1','provider_run_id':os.environ.get('GITHUB_RUN_ID','local'),'event':os.environ.get('GITHUB_EVENT_NAME','local'),'actor':os.environ.get('GITHUB_ACTOR','local'),'candidate_sha':actual,'base_sha':a.base or None,'target':a.target,'artifact_path':artifact.as_posix(),'artifact_sha256':digest,'required_gates':['harness-e2e','feedback-contract','application-browser-e2e','release-identity','pages-package'],'proof_ceiling':'repository harness + headless browser + GitHub Pages deployment; deployed-byte identity requires post-deploy check'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps({'status':'PASS','candidate_sha':actual,'artifact_sha256':digest})); return 0
if __name__=='__main__': raise SystemExit(main())
