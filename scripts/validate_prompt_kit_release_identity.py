#!/usr/bin/env python3
"""Validate that every Prompt Kit delivery surface has one canonical release identity."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Callable

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = Path("harness/contracts/prompt-kit-release-identity.v1.json")
ARTIFACTS_REL = Path("harness/artifacts.v1.json")
PORTABILITY_CONTRACT_REL = Path("harness/contracts/prompt-kit-portability.v1.json")
PORTABLE_BUILDER_REL = Path("scripts/serve_prompt_kit_portable.py")
PORTABLE_RUNTIME_REL = Path("docs/prompt-kit-favorites-portability.js")
FRESHNESS_CONTRACT_REL = Path("harness/contracts/prompt-kit-freshness-guidance.v1.json")
PAGES_WORKFLOW_REL = Path(".github/workflows/prompt-kit-pages.yml")
CANONICAL_ARTIFACT = "web/prompt-kit/index.html"
CANONICAL_PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
PAGES_BUILD_STEP = "Build Pages bundle from canonical registry"


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


def normalize_repo_relative(value: object) -> str:
    """Normalize a repository-relative path for cross-platform identity comparison."""
    text = str(value).strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return PurePosixPath(text).as_posix()


def read_required_bytes(path: Path, label: str) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ReleaseIdentityError(f"cannot read {label}: {path}: {exc}") from exc
    if not payload:
        raise ReleaseIdentityError(f"{label} is empty: {path}")
    return payload


def sha256_file(path: Path) -> str:
    """Hash exact checkout bytes; this is diagnostic and may differ after EOL conversion."""
    payload = read_required_bytes(path, "canonical artifact")
    return hashlib.sha256(payload).hexdigest()


def canonical_content_bytes(path: Path) -> bytes:
    """Return UTF-8 Prompt Kit content with only line endings normalized to LF."""
    payload = read_required_bytes(path, "canonical artifact")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReleaseIdentityError(f"canonical artifact is not UTF-8: {CANONICAL_ARTIFACT}: {exc}") from exc
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.encode("utf-8")


def sha256_canonical_content(path: Path) -> str:
    """Hash logical canonical content independent of Git checkout EOL conversion."""
    return hashlib.sha256(canonical_content_bytes(path)).hexdigest()


def validate_canonical_artifact(root: Path) -> str:
    path = root / CANONICAL_ARTIFACT
    if not path.is_file():
        raise ReleaseIdentityError(f"canonical artifact is missing: {CANONICAL_ARTIFACT}")
    content_digest = sha256_canonical_content(path)
    worktree_digest = sha256_file(path)
    return (
        "canonical Prompt Kit exists; "
        f"content SHA-256 {content_digest}; checkout-byte SHA-256 {worktree_digest}"
    )


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
    release_identity = contract.get("release_identity", {})
    label_policy = str(release_identity.get("version_label_policy", ""))
    if "never sufficient proof" not in label_policy:
        raise ReleaseIdentityError("visible version labels must not become freshness authority")
    content_hash_policy = str(release_identity.get("content_hash_policy", ""))
    if "CRLF" not in content_hash_policy or "LF" not in content_hash_policy:
        raise ReleaseIdentityError("release identity must define cross-platform line-ending normalization")
    path_policy = str(release_identity.get("path_comparison_policy", ""))
    if "forward slash" not in path_policy:
        raise ReleaseIdentityError("release identity must define cross-platform path normalization")
    failures = contract.get("drift_failures")
    if not isinstance(failures, list) or len(failures) < 8:
        raise ReleaseIdentityError("release-identity contract needs explicit drift failures")
    return "release identity contract is canonical, cross-platform, and fail-closed"


def validate_artifact_registry(root: Path) -> str:
    payload = load_json(root, ARTIFACTS_REL)
    sites = [item for item in payload.get("artifacts", []) if item.get("id") == "prompt-kit-website"]
    if len(sites) != 1:
        raise ReleaseIdentityError("artifact registry must contain exactly one prompt-kit-website")
    site = sites[0]
    if normalize_repo_relative(site.get("canonical_path", "")) != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError("prompt-kit-website canonical path drifted")
    surfaces = set(site.get("delivery_surfaces", []))
    required = {CANONICAL_PUBLIC_URL, "Open-Latest-PromptKit.cmd"}
    if not required.issubset(surfaces):
        raise ReleaseIdentityError("prompt-kit-website delivery surfaces are incomplete")
    policy = str(site.get("tracking_policy", ""))
    if "without creating a second editable Prompt Kit" not in policy:
        raise ReleaseIdentityError("artifact registry no longer forbids a second editable Prompt Kit")
    return "artifact registry resolves one canonical Prompt Kit website"


def _workflow_run_commands(text: str, step_name: str) -> list[str]:
    lines = text.splitlines()
    step_index = None
    step_indent = None
    for index, line in enumerate(lines):
        if line.strip() == f"- name: {step_name}":
            step_index = index
            step_indent = len(line) - len(line.lstrip())
            break
    if step_index is None or step_indent is None:
        raise ReleaseIdentityError(f"Pages workflow is missing step: {step_name}")

    run_index = None
    run_indent = None
    for index in range(step_index + 1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped and indent <= step_indent:
            break
        if stripped == "run: |":
            run_index = index
            run_indent = indent
            break
    if run_index is None or run_indent is None:
        raise ReleaseIdentityError(f"Pages step has no executable run block: {step_name}")

    commands: list[str] = []
    for line in lines[run_index + 1 :]:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped and indent <= run_indent:
            break
        if not stripped or stripped.startswith("#"):
            continue
        commands.append(stripped)
    return commands


def validate_pages(root: Path) -> str:
    text = load_text(root, PAGES_WORKFLOW_REL)
    commands = _workflow_run_commands(text, PAGES_BUILD_STEP)
    required = [
        "set -euo pipefail",
        'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"',
        'cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html',
    ]
    missing = [command for command in required if command not in commands]
    if missing:
        raise ReleaseIdentityError(f"Pages build step lost executable canonical parity command(s): {missing}")
    if commands.index(required[1]) > commands.index(required[2]):
        raise ReleaseIdentityError("Pages compares canonical output before building it")
    return "Pages build step executes canonical builder and byte-for-byte parity comparison"


def _load_portable_builder(root: Path) -> ModuleType:
    path = root / PORTABLE_BUILDER_REL
    if not path.is_file():
        raise ReleaseIdentityError(f"missing required file: {PORTABLE_BUILDER_REL.as_posix()}")
    spec = importlib.util.spec_from_file_location("prompt_kit_portable_release_identity_probe", path)
    if spec is None or spec.loader is None:
        raise ReleaseIdentityError("portable builder cannot be imported for behavior proof")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - exact import error is environment-specific
        raise ReleaseIdentityError(f"portable builder import failed: {exc}") from exc
    return module


def validate_portable_derivative(root: Path) -> str:
    contract = load_json(root, PORTABILITY_CONTRACT_REL)
    integration = contract.get("integration", {})
    artifact_rules = contract.get("artifact_rules", {}).get("portable_runtime_artifact", {})
    if normalize_repo_relative(integration.get("canonical_site", "")) != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError("portability contract canonical site drifted")
    if normalize_repo_relative(artifact_rules.get("source", "")) != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError("portable runtime source is not the canonical Prompt Kit")

    module = _load_portable_builder(root)
    parse_args = getattr(module, "parse_args", None)
    build_portable_artifact = getattr(module, "build_portable_artifact", None)
    if not callable(parse_args) or not callable(build_portable_artifact):
        raise ReleaseIdentityError("portable builder lost executable parse/build entry points")
    try:
        defaults = parse_args([])
    except Exception as exc:
        raise ReleaseIdentityError(f"portable builder default arguments failed: {exc}") from exc
    if normalize_repo_relative(getattr(defaults, "source", "")) != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError("portable builder default source is not the canonical Prompt Kit")

    canonical_path = root / CANONICAL_ARTIFACT
    runtime_path = root / PORTABLE_RUNTIME_REL
    if not runtime_path.is_file():
        raise ReleaseIdentityError(f"missing required file: {PORTABLE_RUNTIME_REL.as_posix()}")
    before_worktree_sha = sha256_file(canonical_path)
    before_content_sha = sha256_canonical_content(canonical_path)
    outputs_root = root / "Outputs"
    outputs_root.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="release-identity-", dir=outputs_root) as temp_dir:
            temp = Path(temp_dir)
            receipt = build_portable_artifact(
                repo_root=root,
                source_path=canonical_path,
                runtime_path=runtime_path,
                output_path=temp / "index.html",
                manifest_path=temp / "manifest.json",
                origin="http://127.0.0.1:8765/",
            )
    except Exception as exc:
        raise ReleaseIdentityError(f"portable builder behavior proof failed: {exc}") from exc

    source = receipt.get("source", {}) if isinstance(receipt, dict) else {}
    guardrails = receipt.get("guardrails", {}) if isinstance(receipt, dict) else {}
    receipt_source_path = normalize_repo_relative(source.get("path", ""))
    if receipt_source_path != CANONICAL_ARTIFACT:
        raise ReleaseIdentityError(
            "portable builder receipt does not name the canonical source path after separator normalization"
        )
    if source.get("sha256") != before_worktree_sha:
        raise ReleaseIdentityError("portable builder receipt source hash does not match checkout bytes")
    if guardrails.get("canonical_site_untouched") is not True:
        raise ReleaseIdentityError("portable builder no longer asserts canonical-site immutability")
    if sha256_file(canonical_path) != before_worktree_sha:
        raise ReleaseIdentityError("portable builder mutated the canonical Prompt Kit checkout bytes")
    if sha256_canonical_content(canonical_path) != before_content_sha:
        raise ReleaseIdentityError("portable builder mutated canonical Prompt Kit content identity")
    return (
        "portable local site behavior derives from and hash-records the canonical artifact; "
        "repository-relative receipt paths are separator-normalized"
    )


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
        ("canonical-artifact", validate_canonical_artifact),
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
    content_sha = None
    worktree_sha = None
    if canonical_path.is_file():
        try:
            content_sha = sha256_canonical_content(canonical_path)
            worktree_sha = sha256_file(canonical_path)
        except ReleaseIdentityError:
            content_sha = None
            worktree_sha = None
    failures = [item for item in checks if item["status"] != "PASS"]
    return {
        "schema_version": "prompt-kit-release-identity-report/v1",
        "status": "FAIL" if failures else "PASS",
        "canonical_artifact": CANONICAL_ARTIFACT,
        "canonical_public_url": CANONICAL_PUBLIC_URL,
        "canonical_artifact_sha256": content_sha,
        "canonical_content_sha256": content_sha,
        "canonical_worktree_sha256": worktree_sha,
        "hash_policy": "canonical content normalizes CRLF and CR to LF; worktree hash records exact checkout bytes",
        "path_policy": "repository-relative identity paths normalize backslash to forward slash before comparison",
        "checks": checks,
        "failure_count": len(failures),
        "proof_ceiling": (
            "Repository proof of canonical Prompt Kit content identity across checkout EOL/path conventions, "
            "plus executable Pages and portable-builder wiring. Observed local/public/deployed equality still "
            "requires runtime evidence from the tested machine or deployed URL."
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
        print(f"worktree_sha256={report['canonical_worktree_sha256'] or 'unavailable'}")
        for item in report["checks"]:
            print(f"{item['status']}: {item['id']}: {item['detail']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
