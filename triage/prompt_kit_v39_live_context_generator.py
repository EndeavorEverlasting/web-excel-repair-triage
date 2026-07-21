"""Generate V39 with the canonical live-evidence troubleshooting P54 contract."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Mapping, Optional, Sequence

from . import harness_troubleshooting_contract as troubleshooting
from . import prompt_kit_v39_generator as base

ARTIFACT_NAME = base.ARTIFACT_NAME
DEFAULT_OUTPUT_DIR = base.DEFAULT_OUTPUT_DIR
DEFAULT_BASE_STANDARD_SPEC = base.DEFAULT_STANDARD_AI_SPEC
DEFAULT_GNHF_SPEC = base.DEFAULT_GNHF_SPEC
DEFAULT_TROUBLESHOOTING_SPEC = troubleshooting.DEFAULT_PROMPT_PATH


def _load_json(path: str | Path, *, label: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be one JSON object")
    return payload


def build_live_standard_spec(
    base_standard_spec: str | Path = DEFAULT_BASE_STANDARD_SPEC,
    troubleshooting_spec: str | Path = DEFAULT_TROUBLESHOOTING_SPEC,
    policy_path: str | Path = troubleshooting.DEFAULT_POLICY_PATH,
) -> dict:
    issues = troubleshooting.validate_all(policy_path, troubleshooting_spec)
    if issues:
        raise ValueError(f"live-evidence troubleshooting contract failed: {list(issues)[:8]}")
    payload = _load_json(base_standard_spec, label="base standard-AI prompt source")
    prompt_contract = troubleshooting.load_prompt_contract(troubleshooting_spec)
    prompt = prompt_contract["prompt"]
    section = payload.get("section")
    prompts = payload.get("prompts")
    if not isinstance(section, dict) or not isinstance(prompts, list):
        raise ValueError("base standard-AI prompt source requires section and prompts")
    expected_ids = tuple(base.STANDARD_AI_EXTENSION_IDS)
    if tuple(section.get("prompt_ids", ())) != expected_ids:
        raise ValueError(f"base standard-AI prompt IDs drifted from {list(expected_ids)}")
    matching = [index for index, item in enumerate(prompts) if item.get("prompt_id") == "P54"]
    if matching != [4]:
        raise ValueError(f"base standard-AI source requires exactly one P54 at index 4; found {matching}")
    prompts[matching[0]] = dict(prompt)
    if tuple(item.get("prompt_id") for item in prompts) != expected_ids:
        raise ValueError("live-context overlay changed the standard-AI prompt ID order")
    return payload


def _write_live_spec(
    directory: Path,
    *,
    base_standard_spec: str | Path,
    troubleshooting_spec: str | Path,
    policy_path: str | Path,
) -> Path:
    payload = build_live_standard_spec(base_standard_spec, troubleshooting_spec, policy_path)
    path = directory / "v39_standard_ai_extensions.live.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _finalize_manifest(
    manifest: dict,
    *,
    base_standard_spec: str | Path,
    troubleshooting_spec: str | Path,
    policy_path: str | Path,
) -> dict:
    manifest["generator"] = "triage.prompt_kit_v39_live_context_generator"
    prompt_sources = manifest.setdefault("prompt_sources", {})
    prompt_sources["standard_ai_base"] = str(Path(base_standard_spec))
    prompt_sources["troubleshooting_contract"] = str(Path(troubleshooting_spec))
    prompt_sources["operational_discipline"] = str(Path(policy_path))
    prompt_sources["standard_ai"] = "runtime merge of base standard-AI source plus canonical P54 contract"
    manifest["live_context_troubleshooting"] = {
        "prompt_id": "P54",
        "canonical_source": str(Path(troubleshooting_spec)),
        "derive_paths_commands_and_validators_from_current_repository": True,
        "frozen_repository_specific_paths_or_commands_allowed": False,
        "validated_local_runtime_preferred_when_available": True,
    }
    manifest["proof_ceiling"] += (
        " P54 live-context source selection and contract markers are statically enforced; the actual target "
        "repository and runtime evidence remain execution-time inputs and cannot be proven by workbook generation alone."
    )
    workbook = Path(manifest["workbook"])
    manifest_path = workbook.with_name(f"{ARTIFACT_NAME}_manifest.json")
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    base._rewrite_bundle(
        Path(manifest["bundle"]),
        {workbook.name: workbook.read_bytes(), manifest_path.name: manifest_bytes},
    )
    return manifest


def generate_v39(
    source: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    base_standard_spec: Path = DEFAULT_BASE_STANDARD_SPEC,
    troubleshooting_spec: Path = DEFAULT_TROUBLESHOOTING_SPEC,
    policy_path: Path = troubleshooting.DEFAULT_POLICY_PATH,
    gnhf_spec: Path = DEFAULT_GNHF_SPEC,
) -> dict:
    with tempfile.TemporaryDirectory(prefix="v39-live-context-") as temporary:
        live_spec = _write_live_spec(
            Path(temporary),
            base_standard_spec=base_standard_spec,
            troubleshooting_spec=troubleshooting_spec,
            policy_path=policy_path,
        )
        manifest = base.generate_v39(
            source,
            output_dir,
            standard_ai_spec=live_spec,
            gnhf_spec=gnhf_spec,
        )
    return _finalize_manifest(
        manifest,
        base_standard_spec=base_standard_spec,
        troubleshooting_spec=troubleshooting_spec,
        policy_path=policy_path,
    )


def validate_v39(
    workbook: str | Path,
    *,
    base_standard_spec: Path = DEFAULT_BASE_STANDARD_SPEC,
    troubleshooting_spec: Path = DEFAULT_TROUBLESHOOTING_SPEC,
    policy_path: Path = troubleshooting.DEFAULT_POLICY_PATH,
    gnhf_spec: Path = DEFAULT_GNHF_SPEC,
) -> base.V39SegmentedReport:
    with tempfile.TemporaryDirectory(prefix="v39-live-context-validate-") as temporary:
        live_spec = _write_live_spec(
            Path(temporary),
            base_standard_spec=base_standard_spec,
            troubleshooting_spec=troubleshooting_spec,
            policy_path=policy_path,
        )
        return base.validate_v39(
            workbook,
            standard_ai_spec=live_spec,
            gnhf_spec=gnhf_spec,
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-standard-ai-spec", type=Path, default=DEFAULT_BASE_STANDARD_SPEC)
    parser.add_argument("--troubleshooting-spec", type=Path, default=DEFAULT_TROUBLESHOOTING_SPEC)
    parser.add_argument("--policy", type=Path, default=troubleshooting.DEFAULT_POLICY_PATH)
    parser.add_argument("--gnhf-spec", type=Path, default=DEFAULT_GNHF_SPEC)
    parser.add_argument("--validate-only", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.source and not args.validate_only:
        parser.error("--source is required unless --validate-only is used")
    try:
        if args.validate_only:
            report = validate_v39(
                args.validate_only,
                base_standard_spec=args.base_standard_ai_spec,
                troubleshooting_spec=args.troubleshooting_spec,
                policy_path=args.policy,
                gnhf_spec=args.gnhf_spec,
            )
            result: Mapping[str, object] = report.to_dict()
            valid = report.valid
        else:
            result = generate_v39(
                args.source,
                args.out_dir,
                base_standard_spec=args.base_standard_ai_spec,
                troubleshooting_spec=args.troubleshooting_spec,
                policy_path=args.policy,
                gnhf_spec=args.gnhf_spec,
            )
            valid = True
    except Exception as exc:
        print(f"V39 live-context generation failed: {exc}")
        return 1
    print(
        json.dumps(result, indent=2)
        if args.json or args.validate_only
        else f"Generated: {result['workbook']}\nBundle: {result['bundle']}"
    )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
