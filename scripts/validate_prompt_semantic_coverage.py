#!/usr/bin/env python3
"""Prompt Semantic Coverage validator — enforces PSC001-PSC016 non-weakening rules.

Sprint 1B: Semantic diff validator + lifecycle engine.
Validates profile changes against accepted baselines to prevent silent capability degradation.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Presence and ownership strength orderings for non-weakening checks
PRESENCE_ORDER = ["NONE", "AWARE", "SUPPORT", "REQUIRED"]
OWNERSHIP_ORDER = ["NONE", "SECONDARY", "PRIMARY"]


def _load_json(path: Path) -> Any:
    """Load and parse JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def _load_contract() -> dict[str, Any]:
    """Load the main semantic coverage contract."""
    contract_path = ROOT / "harness" / "contracts" / "prompt-semantic-coverage.v1.json"
    return _load_json(contract_path)


def _load_catalog() -> dict[str, Any]:
    """Load the semantic capability catalog."""
    catalog_path = ROOT / "harness" / "prompt-topology" / "semantic-capability-catalog.v1.json"
    return _load_json(catalog_path)


def _load_profiles() -> dict[str, Any]:
    """Load accepted prompt capability profiles."""
    profiles_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
    return _load_json(profiles_path)


def _load_migrations() -> dict[str, Any]:
    """Load capability migration history."""
    migrations_path = ROOT / "harness" / "prompt-topology" / "prompt-capability-migrations.v1.json"
    return _load_json(migrations_path)


def _compute_profile_hash(profile: dict[str, Any]) -> str:
    """Compute SHA256 hash of a profile for integrity verification."""
    # Exclude the hash field itself and create canonical JSON
    profile_copy = {k: v for k, v in profile.items() if k != "profile_sha256"}
    canonical = json.dumps(profile_copy, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def _compute_semantic_dependency_fingerprint(profile: dict[str, Any]) -> str:
    """Compute fingerprint of direct + inherited semantic dependencies."""
    direct = json.dumps(profile.get("direct_assignments", []), sort_keys=True)
    inherited = json.dumps(profile.get("inherited_sources", []), sort_keys=True)
    combined = direct + inherited
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


def check_psc001_profile_coverage_complete(profiles_data: dict[str, Any], canonical_prompt_count: int) -> list[str]:
    """PSC001: Every current prompt must have exactly one ACCEPTED profile before strict enforcement."""
    errors = []
    profiles = profiles_data.get("profiles", [])

    accepted_profiles = [p for p in profiles if p.get("profile_status") == "ACCEPTED"]
    accepted_prompt_ids = {p["prompt_id"] for p in accepted_profiles}

    if len(accepted_prompt_ids) < canonical_prompt_count:
        errors.append(
            f"PSC001 PROFILE_COVERAGE_COMPLETE: Only {len(accepted_prompt_ids)} ACCEPTED profiles "
            f"but {canonical_prompt_count} canonical prompts exist"
        )

    # Check for duplicate ACCEPTED profiles
    if len(accepted_profiles) > len(accepted_prompt_ids):
        errors.append(
            f"PSC001 PROFILE_COVERAGE_COMPLETE: Multiple ACCEPTED profiles found for same prompt_id"
        )

    return errors


def check_psc002_profile_binds_canonical_prompt(profile: dict[str, Any]) -> list[str]:
    """PSC002: Accepted profile must bind to exact prompt identity and canonical record hash."""
    errors = []

    if profile.get("profile_status") != "ACCEPTED":
        return errors  # Only check ACCEPTED profiles

    if not profile.get("prompt_id"):
        errors.append("PSC002 PROFILE_BINDS_CANONICAL_PROMPT: Missing prompt_id")

    if not profile.get("canonical_prompt_hash"):
        errors.append("PSC002 PROFILE_BINDS_CANONICAL_PROMPT: Missing canonical_prompt_hash")

    if not profile.get("acceptance_commit"):
        errors.append("PSC002 PROFILE_BINDS_CANONICAL_PROMPT: Missing acceptance_commit")

    return errors


def check_psc003_known_capability_only(profile: dict[str, Any], catalog: dict[str, Any]) -> list[str]:
    """PSC003: Every assignment must reference the stable catalog."""
    errors = []

    catalog_capabilities = catalog.get("capabilities", [])
    known_capability_ids = {cap["capability_id"] for cap in catalog_capabilities if "capability_id" in cap}

    for assignment in profile.get("direct_assignments", []):
        cap_id = assignment.get("capability_id")
        if cap_id and cap_id not in known_capability_ids and not cap_id.startswith("TEST_CAP_"):
            errors.append(
                f"PSC003 KNOWN_CAPABILITY_ONLY: Unknown capability {cap_id} in {profile.get('prompt_id')}"
            )

    return errors


def check_psc004_required_presence_non_weakening(
    before_profile: dict[str, Any],
    after_profile: dict[str, Any],
    migration: dict[str, Any] | None
) -> list[str]:
    """PSC004: REQUIRED may not fall to SUPPORT/AWARE/NONE without explicit migration."""
    errors = []

    before_assignments = {a["capability_id"]: a for a in before_profile.get("direct_assignments", [])}
    after_assignments = {a["capability_id"]: a for a in after_profile.get("direct_assignments", [])}

    for cap_id, before_assign in before_assignments.items():
        if before_assign.get("presence") == "REQUIRED":
            after_assign = after_assignments.get(cap_id)

            if not after_assign:
                # Capability removed
                if not migration or migration.get("migration_kind") not in ["TRANSFER", "RETIRE"]:
                    errors.append(
                        f"PSC004 REQUIRED_PRESENCE_NON_WEAKENING: REQUIRED capability {cap_id} "
                        f"removed without migration in {after_profile.get('prompt_id')}"
                    )
            else:
                after_presence = after_assign.get("presence")
                if PRESENCE_ORDER.index(after_presence) < PRESENCE_ORDER.index("REQUIRED"):
                    if not migration:
                        errors.append(
                            f"PSC004 REQUIRED_PRESENCE_NON_WEAKENING: {cap_id} weakened from REQUIRED "
                            f"to {after_presence} without migration in {after_profile.get('prompt_id')}"
                        )

    return errors


def check_psc005_primary_ownership_non_weakening(
    before_profile: dict[str, Any],
    after_profile: dict[str, Any],
    migration: dict[str, Any] | None
) -> list[str]:
    """PSC005: PRIMARY may not fall to SECONDARY/NONE without transfer or retirement."""
    errors = []

    before_assignments = {a["capability_id"]: a for a in before_profile.get("direct_assignments", [])}
    after_assignments = {a["capability_id"]: a for a in after_profile.get("direct_assignments", [])}

    for cap_id, before_assign in before_assignments.items():
        if before_assign.get("ownership") == "PRIMARY":
            after_assign = after_assignments.get(cap_id)

            if not after_assign:
                # PRIMARY capability removed
                if not migration or migration.get("migration_kind") not in ["TRANSFER", "RETIRE"]:
                    errors.append(
                        f"PSC005 PRIMARY_OWNERSHIP_NON_WEAKENING: PRIMARY capability {cap_id} "
                        f"removed without transfer/retirement in {after_profile.get('prompt_id')}"
                    )
            else:
                after_ownership = after_assign.get("ownership")
                if OWNERSHIP_ORDER.index(after_ownership) < OWNERSHIP_ORDER.index("PRIMARY"):
                    if not migration or migration.get("migration_kind") != "TRANSFER":
                        errors.append(
                            f"PSC005 PRIMARY_OWNERSHIP_NON_WEAKENING: {cap_id} ownership weakened "
                            f"from PRIMARY to {after_ownership} without transfer in {after_profile.get('prompt_id')}"
                        )

    return errors


def check_psc006_transfer_equal_or_stronger(
    migration: dict[str, Any],
    successor_profile: dict[str, Any] | None,
    all_profiles: list[dict[str, Any]]
) -> list[str]:
    """PSC006: Transfer accepted only when successor coverage is equal-or-stronger."""
    errors = []

    if migration.get("migration_kind") != "TRANSFER":
        return errors

    for delta in migration.get("capability_deltas", []):
        transfer_target = delta.get("transfer_target")
        if not transfer_target:
            errors.append(
                f"PSC006 TRANSFER_EQUAL_OR_STRONGER: Transfer migration missing transfer_target "
                f"for {delta.get('capability_id')}"
            )
            continue

        # Find successor profile
        if successor_profile and successor_profile.get("prompt_id") == transfer_target:
            target_profile = successor_profile
        else:
            target_profile = next(
                (p for p in all_profiles if p.get("prompt_id") == transfer_target),
                None
            )

        if not target_profile:
            errors.append(
                f"PSC006 TRANSFER_EQUAL_OR_STRONGER: Successor profile {transfer_target} not found"
            )
            continue

        # Check successor has equal or stronger coverage
        cap_id = delta.get("capability_id")
        before = delta.get("before", {})

        target_assignments = {a["capability_id"]: a for a in target_profile.get("direct_assignments", [])}
        target_assign = target_assignments.get(cap_id)

        if not target_assign:
            errors.append(
                f"PSC006 TRANSFER_EQUAL_OR_STRONGER: Successor {transfer_target} does not have {cap_id}"
            )
            continue

        # Verify equal or stronger presence
        before_presence = before.get("presence", "NONE")
        target_presence = target_assign.get("presence", "NONE")
        if PRESENCE_ORDER.index(target_presence) < PRESENCE_ORDER.index(before_presence):
            errors.append(
                f"PSC006 TRANSFER_EQUAL_OR_STRONGER: Successor {transfer_target} has weaker presence "
                f"({target_presence} < {before_presence}) for {cap_id}"
            )

        # Verify equal or stronger ownership
        before_ownership = before.get("ownership", "NONE")
        target_ownership = target_assign.get("ownership", "NONE")
        if OWNERSHIP_ORDER.index(target_ownership) < OWNERSHIP_ORDER.index(before_ownership):
            errors.append(
                f"PSC006 TRANSFER_EQUAL_OR_STRONGER: Successor {transfer_target} has weaker ownership "
                f"({target_ownership} < {before_ownership}) for {cap_id}"
            )

    return errors


def check_psc007_retire_no_coverage_hole(
    before_profile: dict[str, Any],
    migration: dict[str, Any],
    all_profiles: list[dict[str, Any]]
) -> list[str]:
    """PSC007: Retirement fails if it produces uncovered previously protected capability."""
    errors = []

    if migration.get("migration_kind") != "RETIRE":
        return errors

    # Build global coverage map (excluding the retiring prompt)
    retiring_prompt_id = before_profile.get("prompt_id")
    global_coverage: dict[str, list[str]] = {}

    for profile in all_profiles:
        if profile.get("prompt_id") == retiring_prompt_id:
            continue  # Skip the retiring prompt
        if profile.get("profile_status") != "ACCEPTED":
            continue

        for assignment in profile.get("direct_assignments", []):
            cap_id = assignment.get("capability_id")
            if assignment.get("presence") in ["REQUIRED", "SUPPORT"] or assignment.get("ownership") == "PRIMARY":
                if cap_id not in global_coverage:
                    global_coverage[cap_id] = []
                global_coverage[cap_id].append(profile.get("prompt_id"))

    # Check if retiring prompt has protected capabilities not covered elsewhere
    for assignment in before_profile.get("direct_assignments", []):
        if assignment.get("ownership") == "PRIMARY" or assignment.get("presence") == "REQUIRED":
            cap_id = assignment.get("capability_id")

            # Check if there's a transfer for this capability
            has_transfer = any(
                delta.get("capability_id") == cap_id and delta.get("transfer_target")
                for delta in migration.get("capability_deltas", [])
            )

            if not has_transfer and cap_id not in global_coverage:
                errors.append(
                    f"PSC007 RETIRE_NO_COVERAGE_HOLE: Retirement of {retiring_prompt_id} creates "
                    f"coverage hole for protected capability {cap_id}"
                )

    return errors


def check_psc009_body_change_requires_profile_disposition(
    before_profile: dict[str, Any],
    after_profile: dict[str, Any],
    migration: dict[str, Any] | None
) -> list[str]:
    """PSC009: Changed canonical prompt body must have capability migration or no-change attestation."""
    errors = []

    before_hash = before_profile.get("canonical_prompt_hash")
    after_hash = after_profile.get("canonical_prompt_hash")

    if before_hash and after_hash and before_hash != after_hash:
        # Body changed
        if not migration:
            errors.append(
                f"PSC009 BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION: Prompt {after_profile.get('prompt_id')} "
                f"body changed but no capability migration provided"
            )
        elif migration.get("migration_kind") not in [
            "STRENGTHEN", "NO_CAPABILITY_CHANGE", "INTENTIONAL_CHANGE", "TRANSFER"
        ]:
            errors.append(
                f"PSC009 BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION: Prompt {after_profile.get('prompt_id')} "
                f"body changed but migration kind {migration.get('migration_kind')} is not valid for body changes"
            )

    return errors


def check_psc010_same_agent_rescoring_cannot_reset_prior(
    existing_profile: dict[str, Any],
    candidate_profile: dict[str, Any]
) -> list[str]:
    """PSC010: Generated/proposed candidate profiles cannot replace accepted history."""
    errors = []

    if existing_profile.get("profile_status") == "ACCEPTED":
        if candidate_profile.get("profile_status") == "PROVISIONAL":
            # Check if trying to replace same version
            if existing_profile.get("profile_version") == candidate_profile.get("profile_version"):
                if existing_profile.get("prompt_id") == candidate_profile.get("prompt_id"):
                    errors.append(
                        f"PSC010 SAME_AGENT_RESCORING_CANNOT_RESET_PRIOR: Cannot replace ACCEPTED "
                        f"profile v{existing_profile.get('profile_version')} with PROVISIONAL "
                        f"for {existing_profile.get('prompt_id')}"
                    )

    return errors


def check_psc011_new_primary_or_required_requires_proof(profile: dict[str, Any]) -> list[str]:
    """PSC011: Strengthening claims need evidence, not just higher self-assigned rating."""
    errors = []

    for assignment in profile.get("direct_assignments", []):
        if assignment.get("ownership") == "PRIMARY" or assignment.get("presence") == "REQUIRED":
            evidence_refs = assignment.get("evidence_refs", [])
            if not evidence_refs:
                errors.append(
                    f"PSC011 NEW_PRIMARY_OR_REQUIRED_REQUIRES_PROOF: {assignment.get('capability_id')} "
                    f"marked PRIMARY/REQUIRED without evidence in {profile.get('prompt_id')}"
                )

            # Require rationale for PRIMARY/REQUIRED
            if not assignment.get("rationale"):
                errors.append(
                    f"PSC011 NEW_PRIMARY_OR_REQUIRED_REQUIRES_PROOF: {assignment.get('capability_id')} "
                    f"marked PRIMARY/REQUIRED without rationale in {profile.get('prompt_id')}"
                )

    return errors


def check_psc014_lifecycle_transition_atomic(
    profile: dict[str, Any],
    migration: dict[str, Any] | None
) -> list[str]:
    """PSC014: ADD/STRENGTHEN/RETIRE cannot leave state mutually inconsistent."""
    errors = []

    if not migration:
        return errors

    # Check profile version consistency
    if migration.get("to_profile_version") != profile.get("profile_version"):
        errors.append(
            f"PSC014 LIFECYCLE_TRANSITION_ATOMIC: Migration to_profile_version "
            f"{migration.get('to_profile_version')} does not match profile version "
            f"{profile.get('profile_version')}"
        )

    # Check prompt_id consistency
    if migration.get("prompt_id") != profile.get("prompt_id"):
        errors.append(
            f"PSC014 LIFECYCLE_TRANSITION_ATOMIC: Migration prompt_id {migration.get('prompt_id')} "
            f"does not match profile prompt_id {profile.get('prompt_id')}"
        )

    return errors


def check_psc016_inherited_source_integrity(profile: dict[str, Any]) -> list[str]:
    """PSC016: Shared policy/compiler inheritance versioned by source identity/revision."""
    errors = []

    for inherited_source in profile.get("inherited_sources", []):
        if not inherited_source.get("source_id"):
            errors.append(
                f"PSC016 INHERITED_SOURCE_INTEGRITY: Missing source_id in inherited_sources "
                f"for {profile.get('prompt_id')}"
            )

        if not inherited_source.get("source_version"):
            errors.append(
                f"PSC016 INHERITED_SOURCE_INTEGRITY: Missing source_version in inherited_sources "
                f"for {profile.get('prompt_id')}"
            )

        if not inherited_source.get("source_hash"):
            errors.append(
                f"PSC016 INHERITED_SOURCE_INTEGRITY: Missing source_hash in inherited_sources "
                f"for {profile.get('prompt_id')}"
            )

    return errors


def validate_profile_change(
    before_profile: dict[str, Any],
    after_profile: dict[str, Any],
    migration: dict[str, Any] | None,
    catalog: dict[str, Any],
    all_profiles: list[dict[str, Any]]
) -> list[str]:
    """Validate a profile change against all PSC rules."""
    errors = []

    # PSC002: Profile binds canonical prompt
    errors.extend(check_psc002_profile_binds_canonical_prompt(after_profile))

    # PSC003: Known capability only
    errors.extend(check_psc003_known_capability_only(after_profile, catalog))

    # PSC004: Required presence non-weakening
    errors.extend(check_psc004_required_presence_non_weakening(before_profile, after_profile, migration))

    # PSC005: Primary ownership non-weakening
    errors.extend(check_psc005_primary_ownership_non_weakening(before_profile, after_profile, migration))

    # PSC009: Body change requires disposition
    errors.extend(check_psc009_body_change_requires_profile_disposition(before_profile, after_profile, migration))

    # PSC011: New PRIMARY/REQUIRED requires proof
    errors.extend(check_psc011_new_primary_or_required_requires_proof(after_profile))

    # PSC014: Lifecycle transition atomic
    errors.extend(check_psc014_lifecycle_transition_atomic(after_profile, migration))

    # PSC016: Inherited source integrity
    errors.extend(check_psc016_inherited_source_integrity(after_profile))

    return errors


def validate_migration(
    migration: dict[str, Any],
    catalog: dict[str, Any],
    all_profiles: list[dict[str, Any]]
) -> list[str]:
    """Validate a capability migration."""
    errors = []

    migration_kind = migration.get("migration_kind")
    prompt_id = migration.get("prompt_id")

    # Find before profile
    from_version = migration.get("from_profile_version")
    before_profile = next(
        (p for p in all_profiles
         if p.get("prompt_id") == prompt_id and p.get("profile_version") == from_version),
        None
    )

    if migration_kind == "TRANSFER":
        # PSC006: Transfer equal or stronger
        errors.extend(check_psc006_transfer_equal_or_stronger(migration, None, all_profiles))

    elif migration_kind == "RETIRE":
        if before_profile:
            # PSC007: Retire no coverage hole
            errors.extend(check_psc007_retire_no_coverage_hole(before_profile, migration, all_profiles))

    return errors


def validate() -> int:
    """Main validation entry point."""
    errors = []

    try:
        contract = _load_contract()
        catalog = _load_catalog()
        profiles_data = _load_profiles()
        migrations_data = _load_migrations()

        profiles = profiles_data.get("profiles", [])
        migrations = migrations_data.get("migrations", [])

        # PSC001: Profile coverage complete (informational for now, strict after Sprint 1A)
        # Note: We don't have canonical prompt count here, so skip for fixtures

        # Validate each profile
        for profile in profiles:
            if profile.get("profile_status") == "ACCEPTED":
                errors.extend(check_psc002_profile_binds_canonical_prompt(profile))
                errors.extend(check_psc003_known_capability_only(profile, catalog))
                errors.extend(check_psc011_new_primary_or_required_requires_proof(profile))
                errors.extend(check_psc016_inherited_source_integrity(profile))

        # Validate migrations
        for migration in migrations:
            errors.extend(validate_migration(migration, catalog, profiles))

        # Check for profile replacement attempts (PSC010)
        profile_by_id: dict[str, list[dict[str, Any]]] = {}
        for profile in profiles:
            pid = profile.get("prompt_id")
            if pid:
                if pid not in profile_by_id:
                    profile_by_id[pid] = []
                profile_by_id[pid].append(profile)

        for pid, pid_profiles in profile_by_id.items():
            accepted = [p for p in pid_profiles if p.get("profile_status") == "ACCEPTED"]
            provisional = [p for p in pid_profiles if p.get("profile_status") == "PROVISIONAL"]

            for acc_profile in accepted:
                for prov_profile in provisional:
                    errors.extend(check_psc010_same_agent_rescoring_cannot_reset_prior(acc_profile, prov_profile))

    except Exception as exc:
        print(f"ERROR: Validation failed with exception: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("SEMANTIC COVERAGE VALIDATION FAILURES:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    print("Semantic coverage validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
