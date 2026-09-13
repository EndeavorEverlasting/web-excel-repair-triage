#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import os
import shutil
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
OUTPUTS_ROOT = ROOT / 'Outputs'
BACKUP_ROOT = OUTPUTS_ROOT / 'backups'
CSS_PATH = ROOT / 'docs/prompt-topology-viewer.css'
JS_PATH = ROOT / 'docs/prompt-topology-viewer.js'
CONTRACT_PATH = ROOT / 'harness/prompt-topology/phase-c-viewer.v1.json'


class ViewerBuildError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ViewerBuildError(f'missing input: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ViewerBuildError(f'invalid JSON: {path}: {exc}') from exc


def canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def validate_inputs(topology: dict[str, Any], projection: dict[str, Any], state: dict[str, Any]) -> None:
    contract = load_json(CONTRACT_PATH)
    if contract.get('schema_version') != 'prompt-topology-phase-c-viewer/v1':
        raise ViewerBuildError('Phase C contract version drift')
    if topology.get('schema_version') != 'prompt-topology-artifact/v1':
        raise ViewerBuildError('unsupported topology schema')
    if state.get('schema_version') != 'prompt-topology-projection-state/v1':
        raise ViewerBuildError('unsupported projection state schema')

    topology_hash = str(topology.get('content_hash_sha256') or '')
    unhashed = dict(topology)
    unhashed.pop('content_hash_sha256', None)
    if not topology_hash or topology_hash != canonical_hash(unhashed):
        raise ViewerBuildError('topology content hash mismatch')
    if state.get('topology_content_hash_sha256') != topology_hash:
        raise ViewerBuildError('topology/state binding mismatch')

    projection_hash = canonical_hash(projection)
    if state.get('projection_sha256') != projection_hash:
        raise ViewerBuildError('projection/state hash mismatch')

    node_id_list = [node.get('prompt_id') for node in topology.get('nodes', [])]
    node_ids = set(node_id_list)
    point_ids = set((projection.get('points') or {}).keys())
    if None in node_ids or len(node_id_list) != len(node_ids):
        raise ViewerBuildError('duplicate or empty prompt IDs in topology')
    if node_ids != point_ids:
        raise ViewerBuildError(f'prompt/projection parity mismatch nodes={len(node_ids)} points={len(point_ids)}')

    cluster_members = [
        prompt_id
        for cluster in topology.get('clusters', [])
        for prompt_id in cluster.get('member_prompt_ids', [])
    ]
    outliers = list(topology.get('outlier_prompt_ids', []))
    partition = cluster_members + outliers
    if len(partition) != len(node_ids) or set(partition) != node_ids:
        raise ViewerBuildError('cluster/outlier partition mismatch')


def compact_payload(
    topology: dict[str, Any], projection: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    keep_node = (
        'prompt_id',
        'seq',
        'title',
        'prompt_class',
        'prompt_type',
        'family_declared',
        'family_declared_id',
        'keywords',
        'category',
    )
    nodes = [{key: node[key] for key in keep_node if key in node} for node in topology['nodes']]
    edges = [
        {
            'source': edge['source'],
            'target': edge['target'],
            'strength_micros': edge['strength_micros'],
            'channels': [{'type': channel['type']} for channel in edge.get('channels', [])],
        }
        for edge in topology.get('edges', [])
    ]
    clusters = [
        {
            key: cluster[key]
            for key in (
                'cluster_id',
                'member_count',
                'member_prompt_ids',
                'representative_prompt_id',
                'family_candidate_id',
                'lineage',
            )
            if key in cluster
        }
        for cluster in topology.get('clusters', [])
    ]
    opportunities = [
        {
            key: opportunity[key]
            for key in ('cluster_id', 'prompt_ids', 'recommended_action', 'score', 'sector_id', 'state')
            if key in opportunity
        }
        for opportunity in topology.get('opportunities', [])
    ]
    return {
        'schema_version': 'prompt-topology-viewer-data/v1',
        'topology_hash': topology['content_hash_sha256'],
        'projection_hash': state['projection_sha256'],
        'nodes': nodes,
        'edges': edges,
        'clusters': clusters,
        'opportunities': opportunities,
        'outlier_prompt_ids': topology.get('outlier_prompt_ids', []),
        'projection': projection,
        'projection_state': {
            'epoch_id': state['epoch_id'],
            'parent_epoch_id': state.get('parent_epoch_id'),
            'topology_content_hash_sha256': state['topology_content_hash_sha256'],
            'projection_sha256': state['projection_sha256'],
        },
    }


def render_document(payload: dict[str, Any]) -> str:
    css = CSS_PATH.read_text(encoding='utf-8').strip()
    js = JS_PATH.read_text(encoding='utf-8').strip()
    # Escaping every closing-tag prefix protects script data regardless of tag casing.
    data = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    cluster_count = len(payload['clusters'])
    outliers = len(payload['outlier_prompt_ids'])
    fallback_items = ''.join(
        f'<li id="prompt-{html.escape(str(node["prompt_id"]))}"><strong>{html.escape(str(node["prompt_id"]))}</strong> — '
        f'{html.escape(str(node.get("title", "")))} <span>{html.escape(str(node.get("family_declared", "")))}</span></li>'
        for node in payload['nodes']
    )
    return f'''<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="description" content="Read-only immersive viewer for deterministic Prompt Topology Phase A/B evidence">\n<title>Prompt Topology Universe</title>\n<style>\n{css}\n</style>\n</head>\n<body>\n<main class="app">\n<header class="topbar">\n  <div class="brand"><span class="brand-mark"></span><div><h1>Prompt Topology Universe</h1><div class="subtitle">Phase C · read-only semantic evidence viewer</div></div></div>\n  <label class="search-wrap"><span class="search-icon">⌕</span><input id="search" type="search" autocomplete="off" spellcheck="false" aria-label="Search prompts" placeholder="Search P105, title, family, type, keyword…"></label>\n  <div class="stats"><span class="stat"><strong id="nodeCount">0</strong> prompts</span><span class="stat optional"><strong id="edgeCount">0</strong> edges</span><span class="stat optional">{cluster_count} clusters · {outliers} outliers</span></div>\n</header>\n<section class="stage" aria-label="3D prompt topology canvas">\n  <canvas id="universe" tabindex="0" aria-label="Interactive prompt topology universe"></canvas>\n  <div id="hoverLabel" class="hover-label" role="status"></div>\n  <div class="hud"><span class="pill">Drag · rotate</span><span class="pill">Shift+drag · pan</span><span class="pill">Wheel · zoom</span><span class="pill optional">Hover · inspect</span><span class="pill optional">Click · pin</span></div>\n</section>\n<aside class="side">\n  <section class="section"><h2 class="section-title">Clusters</h2><div id="clusters" class="cluster-list"></div></section>\n  <section class="section details"><h2 class="section-title">Prompt evidence</h2><div id="detail"></div></section>\n  <section class="section"><h2 class="section-title">Legend</h2><div class="legend"><div class="legend-item"><span class="dot" style="background:#7cc7ff"></span>family-hashed nodes</div><div class="legend-item"><span class="dot" style="background:#8aa0b7"></span>semantic edges</div></div></section>\n  <section class="section"><h2 class="section-title">Evidence binding</h2><div class="help">Epoch <strong id="epochId"></strong>. Viewer geometry is presentation-only.</div><div id="bindingHash" class="binding"></div></section>\n  <details class="text-fallback"><summary>Text index · {len(payload['nodes'])} prompts</summary><p>Non-3D readable fallback. Prompt identity and grouping come from Phase A evidence.</p><ol>{fallback_items}</ol></details>\n  <noscript><p class="empty">3D interaction requires JavaScript. The text index above remains readable.</p></noscript>\n  <button id="resetView" type="button" class="reset-btn">Reset view</button>\n</aside>\n</main>\n<script>window.PROMPT_TOPOLOGY_DATA={data};</script>\n<script>\n{js}\n</script>\n</body>\n</html>\n'''


def rebuild_inputs() -> tuple[Path, Path, Path, tempfile.TemporaryDirectory[str]]:
    temp = tempfile.TemporaryDirectory(prefix='prompt-topology-phase-c-')
    root = Path(temp.name)
    topology = root / 'topology.v1.json'
    projection = root / 'projection-3d.json'
    state = root / 'projection-state.v1.json'
    subprocess.run(
        [sys.executable, str(ROOT / 'scripts/prompt-topology/run.py'), '--output', str(topology)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts/prompt-topology/project.py'),
            '--topology',
            str(topology),
            '--output',
            str(projection),
            '--state-output',
            str(state),
        ],
        cwd=ROOT,
        check=True,
    )
    return topology, projection, state, temp


def resolve_inputs(
    topology: Path, projection: Path, state: Path
) -> tuple[Path, Path, Path, tempfile.TemporaryDirectory[str] | None]:
    supplied = (topology, projection, state)
    defaults = (DEFAULT_TOPOLOGY, DEFAULT_PROJECTION, DEFAULT_STATE)
    missing = [path for path in supplied if not path.exists()]
    if not missing:
        return topology, projection, state, None
    if supplied == defaults:
        return rebuild_inputs()
    raise ViewerBuildError('incomplete explicit input bundle; missing: ' + ', '.join(str(path) for path in missing))


def _has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    candidates = [absolute, *absolute.parents]
    return any(candidate.exists() and candidate.is_symlink() for candidate in candidates)


def validate_output_path(output: Path, inputs: tuple[Path, Path, Path]) -> None:
    if _has_symlink_component(output):
        raise ViewerBuildError(f'output path must not traverse a symlink: {output}')
    resolved_output = output.resolve()
    for input_path in inputs:
        if resolved_output == input_path.resolve():
            raise ViewerBuildError(f'output path must not equal input path: {output}')


def prepare_inputs(
    topology: Path,
    projection: Path,
    state: Path,
    output: Path,
) -> tuple[Path, Path, Path, tempfile.TemporaryDirectory[str] | None]:
    requested_inputs = (topology, projection, state)
    validate_output_path(output, requested_inputs)
    resolved = resolve_inputs(topology, projection, state)
    validate_output_path(output, resolved[:3])
    return resolved


def backup_existing_external_output(
    output: Path,
    *,
    outputs_root: Path = OUTPUTS_ROOT,
    backup_root: Path = BACKUP_ROOT,
) -> Path | None:
    if not output.exists():
        return None
    absolute_output = output.absolute()
    try:
        absolute_output.relative_to(outputs_root.absolute())
        return None
    except ValueError:
        pass

    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    backup_dir = Path(tempfile.mkdtemp(prefix=f'{stamp}-', dir=backup_root))
    backup_path = backup_dir / output.name
    shutil.copy2(output, backup_path)
    return backup_path


def atomic_write_text(output: Path, rendered: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            newline='\n',
            dir=output.parent,
            prefix=f'.{output.name}.',
            suffix='.tmp',
            delete=False,
        ) as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, output)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def build(topology_path: Path, projection_path: Path, state_path: Path) -> str:
    topology = load_json(topology_path)
    projection = load_json(projection_path)
    state = load_json(state_path)
    validate_inputs(topology, projection, state)
    return render_document(compact_payload(topology, projection, state))


def main() -> int:
    parser = argparse.ArgumentParser(description='Build deterministic Prompt Topology Phase C viewer')
    parser.add_argument('--topology', type=Path, default=DEFAULT_TOPOLOGY)
    parser.add_argument('--projection', type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    temp = None
    try:
        topology_path, projection_path, state_path, temp = prepare_inputs(
            args.topology, args.projection, args.state, args.output
        )
        inputs = (topology_path, projection_path, state_path)
        rendered = build(*inputs)
        if args.check:
            if not args.output.exists():
                raise ViewerBuildError(f'generated viewer missing: {args.output}')
            if args.output.read_text(encoding='utf-8') != rendered:
                raise ViewerBuildError('generated viewer is stale; rebuild canonical artifact')
        else:
            backup_existing_external_output(args.output)
            atomic_write_text(args.output, rendered)
        if args.summary:
            payload = load_json(topology_path)
            state = load_json(state_path)
            print(
                json.dumps(
                    {
                        'status': 'PASS',
                        'nodes': len(payload['nodes']),
                        'edges': len(payload['edges']),
                        'clusters': len(payload['clusters']),
                        'outliers': len(payload['outlier_prompt_ids']),
                        'topology_hash': payload['content_hash_sha256'],
                        'epoch_id': state['epoch_id'],
                        'output': str(args.output),
                    },
                    sort_keys=True,
                )
            )
        return 0
    except (ViewerBuildError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    finally:
        if temp is not None:
            temp.cleanup()


if __name__ == '__main__':
    raise SystemExit(main())
