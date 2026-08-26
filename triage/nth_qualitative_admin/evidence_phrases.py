"""Deterministic evidence-backed qualitative context rendering.

Vocabulary ownership stays with the producer (for example FUN). This module only
validates a supplied catalog, binds evidence references to canonical codes, and
selects presentation variants deterministically. It never invents a workstream.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any, Mapping

from .model import QualitativeAdminError

ALLOWED_SCOPES = {"recurring_pattern", "dated_context", "dated_person_task"}
SCOPE_RANK = {"recurring_pattern": 1, "dated_context": 2, "dated_person_task": 3}
ALLOWED_RISKS = {"lower", "high"}
_RESERVED_RECEIPT = "_evidence_backed_context_receipt"

# Triage does not own producer workstream vocabulary, but it does own the safety
# boundary on what the generated outward language may assert. Phrases that claim
# deployment execution must not be smuggled through a producer catalog as a
# lower-risk recurring-pattern or dated-context term. Generic wording such as
# "deployment support" is intentionally not matched because it does not, by
# itself, assert that a person/date deployment occurred.
_DEPLOYMENT_EXECUTION_CLAIM_PATTERN = re.compile(
    r"\bdeployment\s+(?:execution|installation|go[-\s]?live|cutover|completed|performed|executed)\b"
    r"|\b(?:performed|completed|executed)\s+(?:the\s+)?(?:endpoint\s+|device\s+)?(?:deployment|installation|go[-\s]?live|cutover)\b"
    r"|\b(?:deployed|deploying|installed|installing)\s+(?:the\s+)?(?:assigned\s+)?(?:endpoint|endpoints|device|devices|workstation|workstations|terminal|terminals|system|systems)\b"
    r"|\b(?:endpoint|endpoints|device|devices)\s+(?:deployment|installation)\s+(?:completed|performed|executed)\b"
    r"|\b(?:go[-\s]?live|cutover)\s+(?:completed|performed|executed)\b"
    r"|\bwent\s+live\b"
    r"|\bcut\s+over\b",
    re.I,
)


def _clean_string(value: Any, field: str) -> str:
    text = str(value if value is not None else "").strip()
    if not text:
        raise QualitativeAdminError(f"{field} is required")
    return text


def _catalog_terms(catalog: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    catalog_id = _clean_string(catalog.get("catalog_id"), "qualitative_phrase_catalog.catalog_id")
    terms = catalog.get("terms")
    if not isinstance(terms, Mapping) or not terms:
        raise QualitativeAdminError("qualitative_phrase_catalog.terms must be a non-empty object")
    return catalog_id, terms


def _term_contract(code: str, term: Mapping[str, Any]) -> tuple[str, str, bool, list[str]]:
    risk = str(term.get("risk_tier", "")).strip()
    if risk not in ALLOWED_RISKS:
        raise QualitativeAdminError(f"qualitative phrase term {code!r} has invalid risk_tier")
    required_scope = str(term.get("required_evidence_scope", "")).strip()
    if required_scope not in ALLOWED_SCOPES:
        raise QualitativeAdminError(
            f"qualitative phrase term {code!r} has invalid required_evidence_scope"
        )
    pattern_allowed = term.get("pattern_evidence_allowed", False)
    if not isinstance(pattern_allowed, bool):
        raise QualitativeAdminError(
            f"qualitative phrase term {code!r}.pattern_evidence_allowed must be boolean"
        )
    variants = term.get("outward_variants")
    if not isinstance(variants, list) or len(variants) < 2:
        raise QualitativeAdminError(
            f"qualitative phrase term {code!r} requires at least two outward_variants"
        )
    cleaned = [
        _clean_string(value, f"qualitative phrase term {code!r}.outward_variants")
        for value in variants
    ]
    if len({value.casefold() for value in cleaned}) != len(cleaned):
        raise QualitativeAdminError(f"qualitative phrase term {code!r} variants must be unique")
    if risk == "high" and (pattern_allowed or required_scope != "dated_person_task"):
        raise QualitativeAdminError(
            f"high-risk qualitative phrase term {code!r} must forbid pattern evidence and require dated_person_task"
        )
    if any(_DEPLOYMENT_EXECUTION_CLAIM_PATTERN.search(value) for value in cleaned):
        if risk != "high" or pattern_allowed or required_scope != "dated_person_task":
            raise QualitativeAdminError(
                f"deployment-execution phrase term {code!r} must be high risk, forbid pattern evidence, and require dated_person_task"
            )
    return risk, required_scope, pattern_allowed, cleaned


def _canonical_input_sort_key(row: Any) -> tuple[str, ...]:
    if not isinstance(row, Mapping):
        return ("", "", "", "", "", "")
    evidence = row.get("workstream_evidence")
    evidence_key = json.dumps(evidence, sort_keys=True, separators=(",", ":"), default=str)
    return (
        str(row.get("date", "")),
        str(row.get("technician", "")).casefold(),
        str(row.get("program_assignment", "")).casefold(),
        str(row.get("paid_hours", "")),
        str(row.get("qualitative_work_context", "")).casefold(),
        evidence_key,
    )


def _row_fingerprint(row: Mapping[str, Any]) -> str:
    payload = "|".join(_canonical_input_sort_key(row))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _select_variant(
    *,
    catalog_id: str,
    month_key: str,
    row: Mapping[str, Any],
    code: str,
    variants: list[str],
    last_index_by_code: dict[str, int],
) -> tuple[int, str]:
    seed = "|".join(
        (
            catalog_id,
            month_key,
            _row_fingerprint(row),
            code,
        )
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest[:16], 16) % len(variants)
    if len(variants) > 1 and last_index_by_code.get(code) == index:
        index = (index + 1) % len(variants)
    last_index_by_code[code] = index
    return index, variants[index]


def _refs(value: Any, field: str, *, required: bool) -> list[str]:
    if value is None and not required:
        return []
    if not isinstance(value, list) or (required and not value):
        qualifier = "a non-empty list" if required else "a list"
        raise QualitativeAdminError(f"{field} must be {qualifier}")
    cleaned = [_clean_string(ref, field) for ref in value]
    if len(set(cleaned)) != len(cleaned):
        raise QualitativeAdminError(f"{field} contains duplicate references")
    return cleaned


def resolve_evidence_backed_contexts(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy whose evidence-backed rows have deterministic visible context.

    Legacy rows with ``qualitative_work_context`` and no ``workstream_evidence``
    remain unchanged. Evidence-backed rows must not also supply free text because
    that would create two competing semantic authorities. The generated receipt
    is reserved output metadata and is rejected when supplied by a caller.
    """

    resolved: dict[str, Any] = deepcopy(dict(spec))
    if _RESERVED_RECEIPT in resolved:
        raise QualitativeAdminError(
            f"{_RESERVED_RECEIPT} is reserved generated metadata and cannot be supplied by callers"
        )

    detail = resolved.get("detail_rows")
    if not isinstance(detail, list):
        return resolved
    if not any(
        isinstance(row, Mapping) and row.get("workstream_evidence") is not None
        for row in detail
    ):
        return resolved

    catalog = resolved.get("qualitative_phrase_catalog")
    if not isinstance(catalog, Mapping):
        raise QualitativeAdminError(
            "detail_rows.workstream_evidence requires qualitative_phrase_catalog"
        )
    catalog_id, terms = _catalog_terms(catalog)
    month_key = _clean_string(resolved.get("month_key"), "month_key")

    # Canonicalize before the no-repeat guard so equivalent input permutations
    # produce the same visible language, receipt, and eventual workbook order.
    detail.sort(key=_canonical_input_sort_key)
    last_index_by_code: dict[str, int] = {}
    receipt_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(detail):
        if not isinstance(row, dict):
            continue
        evidence = row.get("workstream_evidence")
        if evidence is None:
            continue
        if str(row.get("qualitative_work_context", "")).strip():
            raise QualitativeAdminError(
                f"detail_rows[{row_index}] cannot combine qualitative_work_context with workstream_evidence"
            )
        if not isinstance(evidence, list) or not evidence:
            raise QualitativeAdminError(
                f"detail_rows[{row_index}].workstream_evidence must be a non-empty list"
            )

        fragments: list[str] = []
        receipt_items: list[dict[str, Any]] = []
        seen_codes: set[str] = set()
        for item_index, item in enumerate(evidence):
            if not isinstance(item, Mapping):
                raise QualitativeAdminError(
                    f"detail_rows[{row_index}].workstream_evidence[{item_index}] must be an object"
                )
            prefix = f"detail_rows[{row_index}].workstream_evidence[{item_index}]"
            code = _clean_string(item.get("code"), f"{prefix}.code")
            if code in seen_codes:
                raise QualitativeAdminError(f"detail_rows[{row_index}] repeats workstream code {code!r}")
            seen_codes.add(code)
            term = terms.get(code)
            if not isinstance(term, Mapping):
                raise QualitativeAdminError(
                    f"detail_rows[{row_index}] references unknown workstream code {code!r}"
                )
            risk, required_scope, pattern_allowed, variants = _term_contract(code, term)
            scope = _clean_string(item.get("evidence_scope"), f"{prefix}.evidence_scope")
            if scope not in ALLOWED_SCOPES:
                raise QualitativeAdminError(
                    f"detail_rows[{row_index}] has invalid evidence_scope {scope!r}"
                )
            evidence_refs = _refs(item.get("evidence_refs"), f"{prefix}.evidence_refs", required=True)
            row_basis_refs = _refs(
                item.get("row_basis_refs"),
                f"{prefix}.row_basis_refs",
                required=scope == "recurring_pattern",
            )

            if risk == "high" and scope != "dated_person_task":
                raise QualitativeAdminError(
                    f"high-risk workstream {code!r} requires dated_person_task evidence"
                )
            if scope == "recurring_pattern" and not pattern_allowed:
                raise QualitativeAdminError(
                    f"workstream {code!r} does not allow recurring_pattern evidence"
                )
            if SCOPE_RANK[scope] < SCOPE_RANK[required_scope]:
                raise QualitativeAdminError(
                    f"workstream {code!r} evidence_scope {scope!r} is weaker than required {required_scope!r}"
                )

            variant_index, fragment = _select_variant(
                catalog_id=catalog_id,
                month_key=month_key,
                row=row,
                code=code,
                variants=variants,
                last_index_by_code=last_index_by_code,
            )
            fragments.append(fragment)
            receipt_items.append(
                {
                    "code": code,
                    "risk_tier": risk,
                    "evidence_scope": scope,
                    "evidence_refs": evidence_refs,
                    "row_basis_refs": row_basis_refs,
                    "variant_index": variant_index,
                    "visible_phrase": fragment,
                }
            )

        row["qualitative_work_context"] = "; ".join(fragments) + "."
        receipt_rows.append(
            {
                "detail_row_index": row_index,
                "date": str(row.get("date", "")),
                "technician": str(row.get("technician", "")),
                "workstreams": receipt_items,
            }
        )

    resolved[_RESERVED_RECEIPT] = {
        "schema_version": "nth-qualitative-context-receipt/v1",
        "catalog_id": catalog_id,
        "selection": "sha256 stable row identity over canonical row order with deterministic no-immediate-repeat guard",
        "canonical_codes_preserved": True,
        "evidence_refs_preserved": True,
        "row_basis_refs_preserved": True,
        "kpi_semantics_changed": False,
        "rows": receipt_rows,
    }
    return resolved
