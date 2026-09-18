# LANE 04 — Close #543 Effective-P07 Local-Proof Continuity

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**PR / branch:** #543 / `fix/local-proof-continuity-20260917`  
**Wave:** A  
**Hard dependencies:** current main only  
**Safe parallel work:** Lanes 01, 02, 03, 05  
**Convergence owner:** this lane; merge #543 when green

## Mission

Finish the effective-P07 compiler/local-action delta, make generated Prompt Kit bytes current through the canonical builder, and integrate #543 before later #542/#537 convergence when safe.

## Read first

- `AGENTS.md`
- #543 current checks/reviews
- `harness/contracts/prompt-language-compiler-policy.v1.json`
- `harness/prompt-compilation/semantics/P07.json`
- `harness/repository-actions.v1.json`
- `tests/test_prompt_compilation.py`
- `scripts/build_prompt_kit_registry.py`
- `docs/HARNESS_LOCAL_FIRST_REQUIRED_CHECKS_REFERENCE_ARCHITECTURE.md`

## Known evidence

At head `a641a85e...`, Prompt Quality History passed. Pages failed because generated `web/prompt-kit/index.html` was stale. Operational harness then reported order/navigation baseline drift from the same stale product state. Deterministic floor failed its generated-site negative canary. Treat this as one source/generated parity defect family until evidence proves otherwise.

## Owned scope

The four #543 source/test files; generated Prompt Kit only through the builder at the final integration candidate.

## Forbidden scope

#542 boundary/observatory files, #537 strength files, manual HTML edits, unrelated navigation product logic.

## Tasks

1. Refresh main and rebase/merge it into #543 without force; if a source-owner collision appears, diagnose before resolving.
2. Run focused P07 compilation tests before generation.
3. Regenerate `web/prompt-kit/index.html` via `scripts/build_prompt_kit_registry.py`.
4. Run `prompt-kit-proof` against refreshed `origin/main`.
5. Re-run order/navigation and deterministic generated-site gates.
6. Inspect exact-head reviews/checks.
7. Mark PR ready only after local proof and generated parity are green.
8. Merge #543 if all merge gates permit; verify new main contains the exact source semantics and generated artifact.

## Validation order

```bash
python -m unittest tests.test_prompt_compilation -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/run_repository_action.py --action prompt-kit-proof --base-ref origin/main --report Outputs/repository-actions/prompt-kit-proof.json
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
git diff --check
git diff --cached --check
```

Then run the repository-owned deterministic/local-required-check action if registered and available.

## Safety

No direct HTML edits. No hosted-CI-only substitution for local repository action when local proof is available. Do not preserve a stale generated artifact to avoid a merge conflict.

## Commit / push / merge contract

Use the existing #543 branch. Commit regenerated output only with its causal source/test repair. Push normally. Remove draft status and merge only after exact-head proof.

## Proof level / ceiling

Target: VALIDATED + INTEGRATED on main.  
Ceiling: repository/local/provider integration; not downstream model behavior or operator acceptance.

## Exact final response

Report pre/post main SHA, #543 exact head, source files, generated artifact hash/parity, local action receipt path, checks, merge SHA, containment/content proof.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git switch fix/local-proof-continuity-20260917 && git merge --no-edit origin/main
```
