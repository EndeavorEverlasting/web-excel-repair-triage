#!/usr/bin/env python3
"""Validate that every Prompt Kit delivery surface has one canonical release identity."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = Path("harness/contracts/prompt-kit-release-identity.v1.json")
ARTIFACTS_REL = Path("harness/artifacts.v1.json")
PORTABILITY_CONTRACT_REL = Path("harness/contracts/prompt-kit-portability.v1.json")
PORTABLE_BUILDER_REL = Path("scripts/serve_prompt_kit_portable.py")
FRESHNESS_CONTRACT_REL = Path("harness/contracts/prompt-kit-freshness-guidance.v1.json")
PAGES_WORKFLOW_REL = Path(".github/workflows/prompt-kit-pages.yml")
CANONICAL_ARTIFACT = "web/prompt-kit/index.html"
CANONICAL_PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"


class ReleaseIdentityError(RuntimeError):
    pass


def load_json(root: Path, relative: Path) -> Any:
    path = root / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseIdentityError(f"missing required file: {relative.as_posix()}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseIdentityError(f"invalid JSON: {relative.as_posix()}: {exc}") from exc


def load_text(root: Path, relative: Path) -> str:
    path = root / relative
    if not path.is_file():
        raise ReleaseIdentityError(f"missing required file: {relative.as_posix()}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ReleaseIdentityError(f"required file is empty: {relative.as_posix()}")
    return text


def validate_contract(root: Path) -> str:
    contract = load_json(root, CONTRACT_REL)
    if contract.get("schema_version") != "prompt-kit-release-identity/v1":
        raise ReleaseIdentityError("release-identity contract schema drifted")
    expected = {
        "repository": "EndeavorEverlasting/web-excel-repair-triage",
        "default_branch": "main",
        "artifact_id": "prompt-kit-website",
        "canonical_artifact": CANONICAL_ARTIFACT,
        "canonical_public_url": CANONICAL_PUBLIC_URL,
    }
    for field, value in expected.items():
        if contract.get(field) != value:
            raise ReleaseIdentityError(f"contract {field} drifted: {contract.get(field)!r}")
    identity_rule = str(contract.get("identity_rule", ""))
    if "one Prompt Kit website release" not in identity_rule:
        raise ReleaseIdentityError("identity rule no longer declares one Prompt Kit release")
    label_policy = str(contract.get("release_identity", {}).get("version_label_policy", ""))
    if "never sufficient proof" not in label_policy:
        raise ReleaseIdentityError("visible version labels must not become freshness authority")
    failures = contract.get("drift_failures")
    if not isinstance(failures, list) or len(failures) < 6:
        raise ReleaseIdentityError("release-identity contract needs explicit drift failures")
    return "release identity contract is canonical and fail-closed"


def validate_artifact_registry(root: Path) -> str:
    payload = load_json(root, ARTIFACTS_REL)
    sites = [item for item in payload.get("artifacts", []) if item.get("id") == "prompt-kit-website"]
    if len(sites) != 1:
        raise ReleaseIdentityError("artifact registry must contain exactly one prompt-kit-website")
    site = sites[0]
    if site.get("canonical_path") != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError("prompt-kit-website canonical path drifted")
    surfaces = set(site.get("delivery_surfaces", []))
    required = {CANONICAL_PUBLIC_URL, "Open-Latest-PromptKit.cmd"}
    if not required.issubset(surfaces):
        raise ReleaseIdentityError("prompt-kit-website delivery surfaces are incomplete")
    policy = str(site.get("tracking_policy", ""))
    if "without creating a second editable Prompt Kit" not in policy:
        raise ReleaseIdentityError("artifact registry no longer forbids a second editable Prompt Kit")
    return "artifact registry resolves one canonical Prompt Kit website"


def validate_pages(root: Path) -> str:
    text = load_text(root, PAGES_WORKFLOW_REL)
    required = (
        'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"',
        'cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html',
    )
    for marker in required:
        if marker not in text:
            raise ReleaseIdentityError(f"Pages workflow lost canonical parity marker: {marker}")
    if 'cp "$SITE_ROOT/index.html" "$SITE_ROOT/prompt-kit/index.html"' in text and CANONICAL_ARTIFACT not in text:
        raise ReleaseIdentityError("Pages workflow may not derive Prompt Kit identity from an unregistered root index")
    return "Pages bundle is required to match the canonical tracked Prompt Kit"


def validate_portable_derivative(root: Path) -> str:
    contract = load_json(root, PORTABILITY_CONTRACT_REL)
    integration = contract.get("integration", {})
    artifact_rules = contract.get("artifact_rules", {}).get("portable_runtime_artifact", {})
    if integration.get("canonical_site") != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError("portability contract canonical site drifted")
    if artifact_rules.get("source") != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError("portable runtime source is not the canonical Prompt Kit")
    builder = load_text(root, PORTABLE_BUILDER_REL)
    required = (
        'parser.add_argument("--source", default="web/prompt-kit/index.html")',
        '"sha256": sha256_bytes(source_bytes)',
        '"canonical_site_untouched": True',
    )
    for marker in required:
        if marker not in builder:
            raise ReleaseIdentityError(f"portable builder lost source-identity evidence: {marker}")
    return "portable local site is a hash-recorded derivative of the canonical artifact"


def validate_freshness(root: Path) -> str:
    contract = load_json(root, FRESHNESS_CONTRACT_REL)
    browser_route = str(contract.get("freshness_routes", {}).get("browser-use", ""))
    if CANONICAL_PUBLIC_URL not in browser_route:
        raise ReleaseIdentityError("freshness browser route no longer names the canonical public Prompt Kit")
    anti_patterns = "\n".join(str(item) for item in contract.get("anti_patterns", []))
    if "version label" not in anti_patterns or "current without checking" not in anti_patterns:
        raise ReleaseIdentityError("freshness guidance must reject version-label-only currentness")
    return "freshness guidance rejects stale local/version-label authority"


def validate_release_identity(root: Path) -> list[dict[str, str]]:
    checks: list[tuple[str, Callable[[Path], str]]] = [
        ("contract", validate_contract),
        ("artifact-registry", validate_artifact_registry),
        ("pages-parity", validate_pages),
        ("portable-derivative", validate_portable_derivative),
        ("freshness", validate_freshness),
    ]
    results: list[dict[str, str]] = []
    for check_id, function in checks:
        try:
            detail = function(root)
        except ReleaseIdentityError as exc:
            results.append({"id": check_id, "status": "FAIL", "detail": str(exc)})
        else:
            results.append({"id": check_id, "status": "PASS", "detail": detail})
    return results


def build_report(root: Path) -> dict[str, Any]:
    checks = validate_release_identity(root)
    canonical_path = root / CANONICAL_ARTIFACT
    source_sha = None
    if canonical_path.is_file():
        source_sha = hashlib.sha256(canonical_path.read_bytes()).hexdigest()
    failures = [item for item in checks if item["status"] != "PASS"]
    return {
        "schema_version": "prompt-kit-release-identity-report/v1",
        "status": "FAIL" if failures else "PASS",
        "canonical_artifact": CANONICAL_ARTIFACT,
        "canonical_public_url": CANONICAL_PUBLIC_URL,
        "canonical_artifact_sha256": source_sha,
        "checks": checks,
        "failure_count": len(failures),
        "proof_ceiling": (
            "Static repository proof of canonical Prompt Kit release identity. "
            "Observed local/public/deployed equality still requires runtime hash evidence."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.expanduser().resolve()
    report = build_report(root)
    if args.output:
        output = args.output.expanduser()
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.summary or not args.output:
        print(f"Prompt Kit release identity: {report['status']}")
        print(f"canonical={report['canonical_artifact']}")
        print(f"sha256={report['canonical_artifact_sha256'] or 'unavailable'}")
        for item in report["checks"]:
            print(f"{item['status']}: {item['id']}: {item['detail']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
