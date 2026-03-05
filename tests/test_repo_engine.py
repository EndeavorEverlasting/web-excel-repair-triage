"""tests/test_repo_engine.py

Repo scanning/classification engine is non-destructive and respects repo root
folder semantics.
"""

from __future__ import annotations

from pathlib import Path

from triage.repo_engine import scan_repo, recommend, RepoItem


def test_scan_repo_classifies_by_folder(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    for d in ("Active", "Deprecated", "Candidates", "Repaired", "Outputs"):
        (tmp_path / d).mkdir(parents=True)

    (tmp_path / "Active" / "gold.xlsx").write_bytes(b"not-a-real-xlsx")
    (tmp_path / "Deprecated" / "work.xlsx").write_bytes(b"not-a-real-xlsx")
    (tmp_path / "Outputs" / "report.json").write_text("{}", encoding="utf-8")

    res = scan_repo(root=tmp_path, run_gates=False, max_files=1000)
    buckets = {Path(i.path).name: i.folder_bucket for i in res.items}
    assert buckets["gold.xlsx"] == "active"
    assert buckets["work.xlsx"] == "deprecated"
    assert buckets["report.json"] == "outputs"


def test_scan_repo_recommends_import_for_unknown_xlsx(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Deprecated").mkdir(parents=True)
    (tmp_path / "stray.xlsx").write_bytes(b"not-a-real-xlsx")

    res = scan_repo(root=tmp_path, run_gates=False, max_files=1000)
    actions = [r.action for r in res.recommendations]
    assert "IMPORT_TO_DEPRECATED" in actions


def test_recommend_flags_promotion_candidate_when_gates_pass(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Active").mkdir(parents=True)
    (tmp_path / "Deprecated").mkdir(parents=True)

    it = RepoItem(
        path=str(tmp_path / "Deprecated" / "ok.xlsx"),
        relpath="Deprecated/ok.xlsx",
        folder_bucket="deprecated",
        role="work",
        ext=".xlsx",
        size=1,
        mtime=0.0,
        gate={"pass": True, "failing_gates": {}},
    )
    recs = recommend([it])
    assert any(r.action == "PROMOTION_CANDIDATE" for r in recs)
