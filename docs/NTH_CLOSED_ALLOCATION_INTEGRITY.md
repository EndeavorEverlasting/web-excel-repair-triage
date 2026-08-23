# NTH Closed Allocation Integrity

## Purpose

A paid attendance day may legitimately contain more than one project or workstream. The integrity requirement is not "one task per day"; it is **one closed attendance record per normalized staff/date whose positive allocation components reconcile exactly to the attendance control**.

This contract separates three different kinds of truth:

1. **attendance authority** — proves paid labor for the staff/date;
2. **allocation evidence** — supports how already-proven attendance is partitioned internally;
3. **planning/current-state context** — may describe future or unresolved work but does not create a closed paid allocation.

## Closed-day rules

`ClosedAttendanceAllocation` is the only closed-day object in `triage/nth_evidence_bounded_allocation.py`.

A closed day must satisfy all of the following:

- `attendance_hours` is finite and strictly greater than zero;
- every component is finite and strictly greater than zero;
- every component matches the closed record's normalized staff/date;
- every `allocation_id` is unique within the day;
- all component hours sum to attendance within the repository tolerance;
- a validated closed set contains at most one closed record per normalized staff/date;
- an `allocation_id` may not be reused across closed records.

Multiple components **are allowed** inside the one closed staff/date record. This preserves legitimate split-project days without allowing duplicate closed rows to double-count attendance.

Zero-hour future/planned work belongs in a planning/current-state record, not in `AllocationComponent` or `ClosedAttendanceAllocation`.

## Evidence authority labels

The reusable component contract recognizes four authority labels:

| Authority | Meaning | Paid-hours authority? | Visibility rule |
| --- | --- | --- | --- |
| `direct_task_evidence` | dated task evidence directly supports the component | no; attendance still controls labor | may be share-safe if its source permits |
| `direct_span_internal_control` | an observed/request-to-response span is used as an internal allocation control | no | internal only |
| `reported_internal_allocation` | operator-reported management allocation without an independently proven exact span | no | internal only |
| `derived_internal_management` | arithmetic remainder of attendance after stronger committed components | no | internal only; derivation required |

A direct span is not transformed into attendance authority. A derived remainder is not transformed into direct task evidence merely because it closes the day.

## Derived remainder

Use `derive_internal_management_remainder(...)` only after same-day attendance is known and one or more stronger components have already been committed.

```text
remainder = attendance_hours - sum(committed component hours)
```

The helper rejects a zero or negative remainder and writes the arithmetic into the component's `derivation` field.

Synthetic regression coverage includes an 8.0-hour attendance control with 1.0 and 3.2 committed internal components, producing a 3.8-hour explicitly derived remainder. Those numbers test the arithmetic and authority boundary; public Triage does not own private person/date operational state.

## Duplicate protection

Two different concepts must not be conflated:

- **legitimate split components:** several unique allocation IDs inside one staff/date record;
- **duplicate labor records:** more than one closed record for the same normalized staff/date, or reuse of an allocation ID.

`validate_closed_allocation_set(...)` accepts the first and rejects the second.

## Relationship to evidence-bounded Configuration

`EvidenceBoundedAllocation` remains the workload-capacity helper. It answers how much Configuration could be defensible under a selected attendance/labor ceiling.

`ClosedAttendanceAllocation` answers a different question: whether the chosen per-day allocation is structurally safe to close.

A workload envelope can never create attendance, and a closed-day reconciliation can never promote a weak allocation source into stronger task evidence.

## Validation

```bash
python -m pytest tests/test_nth_evidence_bounded_allocation.py -q
```

The owning CI must execute this regression file on pull requests and `main` pushes that exercise the artifact-engine surface.
