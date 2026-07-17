"""Generate the complete V39 workbook, including P50 GitHub CLI bootstrap.

This composition layer reuses the tested package-preserving V39 generator rather
than duplicating its OOXML implementation. It combines the accepted P45-P49
local-first prompt source with the separately factored P50 repository-creation
prompt, then invokes one direct V38-to-V39 package generation pass.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Sequence

from . import prompt_kit_v39_generator as base

ARTIFACT_NAME = base.ARTIFACT_NAME
DEFAULT_OUTPUT_DIR = base.DEFAULT_OUTPUT_DIR
DEFAULT_BASE_SPEC = base.DEFAULT_SPEC_PATH
DEFAULT_REPO_PROMPT_SPEC = Path("configs/prompt_kit/v39_github_repo_creation_prompt.json")
NEW_PROMPT_IDS = tuple(f"P{number:02d}" for number in range(45, 51))
ADVANCED_STANDARD_AI_IDS = tuple(f"P{number:02d}" for number in range(37, 51))


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON prompt source {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"prompt source must contain one JSON object: {path}")
    return payload


def compose_spec(base_spec_path: Path, repo_prompt_spec_path: Path) -> dict:
    """Return one validated in-memory P45-P50 prompt specification."""
    base_spec = _load_json(base_spec_path)
    repo_spec = _load_json(repo_prompt_spec_path)
    prompt = repo_spec.get("prompt")
    if repo_spec.get("schema_version") != 1 or not isinstance(prompt, dict):
        raise ValueError("P50 prompt source requires schema_version 1 and one prompt object")
    if prompt.get("prompt_id") != "P50":
        raise ValueError("repository-creation prompt source must define P50")
    if prompt.get("surface") != "standard_ai" or prompt.get("section") != "standard_ai_advanced_local":
        raise ValueError("P50 must be a standard-AI prompt in the advanced/local section")
    lines = prompt.get("lines")
    if not isinstance(lines, list) or not lines or any(not isinstance(line, str) for line in lines):
        raise ValueError("P50 requires a non-empty list of prompt lines")
    text = "\n".join(lines)
    required = (
        "PROMPT SURFACE: STANDARD AI.",
        "DIRECTORY GATE",
        "gh auth status",
        "gh repo create",
        "gh repo view",
        "--clone",
        "--source",
        "--push",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise ValueError(f"P50 is missing required repository-bootstrap markers: {missing}")
    if "--show-token" in text and "Never use --show-token" not in text:
        raise ValueError("P50 must not authorize display of GitHub authentication tokens")
    if text.lstrip().startswith("gnhf `") or "--max-tokens" in text or "--max-iterations" in text:
        raise ValueError("P50 is a standard-AI prompt but contains GNHF launch markers")

    composed = json.loads(json.dumps(base_spec))
    prompts = composed.get("new_prompts")
    if not isinstance(prompts, list) or [item.get("prompt_id") for item in prompts] != list(NEW_PROMPT_IDS[:-1]):
        raise ValueError("base V39 prompt source must define exactly P45-P49 before P50 composition")
    prompts.append(prompt)

    sections = {section.get("id"): section for section in composed.get("sections", [])}
    advanced = sections.get("standard_ai_advanced_local")
    if not isinstance(advanced, dict):
        raise ValueError("base V39 prompt source is missing the advanced standard-AI section")
    expected_before = list(ADVANCED_STANDARD_AI_IDS[:-1])
    if advanced.get("prompt_ids") != expected_before:
        raise ValueError(
            "base V39 advanced standard-AI section must end at P49 before P50 composition; "
            f"expected {expected_before}, found {advanced.get('prompt_ids')}"
        )
    advanced["prompt_ids"] = list(ADVANCED_STANDARD_AI_IDS)
    composed["composition"] = {
        "base_prompt_source": str(base_spec_path),
        "repository_creation_prompt_source": str(repo_prompt_spec_path),
        "new_prompt_ids": list(NEW_PROMPT_IDS),
    }
    return composed


@contextmanager
def _complete_prompt_floor() -> Iterator[None]:
    """Temporarily widen the canonical generator constants to P45-P50."""
    original_new = base.NEW_PROMPT_IDS
    original_advanced = base.ADVANCED_STANDARD_AI_IDS
    base.NEW_PROMPT_IDS = NEW_PROMPT_IDS
    base.ADVANCED_STANDARD_AI_IDS = ADVANCED_STANDARD_AI_IDS
    try:
        yield
    finally:
        base.NEW_PROMPT_IDS = original_new
        base.ADVANCED_STANDARD_AI_IDS = original_advanced


def _write_composed_spec(payload: dict, directory: Path) -> Path:
    path = directory / "v39-composed-p45-p50.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _rewrite_bundle_manifest(bundle_path: Path, manifest_name: str, manifest_bytes: bytes) -> None:
    with zipfile.ZipFile(bundle_path, "r") as source:
        infos = source.infolist()
        entries = {info.filename: source.read(info.filename) for info in infos}
    if manifest_name not in entries:
        raise ValueError(f"generated V39 bundle does not contain {manifest_name}")
    entries[manifest_name] = manifest_bytes
    handle, temporary_name = tempfile.mkstemp(
        prefix=bundle_path.stem + "-",
        suffix=".zip",
        dir=str(bundle_path.parent),
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w") as output:
            for info in infos:
                output.writestr(info, entries[info.filename])
        os.replace(temporary, bundle_path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _finalize_manifest(manifest: dict, base_spec: Path, repo_prompt_spec: Path) -> dict:
    manifest["generator"] = "triage.prompt_kit_v39_composed_generator"
    manifest["composition"] = {
        "base_prompt_source": str(base_spec),
        "repository_creation_prompt_source": str(repo_prompt_spec),
        "repository_creation_prompt": "P50",
    }
    manifest["proof_ceiling"] = (
        "V39 P45-P50 prompt payloads, directory-first command guards, zero-token local tests, "
        "repository factoring, GitHub CLI repository-bootstrap safety, prompt-surface separation, "
        "package structure, formulas, calculation-chain integrity, and deterministic workbook generation. "
        "No GitHub repository is created by generation. Excel for Web behavior and operator acceptance "
        "remain a separate field gate."
    )
    manifest_path = Path(manifest["workbook"]).parent / f"{ARTIFACT_NAME}_manifest.json"
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    _rewrite_bundle_manifest(Path(manifest["bundle"]), manifest_path.name, manifest_bytes)
    return manifest


def generate_v39(
    source: Path,
    output_dir: Path,
    *,
    base_spec_path: Path = DEFAULT_BASE_SPEC,
    repo_prompt_spec_path: Path = DEFAULT_REPO_PROMPT_SPEC,
    expected_source_prompt_count: int = base.SOURCE_PROMPT_COUNT,
) -> dict:
    base_spec_path = base_spec_path.resolve()
    repo_prompt_spec_path = repo_prompt_spec_path.resolve()
    composed = compose_spec(base_spec_path, repo_prompt_spec_path)
    with tempfile.TemporaryDirectory(prefix="prompt-kit-v39-composed-") as temporary:
        composed_path = _write_composed_spec(composed, Path(temporary))
        with _complete_prompt_floor():
            manifest = base.generate_v39(
                source,
                output_dir,
                spec_path=composed_path,
                expected_source_prompt_count=expected_source_prompt_count,
            )
    return _finalize_manifest(manifest, base_spec_path, repo_prompt_spec_path)


def validate_v39(
    workbook: Path,
    *,
    base_spec_path: Path = DEFAULT_BASE_SPEC,
    repo_prompt_spec_path: Path = DEFAULT_REPO_PROMPT_SPEC,
):
    composed = compose_spec(base_spec_path.resolve(), repo_prompt_spec_path.resolve())
    with tempfile.TemporaryDirectory(prefix="prompt-kit-v39-validate-") as temporary:
        composed_path = _write_composed_spec(composed, Path(temporary))
        with _complete_prompt_floor():
            return base.validate_v39(workbook, composed_path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    parser.add_argument("--base-spec", default=DEFAULT_BASE_SPEC, type=Path)
    parser.add_argument("--repo-prompt-spec", default=DEFAULT_REPO_PROMPT_SPEC, type=Path)
    parser.add_argument("--expected-source-prompt-count", default=base.SOURCE_PROMPT_COUNT, type=int)
    parser.add_argument("--validate-only", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.source and not args.validate_only:
        parser.error("--source is required unless --validate-only is used")
    try:
        if args.validate_only:
            report = validate_v39(
                args.validate_only,
                base_spec_path=args.base_spec,
                repo_prompt_spec_path=args.repo_prompt_spec,
            )
            result = report.to_dict()
            valid = report.valid
        else:
            result = generate_v39(
                args.source,
                args.out_dir,
                base_spec_path=args.base_spec,
                repo_prompt_spec_path=args.repo_prompt_spec,
                expected_source_prompt_count=args.expected_source_prompt_count,
            )
            valid = True
    except Exception as exc:
        print(f"complete V39 generation failed: {exc}")
        return 1
    print(
        json.dumps(result, indent=2)
        if args.json or args.validate_only
        else f"Generated: {result['workbook']}\nBundle: {result['bundle']}"
    )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
