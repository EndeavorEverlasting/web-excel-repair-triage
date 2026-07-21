from __future__ import annotations

import json
from pathlib import Path

from triage import harness_handoff, harness_operational_discipline as discipline, harness_operator_report

ROOT = Path(__file__).parents[1]


def test_repo_harness_manifest_exposes_every_required_surface() -> None:
    assert discipline.validate_repository(ROOT) == ()
    manifest = discipline.load_manifest(ROOT / 'configs/harness/harness_manifest_v1.json')
    assert manifest['entrypoint'] == 'HARNESS.md'
    assert manifest['agent_rules'] == ['AGENTS.md']
    assert len(manifest['scoped_skills']) == 3


def test_operator_report_and_handoff_are_machine_and_human_usable(tmp_path: Path) -> None:
    report = harness_operator_report.build_report(ROOT)
    assert report['valid'] is True
    context = {
        'repo': 'owner/repo',
        'branch_or_worktree': 'feat/example',
        'pr_or_sprint': 'PR #1',
        'lane': 'artifact',
        'owned_scope': 'generator and validator',
        'forbidden_scope': 'release',
        'expected_artifacts': 'workbook and manifest',
        'validation_order': 'focused then broad',
        'proof_ceiling': 'Excel for Web field acceptance',
    }
    text = harness_handoff.render(context, {'status': 'PASS', 'evidence': 'tests', 'git_state': 'clean', 'next_command': 'gh pr view 1 --web'})
    for section in ('CONTEXT', 'WORK COMMITTED', 'VALIDATION', 'BLOCKERS / GAPS', 'FINAL GIT STATE', 'NEXT COMMAND'):
        assert section in text
