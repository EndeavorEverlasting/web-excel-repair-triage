"""Rebuild HTML portal from existing sidecars: python -m triage.sidecar_html <out-dir>"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from triage.sidecar_html.rebuild import _load_manifest, rebuild_portal, sections_for_manifest
from triage.sidecar_html.portal import build_run_portal


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="triage.sidecar_html")
    ap.add_argument("out_dir", help="Run output folder containing manifest JSON")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    manifest, manifest_path = _load_manifest(out)
    path = build_run_portal(
        out,
        title="Artifact Run Review",
        subtitle=manifest_path.name,
        sections=sections_for_manifest(manifest, out),
    )
    manifest["html_portal"] = str(path)
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
