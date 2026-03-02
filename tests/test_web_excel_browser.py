from __future__ import annotations

from pathlib import Path

import pytest

from triage import web_excel_browser as w


def test_probe_graceful_when_playwright_missing(tmp_path):
    if w._PW_OK:
        pytest.skip("Playwright installed; this test covers the missing-dependency path")

    r = w.probe_open_in_web_excel(
        url="https://example.com",
        out_root=str(tmp_path),
        timeout_seconds=1,
        take_screenshot=False,
    )
    assert r.success is False
    assert r.opened is False
    assert r.error and "Playwright is not installed" in r.error
    assert Path(r.out_dir, "web_excel_probe_report.json").exists()


def test_probe_data_url_smoke_when_playwright_present(tmp_path):
    if not w._PW_OK:
        pytest.skip("Playwright not installed")

    r = w.probe_open_in_web_excel(
        url="data:text/html,<html><head><title>T</title></head><body>Hello</body></html>",
        out_root=str(tmp_path),
        timeout_seconds=5,
        headless=True,
        take_screenshot=False,
    )
    assert r.opened is True
    assert r.needs_login in (False, True)  # heuristic, but should not crash
    assert r.sheet_observed is False
    assert r.success is False
    assert Path(r.out_dir, "web_excel_probe_report.json").exists()


def test_isolated_probe_writes_report(tmp_path):
    r = w.probe_open_in_web_excel_isolated(
        url="data:text/html,<html><head><title>T</title></head><body>Hello</body></html>",
        out_root=str(tmp_path),
        timeout_seconds=5,
        headless=True,
        take_screenshot=False,
    )
    assert Path(r.out_dir).exists()
    assert Path(r.out_dir, "web_excel_probe_report.json").exists()
