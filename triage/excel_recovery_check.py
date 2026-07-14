"""Automated Excel repair prompt detector.

Opens a workbook in Excel Desktop, detects whether the "Repaired" banner
appears in the window title, and returns a structured result.

Requires: Windows with Microsoft Excel installed, PowerShell 7+.

Usage (CLI):
    python -m triage.excel_recovery_check <file.xlsx>

Exit codes:
    0 = PASS (no repair detected)
    1 = FAIL (repair detected)
    2 = usage error
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional

EXCEL_PATH = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
MAX_WAIT = 12
POLL = 0.5


@dataclass
class RecoveryCheckResult:
    repair_detected: bool
    title: str
    elapsed: float
    file_path: str


def _kill_excel() -> None:
    subprocess.run(
        ["taskkill", "/F", "/IM", "EXCEL.EXE"],
        capture_output=True,
        timeout=5,
    )
    time.sleep(1.5)


def _get_excel_titles() -> list[str]:
    ps = subprocess.run(
        [
            "powershell", "-NoProfile", "-Command",
            "Get-Process -Name EXCEL -ErrorAction SilentlyContinue "
            "| Where-Object { $_.MainWindowTitle -ne '' } "
            "| Select-Object -ExpandProperty MainWindowTitle",
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return [t.strip() for t in ps.stdout.strip().splitlines() if t.strip()]


def check_excel_recovery(file_path: str) -> RecoveryCheckResult:
    """Open *file_path* in Excel and detect repair prompt via window title."""
    file_path = os.path.abspath(file_path)
    fname = os.path.splitext(os.path.basename(file_path))[0]

    _kill_excel()
    proc = subprocess.Popen([EXCEL_PATH, file_path])

    repair_detected = False
    title = ""
    elapsed = 0.0

    while elapsed < MAX_WAIT:
        time.sleep(POLL)
        elapsed += POLL

        titles = _get_excel_titles()
        for t in titles:
            if "Repaired" in t or "\u5df2\u4fee\u590d" in t:
                repair_detected = True
                title = t
                break
            if fname in t and not title:
                title = t

        if repair_detected:
            break
        if title and "Repaired" not in title:
            break

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
    _kill_excel()

    return RecoveryCheckResult(
        repair_detected=repair_detected,
        title=title,
        elapsed=round(elapsed, 1),
        file_path=file_path,
    )


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: python -m triage.excel_recovery_check <file.xlsx>")
        return 2

    result = check_excel_recovery(argv[0])
    status = "FAIL" if result.repair_detected else "PASS"
    print(
        f"{status} | repair={result.repair_detected} "
        f"| title='{result.title}' | {result.elapsed}s"
    )
    return 1 if result.repair_detected else 0


if __name__ == "__main__":
    sys.exit(main())
