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
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

GRAPH = "https://graph.microsoft.com/v1.0"


@dataclass
class GraphResult:
    success: bool
    status_code: int
    step: str  # which step failed (or "complete")
    worksheets: List[str] = field(default_factory=list)
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


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


def probe_by_item(token: str, drive_id: str, item_id: str) -> GraphResult:
    """Probe a file already on OneDrive by drive_id + item_id."""
    base = f"{GRAPH}/drives/{drive_id}/items/{item_id}/workbook"
    return _run_probe(token, base)


def probe_by_share_url(token: str, share_url: str) -> GraphResult:
    """Probe a file via a share URL (e.g. 1drv.ms link)."""
    b = share_url.encode("utf-8")
    share_id = "u!" + base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")
    base = f"{GRAPH}/shares/{share_id}/driveItem/workbook"
    return _run_probe(token, base)


def probe_upload_and_test(token: str, local_path: str, remote_name: Optional[str] = None) -> GraphResult:
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
    return _run_probe(token, base)


def _run_probe(token: str, workbook_base_url: str) -> GraphResult:
    # Step 1: createSession
    code, ses = _api("POST", workbook_base_url + "/createSession", token, {"persistChanges": False})
    if code >= 400:
        return GraphResult(
            success=False, status_code=code, step="createSession",
            error=json.dumps(ses)[:500], raw=ses,
        )
    session_id = ses.get("id")
    if not session_id:
        return GraphResult(
            success=False, status_code=code, step="createSession",
            error="No session id in response.", raw=ses,
        )

    session_headers = {"workbook-session-id": session_id}

    # Step 2: list worksheets
    code, ws = _api("GET", workbook_base_url + "/worksheets?$select=name", token,
                    extra_headers=session_headers)
    if code >= 400:
        return GraphResult(
            success=False, status_code=code, step="listWorksheets",
            error=json.dumps(ws)[:500], raw=ws,
        )

    names = [w.get("name", "") for w in ws.get("value", [])]

    # Step 3: close session
    _api("DELETE", workbook_base_url + f"/sessions/{session_id}", token,
         extra_headers=session_headers)

    return GraphResult(
        success=True, status_code=200, step="complete",
        worksheets=names, raw={"worksheet_count": len(names)},
    )

