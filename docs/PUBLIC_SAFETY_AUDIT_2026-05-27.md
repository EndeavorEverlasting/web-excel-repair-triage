# Public Safety Audit — 2026-05-27

## Scope

Post-convergence validation for **EndeavorEverlasting/web-excel-repair-triage** (Web Excel Triage). This audit adapts the Keen/SysAdminSuite convergence safety checklist to this repository’s actual layout, tracked content, and privacy patterns.

### Adaptations from the Keen (SysAdminSuite) plan

| Keen assumption | This repo |
| --- | --- |
| `AGENTS.md` + deployment-audit bash harness | No root `AGENTS.md`; no `deployment-audit/` or `tests/bash/` tree |
| Hospital/site name grep (WNH, Northwell, …) | Billing/roster pipeline uses vendor and project naming in `attached_assets/` and tests — different sensitivity model |
| PR #39/#40 convergence ledger | Not applicable; sprint was billing/roster/admin-context on this origin |
| `python -m triage.compat_catalog --check` | Referenced in Cursor rules only; **module not present** on `origin/main` at `470486a` |
| Forensics corpus under version control | `Web Excel Compatibility Rules and References/` exists locally but is **not git-tracked** on `main` |

Audit baseline: `origin/main` at `470486a`. No runtime or triage code changes on this branch.

## Commands Run

Executed from repo root against **tracked content on `origin/main`** (excluding this PR’s audit docs):

```bash
git fetch origin
git grep -n "C:\\\\Users\\|C:/Users" origin/main -- .
git grep -n "Cheex\\|rperez26" origin/main -- .
git grep -nE "WNH|WMH|WBS|LIJ|NSUH|Northwell|Marcus|Bayshore|Glen Cove|CCMC|Agilant|Neurons|PO1427182|PO176759" origin/main -- .
git grep -nE "eyJ[A-Za-z0-9_-]{10,}\\." origin/main -- .
git grep -nE "([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}" origin/main -- .
git ls-tree -r --name-only origin/main | grep -Ei '\\.(xlsx|xlsm|docx|zip|xml|csv|html|ps1)$'
git check-ignore -v scripts/online_env.local.ps1 || true
git status --short scripts/online_env.local.ps1
```

Interpretation rules (Keen-aligned): README placeholders (`<You>`, `<path/to/…>`, `example.org`, SAMPLE/LAB fixtures) are acceptable; real operator paths, tenant URLs, PO numbers, and live billing/roster binaries in the public tree are flagged.

## Findings

| Check | Result | Notes |
| --- | --- | --- |
| Absolute `C:\Users\` / `C:/Users` in tracked text | **Partial** | README uses generic `<You>` placeholders (OK). One tracked recovery-log XML fragment embeds a **real local username and Downloads path** (see Exceptions). |
| Personal identifiers (`Cheex`, mailbox tokens) | **Fail** | Match in tracked `Deprecated/xml_fragments/error218920_01.xml`. Untracked local env script on disk also contains personal/tenant identifiers (not committed). |
| Hospital / vendor / PO / project name patterns | **Fail** | Matches in tracked `attached_assets/` filenames, billing tests/generator code, and deprecated JSON literals. |
| JWT / bearer token literals | **Pass** | No live JWTs in tracked files; README documents `GRAPH_TOKEN` placeholder pattern only. |
| MAC-like `aa:bb:cc:dd:ee:ff` patterns | **Pass** | No matches. |
| Tracked binary/data artifacts (`git ls-tree`) | **Fail** | 16 files under `attached_assets/` (4× `.xlsx`, 10× `.docx`, 1× `.zip`) plus 1 recovery XML under `Deprecated/xml_fragments/`. No tracked `.html`/`.csv` on `main`. |
| `scripts/online_env.local.ps1` git hygiene | **Review** | File is **untracked** (good) but **not listed in `.gitignore`** despite header comment claiming it is gitignored. |
| Forensics corpus (`Web Excel Compatibility Rules and References/`) | **Pass (untracked)** | Local-only in this clone; not published via git on `main`. |

## Exceptions

| Item | Disposition |
| --- | --- |
| `README.md` — `C:\Users\<You>\Downloads\…` and `%TEMP%\error*.xml` examples | **Accept** — generic placeholders. |
| `app.py` — Chrome user-data dir placeholder | **Accept** — generic `<you>` placeholder. |
| `refactor_spec.json` — fictional string “A Secret Next Thing” | **Accept** — not a credential. |
| `Outputs/dv_spec_deprecated.json` — dropdown literal with personal-name + site token | **Review** — curated deprecated spec; redact in hygiene PR if retained. |
| `tests/test_billing_regression.py` — synthetic line description with site token | **Flag** — test fixture encodes real site identifier; redact to SAMPLE. |
| `attached_assets/*` (16 tracked files) | **Flag** — live billing/roster/invoice intake tied to vendor POs and project codes; replace with redacted SAMPLE corpus or move out of public git. |
| `Deprecated/xml_fragments/error218920_01.xml` | **Flag** — forensic fragment with real Windows username in `<summary>`; redact path or untrack. |
| Untracked `scripts/online_env.local.ps1` | **Flag (local only)** — contains tenant SharePoint folder URLs; must never be committed; add explicit `.gitignore` entry. |

## Required Fixes (follow-up branches — not this PR)

1. Untrack or redact `attached_assets/` operational workbooks, invoices, and zip bundle; substitute SAMPLE fixtures if tests require them.
2. Redact personal path in `Deprecated/xml_fragments/error218920_01.xml` and site/vendor tokens in billing test strings.
3. Add `scripts/online_env.local.ps1` (or `scripts/*.local.ps1`) to `.gitignore` to match file header intent.
4. Optionally implement or remove stale `compat_catalog` reference in Cursor rules.

## Verdict

**Partial fail** — no JWT/MAC leaks and README placeholders are fine, but **tracked billing/roster artifacts, operator/site strings, and one real local path in a recovery fragment** remain public-safety concerns for a fully open repository.
