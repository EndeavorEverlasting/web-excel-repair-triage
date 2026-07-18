"""Validate and materialize declarative V38 local-agent prompt assets."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "configs" / "prompt_kit" / "v38_prompt_assets.json"
REQUIRED_AGENT_NAMES = (
    "Cosmos by Augment",
    "Cursor",
    "Codex",
    "other local coding agents",
)
REQUIRED_MARKERS = (
    "# LOCAL RUNTIME BUILD CONVERTER",
    "Cosmos by Augment",
    "Cursor",
    "direct access to the local filesystem",
    "## Local-directory discipline",
    "Set-Location",
    "git rev-parse --show-toplevel",
    "## Execution contract",
    "## Required workflow",
    "### 3. Build the local runtime surface",
    "### 4. Execute locally",
    "git diff --check",
    "git commit -m",
    "git push -u origin",
    "## Failure conditions",
    "## Safety boundary",
    "## Final response",
    "LOCAL RUNTIME PROOF",
    "proof ceiling",
)
FORBIDDEN_MARKERS = (
    "wait for me",
    "sit tight",
    "I will do this later",
)


@dataclass(frozen=True)
class PromptDefinition:
    prompt_id: str
    prompt_class: str
    execution_mode: str
    title: str
    source: Path
    output_filename: str
    supported_agents: tuple[str, ...]
    distinct_from: tuple[str, ...]
    requires_local_access: bool
    requires_runtime_execution: bool


@dataclass(frozen=True)
class PromptAsset:
    prompt_id: str
    prompt_class: str
    execution_mode: str
    title: str
    source: str
    output: str
    sha256: str
    supported_agents: tuple[str, ...]
    distinct_from: tuple[str, ...]
    registry: str
    validation_passed: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _repo_relative_path(raw: object, field: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"prompt registry {field} must be a non-empty repository-relative path")
    relative = Path(raw)
    if relative.is_absolute():
        raise ValueError(f"prompt registry {field} must be repository-relative: {raw}")
    resolved = (REPO_ROOT / relative).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"prompt registry {field} escapes the repository: {raw}") from exc
    return resolved


def load_prompt_registry(registry: Path = DEFAULT_REGISTRY) -> tuple[PromptDefinition, ...]:
    registry = registry.resolve()
    if not registry.is_file():
        raise FileNotFoundError(registry)
    try:
        payload = json.loads(registry.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid V38 prompt registry JSON: {exc}") from exc
    if payload.get("schema_version") != 1:
        raise ValueError("V38 prompt registry schema_version must equal 1")
    raw_assets = payload.get("prompt_assets")
    if not isinstance(raw_assets, list) or not raw_assets:
        raise ValueError("V38 prompt registry must define at least one prompt asset")

    definitions: list[PromptDefinition] = []
    seen_ids: set[str] = set()
    seen_outputs: set[str] = set()
    for index, raw in enumerate(raw_assets):
        if not isinstance(raw, dict):
            raise ValueError(f"V38 prompt registry entry {index} must be an object")
        prompt_id = raw.get("id")
        if not isinstance(prompt_id, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]+", prompt_id):
            raise ValueError(f"invalid V38 prompt id: {prompt_id!r}")
        if prompt_id in seen_ids:
            raise ValueError(f"duplicate V38 prompt id: {prompt_id}")
        seen_ids.add(prompt_id)

        prompt_class = raw.get("class")
        execution_mode = raw.get("execution_mode")
        if prompt_class != "local_coding_agent_runtime":
            raise ValueError(f"{prompt_id} must use class local_coding_agent_runtime")
        if execution_mode != "local_runtime_build":
            raise ValueError(f"{prompt_id} must use execution_mode local_runtime_build")

        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"{prompt_id} title must be non-empty")
        source = _repo_relative_path(raw.get("source"), f"{prompt_id}.source")
        try:
            source.relative_to(REPO_ROOT / "prompts" / "v38")
        except ValueError as exc:
            raise ValueError(f"{prompt_id} source must remain under prompts/v38") from exc

        output_filename = raw.get("output")
        if (
            not isinstance(output_filename, str)
            or not output_filename.endswith(".md")
            or Path(output_filename).name != output_filename
        ):
            raise ValueError(f"{prompt_id} output must be one Markdown filename")
        if output_filename in seen_outputs:
            raise ValueError(f"duplicate V38 prompt output: {output_filename}")
        seen_outputs.add(output_filename)

        supported_agents_raw = raw.get("supported_agents")
        if not isinstance(supported_agents_raw, list) or not all(
            isinstance(item, str) and item.strip() for item in supported_agents_raw
        ):
            raise ValueError(f"{prompt_id} supported_agents must be a non-empty string list")
        supported_agents = tuple(supported_agents_raw)
        missing_agents = [item for item in REQUIRED_AGENT_NAMES if item not in supported_agents]
        if missing_agents:
            raise ValueError(f"{prompt_id} is missing required local-agent surfaces: {missing_agents}")

        distinct_from_raw = raw.get("distinct_from")
        if not isinstance(distinct_from_raw, list) or not all(
            isinstance(item, str) and item.strip() for item in distinct_from_raw
        ):
            raise ValueError(f"{prompt_id} distinct_from must be a non-empty string list")
        distinct_from = tuple(distinct_from_raw)
        if "harness_factoring" not in distinct_from:
            raise ValueError(f"{prompt_id} must be explicitly distinct from harness_factoring")

        requires_local_access = raw.get("requires_local_access")
        requires_runtime_execution = raw.get("requires_runtime_execution")
        if requires_local_access is not True:
            raise ValueError(f"{prompt_id} must require local access")
        if requires_runtime_execution is not True:
            raise ValueError(f"{prompt_id} must require runtime execution")

        definitions.append(
            PromptDefinition(
                prompt_id=prompt_id,
                prompt_class=prompt_class,
                execution_mode=execution_mode,
                title=title.strip(),
                source=source,
                output_filename=output_filename,
                supported_agents=supported_agents,
                distinct_from=distinct_from,
                requires_local_access=requires_local_access,
                requires_runtime_execution=requires_runtime_execution,
            )
        )
    return tuple(definitions)


_DEFAULT_DEFINITION = load_prompt_registry()[0]
DEFAULT_SOURCE = _DEFAULT_DEFINITION.source
OUTPUT_FILENAME = _DEFAULT_DEFINITION.output_filename
PROMPT_ID = _DEFAULT_DEFINITION.prompt_id
PROMPT_CLASS = _DEFAULT_DEFINITION.prompt_class
SUPPORTED_AGENTS = _DEFAULT_DEFINITION.supported_agents


def validate_prompt_text(text: str) -> None:
    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    if missing:
        raise ValueError(f"local runtime prompt is missing required markers: {missing}")
    lowered = text.lower()
    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if forbidden:
        raise ValueError(f"local runtime prompt contains forbidden markers: {forbidden}")
    if "Do not merely factor" not in text:
        raise ValueError("local runtime prompt must distinguish runtime construction from factoring")
    if "Do not stop after creating scripts" not in text:
        raise ValueError("local runtime prompt must require execution after implementation")
    if "unknown or incorrect directory" not in text:
        raise ValueError("local runtime prompt must enforce correct-directory discipline")
    if "Do not force-push" not in text:
        raise ValueError("local runtime prompt must forbid force-push")


def load_prompt(source: Path = DEFAULT_SOURCE) -> str:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8")
    validate_prompt_text(text)
    return text


def materialize_prompt_assets(
    output_dir: Path,
    source: Path | None = None,
    registry: Path = DEFAULT_REGISTRY,
) -> tuple[PromptAsset, ...]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = registry.resolve()
    definitions = load_prompt_registry(registry)
    if source is not None and len(definitions) != 1:
        raise ValueError("--source override is valid only when the registry defines exactly one prompt asset")

    assets: list[PromptAsset] = []
    for definition in definitions:
        actual_source = source.resolve() if source is not None else definition.source
        text = load_prompt(actual_source)
        output = output_dir / definition.output_filename
        output.write_text(text.rstrip() + "\n", encoding="utf-8")
        assets.append(
            PromptAsset(
                prompt_id=definition.prompt_id,
                prompt_class=definition.prompt_class,
                execution_mode=definition.execution_mode,
                title=definition.title,
                source=str(actual_source),
                output=str(output),
                sha256=_sha256_bytes(output.read_bytes()),
                supported_agents=definition.supported_agents,
                distinct_from=definition.distinct_from,
                registry=str(registry),
                validation_passed=True,
            )
        )
    return tuple(assets)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("Outputs/prompt_kit_v38"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        assets = materialize_prompt_assets(args.out_dir, args.source, args.registry)
    except Exception as exc:
        print(f"V38 prompt asset generation failed: {exc}")
        return 1
    payload = [asset.to_dict() for asset in assets]
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for asset in assets:
            print(f"Generated: {asset.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
