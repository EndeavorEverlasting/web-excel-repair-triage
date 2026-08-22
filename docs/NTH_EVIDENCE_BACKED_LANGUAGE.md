# Evidence-Backed Qualitative Language

The qualitative NTH builder supports an optional evidence-backed presentation layer without owning business vocabulary.

## Ownership boundary

- The producer (for example FUN) owns canonical workstream codes, risk tiers, evidence authority, and phrase variants.
- Triage validates the supplied catalog, requires evidence references, and deterministically selects a visible phrase.
- Triage does not infer a workstream from attendance, device counts, program phase, or a synonym.

## Input seam

A detail row may use the legacy `qualitative_work_context` string **or** `workstream_evidence`, never both.

`workstream_evidence` items carry:

- `code` — canonical producer-owned workstream code;
- `evidence_scope` — `recurring_pattern`, `dated_context`, or `dated_person_task`;
- `evidence_refs` — one or more producer-owned evidence identifiers;
- `row_basis_refs` — required for `recurring_pattern`; dated/project/attendance basis proving why that recurring pattern is relevant to this specific row.

The top-level `qualitative_phrase_catalog` supplies each code's risk tier, minimum evidence scope, pattern-evidence policy, and visible phrase variants.

Evidence strength is monotonic: `recurring_pattern < dated_context < dated_person_task`. A supplied scope may never be weaker than the term's minimum. High-risk terms must require `dated_person_task` and must forbid recurring-pattern fallback.

The generated field `_evidence_backed_context_receipt` is reserved output metadata. Caller-supplied receipts are rejected rather than trusted.

## Deterministic presentation variation

Before phrase selection, evidence-backed detail rows are placed in a canonical order. Variant selection then uses a SHA-256 seed built from catalog ID, month, stable row fingerprint, and canonical code, with a deterministic no-immediate-repeat guard for the same code. Reordering equivalent input rows therefore does not change which row receives which phrase.

This improves readability when the same legitimate workstream recurs; it is not random and is not an obfuscation mechanism.

The generated manifest preserves a receipt containing canonical codes, evidence scopes, evidence refs, row-basis refs, selected variant indexes, and visible phrases. KPI semantics therefore remain stable even when the human-readable wording changes.

## Safety boundary

Presentation wording never creates attendance, exact task minutes, a new person/date fact, or a higher-risk claim. Recurring-pattern evidence can enrich a row only when its own producer-defined minimum permits it **and** the row supplies a separate compatibility basis. The workbook remains an audience projection of producer-supplied evidence; the manifest retains the auditable semantic/evidence mapping.

## Validation

```bash
python -m pytest tests/test_nth_evidence_backed_language.py -q
python -m pytest tests/test_nth_qualitative_admin.py -q
```
