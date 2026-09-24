#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "harness/prompt-kit-layout/manifest.v1.json"
CONTRACT = ROOT / "harness/prompt-kit-layout/contracts/responsive-header-overlap.v1.json"
DEFAULT_GEOMETRY = ROOT / "Outputs/prompt-kit-layout-geometry.json"
REQUIRED_REQUIREMENTS = {
    "no_brand_search_intersection",
    "no_filter_search_intersection",
    "no_header_escape",
    "no_horizontal_page_overflow",
    "responsive_reflow",
    "touch_target_preservation",
}


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_object(path, label, errors):
    try:
        value = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid {label}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def validate_geometry(contract, geometry_path):
    errors = []
    geometry_path = Path(geometry_path)
    if not geometry_path.exists():
        return [f"browser geometry receipt is required: {geometry_path}"]
    receipt = _load_object(geometry_path, "browser geometry receipt", errors)
    if errors:
        return errors
    if receipt.get("contract_id") != contract.get("contract_id"):
        errors.append("browser geometry receipt contract_id does not match layout contract")
    engine = receipt.get("browser_engine")
    if not isinstance(engine, str) or not engine.strip():
        errors.append("browser geometry receipt must identify browser_engine")
    rows = receipt.get("viewports")
    if not isinstance(rows, list):
        return errors + ["browser geometry receipt viewports must be an array"]
    by_id = {}
    for row in rows:
        if not isinstance(row, dict):
            errors.append("every browser geometry viewport must be an object")
            continue
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id:
            errors.append("browser geometry viewport id must be a non-empty string")
            continue
        if row_id in by_id:
            errors.append(f"duplicate browser geometry viewport id: {row_id}")
            continue
        by_id[row_id] = row
    for expected in contract.get("viewports", []):
        viewport_id = expected["id"]
        row = by_id.get(viewport_id)
        if row is None:
            errors.append(f"browser geometry missing viewport: {viewport_id}")
            continue
        if row.get("width") != expected["width"] or row.get("height") != expected["height"]:
            errors.append(f"browser geometry dimensions do not match contract: {viewport_id}")
        for field in ("brand_search_intersections", "filter_search_intersections", "horizontal_overflow_pixels"):
            if row.get(field) != 0:
                errors.append(f"{viewport_id} {field} must be 0")
        if row.get("header_escape") is not False:
            errors.append(f"{viewport_id} header_escape must be false")
        if row.get("responsive_reflow") is not True:
            errors.append(f"{viewport_id} responsive_reflow must be true")
        if row.get("touch_targets_usable") is not True:
            errors.append(f"{viewport_id} touch_targets_usable must be true")
    extra = sorted(set(by_id) - {item["id"] for item in contract.get("viewports", [])})
    if extra:
        errors.append("browser geometry contains undeclared viewports: " + ", ".join(extra))
    return errors


def validate(require_implementation=False, manifest_path=MANIFEST, contract_path=CONTRACT, geometry_path=None):
    errors = []
    manifest = _load_object(manifest_path, "layout manifest", errors)
    components = manifest.get("components")
    if not isinstance(components, dict):
        errors.append("manifest components must be an object")
        components = {}
    for name, rel in components.items():
        if not isinstance(name, str) or not isinstance(rel, str) or not rel:
            errors.append(f"invalid component entry: {name!r} -> {rel!r}")
            continue
        if not (ROOT / rel).exists():
            errors.append(f"missing component {name}: {rel}")

    contract = _load_object(contract_path, "layout contract", errors)
    viewports = contract.get("viewports")
    if not isinstance(viewports, list):
        errors.append("contract viewports must be an array")
        viewports = []
    ids = []
    valid_viewports = []
    for item in viewports:
        if not isinstance(item, dict):
            errors.append(f"invalid viewport entry: {item!r}")
            continue
        viewport_id = item.get("id")
        if not isinstance(viewport_id, str) or not viewport_id:
            errors.append(f"invalid viewport id: {item!r}")
        else:
            ids.append(viewport_id)
        if not isinstance(item.get("width"), int) or isinstance(item.get("width"), bool) or item.get("width", 0) < 320:
            errors.append(f"invalid viewport width: {item!r}")
        if not isinstance(item.get("height"), int) or isinstance(item.get("height"), bool) or item.get("height", 0) < 480:
            errors.append(f"invalid viewport height: {item!r}")
        if isinstance(viewport_id, str) and viewport_id and isinstance(item.get("width"), int) and isinstance(item.get("height"), int):
            valid_viewports.append(item)
    if len(ids) != len(set(ids)):
        errors.append("viewport ids must be unique")
    if len(viewports) < 3:
        errors.append("at least three responsive viewports are required")

    raw_requirements = contract.get("requirements")
    if not isinstance(raw_requirements, list):
        errors.append("contract requirements must be an array")
        raw_requirements = []
    requirement_ids = set()
    for item in raw_requirements:
        if not isinstance(item, dict):
            errors.append(f"invalid requirement entry: {item!r}")
            continue
        requirement_id = item.get("id")
        if not isinstance(requirement_id, str) or not requirement_id:
            errors.append(f"invalid requirement id: {item!r}")
            continue
        requirement_ids.add(requirement_id)
    missing = sorted(REQUIRED_REQUIREMENTS - requirement_ids)
    if missing:
        errors.append("missing requirements: " + ", ".join(missing))

    acceptance = contract.get("strict_acceptance")
    if not isinstance(acceptance, dict):
        errors.append("strict_acceptance must be an object")
        acceptance = {}
    if acceptance.get("forbidden_intersections") != 0:
        errors.append("strict acceptance must allow zero intersections")
    if acceptance.get("forbidden_horizontal_overflow_pixels") != 0:
        errors.append("strict acceptance must allow zero horizontal overflow pixels")
    if acceptance.get("all_viewports_required") is not True:
        errors.append("strict acceptance must require all declared viewports")
    if acceptance.get("browser_geometry_required") is not True:
        errors.append("browser geometry must remain required")

    if require_implementation:
        if contract.get("implementation_status") != "implemented":
            errors.append("product responsive-layout implementation is not yet proven; status must be implemented")
        if valid_viewports and len(valid_viewports) == len(viewports):
            errors.extend(validate_geometry(contract, geometry_path or DEFAULT_GEOMETRY))
        else:
            errors.append("browser geometry cannot be validated until viewport contract shape is valid")
    return errors, manifest, contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-implementation", action="store_true")
    parser.add_argument("--geometry-report")
    parser.add_argument("--output")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    errors, manifest, contract = validate(args.require_implementation, geometry_path=args.geometry_report)
    report = {
        "harness_id": manifest.get("harness_id"),
        "status": "PASS" if not errors else "FAIL",
        "implementation_status": contract.get("implementation_status"),
        "require_implementation": args.require_implementation,
        "geometry_report": args.geometry_report if args.require_implementation else None,
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
