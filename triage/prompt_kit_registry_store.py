"""Store the prompt-kit registry as a compact catalog plus bounded record shards."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional, Sequence

from .prompt_kit_registry import (
    DEFAULT_KIT_VERSION,
    PromptRegistryError,
    extract_registry,
    validate_registry,
)

CATALOG_SCHEMA = "ai-harness-prompt-registry/v1"
SHARD_SCHEMA = "ai-harness-prompt-record-shard/v1"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_store(
    workbook_path: Path,
    output_dir: Path,
    *,
    kit_version: str = DEFAULT_KIT_VERSION,
    variable_overrides_path: Optional[Path] = None,
    max_shard_bytes: int = 24000,
) -> dict[str, Any]:
    """Extract the workbook and write a compact catalog plus full-record shards."""
    if max_shard_bytes < 4096:
        raise PromptRegistryError("max_shard_bytes must be at least 4096")
    registry = extract_registry(
        workbook_path,
        kit_version=kit_version,
        variable_overrides_path=variable_overrides_path,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir = output_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for prompt in registry["prompts"]:
        candidate = current + [prompt]
        candidate_payload = {
            "schemaVersion": SHARD_SCHEMA,
            "kitVersion": kit_version,
            "promptRange": f"{candidate[0]['id']}-{candidate[-1]['id']}",
            "prompts": candidate,
        }
        encoded = (json.dumps(candidate_payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if current and len(encoded) > max_shard_bytes:
            chunks.append(current)
            current = [prompt]
        else:
            current = candidate
    if current:
        chunks.append(current)

    catalog = {key: value for key, value in registry.items() if key != "prompts"}
    catalog["promptShards"] = []
    for chunk in chunks:
        relative_path = f"shards/prompts-{chunk[0]['id']}-{chunk[-1]['id']}.json"
        shard = {
            "schemaVersion": SHARD_SCHEMA,
            "kitVersion": kit_version,
            "promptRange": f"{chunk[0]['id']}-{chunk[-1]['id']}",
            "prompts": chunk,
        }
        shard_path = output_dir / relative_path
        shard_path.write_text(json.dumps(shard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if shard_path.stat().st_size > max_shard_bytes and len(chunk) > 1:
            raise PromptRegistryError(f"prompt shard exceeds max_shard_bytes: {relative_path}")
        catalog["promptShards"].append(
            {
                "range": shard["promptRange"],
                "path": relative_path,
                "sha256": _sha256(shard_path.read_bytes()),
                "promptCount": len(chunk),
            }
        )

    catalog_path = output_dir / "prompt-registry.v1.json"
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    loaded = load_store(catalog_path)
    errors = validate_registry(loaded)
    if errors:
        raise PromptRegistryError("stored registry failed validation: " + "; ".join(errors))
    return catalog


def load_store(path: Path) -> dict[str, Any]:
    """Load and verify a compact catalog plus prompt-record shards."""
    path = path.resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, MutableMapping):
        raise PromptRegistryError("registry root must be an object")
    registry = dict(payload)
    if registry.get("schemaVersion") != CATALOG_SCHEMA:
        raise PromptRegistryError(f"unsupported catalog schema: {registry.get('schemaVersion')}")
    shard_records = registry.get("promptShards")
    if not isinstance(shard_records, list) or not shard_records:
        raise PromptRegistryError("catalog contains no promptShards")

    resolved_prompts: list[dict[str, Any]] = []
    for record in shard_records:
        if not isinstance(record, Mapping):
            raise PromptRegistryError("promptShards entries must be objects")
        relative_path = str(record.get("path", ""))
        shard_path = (path.parent / relative_path).resolve()
        if path.parent not in shard_path.parents:
            raise PromptRegistryError(f"prompt shard escapes registry directory: {relative_path}")
        shard_bytes = shard_path.read_bytes()
        if _sha256(shard_bytes) != record.get("sha256"):
            raise PromptRegistryError(f"prompt shard SHA mismatch: {relative_path}")
        shard = json.loads(shard_bytes.decode("utf-8"))
        if shard.get("schemaVersion") != SHARD_SCHEMA:
            raise PromptRegistryError(f"unsupported prompt shard schema: {relative_path}")
        if shard.get("kitVersion") != registry.get("kitVersion"):
            raise PromptRegistryError(f"prompt shard kit version mismatch: {relative_path}")
        prompts = shard.get("prompts")
        if not isinstance(prompts, list) or not prompts:
            raise PromptRegistryError(f"prompt shard contains no prompts: {relative_path}")
        if int(record.get("promptCount", -1)) != len(prompts):
            raise PromptRegistryError(f"prompt shard count mismatch: {relative_path}")
        resolved_prompts.extend(dict(prompt) for prompt in prompts)

    resolved_prompts.sort(key=lambda prompt: int(prompt.get("sequence", -1)))
    registry["prompts"] = resolved_prompts
    errors = validate_registry(registry)
    if errors:
        raise PromptRegistryError("registry validation failed: " + "; ".join(errors))
    return registry


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    extract = subcommands.add_parser("extract", help="extract a catalog plus record shards")
    extract.add_argument("workbook")
    extract.add_argument("--out", required=True)
    extract.add_argument("--kit-version", default=DEFAULT_KIT_VERSION)
    extract.add_argument("--variable-overrides")
    extract.add_argument("--max-shard-bytes", type=int, default=24000)

    validate = subcommands.add_parser("validate", help="validate a stored registry")
    validate.add_argument("registry")

    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            catalog = write_store(
                Path(args.workbook),
                Path(args.out),
                kit_version=args.kit_version,
                variable_overrides_path=Path(args.variable_overrides) if args.variable_overrides else None,
                max_shard_bytes=args.max_shard_bytes,
            )
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "prompts": catalog["source"]["promptCount"],
                        "shards": len(catalog["promptShards"]),
                        "output": str(Path(args.out) / "prompt-registry.v1.json"),
                    }
                )
            )
            return 0
        registry = load_store(Path(args.registry))
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "prompts": len(registry["prompts"]),
                    "registry": args.registry,
                }
            )
        )
        return 0
    except (OSError, json.JSONDecodeError, PromptRegistryError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
