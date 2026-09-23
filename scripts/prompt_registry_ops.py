#!/usr/bin/env python3
"""Low-friction, fail-closed prompt registry contribution helper."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_prompt_kit_registry as registry  # noqa: E402
from scripts import prompt_kit_tutorial_coverage as tutorial_coverage  # noqa: E402
from scripts import prompt_registry_external_prior_art as prior_art  # noqa: E402
from scripts import validate_prompt_quality_history as quality_history  # noqa: E402
from scripts import validate_prompt_semantic_coverage as semantic_validator  # noqa: E402

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
OPTIONAL_DRAFT_FIELDS = {"registry_id", "profile", "color", "category", "progress", "semantic_profile"}

SEMANTIC_PROFILES_PATH = REPO_ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
SEMANTIC_MIGRATIONS_PATH = REPO_ROOT / "harness" / "prompt-topology" / "prompt-capability-migrations.v1.json"
SEMANTIC_CATALOG_PATH = REPO_ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json"
QUALITY_MIGRATIONS_PATH = REPO_ROOT / "harness" / "prompt-compilation" / "prompt-semantic-migrations.v1.json"
PROMPT_STRENGTH_PATH = REPO_ROOT / "harness" / "contracts" / "prompt-strength.v1.json"
BACKUP_ROOT = REPO_ROOT / "Outputs" / "backups"

PRESENCE_ORDER = ["NONE", "AWARE", "SUPPORT", "REQUIRED"]
OWNERSHIP_ORDER = ["NONE", "SECONDARY", "PRIMARY"]
ASSIGNMENT_RELATIONS = {"IMPLEMENTS", "ROUTES_TO", "TESTS", "GUARDS", "FORBIDDEN"}
DELIVERY_SOURCES = {"CANONICAL_BODY", "SHARED_POLICY", "COMPILER_OVERLAY", "ROUTED_OWNER", "TEST_GUARD"}
SEMANTIC_PROFILE_FIELDS = {
    "direct_assignments",
    "inherited_sources",
    "evidence_refs",
    "distinct_residual",
    "transfer_targets",
}
SEMANTIC_EDITABLE_PROMPT_FIELDS = {"name", "copyContent", "sprintRole", "useWhen"}
METADATA_EDITABLE_PROMPT_FIELDS = {
    "class", "inspectFirst", "expectedOutput", "nextStep", "proofGate", "keywords",
}
EDITABLE_PROMPT_FIELDS = SEMANTIC_EDITABLE_PROMPT_FIELDS | METADATA_EDITABLE_PROMPT_FIELDS


def _read_json(path_value: str) -> dict[str, Any]:
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
        raise SystemExit(f"Prompt draft is invalid JSON ({label}): {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("Prompt draft must be one JSON object")
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
    """Allocate after every live or historical P-number so retirement never permits reuse."""
    numeric_ids: list[int] = []

    def collect(value: Any) -> None:
        match = PROMPT_ID_RE.fullmatch(str(value or "").strip().upper())
        if match:
            numeric_ids.append(int(match.group(1)))

    for prompt in registry.load_prompt_kit_registry():
        collect(prompt.get("id"))

    for path, collection in (
        (SEMANTIC_PROFILES_PATH, "profiles"),
        (SEMANTIC_MIGRATIONS_PATH, "migrations"),
    ):
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get(collection, []):
            if isinstance(row, dict):
                collect(row.get("prompt_id"))

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


def _require_complete_tutorial_coverage() -> dict[str, Any]:
    report = tutorial_coverage.audit()
    if not report["ready"]:
        raise SystemExit(
            "Prompt tutorial coverage is not ready: "
            f"route_errors={report['route_errors']} "
            f"unknown_wired_prompt_ids={report['unknown_wired_prompt_ids']}"
        )
    if report["needs_wiring_count"] != 0:
        raise SystemExit(
            "Prompt tutorial coverage contains unresolved wiring debt: "
            + ", ".join(report["needs_wiring_prompt_ids"])
        )
    if report["wired_count"] != report["prompt_count"]:
        raise SystemExit(
            "Prompt tutorial coverage is incomplete: "
            f"wired={report['wired_count']} prompts={report['prompt_count']}"
        )
    return report


def _tutorial_coverage_receipt(
    prompt_id: str, report: dict[str, Any] | None = None
) -> dict[str, Any]:
    coverage_report = report or _require_complete_tutorial_coverage()
    wanted = str(prompt_id).strip().upper()
    route = next(
        (item for item in coverage_report["routes"] if item["prompt_id"] == wanted),
        None,
    )
    if route is None:
        raise SystemExit(f"Prompt has no tutorial coverage route: {wanted}")
    if route["needs_wiring"]:
        raise SystemExit(f"Prompt still requires tutorial wiring: {wanted}")
    return {
        "prompt_id": wanted,
        "coverage_ready": True,
        "wiring_status": route["wiring_status"],
        "wiring_source": route["wiring_source"],
        "needs_wiring": False,
        "tutorial_route": list(route["tutorial_route"]),
        "tutorial_document": route["tutorial_document"],
        "tutorial_anchor": route["tutorial_anchor"],
    }


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
    tutorial_report = _require_complete_tutorial_coverage()
    return {
        "next_id": next_id,
        "next_seq": next_seq,
        "registries": registries,
        "required_draft_fields": sorted(REQUIRED_DRAFT_FIELDS),
        "auto_fields": sorted(AUTO_FIELDS),
        "tutorial_coverage": {
            "policy_id": tutorial_report["policy_id"],
            "ready": tutorial_report["ready"],
            "wired_count": tutorial_report["wired_count"],
            "prompt_count": tutorial_report["prompt_count"],
            "needs_wiring_count": tutorial_report["needs_wiring_count"],
        },
        "classification": registry.prompt_classification.classification_summary(
            registry.load_prompt_kit_registry()
        ),
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
    registry.prompt_classification.require_known_prompt_type(str(draft["type"]).strip())
    copy_content = str(draft["copyContent"]).strip()
    if len(copy_content) < 300:
        raise SystemExit("Prompt draft copyContent is too small to be operational (<300 chars)")
    if len(copy_content) > 12000:
        raise SystemExit("Prompt draft copyContent exceeds the 12000-character contribution ceiling")
    if registry.load_actionability_policy()["marker"] in copy_content:
        raise SystemExit(
            "Prompt draft must not copy the shared actionability appendix; the builder owns it"
        )
    if "semantic_profile" in draft:
        _validate_candidate_semantic_profile(draft["semantic_profile"])


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


def _reject_obvious_duplicate(candidate: dict[str, Any]) -> None:
    wanted_name = _normalize_text(str(candidate["name"]))
    wanted_content = _normalize_text(str(candidate["copyContent"]))
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


def _validate_site_parity() -> tuple[bool, int]:
    prompts = registry.load_prompt_kit_registry()
    expected = registry.render()
    output = registry.DEFAULT_OUTPUT
    if not output.exists():
        return False, len(prompts)
    return output.read_text(encoding="utf-8") == expected, len(prompts)


def review_prior_art(query_text: str) -> dict[str, Any]:
    """Expose the all-registered-source gate before a semantic ADD draft exists."""
    try:
        return prior_art.review_external_prior_art(query_text)
    except prior_art.PriorArtGateError as exc:
        raise SystemExit(
            f"Prompt pre-authoring external prior-art review failed closed: {exc}"
        ) from exc


def add_prompt(
    draft: dict[str, Any], explicit_registry: str | None, dry_run: bool
) -> dict[str, Any]:
    target_path, target_payload = _resolve_target(draft, explicit_registry)
    _validate_draft(draft)
    _reject_obvious_duplicate(draft)
    try:
        external_prior_art = prior_art.require_external_prior_art(draft)
    except prior_art.PriorArtGateError as exc:
        raise SystemExit(
            f"Prompt ADD external prior-art gate failed before identity allocation: {exc}"
        ) from exc

    # PSC008 is evaluated before identity allocation.
    semantic_profile_check = require_add_semantic_profile(draft)

    record = _build_record(draft, target_payload)
    preview = tutorial_coverage.coverage_for_prompt(record)
    if preview["needs_wiring"]:
        raise SystemExit(
            f"Prompt ADD would leave tutorial wiring incomplete: {record['id']}"
        )

    candidate_profile = _build_accepted_profile(
        record,
        draft["semantic_profile"],
        profile_version=1,
        prior_profile=None,
    )
    if dry_run:
        return {
            "status": "dry-run",
            "registry_id": target_payload["registry_id"],
            "registry_path": str(target_path.relative_to(REPO_ROOT)),
            "record": record,
            "external_prior_art": external_prior_art,
            "semantic_profile_check": semantic_profile_check,
            "semantic_profile_preview": candidate_profile,
            "tutorial_coverage": {
                "prompt_id": record["id"],
                "coverage_ready": True,
                "wiring_status": preview["wiring_status"],
                "wiring_source": preview["wiring_source"],
                "needs_wiring": False,
                "tutorial_route": list(preview["tutorial_route"]),
                "tutorial_document": preview["tutorial_document"],
                "tutorial_anchor": preview["tutorial_anchor"],
            },
        }

    new_registry = _clone_json(target_payload)
    new_registry["prompts"] = [*target_payload["prompts"], record]
    new_registry_bytes = _json_bytes(new_registry)

    profiles_data = _load_semantic_profiles()
    if any(p.get("prompt_id") == record["id"] for p in profiles_data.get("profiles", [])):
        raise SystemExit(f"Semantic profile history already contains allocated identity: {record['id']}")
    prospective_profiles = [*profiles_data.get("profiles", []), candidate_profile]
    new_profiles_data = _clone_json(profiles_data)
    new_profiles_data["profiles"] = prospective_profiles

    quality_data = _load_quality_migrations()
    quality_migration = _build_quality_history_migration(
        target_path,
        target_path.read_bytes(),
        new_registry_bytes,
        record["id"],
        "ADD",
        _distinct_residual_rationale(draft["semantic_profile"]),
        len(quality_data.get("migrations", [])),
    )
    new_quality_data = _clone_json(quality_data)
    new_quality_data.setdefault("migrations", []).append(quality_migration)

    capability_data = _load_semantic_migrations()
    capability_migration = _build_capability_migration(
        "ADD",
        record["id"],
        before_profile=None,
        after_profile=candidate_profile,
        rationale=_distinct_residual_rationale(draft["semantic_profile"]),
        evidence_refs=_semantic_evidence_refs(draft["semantic_profile"]),
        source_history_migration=quality_migration,
        existing_count=len(capability_data.get("migrations", [])),
        coverage_before=simulate_global_coverage(profiles_data.get("profiles", [])),
        coverage_after=simulate_global_coverage(prospective_profiles),
    )
    new_capability_data = _clone_json(capability_data)
    new_capability_data.setdefault("migrations", []).append(capability_migration)

    staged = {
        target_path: new_registry_bytes,
        SEMANTIC_PROFILES_PATH: _json_bytes(new_profiles_data),
        SEMANTIC_MIGRATIONS_PATH: _json_bytes(new_capability_data),
        QUALITY_MIGRATIONS_PATH: _json_bytes(new_quality_data),
    }
    receipt = _apply_lifecycle_transaction(staged, f"add-{record['id']}")

    return {
        "status": "added",
        "id": record["id"],
        "seq": record["seq"],
        "name": record["name"],
        "registry_id": target_payload["registry_id"],
        "registry_path": str(target_path.relative_to(REPO_ROOT)),
        "site_path": str(registry.DEFAULT_OUTPUT.relative_to(REPO_ROOT)),
        "prompt_count": receipt["prompt_count"],
        "site_parity": True,
        "backup_path": receipt["backup_path"],
        "actionability_policy": registry.load_actionability_policy()["policy_id"],
        "external_prior_art": external_prior_art,
        "semantic_profile_check": semantic_profile_check,
        "semantic_profile_sha256": candidate_profile["profile_sha256"],
        "capability_migration_id": capability_migration["migration_id"],
        "source_history_migration_id": quality_migration["migration_id"],
        "tutorial_coverage": _tutorial_coverage_receipt(record["id"], receipt["tutorial_coverage"]),
    }


def validate_current() -> dict[str, Any]:
    parity, prompt_count = _validate_site_parity()
    if not parity:
        raise SystemExit(
            "Prompt Kit registry is valid but web/prompt-kit/index.html is stale; rebuild it"
        )

    semantic_errors = semantic_validator.validate_repository_state()
    if semantic_errors:
        raise SystemExit("Semantic coverage validation failed: " + " | ".join(semantic_errors))
    quality_errors = quality_history.validate()
    if quality_errors:
        raise SystemExit("Prompt Quality History validation failed: " + " | ".join(quality_errors))

    coverage_report = _require_complete_tutorial_coverage()
    return {
        "status": "valid",
        "prompt_count": prompt_count,
        "site_parity": True,
        "semantic_coverage": "PASS",
        "prompt_quality_history": "PASS",
        "next_id": _next_identity()[0],
        "tutorial_coverage": {
            "policy_id": coverage_report["policy_id"],
            "ready": coverage_report["ready"],
            "wired_count": coverage_report["wired_count"],
            "prompt_count": coverage_report["prompt_count"],
            "classifier_wired_count": coverage_report["classifier_wired_count"],
            "curated_wired_count": coverage_report["curated_wired_count"],
            "needs_wiring_count": coverage_report["needs_wiring_count"],
        },
    }


# ============================================================================
# Sprint 1B + Sprint 2: Semantic coverage lifecycle extensions
# ============================================================================

def _clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _sha256_json(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _load_semantic_profiles() -> dict[str, Any]:
    return json.loads(SEMANTIC_PROFILES_PATH.read_text(encoding="utf-8"))


def _load_semantic_catalog() -> dict[str, Any]:
    return json.loads(SEMANTIC_CATALOG_PATH.read_text(encoding="utf-8"))


def _load_semantic_migrations() -> dict[str, Any]:
    return json.loads(SEMANTIC_MIGRATIONS_PATH.read_text(encoding="utf-8"))


def _load_quality_migrations() -> dict[str, Any]:
    return json.loads(QUALITY_MIGRATIONS_PATH.read_text(encoding="utf-8"))


def _repository_revision() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
        revision = proc.stdout.strip()
        if proc.returncode == 0 and re.fullmatch(r"[a-f0-9]{7,40}", revision):
            return revision
    except (OSError, subprocess.TimeoutExpired):
        pass

    fallback = str(
        _load_semantic_profiles().get("baseline", {}).get("acceptance_commit", "")
    ).strip()
    if re.fullmatch(r"[a-f0-9]{7,40}", fallback):
        return fallback
    return "0000000"


def _default_inherited_sources() -> list[dict[str, str]]:
    strength = json.loads(PROMPT_STRENGTH_PATH.read_text(encoding="utf-8"))
    return [
        {
            "source_id": "prompt-strength-shared-policy",
            "source_version": "v1",
            "source_hash": _sha256_json(strength),
        }
    ]


def _validate_candidate_semantic_profile(profile: Any) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise SystemExit("semantic_profile must be an object")

    unknown = sorted(set(profile) - SEMANTIC_PROFILE_FIELDS)
    if unknown:
        raise SystemExit(
            "semantic_profile contains unknown fields: " + ", ".join(unknown)
        )

    assignments = profile.get("direct_assignments")
    if not isinstance(assignments, list) or not assignments:
        raise SystemExit("semantic_profile.direct_assignments must be a non-empty list")

    known_capabilities = {
        row["capability_id"] for row in _load_semantic_catalog().get("capabilities", [])
    }
    required_assignment_fields = {
        "capability_id",
        "presence",
        "ownership",
        "capability_relation",
        "delivery_source",
    }
    allowed_assignment_fields = required_assignment_fields | {"evidence_refs", "rationale"}

    normalized_assignments: list[dict[str, Any]] = []
    for index, assignment in enumerate(assignments):
        if not isinstance(assignment, dict):
            raise SystemExit(f"semantic_profile.direct_assignments[{index}] must be an object")
        missing = sorted(required_assignment_fields - set(assignment))
        unknown_assignment = sorted(set(assignment) - allowed_assignment_fields)
        if missing:
            raise SystemExit(
                f"semantic_profile.direct_assignments[{index}] missing fields: "
                + ", ".join(missing)
            )
        if unknown_assignment:
            raise SystemExit(
                f"semantic_profile.direct_assignments[{index}] has unknown fields: "
                + ", ".join(unknown_assignment)
            )

        capability_id = str(assignment["capability_id"]).strip()
        if capability_id not in known_capabilities:
            raise SystemExit(
                f"PSC003 KNOWN_CAPABILITY_ONLY: semantic_profile references unknown capability {capability_id}"
            )
        presence = str(assignment["presence"]).strip()
        ownership = str(assignment["ownership"]).strip()
        relation = str(assignment["capability_relation"]).strip()
        delivery = str(assignment["delivery_source"]).strip()
        if presence not in PRESENCE_ORDER:
            raise SystemExit(f"Invalid semantic presence for {capability_id}: {presence}")
        if ownership not in OWNERSHIP_ORDER:
            raise SystemExit(f"Invalid semantic ownership for {capability_id}: {ownership}")
        if relation not in ASSIGNMENT_RELATIONS:
            raise SystemExit(f"Invalid semantic capability_relation for {capability_id}: {relation}")
        if delivery not in DELIVERY_SOURCES:
            raise SystemExit(f"Invalid semantic delivery_source for {capability_id}: {delivery}")

        evidence_refs = assignment.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or any(
            not isinstance(ref, str) or not ref.strip() for ref in evidence_refs
        ):
            raise SystemExit(f"semantic evidence_refs must be non-empty strings for {capability_id}")
        rationale = str(assignment.get("rationale", "")).strip()
        if (ownership == "PRIMARY" or presence == "REQUIRED") and (
            not evidence_refs or not rationale
        ):
            raise SystemExit(
                f"PSC011 NEW_PRIMARY_OR_REQUIRED_REQUIRES_PROOF: {capability_id} "
                "requires evidence_refs and rationale"
            )
        normalized_assignments.append(_clone_json(assignment))

    inherited = profile.get("inherited_sources", [])
    if not isinstance(inherited, list):
        raise SystemExit("semantic_profile.inherited_sources must be a list")
    for index, source in enumerate(inherited):
        if not isinstance(source, dict):
            raise SystemExit(f"semantic_profile.inherited_sources[{index}] must be an object")
        for field in ("source_id", "source_version", "source_hash"):
            if not isinstance(source.get(field), str) or not str(source[field]).strip():
                raise SystemExit(
                    f"semantic_profile.inherited_sources[{index}] requires {field}"
                )

    evidence_refs = profile.get("evidence_refs", [])
    if not isinstance(evidence_refs, list) or any(
        not isinstance(ref, str) or not ref.strip() for ref in evidence_refs
    ):
        raise SystemExit("semantic_profile.evidence_refs must contain only non-empty strings")

    residual = profile.get("distinct_residual")
    if residual is not None:
        if not isinstance(residual, dict):
            raise SystemExit("semantic_profile.distinct_residual must be an object")
        summary = str(residual.get("summary", "")).strip()
        refs = residual.get("evidence_refs", [])
        reviewed = residual.get("reviewed_against", [])
        if not summary:
            raise SystemExit("semantic_profile.distinct_residual requires summary")
        if not isinstance(refs, list) or not refs or any(
            not isinstance(ref, str) or not ref.strip() for ref in refs
        ):
            raise SystemExit("semantic_profile.distinct_residual requires evidence_refs")
        if not isinstance(reviewed, list) or not reviewed or any(
            not isinstance(prompt_id, str) or not PROMPT_ID_RE.fullmatch(prompt_id.strip())
            for prompt_id in reviewed
        ):
            raise SystemExit(
                "semantic_profile.distinct_residual requires reviewed_against prompt IDs"
            )

    transfer_targets = profile.get("transfer_targets", {})
    if not isinstance(transfer_targets, dict):
        raise SystemExit("semantic_profile.transfer_targets must be an object")
    for capability_id, prompt_id in transfer_targets.items():
        if capability_id not in known_capabilities:
            raise SystemExit(f"Unknown transfer capability: {capability_id}")
        if not isinstance(prompt_id, str) or not PROMPT_ID_RE.fullmatch(prompt_id.strip()):
            raise SystemExit(f"Invalid transfer target for {capability_id}: {prompt_id}")

    normalized = _clone_json(profile)
    normalized["direct_assignments"] = normalized_assignments
    return normalized


def _semantic_evidence_refs(profile: dict[str, Any]) -> list[str]:
    refs = {
        str(ref).strip()
        for ref in profile.get("evidence_refs", [])
        if str(ref).strip()
    }
    for assignment in profile.get("direct_assignments", []):
        refs.update(
            str(ref).strip()
            for ref in assignment.get("evidence_refs", [])
            if str(ref).strip()
        )
    residual = profile.get("distinct_residual")
    if isinstance(residual, dict):
        refs.update(
            str(ref).strip()
            for ref in residual.get("evidence_refs", [])
            if str(ref).strip()
        )
    return sorted(refs)


def _distinct_residual_rationale(profile: dict[str, Any]) -> str:
    residual = profile.get("distinct_residual")
    if isinstance(residual, dict) and str(residual.get("summary", "")).strip():
        return str(residual["summary"]).strip()
    return "Candidate introduces capability coverage not present in any accepted prompt profile."


def _check_distinct_residual_for_add(candidate: dict[str, Any]) -> dict[str, Any]:
    """Enforce PSC008 against accepted profile ownership before identity allocation."""
    candidate_profile = _validate_candidate_semantic_profile(candidate.get("semantic_profile"))
    profiles = [
        row
        for row in _load_semantic_profiles().get("profiles", [])
        if row.get("profile_status") == "ACCEPTED"
    ]

    owners_by_capability: dict[str, set[str]] = {}
    for profile in profiles:
        prompt_id = str(profile.get("prompt_id", "")).strip()
        for assignment in profile.get("direct_assignments", []):
            if (
                assignment.get("presence") != "NONE"
                or assignment.get("ownership") != "NONE"
            ):
                owners_by_capability.setdefault(
                    str(assignment.get("capability_id", "")), set()
                ).add(prompt_id)

    candidate_capabilities = {
        str(row["capability_id"]) for row in candidate_profile["direct_assignments"]
    }
    uncovered = sorted(
        capability_id
        for capability_id in candidate_capabilities
        if not owners_by_capability.get(capability_id)
    )
    if uncovered:
        return {
            "distinct_residual": True,
            "mode": "uncovered_capability",
            "uncovered_capabilities": uncovered,
            "overlapping_owners": [],
            "reason": "Candidate covers catalog capabilities with no accepted owner.",
        }

    overlapping_owners = sorted(
        {
            prompt_id
            for capability_id in candidate_capabilities
            for prompt_id in owners_by_capability.get(capability_id, set())
        }
    )
    residual = candidate_profile.get("distinct_residual")
    if isinstance(residual, dict):
        reviewed = {str(item).strip() for item in residual.get("reviewed_against", [])}
        matched = sorted(reviewed.intersection(overlapping_owners))
        if matched:
            return {
                "distinct_residual": True,
                "mode": "reviewed_residual",
                "uncovered_capabilities": [],
                "overlapping_owners": overlapping_owners,
                "reviewed_existing_owners": matched,
                "reason": str(residual["summary"]).strip(),
            }

    return {
        "distinct_residual": False,
        "mode": "absorbed_by_existing_owner",
        "uncovered_capabilities": [],
        "overlapping_owners": overlapping_owners,
        "reason": (
            "All candidate capabilities are already covered by accepted prompts and no "
            "reviewed distinct residual names a current overlapping owner."
        ),
    }


def require_add_semantic_profile(candidate: dict[str, Any]) -> dict[str, Any]:
    if "semantic_profile" not in candidate:
        raise SystemExit(
            "ADD operation requires a candidate semantic profile. "
            "Provide semantic_profile with canonical direct_assignments."
        )
    _validate_candidate_semantic_profile(candidate["semantic_profile"])
    residual_check = _check_distinct_residual_for_add(candidate)
    if not residual_check["distinct_residual"]:
        raise SystemExit(
            "PSC008 ADD_REQUIRES_DISTINCT_RESIDUAL: " + residual_check["reason"]
        )
    return {
        "profile_required": True,
        "profile_shape_valid": True,
        "distinct_residual_check": residual_check,
    }


def _build_accepted_profile(
    record: dict[str, Any],
    candidate: dict[str, Any],
    *,
    profile_version: int,
    prior_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    semantic = _validate_candidate_semantic_profile(candidate)
    inherited = semantic.get("inherited_sources") or _default_inherited_sources()
    direct = _clone_json(semantic["direct_assignments"])
    profile: dict[str, Any] = {
        "prompt_id": record["id"],
        "profile_version": profile_version,
        "canonical_prompt_hash": semantic_validator.compute_canonical_prompt_hash(record),
        "acceptance_commit": _repository_revision(),
        "direct_assignments": direct,
        "inherited_sources": _clone_json(inherited),
        "semantic_dependency_fingerprint": _sha256_json(
            {"direct": direct, "inherited": inherited}
        ),
        "evidence_refs": _semantic_evidence_refs(semantic),
        "profile_status": "ACCEPTED",
    }
    if prior_profile is not None:
        profile["prior_profile_ref"] = {
            "profile_version": prior_profile["profile_version"],
            "profile_sha256": prior_profile["profile_sha256"],
        }
    profile["profile_sha256"] = semantic_validator._compute_profile_hash(profile)
    return profile


def _accepted_profile(profiles_data: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    matches = [
        row
        for row in profiles_data.get("profiles", [])
        if row.get("prompt_id") == prompt_id and row.get("profile_status") == "ACCEPTED"
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one ACCEPTED semantic profile for {prompt_id}; found {len(matches)}"
        )
    return matches[0]


def _assert_profile_matches_record(profile: dict[str, Any], record: dict[str, Any]) -> None:
    expected = semantic_validator.compute_canonical_prompt_hash(record)
    if profile.get("canonical_prompt_hash") != expected:
        raise SystemExit(
            f"PSC009 BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION: {record.get('id')} "
            "already drifted from its ACCEPTED profile; repair history before another mutation"
        )


def _raw_registry_documents() -> list[tuple[Path, Any, bool]]:
    base = json.loads(registry.BASE_REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(base, list):
        raise SystemExit("Base prompt registry must be an array")
    documents: list[tuple[Path, Any, bool]] = [(registry.BASE_REGISTRY, base, True)]
    for path in registry.EXTENSION_REGISTRIES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("prompts"), list):
            raise SystemExit(f"Prompt extension has invalid shape: {path}")
        documents.append((path, payload, False))
    return documents


def _payload_records(payload: Any, is_base: bool) -> list[dict[str, Any]]:
    rows = payload if is_base else payload["prompts"]
    return [row for row in rows if isinstance(row, dict)]


def _payload_with_records(payload: Any, is_base: bool, rows: list[dict[str, Any]]) -> Any:
    if is_base:
        return rows
    updated = _clone_json(payload)
    updated["prompts"] = rows
    return updated


def _find_canonical_prompt(
    prompt_id: str,
) -> tuple[Path, Any, bool, dict[str, Any], int]:
    wanted = prompt_id.strip().upper()
    matches: list[tuple[Path, Any, bool, dict[str, Any], int]] = []
    for path, payload, is_base in _raw_registry_documents():
        rows = _payload_records(payload, is_base)
        for index, record in enumerate(rows):
            if str(record.get("id", "")).strip().upper() == wanted:
                matches.append((path, payload, is_base, record, index))
    if len(matches) != 1:
        raise SystemExit(
            f"Canonical prompt {wanted} must resolve to exactly one source; found {len(matches)}"
        )
    return matches[0]


def _quality_change_kind(operation: str) -> str:
    if operation in {"ADD", "STRENGTHEN", "NO_CAPABILITY_CHANGE"}:
        return "strengthening"
    return "intentional_semantic_change"


def _build_quality_history_migration(
    source_path: Path,
    before_bytes: bytes,
    after_bytes: bytes,
    prompt_id: str,
    operation: str,
    rationale: str,
    existing_count: int,
) -> dict[str, Any]:
    return {
        "migration_id": f"p79-{operation.lower().replace('_', '-')}-{prompt_id.lower()}-{existing_count + 1:03d}",
        "path": source_path.relative_to(REPO_ROOT).as_posix(),
        "from_git_blob_sha1": _git_blob_sha1(before_bytes),
        "to_git_blob_sha1": _git_blob_sha1(after_bytes),
        "affected_prompt_ids": [prompt_id],
        "change_kind": _quality_change_kind(operation),
        "effective_identity_change": "preserve_canonical",
        "rationale": rationale,
        "focused_tests": [
            "tests/test_prompt_semantic_coverage.py",
            "tests/test_prompt_quality_history.py",
        ],
    }


def simulate_global_coverage(
    profiles: list[dict[str, Any]], excluding_prompt_id: str | None = None
) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = {}
    for profile in profiles:
        if profile.get("profile_status") != "ACCEPTED":
            continue
        prompt_id = profile.get("prompt_id")
        if prompt_id == excluding_prompt_id:
            continue
        for assignment in profile.get("direct_assignments", []):
            if (
                assignment.get("ownership") == "PRIMARY"
                or assignment.get("presence") == "REQUIRED"
            ):
                capability_id = str(assignment.get("capability_id", ""))
                coverage.setdefault(capability_id, [])
                if prompt_id not in coverage[capability_id]:
                    coverage[capability_id].append(prompt_id)
    return coverage


def _assignment_summary(assignment: dict[str, Any] | None) -> dict[str, Any] | None:
    if assignment is None:
        return None
    return {
        "presence": assignment.get("presence", "NONE"),
        "ownership": assignment.get("ownership", "NONE"),
    }


def _capability_deltas(
    before_profile: dict[str, Any] | None,
    after_profile: dict[str, Any] | None,
    transfers: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    before = {
        row["capability_id"]: row
        for row in (before_profile or {}).get("direct_assignments", [])
    }
    after = {
        row["capability_id"]: row
        for row in (after_profile or {}).get("direct_assignments", [])
    }
    deltas: list[dict[str, Any]] = []
    for capability_id in sorted(set(before) | set(after)):
        delta: dict[str, Any] = {
            "capability_id": capability_id,
            "before": _assignment_summary(before.get(capability_id)),
            "after": _assignment_summary(after.get(capability_id)),
        }
        if transfers and capability_id in transfers:
            delta["transfer_target"] = transfers[capability_id]
        deltas.append(delta)
    return deltas


def _build_capability_migration(
    operation: str,
    prompt_id: str,
    *,
    before_profile: dict[str, Any] | None,
    after_profile: dict[str, Any] | None,
    rationale: str,
    evidence_refs: list[str],
    source_history_migration: dict[str, Any],
    existing_count: int,
    coverage_before: dict[str, list[str]],
    coverage_after: dict[str, list[str]],
    transfers: dict[str, str] | None = None,
) -> dict[str, Any]:
    migration = {
        "migration_id": f"{operation}_{prompt_id}_{existing_count + 1:03d}",
        "migration_kind": operation,
        "prompt_id": prompt_id,
        "old_canonical_prompt_hash": (
            before_profile.get("canonical_prompt_hash") if before_profile else None
        ),
        "new_canonical_prompt_hash": (
            after_profile.get("canonical_prompt_hash") if after_profile else None
        ),
        "from_profile_version": (
            before_profile.get("profile_version") if before_profile else None
        ),
        "to_profile_version": (
            after_profile.get("profile_version") if after_profile else None
        ),
        "from_profile_sha256": (
            before_profile.get("profile_sha256") if before_profile else None
        ),
        "to_profile_sha256": (
            after_profile.get("profile_sha256") if after_profile else None
        ),
        "capability_deltas": _capability_deltas(
            before_profile, after_profile, transfers
        ),
        "rationale": rationale,
        "evidence_refs": sorted(set(evidence_refs)),
        "focused_tests": [
            "tests/test_prompt_semantic_coverage.py",
            "tests/test_prompt_semantic_validator_1b.py",
        ],
        "source_history_migration_id": source_history_migration["migration_id"],
        "source_history_from_git_blob_sha1": source_history_migration["from_git_blob_sha1"],
        "source_history_to_git_blob_sha1": source_history_migration["to_git_blob_sha1"],
        "coverage_before_fingerprint": _sha256_json(coverage_before),
        "coverage_after_fingerprint": _sha256_json(coverage_after),
        "acceptance_state": "ACCEPTED",
    }
    if before_profile is not None:
        migration["prior_profile_snapshot"] = _clone_json(before_profile)
    return migration


def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.p79-semantic-tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def _create_backup(
    snapshot: dict[Path, bytes | None], operation: str
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%fZ")
    safe_operation = re.sub(r"[^A-Za-z0-9_.-]+", "-", operation)
    backup_dir = BACKUP_ROOT / f"{stamp}-{safe_operation}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    for path, data in snapshot.items():
        if data is None:
            continue
        relative = path.relative_to(REPO_ROOT)
        target = backup_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return backup_dir


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, data in snapshot.items():
        if data is None:
            path.unlink(missing_ok=True)
        else:
            _write_atomic(path, data)


def _apply_lifecycle_transaction(
    staged: dict[Path, bytes], operation: str
) -> dict[str, Any]:
    output = registry.DEFAULT_OUTPUT
    snapshot = _snapshot([*staged, output])
    backup_dir = _create_backup(snapshot, operation)
    try:
        for path, data in staged.items():
            _write_atomic(path, data)

        semantic_errors = semantic_validator.validate_repository_state()
        if semantic_errors:
            raise SystemExit(
                "Semantic lifecycle transaction failed: " + " | ".join(semantic_errors)
            )
        quality_errors = quality_history.validate()
        if quality_errors:
            raise SystemExit(
                "Prompt Quality History transaction failed: " + " | ".join(quality_errors)
            )

        tutorial_report = _require_complete_tutorial_coverage()
        registry.build(output)
        parity, prompt_count = _validate_site_parity()
        if not parity:
            raise SystemExit("Generated Prompt Kit site is not in exact registry parity")
    except BaseException:
        _restore(snapshot)
        raise

    return {
        "backup_path": str(backup_dir.relative_to(REPO_ROOT)),
        "prompt_count": prompt_count,
        "tutorial_coverage": tutorial_report,
    }


def _replace_current_profile(
    profiles_data: dict[str, Any],
    before_profile: dict[str, Any],
    after_profile: dict[str, Any],
) -> dict[str, Any]:
    updated = _clone_json(profiles_data)
    replaced = False
    rows = []
    for row in updated.get("profiles", []):
        if (
            row.get("prompt_id") == before_profile.get("prompt_id")
            and row.get("profile_status") == "ACCEPTED"
        ):
            if replaced:
                raise SystemExit(
                    f"Multiple ACCEPTED profiles found for {before_profile.get('prompt_id')}"
                )
            rows.append(_clone_json(after_profile))
            replaced = True
        else:
            rows.append(row)
    if not replaced:
        raise SystemExit(
            f"ACCEPTED profile disappeared for {before_profile.get('prompt_id')}"
        )
    updated["profiles"] = rows
    return updated


def adopt_profile(
    prompt_id: str,
    candidate: dict[str, Any],
    evidence_refs: list[str],
    rationale: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Adopt an existing unprofiled prompt into semantic coverage without changing its body."""
    prompt_id = prompt_id.strip().upper()
    rationale = rationale.strip()
    if not rationale:
        raise SystemExit("Profile adoption requires a non-empty rationale")

    source_path, _payload, _is_base, record, _index = _find_canonical_prompt(prompt_id)
    profiles_data = _load_semantic_profiles()
    existing = [
        row for row in profiles_data.get("profiles", [])
        if row.get("prompt_id") == prompt_id
    ]
    if any(row.get("profile_status") == "ACCEPTED" for row in existing):
        raise SystemExit(f"{prompt_id} already has an ACCEPTED semantic profile")
    if existing:
        raise SystemExit(
            f"{prompt_id} already has semantic profile history; reconcile it before adoption"
        )

    semantic_candidate = _validate_candidate_semantic_profile(candidate)
    merged_candidate = _clone_json(semantic_candidate)
    merged_refs = sorted(
        set(_semantic_evidence_refs(semantic_candidate))
        | {str(ref).strip() for ref in evidence_refs if str(ref).strip()}
    )
    if not merged_refs:
        raise SystemExit("Profile adoption requires at least one evidence reference")
    merged_candidate["evidence_refs"] = merged_refs

    accepted = _build_accepted_profile(
        record,
        merged_candidate,
        profile_version=1,
        prior_profile=None,
    )
    semantic_errors: list[str] = []
    semantic_errors.extend(semantic_validator.check_psc002_profile_binds_canonical_prompt(accepted))
    semantic_errors.extend(
        semantic_validator.check_psc002_profile_matches_canonical_record(accepted, record)
    )
    semantic_errors.extend(
        semantic_validator.check_psc003_known_capability_only(
            accepted,
            semantic_validator._load_catalog(),
        )
    )
    semantic_errors.extend(
        semantic_validator.check_psc011_new_primary_or_required_requires_proof(accepted)
    )
    semantic_errors.extend(
        semantic_validator.check_psc016_inherited_source_integrity(accepted)
    )
    if semantic_errors:
        raise SystemExit(
            "Profile adoption candidate failed semantic coverage: "
            + " | ".join(semantic_errors)
        )

    updated = _clone_json(profiles_data)
    updated.setdefault("profiles", []).append(accepted)
    updated["profile_count"] = len(updated["profiles"])

    preview = {
        "status": "dry-run" if dry_run else "adopted",
        "prompt_id": prompt_id,
        "registry_path": str(source_path.relative_to(REPO_ROOT)),
        "profile_version": accepted["profile_version"],
        "profile_sha256": accepted["profile_sha256"],
        "evidence_refs": merged_refs,
        "rationale": rationale,
    }
    if dry_run:
        return preview

    receipt = _apply_lifecycle_transaction(
        {SEMANTIC_PROFILES_PATH: _json_bytes(updated)},
        f"adopt-profile-{prompt_id}",
    )
    preview.update(
        {
            "backup_path": receipt["backup_path"],
            "site_path": str(registry.DEFAULT_OUTPUT.relative_to(REPO_ROOT)),
            "site_parity": True,
            "prompt_count": receipt["prompt_count"],
        }
    )
    return preview


def check_retirement_coverage(
    prompt_id: str,
    transfers: dict[str, str] | None = None,
) -> dict[str, Any]:
    profiles_data = _load_semantic_profiles()
    profiles = profiles_data.get("profiles", [])
    target = _accepted_profile(profiles_data, prompt_id)
    transfers = transfers or {}

    holes: list[dict[str, Any]] = []
    alternatives: dict[str, list[str]] = {}
    for assignment in target.get("direct_assignments", []):
        if not (
            assignment.get("ownership") == "PRIMARY"
            or assignment.get("presence") == "REQUIRED"
        ):
            continue

        capability_id = assignment["capability_id"]
        acceptable: list[str] = []
        for profile in profiles:
            if (
                profile.get("profile_status") != "ACCEPTED"
                or profile.get("prompt_id") == prompt_id
            ):
                continue
            successor = next(
                (
                    row
                    for row in profile.get("direct_assignments", [])
                    if row.get("capability_id") == capability_id
                ),
                None,
            )
            if successor is None:
                continue
            if (
                PRESENCE_ORDER.index(successor.get("presence", "NONE"))
                >= PRESENCE_ORDER.index(assignment.get("presence", "NONE"))
                and OWNERSHIP_ORDER.index(successor.get("ownership", "NONE"))
                >= OWNERSHIP_ORDER.index(assignment.get("ownership", "NONE"))
            ):
                acceptable.append(str(profile["prompt_id"]))

        alternatives[capability_id] = sorted(acceptable)
        requested = transfers.get(capability_id)
        if requested and requested not in acceptable:
            holes.append(
                {
                    "capability_id": capability_id,
                    "reason": f"requested transfer target {requested} is not equal-or-stronger",
                    "alternate_owners": sorted(acceptable),
                }
            )
        elif not acceptable:
            holes.append(
                {
                    "capability_id": capability_id,
                    "reason": "no equal-or-stronger accepted owner remains",
                    "alternate_owners": [],
                }
            )

    return {
        "can_retire": not holes,
        "prompt_id": prompt_id,
        "coverage_holes": holes,
        "alternate_owners": alternatives,
        "transfers": transfers,
        "reason": None if not holes else "Retirement would weaken protected global coverage",
    }


def _parse_transfers(values: list[str] | None) -> dict[str, str]:
    transfers: dict[str, str] = {}
    for value in values or []:
        capability_id, separator, prompt_id = value.partition("=")
        capability_id = capability_id.strip()
        prompt_id = prompt_id.strip().upper()
        if not separator or not capability_id or not PROMPT_ID_RE.fullmatch(prompt_id):
            raise SystemExit(
                f"Invalid --transfer {value!r}; expected CAPABILITY_ID=P##"
            )
        if capability_id in transfers:
            raise SystemExit(f"Duplicate --transfer for {capability_id}")
        transfers[capability_id] = prompt_id
    return transfers


def retire_prompt(
    prompt_id: str,
    rationale: str,
    dry_run: bool = False,
    transfers: dict[str, str] | None = None,
) -> dict[str, Any]:
    prompt_id = prompt_id.strip().upper()
    transfers = transfers or {}
    source_path, payload, is_base, record, index = _find_canonical_prompt(prompt_id)

    profiles_data = _load_semantic_profiles()
    before_profile = _accepted_profile(profiles_data, prompt_id)
    _assert_profile_matches_record(before_profile, record)

    coverage_check = check_retirement_coverage(prompt_id, transfers)
    if not coverage_check["can_retire"]:
        raise SystemExit(
            f"PSC007 RETIRE_NO_COVERAGE_HOLE: Cannot retire {prompt_id}. "
            f"{coverage_check['coverage_holes']}"
        )
    if dry_run:
        return {
            "status": "dry-run",
            "prompt_id": prompt_id,
            "can_retire": True,
            "coverage_check": coverage_check,
            "rationale": rationale,
        }

    rows = _payload_records(payload, is_base)
    new_payload = _payload_with_records(
        payload,
        is_base,
        [row for position, row in enumerate(rows) if position != index],
    )
    new_source_bytes = _json_bytes(new_payload)

    quality_data = _load_quality_migrations()
    quality_migration = _build_quality_history_migration(
        source_path,
        source_path.read_bytes(),
        new_source_bytes,
        prompt_id,
        "RETIRE",
        rationale,
        len(quality_data.get("migrations", [])),
    )
    new_quality_data = _clone_json(quality_data)
    new_quality_data.setdefault("migrations", []).append(quality_migration)

    tombstone = _clone_json(before_profile)
    tombstone["profile_status"] = "RETIRED"
    tombstone["profile_sha256"] = semantic_validator._compute_profile_hash(tombstone)
    new_profiles_data = _replace_current_profile(
        profiles_data, before_profile, tombstone
    )

    prospective_profiles = new_profiles_data.get("profiles", [])
    capability_data = _load_semantic_migrations()
    capability_migration = _build_capability_migration(
        "RETIRE",
        prompt_id,
        before_profile=before_profile,
        after_profile=None,
        rationale=rationale,
        evidence_refs=[f"retire:{prompt_id}"],
        source_history_migration=quality_migration,
        existing_count=len(capability_data.get("migrations", [])),
        coverage_before=simulate_global_coverage(profiles_data.get("profiles", [])),
        coverage_after=simulate_global_coverage(prospective_profiles),
        transfers=transfers,
    )
    new_capability_data = _clone_json(capability_data)
    new_capability_data.setdefault("migrations", []).append(capability_migration)

    staged = {
        source_path: new_source_bytes,
        SEMANTIC_PROFILES_PATH: _json_bytes(new_profiles_data),
        SEMANTIC_MIGRATIONS_PATH: _json_bytes(new_capability_data),
        QUALITY_MIGRATIONS_PATH: _json_bytes(new_quality_data),
    }
    receipt = _apply_lifecycle_transaction(staged, f"retire-{prompt_id}")

    return {
        "status": "retired",
        "prompt_id": prompt_id,
        "capability_migration_id": capability_migration["migration_id"],
        "source_history_migration_id": quality_migration["migration_id"],
        "coverage_check": coverage_check,
        "backup_path": receipt["backup_path"],
        "site_path": str(registry.DEFAULT_OUTPUT.relative_to(REPO_ROOT)),
        "site_parity": True,
        "rationale": rationale,
    }


def validate_body_change_disposition(
    prompt_id: str,
    old_body_hash: str,
    new_body_hash: str,
    disposition: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    if old_body_hash == new_body_hash:
        return {"body_changed": False, "disposition_required": False}

    valid_dispositions = {
        "NO_CAPABILITY_CHANGE",
        "STRENGTHEN",
        "INTENTIONAL_CHANGE",
        "TRANSFER",
    }
    if disposition not in valid_dispositions:
        raise SystemExit(
            "PSC009 BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION: "
            f"Body changed but disposition {disposition!r} is not in {sorted(valid_dispositions)}"
        )
    if not evidence_refs:
        raise SystemExit(
            "PSC009 BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION: "
            f"{disposition} requires at least one --evidence-ref"
        )
    return {
        "body_changed": True,
        "disposition_required": True,
        "disposition": disposition,
        "disposition_valid": True,
        "evidence_refs": list(evidence_refs),
        "prompt_id": prompt_id,
    }


def edit_prompt(
    prompt_id: str,
    patch: dict[str, Any],
    disposition: str,
    evidence_refs: list[str],
    rationale: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    prompt_id = prompt_id.strip().upper()
    allowed = EDITABLE_PROMPT_FIELDS | {"semantic_profile"}
    unknown = sorted(set(patch) - allowed)
    if unknown:
        raise SystemExit("Prompt edit contains unsupported fields: " + ", ".join(unknown))
    changed_fields = sorted(set(patch).intersection(EDITABLE_PROMPT_FIELDS))
    semantic_changed_fields = sorted(
        set(patch).intersection(SEMANTIC_EDITABLE_PROMPT_FIELDS)
    )
    if not changed_fields:
        raise SystemExit(
            "Prompt edit must change at least one supported field: "
            + ", ".join(sorted(EDITABLE_PROMPT_FIELDS))
        )
    if not semantic_changed_fields:
        raise SystemExit(
            "Prompt edit metadata may accompany a semantic edit but cannot independently "
            "advance the semantic lifecycle; change at least one of: "
            + ", ".join(sorted(SEMANTIC_EDITABLE_PROMPT_FIELDS))
        )

    source_path, payload, is_base, record, index = _find_canonical_prompt(prompt_id)
    profiles_data = _load_semantic_profiles()
    before_profile = _accepted_profile(profiles_data, prompt_id)
    _assert_profile_matches_record(before_profile, record)

    new_record = _clone_json(record)
    for field in changed_fields:
        value = patch[field]
        if field == "keywords":
            if not isinstance(value, list) or not value:
                raise SystemExit("Prompt edit keywords must be a non-empty list")
            if any(not isinstance(item, str) or not item.strip() for item in value):
                raise SystemExit("Prompt edit keywords must contain only non-empty strings")
            normalized = [item.strip() for item in value]
            if len(normalized) != len({_normalize_text(item) for item in normalized}):
                raise SystemExit("Prompt edit keywords must not contain duplicates")
            new_record[field] = normalized
            continue
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"Prompt edit field must be a non-empty string: {field}")
        new_record[field] = value.rstrip() if field == "copyContent" else value.strip()

    copy_content = str(new_record.get("copyContent", "")).strip()
    if len(copy_content) < 300 or len(copy_content) > 12000:
        raise SystemExit("Edited copyContent must remain between 300 and 12000 characters")
    if registry.load_actionability_policy()["marker"] in copy_content:
        raise SystemExit(
            "Edited canonical body must not copy the shared actionability appendix"
        )

    old_hash = semantic_validator.compute_canonical_prompt_hash(record)
    new_hash = semantic_validator.compute_canonical_prompt_hash(new_record)
    disposition_receipt = validate_body_change_disposition(
        prompt_id, old_hash, new_hash, disposition, evidence_refs
    )
    if not disposition_receipt["body_changed"]:
        raise SystemExit("Prompt edit produced no canonical semantic change")

    if disposition == "NO_CAPABILITY_CHANGE":
        if "semantic_profile" in patch:
            raise SystemExit(
                "NO_CAPABILITY_CHANGE must preserve the accepted capability assignments; "
                "omit semantic_profile"
            )
        semantic_candidate = {
            "direct_assignments": _clone_json(before_profile["direct_assignments"]),
            "inherited_sources": _clone_json(before_profile.get("inherited_sources", [])),
            "evidence_refs": sorted(
                set(before_profile.get("evidence_refs", [])) | set(evidence_refs)
            ),
        }
    else:
        if "semantic_profile" not in patch:
            raise SystemExit(
                f"{disposition} requires semantic_profile with the proposed assignments"
            )
        semantic_candidate = _validate_candidate_semantic_profile(patch["semantic_profile"])

    after_profile = _build_accepted_profile(
        new_record,
        semantic_candidate,
        profile_version=int(before_profile["profile_version"]) + 1,
        prior_profile=before_profile,
    )
    new_profiles_data = _replace_current_profile(
        profiles_data, before_profile, after_profile
    )
    prospective_profiles = new_profiles_data.get("profiles", [])

    rows = _payload_records(payload, is_base)
    new_rows = [new_record if position == index else row for position, row in enumerate(rows)]
    new_payload = _payload_with_records(payload, is_base, new_rows)
    new_source_bytes = _json_bytes(new_payload)

    quality_data = _load_quality_migrations()
    quality_migration = _build_quality_history_migration(
        source_path,
        source_path.read_bytes(),
        new_source_bytes,
        prompt_id,
        disposition,
        rationale,
        len(quality_data.get("migrations", [])),
    )
    new_quality_data = _clone_json(quality_data)
    new_quality_data.setdefault("migrations", []).append(quality_migration)

    capability_data = _load_semantic_migrations()
    transfers = semantic_candidate.get("transfer_targets", {})
    capability_migration = _build_capability_migration(
        disposition,
        prompt_id,
        before_profile=before_profile,
        after_profile=after_profile,
        rationale=rationale,
        evidence_refs=sorted(
            set(evidence_refs) | set(_semantic_evidence_refs(semantic_candidate))
        ),
        source_history_migration=quality_migration,
        existing_count=len(capability_data.get("migrations", [])),
        coverage_before=simulate_global_coverage(profiles_data.get("profiles", [])),
        coverage_after=simulate_global_coverage(prospective_profiles),
        transfers=transfers,
    )

    semantic_errors = semantic_validator.validate_profile_change(
        before_profile,
        after_profile,
        capability_migration,
        _load_semantic_catalog(),
        prospective_profiles,
    )
    if semantic_errors:
        raise SystemExit(
            "Semantic edit rejected before mutation: " + " | ".join(semantic_errors)
        )

    new_capability_data = _clone_json(capability_data)
    new_capability_data.setdefault("migrations", []).append(capability_migration)

    if dry_run:
        return {
            "status": "dry-run",
            "prompt_id": prompt_id,
            "changed_fields": changed_fields,
            "disposition": disposition_receipt,
            "semantic_profile_preview": after_profile,
            "capability_migration_preview": capability_migration,
            "source_history_migration_preview": quality_migration,
        }

    staged = {
        source_path: new_source_bytes,
        SEMANTIC_PROFILES_PATH: _json_bytes(new_profiles_data),
        SEMANTIC_MIGRATIONS_PATH: _json_bytes(new_capability_data),
        QUALITY_MIGRATIONS_PATH: _json_bytes(new_quality_data),
    }
    receipt = _apply_lifecycle_transaction(staged, f"edit-{prompt_id}")

    return {
        "status": "edited",
        "prompt_id": prompt_id,
        "changed_fields": changed_fields,
        "profile_version": after_profile["profile_version"],
        "profile_sha256": after_profile["profile_sha256"],
        "capability_migration_id": capability_migration["migration_id"],
        "source_history_migration_id": quality_migration["migration_id"],
        "backup_path": receipt["backup_path"],
        "site_path": str(registry.DEFAULT_OUTPUT.relative_to(REPO_ROOT)),
        "site_parity": True,
        "disposition": disposition_receipt,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect, add, adopt profiles, edit, retire, and validate Prompt Kit registry lifecycle "
            "mutations through P79 semantic coverage gates."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "inspect",
        help="Print next identity and compact registry routing choices as JSON.",
    )

    prior = sub.add_parser(
        "prior-art",
        help="Search every registered upstream before authoring a semantic ADD draft.",
    )
    prior.add_argument(
        "--query",
        required=True,
        help="User use case plus candidate mechanics to compare with internal owners and registered upstreams.",
    )

    add = sub.add_parser(
        "add",
        help=(
            "Recheck prior art and semantic residual, allocate identity, persist the "
            "ACCEPTED profile/migration, rebuild, and validate."
        ),
    )
    add.add_argument("--input", required=True, help="Draft JSON path, or - for stdin.")
    add.add_argument("--registry", help="Existing registry_id; otherwise resolve from draft profile.")
    add.add_argument("--dry-run", action="store_true", help="Resolve and validate without writing files.")

    adopt = sub.add_parser(
        "adopt-profile",
        help=(
            "Adopt an existing unprofiled prompt into semantic coverage without changing "
            "its canonical body."
        ),
    )
    adopt.add_argument("--prompt-id", required=True, help="Existing prompt ID to profile.")
    adopt.add_argument(
        "--input",
        required=True,
        help="Semantic profile JSON containing direct_assignments and optional inherited/evidence fields.",
    )
    adopt.add_argument(
        "--evidence-ref",
        action="append",
        default=[],
        help="Reviewed profile-adoption evidence reference; repeat for multiple refs.",
    )
    adopt.add_argument("--rationale", required=True, help="Reviewed reason for adopting this prompt into semantic coverage.")
    adopt.add_argument("--dry-run", action="store_true", help="Validate adoption without writing files.")

    edit = sub.add_parser(
        "edit",
        help="Edit a protected canonical prompt through PSC009 profile-disposition enforcement.",
    )
    edit.add_argument("--prompt-id", required=True, help="Prompt ID to edit (e.g., P07).")
    edit.add_argument("--input", required=True, help="JSON patch path, or - for stdin.")
    edit.add_argument(
        "--disposition",
        required=True,
        choices=["NO_CAPABILITY_CHANGE", "STRENGTHEN", "INTENTIONAL_CHANGE", "TRANSFER"],
    )
    edit.add_argument(
        "--evidence-ref",
        action="append",
        default=[],
        help="Focused proof reference; repeat for multiple refs.",
    )
    edit.add_argument("--rationale", required=True, help="Reviewed reason for the body/profile transition.")
    edit.add_argument("--dry-run", action="store_true", help="Validate the transition without writing files.")

    retire = sub.add_parser(
        "retire",
        help="Retire a prompt only when equal-or-stronger coverage remains (PSC007).",
    )
    retire.add_argument("--prompt-id", required=True, help="Prompt ID to retire (e.g., P42).")
    retire.add_argument("--rationale", required=True, help="Reason for retirement.")
    retire.add_argument(
        "--transfer",
        action="append",
        default=[],
        help="Optional CAPABILITY_ID=P## successor binding; repeat as needed.",
    )
    retire.add_argument("--dry-run", action="store_true", help="Check retirement without writing files.")

    sub.add_parser(
        "validate",
        help="Validate registry/site parity, semantic coverage, history, and tutorial wiring.",
    )
    args = parser.parse_args(argv)

    if args.command == "inspect":
        result = inspect_state()
    elif args.command == "prior-art":
        result = review_prior_art(args.query)
    elif args.command == "add":
        result = add_prompt(_read_json(args.input), args.registry, args.dry_run)
    elif args.command == "adopt-profile":
        result = adopt_profile(
            args.prompt_id,
            _read_json(args.input),
            args.evidence_ref,
            args.rationale,
            args.dry_run,
        )
    elif args.command == "edit":
        result = edit_prompt(
            args.prompt_id,
            _read_json(args.input),
            args.disposition,
            args.evidence_ref,
            args.rationale,
            args.dry_run,
        )
    elif args.command == "retire":
        result = retire_prompt(
            args.prompt_id,
            args.rationale,
            args.dry_run,
            _parse_transfers(args.transfer),
        )
    else:
        result = validate_current()

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
