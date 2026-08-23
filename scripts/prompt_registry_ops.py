#!/usr/bin/env python3
"""Low-friction, fail-closed prompt registry contribution helper."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_prompt_kit_registry as registry  # noqa: E402
from scripts import prompt_registry_grounding as grounding  # noqa: E402

PROMPT_ID_RE = re.compile(r"^P(\d+)$")
AUTO_FIELDS = {"id", "seq", "copySheet"}
REQUIRED_DRAFT_FIELDS = {
    "name",
    "type",
    "class",
    "sprintRole",
    "useWhen",
    "inspectFirst",
    "expectedOutput",
    "nextStep",
    "proofGate",
    "copyContent",
    "keywords",
}
OPTIONAL_DRAFT_FIELDS = {"registry_id", "profile", "color", "category", "progress"}


def _read_json(path_value: str, noun: str = "Prompt draft") -> dict[str, Any]:
    if path_value == "-":
        text = sys.stdin.read()
        label = "stdin"
    else:
        path = Path(path_value)
        text = path.read_text(encoding="utf-8")
        label = str(path)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{noun} is invalid JSON ({label}): {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{noun} must be one JSON object")
    return payload


def _extension_documents() -> list[tuple[Path, dict[str, Any]]]:
    documents: list[tuple[Path, dict[str, Any]]] = []
    for path in registry.EXTENSION_REGISTRIES:
        payload = registry._load_json(path)
        if not isinstance(payload, dict):
            raise SystemExit(f"Registry extension must be a JSON object: {path}")
        if payload.get("schema_version") != "prompt-registry-extension/v1":
            raise SystemExit(f"Unsupported registry extension schema in {path}")
        registry_id = payload.get("registry_id")
        prompts = payload.get("prompts")
        if not isinstance(registry_id, str) or not registry_id.strip():
            raise SystemExit(f"Registry extension has no registry_id: {path}")
        if not isinstance(prompts, list):
            raise SystemExit(f"Registry extension prompts must be an array: {path}")
        documents.append((path, payload))
    return documents


def _next_identity() -> tuple[str, str]:
    numeric_ids: list[int] = []
    for prompt in registry.load_prompt_kit_registry():
        match = PROMPT_ID_RE.fullmatch(str(prompt.get("id", "")).strip().upper())
        if match:
            numeric_ids.append(int(match.group(1)))
    if not numeric_ids:
        raise SystemExit("Prompt Kit contains no numeric P## identities")
    value = max(numeric_ids) + 1
    return f"P{value:02d}", f"{value:02d}"


def _distinct_values(prompts: list[dict[str, Any]], field: str) -> list[str]:
    values = {
        str(prompt.get(field, "")).strip()
        for prompt in prompts
        if str(prompt.get(field, "")).strip()
    }
    return sorted(values)


def inspect_state() -> dict[str, Any]:
    next_id, next_seq = _next_identity()
    registries: list[dict[str, Any]] = []
    for path, payload in _extension_documents():
        prompts = [item for item in payload["prompts"] if isinstance(item, dict)]
        registries.append(
            {
                "registry_id": payload["registry_id"],
                "path": str(path.relative_to(REPO_ROOT)),
                "prompt_count": len(prompts),
                "profiles": _distinct_values(prompts, "profile"),
                "colors": _distinct_values(prompts, "color"),
                "categories": _distinct_values(prompts, "category"),
            }
        )
    return {
        "next_id": next_id,
        "next_seq": next_seq,
        "registries": registries,
        "required_draft_fields": sorted(REQUIRED_DRAFT_FIELDS),
        "auto_fields": sorted(AUTO_FIELDS),
    }


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _validate_draft(draft: dict[str, Any]) -> None:
    forbidden = sorted(AUTO_FIELDS & set(draft))
    if forbidden:
        raise SystemExit(
            "Prompt draft must not set auto-owned fields: " + ", ".join(forbidden)
        )
    unknown = sorted(set(draft) - REQUIRED_DRAFT_FIELDS - OPTIONAL_DRAFT_FIELDS)
    if unknown:
        raise SystemExit("Prompt draft contains unknown fields: " + ", ".join(unknown))
    missing = sorted(REQUIRED_DRAFT_FIELDS - set(draft))
    if missing:
        raise SystemExit("Prompt draft is missing fields: " + ", ".join(missing))
    for field in REQUIRED_DRAFT_FIELDS - {"keywords"}:
        value = draft.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"Prompt draft field must be a non-empty string: {field}")
    keywords = draft.get("keywords")
    if not isinstance(keywords, list) or not keywords:
        raise SystemExit("Prompt draft keywords must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in keywords):
        raise SystemExit("Every prompt draft keyword must be a non-empty string")
    if len(keywords) != len({_normalize_text(item) for item in keywords}):
        raise SystemExit("Prompt draft keywords must not contain duplicates")
    copy_content = str(draft["copyContent"]).strip()
    if len(copy_content) < 300:
        raise SystemExit("Prompt draft copyContent is too small to be operational (<300 chars)")
    if len(copy_content) > 12000:
        raise SystemExit("Prompt draft copyContent exceeds the 12000-character contribution ceiling")
    if registry.load_actionability_policy()["marker"] in copy_content:
        raise SystemExit(
            "Prompt draft must not copy the shared actionability appendix; the builder owns it"
        )


def _resolve_target(
    draft: dict[str, Any], explicit_registry: str | None
) -> tuple[Path, dict[str, Any]]:
    documents = _extension_documents()
    requested = (explicit_registry or str(draft.get("registry_id", ""))).strip()
    if requested:
        matches = [item for item in documents if item[1]["registry_id"] == requested]
        if len(matches) != 1:
            choices = ", ".join(payload["registry_id"] for _, payload in documents)
            raise SystemExit(f"Unknown registry_id {requested!r}. Choices: {choices}")
        return matches[0]

    profile = str(draft.get("profile", "")).strip()
    if not profile:
        raise SystemExit(
            "Target registry is ambiguous. Supply --registry or draft.registry_id; "
            "run `python scripts/prompt_registry_ops.py inspect` for compact choices."
        )
    matches: list[tuple[Path, dict[str, Any]]] = []
    for item in documents:
        prompts = [prompt for prompt in item[1]["prompts"] if isinstance(prompt, dict)]
        profiles = set(_distinct_values(prompts, "profile"))
        if profile in profiles:
            matches.append(item)
    if len(matches) != 1:
        choices = ", ".join(payload["registry_id"] for _, payload in matches) or "none"
        raise SystemExit(
            f"Profile {profile!r} does not resolve to exactly one registry (matches: {choices}); "
            "supply --registry."
        )
    return matches[0]


def _infer_or_require(
    draft: dict[str, Any], prompts: list[dict[str, Any]], field: str
) -> str:
    explicit = str(draft.get(field, "")).strip()
    if explicit:
        return explicit
    values = _distinct_values(prompts, field)
    if len(values) == 1:
        return values[0]
    raise SystemExit(
        f"Cannot infer {field} from target registry; set it explicitly. Values: {values}"
    )


def _build_record(
    draft: dict[str, Any], target_payload: dict[str, Any]
) -> dict[str, Any]:
    _validate_draft(draft)
    prompts = [item for item in target_payload["prompts"] if isinstance(item, dict)]
    next_id, next_seq = _next_identity()
    record = {
        "id": next_id,
        "seq": next_seq,
        "name": str(draft["name"]).strip(),
        "type": str(draft["type"]).strip(),
        "class": str(draft["class"]).strip(),
        "sprintRole": str(draft["sprintRole"]).strip(),
        "progress": str(draft.get("progress", "YES")).strip() or "YES",
        "useWhen": str(draft["useWhen"]).strip(),
        "inspectFirst": str(draft["inspectFirst"]).strip(),
        "expectedOutput": str(draft["expectedOutput"]).strip(),
        "nextStep": str(draft["nextStep"]).strip(),
        "proofGate": str(draft["proofGate"]).strip(),
        "color": _infer_or_require(draft, prompts, "color"),
        "copySheet": f"{next_id}_COPY_SAFE",
        "category": _infer_or_require(draft, prompts, "category"),
        "copyContent": str(draft["copyContent"]).rstrip(),
        "keywords": [str(item).strip() for item in draft["keywords"]],
    }
    profile = str(draft.get("profile", "")).strip()
    if profile:
        record["profile"] = profile
    else:
        inferred_profile = _distinct_values(prompts, "profile")
        if len(inferred_profile) == 1:
            record["profile"] = inferred_profile[0]
    return record


def _reject_obvious_duplicate(record: dict[str, Any]) -> None:
    wanted_name = _normalize_text(str(record["name"]))
    wanted_content = _normalize_text(str(record["copyContent"]))
    for prompt in registry.load_prompt_kit_registry():
        if _normalize_text(str(prompt.get("name", ""))) == wanted_name:
            raise SystemExit(
                f"Prompt contribution duplicates existing name: {prompt.get('id')} {prompt.get('name')}"
            )
        source_content = str(prompt.get("copyContent", ""))
        marker = registry.load_actionability_policy()["marker"]
        if marker in source_content:
            source_content = source_content.split(marker, 1)[0].rstrip()
        if _normalize_text(source_content) == wanted_content:
            raise SystemExit(
                f"Prompt contribution duplicates existing copyContent: {prompt.get('id')}"
            )



def build_grounding_packet() -> dict[str, Any]:
    """Return the current compact structural dossier for exact registry operations."""
    state = inspect_state()
    return grounding.build_packet(
        repo_root=REPO_ROOT,
        registry_module=registry,
        helper_path=Path(__file__).resolve(),
        required_fields=REQUIRED_DRAFT_FIELDS,
        optional_fields=OPTIONAL_DRAFT_FIELDS,
        auto_fields=AUTO_FIELDS,
        next_identity={
            "id": state["next_id"],
            "seq": state["next_seq"],
            "copySheet": f"{state['next_id']}_COPY_SAFE",
        },
        registries=state["registries"],
    )


def _gate_status_for_error(message: str) -> str:
    lowered = message.casefold()
    if (
        "unknown registry_id" in lowered
        or "target registry is ambiguous" in lowered
        or "does not resolve to exactly one registry" in lowered
    ):
        return grounding.UNSOURCED_BLOCK
    if "duplicates existing" in lowered:
        return grounding.CONTRADICTION_BLOCK
    return grounding.SCHEMA_MISMATCH


def ground_prompt_proposal(
    draft: dict[str, Any],
    explicit_registry: str | None,
    grounding_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate all exact contribution parameters without mutating repository state."""
    try:
        current = build_grounding_packet()
    except (OSError, RuntimeError, SystemExit, ValueError) as exc:
        return grounding.gate_result(
            grounding.GROUNDING_FAILURE, "cannot_build_current_grounding", detail=str(exc)
        )

    if grounding_packet is not None:
        packet_gate = grounding.validate_packet(grounding_packet, current)
        if packet_gate["status"] != grounding.GROUNDED_PASS:
            return packet_gate

    try:
        target_path, target_payload = _resolve_target(draft, explicit_registry)
        record = _build_record(draft, target_payload)
        _reject_obvious_duplicate(record)
    except SystemExit as exc:
        message = str(exc)
        return grounding.gate_result(
            _gate_status_for_error(message),
            "proposal_rejected",
            detail=message,
            source_fingerprint=current["source_fingerprint"],
            packet_fingerprint=current["packet_fingerprint"],
        )

    registry_entry = next(
        (
            item
            for item in current["registries"]
            if item["registry_id"] == target_payload["registry_id"]
        ),
        None,
    )
    if registry_entry is None:
        return grounding.gate_result(
            grounding.UNSOURCED_BLOCK,
            "target_registry_missing_from_grounding_packet",
            registry_id=target_payload["registry_id"],
        )
    target_relative = str(target_path.relative_to(REPO_ROOT)).replace("\\", "/")
    if registry_entry["path"].replace("\\", "/") != target_relative:
        return grounding.gate_result(
            grounding.CONTRADICTION_BLOCK,
            "registry_path_contradiction",
            registry_id=target_payload["registry_id"],
            grounded_path=registry_entry["path"],
            resolved_path=target_relative,
        )

    expected_identity = current["next_identity"]
    actual_identity = {
        "id": record["id"],
        "seq": record["seq"],
        "copySheet": record["copySheet"],
    }
    if actual_identity != expected_identity:
        return grounding.gate_result(
            grounding.CONTRADICTION_BLOCK,
            "identity_contradiction",
            expected=expected_identity,
            actual=actual_identity,
        )

    return {
        "status": grounding.GROUNDED_PASS,
        "gate_id": grounding.GATE_ID,
        "reason": "proposal_matches_current_structure",
        "source_fingerprint": current["source_fingerprint"],
        "packet_fingerprint": current["packet_fingerprint"],
        "record": record,
        "attribution": {
            "registry_id": {
                "source_key": registry_entry["source_key"],
                "path": registry_entry["path"],
                "selector": "$.registry_id",
            },
            "identity": {
                "source_key": "combined_prompt_registry",
                "selector": "max(P##)+1",
            },
            "draft_schema": {
                "source_key": "helper",
                "path": "scripts/prompt_registry_ops.py",
                "selector": "REQUIRED_DRAFT_FIELDS|OPTIONAL_DRAFT_FIELDS|AUTO_FIELDS",
            },
            "actionability_policy": {
                "source_key": "actionability_policy",
                "path": current["actionability_policy"]["path"],
                "selector": "$.policy_id",
            },
            "builder": {
                "source_key": "builder",
                "path": current["builder"]["path"],
                "selector": "EXTENSION_REGISTRIES|DEFAULT_OUTPUT",
            },
        },
    }


def _validate_site_parity() -> tuple[bool, int]:
    prompts = registry.load_prompt_kit_registry()
    expected = registry.render()
    output = registry.DEFAULT_OUTPUT
    if not output.exists():
        return False, len(prompts)
    return output.read_text(encoding="utf-8") == expected, len(prompts)


def _apply_prompt_record(
    target_path: Path,
    target_payload: dict[str, Any],
    record: dict[str, Any],
    gate: dict[str, Any],
) -> dict[str, Any]:
    """Perform the protected write path after the grounding gate has passed."""
    original_registry = target_path.read_text(encoding="utf-8")
    output = registry.DEFAULT_OUTPUT
    original_output = output.read_text(encoding="utf-8") if output.exists() else None
    try:
        payload = dict(target_payload)
        payload["prompts"] = [*target_payload["prompts"], record]
        target_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        effective = {prompt["id"]: prompt for prompt in registry.load_prompt_registry()}
        if record["id"] not in effective:
            raise SystemExit(f"New prompt did not load into operational registry: {record['id']}")
        policy = registry.load_actionability_policy()
        if effective[record["id"]].get("actionabilityPolicy") != policy["policy_id"]:
            raise SystemExit("New prompt did not receive the shared actionability policy")
        registry.build(output)
        parity, prompt_count = _validate_site_parity()
        if not parity:
            raise SystemExit("Generated Prompt Kit site is not in exact registry parity")
    except BaseException:
        target_path.write_text(original_registry, encoding="utf-8")
        if original_output is None:
            output.unlink(missing_ok=True)
        else:
            output.write_text(original_output, encoding="utf-8")
        raise

    return {
        "status": "added",
        "id": record["id"],
        "seq": record["seq"],
        "name": record["name"],
        "registry_id": target_payload["registry_id"],
        "registry_path": str(target_path.relative_to(REPO_ROOT)),
        "site_path": str(output.relative_to(REPO_ROOT)),
        "prompt_count": prompt_count,
        "site_parity": True,
        "actionability_policy": registry.load_actionability_policy()["policy_id"],
        "grounding_gate": {
            key: gate[key]
            for key in (
                "status",
                "gate_id",
                "source_fingerprint",
                "packet_fingerprint",
                "attribution",
            )
        },
    }


def add_prompt(
    draft: dict[str, Any],
    explicit_registry: str | None,
    dry_run: bool,
    grounding_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate = ground_prompt_proposal(draft, explicit_registry, grounding_packet)
    if gate["status"] != grounding.GROUNDED_PASS:
        raise SystemExit(json.dumps(gate, indent=2, ensure_ascii=False))

    target_path, target_payload = _resolve_target(draft, explicit_registry)
    record = gate["record"]
    gate_summary = {
        key: gate[key]
        for key in (
            "status",
            "gate_id",
            "source_fingerprint",
            "packet_fingerprint",
            "attribution",
        )
    }
    if dry_run:
        return {
            "status": "dry-run",
            "registry_id": target_payload["registry_id"],
            "registry_path": str(target_path.relative_to(REPO_ROOT)),
            "record": record,
            "grounding_gate": gate_summary,
        }

    current_before_write = build_grounding_packet()
    if current_before_write["packet_fingerprint"] != gate["packet_fingerprint"]:
        block = grounding.gate_result(
            grounding.CONTRADICTION_BLOCK,
            "source_changed_after_gate",
            gated_packet_fingerprint=gate["packet_fingerprint"],
            current_packet_fingerprint=current_before_write["packet_fingerprint"],
        )
        raise SystemExit(json.dumps(block, indent=2, ensure_ascii=False))

    return _apply_prompt_record(target_path, target_payload, record, gate)


def validate_current() -> dict[str, Any]:
    parity, prompt_count = _validate_site_parity()
    if not parity:
        raise SystemExit(
            "Prompt Kit registry is valid but web/prompt-kit/index.html is stale; rebuild it"
        )
    return {
        "status": "valid",
        "prompt_count": prompt_count,
        "site_parity": True,
        "next_id": _next_identity()[0],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect, ground, add, and validate Prompt Kit registry contributions."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect", help="Print next identity and compact registry routing choices as JSON.")
    sub.add_parser("ground", help="Emit the current source-pinned JIT grounding packet as JSON.")
    check = sub.add_parser("check", help="Validate one proposed contribution without writing files.")
    check.add_argument("--input", required=True, help="Draft JSON path, or - for stdin.")
    check.add_argument("--registry", help="Existing registry_id; otherwise resolve from draft profile.")
    check.add_argument("--grounding", help="Previously emitted grounding packet; stale/tampered packets block.")
    add = sub.add_parser("add", help="Ground, add one prompt draft, rebuild, and validate.")
    add.add_argument("--input", required=True, help="Draft JSON path, or - for stdin.")
    add.add_argument("--registry", help="Existing registry_id; otherwise resolve from draft profile.")
    add.add_argument("--grounding", help="Previously emitted grounding packet; stale/tampered packets block.")
    add.add_argument("--dry-run", action="store_true", help="Ground and resolve without writing files.")
    sub.add_parser("validate", help="Validate current registry loading and generated-site parity.")
    args = parser.parse_args(argv)

    exit_code = 0
    if args.command == "inspect":
        result = inspect_state()
    elif args.command == "ground":
        result = build_grounding_packet()
    elif args.command == "check":
        packet = (
            _read_json(args.grounding, "Grounding packet") if args.grounding else None
        )
        result = ground_prompt_proposal(
            _read_json(args.input), args.registry, packet
        )
        if result["status"] != grounding.GROUNDED_PASS:
            exit_code = 2
    elif args.command == "add":
        packet = (
            _read_json(args.grounding, "Grounding packet") if args.grounding else None
        )
        result = add_prompt(
            _read_json(args.input), args.registry, args.dry_run, packet
        )
    else:
        result = validate_current()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
