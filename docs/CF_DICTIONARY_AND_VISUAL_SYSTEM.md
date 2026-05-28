# CF Dictionary and Visual System — NW PRJ Dashboard v6

## CF_Dictionary requirement

Every generated dashboard MUST include a `CF_Dictionary` sheet. Validators fail workbooks missing this sheet.

Each row documents one conditional-format rule:

| Column | Meaning |
| --- | --- |
| Rule ID | Stable identifier (e.g. `CF_A_DONE`) |
| Priority | Integer; lower runs first |
| Applies To | Sheet and column range |
| Condition (plain English) | Team-readable trigger |
| Formula (audit) | Stored formula for diff/review |
| Fill / Font | Visual outcome |
| Overrides | What this rule must beat or yield to |

## Column A override (non-negotiable)

Rules that color by `Work Queue Status` or roster strings MUST NOT run before Column A review rules. Done rows that stay yellow because an AMBER queue rule fired first are a **contract violation**.

## Tab color taxonomy

Configured in `configs/cf_palette_v1.json`. Roles:

| Tab role | Color intent | Example sheets |
| --- | --- | --- |
| `operator_entry` | Blue — start here | `Start Here` |
| `dashboard_hub` | Green — primary tool | `Dashboard_Tool_v6_x` |
| `active_queue` | Red/orange — needs action | `Active_Admin_Targets` |
| `review_queue` | Amber — partial/review | `Partial_Hours_Active` |
| `guardrail` | Purple — policy / Rich Guard | `Review_Guardrails` |
| `quiet` | Light gray — watch only | `Quiet_Queues` |
| `archive` | Dark gray — resolved/dismissed | `Resolved_Archive` |
| `reference` | Teal — lookup | `CF_Dictionary`, `Definitions_Current`, `Dropdown_Values` |
| `automation` | Slate — repo notes | `Repo_Automation_Notes` |

## Fill palette (active rows)

| Semantic | ARGB (Excel) | Use |
| --- | --- | --- |
| `resolved_green` | `FF92D050` | Column A done family |
| `skipped_gray` | `FFBFBFBF` | Column A skipped/gray |
| `blocker_red` | `FFFF6666` | Submission blocker |
| `review_amber` | `FFFFC000` | Partial / needs review |
| `rich_guard_purple` | `FFB4A7D6` | Rich Guard |
| `roster_blue` | `FF9DC3E6` | Roster-later |
| `quiet_muted` | `FFE7E6E6` | Archive / quiet |

## Visual_System sheet

The `Visual_System_v6_x` sheet mirrors this document for operators. Generator copies tab colors from `cf_palette_v1.json` at build time.

## Anti-patterns

- R1C1 references (`RC1`, `RC2`) in CF formulas
- `SEARCH("AMBER", …)` on queue status instead of Column A
- Missing `CF_Dictionary` while CF rules exist on data sheets
