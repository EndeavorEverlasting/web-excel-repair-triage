#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def dump(path: str, value) -> None:
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def repair_p13() -> None:
    path = "registry/prompts/prompt-overrides.v1.json"
    payload = load(path)
    prompt = next((item for item in payload["overrides"] if item.get("id") == "P13"), None)
    require(prompt is not None, "P13 override missing after stack convergence")
    copy = prompt["copyContent"]

    declaration = """0. SPRINT DECLARATION BEFORE MUTATION
Before any tracked, deployment, release, merge, runtime, or durable-authority mutation, state and verify:
- repository and branch/worktree;
- lane and mission;
- owned scope and forbidden scope;
- dependencies and collision risks;
- expected tracked artifacts;
- validation order;
- proof ceiling;
- mutation authority, including whether merge/deploy/live-target mutation is actually authorized.
Preserve dirty or separately owned work through an isolated branch/worktree. A repeated-urgency signal accelerates the critical path; it never bypasses repository safety or authority.

"""
    if "0. SPRINT DECLARATION BEFORE MUTATION" not in copy:
        marker = "1. RECOVER THE RECURRENCE WITHOUT MAKING THE OPERATOR RETYPE IT"
        require(marker in copy, "P13 recurrence marker missing")
        copy = copy.replace(marker, declaration + marker, 1)

    isolation = """- dedicated branch and isolated worktree for the Sub-Part Agent writing lane;
- waiting lanes and their explicit start gates;
- shared-surface owner for generated artifacts, registries, manifests, or other collision-prone files;
- final convergence owner responsible for integrating the lane without discarding concurrent work;
"""
    if "dedicated branch and isolated worktree" not in copy:
        marker = "- dependency and start gate;\n"
        require(marker in copy, "P13 Sub-Part Agent dependency marker missing")
        copy = copy.replace(marker, marker + isolation, 1)

    prompt["copyContent"] = copy
    for keyword in ("sprint declaration", "isolated worktree", "convergence owner"):
        if keyword not in prompt["keywords"]:
            prompt["keywords"].append(keyword)
    dump(path, payload)


def repair_p65() -> None:
    path = "registry/prompts/tutorial-discovery-prompts.v1.json"
    payload = load(path)
    prompt = next((item for item in payload["prompts"] if item.get("id") == "P65"), None)
    require(prompt is not None, "P65 prompt finder missing")
    copy = prompt["copyContent"]
    route = "- P13 Repeated Friction → Urgency Recovery + Rule Repair: recover recurring stalls, missed urgency, proof-floor loops, or omitted safe parallelism while advancing the current gate.\n"
    if "P13 Repeated Friction" not in copy:
        marker = "- P14 Review and Repair:"
        require(marker in copy, "P65 P14 route marker missing")
        copy = copy.replace(marker, route + marker, 1)
    if "repeated friction or urgency" not in copy:
        marker = "2. Desired outcome: "
        idx = copy.find(marker)
        require(idx >= 0, "P65 desired-outcome questionnaire marker missing")
        end = copy.find("\n", idx)
        line = copy[idx:end]
        copy = copy[:idx] + line.replace("Desired outcome: ", "Desired outcome: recover repeated friction or urgency, ", 1) + copy[end:]
    prompt["copyContent"] = copy
    for keyword in ("repeated friction", "urgency recovery", "proof floor loop"):
        if keyword not in prompt["keywords"]:
            prompt["keywords"].append(keyword)
    dump(path, payload)


def narrow_search_alias() -> None:
    path = ROOT / "build_prompt_kit.py"
    text = path.read_text(encoding="utf-8")
    old = '    "repeating myself": "P13", "critical path": "P13",\n'
    require(old in text or '"critical path": "P13"' not in text, "Unexpected critical-path synonym form")
    text = text.replace(old, '    "repeating myself": "P13",\n')
    path.write_text(text, encoding="utf-8")


def register_layout_harness() -> None:
    manifest_path = "harness/manifest.v1.json"
    manifest = load(manifest_path)
    manifest["domain_contracts"]["prompt_kit_responsive_layout"] = {
        "contract": "harness/prompt-kit-layout/contracts/responsive-header-overlap.v1.json",
        "validator": "scripts/validate_prompt_kit_layout_harness.py",
        "contract_tests": "tests/test_prompt_kit_layout_harness.py",
        "workflow": "harness/prompt-kit-layout/WORKFLOW.md",
        "harness_gate": "python scripts/validate_prompt_kit_layout_harness.py --summary",
        "strict_product_gate": "python scripts/validate_prompt_kit_layout_harness.py --require-implementation --geometry-report Outputs/prompt-kit-layout-geometry.json --summary",
        "domain_manifest": "harness/prompt-kit-layout/manifest.v1.json",
        "skill": ".ai/skills/prompt-kit-responsive-layout/SKILL.md",
        "artifact_registry": "harness/prompt-kit-layout/artifacts.v1.json",
        "operator_report": "harness/prompt-kit-layout/reports/CURRENT_STATE.md"
    }
    skill = ".ai/skills/prompt-kit-responsive-layout/SKILL.md"
    if skill not in manifest["skills"]:
        manifest["skills"].append(skill)
    commands = [
        "python scripts/validate_prompt_kit_layout_harness.py --summary",
        "python -m unittest tests.test_prompt_kit_layout_harness -v",
    ]
    for command in reversed(commands):
        if command not in manifest["validation_order"]:
            anchor = manifest["validation_order"].index("python tests/test_prompt_kit_header_contract.py")
            manifest["validation_order"].insert(anchor, command)
    dump(manifest_path, manifest)

    capabilities_path = "harness/capabilities.v1.json"
    capabilities = load(capabilities_path)
    if not any(item.get("id") == "prompt-kit-responsive-layout" for item in capabilities["capabilities"]):
        capabilities["capabilities"].append({
            "id": "prompt-kit-responsive-layout",
            "version": "1.0.0",
            "status": "canonical",
            "skill": skill,
            "trigger_ids": ["prompt-kit-responsive-overlap"],
            "operation": "Classify Prompt Kit header/search collisions, enforce responsive source and generated-artifact contracts, and require browser geometry before strict no-overlap proof.",
            "inputs": [
                "operator overlap evidence",
                "web/prompt-kit/index.html",
                "docs/prompt-kit-polish.js",
                "harness/prompt-kit-layout/contracts/responsive-header-overlap.v1.json",
                "declared responsive viewports"
            ],
            "outputs": [
                "responsive-layout harness validation",
                "focused source/artifact regression proof",
                "browser geometry receipt for strict proof when available"
            ],
            "implementation": {"kind": "script", "path": "scripts/validate_prompt_kit_layout_harness.py"},
            "proof_ceiling": "Static harness/source/artifact proof unless a validated browser-geometry receipt covers every declared viewport."
        })
    dump(capabilities_path, capabilities)

    triggers_path = "harness/triggers.v1.json"
    triggers = load(triggers_path)
    if not any(item.get("id") == "prompt-kit-responsive-overlap" for item in triggers["triggers"]):
        triggers["triggers"].append({
            "id": "prompt-kit-responsive-overlap",
            "capability_id": "prompt-kit-responsive-layout",
            "skill": skill,
            "workflow": "harness/prompt-kit-layout/WORKFLOW.md",
            "conditions": [
                "Prompt Kit header, brand, search, filter, or navigation controls overlap",
                "responsive header regression is reported across viewport widths",
                "strict browser no-overlap proof is requested"
            ],
            "forbidden_conditions": [
                "request is unrelated to Prompt Kit layout",
                "browser geometry is claimed from static source assertions alone"
            ]
        })
    dump(triggers_path, triggers)


def replace_layout_validator() -> None:
    path = ROOT / "scripts/validate_prompt_kit_layout_harness.py"
    source = r'''#!/usr/bin/env python3
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
            errors.append("product responsive-layout implementation is not fully proven; status must be implemented")
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
'''
    path.write_text(source, encoding="utf-8")


def document_geometry_receipt() -> None:
    path = ROOT / "harness/prompt-kit-layout/ARTIFACT_REGISTRY.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Browser geometry receipt schema"
    if marker not in text:
        text += """

## Browser geometry receipt schema

Strict product proof consumes `Outputs/prompt-kit-layout-geometry.json`; a status string alone is never sufficient. The receipt must identify `contract_id`, `browser_engine`, and one `viewports` row for every declared viewport. Each row records the exact `id`, `width`, and `height`, `brand_search_intersections: 0`, `filter_search_intersections: 0`, `header_escape: false`, `horizontal_overflow_pixels: 0`, `responsive_reflow: true`, and `touch_targets_usable: true`.

The default harness gate does not fabricate this receipt. `--require-implementation` fails until a browser/geometry lane has produced and validated it.
"""
        path.write_text(text, encoding="utf-8")


def harden_repository_access_copy() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    sentence = "**Release behavior:** the public Prompt Kit link above is the GitHub Pages deployment from canonical `main`. Pull-request and feature-branch Pages checks are previews only; a Prompt Kit website change is not operator-delivered until it lands on `main` and the Pages deployment succeeds.\n\n"
    anchor = "The Prompt Kit is a separate, self-contained operator surface in this repository. You do **not** need to install the workbook-repair application just to use the prompts.\n\n"
    if sentence not in text:
        require(anchor in text, "README Prompt Kit quick-access anchor missing")
        text = text.replace(anchor, anchor + sentence, 1)
        path.write_text(text, encoding="utf-8")


def write_regression_tests() -> None:
    path = ROOT / "tests/test_prompt_kit_mainline_delivery.py"
    source = r'''import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_layout_validator():
    spec = importlib.util.spec_from_file_location("layout_validator", ROOT / "scripts/validate_prompt_kit_layout_harness.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PromptKitMainlineDeliveryTests(unittest.TestCase):
    def test_p13_declares_sprint_and_isolates_subpart_agents(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"]
        for phrase in (
            "SPRINT DECLARATION BEFORE MUTATION",
            "repository and branch/worktree",
            "owned scope and forbidden scope",
            "validation order",
            "proof ceiling",
            "mutation authority",
            "dedicated branch and isolated worktree",
            "waiting lanes and their explicit start gates",
            "shared-surface owner",
            "final convergence owner",
        ):
            self.assertIn(phrase, copy)

    def test_p65_can_route_repeated_friction_without_browser_finder(self):
        payload = load_json("registry/prompts/tutorial-discovery-prompts.v1.json")
        p65 = next(item for item in payload["prompts"] if item["id"] == "P65")
        self.assertIn("P13 Repeated Friction", p65["copyContent"])
        self.assertIn("repeated friction or urgency", p65["copyContent"])

    def test_generic_path_search_is_not_a_p13_synonym(self):
        source = (ROOT / "build_prompt_kit.py").read_text(encoding="utf-8")
        self.assertNotIn('"critical path": "P13"', source)

    def test_layout_harness_is_registered_at_root(self):
        manifest = load_json("harness/manifest.v1.json")
        capabilities = load_json("harness/capabilities.v1.json")
        triggers = load_json("harness/triggers.v1.json")
        self.assertIn("prompt_kit_responsive_layout", manifest["domain_contracts"])
        self.assertTrue(any(item["id"] == "prompt-kit-responsive-layout" for item in capabilities["capabilities"]))
        self.assertTrue(any(item["id"] == "prompt-kit-responsive-overlap" for item in triggers["triggers"]))

    def test_layout_validator_fails_closed_on_malformed_shapes(self):
        validator = load_layout_validator()
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            manifest = td / "manifest.json"
            contract = td / "contract.json"
            manifest.write_text(json.dumps({"components": []}), encoding="utf-8")
            contract.write_text(json.dumps({"viewports": ["bad"], "requirements": [42], "strict_acceptance": []}), encoding="utf-8")
            errors, _, _ = validator.validate(False, manifest, contract)
            self.assertTrue(errors)
            self.assertTrue(any("must be" in error or "invalid" in error for error in errors))

    def test_layout_strict_gate_requires_all_viewports_and_real_geometry(self):
        validator = load_layout_validator()
        manifest = ROOT / "harness/prompt-kit-layout/manifest.v1.json"
        contract_path = ROOT / "harness/prompt-kit-layout/contracts/responsive-header-overlap.v1.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            pending = td / "pending.json"
            pending.write_text(json.dumps(contract), encoding="utf-8")
            errors, _, _ = validator.validate(True, manifest, pending, td / "missing-geometry.json")
            self.assertTrue(any("status must be implemented" in error for error in errors))
            self.assertTrue(any("geometry receipt is required" in error for error in errors))

            contract["implementation_status"] = "implemented"
            contract["strict_acceptance"]["all_viewports_required"] = False
            bad_acceptance = td / "bad-acceptance.json"
            bad_acceptance.write_text(json.dumps(contract), encoding="utf-8")
            errors, _, _ = validator.validate(False, manifest, bad_acceptance)
            self.assertIn("strict acceptance must require all declared viewports", errors)

            contract["strict_acceptance"]["all_viewports_required"] = True
            implemented = td / "implemented.json"
            implemented.write_text(json.dumps(contract), encoding="utf-8")
            receipt = {
                "contract_id": contract["contract_id"],
                "browser_engine": "synthetic-test-fixture",
                "viewports": [
                    {
                        "id": item["id"], "width": item["width"], "height": item["height"],
                        "brand_search_intersections": 0,
                        "filter_search_intersections": 0,
                        "header_escape": False,
                        "horizontal_overflow_pixels": 0,
                        "responsive_reflow": True,
                        "touch_targets_usable": True,
                    }
                    for item in contract["viewports"]
                ],
            }
            geometry = td / "geometry.json"
            geometry.write_text(json.dumps(receipt), encoding="utf-8")
            errors, _, _ = validator.validate(True, manifest, implemented, geometry)
            self.assertEqual([], errors)

    def test_repo_quick_access_explains_mainline_deployment_gate(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Open the Prompt Kit", readme)
        self.assertIn("feature-branch Pages checks are previews only", readme)
        workflow = (ROOT / ".github/workflows/prompt-kit-pages.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [main]", workflow)
        self.assertIn("Deploy Prompt Kit to GitHub Pages", workflow)


if __name__ == "__main__":
    unittest.main()
'''
    path.write_text(source, encoding="utf-8")


def main() -> None:
    repair_p13()
    repair_p65()
    narrow_search_alias()
    register_layout_harness()
    replace_layout_validator()
    document_geometry_receipt()
    harden_repository_access_copy()
    write_regression_tests()


if __name__ == "__main__":
    main()
