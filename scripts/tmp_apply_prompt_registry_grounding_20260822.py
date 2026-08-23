#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "scripts" / "prompt_registry_ops.py"
GROUNDING = ROOT / "scripts" / "prompt_registry_grounding.py"
TEST = ROOT / "tests" / "test_prompt_registry_grounding.py"
SPEC = ROOT / "harness" / "specs" / "prompt-operations.md"
WORKFLOW = ROOT / ".github" / "workflows" / "skill-prompt-registry.yml"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


GROUNDING.write_text(r'''#!/usr/bin/env python3
"""Deterministic JIT grounding for exact Prompt Kit registry operations."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "prompt-registry-grounding/v1"
GATE_ID = "prompt-registry-contribution/v1"
GROUNDED_PASS = "GROUNDED_PASS"
UNSOURCED_BLOCK = "UNSOURCED_BLOCK"
CONTRADICTION_BLOCK = "CONTRADICTION_BLOCK"
SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
GROUNDING_FAILURE = "GROUNDING_FAILURE"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    try:
        return _hash_bytes(path.read_bytes())
    except OSError as exc:
        raise RuntimeError(f"cannot read grounding source {path}: {exc}") from exc


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _hash_bytes(encoded)


def source_fingerprint(sources: Iterable[dict[str, Any]]) -> str:
    normalized = sorted(
        (
            {
                "source_key": str(item["source_key"]),
                "path": str(item["path"]),
                "sha256": str(item["sha256"]),
            }
            for item in sources
        ),
        key=lambda item: (item["source_key"], item["path"]),
    )
    return _fingerprint(normalized)


def packet_fingerprint(packet: dict[str, Any]) -> str:
    return _fingerprint(
        {key: value for key, value in packet.items() if key != "packet_fingerprint"}
    )


def gate_result(status: str, reason: str, **extra: Any) -> dict[str, Any]:
    result = {"status": status, "gate_id": GATE_ID, "reason": reason}
    result.update(extra)
    return result


def build_packet(
    *,
    repo_root: Path,
    registry_module: Any,
    helper_path: Path,
    required_fields: set[str],
    optional_fields: set[str],
    auto_fields: set[str],
    next_identity: dict[str, str],
    registries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a compact source-pinned packet without loading prompt bodies into it."""
    registry_entries: list[dict[str, Any]] = []
    source_specs: list[tuple[str, Path]] = [
        ("base_registry", registry_module.BASE_REGISTRY),
    ]
    for item in registries:
        path = repo_root / item["path"]
        source_key = f"registry:{item['registry_id']}"
        source_specs.append((source_key, path))
        registry_entries.append(
            {
                **item,
                "source_key": source_key,
                "sha256": _hash_file(path),
            }
        )
    for path in registry_module.CONTENT_REGISTRIES:
        source_specs.append((f"content_registry:{path.name}", path))
    source_specs.extend(
        [
            ("prompt_overrides", registry_module.PROMPT_OVERRIDES),
            ("actionability_policy", registry_module.ACTIONABILITY_POLICY),
            ("builder", Path(registry_module.__file__).resolve()),
            ("helper", helper_path.resolve()),
        ]
    )

    seen: set[Path] = set()
    sources: list[dict[str, str]] = []
    for source_key, path in source_specs:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        sources.append(
            {
                "source_key": source_key,
                "path": _relative(resolved, repo_root),
                "sha256": _hash_file(resolved),
            }
        )

    policy = registry_module.load_actionability_policy()
    builder_path = _relative(Path(registry_module.__file__).resolve(), repo_root)
    policy_path = _relative(registry_module.ACTIONABILITY_POLICY, repo_root)
    packet: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "gate_id": GATE_ID,
        "source_fingerprint": source_fingerprint(sources),
        "sources": sources,
        "registries": registry_entries,
        "next_identity": dict(next_identity),
        "draft_fields": {
            "required": sorted(required_fields),
            "optional": sorted(optional_fields),
            "auto_owned": sorted(auto_fields),
        },
        "actionability_policy": {
            "policy_id": policy["policy_id"],
            "path": policy_path,
            "sha256": _hash_file(registry_module.ACTIONABILITY_POLICY),
        },
        "builder": {
            "path": builder_path,
            "sha256": _hash_file(Path(registry_module.__file__).resolve()),
        },
        "output": _relative(registry_module.DEFAULT_OUTPUT, repo_root),
    }
    packet["packet_fingerprint"] = packet_fingerprint(packet)
    return packet


def validate_packet(
    supplied: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(supplied, dict):
        return gate_result(SCHEMA_MISMATCH, "grounding_packet_not_object")
    if supplied.get("schema_version") != SCHEMA_VERSION:
        return gate_result(
            SCHEMA_MISMATCH,
            "grounding_schema_mismatch",
            expected=SCHEMA_VERSION,
            actual=supplied.get("schema_version"),
        )
    claimed_source = supplied.get("source_fingerprint")
    claimed_packet = supplied.get("packet_fingerprint")
    if not isinstance(claimed_source, str) or not _HEX64.fullmatch(claimed_source):
        return gate_result(SCHEMA_MISMATCH, "invalid_source_fingerprint")
    if not isinstance(claimed_packet, str) or not _HEX64.fullmatch(claimed_packet):
        return gate_result(SCHEMA_MISMATCH, "invalid_packet_fingerprint")
    if packet_fingerprint(supplied) != claimed_packet:
        return gate_result(CONTRADICTION_BLOCK, "tampered_grounding_packet")
    if claimed_packet != current["packet_fingerprint"]:
        return gate_result(
            CONTRADICTION_BLOCK,
            "stale_source_identity",
            supplied_source_fingerprint=claimed_source,
            current_source_fingerprint=current["source_fingerprint"],
            supplied_packet_fingerprint=claimed_packet,
            current_packet_fingerprint=current["packet_fingerprint"],
        )
    return gate_result(
        GROUNDED_PASS,
        "grounding_packet_current",
        source_fingerprint=current["source_fingerprint"],
        packet_fingerprint=current["packet_fingerprint"],
    )
''', encoding="utf-8")

ops = OPS.read_text(encoding="utf-8")
ops = replace_once(
    ops,
    'from scripts import build_prompt_kit_registry as registry  # noqa: E402\n',
    'from scripts import build_prompt_kit_registry as registry  # noqa: E402\nfrom scripts import prompt_registry_grounding as grounding  # noqa: E402\n',
    "grounding import",
)
ops = replace_once(
    ops,
    'def _read_json(path_value: str) -> dict[str, Any]:\n',
    'def _read_json(path_value: str, noun: str = "Prompt draft") -> dict[str, Any]:\n',
    "read-json signature",
)
ops = replace_once(
    ops,
    '        raise SystemExit(f"Prompt draft is invalid JSON ({label}): {exc}") from exc\n    if not isinstance(payload, dict):\n        raise SystemExit("Prompt draft must be one JSON object")\n',
    '        raise SystemExit(f"{noun} is invalid JSON ({label}): {exc}") from exc\n    if not isinstance(payload, dict):\n        raise SystemExit(f"{noun} must be one JSON object")\n',
    "read-json errors",
)

insert_anchor = '\n\ndef _validate_site_parity() -> tuple[bool, int]:\n'
grounding_functions = r'''


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
'''
if grounding_functions.strip() not in ops:
    ops = replace_once(ops, insert_anchor, grounding_functions + insert_anchor, "grounding functions")

start = ops.index('def add_prompt(\n')
end = ops.index('\n\ndef validate_current()', start)
new_add = r'''def _apply_prompt_record(
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
'''
ops = ops[:start] + new_add + ops[end:]

main_start = ops.index('def main(argv: list[str] | None = None) -> int:\n')
main_end = ops.index('\n\nif __name__ == "__main__":', main_start)
new_main = r'''def main(argv: list[str] | None = None) -> int:
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
'''
ops = ops[:main_start] + new_main + ops[main_end:]
OPS.write_text(ops, encoding="utf-8")

TEST.write_text(r'''from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import prompt_registry_grounding as grounding
from scripts import prompt_registry_ops

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "harness" / "specs" / "prompt-operations.md"


def fixture_draft() -> dict[str, object]:
    return {
        "name": "Grounding Gate Test Fixture",
        "type": "MAINTENANCE",
        "class": "PROMPT KIT / TEST",
        "sprintRole": "Exercise deterministic prompt grounding",
        "useWhen": "A grounding gate regression is required.",
        "inspectFirst": "Current registry truth.",
        "expectedOutput": "A source-pinned dry-run prompt record.",
        "nextStep": "Validate the grounded record.",
        "proofGate": "No protected write occurs before GROUNDED_PASS.",
        "copyContent": "EXECUTE A DETERMINISTIC GROUNDED PROMPT REGISTRY TEST. " * 12,
        "keywords": ["grounding gate fixture", "registry grounding fixture"],
        "profile": "spec-architecture",
        "color": "Cyan",
    }


class PromptRegistryGroundingTests(unittest.TestCase):
    def test_grounding_packet_is_source_pinned_and_compact(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        self.assertEqual(packet["schema_version"], grounding.SCHEMA_VERSION)
        self.assertEqual(packet["gate_id"], grounding.GATE_ID)
        self.assertRegex(packet["source_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertRegex(packet["packet_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertRegex(packet["next_identity"]["id"], r"^P\d+$")
        self.assertEqual(
            packet["next_identity"]["copySheet"],
            f"{packet['next_identity']['id']}_COPY_SAFE",
        )
        self.assertIn("id", packet["draft_fields"]["auto_owned"])
        self.assertIn("spec-architecture-prompts", {r["registry_id"] for r in packet["registries"]})
        self.assertTrue(all(len(item["sha256"]) == 64 for item in packet["sources"]))
        serialized = json.dumps(packet)
        self.assertNotIn("copyContent", serialized)
        self.assertNotIn("keywords", serialized)

    def test_valid_proposal_passes_with_resolvable_attribution(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", packet
        )
        self.assertEqual(gate["status"], grounding.GROUNDED_PASS)
        self.assertEqual(gate["record"]["id"], packet["next_identity"]["id"])
        self.assertEqual(
            gate["attribution"]["registry_id"]["selector"], "$.registry_id"
        )
        self.assertEqual(
            gate["attribution"]["draft_schema"]["path"],
            "scripts/prompt_registry_ops.py",
        )

    def test_hallucinated_registry_is_unsourced_block(self) -> None:
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "invented-agent-memory-registry"
        )
        self.assertEqual(gate["status"], grounding.UNSOURCED_BLOCK)
        self.assertIn("Unknown registry_id", gate["detail"])

    def test_model_supplied_auto_identity_is_schema_mismatch(self) -> None:
        draft = fixture_draft()
        draft["id"] = "P999"
        gate = prompt_registry_ops.ground_prompt_proposal(
            draft, "spec-architecture-prompts"
        )
        self.assertEqual(gate["status"], grounding.SCHEMA_MISMATCH)
        self.assertIn("auto-owned fields", gate["detail"])

    def test_tampered_packet_is_contradiction_block(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        tampered = copy.deepcopy(packet)
        tampered["next_identity"]["id"] = "P999"
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", tampered
        )
        self.assertEqual(gate["status"], grounding.CONTRADICTION_BLOCK)
        self.assertEqual(gate["reason"], "tampered_grounding_packet")

    def test_coherently_stale_packet_is_contradiction_block(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        stale = copy.deepcopy(packet)
        stale["sources"][0]["sha256"] = "0" * 64
        stale["source_fingerprint"] = grounding.source_fingerprint(stale["sources"])
        stale["packet_fingerprint"] = grounding.packet_fingerprint(stale)
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", stale
        )
        self.assertEqual(gate["status"], grounding.CONTRADICTION_BLOCK)
        self.assertEqual(gate["reason"], "stale_source_identity")

    def test_malformed_grounding_schema_fails_closed(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        packet["schema_version"] = "prompt-registry-grounding/v999"
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", packet
        )
        self.assertEqual(gate["status"], grounding.SCHEMA_MISMATCH)
        self.assertEqual(gate["reason"], "grounding_schema_mismatch")

    def test_stale_packet_blocks_side_effect_path(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        stale = copy.deepcopy(packet)
        stale["sources"][0]["sha256"] = "0" * 64
        stale["source_fingerprint"] = grounding.source_fingerprint(stale["sources"])
        stale["packet_fingerprint"] = grounding.packet_fingerprint(stale)
        with mock.patch.object(prompt_registry_ops, "_apply_prompt_record") as apply:
            with self.assertRaises(SystemExit):
                prompt_registry_ops.add_prompt(
                    fixture_draft(),
                    "spec-architecture-prompts",
                    dry_run=False,
                    grounding_packet=stale,
                )
            apply.assert_not_called()

    def test_valid_gate_reaches_side_effect_path_exactly_once(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        with mock.patch.object(
            prompt_registry_ops,
            "_apply_prompt_record",
            return_value={"status": "added-for-test"},
        ) as apply:
            result = prompt_registry_ops.add_prompt(
                fixture_draft(),
                "spec-architecture-prompts",
                dry_run=False,
                grounding_packet=packet,
            )
        self.assertEqual(result["status"], "added-for-test")
        apply.assert_called_once()
        gate = apply.call_args.args[3]
        self.assertEqual(gate["status"], grounding.GROUNDED_PASS)

    def test_dry_run_carries_grounding_receipt_without_mutation(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        target = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
        before = target.read_bytes()
        result = prompt_registry_ops.add_prompt(
            fixture_draft(),
            "spec-architecture-prompts",
            dry_run=True,
            grounding_packet=packet,
        )
        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["grounding_gate"]["status"], grounding.GROUNDED_PASS)
        self.assertEqual(target.read_bytes(), before)

    def test_prompt_operations_contract_keeps_grounding_automatic_and_jit(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        for phrase in (
            "Exact prompt-contribution grounding",
            "prompt_registry_ops.py ground",
            "prompt_registry_ops.py check",
            "`add` repeats the gate internally",
            "GROUNDED_PASS",
            "stale or tampered",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

spec = SPEC.read_text(encoding="utf-8")
section = r'''
## Exact prompt-contribution grounding

Exact registry mechanics are a deterministic tool boundary, not model-memory work. `scripts/prompt_registry_ops.py` owns a compact JIT grounding packet containing current registry IDs/paths, next auto-owned identity, draft-field contract, actionability policy identity, builder/output identity, and SHA-256 provenance for only the canonical structural sources that can affect those values. It does **not** load prompt bodies into the grounding packet.

For an agent or tool that needs exact structure before composing a contribution, use:

```bash
python scripts/prompt_registry_ops.py ground > /tmp/prompt-grounding.json
python scripts/prompt_registry_ops.py check --input <draft.json> --registry <registry_id> --grounding /tmp/prompt-grounding.json
```

The check is read-only and returns one fail-closed gate state: `GROUNDED_PASS`, `UNSOURCED_BLOCK`, `CONTRADICTION_BLOCK`, `SCHEMA_MISMATCH`, or `GROUNDING_FAILURE`. Critical parameters carry resolvable source-key/path/selector attribution. A stale or tampered grounding packet is never treated as PASS.

Ordinary contributors do not need extra ceremony: `add` repeats the gate internally immediately before its protected registry/site write path. Supplying `--grounding` pins the add to a previously emitted packet; if canonical structural inputs moved, the add blocks and must refresh rather than silently allocating from stale memory. Auto-owned `id`, `seq`, and `copySheet` remain forbidden in drafts.

Model critics may help with semantic prompt quality, but they do not override deterministic registry/schema/grounding failures.

'''
anchor = "## Copy-safe and reference surfaces\n"
if "## Exact prompt-contribution grounding" not in spec:
    spec = replace_once(spec, anchor, section + anchor, "prompt-operations grounding section")
SPEC.write_text(spec, encoding="utf-8")

workflow = WORKFLOW.read_text(encoding="utf-8")
for marker in (
    "      - scripts/build_prompt_kit_registry.py\n",
):
    additions = (
        marker
        + "      - scripts/prompt_registry_ops.py\n"
        + "      - scripts/prompt_registry_grounding.py\n"
        + "      - tests/test_prompt_registry_grounding.py\n"
        + "      - harness/specs/prompt-operations.md\n"
    )
    # two path blocks (pull_request and push)
    if workflow.count("      - scripts/prompt_registry_ops.py\n") < 2:
        workflow = workflow.replace(marker, additions)

compile_anchor = "            scripts/build_prompt_kit_registry.py \\\n            scripts/prompt_kit_generator_gui.py \\\n"
compile_replacement = "            scripts/build_prompt_kit_registry.py \\\n            scripts/prompt_registry_ops.py \\\n            scripts/prompt_registry_grounding.py \\\n            scripts/prompt_kit_generator_gui.py \\\n            tests/test_prompt_registry_grounding.py \\\n"
workflow = replace_once(workflow, compile_anchor, compile_replacement, "workflow compile")
run_anchor = "          python -m unittest tests.test_skill_prompt_registry -v\n          python -m unittest tests.test_actionable_prompt_registry -v\n"
run_replacement = "          python -m unittest tests.test_skill_prompt_registry -v\n          python -m unittest tests.test_actionable_prompt_registry -v\n          python -m unittest tests.test_prompt_registry_grounding -v\n"
workflow = replace_once(workflow, run_anchor, run_replacement, "workflow tests")
WORKFLOW.write_text(workflow, encoding="utf-8")

print("patched prompt registry grounding gate")
