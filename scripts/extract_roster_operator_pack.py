#!/usr/bin/env python3
"""Extract operator CF pack + review configs from blessed reference ZIP."""
from __future__ import annotations

import argparse
import json
import sys

from triage.roster_log_review_queue.extract_pack import extract_all


def main() -> int:
    p = argparse.ArgumentParser(description="Extract roster operator pack configs.")
    p.add_argument("--reference-zip", required=True)
    p.add_argument("--out-dir", default="configs/roster_log_review_queue")
    args = p.parse_args()
    summary = extract_all(args.reference_zip, args.out_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
