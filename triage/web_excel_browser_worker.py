"""triage/web_excel_browser_worker.py
-------------------------------------
Worker process for Web Excel browser probe.

Used by `probe_open_in_web_excel_isolated()` to guarantee a hard wall-clock
timeout. The worker writes `web_excel_probe_report.json` to the requested output
folder and prints the same JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage.web_excel_browser import probe_open_in_web_excel


def _main() -> int:
    ap = argparse.ArgumentParser(description="Web Excel browser probe worker")
    ap.add_argument("--url", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--user-data-dir", default=None)
    ap.add_argument("--browser", default="chromium")
    ap.add_argument("--channel", default=None)
    ap.add_argument("--no-screenshot", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    r = probe_open_in_web_excel(
        url=args.url,
        out_root=str(out_dir.parent),
        out_dir_override=str(out_dir),
        timeout_seconds=int(args.timeout),
        headless=bool(args.headless),
        user_data_dir=args.user_data_dir,
        browser=str(args.browser),
        channel=args.channel,
        take_screenshot=not bool(args.no_screenshot),
    )

    payload = r.to_dict()
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
