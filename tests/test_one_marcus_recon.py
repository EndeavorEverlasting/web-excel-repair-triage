"""Tests for the 1 Marcus recon part-number relink engine (sanitized fixtures)."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

from tests.fixtures.one_marcus_recon import fixtures as fx
from triage.one_marcus_recon import date_inference as di
from triage.one_marcus_recon import formula_relink as fr
from triage.one_marcus_recon import preflight as pf
from triage.one_marcus_recon.config import PART_NUMBERS_SHEET
from triage.one_marcus_recon.exporter import run_recon
from triage.one_marcus_recon.package_cleanup import Package

STABLE_TAB = PART_NUMBERS_SHEET
DATED_INFERRED_TAB = "5-28-2026 Part Numbers"
_DATED_PN_SHEET = re.compile(r"^\d{1,2}-\d{1,2}-\d{4} Part Numbers$")
REAL_WB = Path("Candidates/inventory recon/WEBSAFE_Tab-Linked_1_Marcus_Compiled_Recon_Integrated_5-28-2026_PARTNUMBERS_LINKED_CANDIDATE_v2.xlsx")


def _names(path: str):
    with zipfile.ZipFile(path) as z:
        return z.namelist()


def _all_text(path: str) -> str:
    blob = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith(".xml") or n.endswith(".rels"):
                blob.append(z.read(n).decode("utf-8", "ignore"))
    return "".join(blob)


def _assert_no_dated_part_numbers_tabs(sheet_names: list[str]) -> None:
    assert not any(_DATED_PN_SHEET.match(n) for n in sheet_names)


@pytest.fixture
def stale_input(tmp_path):
    return fx.make_stale_recon(str(tmp_path / "1 Marcus Recon Integrated 5-28-2026.xlsx"))


@pytest.fixture
def output_path(tmp_path):
    return str(tmp_path / "out" / "1_Marcus_Recon_2026-05-28_WEBSAFE.xlsx")


def test_stale_fixture_workbook_xml_is_namespace_valid(stale_input):
    with zipfile.ZipFile(stale_input) as archive:
        ET.fromstring(archive.read("xl/workbook.xml"))


def test_infers_recon_update_date_from_filename(stale_input):
    pkg = Package.from_path(stale_input)
    names = fr.workbook_sheet_names(pkg.text("xl/workbook.xml"))
    chosen, _cands, _warn = di.infer_update_date(stale_input, "auto", names)
    assert chosen.date_iso == "2026-05-28"
    assert chosen.source == "filename"
    assert chosen.tab_label == DATED_INFERRED_TAB


def test_renames_part_number_tab_to_stable_name(stale_input, output_path):
    result = run_recon(stale_input, output_path=output_path, cli_date="auto")
    assert result.report.final_part_number_tab == STABLE_TAB
    assert result.report.baseline_compare_pass is True
    assert result.report.renamed_tabs == [f"5-07-2026 Part Numbers -> {STABLE_TAB}"]
    with zipfile.ZipFile(output_path) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8")
    assert f'name="{STABLE_TAB}"' in wb or f"name='{STABLE_TAB}'" in wb
    assert "5-07-2026 Part Numbers" not in wb
    _assert_no_dated_part_numbers_tabs(fr.workbook_sheet_names(wb))


def test_rewrites_formulas_from_old_part_number_tab(stale_input, output_path):
    result = run_recon(stale_input, output_path=output_path, cli_date="auto")
    assert result.report.formula_cells_patched > 0
    text = _all_text(output_path)
    assert f"'{STABLE_TAB}'!" in text
    assert "'5-07-2026 Part Numbers'!" not in text


def test_localizes_external_part_number_formulas(stale_input, output_path):
    run_recon(stale_input, output_path=output_path, cli_date="auto")
    text = _all_text(output_path)
    assert "[1]'" not in text
    assert f"'{STABLE_TAB}'!$A$1" in text


def test_removes_external_link_parts_after_localization(stale_input, output_path):
    result = run_recon(stale_input, output_path=output_path, cli_date="auto")
    assert any("externalLinks" in p for p in result.report.external_link_parts_removed)
    assert not [n for n in _names(output_path) if n.startswith("xl/externalLinks/")]
    assert "externalLink" not in _all_text(output_path)


def test_removes_calc_chain_after_formula_patch(stale_input, output_path):
    result = run_recon(stale_input, output_path=output_path, cli_date="auto")
    assert result.report.calc_chain_removed is True
    assert "xl/calcChain.xml" not in _names(output_path)


def test_preserves_unrelated_tabs_and_sheet_order(stale_input, output_path):
    before = fr.workbook_sheet_names(Package.from_path(stale_input).text("xl/workbook.xml"))
    run_recon(stale_input, output_path=output_path, cli_date="auto")
    after = fr.workbook_sheet_names(Package.from_path(output_path).text("xl/workbook.xml"))
    expected = [STABLE_TAB if n == "5-07-2026 Part Numbers" else n for n in before]
    assert after == expected
    assert "Notes" in after and "README Integration" in after


def test_dry_run_reports_without_output_write(stale_input, output_path):
    result = run_recon(stale_input, output_path=output_path, cli_date="auto", dry_run=True)
    assert result.report.dry_run is True
    assert result.report.formula_cells_patched > 0
    assert not Path(output_path).exists()
    assert result.outputs == {}


def test_warns_on_ambiguous_date_candidates(tmp_path):
    src = fx.make_ambiguous(str(tmp_path / "1 Marcus Recon Integrated.xlsx"))
    result = run_recon(src, output_path=str(tmp_path / "amb_WEBSAFE.xlsx"), cli_date="auto")
    assert any("ambiguous" in w for w in result.report.warnings)
    pkg = Package.from_path(src)
    names = fr.workbook_sheet_names(pkg.text("xl/workbook.xml"))
    with pytest.raises(di.AmbiguousDateError):
        di.infer_update_date(src, "auto", names, strict=True)


def test_webexcel_preflight_rejects_stale_refs_and_stopship_tokens(stale_input, output_path):
    pre_in = pf.run_preflight(stale_input, target_part_number_tab=STABLE_TAB)
    assert pre_in.preflight_pass is False
    assert pre_in.has_calc_chain and pre_in.external_link_parts
    result = run_recon(stale_input, output_path=output_path, cli_date="auto")
    assert result.report.webexcel_preflight_pass is True
    pre_out = pf.run_preflight(output_path, target_part_number_tab=STABLE_TAB)
    assert pre_out.preflight_pass is True
    assert not pre_out.stale_dated_refs


@pytest.mark.skipif(not REAL_WB.exists(), reason="private real workbook not present")
def test_real_workbook_idempotent_regression(tmp_path):
    out = str(tmp_path / "real_1_Marcus_Recon_2026-05-28_WEBSAFE.xlsx")
    before = fr.workbook_sheet_names(Package.from_path(str(REAL_WB)).text("xl/workbook.xml"))
    result = run_recon(str(REAL_WB), output_path=out, cli_date="2026-05-28")
    after = fr.workbook_sheet_names(Package.from_path(out).text("xl/workbook.xml"))
    expected = [STABLE_TAB if _DATED_PN_SHEET.match(n) else n for n in before]
    assert after == expected
    assert STABLE_TAB in after
    _assert_no_dated_part_numbers_tabs(after)
    names = _names(out)
    assert any(n.startswith("xl/tables/table") for n in names)
    assert any(n.startswith("xl/drawings/drawing") for n in names)
    assert result.report.webexcel_preflight_pass is True
    assert result.report.final_part_number_tab == STABLE_TAB
