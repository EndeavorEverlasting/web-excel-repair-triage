"""
triage/graph_probe.py
---------------------
Optional Microsoft Graph workbook-session probe.
Tests whether a .xlsx will open cleanly in the Excel-for-Web backend.

Flow
----
1. Upload the file to OneDrive (PUT /me/drive/root:/{name}:/content)
2. Create a non-persistent workbook session (POST .../workbook/createSession)
3. List worksheets (GET .../workbook/worksheets)
4. Close session (DELETE .../workbook/sessions/{id})

If any step returns 4xx/5xx, the file is flagged as a FAIL.

Requirements
------------
- GRAPH_TOKEN env var (Bearer token with Files.ReadWrite scope)
  OR token passed directly to probe().
- Python stdlib only (urllib).
"""
from __future__ import annotations
import base64
import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

GRAPH = "https://graph.microsoft.com/v1.0"


@dataclass
class GraphResult:
    success: bool
    status_code: int
    step: str  # which step failed (or "complete")
    worksheets: List[str] = field(default_factory=list)

    # Optional: lightweight "sheet observation" for debugging.
    preview_sheet: Optional[str] = None
    preview_address: Optional[str] = None
    preview_text: List[List[str]] = field(default_factory=list)
    preview_image: Optional[str] = None

    # Optional: artifact folder (JSON + preview) written when out_root is provided.
    out_dir: Optional[str] = None
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


def _now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_stem(name: str) -> str:
    # Keep it stable and filesystem-safe.
    base = os.path.basename(name)
    stem = os.path.splitext(base)[0]
    out = []
    for ch in stem:
        if ch.isalnum() or ch in ("-", "_", "."):
            out.append(ch)
        else:
            out.append("_")
    s = "".join(out).strip("_")
    return s or "graph_probe"


def _col_letter(n: int) -> str:
    """1-based column index -> Excel column letters."""
    if n < 1:
        raise ValueError(n)
    s = ""
    x = n
    while x:
        x, r = divmod(x - 1, 26)
        s = chr(ord("A") + r) + s
    return s


def _render_preview_png(preview_text: List[List[str]], out_path: Path) -> Optional[str]:
    """Render a small grid image from preview_text. Returns path or None."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        return None
    if not preview_text:
        return None

    rows = len(preview_text)
    cols = max((len(r) for r in preview_text), default=0)
    if cols == 0:
        return None

    cell_w, cell_h = 180, 28
    pad = 10
    img_w = pad * 2 + cols * cell_w
    img_h = pad * 2 + rows * cell_h
    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    drw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # grid
    for r in range(rows + 1):
        y = pad + r * cell_h
        drw.line([(pad, y), (pad + cols * cell_w, y)], fill=(220, 220, 220), width=1)
    for c in range(cols + 1):
        x = pad + c * cell_w
        drw.line([(x, pad), (x, pad + rows * cell_h)], fill=(220, 220, 220), width=1)

    # text (truncate)
    for r in range(rows):
        for c in range(cols):
            v = ""
            try:
                v = str(preview_text[r][c])
            except Exception:
                v = ""
            v = v.replace("\r", " ").replace("\n", " ")
            if len(v) > 40:
                v = v[:37] + "..."
            x = pad + c * cell_w + 6
            y = pad + r * cell_h + 6
            drw.text((x, y), v, fill=(0, 0, 0), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return str(out_path)


def _api(method: str, url: str, token: str, body=None, extra_headers: dict | None = None) -> tuple[int, dict]:
    data = None
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.getcode(), json.loads(raw.decode("utf-8", errors="ignore") or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception:
            payload = {"raw": raw.decode("utf-8", errors="ignore")}
        return e.code, payload


def _upload(token: str, file_path: str, remote_name: str) -> tuple[int, dict]:
    """PUT file bytes to /me/drive/root:/{remote_name}:/content"""
    url = f"{GRAPH}/me/drive/root:/{remote_name}:/content"
    with open(file_path, "rb") as f:
        data = f.read()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.getcode(), json.loads(raw.decode("utf-8", errors="ignore") or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception:
            payload = {"raw": raw.decode("utf-8", errors="ignore")}
        return e.code, payload


def probe_by_item(
    token: str,
    drive_id: str,
    item_id: str,
    out_root: Optional[str] = None,
) -> GraphResult:
    """Probe a file already on OneDrive by drive_id + item_id."""
    base = f"{GRAPH}/drives/{drive_id}/items/{item_id}/workbook"
    label = f"drive_{drive_id[:8]}_item_{item_id[:8]}"
    return _run_probe(token, base, out_root=out_root, label=label)


def probe_by_share_url(
    token: str,
    share_url: str,
    out_root: Optional[str] = None,
) -> GraphResult:
    """Probe a file via a share URL (e.g. 1drv.ms link)."""
    b = share_url.encode("utf-8")
    share_id = "u!" + base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")
    base = f"{GRAPH}/shares/{share_id}/driveItem/workbook"
    return _run_probe(token, base, out_root=out_root, label="share")


def probe_upload_and_test(
    token: str,
    local_path: str,
    remote_name: Optional[str] = None,
    out_root: Optional[str] = None,
) -> GraphResult:
    """Upload *local_path* to OneDrive /me/drive root, then probe it."""
    import os as _os
    if remote_name is None:
        remote_name = _os.path.basename(local_path)
    code, upload_resp = _upload(token, local_path, remote_name)
    if code >= 400:
        return GraphResult(
            success=False, status_code=code, step="upload",
            error=json.dumps(upload_resp)[:500], raw=upload_resp,
        )
    item_id = upload_resp.get("id")
    drive_id = upload_resp.get("parentReference", {}).get("driveId")
    if not item_id or not drive_id:
        return GraphResult(
            success=False, status_code=code, step="upload",
            error="Upload succeeded but driveId/itemId missing in response.",
            raw=upload_resp,
        )
    base = f"{GRAPH}/drives/{drive_id}/items/{item_id}/workbook"
    r = _run_probe(token, base, out_root=out_root, label=_safe_stem(local_path))
    # Attach upload metadata for debugging/opening manually.
    r.raw = dict(r.raw or {})
    r.raw.update({
        "uploaded_drive_id": drive_id,
        "uploaded_item_id": item_id,
        "uploaded_remote_name": remote_name,
    })
    return r


def _run_probe(token: str, workbook_base_url: str, out_root: Optional[str], label: str) -> GraphResult:
    out_dir: Optional[Path] = None
    if out_root:
        out_dir = Path(out_root) / f"{_safe_stem(label)[:60]}_{_now_ts()}"
        out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: createSession
    code, ses = _api("POST", workbook_base_url + "/createSession", token, {"persistChanges": False})
    if code >= 400:
        r = GraphResult(
            success=False, status_code=code, step="createSession",
            error=json.dumps(ses)[:500], raw=ses,
        )
        if out_dir:
            r.out_dir = str(out_dir)
            (out_dir / "graph_probe_report.json").write_text(json.dumps(r.__dict__, indent=2), encoding="utf-8")
        return r
    session_id = ses.get("id")
    if not session_id:
        r = GraphResult(
            success=False, status_code=code, step="createSession",
            error="No session id in response.", raw=ses,
        )
        if out_dir:
            r.out_dir = str(out_dir)
            (out_dir / "graph_probe_report.json").write_text(json.dumps(r.__dict__, indent=2), encoding="utf-8")
        return r

    session_headers = {"workbook-session-id": session_id}

    # Step 2: list worksheets
    code, ws = _api("GET", workbook_base_url + "/worksheets?$select=id,name", token,
                    extra_headers=session_headers)
    if code >= 400:
        r = GraphResult(
            success=False, status_code=code, step="listWorksheets",
            error=json.dumps(ws)[:500], raw=ws,
        )
        if out_dir:
            r.out_dir = str(out_dir)
            (out_dir / "graph_probe_report.json").write_text(json.dumps(r.__dict__, indent=2), encoding="utf-8")
        return r

    ws_rows = ws.get("value", []) or []
    names = [w.get("name", "") for w in ws_rows]

    # Optional step: pull a small range so we can *observe* sheet content.
    preview_text: List[List[str]] = []
    preview_sheet: Optional[str] = None
    preview_address: Optional[str] = None
    preview_image: Optional[str] = None
    try:
        if ws_rows:
            ws0 = ws_rows[0]
            ws_id = ws0.get("id") or ws0.get("name")
            preview_sheet = ws0.get("name")
            # Default: A1..L20
            max_cols, max_rows = 12, 20
            preview_address = f"A1:{_col_letter(max_cols)}{max_rows}"
            ws_id_q = urllib.parse.quote(str(ws_id))
            # NOTE: keep ':' unescaped inside the Graph range address.
            addr_q = urllib.parse.quote(preview_address, safe=":")
            url = workbook_base_url + f"/worksheets/{ws_id_q}/range(address='{addr_q}')?$select=text"
            code2, rng = _api("GET", url, token, extra_headers=session_headers)
            if code2 < 400:
                preview_text = rng.get("text") or []
    except Exception:
        # Non-fatal: worksheet list is already strong evidence.
        preview_text = []

    # Step 3: close session
    _api("DELETE", workbook_base_url + f"/sessions/{session_id}", token,
         extra_headers=session_headers)

    r = GraphResult(
        success=True,
        status_code=200,
        step="complete",
        worksheets=names,
        preview_sheet=preview_sheet,
        preview_address=preview_address,
        preview_text=preview_text,
        raw={"worksheet_count": len(names)},
    )

    if out_dir:
        r.out_dir = str(out_dir)
        # Save JSON artifacts
        (out_dir / "graph_probe_report.json").write_text(json.dumps(r.__dict__, indent=2), encoding="utf-8")
        if preview_text:
            (out_dir / "graph_probe_preview.json").write_text(
                json.dumps({"sheet": preview_sheet, "address": preview_address, "text": preview_text}, indent=2),
                encoding="utf-8",
            )
            preview_image = _render_preview_png(preview_text, out_dir / "graph_sheet_preview.png")
            r.preview_image = preview_image
            # Update report with preview_image path
            (out_dir / "graph_probe_report.json").write_text(json.dumps(r.__dict__, indent=2), encoding="utf-8")

    return r

