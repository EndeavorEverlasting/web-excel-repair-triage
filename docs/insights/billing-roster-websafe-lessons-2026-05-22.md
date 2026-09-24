# Billing/Roster Web-Safe Lessons Learned

Date captured: 2026-05-22

Purpose: preserve the operational lessons from a live roster-to-billing reconciliation cycle so future workbook generation can be automated without repeating manual mistakes.

This document is intentionally business-logic focused. It does not store employee evidence, screenshots, payroll details, client-private material, or workbook artifacts. Keep the repo clean. The machine needs rules, not gossip.

## Core rule

Excel Web repair validation and billing correctness are separate gates.

A workbook can open cleanly in Excel for Web while still being wrong because resolved review targets were excluded, stale project assignments were carried forward, or a summary was regenerated from the wrong intermediate artifact.

Every billing workbook should pass two checks:

1. **Web-safe package check**: ZIP/XML/package structure opens cleanly in Excel for Web.
2. **Truth-pass business check**: totals match the newest roster log after all confirmed corrections and resolved review items have been applied.

Do not ship until both are green.

## Roster-to-billing pipeline

Use this flow for admin billing outputs:

```text
Roster Log
  -> normalize live punches
  -> apply assignment overrides
  -> classify review status
  -> compute paid hours and project buckets
  -> generate admin summary workbook
  -> web-safe package validation
  -> truth-pass reconciliation against roster log
```

Never compute the final billing summary from a previous billing summary workbook. That is how stale flags and wrong totals survive.

## Review item states

Review items need explicit states. A flagged item is not always an excluded item.

Recommended states:

| State | Meaning | Include in totals? |
| --- | --- | --- |
| `REVIEW_OPEN` | Needs source correction or manager confirmation | No, unless policy says provisional totals are allowed |
| `RESOLVED_CONFIRMED` | The target was reviewed and confirmed | Yes |
| `RESOLVED_CORRECTED` | The roster log was corrected upstream | Yes |
| `EXCLUDED_NON_BILLABLE` | Non-PTO, non-work, or otherwise non-billable marker | No |
| `ASSIGNMENT_ONLY_REVIEW` | Hours are valid, project bucket needs confirmation | Include in staff total; isolate from project bucket until resolved |

Do not keep a resolved item in a scary review bucket. That wastes time and causes bad downstream decisions.

## Where corrections belong

Corrections belong upstream in the roster log, not in the final billing summary.

Preferred correction targets:

| Correction type | Correct in source | Notes |
| --- | --- | --- |
| Missing or wrong clock-out | `Live - <Month Year>` | Use actual Excel datetime or standard AM/PM display |
| Overnight clock-out | `Live - <Month Year>` | Store as next calendar date, then format as time |
| Project allocation change | `Assignments - <Month Year>` | Add explicit override row with staff, date, project, note |
| Non-billable day marker | `Live - <Month Year>` | Use clear markers like `NON-PTO`, then exclude by rule |
| Confirmed reviewed item | Review-state metadata or helper tab | Mark resolved so it is counted correctly |

The downstream summary should be disposable. The roster log should tell the truth.

## Time handling rules

Admin-facing outputs should use standard AM/PM time unless the requester explicitly wants 24-hour time.

Recommended display format:

```text
h:mm AM/PM
```

Storage rules:

1. Store valid Excel dates/times, not text, whenever possible.
2. If a shift crosses midnight, store the out-time as the next calendar date.
3. If out-time is earlier than in-time and no next-date marker exists, mark `REVIEW_OPEN`.
4. Exact midnight should be represented as the next day at `12:00 AM` when it is a true shift end.
5. Long shifts are not automatically errors. They are review targets until confirmed, then they become billable totals.

## Assignment override rules

Assignment overrides should beat default project mappings.

Precedence:

1. Explicit date-level assignment override
2. Confirmed manager/staff correction entered into the roster log
3. Default staff assignment for the period
4. Unassigned or project assignment review bucket

Important split-day rule:

If a staff member supported different workstreams on different dates in the same week, do not flatten them into one project bucket. Date-level overrides must survive into the summary.

## Hours totals rules

The generator should produce these reconciliation views:

1. Staff total hours
2. Project bucket total hours
3. Daily detail
4. Review/correction ledger
5. Excluded non-billable ledger

Required invariant:

```text
sum(project bucket hours) + unresolved assignment-review hours + excluded non-billable hours = normalized roster hours before exclusions
```

A second invariant should check final billable totals:

```text
sum(project bucket hours) + unresolved assignment-review hours = paid/billable hours after exclusions
```

If those do not reconcile, stop the build.

## Presentation requirements learned from the live cycle

For manager/admin review workbooks:

1. Use larger, readable body fonts.
2. Use prominent headers.
3. Mark review items clearly, but do not keep resolved items flagged as unresolved.
4. Place charts in a compact dashboard region.
5. Size charts so they are readable without dragging or zooming.
6. Keep dashboard totals near the top left.
7. Put review/correction tables below the main summary, not buried on a hidden tab.
8. Use standard AM/PM time in admin-facing views.
9. Avoid making users infer whether a correction is hours-related or assignment-only. Say it.

## Chart and dashboard rules for Excel Web

Charts should be generated from stable in-workbook ranges only.

Avoid:

1. External links
2. Charts pointing at copied/pasted ranges from another workbook
3. Dynamic named ranges unless Graph/browser probe proves they survive
4. Hidden helper structures that become detached after tab copy

Prefer:

1. Static summary tables for chart sources
2. Values-first dashboard outputs
3. Simple bar/pie charts where Excel Web is least likely to rewrite the package
4. A visible chart source range on the same sheet or a clearly named helper sheet

## Web-safe generation guardrails

Before shipping any generated workbook:

1. Confirm the `.xlsx` is a valid ZIP.
2. Scan all XML and rels parts for stop-ship tokens.
3. Scan visible cells for Excel error tokens such as `#REF!`, `#VALUE!`, `#DIV/0!`, `#NAME?`, and `#N/A`.
4. Confirm workbook relationships point to existing parts.
5. Confirm chart and drawing relationships point to existing parts.
6. Confirm no stale repair artifacts or broken external workbook references remain.
7. Open with Graph probe or browser probe when available.
8. Run truth-pass totals from the roster log after the package passes.

Web-safe does not mean correct. Correct does not mean Web-safe. The tool must prove both.

## Suggested automation hook

Future CLI/API target:

```text
python -m triage.billing_roster_pipeline \
  --roster "Candidates/INTERNAL_May_Billing_Active_Roster_Log.xlsx" \
  --month 2026-05 \
  --output "Outputs/billing/May_2026_Admin_Billing_Summary_WEBSAFE.xlsx" \
  --admin-time-format ampm \
  --truth-pass strict \
  --emit-corrections-ledger
```

Recommended emitted artifacts:

| Artifact | Purpose |
| --- | --- |
| `*_WEBSAFE.xlsx` | Admin-facing workbook |
| `*_truth_pass.json` | Totals, invariants, unresolved review states |
| `*_corrections_needed.xlsx` | Exact upstream roster cells/override rows to fix |
| `*_build_notes.md` | Human-readable summary of what changed |

## Implementation checklist

- [ ] Treat resolved review items as counted totals.
- [ ] Keep unresolved assignment reviews separate from excluded non-billable rows.
- [ ] Generate exact roster-log correction targets by sheet, row, and column.
- [ ] Store overnight out-times with the next calendar date.
- [ ] Render admin-facing time as AM/PM.
- [ ] Recompute from the newest roster log, never from a prior summary workbook.
- [ ] Add a final truth-pass totals reconciliation JSON.
- [ ] Keep workbook styling readable: larger font, stronger headers, clean dashboard chart placement.
- [ ] Run package-level Web Excel gates after workbook generation.
- [ ] Fail the build if package validation passes but truth-pass reconciliation fails.

## Privacy rule

Do not commit real staff screenshots, payroll messages, client workbook exports, or private roster logs into this public repo.

Commit only sanitized rules, tests with synthetic names, and generated fixtures that cannot expose real staff hours or payroll details.
