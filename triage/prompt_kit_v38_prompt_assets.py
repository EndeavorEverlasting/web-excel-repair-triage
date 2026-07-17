"""Validate and materialize the V38 local-agent prompt support files."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "prompts" / "v38" / "local-runtime-build.md"
OUTPUT_FILENAME = "AI_Harness_Prompt_Kit_v38_local_runtime_build.md"
PROMPT_ID = "LOCAL_RUNTIME_BUILD"
PROMPT_CLASS = "local_coding_agent_runtime"
SUPPORTED_AGENTS = (
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
    "force-push",
)


@dataclass(frozen=True)
class PromptAsset:
    prompt_id: str
    prompt_class: str
    title: str
    source: str
    output: str
    sha256: str
    supported_agents: tuple[str, ...]
    validation_passed: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def load_prompt(source: Path = DEFAULT_SOURCE) -> str:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8")
    validate_prompt_text(text)
    return text


def materialize_prompt_assets(output_dir: Path, source: Path = DEFAULT_SOURCE) -> tuple[PromptAsset, ...]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    source = source.resolve()
    text = load_prompt(source)
    output = output_dir / OUTPUT_FILENAME
    output.write_text(text.rstrip() + "\n", encoding="utf-8")
    payload = output.read_bytes()
    return (
        PromptAsset(
            prompt_id=PROMPT_ID,
            prompt_class=PROMPT_CLASS,
            title="Local Runtime Build Converter",
            source=str(source),
            output=str(output),
            sha256=_sha256_bytes(payload),
            supported_agents=SUPPORTED_AGENTS,
            validation_passed=True,
        ),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=Path("Outputs/prompt_kit_v38"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        assets = materialize_prompt_assets(args.out_dir, args.source)
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
