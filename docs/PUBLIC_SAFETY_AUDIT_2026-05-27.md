# Public Safety Audit — 2026-05-27

## Scope

Post-convergence validation for the **Web Excel Triage** workspace (Web Excel Triage git repository). This audit records grep and inventory commands from the SysAdminSuite convergence validation plan, executed against the actual repository remotes and tracked content. Runtime code was not modified in this pass.

## Commands Run

```bash
git grep -n "C:\\\\Users\\|C:/Users" -- . || true
git grep -n "local-reference" -- AGENTS.md docs || true
git grep -n "PR #40.*does not exist" -- docs || true
git grep -nE "WNH|WMH|WBS|LIJ|NSUH|Northwell|Marcus|Bayshore|Glen Cove|CCMC" -- . || true
git grep -nE "([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}" -- . || true
find . \( -iname "*.xlsx" -o -iname "*.xlsm" -o -iname "*.html" -o -iname "*.xml" -o -iname "*.csv" \) -print
```

`find` was executed via **Git Bash** (`C:\Program Files\Git\bin\bash.exe`). `git grep` was executed from the repo root on branch `docs/post-convergence-validation-2026-05-27` at `470486a`.

## Findings

| Check | Result | Notes |
| --- | --- | --- |
| Absolute `C:\Users\` / `C:/Users` paths in tracked text | **Pass** | No matches (exit code 1). |
| `local-reference` in `AGENTS.md` or `docs/` | **Pass** | No matches. |
| Stale `PR #40.*does not exist` doc string | **Pass** | No matches under `docs/`. |
| Hospital / site / operator name patterns (regex set) | **Fail** | Matches in tracked content (see Exceptions). |
| MAC-like `aa:bb:cc:dd:ee:ff` patterns | **Pass** | No matches (exit code 1). |
| Workspace `find` for `.xlsx/.xlsm/.html/.xml/.csv` | **Fail** | Tracked billing/roster workbooks and fragment XML present (see Exceptions). |

## Exceptions

Interpretation per plan: placeholders and lab/sample naming are acceptable; real operator artifacts in the public tree are not.

| Item | Disposition |
| --- | --- |
| `Outputs/dv_spec_deprecated.json` — dropdown literal containing a personal-name token and "HQ" | **Review** — deprecated spec fixture; treat as non-production but rename/redact in a dedicated hygiene PR if retained. |
| `tests/test_billing_regression.py` — invoice line description containing a hospital site token | **Flag** — synthetic test string still encodes a real site identifier; redact in a test-data cleanup branch. |
| `attached_assets/*.xlsx` (four files, git-tracked) | **Flag** — filenames and content class indicate live billing/roster intake artifacts tied to a named health network and project codes; not appropriate for long-term public tracking. |
| `Deprecated/xml_fragments/error218920_01.xml` | **Accept with caution** — technical fragment without site identifiers in path; keep out of user-facing docs. |
| Untracked `scripts/online_env.local.ps1` on disk after main reset | **Out of scope for grep** — secrets/local env; must never be committed (per `AGENTS.md`). |

`find` on disk also reported the same paths under `./attached_assets/` and `./Deprecated/xml_fragments/` (no additional HTML/CSV beyond git-tracked set in this clone).

## Required Fixes

1. Remove or untrack billing/roster `.xlsx` files under `attached_assets/` (replace with redacted SAMPLE fixtures if needed for demos).
2. Redact hospital/site tokens from `tests/test_billing_regression.py` and review deprecated JSON literals for operator-identifying strings.
3. Confirm `.gitignore` covers local env scripts and any future generated billing run outputs.

**No runtime or triage code changes were made on this branch** (documentation-only PR).

## Verdict

**Partial fail** — no local path or MAC leaks; documentation grep targets clean; **tracked workbook filenames and test/site strings remain a public-safety concern** and should be handled in follow-up branches, not in this audit PR.
