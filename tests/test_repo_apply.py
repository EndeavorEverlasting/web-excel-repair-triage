"""tests/test_repo_apply.py

Apply-recommendations is opt-in but must be safe:
- copy by default
- overwrite requires confirmation
- overwrite creates backups
"""

from __future__ import annotations

import json
from pathlib import Path


from triage.repo_apply import apply_recommendations


def test_apply_import_to_deprecated_copies_and_reports(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Deprecated").mkdir()
    (tmp_path / "Outputs").mkdir()

    src = tmp_path / "loose.xlsx"
    src.write_bytes(b"xlsxbytes")
    recs = [
        {
            "action": "IMPORT_TO_DEPRECATED",
            "path": str(src),
            "reason": "import",
            "suggested_dest": str(tmp_path / "Deprecated" / "loose.xlsx"),
        }
    ]

    r = apply_recommendations(recs, selected_actions=["IMPORT_TO_DEPRECATED"])
    assert (tmp_path / "Deprecated" / "loose.xlsx").exists()
    report = Path(r.report_path)
    assert report.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["endeavor"] == "APPLY_REPO_RECOMMENDATIONS"


def test_apply_overwrite_requires_confirmation_and_creates_backup(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Outputs").mkdir()
    (tmp_path / "Deprecated").mkdir()

    src = tmp_path / "Deprecated" / "a.txt"
    src.write_text("new", encoding="utf-8")
    dest = tmp_path / "Outputs" / "legacy" / "a.txt"
    dest.parent.mkdir(parents=True)
    dest.write_text("old", encoding="utf-8")

    recs = [
        {
            "action": "RELOCATE_DEPRECATED_ARTIFACT_TO_OUTPUTS",
            "path": str(src),
            "reason": "relocate",
            "suggested_dest": str(dest),
        }
    ]

    # Wrong phrase: skip
    r1 = apply_recommendations(
        recs,
        selected_actions=["RELOCATE_DEPRECATED_ARTIFACT_TO_OUTPUTS"],
        allow_overwrite=True,
        confirmation_phrase="NO",
    )
    assert r1.summary["ok"] == 0
    assert r1.summary["skipped"] == 1

    # Correct phrase: overwrite + backup
    r2 = apply_recommendations(
        recs,
        selected_actions=["RELOCATE_DEPRECATED_ARTIFACT_TO_OUTPUTS"],
        allow_overwrite=True,
        confirmation_phrase="OVERWRITE",
    )
    assert r2.summary["ok"] == 1
    assert dest.read_text(encoding="utf-8") == "new"

    backups = list((tmp_path / "Outputs" / "backups").rglob("*a.txt"))
    assert backups, "expected a backup file to be created"


def test_apply_budget_skips_outputs_over_budget(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Outputs").mkdir()
    (tmp_path / "Deprecated").mkdir()

    src = tmp_path / "Deprecated" / "big.bin"
    src.write_bytes(b"x" * 2048)
    dest = tmp_path / "Outputs" / "big.bin"
    recs = [
        {
            "action": "RELOCATE_DEPRECATED_ARTIFACT_TO_OUTPUTS",
            "path": str(src),
            "reason": "relocate",
            "suggested_dest": str(dest),
        }
    ]

    r = apply_recommendations(
        recs,
        selected_actions=["RELOCATE_DEPRECATED_ARTIFACT_TO_OUTPUTS"],
        budget_root="Outputs",
        budget_bytes=1024,
    )
    assert r.summary["ok"] == 0
    assert r.summary["skipped"] == 1
    assert not dest.exists()
