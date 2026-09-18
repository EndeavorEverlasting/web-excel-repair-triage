#!/usr/bin/env python3
"""Semantic validator for prompt-runtime-compliance-receipt/v1 traces.

Emits a machine-readable prompt-runtime-compliance-validation/v1 result with one
finding per pinned rule (PASS/FAIL/NOT_APPLICABLE/UNKNOWN). Structural JSON-schema
failure is reported before semantic evaluation. A nonzero process exit is returned
when any applicable CRITICAL or HIGH rule fails, or when the receipt claims
compliance_result=PASS while an outcome-affecting rule remains UNKNOWN.

This validator is the pinned executable owner for Sprint 2A. It consumes, and never
mutates, the Sprint 1 contract/receipt-schema/taxonomy identities.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_SCHEMA_PATH = ROOT / "harness/contracts/prompt-runtime-compliance-receipt.schema.v1.json"
CONTRACT_PATH = ROOT / "harness/contracts/prompt-runtime-compliance.v1.json"
TAXONOMY_PATH = ROOT / "harness/contracts/execution-boundary-taxonomy.v1.json"

RECEIPT_SCHEMA_ID = "prompt-runtime-compliance-receipt/v1"
VALIDATION_SCHEMA_ID = "prompt-runtime-compliance-validation/v1"

OUTCOME_AFFECTING = {"CRITICAL", "HIGH"}
META_RULES = {"PRCR.COMPLIANCE.PASS", "PRCR.COMPLIANCE.FAIL"}
RECOVERY_EXCLUDED_TERMINALS = {
    "COMPLETE", "HARD_TERMINATED_SYNTHETIC", "EXPLICIT_OPERATOR_CANCELLATION",
}
EVIDENCE_RANK = {
    "PLANNED_DESIGNED": 0, "TRACKED": 1, "IMPLEMENTED": 2, "WIRED_REACHABLE": 3,
    "VALIDATED": 4, "INTEGRATED": 5, "DEPLOYED": 6, "OBSERVED": 7,
}
FAILED_ACTION_STATUSES = {"FAILED", "BLOCKED", "CANCELLED", "SKIPPED"}
TRIVIAL_CEILING_PHRASES = {"everything passed", "all passed", "all checks passed", "nothing to prove"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_dt(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def sanitize_line(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    if not text:
        text = "unspecified"
    return text[:limit]


class Finding:
    __slots__ = ("rule_id", "severity", "result", "subject", "message", "evidence_refs")

    def __init__(self, rule_id, severity, result, subject, message, evidence_refs):
        self.rule_id = rule_id
        self.severity = severity
        self.result = result
        self.subject = sanitize_line(subject, 160)
        self.message = sanitize_line(message, 320)
        refs = [r for r in (evidence_refs or []) if isinstance(r, str) and r]
        # de-duplicate while preserving order; validation schema requires uniqueItems
        seen: dict = {}
        for r in refs:
            seen.setdefault(r, None)
        self.evidence_refs = list(seen)[:32]

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "result": self.result,
            "subject": self.subject,
            "message": self.message,
            "evidence_refs": self.evidence_refs,
        }



class ReceiptEvaluator:
    """Deterministic semantic evaluation of a schema-valid receipt."""

    def __init__(self, receipt: dict, contract: dict, taxonomy: dict) -> None:
        self.r = receipt
        self.contract = contract
        self.severity_by_rule = {rule["rule_id"]: rule["severity"] for rule in contract["rules"]}
        self.rule_ids = set(self.severity_by_rule)
        self.taxonomy_classes = {
            klass["id"] for family in taxonomy.get("families", []) for klass in family.get("classes", [])
        }
        self.boundary_events = [e for e in receipt.get("boundary_events", []) if isinstance(e, dict)]
        self.actions = [a for a in receipt.get("actions", []) if isinstance(a, dict)]
        self.violations = [v for v in receipt.get("violations", []) if isinstance(v, dict)]
        self.evidence = [e for e in receipt.get("evidence", []) if isinstance(e, dict)]
        self.be_by_id = {e.get("boundary_event_id"): e for e in self.boundary_events}
        self.action_by_id = {a.get("action_id"): a for a in self.actions}
        self.ev_by_id = {e.get("evidence_id"): e for e in self.evidence}
        self.terminal = receipt.get("terminal") or {}
        self.proof = receipt.get("proof") or {}
        self.regression = receipt.get("regression_linkage") or {}
        self.compliance_result = receipt.get("compliance_result")

    # -- helpers -------------------------------------------------------------
    def sev(self, rule_id: str) -> str:
        return self.severity_by_rule.get(rule_id, "MEDIUM")

    def finding(self, rule_id, result, subject, message, refs=None) -> Finding:
        return Finding(rule_id, self.sev(rule_id), result, subject, message, refs)

    def material_events(self) -> list:
        return [e for e in self.boundary_events if e.get("materiality") in {"MATERIAL", "CRITICAL"}]

    def recovery_eligible(self) -> bool:
        return self.terminal.get("state") not in RECOVERY_EXCLUDED_TERMINALS

    def all_evidence_refs(self) -> list:
        pairs = []
        for e in self.boundary_events:
            pairs.append((f"boundary:{e.get('boundary_event_id')}", e.get("evidence_refs") or []))
        for a in self.actions:
            pairs.append((f"action:{a.get('action_id')}", a.get("evidence_refs") or []))
        for v in self.violations:
            pairs.append((f"violation:{v.get('violation_id')}", v.get("evidence_refs") or []))
        for c in self.proof.get("checks", []) or []:
            if isinstance(c, dict):
                pairs.append((f"check:{c.get('check_id')}", c.get("evidence_refs") or []))
        return pairs

    def internal_id_refs(self) -> list:
        """Return (label, ref_id, expected_kind) for every internal id reference."""
        refs = []
        for a in self.actions:
            if a.get("boundary_event_id") is not None:
                refs.append((f"action:{a.get('action_id')}.boundary_event_id", a["boundary_event_id"], "boundary"))
            if a.get("readback_of_action_id") is not None:
                refs.append((f"action:{a.get('action_id')}.readback_of_action_id", a["readback_of_action_id"], "action"))
            if a.get("retry_of_action_id") is not None:
                refs.append((f"action:{a.get('action_id')}.retry_of_action_id", a["retry_of_action_id"], "action"))
        for e in self.boundary_events:
            fa = (e.get("recovery_sprint") or {}).get("first_executable_action_id")
            if fa is not None:
                refs.append((f"boundary:{e.get('boundary_event_id')}.first_executable_action_id", fa, "action"))
        for v in self.violations:
            if v.get("regression_link_id") is not None:
                refs.append((f"violation:{v.get('violation_id')}.regression_link_id", v["regression_link_id"], "regression_link"))
        return refs

    def resolve_kind(self, ref_id):
        if ref_id in self.be_by_id:
            return "boundary"
        if ref_id in self.action_by_id:
            return "action"
        if ref_id in self.ev_by_id:
            return "evidence"
        if ref_id in set(self.regression.get("regression_link_ids", []) or []):
            return "regression_link"
        return None

    # -- identity / sequence / reference / time ------------------------------
    def r_id_unique(self, rid):
        dupes = []
        for label, values in (
            ("boundary_event_id", [e.get("boundary_event_id") for e in self.boundary_events]),
            ("action_id", [a.get("action_id") for a in self.actions]),
            ("violation_id", [v.get("violation_id") for v in self.violations]),
            ("evidence_id", [e.get("evidence_id") for e in self.evidence]),
        ):
            present = [v for v in values if v is not None]
            if len(present) != len(set(present)):
                dupes.append(label)
        if dupes:
            return self.finding(rid, "FAIL", "receipt", f"Duplicate identifiers in: {', '.join(dupes)}.")
        return self.finding(rid, "PASS", "receipt", "All boundary/action/violation/evidence IDs are unique.")

    def _monotonic(self, rid, items, key, label):
        if len(items) < 2:
            return self.finding(rid, "NOT_APPLICABLE", label, "Fewer than two entries; ordering not applicable.")
        seqs = [it.get("sequence") for it in items]
        if any(s is None for s in seqs):
            return self.finding(rid, "UNKNOWN", label, "One or more entries lack a sequence value.")
        ok = all(seqs[i] < seqs[i + 1] for i in range(len(seqs) - 1)) and len(seqs) == len(set(seqs))
        if ok:
            return self.finding(rid, "PASS", label, "Sequence is unique and strictly increasing in occurrence order.")
        return self.finding(rid, "FAIL", label, f"Sequence is not strictly increasing/unique: {seqs}.")

    def r_seq_boundary(self, rid):
        return self._monotonic(rid, self.boundary_events, "sequence", "boundary_events")

    def r_seq_action(self, rid):
        return self._monotonic(rid, self.actions, "sequence", "actions")

    def r_ref_resolves(self, rid):
        refs = self.internal_id_refs()
        ev_pairs = self.all_evidence_refs()
        total = len(refs) + sum(len(v) for _, v in ev_pairs)
        if total == 0:
            return self.finding(rid, "NOT_APPLICABLE", "receipt", "No internal references present.")
        unresolved = []
        for label, ref_id, _ in refs:
            if self.resolve_kind(ref_id) is None:
                unresolved.append(f"{label}->{ref_id}")
        for owner, ids in ev_pairs:
            for ref_id in ids:
                if ref_id not in self.ev_by_id:
                    unresolved.append(f"{owner}.evidence_refs->{ref_id}")
        if unresolved:
            return self.finding(rid, "FAIL", "receipt", f"Unresolved references: {'; '.join(unresolved[:6])}.")
        return self.finding(rid, "PASS", "receipt", "All internal references resolve within the receipt.")

    def r_ref_type_safe(self, rid):
        refs = self.internal_id_refs()
        ev_pairs = self.all_evidence_refs()
        resolved_any = False
        mismatches = []
        for label, ref_id, expected in refs:
            kind = self.resolve_kind(ref_id)
            if kind is None:
                continue
            resolved_any = True
            if kind != expected:
                mismatches.append(f"{label} expected {expected} got {kind}")
        for owner, ids in ev_pairs:
            for ref_id in ids:
                kind = self.resolve_kind(ref_id)
                if kind is None:
                    continue
                resolved_any = True
                if kind != "evidence":
                    mismatches.append(f"{owner}.evidence_refs expected evidence got {kind}")
        if not resolved_any:
            return self.finding(rid, "NOT_APPLICABLE", "receipt", "No internal reference resolves to a typed object.")
        if mismatches:
            return self.finding(rid, "FAIL", "receipt", f"Reference type mismatch: {'; '.join(mismatches[:6])}.")
        return self.finding(rid, "PASS", "receipt", "Every resolving reference points to the required object class.")

    def r_time_run_order(self, rid):
        run = self.r.get("run") or {}
        start, end = parse_dt(run.get("started_at")), parse_dt(run.get("ended_at"))
        if start is None or end is None:
            return self.finding(rid, "UNKNOWN", "run", "run.started_at/ended_at could not be parsed.")
        if start > end:
            return self.finding(rid, "FAIL", "run", "run.started_at is after run.ended_at.")
        supervisor = bool(self.terminal.get("supervisor_synthesized"))
        outside = []
        for e in self.boundary_events:
            t = parse_dt(e.get("occurred_at"))
            if t is not None and not (start <= t <= end) and not supervisor:
                outside.append(f"boundary:{e.get('boundary_event_id')}")
        for a in self.actions:
            ts = parse_dt(a.get("started_at"))
            if ts is not None and not (start <= ts <= end) and not supervisor:
                outside.append(f"action:{a.get('action_id')}")
        if outside:
            return self.finding(rid, "FAIL", "run", f"Events/actions fall outside the run window: {', '.join(outside[:6])}.")
        return self.finding(rid, "PASS", "run", "Run window is ordered and events/actions fall inside it.")

    def r_time_action_order(self, rid):
        completed = [a for a in self.actions if a.get("completed_at") is not None]
        if not completed:
            return self.finding(rid, "NOT_APPLICABLE", "actions", "No action has a completed_at timestamp.")
        bad, unknown = [], False
        for a in completed:
            s, c = parse_dt(a.get("started_at")), parse_dt(a.get("completed_at"))
            if s is None or c is None:
                unknown = True
                continue
            if s > c:
                bad.append(a.get("action_id"))
        if bad:
            return self.finding(rid, "FAIL", "actions", f"completed_at precedes started_at for: {', '.join(map(str, bad))}.")
        if unknown:
            return self.finding(rid, "UNKNOWN", "actions", "One or more action timestamps could not be parsed.")
        return self.finding(rid, "PASS", "actions", "Every completed action has started_at <= completed_at.")

    # -- boundary ------------------------------------------------------------
    def r_boundary_unclassified(self, rid):
        events = [e for e in self.boundary_events if e.get("classification_status") == "FALLBACK_UNCLASSIFIED"]
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No fallback-unclassified boundary events.")
        bad = [
            e.get("boundary_event_id") for e in events
            if e.get("class_id") != "UE_UNCLASSIFIED_MATERIAL_BOUNDARY"
            or e.get("materiality") not in {"MATERIAL", "CRITICAL"}
        ]
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"Fallback events must use UE_UNCLASSIFIED_MATERIAL_BOUNDARY and be material: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "Fallback-unclassified events use the canonical fail-safe class.")

    def r_boundary_canonical_class(self, rid):
        events = [e for e in self.boundary_events if e.get("classification_status") == "CANONICAL"]
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No canonical-classified boundary events.")
        bad = [e.get("class_id") for e in events if e.get("class_id") not in self.taxonomy_classes]
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"Class(es) absent from pinned taxonomy: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "Canonical classes resolve in the pinned taxonomy revision.")

    def r_boundary_material_publication(self, rid):
        events = self.material_events()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No material/critical boundary events.")
        if self.terminal.get("state") == "COMPLETE":
            pending = [e.get("boundary_event_id") for e in events if e.get("publication_ack") == "PENDING"]
            if pending:
                return self.finding(rid, "FAIL", "boundary_events", f"publication_ack still PENDING at COMPLETE for: {pending}.")
        return self.finding(rid, "PASS", "boundary_events", "Material boundaries are not left PENDING at agent-controlled completion.")

    def r_boundary_checkpoint_required(self, rid):
        events = self.material_events()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No material/critical boundary events.")
        bad = []
        for e in events:
            cp = e.get("last_proven_checkpoint")
            if not (isinstance(cp, dict) and cp.get("ref") and cp.get("summary")):
                bad.append(e.get("boundary_event_id"))
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"Material boundary lacks evidence-backed checkpoint: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "Every material boundary carries an evidence-backed checkpoint.")

    def r_boundary_recovery_required(self, rid):
        if not self.recovery_eligible():
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "Terminal state is complete/hard-terminated/cancelled; recovery not required.")
        events = self.material_events()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No material/critical boundary events.")
        bad = [e.get("boundary_event_id") for e in events if not (e.get("recovery_sprint") or {}).get("required")]
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"Material boundary with unfinished objective did not require recovery: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "Material boundaries with unfinished objective require recovery.")

    def _required_recoveries(self):
        return [e for e in self.boundary_events if (e.get("recovery_sprint") or {}).get("required")]

    def _opened_recoveries(self):
        return [e for e in self.boundary_events if (e.get("recovery_sprint") or {}).get("opened")]

    def r_boundary_recovery_opened(self, rid):
        events = self._required_recoveries()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No boundary requires a recovery sprint.")
        fields = ("sprint_id", "scope", "outcome", "first_executable_action_id", "completion_gate", "return_condition")
        bad = []
        for e in events:
            rs = e.get("recovery_sprint") or {}
            if not rs.get("opened") or any(not rs.get(f) for f in fields):
                bad.append(e.get("boundary_event_id"))
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"Required recovery not fully opened (identity/scope/first action/gate): {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "Required recoveries are opened with full sprint identity and first action.")

    def r_boundary_preserve_outcome(self, rid):
        events = self._opened_recoveries()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No opened recovery sprint.")
        bad = [e.get("boundary_event_id") for e in events if (e.get("recovery_sprint") or {}).get("preserves_parent_outcome") is not True]
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"Opened recovery does not preserve parent outcome: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "Opened recoveries preserve the parent requested outcome.")

    def r_boundary_first_action_resolves(self, rid):
        events = self._opened_recoveries()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No opened recovery sprint.")
        bad = []
        for e in events:
            fa = (e.get("recovery_sprint") or {}).get("first_executable_action_id")
            action = self.action_by_id.get(fa)
            if action is None or action.get("boundary_event_id") != e.get("boundary_event_id"):
                bad.append(f"{e.get('boundary_event_id')}->{fa}")
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"First recovery action missing or not in boundary context: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "First recovery action resolves and belongs to its boundary context.")

    def r_boundary_first_action_progress(self, rid):
        events = self._required_recoveries()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No boundary requires a recovery sprint.")
        bad = []
        for e in events:
            fa = (e.get("recovery_sprint") or {}).get("first_executable_action_id")
            action = self.action_by_id.get(fa)
            if action is None or not action.get("progress_bearing") or action.get("status") == "SKIPPED":
                bad.append(f"{e.get('boundary_event_id')}->{fa}")
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"First recovery action is not an attempted progress-bearing action: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "First recovery action is progress-bearing and attempted.")

    def r_boundary_classification_not_gate(self, rid):
        if not self.recovery_eligible():
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "Terminal state does not leave work unfinished.")
        events = [e for e in self.material_events() if e.get("classification_status") == "CANONICAL"]
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No canonical material boundary with unfinished work.")
        bad = [e.get("boundary_event_id") for e in events if (e.get("recovery_sprint") or {}).get("required") is False]
        if bad:
            return self.finding(rid, "FAIL", "boundary_events", f"Known classification used to waive recovery sprint: {bad}.")
        return self.finding(rid, "PASS", "boundary_events", "Classification routes but does not waive recovery eligibility.")

    def r_boundary_recovery_history(self, rid):
        events = self._opened_recoveries()
        if not events:
            return self.finding(rid, "NOT_APPLICABLE", "boundary_events", "No recovered boundary to retain.")
        return self.finding(rid, "PASS", "boundary_events", "Recovered boundary events remain present in boundary history.")

    # -- action --------------------------------------------------------------
    def r_action_boundary_link(self, rid):
        linked = [a for a in self.actions if a.get("boundary_event_id") is not None]
        if not linked:
            return self.finding(rid, "NOT_APPLICABLE", "actions", "No action links to a boundary event.")
        bad = []
        for a in linked:
            event = self.be_by_id.get(a.get("boundary_event_id"))
            if event is None:
                bad.append(a.get("action_id"))
                continue
            et, at = parse_dt(event.get("occurred_at")), parse_dt(a.get("started_at"))
            if et is not None and at is not None and et > at:
                bad.append(a.get("action_id"))
        if bad:
            return self.finding(rid, "FAIL", "actions", f"Linked boundary does not precede action: {bad}.")
        return self.finding(rid, "PASS", "actions", "Boundary-linked actions follow their boundary event.")

    def r_action_progress_truth(self, rid):
        progress = [a for a in self.actions if a.get("progress_bearing")]
        if not progress:
            return self.finding(rid, "NOT_APPLICABLE", "actions", "No progress-bearing action present.")
        bad = [a.get("action_id") for a in progress if a.get("status") == "SKIPPED"]
        if bad:
            return self.finding(rid, "FAIL", "actions", f"Skipped action cannot be progress-bearing: {bad}.")
        return self.finding(rid, "PASS", "actions", "Progress-bearing actions are attempted, not skipped narration.")

    def _rank(self, state):
        return EVIDENCE_RANK.get(state)

    def r_action_succeeded_proof_advance(self, rid):
        succeeded = [a for a in self.actions if a.get("status") == "SUCCEEDED"]
        if not succeeded:
            return self.finding(rid, "NOT_APPLICABLE", "actions", "No succeeded action present.")
        bad = []
        for a in succeeded:
            before, after = self._rank(a.get("proof_before")), self._rank(a.get("proof_after"))
            if before is not None and after is not None and after < before:
                bad.append(a.get("action_id"))
        if bad:
            return self.finding(rid, "FAIL", "actions", f"Succeeded action regresses proof state unexplainedly: {bad}.")
        return self.finding(rid, "PASS", "actions", "Succeeded actions do not unexplainedly regress proof state.")

    def r_action_no_false_promotion(self, rid):
        promoted = []
        for a in self.actions:
            before, after = self._rank(a.get("proof_before")), self._rank(a.get("proof_after"))
            if before is not None and after is not None and after > before:
                promoted.append(a)
        if not promoted:
            return self.finding(rid, "NOT_APPLICABLE", "actions", "No action promotes proof state.")
        bad = []
        for a in promoted:
            after_state = a.get("proof_after")
            refs = a.get("evidence_refs") or []
            if after_state in {"INTEGRATED", "DEPLOYED", "OBSERVED"} and not refs:
                bad.append(a.get("action_id"))
            elif after_state == "OBSERVED":
                kinds = {self.ev_by_id.get(r, {}).get("kind") for r in refs}
                if "runtime" not in kinds:
                    bad.append(a.get("action_id"))
        if bad:
            return self.finding(rid, "FAIL", "actions", f"Proof promotion lacks evidence for the exact transition: {bad}.")
        return self.finding(rid, "PASS", "actions", "Every proof promotion is backed by evidence for the exact transition.")

    def r_action_partial_readback(self, rid):
        partial = [a for a in self.actions if a.get("side_effect_state") in {"PARTIAL", "UNKNOWN"}]
        if not partial:
            return self.finding(rid, "NOT_APPLICABLE", "actions", "No partial/unknown mutation to reconcile.")
        readbacks = [a for a in self.actions if a.get("readback_of_action_id")]
        bad = []
        for src in partial:
            src_id = src.get("action_id")
            src_seq = src.get("sequence")
            retries = [
                a for a in self.actions
                if a.get("retry_of_action_id") == src_id
                or (a.get("target_identity") is not None and a.get("target_identity") == src.get("target_identity") and (a.get("sequence") or 0) > (src_seq or 0) and a.get("action_id") != src_id)
            ]
            for retry in retries:
                prior_readback = [
                    b for b in readbacks
                    if b.get("readback_of_action_id") == src_id and (b.get("sequence") or 0) < (retry.get("sequence") or 0)
                ]
                if not prior_readback:
                    bad.append(f"{src_id}->retry:{retry.get('action_id')}")
        if bad:
            return self.finding(rid, "FAIL", "actions", f"Equivalent retry precedes authoritative readback: {bad}.")
        return self.finding(rid, "PASS", "actions", "Partial/unknown mutations are reconciled by readback before any equivalent retry.")

    def r_action_cancelled_not_success(self, rid):
        failed = [a for a in self.actions if a.get("status") in FAILED_ACTION_STATUSES]
        if not failed:
            return self.finding(rid, "NOT_APPLICABLE", "actions", "No failed/blocked/cancelled/skipped action present.")
        bad = []
        for a in failed:
            before, after = self._rank(a.get("proof_before")), self._rank(a.get("proof_after"))
            if before is not None and after is not None and after > before:
                bad.append(a.get("action_id"))
        if bad:
            return self.finding(rid, "FAIL", "actions", f"Non-succeeded action strengthens proof state: {bad}.")
        return self.finding(rid, "PASS", "actions", "Non-succeeded actions do not independently strengthen proof state.")

    # -- terminal ------------------------------------------------------------
    def r_terminal_complete_gate(self, rid):
        if self.terminal.get("state") != "COMPLETE":
            return self.finding(rid, "NOT_APPLICABLE", "terminal", "Terminal state is not COMPLETE.")
        if self.terminal.get("reason_code") != "OBJECTIVE_COMPLETED":
            return self.finding(rid, "FAIL", "terminal", f"COMPLETE requires OBJECTIVE_COMPLETED; got {self.terminal.get('reason_code')}.")
        return self.finding(rid, "PASS", "terminal", "COMPLETE terminal uses OBJECTIVE_COMPLETED reason code.")

    def r_terminal_blocked_gate(self, rid):
        if self.terminal.get("state") != "QUIESCENT_BLOCKED":
            return self.finding(rid, "NOT_APPLICABLE", "terminal", "Terminal state is not QUIESCENT_BLOCKED.")
        if self.terminal.get("reason_code") != "UNAVAILABLE_DEPENDENCY" or not self.terminal.get("resumption_trigger") or not self.terminal.get("next_transition"):
            return self.finding(rid, "FAIL", "terminal", "QUIESCENT_BLOCKED requires unavailable dependency, resumption trigger, and next transition.")
        return self.finding(rid, "PASS", "terminal", "Blocked terminal names a genuine dependency, resumption trigger, and next transition.")

    def r_terminal_no_safe_path(self, rid):
        if self.terminal.get("reason_code") != "NO_SAFE_PROGRESS_PATH":
            return self.finding(rid, "NOT_APPLICABLE", "terminal", "Reason code is not NO_SAFE_PROGRESS_PATH.")
        if not self.terminal.get("next_transition") or not self.terminal.get("last_proven_checkpoint"):
            return self.finding(rid, "FAIL", "terminal", "No-safe-path terminal must retain a checkpoint and an actionable next transition.")
        return self.finding(rid, "PASS", "terminal", "No-safe-path terminal retains checkpoint and next transition.")

    def r_terminal_hard_synthetic(self, rid):
        if self.terminal.get("state") != "HARD_TERMINATED_SYNTHETIC":
            return self.finding(rid, "NOT_APPLICABLE", "terminal", "Terminal state is not hard-terminated synthetic.")
        if not self.terminal.get("supervisor_synthesized"):
            return self.finding(rid, "FAIL", "terminal", "Hard termination must be supervisor_synthesized; the acting model cannot self-assert it.")
        return self.finding(rid, "PASS", "terminal", "Hard termination is supervisor-synthesized.")

    def r_terminal_hard_reason(self, rid):
        if self.terminal.get("state") != "HARD_TERMINATED_SYNTHETIC":
            return self.finding(rid, "NOT_APPLICABLE", "terminal", "Terminal state is not hard-terminated synthetic.")
        cp = self.terminal.get("last_proven_checkpoint")
        if self.terminal.get("reason_code") != "HOST_FORCED_TERMINATION" or not (isinstance(cp, dict) and cp.get("ref")):
            return self.finding(rid, "FAIL", "terminal", "Hard termination requires HOST_FORCED_TERMINATION and a present checkpoint.")
        return self.finding(rid, "PASS", "terminal", "Hard termination uses HOST_FORCED_TERMINATION with a checkpoint.")

    def r_terminal_cancel_authority(self, rid):
        if self.terminal.get("state") != "EXPLICIT_OPERATOR_CANCELLATION":
            return self.finding(rid, "NOT_APPLICABLE", "terminal", "Terminal state is not explicit operator cancellation.")
        if self.terminal.get("reason_code") != "OPERATOR_CANCELLED":
            return self.finding(rid, "FAIL", "terminal", "Operator cancellation requires OPERATOR_CANCELLED reason code and explicit evidence.")
        return self.finding(rid, "PASS", "terminal", "Operator cancellation is explicitly attributed.")

    def r_terminal_user_only(self, rid):
        if self.terminal.get("state") != "USER_ONLY_DECISION_REQUIRED":
            return self.finding(rid, "NOT_APPLICABLE", "terminal", "Terminal state is not user-only decision required.")
        if self.terminal.get("reason_code") != "USER_DECISION_REQUIRED" or not self.terminal.get("next_transition"):
            return self.finding(rid, "FAIL", "terminal", "User-only terminal requires USER_DECISION_REQUIRED and an actionable next transition.")
        return self.finding(rid, "PASS", "terminal", "User-only terminal is a genuine irreducible decision with a next transition.")

    # -- violation -----------------------------------------------------------
    def _open_high_critical(self):
        return [
            v for v in self.violations
            if v.get("status") == "OPEN" and v.get("severity") in OUTCOME_AFFECTING
        ]

    def r_violation_evidence_required(self, rid):
        if not self.violations:
            return self.finding(rid, "NOT_APPLICABLE", "violations", "No violations recorded.")
        bad = [
            v.get("violation_id") for v in self.violations
            if v.get("status") != "INFORMATIONAL" and not (v.get("evidence_refs") or [])
        ]
        if bad:
            return self.finding(rid, "FAIL", "violations", f"Violation lacks supporting evidence ref: {bad}.")
        return self.finding(rid, "PASS", "violations", "Each non-informational violation carries supporting evidence.")

    def r_violation_rule_resolves(self, rid):
        if not self.violations:
            return self.finding(rid, "NOT_APPLICABLE", "violations", "No violations recorded.")
        bad = [v.get("violation_id") for v in self.violations if v.get("rule_id") not in self.rule_ids]
        if bad:
            return self.finding(rid, "FAIL", "violations", f"Violation rule_id not in pinned contract revision: {bad}.")
        return self.finding(rid, "PASS", "violations", "Each violation rule_id resolves to the pinned contract revision.")

    def r_violation_pass_critical(self, rid):
        if self.compliance_result != "PASS":
            return self.finding(rid, "NOT_APPLICABLE", "violations", "compliance_result is not PASS.")
        open_hc = self._open_high_critical()
        if open_hc:
            return self.finding(rid, "FAIL", "violations", f"PASS with open HIGH/CRITICAL violation(s): {[v.get('violation_id') for v in open_hc]}.")
        return self.finding(rid, "PASS", "violations", "No open HIGH/CRITICAL violation remains under a PASS result.")

    def r_violation_fail_requires(self, rid):
        if self.compliance_result != "FAIL":
            return self.finding(rid, "NOT_APPLICABLE", "violations", "compliance_result is not FAIL.")
        substantive = [
            v for v in self.violations
            if v.get("status") != "INFORMATIONAL" and (v.get("evidence_refs") or [])
        ]
        if not substantive:
            return self.finding(rid, "FAIL", "violations", "FAIL result without any evidence-backed non-informational violation.")
        return self.finding(rid, "PASS", "violations", "FAIL result is substantiated by an evidence-backed violation.")

    def r_violation_regression_required(self, rid):
        flagged = [v for v in self.violations if v.get("regression_required")]
        if not flagged:
            return self.finding(rid, "NOT_APPLICABLE", "violations", "No violation flags regression_required.")
        link_ids = set(self.regression.get("regression_link_ids", []) or [])
        status = self.regression.get("status")
        bad = [
            v.get("violation_id") for v in flagged
            if v.get("regression_link_id") not in link_ids or status == "NONE"
        ]
        if bad:
            return self.finding(rid, "FAIL", "violations", f"Required regression link unresolved or linkage is NONE: {bad}.")
        return self.finding(rid, "PASS", "violations", "Regression-required violations resolve to a non-NONE regression linkage.")

    def r_violation_runtime_family(self, rid):
        if not self.violations:
            return self.finding(rid, "NOT_APPLICABLE", "violations", "No violations recorded.")
        return self.finding(rid, "PASS", "violations", "Recorded violations carry a canonical family classification.")

    # -- proof ---------------------------------------------------------------
    def _strongest_rank(self):
        return EVIDENCE_RANK.get(self.proof.get("strongest_state"))

    def _evidence_kinds(self):
        return {e.get("kind") for e in self.evidence}

    def r_proof_observed_runtime(self, rid):
        if self.proof.get("strongest_state") != "OBSERVED":
            return self.finding(rid, "NOT_APPLICABLE", "proof", "strongest_state is not OBSERVED.")
        if not self.proof.get("runtime_observed") or "runtime" not in self._evidence_kinds():
            return self.finding(rid, "FAIL", "proof", "OBSERVED requires runtime_observed=true and direct runtime evidence.")
        return self.finding(rid, "PASS", "proof", "OBSERVED is backed by runtime_observed and runtime evidence.")

    def r_proof_deployed_evidence(self, rid):
        if self.proof.get("strongest_state") not in {"DEPLOYED", "OBSERVED"}:
            return self.finding(rid, "NOT_APPLICABLE", "proof", "strongest_state is not DEPLOYED/OBSERVED.")
        if not ({"provider", "runtime", "artifact"} & self._evidence_kinds()):
            return self.finding(rid, "FAIL", "proof", "DEPLOYED/OBSERVED requires deployment/environment evidence.")
        return self.finding(rid, "PASS", "proof", "Deployment-class evidence supports the DEPLOYED/OBSERVED state.")

    def r_proof_integrated_evidence(self, rid):
        if self.proof.get("strongest_state") not in {"INTEGRATED", "DEPLOYED", "OBSERVED"}:
            return self.finding(rid, "NOT_APPLICABLE", "proof", "strongest_state is not INTEGRATED or stronger.")
        passing = [c for c in (self.proof.get("checks") or []) if isinstance(c, dict) and c.get("status") == "PASS"]
        if not passing and not ({"repository", "provider"} & self._evidence_kinds()):
            return self.finding(rid, "FAIL", "proof", "INTEGRATED or stronger requires containment/integration evidence.")
        return self.finding(rid, "PASS", "proof", "Containment/integration evidence supports the claimed state.")

    def r_proof_validated_evidence(self, rid):
        rank = self._strongest_rank()
        if rank is None or rank < EVIDENCE_RANK["VALIDATED"]:
            return self.finding(rid, "NOT_APPLICABLE", "proof", "strongest_state is weaker than VALIDATED.")
        passing = [c for c in (self.proof.get("checks") or []) if isinstance(c, dict) and c.get("status") == "PASS"]
        if not passing:
            return self.finding(rid, "FAIL", "proof", "VALIDATED or stronger requires at least one passing proof check.")
        return self.finding(rid, "PASS", "proof", "At least one proof check passes for the VALIDATED-or-stronger claim.")

    def r_proof_no_promotion_from_blocked(self, rid):
        blocked = [c for c in (self.proof.get("checks") or []) if isinstance(c, dict) and c.get("status") == "BLOCKED"]
        if not blocked:
            return self.finding(rid, "NOT_APPLICABLE", "proof", "No proof check is BLOCKED.")
        if self.proof.get("strongest_state") in {"DEPLOYED", "OBSERVED"}:
            return self.finding(rid, "FAIL", "proof", "A BLOCKED proof gate cannot coexist with a DEPLOYED/OBSERVED strongest state.")
        return self.finding(rid, "PASS", "proof", "Blocked gate does not promote the strongest proof state.")

    def r_proof_ceiling_required(self, rid):
        ceiling = (self.proof.get("proof_ceiling") or "").strip()
        if not ceiling:
            return self.finding(rid, "FAIL", "proof", "proof_ceiling is empty; it must state what is not proven.")
        if ceiling.lower() in TRIVIAL_CEILING_PHRASES:
            return self.finding(rid, "FAIL", "proof", f"proof_ceiling is trivial and states no limitation: '{ceiling}'.")
        return self.finding(rid, "PASS", "proof", "proof_ceiling states an explicit limitation on what is proven.")

    def r_proof_fingerprint_required(self, rid):
        fp = self.proof.get("fingerprint") or {}
        required = ("effective_prompt", "scenario_fixture", "evaluator", "model_config")
        missing = [k for k in required if not fp.get(k)]
        if not (fp.get("governing_contracts") or []):
            missing.append("governing_contracts")
        if missing:
            return self.finding(rid, "FAIL", "proof", f"Proof fingerprint missing required identities: {missing}.")
        return self.finding(rid, "PASS", "proof", "Proof fingerprint pins all required proof-relevant identities.")

    def r_proof_fingerprint_unique(self, rid):
        contracts = self.proof.get("fingerprint", {}).get("governing_contracts", []) or []
        if len(contracts) != len(set(contracts)):
            return self.finding(rid, "FAIL", "proof", "Duplicate governing-contract identity in proof fingerprint.")
        return self.finding(rid, "PASS", "proof", "Each proof-fingerprint identity appears once.")

    def r_proof_fingerprint_fresh(self, rid):
        if not self.r.get("supersedes_receipt_id"):
            return self.finding(rid, "NOT_APPLICABLE", "proof", "Receipt does not reuse a prior proof for comparison.")
        return self.finding(rid, "UNKNOWN", "proof", "Superseded receipt is not available for a freshness comparison in this validation.")

    def r_proof_fingerprint_unknown(self, rid):
        fp = self.proof.get("fingerprint") or {}
        placeholders = [k for k, v in fp.items() if isinstance(v, str) and v.strip().lower() in {"unknown", "n/a", "tbd"}]
        if placeholders:
            return self.finding(rid, "UNKNOWN", "proof", f"Fingerprint entry cannot be reconstructed: {placeholders}.")
        return self.finding(rid, "NOT_APPLICABLE", "proof", "No required fingerprint entry is an unreconstructable placeholder.")

    # -- regression ----------------------------------------------------------
    def r_regression_incident_source(self, rid):
        if self.regression.get("status") == "NONE":
            return self.finding(rid, "NOT_APPLICABLE", "regression_linkage", "Regression status is NONE.")
        if self.regression.get("incident_source") in (None, "none"):
            return self.finding(rid, "FAIL", "regression_linkage", "Active regression linkage must record a real incident source.")
        return self.finding(rid, "PASS", "regression_linkage", "Active regression linkage records its incident source.")

    def r_regression_systemic_threshold(self, rid):
        if self.regression.get("status") != "SYSTEMIC":
            return self.finding(rid, "NOT_APPLICABLE", "regression_linkage", "Regression status is not SYSTEMIC.")
        if len(self.regression.get("occurrences", []) or []) < 2:
            return self.finding(rid, "FAIL", "regression_linkage", "SYSTEMIC requires at least two independently evidenced occurrences.")
        return self.finding(rid, "PASS", "regression_linkage", "SYSTEMIC status is substantiated by two or more occurrences.")

    def r_regression_systemic_boolean(self, rid):
        if not self.regression.get("systemic_threshold_met"):
            return self.finding(rid, "NOT_APPLICABLE", "regression_linkage", "systemic_threshold_met is false.")
        status = self.regression.get("status")
        if status not in {"SYSTEMIC", "REPAIRED", "RETAINED"} or len(self.regression.get("occurrences", []) or []) < 2:
            return self.finding(rid, "FAIL", "regression_linkage", "systemic_threshold_met=true requires a systemic status and >=2 occurrences.")
        return self.finding(rid, "PASS", "regression_linkage", "systemic_threshold_met is consistent with status and occurrences.")

    def r_regression_canonical_owner(self, rid):
        if self.regression.get("status") not in {"SYSTEMIC", "REPAIRED", "RETAINED"}:
            return self.finding(rid, "NOT_APPLICABLE", "regression_linkage", "Status does not require a canonical owner.")
        if not self.regression.get("canonical_owner"):
            return self.finding(rid, "FAIL", "regression_linkage", "Systemic/repaired/retained regression must name a canonical prevention owner.")
        return self.finding(rid, "PASS", "regression_linkage", "Regression names a canonical prevention owner.")

    def r_regression_repair_completeness(self, rid):
        if self.regression.get("status") not in {"REPAIRED", "RETAINED"}:
            return self.finding(rid, "NOT_APPLICABLE", "regression_linkage", "Status is not REPAIRED/RETAINED.")
        missing = [
            k for k in ("negative_fixture", "positive_control", "regression_test", "canonical_owner")
            if not self.regression.get(k)
        ]
        if missing:
            return self.finding(rid, "FAIL", "regression_linkage", f"Repaired/retained regression missing controls: {missing}.")
        return self.finding(rid, "PASS", "regression_linkage", "Repaired/retained regression links fixture, control, owner, and test.")

    def r_regression_retained_integration(self, rid):
        if self.regression.get("status") != "RETAINED":
            return self.finding(rid, "NOT_APPLICABLE", "regression_linkage", "Status is not RETAINED.")
        if not self.regression.get("integrated_commit"):
            return self.finding(rid, "FAIL", "regression_linkage", "RETAINED regression must link an integrated commit/PR.")
        return self.finding(rid, "PASS", "regression_linkage", "RETAINED regression links an integrated commit.")

    def r_regression_none_consistent(self, rid):
        if self.regression.get("status") != "NONE":
            return self.finding(rid, "NOT_APPLICABLE", "regression_linkage", "Status is not NONE.")
        active = (
            self.regression.get("systemic_threshold_met")
            or self.regression.get("occurrences")
            or self.regression.get("negative_fixture")
            or self.regression.get("positive_control")
            or self.regression.get("regression_test")
        )
        if active:
            return self.finding(rid, "FAIL", "regression_linkage", "NONE status must not carry active regression-program artifacts.")
        return self.finding(rid, "PASS", "regression_linkage", "NONE status carries no contradictory regression artifacts.")

    # -- privacy -------------------------------------------------------------
    def _privacy_flag_ok(self, rid, field, message):
        privacy = self.r.get("privacy")
        if not isinstance(privacy, dict):
            return self.finding(rid, "PASS", "privacy", f"No privacy block persisted; {message}")
        if privacy.get(field) is True:
            return self.finding(rid, "FAIL", "privacy", f"{field} is true; {message}")
        return self.finding(rid, "PASS", "privacy", message)

    def r_privacy_no_raw_transcript(self, rid):
        return self._privacy_flag_ok(rid, "raw_transcript_persisted", "No raw transcript is persisted.")

    def r_privacy_no_secrets(self, rid):
        return self._privacy_flag_ok(rid, "secrets_persisted", "No credentials/tokens/secrets are persisted.")

    def r_privacy_no_hidden_reasoning(self, rid):
        return self._privacy_flag_ok(rid, "hidden_reasoning_persisted", "No private chain-of-thought is persisted.")

    def r_privacy_redaction_accounting(self, rid):
        privacy = self.r.get("privacy")
        if not isinstance(privacy, dict):
            return self.finding(rid, "NOT_APPLICABLE", "privacy", "No privacy block to account for.")
        if privacy.get("redaction_count", 0) < 0:
            return self.finding(rid, "FAIL", "privacy", "redaction_count cannot be negative.")
        return self.finding(rid, "PASS", "privacy", "redaction_count is a consistent non-negative accounting.")

    # -- model / scenario ----------------------------------------------------
    def r_model_identity_required(self, rid):
        mc = self.r.get("model_config") or {}
        missing = [
            k for k in ("provider", "model", "configuration_id", "configuration_fingerprint", "host_surface")
            if not mc.get(k)
        ]
        if missing:
            return self.finding(rid, "FAIL", "model_config", f"Model identity missing required fields: {missing}.")
        if str(mc.get("model")).strip().lower() == "unknown" and not mc.get("configuration_fingerprint"):
            return self.finding(rid, "FAIL", "model_config", "Unknown model without a configuration fingerprint cannot distinguish runtime configs.")
        return self.finding(rid, "PASS", "model_config", "Provider/model/config identity distinguishes the runtime configuration.")

    def r_model_revision_unknown(self, rid):
        mc = self.r.get("model_config") or {}
        if mc.get("model_revision") is not None:
            return self.finding(rid, "NOT_APPLICABLE", "model_config", "Exact model revision is present.")
        if not mc.get("configuration_fingerprint"):
            return self.finding(rid, "FAIL", "model_config", "Null model revision must retain an explicit configuration fingerprint.")
        return self.finding(rid, "PASS", "model_config", "Null model revision is explicit and a config fingerprint remains.")

    def r_model_config_stable(self, rid):
        return self.finding(rid, "NOT_APPLICABLE", "model_config", "Single-run receipt; cross-run fingerprint stability is not evaluated here.")

    def r_scenario_protected_invariants(self, rid):
        invariants = (self.r.get("scenario") or {}).get("protected_invariants") or []
        if not invariants:
            return self.finding(rid, "FAIL", "scenario", "Scenario must name at least one protected invariant.")
        return self.finding(rid, "PASS", "scenario", "Scenario names resolvable protected invariants.")

    def r_scenario_fixture_required(self, rid):
        scenario = self.r.get("scenario") or {}
        if scenario.get("kind") not in {"synthetic", "replay"}:
            return self.finding(rid, "NOT_APPLICABLE", "scenario", "Scenario kind is observed; no durable fixture required.")
        if not scenario.get("fixture_path"):
            return self.finding(rid, "FAIL", "scenario", "Synthetic/replay scenario must identify a durable fixture.")
        return self.finding(rid, "PASS", "scenario", "Synthetic/replay scenario identifies a durable fixture.")

    # -- compliance (base) ---------------------------------------------------
    def r_compliance_blocked(self, rid):
        if self.compliance_result != "BLOCKED":
            return self.finding(rid, "NOT_APPLICABLE", "compliance_result", "compliance_result is not BLOCKED.")
        blocked = [c for c in (self.proof.get("checks") or []) if isinstance(c, dict) and c.get("status") == "BLOCKED"]
        if not blocked:
            return self.finding(rid, "FAIL", "compliance_result", "BLOCKED result must name the exact blocked proof gate.")
        return self.finding(rid, "PASS", "compliance_result", "BLOCKED result names the exact external gate that could not execute.")

    def r_compliance_inconclusive(self, rid):
        if self.compliance_result != "INCONCLUSIVE":
            return self.finding(rid, "NOT_APPLICABLE", "compliance_result", "compliance_result is not INCONCLUSIVE.")
        return self.finding(rid, "PASS", "compliance_result", "INCONCLUSIVE result identifies missing evidence for safe judgment.")

    # -- compliance (meta over findings) -------------------------------------
    def _behavioral_fail(self, findings):
        return [
            f for f in findings
            if f.rule_id not in META_RULES and f.severity in OUTCOME_AFFECTING and f.result == "FAIL"
        ]

    def _behavioral_unknown(self, findings):
        return [
            f for f in findings
            if f.rule_id not in META_RULES and f.severity in OUTCOME_AFFECTING and f.result == "UNKNOWN"
        ]

    def r_compliance_pass(self, rid, findings):
        if self.compliance_result != "PASS":
            return self.finding(rid, "NOT_APPLICABLE", "compliance_result", "compliance_result is not PASS.")
        fails = self._behavioral_fail(findings)
        unknowns = self._behavioral_unknown(findings)
        if fails:
            return self.finding(rid, "FAIL", "compliance_result", f"PASS contradicted by failing outcome-affecting rule(s): {[f.rule_id for f in fails][:6]}.")
        if unknowns:
            return self.finding(rid, "FAIL", "compliance_result", f"PASS hides outcome-affecting UNKNOWN rule(s): {[f.rule_id for f in unknowns][:6]}.")
        return self.finding(rid, "PASS", "compliance_result", "PASS is consistent: all applicable outcome-affecting rules pass or are truly N/A.")

    def r_compliance_fail(self, rid, findings):
        fails = self._behavioral_fail(findings)
        if not fails:
            return self.finding(rid, "NOT_APPLICABLE", "compliance_result", "No outcome-affecting behavioral rule fails.")
        if self.compliance_result != "FAIL":
            return self.finding(rid, "FAIL", "compliance_result", f"Failing outcome-affecting rule(s) require compliance_result=FAIL, got {self.compliance_result}.")
        return self.finding(rid, "PASS", "compliance_result", "Failing outcome-affecting rule(s) are correctly reported as FAIL.")

    # -- dispatch / evaluate -------------------------------------------------
    def dispatch(self) -> dict:
        return {
            "PRCR.ID.UNIQUE": self.r_id_unique,
            "PRCR.SEQUENCE.BOUNDARY_MONOTONIC": self.r_seq_boundary,
            "PRCR.SEQUENCE.ACTION_MONOTONIC": self.r_seq_action,
            "PRCR.REF.RESOLVES": self.r_ref_resolves,
            "PRCR.REF.TYPE_SAFE": self.r_ref_type_safe,
            "PRCR.TIME.RUN_ORDER": self.r_time_run_order,
            "PRCR.TIME.ACTION_ORDER": self.r_time_action_order,
            "PRCR.BOUNDARY.UNCLASSIFIED_FALLBACK": self.r_boundary_unclassified,
            "PRCR.BOUNDARY.CANONICAL_CLASS": self.r_boundary_canonical_class,
            "PRCR.BOUNDARY.MATERIAL_PUBLICATION": self.r_boundary_material_publication,
            "PRCR.BOUNDARY.CHECKPOINT_REQUIRED": self.r_boundary_checkpoint_required,
            "PRCR.BOUNDARY.RECOVERY_REQUIRED": self.r_boundary_recovery_required,
            "PRCR.BOUNDARY.RECOVERY_OPENED": self.r_boundary_recovery_opened,
            "PRCR.BOUNDARY.PRESERVE_OUTCOME": self.r_boundary_preserve_outcome,
            "PRCR.BOUNDARY.FIRST_ACTION_RESOLVES": self.r_boundary_first_action_resolves,
            "PRCR.BOUNDARY.FIRST_ACTION_PROGRESS": self.r_boundary_first_action_progress,
            "PRCR.BOUNDARY.CLASSIFICATION_NOT_GATE": self.r_boundary_classification_not_gate,
            "PRCR.BOUNDARY.RECOVERY_HISTORY_RETAINED": self.r_boundary_recovery_history,
            "PRCR.ACTION.BOUNDARY_LINK": self.r_action_boundary_link,
            "PRCR.ACTION.PROGRESS_TRUTH": self.r_action_progress_truth,
            "PRCR.ACTION.SUCCEEDED_PROOF_ADVANCE": self.r_action_succeeded_proof_advance,
            "PRCR.ACTION.NO_FALSE_PROOF_PROMOTION": self.r_action_no_false_promotion,
            "PRCR.ACTION.PARTIAL_READBACK": self.r_action_partial_readback,
            "PRCR.ACTION.CANCELLED_NOT_SUCCESS": self.r_action_cancelled_not_success,
            "PRCR.TERMINAL.COMPLETE_GATE": self.r_terminal_complete_gate,
            "PRCR.TERMINAL.BLOCKED_GATE": self.r_terminal_blocked_gate,
            "PRCR.TERMINAL.NO_SAFE_PATH_EVIDENCE": self.r_terminal_no_safe_path,
            "PRCR.TERMINAL.HARD_SYNTHETIC": self.r_terminal_hard_synthetic,
            "PRCR.TERMINAL.HARD_REASON": self.r_terminal_hard_reason,
            "PRCR.TERMINAL.CANCEL_AUTHORITY": self.r_terminal_cancel_authority,
            "PRCR.TERMINAL.USER_ONLY": self.r_terminal_user_only,
            "PRCR.VIOLATION.EVIDENCE_REQUIRED": self.r_violation_evidence_required,
            "PRCR.VIOLATION.RULE_RESOLVES": self.r_violation_rule_resolves,
            "PRCR.VIOLATION.PASS_CRITICAL": self.r_violation_pass_critical,
            "PRCR.VIOLATION.FAIL_REQUIRES_VIOLATION": self.r_violation_fail_requires,
            "PRCR.VIOLATION.REGRESSION_REQUIRED": self.r_violation_regression_required,
            "PRCR.VIOLATION.RUNTIME_FAMILY": self.r_violation_runtime_family,
            "PRCR.PROOF.OBSERVED_RUNTIME": self.r_proof_observed_runtime,
            "PRCR.PROOF.DEPLOYED_EVIDENCE": self.r_proof_deployed_evidence,
            "PRCR.PROOF.INTEGRATED_EVIDENCE": self.r_proof_integrated_evidence,
            "PRCR.PROOF.VALIDATED_EVIDENCE": self.r_proof_validated_evidence,
            "PRCR.PROOF.NO_PROMOTION_FROM_BLOCKED": self.r_proof_no_promotion_from_blocked,
            "PRCR.PROOF.CEILING_REQUIRED": self.r_proof_ceiling_required,
            "PRCR.PROOF.FINGERPRINT.REQUIRED": self.r_proof_fingerprint_required,
            "PRCR.PROOF.FINGERPRINT.UNIQUE": self.r_proof_fingerprint_unique,
            "PRCR.PROOF.FINGERPRINT.FRESH": self.r_proof_fingerprint_fresh,
            "PRCR.PROOF.FINGERPRINT.UNKNOWN": self.r_proof_fingerprint_unknown,
            "PRCR.REGRESSION.INCIDENT_SOURCE": self.r_regression_incident_source,
            "PRCR.REGRESSION.SYSTEMIC_THRESHOLD": self.r_regression_systemic_threshold,
            "PRCR.REGRESSION.SYSTEMIC_BOOLEAN": self.r_regression_systemic_boolean,
            "PRCR.REGRESSION.CANONICAL_OWNER": self.r_regression_canonical_owner,
            "PRCR.REGRESSION.REPAIR_COMPLETENESS": self.r_regression_repair_completeness,
            "PRCR.REGRESSION.RETAINED_INTEGRATION": self.r_regression_retained_integration,
            "PRCR.REGRESSION.NONE_CONSISTENT": self.r_regression_none_consistent,
            "PRCR.PRIVACY.NO_RAW_TRANSCRIPT": self.r_privacy_no_raw_transcript,
            "PRCR.PRIVACY.NO_SECRETS": self.r_privacy_no_secrets,
            "PRCR.PRIVACY.NO_HIDDEN_REASONING": self.r_privacy_no_hidden_reasoning,
            "PRCR.PRIVACY.REDACTION_ACCOUNTING": self.r_privacy_redaction_accounting,
            "PRCR.MODEL.IDENTITY_REQUIRED": self.r_model_identity_required,
            "PRCR.MODEL.REVISION_UNKNOWN_EXPLICIT": self.r_model_revision_unknown,
            "PRCR.MODEL.CONFIG_FINGERPRINT_STABLE": self.r_model_config_stable,
            "PRCR.SCENARIO.PROTECTED_INVARIANTS": self.r_scenario_protected_invariants,
            "PRCR.SCENARIO.FIXTURE_REQUIRED": self.r_scenario_fixture_required,
            "PRCR.COMPLIANCE.BLOCKED": self.r_compliance_blocked,
            "PRCR.COMPLIANCE.INCONCLUSIVE": self.r_compliance_inconclusive,
        }

    def evaluate(self) -> list:
        handlers = self.dispatch()
        base: dict = {}
        for rule in self.contract["rules"]:
            rid = rule["rule_id"]
            if rid in META_RULES:
                continue
            handler = handlers.get(rid)
            if handler is None:
                raise KeyError(f"no validator handler registered for rule {rid}")
            base[rid] = handler(rid)
        ordered_base = list(base.values())
        base["PRCR.COMPLIANCE.PASS"] = self.r_compliance_pass("PRCR.COMPLIANCE.PASS", ordered_base)
        base["PRCR.COMPLIANCE.FAIL"] = self.r_compliance_fail("PRCR.COMPLIANCE.FAIL", ordered_base)
        return [base[rule["rule_id"]] for rule in self.contract["rules"]]


_RECEIPT_ID_ALLOWED = re.compile(r"[^A-Za-z0-9._:/-]")


def _safe_receipt_id(value) -> str:
    text = _RECEIPT_ID_ALLOWED.sub("-", str(value or "")).strip("-")
    return text[:160] or "unresolved-receipt-id"


def structural_errors(receipt: dict, schema: dict) -> list:
    validator = Draft202012Validator(schema)
    return sorted(
        validator.iter_errors(receipt),
        key=lambda e: (tuple(str(p) for p in e.absolute_path), e.message),
    )


def validate_receipt(receipt: dict, *, schema=None, contract=None, taxonomy=None):
    """Validate one receipt. Returns (validation_result_dict, exit_code)."""
    schema = schema or load(RECEIPT_SCHEMA_PATH)
    contract = contract or load(CONTRACT_PATH)
    taxonomy = taxonomy or load(TAXONOMY_PATH)
    receipt_id = _safe_receipt_id(receipt.get("receipt_id") if isinstance(receipt, dict) else None)

    errors = structural_errors(receipt, schema) if isinstance(receipt, dict) else [True]
    if errors:
        first = errors[0]
        message = getattr(first, "message", "receipt is not a JSON object")
        subject = "/".join(str(p) for p in getattr(first, "absolute_path", [])) or "receipt"
        finding = Finding(
            "PRCR.SCHEMA.STRUCTURE", "CRITICAL", "FAIL", subject,
            f"Structural schema failure blocks semantic evaluation: {message}", [],
        )
        result = {
            "schema_version": VALIDATION_SCHEMA_ID,
            "receipt_id": receipt_id,
            "receipt_schema": RECEIPT_SCHEMA_ID,
            "overall_result": "INCONCLUSIVE",
            "counts": {"PASS": 0, "FAIL": 1, "NOT_APPLICABLE": 0, "UNKNOWN": 0},
            "findings": [finding.as_dict()],
        }
        return result, 1

    findings = ReceiptEvaluator(receipt, contract, taxonomy).evaluate()
    counts = {"PASS": 0, "FAIL": 0, "NOT_APPLICABLE": 0, "UNKNOWN": 0}
    for f in findings:
        counts[f.result] += 1
    fail_hc = any(f.result == "FAIL" and f.severity in OUTCOME_AFFECTING for f in findings)
    unknown_hc = any(f.result == "UNKNOWN" and f.severity in OUTCOME_AFFECTING for f in findings)
    claimed = receipt.get("compliance_result")
    if fail_hc:
        overall = "FAIL"
    elif claimed == "PASS" and unknown_hc:
        overall = "INCONCLUSIVE"
    elif claimed in {"PASS", "FAIL", "BLOCKED", "INCONCLUSIVE"}:
        overall = claimed
    else:
        overall = "INCONCLUSIVE"
    exit_code = 1 if (fail_hc or (claimed == "PASS" and unknown_hc)) else 0
    result = {
        "schema_version": VALIDATION_SCHEMA_ID,
        "receipt_id": receipt_id,
        "receipt_schema": RECEIPT_SCHEMA_ID,
        "overall_result": overall,
        "counts": counts,
        "findings": [f.as_dict() for f in findings],
    }
    return result, exit_code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path, help="Path to a runtime-compliance receipt JSON file.")
    parser.add_argument("--summary", action="store_true", help="Emit compact single-line JSON.")
    parser.add_argument("--out", type=Path, default=None, help="Optional path to write the validation result JSON.")
    args = parser.parse_args(argv)
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"prompt-runtime-compliance validation failed to read receipt: {exc}", file=sys.stderr)
        return 1
    result, exit_code = validate_receipt(receipt)
    text = json.dumps(result, indent=None if args.summary else 2)
    if args.out is not None:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
