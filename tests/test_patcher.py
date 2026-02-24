"""
tests/test_patcher.py
---------------------
Unit tests for triage.patcher — focused on the stub-skip behaviour introduced
to handle <REVIEW_REQUIRED> and <FILL_IN_*> placeholder patches gracefully.

Test matrix
-----------
  T1  clean recipe (valid match)       → returns output path, no exception
  T2  stubs only (REVIEW_REQUIRED)     → PatchWarning raised, file written
  T3  stubs only (FILL_IN_* variants)  → PatchWarning raised, file written
  T4  stubs + valid real patch         → PatchWarning raised, real patch applied
  T5  bad literal match (no stub)      → PatchError raised
  T6  delete_part removes entry        → entry absent in output zip
  T7  mixed: stubs + bad real match    → PatchError raised (not PatchWarning)
"""
from __future__ import annotations
import io
import zipfile
import tempfile
import os
import pytest

from triage.patcher import apply_recipe, PatchError, PatchWarning, STUB_PLACEHOLDERS


# ─────────────────────────── helpers ────────────────────────────────────────

_SHEET1 = b'<?xml version="1.0"?><worksheet><sheetData><row r="1"><c r="A1"><v>HELLO</v></c></row></sheetData></worksheet>'
_STYLES = b'<?xml version="1.0"?><styleSheet><dxfs count="0"/></styleSheet>'


def _make_xlsx(extra_parts: dict[str, bytes] | None = None) -> bytes:
    """Build a minimal in-memory .xlsx ZIP for testing."""
    parts: dict[str, bytes] = {
        "[Content_Types].xml": b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        "xl/worksheets/sheet1.xml": _SHEET1,
        "xl/styles.xml": _STYLES,
        "xl/calcChain.xml": b'<?xml version="1.0"?><calcChain><c r="A1" i="1"/></calcChain>',
    }
    if extra_parts:
        parts.update(extra_parts)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    return buf.getvalue()


def _write_tmp(data: bytes) -> str:
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(data)
    return path


def _read_part(out_path: str, part_name: str) -> bytes:
    with zipfile.ZipFile(out_path, "r") as z:
        return z.read(part_name)


# ─────────────────────────── test cases ─────────────────────────────────────

def test_t1_clean_recipe_returns_path(tmp_path):
    """T1: Valid literal_replace returns output path with no exception."""
    src = _write_tmp(_make_xlsx())
    out = str(tmp_path / "out.xlsx")
    recipe = {"patches": [{"id": "p01", "part": "xl/worksheets/sheet1.xml",
                            "operation": "literal_replace",
                            "match": "HELLO", "replacement": "WORLD", "occurrence": 1}]}
    result = apply_recipe(src, recipe, out)
    assert result == out
    assert b"WORLD" in _read_part(out, "xl/worksheets/sheet1.xml")
    assert b"HELLO" not in _read_part(out, "xl/worksheets/sheet1.xml")


def test_t2_review_required_stubs_raise_patch_warning(tmp_path):
    """T2: REVIEW_REQUIRED stubs → PatchWarning, output file written."""
    src = _write_tmp(_make_xlsx())
    out = str(tmp_path / "out.xlsx")
    recipe = {"patches": [
        {"id": "pfa66d0", "part": "xl/worksheets/sheet1.xml",
         "operation": "literal_replace",
         "description": "CF_DXFID_CLONE — Manual review required.",
         "match": "<REVIEW_REQUIRED>", "replacement": "<REVIEW_REQUIRED>", "occurrence": 1},
        {"id": "pa01f5f", "part": "xl/styles.xml",
         "operation": "literal_replace",
         "description": "SHARED_REF_TRIM — Manual review required.",
         "match": "<REVIEW_REQUIRED>", "replacement": "<REVIEW_REQUIRED>", "occurrence": 1},
    ]}
    with pytest.raises(PatchWarning) as exc_info:
        apply_recipe(src, recipe, out)
    pw = exc_info.value
    assert len(pw.skipped) == 2
    assert pw.output_path == out
    assert os.path.exists(out), "Output file must be written even when PatchWarning is raised"
    # Original data unchanged (stubs did nothing)
    assert b"HELLO" in _read_part(out, "xl/worksheets/sheet1.xml")


def test_t3_fill_in_stubs_raise_patch_warning(tmp_path):
    """T3: FILL_IN_* placeholder stubs are also treated as stubs."""
    src = _write_tmp(_make_xlsx())
    out = str(tmp_path / "out.xlsx")
    recipe = {"patches": [
        {"id": "p01", "part": "xl/worksheets/sheet1.xml",
         "operation": "literal_replace",
         "description": "Strip linefeed from tableColumn.",
         "match": "<FILL_IN_LINEFEED_VALUE>", "replacement": "<FILL_IN_CLEAN_VALUE>"},
    ]}
    with pytest.raises(PatchWarning) as exc_info:
        apply_recipe(src, recipe, out)
    assert len(exc_info.value.skipped) == 1
    assert os.path.exists(out)


def test_t4_stubs_plus_real_patch_raises_warning_but_applies_real(tmp_path):
    """T4: Stubs + real patch → PatchWarning raised AND real patch is applied."""
    src = _write_tmp(_make_xlsx())
    out = str(tmp_path / "out.xlsx")
    recipe = {"patches": [
        {"id": "pStub", "part": "xl/worksheets/sheet1.xml",
         "operation": "literal_replace",
         "match": "<REVIEW_REQUIRED>", "replacement": "<REVIEW_REQUIRED>"},
        {"id": "pReal", "part": "xl/worksheets/sheet1.xml",
         "operation": "literal_replace",
         "match": "HELLO", "replacement": "PATCHED"},
    ]}
    with pytest.raises(PatchWarning) as exc_info:
        apply_recipe(src, recipe, out)
    pw = exc_info.value
    assert len(pw.skipped) == 1
    assert b"PATCHED" in _read_part(out, "xl/worksheets/sheet1.xml"), \
        "Real patch must be applied even when stubs are also present"


def test_t5_bad_real_match_raises_patch_error(tmp_path):
    """T5: Real literal_replace with non-existent match → PatchError."""
    src = _write_tmp(_make_xlsx())
    out = str(tmp_path / "out.xlsx")
    recipe = {"patches": [
        {"id": "p01", "part": "xl/worksheets/sheet1.xml",
         "operation": "literal_replace",
         "match": "DOES_NOT_EXIST_IN_FILE", "replacement": "X"},
    ]}
    with pytest.raises(PatchError):
        apply_recipe(src, recipe, out)


def test_t6_delete_part_removes_entry(tmp_path):
    """T6: delete_part removes the ZIP entry."""
    src = _write_tmp(_make_xlsx())
    out = str(tmp_path / "out.xlsx")
    recipe = {"patches": [
        {"id": "p01", "part": "xl/calcChain.xml", "operation": "delete_part"},
    ]}
    result = apply_recipe(src, recipe, out)
    with zipfile.ZipFile(result, "r") as z:
        assert "xl/calcChain.xml" not in z.namelist()


def test_t7_mixed_stubs_and_bad_real_match_raises_patch_error(tmp_path):
    """T7: Stubs + bad real match → PatchError (hard failure wins over warning)."""
    src = _write_tmp(_make_xlsx())
    out = str(tmp_path / "out.xlsx")
    recipe = {"patches": [
        {"id": "pStub", "part": "xl/worksheets/sheet1.xml",
         "operation": "literal_replace",
         "match": "<REVIEW_REQUIRED>", "replacement": "<REVIEW_REQUIRED>"},
        {"id": "pBad", "part": "xl/worksheets/sheet1.xml",
         "operation": "literal_replace",
         "match": "DOES_NOT_EXIST", "replacement": "X"},
    ]}
    with pytest.raises(PatchError):
        apply_recipe(src, recipe, out)


def test_stub_placeholders_constant_coverage():
    """All three placeholder strings from report.py are registered."""
    assert "<REVIEW_REQUIRED>" in STUB_PLACEHOLDERS
    assert "<FILL_IN_LINEFEED_VALUE>" in STUB_PLACEHOLDERS
    assert "<FILL_IN_CLEAN_VALUE>" in STUB_PLACEHOLDERS

