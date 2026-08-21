# Integrated Roster Ledger Validation

Triage owns the workbook-generation and repair mechanics for data validation. FUN owns the evidence meaning of the integrated roster's reusable Event Type and Status vocabulary. Google Drive preserves the current human-facing dictionary in the canonical roster.

## Current contract

For the canonical integrated roster, mutable Activity & Ad Hoc Ledger dropdowns must be backed by one worksheet dictionary rather than duplicated inline lists:

- Event Type target: `Activity & Ad Hoc Ledger!D11:D1000`
- Event Type dictionary: `Review Rules!J2:J100`
- Event Type guidance: `Review Rules!K2:K100`
- Status target: `Activity & Ad Hoc Ledger!K11:K1000`
- Status dictionary: `Review Rules!L2:L100`
- Status guidance: `Review Rules!M2:M100`

Use `triage.dv_range_sources.make_range_list_validation` for OOXML generation/repair paths that need these mechanics. Do not copy the current FUN vocabulary into Triage code as a second semantic authority.

## Failure mode this prevents

A strict inline dropdown can become stale while legitimate management categories continue to evolve. The cell then reports valid evidence as invalid even though the problem is the validation list, not the evidence. Reusable categories belong in the canonical dictionary; the validation rule points to that dictionary.

## Evidence boundary

Changing validation mechanics does not create paid hours, prove completed work, change project allocation, or promote internal context into client/leadership output. Attendance and FUN evidence contracts retain those authorities.
