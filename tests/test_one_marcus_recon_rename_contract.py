from __future__ import annotations

import zipfile

from tests.fixtures.one_marcus_recon import fixtures as fx
from triage.one_marcus_recon import formula_relink as fr
from triage.one_marcus_recon.config import PART_NUMBERS_SHEET
from triage.one_marcus_recon.exporter import run_recon
from triage.one_marcus_recon.package_cleanup import Package

STALE_TAB = "5-07-2026 Part Numbers"


def _run(tmp_path):
    source = fx.make_stale_recon(str(tmp_path / "1 Marcus Recon Integrated 5-28-2026.xlsx"))
    output = str(tmp_path / "out" / "1_Marcus_Recon_2026-05-28_WEBSAFE.xlsx")
    result = run_recon(source, output_path=output, cli_date="auto")
    return source, output, result


def _workbook_xml(path: str) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read("xl/workbook.xml").decode("utf-8")


def test_source_tab_selection_prefers_only_dated_candidate(tmp_path) -> None:
    source = fx.make_stale_recon(str(tmp_path / "1 Marcus Recon Integrated 5-28-2026.xlsx"))
    workbook_xml = Package.from_path(source).text("xl/workbook.xml")
    names = fr.workbook_sheet_names(workbook_xml)

    assert STALE_TAB in names
    assert fr.choose_source_tab(
        names,
        explicit_tab=None,
        chosen_date_iso="2026-05-28",
        target_label=PART_NUMBERS_SHEET,
    ) == STALE_TAB


def test_run_recon_reports_stable_tab_rename(tmp_path) -> None:
    _source, _output, result = _run(tmp_path)

    assert result.report.final_part_number_tab == PART_NUMBERS_SHEET
    assert result.report.renamed_tabs == [f"{STALE_TAB} -> {PART_NUMBERS_SHEET}"]


def test_output_workbook_contains_stable_tab(tmp_path) -> None:
    _source, output, _result = _run(tmp_path)
    workbook_xml = _workbook_xml(output)

    assert PART_NUMBERS_SHEET in fr.workbook_sheet_names(workbook_xml)


def test_output_workbook_removes_stale_tab(tmp_path) -> None:
    _source, output, _result = _run(tmp_path)
    workbook_xml = _workbook_xml(output)

    assert STALE_TAB not in fr.workbook_sheet_names(workbook_xml)
    assert STALE_TAB not in workbook_xml
