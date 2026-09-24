"""tests/test_promote.py

Promotion into Active/ is controlled and logged.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from triage.promote import PromotionError, promote_to_active


def _make_xlsx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", b"<?xml version='1.0'?><Types/>")
        z.writestr("xl/worksheets/sheet1.xml", b"<?xml version='1.0'?><worksheet/>")
    return buf.getvalue()


def test_promote_refuses_non_deprecated_origin(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Active").mkdir()
    (tmp_path / "Deprecated").mkdir()

    src = tmp_path / "Deprecated" / "work.xlsx"
    src.write_bytes(_make_xlsx_bytes())

    with pytest.raises(PromotionError) as exc:
        promote_to_active(origin_deprecated_path=tmp_path / "Candidates" / "x.xlsx", source_path=src)
    assert "Deprecated" in str(exc.value)


def test_promote_refuses_source_in_active(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Active").mkdir()
    (tmp_path / "Deprecated").mkdir()

    origin = tmp_path / "Deprecated" / "orig.xlsx"
    origin.write_bytes(_make_xlsx_bytes())
    src_active = tmp_path / "Active" / "already.xlsx"
    src_active.write_bytes(_make_xlsx_bytes())

    with pytest.raises(PromotionError) as exc:
        promote_to_active(origin_deprecated_path=origin, source_path=src_active)
    assert "already under Active" in str(exc.value)


def test_promote_copies_and_logs(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Active").mkdir()
    (tmp_path / "Deprecated").mkdir()
    (tmp_path / "Outputs").mkdir()

    origin = tmp_path / "Deprecated" / "gold.xlsx"
    src = tmp_path / "Deprecated" / "gold.xlsx"
    src.write_bytes(_make_xlsx_bytes())

    r = promote_to_active(origin_deprecated_path=origin, source_path=src)

    dest = Path(r.dest_path)
    assert dest.exists()
    assert dest.parent.name == "Active"
    assert dest.name == "gold.xlsx"
    assert r.src_sha256 == r.dest_sha256

    report = Path(r.report_path)
    assert report.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["endeavor"] == "PROMOTE_TO_ACTIVE"
    assert payload["sha_match"] is True


def test_promote_refuses_collision_without_overwrite(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAGE_REPO_ROOT", str(tmp_path))
    (tmp_path / "Active").mkdir()
    (tmp_path / "Deprecated").mkdir()

    origin = tmp_path / "Deprecated" / "gold.xlsx"
    src = tmp_path / "Deprecated" / "gold.xlsx"
    src.write_bytes(_make_xlsx_bytes())
    (tmp_path / "Active" / "gold.xlsx").write_bytes(b"old")

    with pytest.raises(PromotionError) as exc:
        promote_to_active(origin_deprecated_path=origin, source_path=src, allow_overwrite=False)
    assert "already exists" in str(exc.value)
