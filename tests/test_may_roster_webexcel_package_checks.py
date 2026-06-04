"""Web Excel package preflight gate tests."""
from __future__ import annotations

from tests.fixtures.may_roster_webexcel.builders import (
    build_clean_simple_workbook,
    build_formula_workbook,
    inject_text_into_sheet,
)
from triage.may_roster_webexcel.package_checks import run_package_preflight


def test_clean_workbook_passes(tmp_path):
    p = build_clean_simple_workbook(str(tmp_path / "clean.xlsx"))
    res = run_package_preflight(p)
    assert res.passed, res.to_dict()
    assert "manual open confirmation still required" in res.message.lower()


def test_namespace_leakage_flagged(tmp_path):
    src = build_clean_simple_workbook(str(tmp_path / "clean.xlsx"))
    bad = inject_text_into_sheet(src, str(tmp_path / "ns.xlsx"), "ns0:")
    res = run_package_preflight(bad)
    assert not res.passed
    assert res.findings.get("namespace_leakage")


def test_function_namespace_token_flagged(tmp_path):
    src = build_clean_simple_workbook(str(tmp_path / "clean.xlsx"))
    bad = inject_text_into_sheet(src, str(tmp_path / "fn.xlsx"), "_xlfn.")
    res = run_package_preflight(bad)
    assert not res.passed
    assert res.findings.get("function_namespace_tokens")


def test_missing_file():
    res = run_package_preflight("does_not_exist_12345.xlsx")
    assert not res.passed
    assert "file_not_found" in res.errors


def test_sharesafe_rejects_formula(tmp_path):
    p = build_formula_workbook(str(tmp_path / "formula.xlsx"))
    res = run_package_preflight(p, sharesafe=True)
    assert not res.passed
    assert res.findings.get("formula_in_sharesafe")


def test_formula_workbook_allowed_when_not_sharesafe(tmp_path):
    p = build_formula_workbook(str(tmp_path / "formula.xlsx"))
    res = run_package_preflight(p, sharesafe=False)
    # Not asserting pass/fail on gates here, only that share-safe purity is
    # not enforced when sharesafe=False.
    assert not res.findings.get("formula_in_sharesafe")
