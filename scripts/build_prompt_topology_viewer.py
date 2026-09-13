#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOPOLOGY = ROOT / 'artifacts/prompt-topology/topology.v1.json'
DEFAULT_PROJECTION = ROOT / 'artifacts/prompt-topology/projection-3d.json'
DEFAULT_STATE = ROOT / 'artifacts/prompt-topology/projection-state.v1.json'
DEFAULT_OUTPUT = ROOT / 'Outputs/prompt-topology-viewer/index.html'
CSS_PATH = ROOT / 'docs/prompt-topology-viewer.css'
JS_PATH = ROOT / 'docs/prompt-topology-viewer.js'
CONTRACT_PATH = ROOT / 'harness/prompt-topology/phase-c-viewer.v1.json'

class ViewerBuildError(RuntimeError): pass

def load_json(path: Path) -> dict[str, Any]:
    try: return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc: raise ViewerBuildError(f'missing input: {path}') from exc
    except json.JSONDecodeError as exc: raise ViewerBuildError(f'invalid JSON: {path}: {exc}') from exc

def canonical_hash(payload: Any) -> str:
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def validate_inputs(topology: dict[str,Any], projection: dict[str,Any], state: dict[str,Any]) -> None:
    contract=load_json(CONTRACT_PATH)
    if contract.get('schema_version')!='prompt-topology-phase-c-viewer/v1': raise ViewerBuildError('Phase C contract version drift')
    if topology.get('schema_version')!='prompt-topology-artifact/v1': raise ViewerBuildError('unsupported topology schema')
    if state.get('schema_version')!='prompt-topology-projection-state/v1': raise ViewerBuildError('unsupported projection state schema')
    topology_hash=topology.get('content_hash_sha256')
    if not topology_hash or state.get('topology_content_hash_sha256')!=topology_hash: raise ViewerBuildError('topology/state binding mismatch')
    projection_hash=canonical_hash(projection)
    if state.get('projection_sha256')!=projection_hash: raise ViewerBuildError('projection/state hash mismatch')
    node_ids={n.get('prompt_id') for n in topology.get('nodes',[])}
    point_ids=set((projection.get('points') or {}).keys())
    if None in node_ids or node_ids!=point_ids: raise ViewerBuildError(f'prompt/projection parity mismatch nodes={len(node_ids)} points={len(point_ids)}')
    cluster_members=[pid for c in topology.get('clusters',[]) for pid in c.get('member_prompt_ids',[])]
    outliers=topology.get('outlier_prompt_ids',[])
    if set(cluster_members)|set(outliers)!=node_ids or set(cluster_members)&set(outliers): raise ViewerBuildError('cluster/outlier partition mismatch')

def compact_payload(topology:dict[str,Any],projection:dict[str,Any],state:dict[str,Any])->dict[str,Any]:
    keep_node=('prompt_id','seq','title','prompt_class','prompt_type','family_declared','family_declared_id','keywords','category')
    nodes=[{k:n[k] for k in keep_node if k in n} for n in topology['nodes']]
    edges=[{'source':e['source'],'target':e['target'],'strength_micros':e['strength_micros'],'channels':[{'type':c['type']} for c in e.get('channels',[])]} for e in topology.get('edges',[])]
    clusters=[{k:c[k] for k in ('cluster_id','member_count','member_prompt_ids','representative_prompt_id','family_candidate_id','lineage') if k in c} for c in topology.get('clusters',[])]
    opportunities=[{k:o[k] for k in ('cluster_id','prompt_ids','recommended_action','score','sector_id','state') if k in o} for o in topology.get('opportunities',[])]
    return {'schema_version':'prompt-topology-viewer-data/v1','topology_hash':topology['content_hash_sha256'],'projection_hash':state['projection_sha256'],'nodes':nodes,'edges':edges,'clusters':clusters,'opportunities':opportunities,'outlier_prompt_ids':topology.get('outlier_prompt_ids',[]),'projection':projection,'projection_state':{'epoch_id':state['epoch_id'],'parent_epoch_id':state.get('parent_epoch_id'),'topology_content_hash_sha256':state['topology_content_hash_sha256'],'projection_sha256':state['projection_sha256']}}

def render_document(payload:dict[str,Any])->str:
    css=CSS_PATH.read_text(encoding='utf-8').strip(); js=JS_PATH.read_text(encoding='utf-8').strip()
    data=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
    cluster_count=len(payload['clusters']); outliers=len(payload['outlier_prompt_ids'])
    return f'''<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="description" content="Read-only immersive viewer for deterministic Prompt Topology Phase A/B evidence">\n<title>Prompt Topology Universe</title>\n<style>\n{css}\n</style>\n</head>\n<body>\n<main class="app">\n<header class="topbar">\n  <div class="brand"><span class="brand-mark"></span><div><h1>Prompt Topology Universe</h1><div class="subtitle">Phase C · read-only semantic evidence viewer</div></div></div>\n  <label class="search-wrap"><span class="search-icon">⌕</span><input id="search" type="search" autocomplete="off" spellcheck="false" aria-label="Search prompts" placeholder="Search P105, title, family, type, keyword…"></label>\n  <div class="stats"><span class="stat"><strong id="nodeCount">0</strong> prompts</span><span class="stat optional"><strong id="edgeCount">0</strong> edges</span><span class="stat optional">{cluster_count} clusters · {outliers} outliers</span></div>\n</header>\n<section class="stage" aria-label="3D prompt topology canvas">\n  <canvas id="universe" tabindex="0" aria-label="Interactive prompt topology universe"></canvas>\n  <div id="hoverLabel" class="hover-label" role="status"></div>\n  <div class="hud"><span class="pill">Drag · rotate</span><span class="pill">Wheel · zoom</span><span class="pill optional">Hover · inspect</span><span class="pill optional">Click · pin</span></div>\n</section>\n<aside class="side">\n  <section class="section"><h2 class="section-title">Clusters</h2><div id="clusters" class="cluster-list"></div></section>\n  <section class="section details"><h2 class="section-title">Prompt evidence</h2><div id="detail"></div></section>\n  <section class="section"><h2 class="section-title">Legend</h2><div class="legend"><div class="legend-item"><span class="dot" style="background:#7cc7ff"></span>family-hashed nodes</div><div class="legend-item"><span class="dot" style="background:#8aa0b7"></span>semantic edges</div></div></section>\n  <section class="section"><h2 class="section-title">Evidence binding</h2><div class="help">Epoch <strong id="epochId"></strong>. Viewer geometry is presentation-only.</div><div id="bindingHash" class="binding"></div></section>\n  <button id="resetView" type="button" class="reset-btn">Reset view</button>\n</aside>\n</main>\n<script>window.PROMPT_TOPOLOGY_DATA={data};</script>\n<script>\n{js}\n</script>\n</body>\n</html>\n'''

def rebuild_inputs() -> tuple[Path,Path,Path,tempfile.TemporaryDirectory[str]]:
    temp=tempfile.TemporaryDirectory(prefix='prompt-topology-phase-c-'); root=Path(temp.name)
    topology=root/'topology.v1.json'; projection=root/'projection-3d.json'; state=root/'projection-state.v1.json'
    subprocess.run([sys.executable,str(ROOT/'scripts/prompt-topology/run.py'),'--output',str(topology)],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/prompt-topology/project.py'),'--topology',str(topology),'--output',str(projection),'--state-output',str(state)],cwd=ROOT,check=True)
    return topology,projection,state,temp

def build(topology_path:Path,projection_path:Path,state_path:Path)->str:
    topology=load_json(topology_path);projection=load_json(projection_path);state=load_json(state_path);validate_inputs(topology,projection,state)
    return render_document(compact_payload(topology,projection,state))

def main()->int:
    ap=argparse.ArgumentParser(description='Build deterministic Prompt Topology Phase C viewer')
    ap.add_argument('--topology',type=Path,default=DEFAULT_TOPOLOGY);ap.add_argument('--projection',type=Path,default=DEFAULT_PROJECTION);ap.add_argument('--state',type=Path,default=DEFAULT_STATE);ap.add_argument('--output',type=Path,default=DEFAULT_OUTPUT);ap.add_argument('--check',action='store_true');ap.add_argument('--summary',action='store_true')
    args=ap.parse_args(); temp=None
    try:
      tp,pp,sp=args.topology,args.projection,args.state
      if not (tp.exists() and pp.exists() and sp.exists()): tp,pp,sp,temp=rebuild_inputs()
      rendered=build(tp,pp,sp)
      if args.check:
        if not args.output.exists(): raise ViewerBuildError(f'generated viewer missing: {args.output}')
        if args.output.read_text(encoding='utf-8')!=rendered: raise ViewerBuildError('generated viewer is stale; rebuild canonical artifact')
      else:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(rendered,encoding='utf-8',newline='\n')
      if args.summary:
        payload=load_json(tp);state=load_json(sp);print(json.dumps({'status':'PASS','nodes':len(payload['nodes']),'edges':len(payload['edges']),'clusters':len(payload['clusters']),'outliers':len(payload['outlier_prompt_ids']),'topology_hash':payload['content_hash_sha256'],'epoch_id':state['epoch_id'],'output':str(args.output)},sort_keys=True))
      return 0
    except (ViewerBuildError,subprocess.CalledProcessError) as exc:
      print(f'ERROR: {exc}',file=sys.stderr);return 1
    finally:
      if temp is not None: temp.cleanup()
if __name__=='__main__': raise SystemExit(main())
