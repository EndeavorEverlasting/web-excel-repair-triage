#!/usr/bin/env python3
"""
webexcel_graph_probe.py
Optional: Use Microsoft Graph to probe workbook openability WITHOUT a browser.
This is the closest thing to an automated "Web test" you can run locally.

Requirements:
- You must supply an OAuth2 Bearer token with Files.ReadWrite.All (or equivalent) for the file.
- You must supply a DriveItem reference.

This script avoids non-stdlib deps by using urllib. It does NOT obtain tokens for you.

Environment variables:
  GRAPH_TOKEN  = 'eyJ...'
Args (choose ONE form):
  1) drive+item:
     python webexcel_graph_probe.py --drive-id <DRIVE_ID> --item-id <ITEM_ID>
  2) share link:
     python webexcel_graph_probe.py --share-url "<https://1drv.ms/x/s!...>"

What it does:
- createSession(persistChanges=false)
- read workbook properties + list worksheets
If Graph returns 4xx/5xx or workbook errors, treat as "not clean".

NOTE:
- Graph and Excel for Web are close cousins, not identical. A pass here is strong evidence, not proof.
"""

import base64
import json
import os
import sys
import urllib.request
import urllib.parse

GRAPH = "https://graph.microsoft.com/v1.0"

def api(method, url, token, body=None):
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
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
        txt = raw.decode("utf-8", errors="ignore")
        try:
            payload = json.loads(txt)
        except Exception:
            payload = {"raw": txt}
        return e.code, payload

def encode_share_url(share_url: str) -> str:
    # Graph expects: /shares/{shareId}/driveItem
    # shareId = "u!" + base64url(share_url)
    b = share_url.encode("utf-8")
    s = base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")
    return "u!" + s

def usage():
    print("Usage:")
    print("  python webexcel_graph_probe.py --drive-id <DRIVE_ID> --item-id <ITEM_ID>")
    print('  python webexcel_graph_probe.py --share-url "<ONE_DRIVE_SHARE_URL>"')
    sys.exit(2)

def main():
    token = os.environ.get("GRAPH_TOKEN")
    if not token:
        print("Missing GRAPH_TOKEN environment variable.")
        sys.exit(2)

    args = sys.argv[1:]
    drive_id = item_id = share_url = None
    i = 0
    while i < len(args):
        if args[i] == "--drive-id":
            drive_id = args[i+1]; i += 2
        elif args[i] == "--item-id":
            item_id = args[i+1]; i += 2
        elif args[i] == "--share-url":
            share_url = args[i+1]; i += 2
        else:
            usage()

    if share_url:
        share_id = encode_share_url(share_url)
        base = f"{GRAPH}/shares/{share_id}/driveItem/workbook"
    elif drive_id and item_id:
        base = f"{GRAPH}/drives/{drive_id}/items/{item_id}/workbook"
    else:
        usage()

    # create session (no persistence)
    code, ses = api("POST", base + "/createSession", token, {"persistChanges": False})
    if code >= 400:
        print("createSession failed:", code)
        print(json.dumps(ses, indent=2))
        sys.exit(2)

    session_id = ses.get("id")
    if not session_id:
        print("No session id returned; unexpected.")
        print(json.dumps(ses, indent=2))
        sys.exit(2)

    print("Session created:", session_id)

    # Use session header
    def api_s(method, url, body=None):
        data = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "workbook-session-id": session_id,
        }
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
            txt = raw.decode("utf-8", errors="ignore")
            try:
                payload = json.loads(txt)
            except Exception:
                payload = {"raw": txt}
            return e.code, payload

    # List worksheets
    code, ws = api_s("GET", base + "/worksheets?$select=name", None)
    if code >= 400:
        print("worksheets failed:", code)
        print(json.dumps(ws, indent=2))
        sys.exit(2)

    names = [w.get("name") for w in ws.get("value", [])]
    print("Worksheets:", len(names))
    for n in names[:30]:
        print(" -", n)

    print("Graph probe: success (strong evidence workbook is openable in web context).")
    sys.exit(0)

if __name__ == "__main__":
    main()
