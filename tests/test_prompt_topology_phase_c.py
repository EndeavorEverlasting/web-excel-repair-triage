from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('phase_c_builder', ROOT / 'scripts/build_prompt_topology_viewer.py')
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def ch(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def fixture():
    topology = {
        'schema_version': 'prompt-topology-artifact/v1',
        'nodes': [
            {
                'prompt_id': 'P00',
                'seq': '00',
                'title': 'Alpha',
                'prompt_type': 'DISCOVER',
                'prompt_class': 'TEST',
                'family_declared': 'Foundation',
                'family_declared_id': 'foundation',
                'keywords': ['alpha'],
                'category': 'standard',
            },
            {
                'prompt_id': 'P01',
                'seq': '01',
                'title': 'Beta',
                'prompt_type': 'BUILD',
                'prompt_class': 'TEST',
                'family_declared': 'Build',
                'family_declared_id': 'build-repair',
                'keywords': ['beta'],
                'category': 'standard',
            },
        ],
        'edges': [
            {
                'source': 'P00',
                'target': 'P01',
                'strength_micros': 900000,
                'channels': [{'type': 'SEMANTIC_NEIGHBOR'}],
            }
        ],
        'clusters': [
            {
                'cluster_id': 'C-TEST',
                'member_count': 2,
                'member_prompt_ids': ['P00', 'P01'],
                'representative_prompt_id': 'P00',
                'family_candidate_id': 'foundation',
                'lineage': 'NEW',
            }
        ],
        'opportunities': [
            {
                'cluster_id': 'C-TEST',
                'prompt_ids': ['P00', 'P01'],
                'recommended_action': 'INVESTIGATE',
                'score': 12,
                'sector_id': 'C-TEST',
                'state': 'UNDERDEVELOPED',
            }
        ],
        'outlier_prompt_ids': [],
    }
    topology['content_hash_sha256'] = ch({k: topology[k] for k in topology if k != 'content_hash_sha256'})
    projection = {
        'schema_version': '1.0.0',
        'algorithm': 'umap',
        'parameters': {'n_components': 3},
        'points': {
            'P00': {'x': 0.1, 'y': 0.2, 'z': 0.3},
            'P01': {'x': -0.1, 'y': -0.2, 'z': -0.3},
        },
    }
    state = {
        'schema_version': 'prompt-topology-projection-state/v1',
        'epoch_id': 'E-TEST',
        'parent_epoch_id': None,
        'topology_content_hash_sha256': topology['content_hash_sha256'],
        'projection_sha256': ch(projection),
        'prompt_count': 2,
        'content_hash_sha256': 'b' * 64,
        'alignment': {},
        'provenance': {},
    }
    return topology, projection, state


def rebind_topology(topology, state):
    topology['content_hash_sha256'] = ch({k: topology[k] for k in topology if k != 'content_hash_sha256'})
    state['topology_content_hash_sha256'] = topology['content_hash_sha256']


class PhaseCViewerTests(unittest.TestCase):
    def test_fixture_build_is_deterministic_and_self_contained(self):
        topology, projection, state = fixture()
        first = mod.render_document(mod.compact_payload(topology, projection, state))
        second = mod.render_document(mod.compact_payload(topology, projection, state))
        self.assertEqual(first, second)
        self.assertIn('Prompt Topology Universe', first)
        self.assertIn('window.PROMPT_TOPOLOGY_DATA=', first)
        self.assertNotIn('<script src=', first)
        self.assertNotIn('<link rel="stylesheet"', first)
        self.assertIn('Text index · 2 prompts', first)
        self.assertIn('id="prompt-P00"', first)

    def test_exact_hash_binding_and_prompt_point_parity(self):
        topology, projection, state = fixture()
        mod.validate_inputs(topology, projection, state)
        bad_state = dict(state)
        bad_state['topology_content_hash_sha256'] = 'f' * 64
        with self.assertRaisesRegex(mod.ViewerBuildError, 'topology/state'):
            mod.validate_inputs(topology, projection, bad_state)
        bad_projection = json.loads(json.dumps(projection))
        bad_projection['points'].pop('P01')
        bad_state = dict(state)
        bad_state['projection_sha256'] = ch(bad_projection)
        with self.assertRaisesRegex(mod.ViewerBuildError, 'parity'):
            mod.validate_inputs(topology, bad_projection, bad_state)

    def test_duplicate_prompt_ids_fail_closed(self):
        topology, projection, state = fixture()
        topology['nodes'].append(dict(topology['nodes'][0]))
        rebind_topology(topology, state)
        with self.assertRaisesRegex(mod.ViewerBuildError, 'duplicate'):
            mod.validate_inputs(topology, projection, state)

    def test_duplicate_partition_membership_fails_closed(self):
        topology, projection, state = fixture()
        topology['clusters'][0]['member_prompt_ids'].append('P00')
        topology['clusters'][0]['member_count'] = 3
        rebind_topology(topology, state)
        with self.assertRaisesRegex(mod.ViewerBuildError, 'partition'):
            mod.validate_inputs(topology, projection, state)

    def test_projection_hash_tamper_fails_closed(self):
        topology, projection, state = fixture()
        bad_projection = json.loads(json.dumps(projection))
        bad_projection['points']['P00']['x'] = 0.9
        with self.assertRaisesRegex(mod.ViewerBuildError, 'projection/state'):
            mod.validate_inputs(topology, bad_projection, state)

    def test_output_path_cannot_equal_any_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            topology = root / 'topology.json'
            projection = root / 'projection.json'
            state = root / 'state.json'
            for path in (topology, projection, state):
                path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(mod.ViewerBuildError, 'must not equal input'):
                mod.validate_output_path(topology, (topology, projection, state))

    def test_external_overwrite_creates_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_root = root / 'Outputs'
            backup_root = outputs_root / 'backups'
            external = root / 'viewer.html'
            external.write_text('previous viewer', encoding='utf-8')
            backup = mod.backup_existing_external_output(
                external,
                outputs_root=outputs_root,
                backup_root=backup_root,
            )
            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertTrue(backup.is_file())
            self.assertEqual(backup.read_text(encoding='utf-8'), 'previous viewer')
            self.assertEqual(external.read_text(encoding='utf-8'), 'previous viewer')

    def test_viewer_source_has_no_collection_or_persistence_apis(self):
        source = (ROOT / 'docs/prompt-topology-viewer.js').read_text(encoding='utf-8')
        for forbidden in ('fetch(', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'sendBeacon', 'localStorage', 'sessionStorage'):
            self.assertNotIn(forbidden, source)

    def test_viewer_source_clamps_hover_and_refreshes_cleared_search(self):
        source = (ROOT / 'docs/prompt-topology-viewer.js').read_text(encoding='utf-8')
        self.assertIn('Math.max(8,stage.width-290)', source)
        self.assertIn('Math.max(8,stage.height-54)', source)
        self.assertIn('renderDetail(null);renderClusters();return;', source)

    def test_contract_preserves_semantic_boundary(self):
        contract = json.loads((ROOT / 'harness/prompt-topology/phase-c-viewer.v1.json').read_text())
        self.assertIn('projection-driven classification', contract['forbidden'])
        self.assertIn('registry mutation', contract['forbidden'])
        self.assertFalse(contract['privacy']['telemetry'])
        self.assertFalse(contract['privacy']['persistent_browser_storage'])


if __name__ == '__main__':
    unittest.main()
