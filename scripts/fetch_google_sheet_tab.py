#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

SHEET_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")
SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


def rows_to_csv(values: object) -> str:
    if not isinstance(values, list) or not values:
        raise SystemExit("Google Sheet tab returned no rows")
    if any(not isinstance(row, list) for row in values):
        raise SystemExit("Google Sheet values must be row arrays")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(values)
    return buffer.getvalue()


def fetch_values(
    spreadsheet_id: str, sheet_name: str, credentials_json: str
) -> list[list[object]]:
    if not SHEET_ID_RE.fullmatch(spreadsheet_id):
        raise SystemExit("invalid spreadsheet id")
    try:
        info = json.loads(credentials_json)
    except json.JSONDecodeError as exc:
        raise SystemExit("Google service-account credentials are invalid JSON") from exc
    if not isinstance(info, dict) or info.get("type") != "service_account":
        raise SystemExit("Google credentials must be a service-account JSON object")
    try:
        import requests
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
    except ImportError as exc:
        raise SystemExit("live Google Sheet intake requires google-auth and requests") from exc

    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=[SCOPE]
    )
    credentials.refresh(Request())
    encoded_sheet = quote(sheet_name, safe="")
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
        f"{encoded_sheet}?majorDimension=ROWS"
    )
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=30,
    )
    if response.status_code != 200:
        raise SystemExit(
            f"Google Sheets API read failed with HTTP {response.status_code}"
        )
    payload = response.json()
    values = payload.get("values")
    if not isinstance(values, list):
        raise SystemExit("Google Sheets API response has no values array")
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read one private Google Sheet tab with read-only service-account "
            "credentials and write CSV."
        )
    )
    parser.add_argument("--sheet-name", default="Insights")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--sheet-id-env", default="PROMPT_KIT_EXPERT_INSIGHTS_SHEET_ID"
    )
    parser.add_argument(
        "--credentials-env",
        default="PROMPT_KIT_EXPERT_INSIGHTS_GOOGLE_CREDENTIALS",
    )
    args = parser.parse_args(argv)
    spreadsheet_id = os.environ.get(args.sheet_id_env, "").strip()
    credentials_json = os.environ.get(args.credentials_env, "").strip()
    if not spreadsheet_id:
        raise SystemExit(f"missing required environment variable: {args.sheet_id_env}")
    if not credentials_json:
        raise SystemExit(
            f"missing required environment variable: {args.credentials_env}"
        )
    values = fetch_values(spreadsheet_id, args.sheet_name, credentials_json)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rows_to_csv(values), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "rows": len(values),
                "sheet_name": args.sheet_name,
                "output": args.output.as_posix(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
