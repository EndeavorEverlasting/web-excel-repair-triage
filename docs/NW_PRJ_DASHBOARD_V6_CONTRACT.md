# NW PRJ Tech Roster Dashboard v6 — Web Excel Contract

## Purpose

Formalize the proven v6.5 / v6.6 dashboard workflow so generation is repeatable, auditable, and safe for Excel for Web. This contract supersedes tribal spreadsheet fixes.

## Carryover thesis

```text
Generate fewer flags, not more.
Respect manual resolution.
Treat gray as quiet.
Make Column A control visual state.
Target the manual admin scratch copy first.
Never trust Excel Web compatibility until the package passes structural checks.
Never let weak roster evidence downgrade confirmed admin hours.
```

## Input hierarchy (authority order)

1. **Manual admin scratch / control copy** — checkpoint surface; hours and edits here win for admin truth until leadership promotes official admin.
2. **Official admin workbook** — leadership-facing hours/control artifact; not project-assignment authority.
3. **Latest roster log** — punch timing and hours evidence.
4. **Prior dashboard workbook** — manual review status, notes, and resolved rows.

The generator MUST accept, at minimum:

- Latest dashboard workbook
- Latest roster log
- Latest manual admin scratch/control copy
- Optional official admin workbook

## Output naming

```text
NW_PRJ_Tech_Roster_Dashboard_v6_x_<descriptor>_WEBSAFE.xlsx
```

If Excel for Web repairs the file or the filename contains `repaired_` / `Deprecated_repaired_`, the artifact is **failed**. Do not bless it or continue without labeling the source as repaired.

## Required sheet structure

| Sheet | Role |
| --- | --- |
| `Start Here` | Operator instructions |
| `Dashboard_Tool_v6_x` | Summary and controls |
| `Active_Admin_Targets` | Actionable admin edit queue |
| `Partial_Hours_Active` | Partial-hour review (amber) |
| `Review_Guardrails` | Rich Guard and policy rows |
| `Quiet_Queues` | Low-noise watch list |
| `Resolved_Archive` | Done / skipped / gray demoted rows |
| `Tech_Summary` | Per-tech rollup |
| `CF_Dictionary` | Human-readable CF rule catalog (**required**) |
| `Definitions_Current` | Field definitions |
| `Visual_System_v6_x` | Palette and tab-color matrix |
| `Dropdown_Values` | Validated lists |
| `Repo_Automation_Notes` | Generator version and inputs used |

## Required active row fields

Every actionable row MUST include:

`Review Status`, `Work Queue Status`, `Target Type`, `Action Needed`, `Target Workbook`, `Edit Sheet`, `Edit Row`, `Edit In Cell`, `Proposed In`, `Edit Out Cell`, `Proposed Out`, `Total Cell`, `Expected Total`, `Tech`, `Date`, `Team Scope`, `Current Admin Value`, `Roster Latest In`, `Roster Latest Out`, `Roster Latest Hours`, `Roster Check`, `Roster Check Notes`, `Reason Code`, `Confidence`, `Submission Blocker`, `Manual Note / Resolution Note`

## Column A override doctrine

**Column A (`Review Status`) wins before all other conditional formatting.**

| Review Status | Visual |
| --- | --- |
| `Done`, `Confirmed Valid`, `Addressed`, `Resolved` | Green |
| `Skipped/Gray`, `Gray/Skip` | Gray |
| Unresolved | May inherit queue colors (red, amber, purple, blue) |

Forbidden CF patterns:

- `=ISNUMBER(SEARCH("AMBER",RC2))` — queue string sniffing
- `=RC1="Done"` — R1C1 leakage; not team-readable

## CF priority order

1. Column A done/resolved → green
2. Column A skipped/gray → gray
3. Submission blocker / admin edit → red
4. Partial / review → amber
5. Rich Guard → purple
6. Roster-later → blue
7. Quiet / archive → muted gray/green

## Team scope

`Team Scope` MUST be one of:

- `Cybernet/Neuron Active`
- `Tracked Only`
- `Out of Scope`

Admin `Project Team` tab is **not** project-assignment authority. Expectations come from roster defaults, assignments, worked-project tabs, explicit notes, and approved overrides.

## Gray archive doctrine

Gray means dismissed / false flag / not applicable / skip — **not** unresolved. Gray rows MUST be demoted to `Resolved_Archive` by default. They may return to active queues only when new roster or admin scratch evidence proves a real submission issue.

## Rich Guard

```text
Preserve admin full/long-day hours unless explicit short-day evidence exists.
```

Weak roster evidence may trigger review; it MUST NOT downgrade admin full/long-day hours in the scratch copy. Afternoon clock-outs are suspect unless an exception documents a short day.

## Partial hours

Roster/admin hours greater than 0 and less than 8 require review before leadership submission. Valid outcomes: `Confirmed Valid`, `Addressed`, `Needs Review`, `Skipped/Gray`. Partials are amber review, not automatic red errors.

## Formula edit doctrine

Techs MUST:

- Edit **In** and **Out** cells only
- **Not** overwrite **Total** cell formulas
- Check **Expected Total**

The generator separates: `Edit In Cell`, `Proposed In`, `Edit Out Cell`, `Proposed Out`, `Total Cell`, `Expected Total`.

## Manual status carry-forward

Manual status and notes are **evidence**. They MUST be carried forward from the prior dashboard unless newer contradictory roster or admin scratch evidence exists.

## Layout fingerprint

Cell targets MUST be resolved from header / date / tech mapping, not hardcoded forever. If the layout fingerprint changes, generation MUST fail with a clear warning.

## Related documents

- [CF_DICTIONARY_AND_VISUAL_SYSTEM.md](CF_DICTIONARY_AND_VISUAL_SYSTEM.md)
- [WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md](WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md)
- [NW_PRJ_RECONCILIATION_INSIGHTS.md](NW_PRJ_RECONCILIATION_INSIGHTS.md)
- [ARTIFACT_GENERATION_LEDGER.md](ARTIFACT_GENERATION_LEDGER.md)
- [billing_bridge/WEB_EXCEL_VALIDATION.md](billing_bridge/WEB_EXCEL_VALIDATION.md)
