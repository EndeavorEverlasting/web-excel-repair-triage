"""triage/excel_desktop.py
----------------------
Desktop Excel probe.

Goal
----
Open a candidate workbook in *desktop* Microsoft Excel, automatically handle
common corruption/recovery dialogs, capture screenshots, and collect the
Excel-generated recoveryLog XML (often saved as %TEMP%/error*.xml).

This is intentionally Windows-only.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import sys
import tempfile
import threading
import time
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


# ── Optional Windows/Excel deps (repo may run without them on non-Windows) ──
try:
    import pythoncom  # type: ignore
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32gui  # type: ignore
    import win32process  # type: ignore
    import win32com.client  # type: ignore

    _WIN_OK = True
except Exception:  # pragma: no cover
    pythoncom = None  # type: ignore
    win32api = None  # type: ignore
    win32con = None  # type: ignore
    win32gui = None  # type: ignore
    win32process = None  # type: ignore
    win32com = None  # type: ignore
    _WIN_OK = False

try:
    from PIL import ImageGrab  # type: ignore

    _PIL_OK = True
except Exception:  # pragma: no cover
    ImageGrab = None  # type: ignore
    _PIL_OK = False


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_stem(p: str) -> str:
    s = Path(p).stem
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s[:120] if len(s) > 120 else s


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _read_text_short(path: Path, limit: int = 4000) -> str:
    try:
        t = path.read_text(encoding="utf-8", errors="ignore")
        return t[:limit]
    except Exception:
        return ""


def list_recovery_log_candidates(search_dirs: Iterable[Path] | None = None) -> List[Path]:
    """Return possible Excel recovery logs (error*.xml) ordered by mtime desc."""
    if search_dirs is None:
        search_dirs = [Path(tempfile.gettempdir())]
    out: List[Path] = []
    for d in search_dirs:
        try:
            if d.exists():
                out.extend([p for p in d.glob("error*.xml") if p.is_file()])
        except Exception:
            continue
    out.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return out


def find_new_recovery_logs(
    since_epoch: float,
    search_dirs: Iterable[Path] | None = None,
) -> List[Path]:
    """Find error*.xml created/modified since *since_epoch* (unix time)."""
    logs = list_recovery_log_candidates(search_dirs=search_dirs)
    return [p for p in logs if p.stat().st_mtime >= since_epoch]


def _snapshot_errorxml_listing(search_dirs: Iterable[Path], limit: int = 50) -> List[Dict[str, Any]]:
    """Return a stable, JSON-serialisable listing of recent %TEMP%/error*.xml files."""
    rows: List[Dict[str, Any]] = []
    for p in list_recovery_log_candidates(search_dirs=search_dirs)[: int(limit)]:
        try:
            st = p.stat()
            rows.append(
                {
                    "path": str(p),
                    "mtime": float(st.st_mtime),
                    "size": int(st.st_size),
                }
            )
        except Exception:
            continue
    return rows


def _write_temp_errorxml_listing(
    out_dir: Path,
    search_dirs: Iterable[Path],
    *,
    stage: str,
    before_set: Optional[set[str]] = None,
    after_set: Optional[set[str]] = None,
) -> str:
    """Write an artifact that proves what recovery logs existed (or not) during a run."""
    payload: Dict[str, Any] = {
        "stage": stage,
        "written_at": _now_ts(),
        "search_dirs": [str(p) for p in search_dirs],
        "entries": _snapshot_errorxml_listing(search_dirs=search_dirs, limit=80),
    }
    if before_set is not None:
        payload["before_count"] = len(before_set)
    if after_set is not None:
        payload["after_count"] = len(after_set)

    path = out_dir / "temp_errorxml_listing.json"
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        # Best-effort evidence only.
        pass
    return str(path)


class _RecoveryLogWatcher:
    """Polls %TEMP% for Excel recovery logs during the run and copies them immediately.

    This makes recovery XML capture more reliable in cases where:
    - Excel writes the log late (near timeout)
    - The log exists only briefly
    - The file is intermittently locked
    """

    def __init__(
        self,
        search_dirs: List[Path],
        out_dir: Path,
        stop_event: threading.Event,
        since_epoch: float,
        hard_deadline: float,
        poll_interval: float = 0.20,
        max_copies: int = 25,
    ) -> None:
        self.search_dirs = search_dirs
        self.out_dir = out_dir
        self.stop_event = stop_event
        self.since_epoch = float(since_epoch)
        self.hard_deadline = float(hard_deadline)
        self.poll_interval = float(poll_interval)
        self.max_copies = int(max_copies)
        self._seen_mtime: Dict[str, float] = {}
        self.copied: List[Dict[str, str]] = []

    def _try_copy(self, src: Path, mtime: float) -> None:
        if len(self.copied) >= self.max_copies:
            return
        dst = self.out_dir / f"recovery_live_{len(self.copied):02d}_{src.name}"
        for _ in range(4):
            if time.time() > self.hard_deadline:
                break
            try:
                dst.write_bytes(src.read_bytes())
                self.copied.append(
                    {
                        "source": str(src),
                        "copied": str(dst),
                        "snippet": _read_text_short(dst, limit=4000),
                        "observed_mtime": str(mtime),
                    }
                )
                return
            except Exception:
                time.sleep(0.10)

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                for p in list_recovery_log_candidates(self.search_dirs):
                    try:
                        st = p.stat()
                        m = float(st.st_mtime)
                    except Exception:
                        continue
                    if m < self.since_epoch:
                        continue
                    key = str(p)
                    prev = float(self._seen_mtime.get(key, 0.0))
                    if m <= prev:
                        continue
                    self._seen_mtime[key] = m
                    self._try_copy(p, mtime=m)
            except Exception:
                pass

            # Wait (interruptible) rather than sleep so stop is responsive.
            self.stop_event.wait(timeout=self.poll_interval)


def _win_get_pid(hwnd: int) -> int:
    if not _WIN_OK:
        return -1
    _tid, pid = win32process.GetWindowThreadProcessId(hwnd)  # type: ignore[attr-defined]
    return int(pid)


def _tasklist_excel_pids(timeout_s: float = 1.5) -> List[int]:
    """Return EXCEL.EXE process IDs (best-effort, fast).

    We intentionally use the built-in `tasklist` rather than heavier process
    enumeration via win32 APIs; this avoids permission edge cases and is fast
    enough for our 15s probe budget.
    """
    if sys.platform != "win32":
        return []
    try:
        import csv
        from io import StringIO

        cp = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
            timeout=float(timeout_s),
        )
        if not cp.stdout:
            return []
        pids: List[int] = []
        for row in csv.reader(StringIO(cp.stdout)):
            # Expected columns: Image Name, PID, Session Name, Session#, Mem Usage
            if not row:
                continue
            if row[0].strip().upper() != "EXCEL.EXE":
                continue
            try:
                pids.append(int(row[1]))
            except Exception:
                continue
        return sorted(set(pids))
    except Exception:
        return []


def _powershell_process_commandline(pid: int, timeout_s: float = 1.0) -> Optional[str]:
    """Best-effort fetch of a process command line (Windows only).

    Used to distinguish user-launched Excel from COM/automation-launched Excel
    (often includes '-Embedding' or '/automation').
    """
    if sys.platform != "win32":
        return None
    try:
        cmd = f'(Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}").CommandLine'
        cp = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                cmd,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=float(timeout_s),
        )
        out = (cp.stdout or "").strip()
        return out or None
    except Exception:
        return None


def _looks_like_excel_com_automation_cmdline(cmdline: Optional[str]) -> bool:
    """Heuristic: was Excel launched via COM/automation?

    This helps us safely clean up orphaned Excel instances created by this probe
    even across runs, without killing a user's normal interactive Excel session.
    """
    if not cmdline:
        return False
    s = str(cmdline).lower()
    return ("-embedding" in s) or ("/automation" in s)


def _find_xlmain_hwnd_for_pid(pid: int) -> int:
    """Find the top-level XLMAIN window for a given Excel PID (0 if not found)."""
    if not _WIN_OK:
        return 0
    try:
        for hwnd in _win_enum_windows(visible_only=False):
            try:
                if int(_win_get_pid(hwnd)) != int(pid):
                    continue
                if _win_get_class(hwnd) == "XLMAIN":
                    return int(hwnd)
            except Exception:
                continue
    except Exception:
        pass
    return 0


def _win_get_owner(hwnd: int) -> int:
    """Return owner window handle (0 if none/unknown)."""
    if not _WIN_OK:
        return 0
    try:
        return int(win32gui.GetWindow(hwnd, win32con.GW_OWNER))  # type: ignore[attr-defined]
    except Exception:
        return 0


def _win_owner_chain(hwnd: int, max_depth: int = 10) -> List[int]:
    """Follow GW_OWNER pointers to approximate modal ownership chains."""
    out: List[int] = []
    cur = int(hwnd)
    for _ in range(max_depth):
        o = int(_win_get_owner(cur))
        if o in (0, -1) or o == cur or o in out:
            break
        out.append(o)
        cur = o
    return out


def _win_belongs_to_excel(hwnd: int, excel_pid: int, excel_hwnd: int) -> bool:
    """Best-effort: is hwnd in the Excel process / owned-by chain of excel_hwnd."""
    try:
        if int(_win_get_pid(hwnd)) == int(excel_pid):
            return True
    except Exception:
        pass
    try:
        chain = _win_owner_chain(hwnd)
        if int(excel_hwnd) in chain:
            return True
        for o in chain:
            try:
                if int(_win_get_pid(o)) == int(excel_pid):
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _win_set_foreground(hwnd: int) -> None:
    """Best-effort bring a window to the foreground (may be blocked by OS policy)."""
    if not _WIN_OK:
        return
    try:
        win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
    except Exception:
        pass
    try:
        win32gui.SetForegroundWindow(hwnd)  # type: ignore[attr-defined]
    except Exception:
        pass


def _debug_window_snapshot(excel_pid: int, excel_hwnd: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Collect a small snapshot of Excel-ish windows for troubleshooting dialog capture."""
    out: List[Dict[str, Any]] = []
    if not _WIN_OK:
        return out

    # Always include the Excel main hwnd if provided, even if it isn't returned by EnumWindows.
    try:
        if int(excel_hwnd) not in (0, -1):
            out.append(
                {
                    "hwnd": int(excel_hwnd),
                    "pid": int(_win_get_pid(int(excel_hwnd))),
                    "owner": int(_win_get_owner(int(excel_hwnd))),
                    "class": _win_get_class(int(excel_hwnd)),
                    "title": _win_get_text(int(excel_hwnd)),
                    "rect": _win_get_rect(int(excel_hwnd)),
                }
            )
    except Exception:
        pass

    for hwnd in _win_enum_windows(visible_only=False):
        try:
            pid = _win_get_pid(hwnd)

            owner = _win_get_owner(hwnd)
            belongs = _win_belongs_to_excel(hwnd, excel_pid=excel_pid, excel_hwnd=excel_hwnd)
            title = _win_get_text(hwnd)
            cls = _win_get_class(hwnd)
            title_l = (title or "").lower()
            cls_l = (cls or "").lower()
            excelish = (

                belongs
                or ("excel" in title_l)
                or (cls == "#32770")
                or ("dialog" in cls_l)
                or ("nuidialog" in cls_l)
            )
            if not excelish:
                continue
            out.append(
                {
                    "hwnd": int(hwnd),
                    "pid": int(pid),
                    "owner": int(owner),
                    "class": cls,
                    "title": title,
                    "rect": _win_get_rect(hwnd),
                }
            )
            if len(out) >= int(limit):
                break
        except Exception:
            continue
    return out


def _win_enum_windows(visible_only: bool = True) -> List[int]:
    if not _WIN_OK:
        return []
    out: List[int] = []

    def cb(hwnd: int, _lparam: Any) -> None:
        try:
            if (not visible_only) or win32gui.IsWindowVisible(hwnd):  # type: ignore[attr-defined]
                out.append(hwnd)
        except Exception:
            return

    win32gui.EnumWindows(cb, None)  # type: ignore[attr-defined]
    return out


def _win_get_class(hwnd: int) -> str:
    try:
        return win32gui.GetClassName(hwnd)  # type: ignore[attr-defined]
    except Exception:
        return ""


def _win_get_text(hwnd: int) -> str:
    try:
        return win32gui.GetWindowText(hwnd)  # type: ignore[attr-defined]
    except Exception:
        return ""


def _win_get_rect(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
    try:
        l, t, r, b = win32gui.GetWindowRect(hwnd)  # type: ignore[attr-defined]
        if r <= l or b <= t:
            return None
        return (l, t, r, b)
    except Exception:
        return None


def _win_enum_children(hwnd: int) -> List[int]:
    if not _WIN_OK:
        return []
    out: List[int] = []

    def cb(ch: int, _lparam: Any) -> None:
        out.append(ch)

    try:
        win32gui.EnumChildWindows(hwnd, cb, None)  # type: ignore[attr-defined]
    except Exception:
        pass
    return out


def _dialog_body_text(hwnd_dialog: int) -> str:
    """Best-effort extraction of dialog body text.

    Older dialogs expose the body via STATIC controls; newer Office dialog hosts
    sometimes don't. We therefore collect any non-empty child texts and de-dup.
    """
    parts: List[str] = []

    # Some dialogs put useful text on the top-level window itself.
    try:
        top = _win_get_text(hwnd_dialog).strip()
        if top:
            parts.append(top)
    except Exception:
        pass

    for ch in _win_enum_children(hwnd_dialog):
        try:
            cls = _win_get_class(ch).lower()
            txt = _win_get_text(ch).strip()
            if not txt:
                continue
            # Avoid polluting the body with button captions.
            if cls == "button":
                continue
            parts.append(txt)
        except Exception:
            continue
    # de-dup preserving order
    seen: set[str] = set()
    uniq: List[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return "\n".join(uniq).strip()


def _click_dialog_button(hwnd_dialog: int, prefer: Tuple[str, ...]) -> Optional[str]:
    """Click a button by caption (e.g., ("Yes","OK")). Returns clicked caption."""
    if not _WIN_OK:
        return None
    buttons: List[Tuple[int, str]] = []
    for ch in _win_enum_children(hwnd_dialog):
        if _win_get_class(ch).lower() == "button":
            cap = _win_get_text(ch).strip()
            if cap:
                buttons.append((ch, cap))

    # pick preferred in order
    target: Optional[Tuple[int, str]] = None
    for want in prefer:
        for h, cap in buttons:
            if cap.lower() == want.lower():
                target = (h, cap)
                break
        if target:
            break

    # fallback: first button
    if not target and buttons:
        target = buttons[0]

    if not target:
        return None

    hbtn, cap = target
    try:
        win32api.PostMessage(hbtn, win32con.BM_CLICK, 0, 0)  # type: ignore[attr-defined]
        return cap
    except Exception:
        try:
            win32gui.SendMessage(hbtn, win32con.BM_CLICK, 0, 0)  # type: ignore[attr-defined]
            return cap
        except Exception:
            return None


def grab_screenshot(path: Path, hwnd: Optional[int] = None) -> Optional[str]:
    """Capture a screenshot of *hwnd* (or full screen) to *path* (PNG)."""
    if not _PIL_OK:
        return None
    try:
        bbox = _win_get_rect(hwnd) if (hwnd is not None and _WIN_OK) else None
        img = ImageGrab.grab(bbox=bbox) if bbox else ImageGrab.grab()  # type: ignore[attr-defined]
        img.save(path)
        return str(path)
    except Exception:
        return None


@dataclass
class DialogEvent:
    ts: str
    hwnd: int
    title: str
    body: str
    action: str
    clicked: Optional[str] = None
    screenshot: Optional[str] = None


@dataclass
class ExcelDesktopProbeResult:
    candidate_path: str
    out_dir: str
    excel_pid: Optional[int] = None
    excel_hwnd: Optional[int] = None

    opened: bool = False
    repaired_open: bool = False
    fatal: bool = False
    exception: Optional[str] = None

    timed_out: bool = False

    dialogs: List[DialogEvent] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    recovery_logs: List[Dict[str, str]] = field(default_factory=list)

    # Evidence artifact even when no recovery XML was copied.
    temp_errorxml_listing_path: Optional[str] = None

    repaired_copy_path: Optional[str] = None

    # Non-screenshot evidence (useful when Windows blocks screen capture)
    workbook_count: Optional[int] = None
    active_workbook_name: Optional[str] = None
    sheet_names: List[str] = field(default_factory=list)
    elapsed_seconds: Optional[float] = None


    # Debug window snapshot near the end of the run (helps tune dialog detection)
    window_debug: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def excel_desktop_probe_result_from_dict(payload: dict) -> ExcelDesktopProbeResult:
    """Re-hydrate :class:`ExcelDesktopProbeResult` from its JSON/dict form."""
    d = dict(payload)
    dialogs_raw = d.get("dialogs") or []
    dialogs: List[DialogEvent] = []
    for ev in dialogs_raw:
        if isinstance(ev, DialogEvent):
            dialogs.append(ev)
        elif isinstance(ev, dict):
            dialogs.append(DialogEvent(**ev))
    d["dialogs"] = dialogs
    return ExcelDesktopProbeResult(**d)


class _DialogMonitor:
    """Watches for Excel dialogs for a specific Excel process PID and auto-clicks."""

    def __init__(
        self,
        excel_pid: int,
        excel_hwnd: int,
        out_dir: Path,
        on_event: Callable[[DialogEvent], None],
        stop_event: threading.Event,
        poll_interval: float = 0.05,
    ) -> None:
        self.excel_pid = excel_pid
        self.excel_hwnd = excel_hwnd
        self.out_dir = out_dir
        self.on_event = on_event
        self.stop_event = stop_event
        self.poll_interval = poll_interval
        self._seen_hwnds: set[int] = set()

    def _policy(self, title: str, body: str, belongs: bool) -> Tuple[str, Tuple[str, ...]]:
        """Return (action_label, preferred_buttons).

        If a modal belongs to our Excel instance, we must be willing to click a
        safe default even when the dialog body is not readable via Win32 APIs.
        """
        t = (title or "").lower()
        b = (body or "").lower()

        # Most common corruption prompt
        if ("recover" in b) and ("found a problem" in b or "problem" in b or "content" in b):
            return ("RECOVER_YES", ("Yes", "OK"))

        # Fatal open failure
        if "cannot be opened" in b or "cannot be opened or repaired" in b:
            return ("FATAL_OK", ("OK",))

        # Post-repair summary
        if "repairs were made" in b or "repaired records" in b:
            return ("REPAIRED_OK", ("OK",))

        # Generic Excel dialog: safest is OK
        if "excel" in t or "microsoft office" in t:
            return ("GENERIC_OK", ("Yes", "OK", "Continue", "Open", "Repair"))

        # Blocking-but-unreadable modal owned by Excel (common with modern Office UI)
        if belongs:
            return ("BLOCKING_DEFAULT", ("Yes", "OK", "Continue", "Open", "Repair"))

        return ("IGNORE", tuple())

    def run(self) -> None:
        if not _WIN_OK:
            return
        while not self.stop_event.is_set():
            try:
                for hwnd in _win_enum_windows(visible_only=False):
                    if hwnd in self._seen_hwnds:
                        continue
                    pid = _win_get_pid(hwnd)
                    owner = _win_get_owner(hwnd)
                    belongs = _win_belongs_to_excel(hwnd, excel_pid=self.excel_pid, excel_hwnd=self.excel_hwnd)

                    cls = _win_get_class(hwnd)
                    title = _win_get_text(hwnd)

                    # Excel modals are often #32770, but newer Office builds can use
                    # other dialog host classes (e.g. "NUIDialog").
                    # We treat any small, visible, non-main window titled "Microsoft Excel"
                    # as a candidate dialog.
                    cls_l = (cls or "").lower()
                    title_l = (title or "").strip().lower()
                    is_class_dialog = cls == "#32770" or "dialog" in cls_l or "nuidialog" in cls_l
                    # Many Office dialogs are titled "Microsoft Excel", but some builds use
                    # "Microsoft Office", "Excel", or even an empty title.
                    is_excelish_title = ("excel" in title_l) or ("microsoft office" in title_l)
                    # Only consider Excel dialogs:
                    # - either clearly Excel/Office by title
                    # - or dialog-host classes that belong to *our* Excel instance
                    # (many non-dialog child windows belong to Excel; don't treat them as modals).
                    if not (is_excelish_title or (belongs and is_class_dialog)):
                        continue
                    if int(hwnd) == int(self.excel_hwnd):
                        continue
                    # Exclude the main workbook window if it's titled "Microsoft Excel"
                    rect = _win_get_rect(hwnd)
                    if rect:
                        l, t, r, b = rect
                        w, h = (r - l), (b - t)
                        if w > 1400 and h > 800:
                            continue

                    body = _dialog_body_text(hwnd)
                    body_l = (body or "").lower()
                    # If the window doesn't belong to our Excel instance, only keep it if it looks Excel-ish.
                    # IMPORTANT: some Office dialog hosts don't expose body text via GetWindowText,
                    # so we allow empty body when the class/title look like Excel.
                    if (not belongs) and (not is_excelish_title):
                        continue
                    if (not belongs) and body_l and not (
                        ("recover" in body_l) or ("repairs" in body_l) or ("repaired" in body_l)
                        or ("cannot" in body_l and "open" in body_l) or ("found a problem" in body_l)
                    ):
                        continue
                    action, prefer = self._policy(title, body, belongs=bool(belongs))
                    if action == "IGNORE":
                        continue


                    self._seen_hwnds.add(hwnd)
                    _win_set_foreground(hwnd)
                    shot = grab_screenshot(self.out_dir / f"dialog_{_now_ts()}.png", hwnd=hwnd)
                    clicked = _click_dialog_button(hwnd, prefer=prefer) if prefer else None

                    # If we couldn't find a button but this is likely blocking our COM call,
                    # try a safe ENTER on the dialog window.
                    if clicked is None and action.startswith("BLOCKING"):
                        try:
                            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)  # type: ignore[attr-defined]
                            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)  # type: ignore[attr-defined]
                            clicked = "ENTER"
                        except Exception:
                            pass

                    ev = DialogEvent(
                        ts=datetime.now().isoformat(timespec="seconds"),
                        hwnd=int(hwnd),
                        title=title,
                        body=body,
                        action=action,
                        clicked=clicked,
                        screenshot=shot,
                    )
                    self.on_event(ev)
            except Exception:
                # keep looping; do not crash monitor
                pass

            time.sleep(self.poll_interval)


def probe_open_in_desktop_excel(
    candidate_path: str,
    out_root: str = "Outputs/excel_runs",
    out_dir_override: Optional[str] = None,
    visible: bool = True,
    try_repair: bool = True,
    save_repaired_copy: bool = True,
    timeout_seconds: int = 15,
    display_alerts: bool = True,
    search_log_dirs: Optional[List[str]] = None,
    force_kill_on_timeout: bool = True,
    force_kill_on_exit: bool = True,
) -> ExcelDesktopProbeResult:
    """Open *candidate_path* in desktop Excel, auto-handle dialogs, collect artifacts."""
    if not _WIN_OK:
        raise RuntimeError("Desktop Excel probe requires Windows pywin32 (pythoncom/win32com/win32gui).")
    if not Path(candidate_path).exists():
        raise FileNotFoundError(candidate_path)

    if out_dir_override:
        out_dir = Path(out_dir_override)
        _ensure_dir(out_dir)
    else:
        out_dir = Path(out_root) / f"{_safe_stem(candidate_path)[:60]}_{_now_ts()}"
        _ensure_dir(out_dir)

    result = ExcelDesktopProbeResult(candidate_path=candidate_path, out_dir=str(out_dir))

    # Where to look for recovery logs
    dirs = [Path(tempfile.gettempdir())]
    if search_log_dirs:
        dirs.extend([Path(d) for d in search_log_dirs])

    # NOTE: Excel can write recovery logs very quickly; allow a small grace window
    # when filtering by mtime.
    since = time.time()
    hard_deadline = since + float(max(1.0, float(timeout_seconds)))
    before_set = {str(p) for p in list_recovery_log_candidates(dirs)}

    stop_evt = threading.Event()
    watchdog_stop = threading.Event()

    # Recovery log watcher (copies error*.xml immediately when they appear)
    log_stop_evt = threading.Event()
    log_watcher = _RecoveryLogWatcher(
        search_dirs=dirs,
        out_dir=out_dir,
        stop_event=log_stop_evt,
        since_epoch=since - 1.0,
        hard_deadline=hard_deadline,
    )
    threading.Thread(target=log_watcher.run, name="excel_recovery_log_watcher", daemon=True).start()

    excel = None
    wb = None

    # Persist dialog events as they happen so evidence survives worker termination.
    dialog_events_path = out_dir / "dialog_events.jsonl"

    last_dialog_epoch = time.time()
    monitor_event_count = 0

    def _append_dialog(ev: DialogEvent) -> None:
        nonlocal last_dialog_epoch, monitor_event_count
        last_dialog_epoch = time.time()
        monitor_event_count += 1
        result.dialogs.append(ev)
        if ev.screenshot:
            result.screenshots.append(ev.screenshot)
        if ev.action.startswith("FATAL"):
            result.fatal = True
        try:
            with dialog_events_path.open("a", encoding="utf-8", errors="replace") as f:
                f.write(json.dumps(dataclasses.asdict(ev), ensure_ascii=False) + "\n")
        except Exception:
            pass

    # COM work must happen in the creating thread; keep everything in this thread.
    pythoncom.CoInitialize()  # type: ignore[attr-defined]
    try:
        excel_pids_before = _tasklist_excel_pids() if _WIN_OK else []

        excel = win32com.client.DispatchEx("Excel.Application")  # type: ignore[attr-defined]
        excel.Visible = bool(visible)
        # For corruption prompts we *want* the dialog to appear so we can screenshot it
        # and deterministically click the right button.
        excel.DisplayAlerts = bool(display_alerts)
        # Some Office builds suppress UI prompts in non-interactive automation; be explicit.
        try:
            excel.Interactive = True
        except Exception:
            pass
        try:
            excel.UserControl = True
        except Exception:
            pass
        try:
            excel.EnableEvents = True
        except Exception:
            pass
        # Harden against link/macro prompts
        try:
            excel.AskToUpdateLinks = False
        except Exception:
            pass
        try:
            excel.AutomationSecurity = 3  # msoAutomationSecurityForceDisable
        except Exception:
            pass

        # Identify the Excel process/window robustly.
        # In some builds, `excel.Hwnd` can be transient/invalid early in startup.
        hwnd = int(getattr(excel, "Hwnd", 0) or 0)
        pid_from_hwnd = _win_get_pid(hwnd) if hwnd not in (0, -1) else -1

        # Prefer the newly-spawned EXCEL.EXE PID when possible.
        try:
            time.sleep(0.15)
        except Exception:
            pass
        excel_pids_after = _tasklist_excel_pids() if _WIN_OK else []
        new_pids = [p for p in excel_pids_after if p not in set(excel_pids_before)]
        chosen_pid = int(new_pids[-1]) if new_pids else int(pid_from_hwnd)
        if chosen_pid <= 0:
            chosen_pid = int(pid_from_hwnd)
        result.excel_pid = chosen_pid if chosen_pid > 0 else None

        # Find the real XLMAIN window for the chosen PID.
        main_hwnd = _find_xlmain_hwnd_for_pid(int(result.excel_pid or -1)) if result.excel_pid else 0
        if main_hwnd:
            hwnd = int(main_hwnd)
        result.excel_hwnd = int(hwnd) if hwnd not in (0, -1) else None

        if hwnd not in (0, -1):
            _win_set_foreground(hwnd)

        # Hard watchdog: if Excel/COM hangs, kill the spawned Excel instance so the
        # probe returns within timeout_seconds.
        def _watchdog_kill() -> None:
            try:
                # Wait full timeout unless we finish earlier.
                kill_wait = float(max(0.5, float(timeout_seconds) - 1.0))
                if watchdog_stop.wait(timeout=kill_wait):
                    return
                if not force_kill_on_timeout:
                    return
                pid = int(result.excel_pid or -1)
                if pid <= 0:
                    return
                result.timed_out = True
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=1.5,
                )
            except Exception:
                pass

        threading.Thread(target=_watchdog_kill, name="excel_probe_watchdog", daemon=True).start()

        monitor = _DialogMonitor(
            excel_pid=int(result.excel_pid or -1),
            excel_hwnd=int(hwnd),
            out_dir=out_dir,
            on_event=_append_dialog,
            stop_event=stop_evt,
        )
        th = threading.Thread(target=monitor.run, name="excel_dialog_monitor", daemon=True)
        th.start()

        # Take an initial screenshot (helps when Excel can't open anything)
        init_shot = grab_screenshot(out_dir / f"excel_initial_{_now_ts()}.png", hwnd=hwnd)
        if init_shot:
            result.screenshots.append(init_shot)

        # Attempt open
        # CorruptLoad: 0=normal, 1=repair, 2=extract data
        tried_modes: List[int] = []
        modes = ([1, 2] if try_repair else [0])
        for corrupt_load in modes:
            tried_modes.append(corrupt_load)
            try:
                wb = excel.Workbooks.Open(
                    os.path.abspath(candidate_path),
                    UpdateLinks=0,
                    ReadOnly=False,
                    AddToMru=False,
                    IgnoreReadOnlyRecommended=True,
                    Editable=True,
                    Notify=False,
                    Local=True,
                    CorruptLoad=corrupt_load,
                )
                result.opened = True
                result.repaired_open = bool(corrupt_load != 0)
                break
            except Exception:
                # Some builds behave differently depending on which optional args are supplied.
                # Retry with a minimal signature before declaring failure.
                try:
                    wb = excel.Workbooks.Open(
                        os.path.abspath(candidate_path),
                        CorruptLoad=corrupt_load,
                    )
                    result.opened = True
                    result.repaired_open = bool(corrupt_load != 0)
                    result.exception = None
                    break
                except Exception as e2:
                    result.exception = f"{type(e2).__name__}: {e2}"
                    result.opened = False

        # Some environments (notably Mark-of-the-Web / Protected View) may refuse
        # Workbooks.Open() and instead require opening via ProtectedViewWindows.
        # This path also gives us a chance to detect a Protected View window even
        # when no modal dialog is enumerated.
        if not result.opened:
            try:
                # If the file is blocked, this may succeed even when Workbooks.Open fails.
                excel.ProtectedViewWindows.Open(os.path.abspath(candidate_path))
            except Exception as e_pv:
                # Non-fatal; keep original exception but append PV attempt info.
                result.exception = (result.exception or "") + f" | ProtectedViewOpen failed: {type(e_pv).__name__}: {e_pv}"

        # Wait a bit for any last dialogs to appear and be handled.
        # IMPORTANT: Even if Workbooks.Open throws, Excel may still show a
        # recovery prompt and open the workbook after our dialog monitor clicks.
        def _send_enter() -> None:
            """Best-effort modal dismissal when dialog enumeration misses the prompt."""
            if not _WIN_OK:
                return
            try:
                _win_set_foreground(hwnd)
                # VK_RETURN = 0x0D
                win32api.keybd_event(0x0D, 0, 0, 0)  # type: ignore[attr-defined]
                win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)  # type: ignore[attr-defined]
                result.dialogs.append(
                    DialogEvent(
                        ts=_now_ts(),
                        hwnd=int(hwnd),
                        title="(sendkeys)",
                        body="Sent ENTER to foreground window",
                        action="SENDKEY_ENTER",
                        clicked="ENTER",
                        screenshot=None,
                    )
                )
            except Exception:
                pass

        open_fail_epoch = time.time()
        enter_sent = 0
        while time.time() < hard_deadline:
            # If open succeeded we can proceed.
            if result.opened:
                break
            # If fatal dialog appeared, break
            if result.fatal:
                break

            # If COM open failed but Excel did open something anyway, detect it.
            try:
                if int(getattr(excel.Workbooks, "Count", 0)) > 0:
                    wb = excel.ActiveWorkbook
                    result.opened = True
                    break
            except Exception:
                pass

            # Protected View path: if a ProtectedViewWindow exists, try to promote it
            # into a normal Workbook.
            try:
                pv_count = int(getattr(excel.ProtectedViewWindows, "Count", 0))
                if pv_count > 0:
                    pv = excel.ProtectedViewWindows(1)
                    try:
                        wb = pv.Edit()
                        result.opened = True
                        break
                    except Exception:
                        # If we can't edit, we at least know PV is involved.
                        pass
            except Exception:
                pass

            # If we have not observed *any* dialogs shortly after failure, stop early.
            # This keeps the probe responsive ("<=15s") rather than always consuming the full budget.
            since_fail = float(time.time() - open_fail_epoch)
            early_stop_s = float(min(8.0, max(3.0, float(timeout_seconds) - 2.0)))
            if (monitor_event_count == 0) and (since_fail > early_stop_s):
                break

            # Best-effort modal dismissal when enumeration misses the prompt.
            # Keep this very limited to avoid spamming keystrokes.
            quiet_for = float(time.time() - last_dialog_epoch)
            if enter_sent < 2 and since_fail < 2.5 and quiet_for > 0.75:
                _send_enter()
                enter_sent += 1
            time.sleep(0.25)

        # Best-effort COM evidence even if screenshots are blocked.
        try:
            result.workbook_count = int(getattr(excel.Workbooks, "Count", 0))
        except Exception:
            result.workbook_count = None
        try:
            if int(getattr(excel.Workbooks, "Count", 0)) > 0:
                awb = excel.ActiveWorkbook
                result.active_workbook_name = str(getattr(awb, "Name", "")) or None
                try:
                    n = int(getattr(awb.Worksheets, "Count", 0))
                    max_n = min(n, 50)
                    names: List[str] = []
                    for idx in range(1, max_n + 1):
                        try:
                            names.append(str(awb.Worksheets(idx).Name))
                        except Exception:
                            break
                    result.sheet_names = names
                except Exception:
                    result.sheet_names = []
        except Exception:
            pass

        # Screenshot after open attempt
        post_shot = None
        if time.time() < hard_deadline:
            post_shot = grab_screenshot(out_dir / f"excel_postopen_{_now_ts()}.png", hwnd=hwnd)
        if post_shot:
            result.screenshots.append(post_shot)

        # Also capture a full-screen screenshot for failures where the dialog is not
        # detected by window enumeration (e.g. modern Office dialog hosts).
        full_shot = None
        if time.time() < hard_deadline:
            full_shot = grab_screenshot(out_dir / f"screen_postopen_{_now_ts()}.png", hwnd=None)
        if full_shot:
            result.screenshots.append(full_shot)

        # Debug snapshot of windows (helps diagnose why dialogs aren't being captured)
        try:
            result.window_debug = _debug_window_snapshot(int(result.excel_pid or -1), hwnd)
        except Exception:
            pass

        # If workbook opened, optionally save a repaired copy for diffing.
        # IMPORTANT: SaveCopyAs can preserve some on-disk package quirks; using SaveAs
        # often yields a more fully-normalised package (which is what we want for Web).
        if wb is not None and save_repaired_copy:
            # Avoid Windows MAX_PATH issues: keep filename short.
            repaired_path = (out_dir / f"repaired_desktop_{_safe_stem(candidate_path)[:60]}.xlsx").resolve()
            try:
                # Give Excel a brief moment to finish any async repair work.
                t0 = time.time()
                while (time.time() - t0) < 2.0:
                    try:
                        if bool(getattr(excel, "Ready", True)):
                            break
                    except Exception:
                        break
                    time.sleep(0.1)

                prev_alerts = None
                try:
                    prev_alerts = excel.DisplayAlerts
                    excel.DisplayAlerts = False
                except Exception:
                    prev_alerts = None

                try:
                    # 51 = xlOpenXMLWorkbook (.xlsx)
                    wb.SaveAs(str(repaired_path), FileFormat=51)
                    result.repaired_copy_path = str(repaired_path)
                finally:
                    try:
                        if prev_alerts is not None:
                            excel.DisplayAlerts = prev_alerts
                    except Exception:
                        pass
            except Exception as e:
                # Fall back to SaveCopyAs
                try:
                    wb.SaveCopyAs(str(repaired_path))
                    result.repaired_copy_path = str(repaired_path)
                except Exception as e2:
                    # non-fatal
                    result.exception = (result.exception or "") + (
                        f" | SaveAs failed: {type(e).__name__}: {e}"
                        f" | SaveCopyAs failed: {type(e2).__name__}: {e2}"
                    )

        # Close
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:
            pass

    finally:
        stop_evt.set()
        watchdog_stop.set()
        log_stop_evt.set()

        # Give the log watcher a moment to finish a last copy without exceeding budget.
        try:
            if time.time() < hard_deadline:
                time.sleep(min(0.15, max(0.0, hard_deadline - time.time())))
        except Exception:
            pass
        try:
            # If we timed out / had to kill Excel, Quit() can hang; skip it.
            if excel is not None and not bool(result.timed_out):
                excel.Quit()
        except Exception:
            pass

        # Ensure our spawned Excel instance(s) don't linger between iterations.
        # Kill every PID that was not running before *this* probe started, so that
        # helper/child processes spawned alongside the main EXCEL.EXE are also
        # cleaned up even when they don't match result.excel_pid.
        if force_kill_on_exit:
            try:
                # Collect all Excel PIDs that appeared during this run.
                pids_to_kill: List[int] = []
                primary_pid = int(result.excel_pid or -1)
                if primary_pid > 0:
                    pids_to_kill.append(primary_pid)
                # Also include any new PIDs detected at dispatch time.
                for p in new_pids:
                    if int(p) > 0 and int(p) not in pids_to_kill:
                        pids_to_kill.append(int(p))
                # Also check current snapshot vs before (catches late-spawned helpers).
                if _WIN_OK:
                    try:
                        current_snap = _tasklist_excel_pids()
                        before_snap_set = set(int(p) for p in excel_pids_before)
                        for p in current_snap:
                            if int(p) not in before_snap_set and int(p) not in pids_to_kill:
                                pids_to_kill.append(int(p))
                    except Exception:
                        pass
                for pid in pids_to_kill:
                    try:
                        subprocess.run(
                            ["taskkill", "/PID", str(pid), "/T", "/F"],
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=1.5,
                        )
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()  # type: ignore[attr-defined]
        except Exception:
            pass

    result.elapsed_seconds = float(time.time() - since)

    # Merge any watcher-copied logs first (most reliable).
    try:
        if log_watcher.copied:
            result.recovery_logs.extend(log_watcher.copied)
    except Exception:
        pass

    # Collect recovery logs written since start (with a grace window) if we still have time.
    if time.time() > hard_deadline:
        # Even when we can't copy recovery logs (time budget), emit a listing artifact
        # so callers can tell whether Excel produced any error*.xml at all.
        try:
            after_set = {str(p) for p in list_recovery_log_candidates(dirs)}
            result.temp_errorxml_listing_path = _write_temp_errorxml_listing(
                out_dir,
                dirs,
                stage="hard_deadline",
                before_set=before_set,
                after_set=after_set,
            )
        except Exception:
            pass

        report_path = out_dir / "desktop_excel_probe_report.json"
        report_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        return result

    after_logs = find_new_recovery_logs(since_epoch=since - 10.0, search_dirs=dirs)
    # Some Excel runs modify an existing error*.xml; include those too
    after_set = {str(p) for p in list_recovery_log_candidates(dirs)}
    changed = [Path(p) for p in (after_set - before_set) if p.lower().endswith(".xml")]
    for p in changed:
        if p not in after_logs:
            after_logs.append(p)

    for i, src in enumerate(sorted(set(after_logs), key=lambda x: x.stat().st_mtime, reverse=True)):
        dst = out_dir / f"recovery_{i:02d}_{src.name}"
        # Some Office builds keep the file briefly locked; retry a few times.
        copied = False
        for _ in range(3):
            if time.time() > hard_deadline:
                break
            try:
                dst.write_bytes(src.read_bytes())
                copied = True
                break
            except Exception:
                time.sleep(0.15)
        if not copied:
            continue
        result.recovery_logs.append(
            {
                "source": str(src),
                "copied": str(dst),
                "snippet": _read_text_short(dst, limit=4000),
            }
        )


    # Always emit a listing artifact so "no recovery XML" is auditable.
    try:
        result.temp_errorxml_listing_path = _write_temp_errorxml_listing(
            out_dir,
            dirs,
            stage="final",
            before_set=before_set,
            after_set=after_set,
        )
    except Exception:
        pass

    # Persist report JSON
    report_path = out_dir / "desktop_excel_probe_report.json"
    report_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return result


def probe_open_in_desktop_excel_isolated(
    candidate_path: str,
    out_root: str = "Outputs/excel_runs",
    visible: bool = True,
    try_repair: bool = True,
    save_repaired_copy: bool = True,
    timeout_seconds: int = 15,
    display_alerts: bool = True,
    search_log_dirs: Optional[List[str]] = None,
    force_kill_on_timeout: bool = True,
    force_kill_on_exit: bool = True,
) -> ExcelDesktopProbeResult:
    """Run the desktop probe in a subprocess to guarantee a hard wall-clock timeout.

    This is the "engine boundary" needed for reliability: Excel/COM can hang in ways
    that bypass our in-process watchdog (e.g., during COM server startup). By running
    the probe in a worker subprocess, the supervisor can forcibly stop the whole tree
    and still collect artifacts (stdout/stderr + recovery logs).
    """
    if not Path(candidate_path).exists():
        raise FileNotFoundError(candidate_path)

    since = time.time()
    hard_deadline = since + float(max(1.0, float(timeout_seconds)))

    # Pre-create a deterministic output directory so we have a place to write
    # supervisor artifacts even if the worker hangs/crashes.
    out_dir = Path(out_root) / f"{_safe_stem(candidate_path)[:60]}_{_now_ts()}_isolated"
    _ensure_dir(out_dir)

    # Best-effort pre-clean: kill any *automation-launched* orphan Excel instances.
    # Why: if a previous run leaked an Excel COM server, subsequent runs would treat
    # it as "pre-existing" and never clean it up (to avoid killing user Excel).
    pre_cleanup: Dict[str, Any] = {
        "checked_pids": [],
        "automation_pids": [],
        "killed": [],
    }
    if _WIN_OK and bool(force_kill_on_exit):
        try:
            existing = _tasklist_excel_pids()
            pre_cleanup["checked_pids"] = list(map(int, existing or []))
            for pid in existing or []:
                cmdline = _powershell_process_commandline(int(pid))
                if _looks_like_excel_com_automation_cmdline(cmdline):
                    pre_cleanup["automation_pids"].append({"pid": int(pid), "cmdline": (cmdline or "")[:800]})
                    try:
                        cp = subprocess.run(
                            ["taskkill", "/PID", str(int(pid)), "/T", "/F"],
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=1.5,
                        )
                        pre_cleanup["killed"].append(
                            {
                                "pid": int(pid),
                                "rc": int(cp.returncode),
                                "stdout": (cp.stdout or "")[:800],
                                "stderr": (cp.stderr or "")[:800],
                            }
                        )
                    except Exception as e:
                        pre_cleanup["killed"].append({"pid": int(pid), "error": str(e)})
            try:
                time.sleep(0.15)
            except Exception:
                pass
        except Exception:
            pass

    # Track EXCEL.EXE processes that exist before we start so we can kill only the
    # ones spawned by this probe (avoid killing a user's already-open Excel instance).
    excel_pids_before_sup = _tasklist_excel_pids() if _WIN_OK else []

    # Where to look for recovery logs (same as inner probe)
    dirs = [Path(tempfile.gettempdir())]
    if search_log_dirs:
        dirs.extend([Path(d) for d in search_log_dirs])
    before_set = {str(p) for p in list_recovery_log_candidates(dirs)}

    # Worker outputs
    result_json = out_dir / "worker_result.json"
    stdout_path = out_dir / "worker_stdout.txt"
    stderr_path = out_dir / "worker_stderr.txt"

    cmd = [
        sys.executable,
        "-m",
        "triage.excel_desktop_worker",
        "--file",
        str(candidate_path),
        "--out-dir",
        str(out_dir),
        "--result-json",
        str(result_json),
        "--timeout",
        # Give the worker a slightly smaller budget so it can flush worker_result.json
        # and exit cleanly before the supervisor's hard wall-clock deadline.
        # Keep this buffer small because callers often want a hard 15s decision loop.
        str(max(1, int(timeout_seconds) - 1)),
    ]
    if not visible:
        cmd.append("--no-visible")
    if not try_repair:
        cmd.append("--no-repair")
    if not save_repaired_copy:
        cmd.append("--no-save-repaired")
    if not display_alerts:
        cmd.append("--no-alerts")
    if not force_kill_on_timeout:
        cmd.append("--no-force-kill-timeout")
    if not force_kill_on_exit:
        cmd.append("--no-force-kill-exit")
    if search_log_dirs:
        for d in search_log_dirs:
            cmd.extend(["--search-log-dir", d])

    # Run worker and enforce wall-clock timeout.
    timed_out = False
    worker_rc: Optional[int] = None
    worker_stdout = ""
    worker_stderr = ""

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        # NOTE: use the *same* timeout budget as requested.
        worker_stdout, worker_stderr = proc.communicate(timeout=float(timeout_seconds))
        worker_rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        if force_kill_on_timeout:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=1.5,
                )
            except Exception:
                pass
        try:
            worker_stdout, worker_stderr = proc.communicate(timeout=0.75)
        except Exception:
            pass
        worker_rc = proc.returncode

    # Persist worker IO for debugging.
    try:
        stdout_path.write_text(worker_stdout or "", encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        stderr_path.write_text(worker_stderr or "", encoding="utf-8", errors="replace")
    except Exception:
        pass

    r: Optional[ExcelDesktopProbeResult] = None

    # Prefer worker result JSON if present.
    if result_json.exists():
        try:
            payload = json.loads(result_json.read_text(encoding="utf-8"))
            r = excel_desktop_probe_result_from_dict(payload)
            r.out_dir = str(out_dir)
            r.timed_out = bool(r.timed_out) or bool(timed_out)

            # If we only have the worker's initial heartbeat and the supervisor
            # hit its wall-clock timeout, normalize to a clear failure.
            if bool(timed_out) and (r.exception == "worker_started"):
                r.fatal = True
                r.opened = False
                r.exception = (
                    "Worker timed out before producing a final result. "
                    f"worker_rc={worker_rc}; see {stdout_path.name}/{stderr_path.name}"
                )
                if r.elapsed_seconds is None:
                    r.elapsed_seconds = float(time.time() - since)
        except Exception:
            r = None

    if r is None:
        # Fallback: create a minimal result and attempt to harvest recovery logs anyway.
        r = ExcelDesktopProbeResult(candidate_path=candidate_path, out_dir=str(out_dir))
        r.opened = False
        r.fatal = True
        r.timed_out = bool(timed_out)
        r.exception = (
            "Worker probe timed out and did not produce a result JSON. "
            f"worker_rc={worker_rc}; see {stdout_path.name}/{stderr_path.name}"
        )
        r.elapsed_seconds = float(time.time() - since)

        # Harvest any new/changed recovery logs into out_dir even on timeout.
        try:
            after_logs = find_new_recovery_logs(since_epoch=since - 10.0, search_dirs=dirs)
            after_set = {str(p) for p in list_recovery_log_candidates(dirs)}
            changed = [Path(p) for p in (after_set - before_set) if p.lower().endswith(".xml")]
            for p in changed:
                if p not in after_logs:
                    after_logs.append(p)

            for i, src in enumerate(sorted(set(after_logs), key=lambda x: x.stat().st_mtime, reverse=True)):
                if time.time() > hard_deadline:
                    break
                dst = out_dir / f"recovery_supervisor_{i:02d}_{src.name}"
                try:
                    dst.write_bytes(src.read_bytes())
                    r.recovery_logs.append(
                        {"source": str(src), "copied": str(dst), "snippet": _read_text_short(dst, limit=4000)}
                    )
                except Exception:
                    continue
        except Exception:
            pass

    # If the worker produced screenshots but did not populate the list (or we fell
    # back to a minimal result), harvest any PNG artifacts from the out_dir.
    try:
        pngs = sorted(out_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
        existing = set(r.screenshots or [])
        for p in pngs:
            sp = str(p)
            if sp not in existing:
                r.screenshots.append(sp)
                existing.add(sp)
    except Exception:
        pass

    # Harvest incremental dialog events (written by the worker/probe) if present.
    try:
        ev_path = out_dir / "dialog_events.jsonl"
        if ev_path.exists():
            existing_keys = {(ev.ts, ev.hwnd, ev.action, ev.title) for ev in (r.dialogs or [])}
            for line in ev_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    ev = DialogEvent(**d)
                    key = (ev.ts, ev.hwnd, ev.action, ev.title)
                    if key not in existing_keys:
                        r.dialogs.append(ev)
                        existing_keys.add(key)
                except Exception:
                    continue
    except Exception:
        pass

    # Always emit a listing artifact so "no recovery XML" is auditable even when
    # the worker never produced/could not be harvested.
    try:
        after_set2 = {str(p) for p in list_recovery_log_candidates(dirs)}
        r.temp_errorxml_listing_path = _write_temp_errorxml_listing(
            out_dir,
            dirs,
            stage="supervisor_final",
            before_set=before_set,
            after_set=after_set2,
        )
    except Exception:
        pass

    # Final safety: ensure any Excel processes spawned during this isolated run
    # do not linger between iterations (even if the worker's COM Quit()/taskkill
    # did not succeed or the worker never produced a final result).
    try:
        cleanup = {
            "pre_cleanup": pre_cleanup,
            "excel_pids_before": list(map(int, excel_pids_before_sup or [])),
            "excel_pids_after": [],
            "new_excel_pids": [],
            "killed": [],
            "late_passes": [],
            "still_running_after_cleanup": [],
        }

        if _WIN_OK and force_kill_on_exit:
            excel_pids_after_sup = _tasklist_excel_pids()
            cleanup["excel_pids_after"] = list(map(int, excel_pids_after_sup or []))
            before_set = set(int(p) for p in (excel_pids_before_sup or []))
            new_pids = [int(p) for p in (excel_pids_after_sup or []) if int(p) not in before_set]

            attempted_pids: set[int] = set()

            # If the worker reported an Excel PID, include it if it's newly created.
            try:
                reported_pid = int(getattr(r, "excel_pid", None) or -1)
            except Exception:
                reported_pid = -1
            if reported_pid > 0 and reported_pid not in before_set and reported_pid not in new_pids:
                new_pids.append(reported_pid)

            cleanup["new_excel_pids"] = list(map(int, new_pids))

            for pid in new_pids:
                try:
                    attempted_pids.add(int(pid))
                    cp = subprocess.run(
                        ["taskkill", "/PID", str(int(pid)), "/T", "/F"],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=1.5,
                    )
                    cleanup["killed"].append(
                        {
                            "pid": int(pid),
                            "rc": int(cp.returncode),
                            "stdout": (cp.stdout or "")[:800],
                            "stderr": (cp.stderr or "")[:800],
                        }
                    )
                except Exception as e:
                    cleanup["killed"].append({"pid": int(pid), "error": str(e)})

            # Late passes: Excel (and its helper/child processes) can spawn *after* our
            # first post-run snapshot, especially with modern Office 365 Click-to-Run.
            # IMPORTANT: we intentionally do NOT gate on _looks_like_excel_com_automation_cmdline
            # here. `before_set` already captures every Excel PID that was running before
            # this probe started, so any PID in `extra` is guaranteed to have been created
            # by this run and is safe to kill regardless of its command-line flags.
            for pass_i in range(5):
                try:
                    time.sleep(0.25)
                except Exception:
                    pass
                try:
                    current = _tasklist_excel_pids()
                    extra = [int(p) for p in (current or []) if int(p) not in before_set]
                    if not extra:
                        break

                    pass_rec: Dict[str, Any] = {
                        "pass": int(pass_i + 1),
                        "extra_candidates": list(map(int, extra)),
                        "killed": [],
                    }
                    for pid in extra:
                        try:
                            cmdline = _powershell_process_commandline(int(pid))
                            is_auto = _looks_like_excel_com_automation_cmdline(cmdline)

                            attempted_pids.add(int(pid))
                            # Primary: taskkill /T /F (kills process tree)
                            cp = subprocess.run(
                                ["taskkill", "/PID", str(int(pid)), "/T", "/F"],
                                capture_output=True,
                                text=True,
                                check=False,
                                timeout=2.0,
                            )
                            kill_rec: Dict[str, Any] = {
                                "pid": int(pid),
                                "is_automation": bool(is_auto),
                                "cmdline": (cmdline or "")[:800],
                                "rc": int(cp.returncode),
                                "stdout": (cp.stdout or "")[:800],
                                "stderr": (cp.stderr or "")[:800],
                            }
                            # Fallback: if taskkill reported the process didn't exist or
                            # returned non-zero, also try PowerShell Stop-Process.
                            if cp.returncode != 0:
                                try:
                                    ps_cmd = f"Stop-Process -Id {int(pid)} -Force -ErrorAction SilentlyContinue"
                                    ps_cp = subprocess.run(
                                        ["powershell", "-NoProfile", "-NonInteractive",
                                         "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                                        capture_output=True,
                                        text=True,
                                        check=False,
                                        timeout=2.0,
                                    )
                                    kill_rec["ps_fallback_rc"] = int(ps_cp.returncode)
                                    kill_rec["ps_fallback_stderr"] = (ps_cp.stderr or "")[:400]
                                except Exception as e_ps:
                                    kill_rec["ps_fallback_error"] = str(e_ps)
                            pass_rec["killed"].append(kill_rec)
                        except Exception as e:
                            pass_rec["killed"].append({"pid": int(pid), "error": str(e)})

                    cleanup["late_passes"].append(pass_rec)
                except Exception:
                    break

            # Final nuclear pass: give processes a moment to die, then re-check.
            # Kill any still-alive Excel PIDs not in before_set using PowerShell Stop-Process
            # which bypasses taskkill permission edge-cases on some Office builds.
            try:
                time.sleep(0.4)
            except Exception:
                pass
            try:
                final_snap = _tasklist_excel_pids()
                final_extra = [int(p) for p in (final_snap or []) if int(p) not in before_set]
                if final_extra:
                    pids_str = ",".join(str(p) for p in final_extra)
                    ps_nuclear = (
                        f"$pids = @({pids_str}); "
                        f"foreach ($p in $pids) {{ "
                        f"Stop-Process -Id $p -Force -ErrorAction SilentlyContinue "
                        f"}}"
                    )
                    subprocess.run(
                        ["powershell", "-NoProfile", "-NonInteractive",
                         "-ExecutionPolicy", "Bypass", "-Command", ps_nuclear],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=3.0,
                    )
                    for p in final_extra:
                        attempted_pids.add(int(p))
                    cleanup["nuclear_pass"] = {"pids": final_extra}
            except Exception:
                pass

            # Re-check for any still-running pids we believe we spawned.
            try:
                time.sleep(0.3)
            except Exception:
                pass
            still = set(_tasklist_excel_pids())
            if attempted_pids:
                cleanup["still_running_after_cleanup"] = [pid for pid in sorted(attempted_pids) if int(pid) in still]
            else:
                cleanup["still_running_after_cleanup"] = [pid for pid in new_pids if int(pid) in still]

        # Persist supervisor cleanup info for debugging.
        try:
            (out_dir / "supervisor_process_cleanup.json").write_text(
                json.dumps(cleanup, indent=2), encoding="utf-8"
            )
        except Exception:
            pass
    except Exception:
        pass

    report_path = out_dir / "desktop_excel_probe_report.json"
    try:
        report_path.write_text(json.dumps(r.to_dict(), indent=2), encoding="utf-8")
    except Exception:
        pass
    return r


def _cli() -> int:  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(description="Desktop Excel probe (open + capture recovery logs)")
    ap.add_argument("--file", required=True, help="Path to candidate .xlsx")
    ap.add_argument("--out", default="Outputs/excel_runs", help="Output root directory")
    ap.add_argument("--no-visible", action="store_true", help="Run Excel hidden (screenshots may be blank)")
    ap.add_argument("--no-repair", action="store_true", help="Do not use CorruptLoad=repair")
    ap.add_argument("--no-save-repaired", action="store_true", help="Do not SaveCopyAs repaired workbook")

    ap.add_argument("--timeout", type=int, default=15, help="Timeout seconds")
    ap.add_argument("--no-force-kill", action="store_true", help="Do not taskkill the spawned Excel instance")
    ap.add_argument("--isolate", action="store_true", help="Run probe in a subprocess to guarantee wall-clock timeout")
    args = ap.parse_args()

    fn = probe_open_in_desktop_excel_isolated if args.isolate else probe_open_in_desktop_excel
    r = fn(
        candidate_path=args.file,
        out_root=args.out,
        visible=not args.no_visible,
        try_repair=not args.no_repair,
        save_repaired_copy=not args.no_save_repaired,
        timeout_seconds=args.timeout,
        force_kill_on_timeout=not args.no_force_kill,
        force_kill_on_exit=not args.no_force_kill,
    )
    print(json.dumps(r.to_dict(), indent=2))
    return 0 if r.opened and not r.fatal else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
