"""CLI for building Roster Log V2 from local JSON state."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Optional, Sequence

from triage.one_marcus_recon.path_guard import assert_output_path_allowed

from .builder import build_roster_workbook
from .schema import normalize_state


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build normalized multi-project Roster Log V2")
    parser.add_argument("--state", required=True, help="roster-log-v2/v1 JSON state")
    parser.add_argument("--output", required=True, help="new .xlsx output; source roster is never overwritten")
    parser.add_argument("--require-reconciled", action="store_true", help="fail when any attendance/allocation variance remains")
    parser.add_argument("--manifest", help="optional JSON build receipt")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.state)
    output = Path(args.output)
    if not source.exists():
        raise SystemExit(f"state file not found: {source}")
    assert_output_path_allowed(__file__, str(output))
    if source.resolve() == output.resolve():
        raise SystemExit("output must not overwrite state input")

    payload = normalize_state(json.loads(source.read_text(encoding="utf-8")))
    result = build_roster_workbook(payload, output, require_reconciled=args.require_reconciled)
    receipt = {
        "artifact": output.name,
        "schema_version": payload["schema_version"],
        "source_state": source.name,
        "source_sha256": _sha256(source),
        "artifact_sha256": _sha256(output),
        **result,
    }
    if args.manifest:
        manifest = Path(args.manifest)
        assert_output_path_allowed(__file__, str(manifest))
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
