"""triage/web_excel_browser.py
--------------------------------
Browser-based Excel-for-Web probe.

Why this exists
---------------
The repo already provides a strong **web compatibility** check via
`triage/graph_probe.py` (upload -> workbook session -> list worksheets -> range
read). That validates the Excel-for-Web backend without driving a browser.

Some workflows also want a **real browser UI smoke-test**: open the workbook
link, verify a worksheet UI is present, detect any repair banner messaging, and
then close the browser — all under a strict time budget.

Implementation
--------------
This module uses Playwright *if installed*. It is intentionally optional so the
core engine remains stdlib-only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


try:  # optional dependency
    from playwright.sync_api import sync_playwright  # type: ignore
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # type: ignore

    _PW_OK = True
except Exception:  # pragma: no cover
    sync_playwright = None  # type: ignore
    PlaywrightTimeoutError = Exception  # type: ignore
    _PW_OK = False


def _now_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _safe_stem(s: str) -> str:
    s = s.strip()
    if not s:
        return "web"
    # Prefer last URL segment if this looks like a URL.
    if "://" in s:
        try:
            s = s.split("?", 1)[0].rstrip("/")
            s = s.rsplit("/", 1)[-1] or "web"
        except Exception:
            pass
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s.strip("._-") or "web"


@dataclass
class WebExcelBrowserResult:
    url: str
    out_dir: str
    success: bool = False
    opened: bool = False
    needs_login: bool = False
    sheet_observed: bool = False
    repair_banner_detected: bool = False
    worksheet_tabs: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    mode: Optional[str] = None
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: Optional[float] = None
    timed_out: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "out_dir": self.out_dir,
            "success": self.success,
            "opened": self.opened,
            "needs_login": self.needs_login,
            "sheet_observed": self.sheet_observed,
            "repair_banner_detected": self.repair_banner_detected,
            "worksheet_tabs": self.worksheet_tabs,
            "evidence": self.evidence,
            "mode": self.mode,
            "timeline": self.timeline,
            "elapsed_seconds": self.elapsed_seconds,
            "timed_out": self.timed_out,
            "error": self.error,
        }


_REPAIR_TEXT_MARKERS = [
    "we found a problem with some content",
    "workbook repaired",
    "fix this workbook",
    "we fixed",
    "repaired",
]


def probe_open_in_web_excel(
    url: str,
    out_root: str = "Outputs/web_runs",
    out_dir_override: Optional[str] = None,
    timeout_seconds: int = 15,
    headless: bool = False,
    user_data_dir: Optional[str] = None,
    browser: str = "chromium",
    channel: Optional[str] = None,
    take_screenshot: bool = True,
) -> WebExcelBrowserResult:
    """Open *url* in a browser and look for evidence a worksheet UI is loaded.

    Notes
    -----
    - This is a *smoke test*, not a structural validator.
    - For backend validation without a browser, prefer `triage/graph_probe.py`.
    """

    started = time.time()

    if out_dir_override:
        out_dir = Path(out_dir_override)
    else:
        out_dir = Path(out_root) / f"{_safe_stem(url)[:60]}_{_now_ts()}"
    out_dir.mkdir(parents=True, exist_ok=True)

    r = WebExcelBrowserResult(url=url, out_dir=str(out_dir))

    if not _PW_OK:
        r.error = (
            "Playwright is not installed. Install it to enable browser probing. "
            "Suggested commands: pip install playwright && python -m playwright install"
        )
        r.elapsed_seconds = round(time.time() - started, 3)
        (out_dir / "web_excel_probe_report.json").write_text(json.dumps(r.to_dict(), indent=2), encoding="utf-8")
        return r

    try:
        with sync_playwright() as pw:  # type: ignore[misc]
                btype = getattr(pw, browser)
                browser_obj = None

                # Persistent context allows using an existing signed-in session.
                if user_data_dir:
                    ctx = btype.launch_persistent_context(
                        user_data_dir=os.fspath(Path(user_data_dir)),
                        headless=headless,
                        channel=channel,
                    )
                    page = ctx.new_page()
                else:
                    browser_obj = btype.launch(headless=headless, channel=channel)
                    ctx = browser_obj.new_context()
                    page = ctx.new_page()

                try:
                    # Timebox everything.
                    ms = max(1000, int(timeout_seconds * 1000))
                    page.set_default_timeout(ms)

                    # Navigate.
                    page.goto(url, wait_until="domcontentloaded", timeout=ms)
                    r.opened = True

                    # Poll quickly for sheet-vs-login state within the hard budget.
                    deadline = started + float(max(1, int(timeout_seconds)))
                    poll_ms = 500
                    last_title = ""
                    last_url = ""
                    last_grid = 0
                    last_tab = 0
                    last_needs_login = False
                    last_repair = False
                    tabs: List[str] = []

                    while True:
                        now = time.time()
                        if now > deadline:
                            break

                        try:
                            last_title = page.title() or ""
                        except Exception:
                            pass

                        try:
                            last_url = page.url or ""
                        except Exception:
                            pass

                        # Detect login wall (heuristic).
                        login = False
                        try:
                            if page.locator("input[type='password']").count() > 0:
                                login = True
                            if page.locator("input[name='passwd']").count() > 0:
                                login = True
                            if page.locator("text=Sign in").count() > 0:
                                login = True
                            if page.locator("text=Stay signed in").count() > 0:
                                login = True
                        except Exception:
                            pass
                        last_needs_login = bool(login)

                        # Worksheet UI heuristics.
                        grid_count = 0
                        tab_count = 0
                        try:
                            grid_count = int(page.locator("[role='grid']").count())
                        except Exception:
                            grid_count = 0
                        try:
                            tab_count = int(page.locator("[role='tab']").count())
                        except Exception:
                            tab_count = 0
                        last_grid, last_tab = int(grid_count), int(tab_count)

                        # Repair banner detection: scan for common marker text.
                        repair = False
                        try:
                            for marker in _REPAIR_TEXT_MARKERS:
                                if page.locator(f"text={marker}").count() > 0:
                                    repair = True
                                    break
                        except Exception:
                            repair = False
                        last_repair = bool(repair)

                        # Tab labels (best-effort; can be expensive so only do once we see tabs)
                        if tab_count > 0 and not tabs:
                            try:
                                raw_tabs = page.locator("[role='tab']").all_text_contents()
                                tabs = [t.strip() for t in raw_tabs if (t or "").strip()][:25]
                            except Exception:
                                tabs = []

                        mode = "login" if last_needs_login else (
                            "sheet" if (last_grid > 0 or last_tab > 0) else "unknown"
                        )
                        r.timeline.append(
                            {
                                "t": round(now - started, 3),
                                "url": last_url,
                                "title": last_title,
                                "grid_count": last_grid,
                                "tab_count": last_tab,
                                "needs_login": last_needs_login,
                                "repair_banner_detected": last_repair,
                                "mode": mode,
                            }
                        )

                        # Early stop as soon as we have a decisive state.
                        if last_needs_login or (last_grid > 0 or last_tab > 0):
                            break

                        # Keep polling until deadline.
                        try:
                            page.wait_for_timeout(poll_ms)
                        except Exception:
                            break

                    # Final derived state from last sample.
                    title = last_title
                    final_url = last_url
                    r.needs_login = bool(last_needs_login)
                    r.worksheet_tabs = list(tabs)
                    r.repair_banner_detected = bool(last_repair)
                    r.sheet_observed = (not r.needs_login) and (last_grid > 0 or last_tab > 0)
                    r.mode = "login" if r.needs_login else ("sheet" if r.sheet_observed else "unknown")
                    r.success = r.sheet_observed and (not r.repair_banner_detected)
                    r.evidence = {
                        "title": title,
                        "final_url": final_url,
                        "grid_count": int(last_grid),
                        "tab_count": int(last_tab),
                        "browser": browser,
                        "channel": channel,
                        "headless": headless,
                        "user_data_dir": user_data_dir,
                        "timeline_len": len(r.timeline),
                    }

                    # Save extra artifacts for audit/debug.
                    try:
                        (out_dir / "page_title.txt").write_text(title or "", encoding="utf-8")
                        (out_dir / "page_url.txt").write_text(final_url or "", encoding="utf-8")
                    except Exception:
                        pass

                    try:
                        body_text = page.inner_text("body")
                        (out_dir / "page_text_excerpt.txt").write_text((body_text or "")[:20000], encoding="utf-8")
                    except Exception:
                        pass

                    if take_screenshot:
                        try:
                            page.screenshot(path=str(out_dir / "web_excel.png"), full_page=False)
                        except Exception:
                            pass
                finally:
                    # Always close.
                    try:
                        ctx.close()
                    except Exception:
                        pass
                    try:
                        if browser_obj is not None:
                            browser_obj.close()
                    except Exception:
                        pass

    except PlaywrightTimeoutError as e:  # type: ignore[misc]
        r.timed_out = True
        r.error = f"Timeout: {e}"
    except Exception as e:
        r.error = f"{type(e).__name__}: {e}"

    r.elapsed_seconds = round(time.time() - started, 3)
    (out_dir / "web_excel_probe_report.json").write_text(json.dumps(r.to_dict(), indent=2), encoding="utf-8")
    return r


def probe_open_in_web_excel_isolated(
    url: str,
    out_root: str = "Outputs/web_runs",
    timeout_seconds: int = 15,
    headless: bool = False,
    user_data_dir: Optional[str] = None,
    browser: str = "chromium",
    channel: Optional[str] = None,
    take_screenshot: bool = True,
) -> WebExcelBrowserResult:
    """Run the browser probe in a subprocess to enforce a hard wall-clock timeout."""

    out_dir = Path(out_root) / f"{_safe_stem(url)[:60]}_{_now_ts()}_isolated"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "triage.web_excel_browser_worker",
        "--url",
        url,
        "--out-dir",
        str(out_dir),
        "--timeout",
        str(int(timeout_seconds)),
        "--browser",
        browser,
    ]
    if headless:
        cmd.append("--headless")
    if channel:
        cmd += ["--channel", channel]
    if user_data_dir:
        cmd += ["--user-data-dir", user_data_dir]
    if not take_screenshot:
        cmd.append("--no-screenshot")

    def _kill_process_tree(pid: int) -> None:
        """Best-effort kill of the worker *and its child processes* (browser).

        On Windows this uses `taskkill /T` which is the most reliable way to ensure
        any spawned msedge/chromium processes are also terminated.
        """

        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except Exception:
                pass

    hard_timeout = max(2, int(timeout_seconds) + 1)

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd(),
        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
    )

    try:
        stdout, stderr = p.communicate(timeout=hard_timeout)
    except subprocess.TimeoutExpired:
        _kill_process_tree(p.pid)
        r = WebExcelBrowserResult(url=url, out_dir=str(out_dir), timed_out=True, error="Timed out (subprocess)")
        (out_dir / "worker_stdout.txt").write_text("", encoding="utf-8")
        (out_dir / "worker_stderr.txt").write_text("Timed out (subprocess)\n", encoding="utf-8")
        (out_dir / "web_excel_probe_report.json").write_text(json.dumps(r.to_dict(), indent=2), encoding="utf-8")
        return r
    finally:
        # Defensive: ensure the worker isn't left behind.
        try:
            if p.poll() is None:
                _kill_process_tree(p.pid)
        except Exception:
            pass

    (out_dir / "worker_stdout.txt").write_text(stdout or "", encoding="utf-8")
    (out_dir / "worker_stderr.txt").write_text(stderr or "", encoding="utf-8")

    # Worker always writes a report; prefer reading from disk.
    report = out_dir / "web_excel_probe_report.json"
    if report.exists():
        return WebExcelBrowserResult(**json.loads(report.read_text(encoding="utf-8")))

    # Fallback: parse stdout as dict.
    if (stdout or "").strip():
        try:
            return WebExcelBrowserResult(**json.loads(stdout))
        except Exception:
            pass
    return WebExcelBrowserResult(url=url, out_dir=str(out_dir), success=False, opened=False, error=(stderr or "")[:500])
