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
from scripts import prompt_registry_external_prior_art as prior_art  # noqa: E402

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
OPTIONAL_DRAFT_FIELDS = {
    "registry_id",
    "profile",
    "color",
    "category",
    "progress",
    "tutorial",
}
TUTORIAL_FRESHNESS_LEDGER = (
    REPO_ROOT / "registry" / "prompts" / "tutorial-freshness.v1.json"
)


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
        "optional_draft_fields": sorted(OPTIONAL_DRAFT_FIELDS),
        "auto_fields": sorted(AUTO_FIELDS),
        "tutorial_freshness": {
            "required_before_write": True,
            "ledger": str(TUTORIAL_FRESHNESS_LEDGER.relative_to(REPO_ROOT)),
        },
        "classification": registry.prompt_classification.classification_summary(
            registry.load_prompt_kit_registry()
        ),
    }


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _load_tutorial_freshness() -> dict[str, Any]:
    payload = registry._load_json(TUTORIAL_FRESHNESS_LEDGER)
    if not isinstance(payload, dict):
        raise SystemExit("Tutorial freshness ledger must be a JSON object")
    if payload.get("schema_version") != "prompt-tutorial-freshness/v1":
        raise SystemExit("Unsupported tutorial freshness ledger schema")
    policy_id = payload.get("policy_id")
    allowed = payload.get("allowed_dispositions")
    records = payload.get("records")
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise SystemExit("Tutorial freshness ledger must define policy_id")
    if not isinstance(allowed, list) or not allowed:
        raise SystemExit("Tutorial freshness ledger must define allowed_dispositions")
    if any(not isinstance(item, str) or not item.strip() for item in allowed):
        raise SystemExit("Tutorial freshness dispositions must be non-empty strings")
    if not isinstance(records, list):
        raise SystemExit("Tutorial freshness ledger must define a records array")
    return payload


def _validate_tutorial_plan(
    draft: dict[str, Any], *, require: bool
) -> dict[str, Any] | None:
    tutorial = draft.get("tutorial")
    if tutorial is None:
        if require:
            raise SystemExit(
                "Prompt ADD requires draft.tutorial before identity allocation; update the tutorial "
                "surface first, then provide disposition, tutorial_paths, and reason"
            )
        return None
    if not isinstance(tutorial, dict):
        raise SystemExit("Prompt draft tutorial must be one object")

    ledger = _load_tutorial_freshness()
    allowed = {str(item) for item in ledger["allowed_dispositions"]}
    disposition = str(tutorial.get("disposition", "")).strip()
    reason = str(tutorial.get("reason", "")).strip()
    paths = tutorial.get("tutorial_paths")
    if disposition not in allowed:
        raise SystemExit(
            "Prompt draft tutorial disposition must be one of: "
            + ", ".join(sorted(allowed))
        )
    if not reason:
        raise SystemExit("Prompt draft tutorial reason must be non-empty")
    reference_only = disposition == "REFERENCE_ONLY_WITH_REASON"
    if not isinstance(paths, list) or (not paths and not reference_only):
        raise SystemExit("Prompt draft tutorial_paths must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in paths):
        raise SystemExit("Every tutorial path must be a non-empty string")

    prompt_name = str(draft.get("name", "")).strip()
    covered_paths: list[str] = []
    normalized_paths: list[str] = []
    for value in paths:
        relative = value.strip()
        path = (REPO_ROOT / relative).resolve()
        try:
            path.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise SystemExit(f"Tutorial path escapes repository: {relative}") from exc
        if not path.is_file():
            raise SystemExit(f"Tutorial path does not exist: {relative}")
        normalized_paths.append(relative)
        if prompt_name and prompt_name in path.read_text(encoding="utf-8"):
            covered_paths.append(relative)

    if not covered_paths and not reference_only:
        raise SystemExit(
            "Prompt ADD tutorial freshness failed: at least one declared tutorial path must "
            "already mention the new prompt name before the registry write"
        )
    return {
        "disposition": disposition,
        "tutorial_paths": normalized_paths,
        "reason": reason,
        "coverage_paths": covered_paths,
    }


def _append_tutorial_add_record(
    payload: dict[str, Any], record: dict[str, Any], tutorial: dict[str, Any]
) -> dict[str, Any]:
    updated = dict(payload)
    records = list(payload.get("records", []))
    records.append(
        {
            "prompt_id": str(record["id"]),
            "prompt_name": str(record["name"]),
            "event": "ADD",
            "disposition": str(tutorial["disposition"]),
            "tutorial_paths": list(tutorial["tutorial_paths"]),
            "reason": str(tutorial["reason"]),
            "status": "RECORDED_BY_ADD_HELPER",
        }
    )
    updated["records"] = records
    return updated


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
    if "tutorial" in draft:
        _validate_tutorial_plan(draft, require=False)


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
    record = _build_record(draft, target_payload)
    tutorial_plan = _validate_tutorial_plan(draft, require=not dry_run)
    if dry_run:
        return {
            "status": "dry-run",
            "registry_id": target_payload["registry_id"],
            "registry_path": str(target_path.relative_to(REPO_ROOT)),
            "record": record,
            "external_prior_art": external_prior_art,
            "tutorial_freshness": tutorial_plan
            or {
                "status": "required-before-write",
                "ledger": str(TUTORIAL_FRESHNESS_LEDGER.relative_to(REPO_ROOT)),
            },
        }

    assert tutorial_plan is not None
    original_registry = target_path.read_text(encoding="utf-8")
    output = registry.DEFAULT_OUTPUT
    original_output = output.read_text(encoding="utf-8") if output.exists() else None
    original_tutorial_ledger = TUTORIAL_FRESHNESS_LEDGER.read_text(encoding="utf-8")
    try:
        payload = dict(target_payload)
        payload["prompts"] = [*target_payload["prompts"], record]
        target_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        ledger = _load_tutorial_freshness()
        updated_ledger = _append_tutorial_add_record(ledger, record, tutorial_plan)
        TUTORIAL_FRESHNESS_LEDGER.write_text(
            json.dumps(updated_ledger, indent=2, ensure_ascii=False) + "\n",
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
        TUTORIAL_FRESHNESS_LEDGER.write_text(original_tutorial_ledger, encoding="utf-8")
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
        "external_prior_art": external_prior_art,
        "tutorial_freshness": {
            **tutorial_plan,
            "ledger": str(TUTORIAL_FRESHNESS_LEDGER.relative_to(REPO_ROOT)),
            "status": "RECORDED_BY_ADD_HELPER",
        },
    }


def validate_current() -> dict[str, Any]:
    parity, prompt_count = _validate_site_parity()
    if not parity:
        raise SystemExit(
            "Prompt Kit registry is valid but web/prompt-kit/index.html is stale; rebuild it"
        )
    tutorial = _load_tutorial_freshness()
    return {
        "status": "valid",
        "prompt_count": prompt_count,
        "site_parity": True,
        "next_id": _next_identity()[0],
        "tutorial_freshness_policy": tutorial["policy_id"],
        "tutorial_freshness_records": len(tutorial["records"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect, add, and validate Prompt Kit registry contributions with minimal ceremony."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect", help="Print next identity and compact registry routing choices as JSON.")
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
            "Recheck every registered upstream, require tutorial freshness coverage, then add one "
            "prompt draft, allocate identity, rebuild, and validate."
        ),
    )
    add.add_argument("--input", required=True, help="Draft JSON path, or - for stdin.")
    add.add_argument("--registry", help="Existing registry_id; otherwise resolve from draft profile.")
    add.add_argument("--dry-run", action="store_true", help="Resolve and validate without writing files.")
    sub.add_parser("validate", help="Validate current registry loading and generated-site parity.")
    args = parser.parse_args(argv)

    if args.command == "inspect":
        result = inspect_state()
    elif args.command == "prior-art":
        result = review_prior_art(args.query)
    elif args.command == "add":
        result = add_prompt(_read_json(args.input), args.registry, args.dry_run)
    else:
        result = validate_current()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
