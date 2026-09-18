"""Tests for git-tracked binary artifact hygiene."""
from __future__ import annotations

from triage.artifact_hygiene_policy import classify_path
from triage.gitignore_hygiene import scan_tracked_binaries


def test_attached_assets_not_tracked_on_clean_tip():
    report = scan_tracked_binaries()
    attached = [f for f in report.findings if f.path.startswith("attached_assets/")]
    assert not attached, attached


def test_fixture_allowlist_passes():
    report = scan_tracked_binaries(
        paths=[
            "tests/fixtures/cybernet_targets/mini_all_wave.xlsx",
            "README.md",
        ]
    )
    assert report.ok


def test_prompt_parallel_dispatch_manifest_is_control_plane_not_runtime_artifact():
    assert classify_path("Outputs/prompt-parallel-dispatch/manifest.json") is None


def test_prompt_parallel_dispatch_receipt_remains_runtime_artifact():
    finding = classify_path("Outputs/prompt-parallel-dispatch/receipt.json")
    assert finding is not None
    assert finding.reason == "generated_or_runtime_artifact"
