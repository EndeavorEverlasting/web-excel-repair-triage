#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "harness/prompt-kit-layout/manifest.v1.json"
CONTRACT = ROOT / "harness/prompt-kit-layout/contracts/responsive-header-overlap.v1.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(require_implementation=False):
    errors = []
    manifest = load_json(MANIFEST)
    components = manifest.get("components", {})
    for name, rel in components.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing component {name}: {rel}")
    contract = load_json(CONTRACT)
    viewports = contract.get("viewports", [])
    ids = [item.get("id") for item in viewports]
    if len(ids) != len(set(ids)):
        errors.append("viewport ids must be unique")
    if len(viewports) < 3:
        errors.append("at least three responsive viewports are required")
    for item in viewports:
        if not isinstance(item.get("width"), int) or item["width"] < 320:
            errors.append(f"invalid viewport width: {item}")
        if not isinstance(item.get("height"), int) or item["height"] < 480:
            errors.append(f"invalid viewport height: {item}")
    requirements = {item.get("id") for item in contract.get("requirements", [])}
    required = {"no_brand_search_intersection","no_filter_search_intersection","no_header_escape","no_horizontal_page_overflow","responsive_reflow","touch_target_preservation"}
    missing = sorted(required - requirements)
    if missing:
        errors.append("missing requirements: " + ", ".join(missing))
    acceptance = contract.get("strict_acceptance", {})
    if acceptance.get("forbidden_intersections") != 0:
        errors.append("strict acceptance must allow zero intersections")
    if acceptance.get("forbidden_horizontal_overflow_pixels") != 0:
        errors.append("strict acceptance must allow zero horizontal overflow pixels")
    if not acceptance.get("browser_geometry_required"):
        errors.append("browser geometry must remain required")
    if require_implementation and contract.get("implementation_status") != "implemented":
        errors.append("product responsive-layout implementation is not yet proven; status is not implemented")
    return errors, manifest, contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-implementation", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    errors, manifest, contract = validate(args.require_implementation)
    report = {
        "harness_id": manifest.get("harness_id"),
        "status": "PASS" if not errors else "FAIL",
        "implementation_status": contract.get("implementation_status"),
        "require_implementation": args.require_implementation,
        "errors": errors,
    }
    if args.output:
        out = (ROOT / args.output).resolve()
        outputs = (ROOT / "Outputs").resolve()
        try:
            out.relative_to(outputs)
        except ValueError:
            raise SystemExit("output must be under Outputs/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        print(f"Prompt Kit responsive-layout harness: {report['status']}")
        print(f"implementation_status={report['implementation_status']}")
        for error in errors:
            print(f"FAIL: {error}")
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
