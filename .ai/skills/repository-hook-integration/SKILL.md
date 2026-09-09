# Repository Hook Integration

## Trigger

Use when a repository needs its tracked pre-commit/pre-push hooks activated, verified, repaired, or reconciled with an existing local Git hook authority. Use current provider-specific hook documentation as donor evidence when Claude, Codex, DeepSeek Harness, Husky, Lefthook, or another adapter is involved; do not assume dialect compatibility.

## Required inputs

- Current repository root, branch/worktree state, and `AGENTS.md`.
- Existing `.githooks/`, `scripts/install_local_hooks.py`, and local/default Git hook configuration.
- Requested hook purpose and any existing provider-specific hook owner.
- Owned/forbidden scope and proof requirement.

## Outputs

- Preserved or activated canonical repository hook authority.
- Exact activation/check command and result.
- Explicit coexistence blocker when another hook path or linked worktree makes mutation unsafe.
- Provider-adapter disposition: reuse, bridge, defer, or reject; never silent replacement.

## Procedure

1. Refresh repository truth and inspect tracked hook ownership before installing anything.
2. Prefer the repository's existing `.githooks` + `scripts/install_local_hooks.py` owner. Do not add Husky/Lefthook/provider hooks merely because upstream examples use them.
3. Inspect `core.hooksPath`, default Git hooks, linked worktrees, and tracked executable modes. Preserve competing or ambiguous hook setups.
4. If the existing owner can satisfy the request, activate it with `python scripts/install_local_hooks.py`; use `--check` for read-only verification.
5. Add a provider-specific adapter only when the request requires semantics the canonical Git hooks cannot express. Keep that adapter behind the same capability boundary and prove its own activation independently.
6. Run focused activation regressions, harness validation, and patch hygiene before integration.

## Guardrails

- Never change global Git hook configuration.
- Never overwrite a different local `core.hooksPath` without explicit reviewed replacement intent.
- Never bypass existing default hooks silently.
- Refuse shared `core.hooksPath` mutation when linked worktrees make the effect ambiguous.
- A Claude/Codex/DeepSeek hook example is donor procedure, not repository authority.
- Hook activation proves interception wiring, not the correctness of every command executed by the hook.

## Validation

```bash
python -m unittest tests.test_repository_hook_integration tests.test_local_hook_activation -v
python scripts/install_local_hooks.py --check
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
git diff --check
```

The `--check` command requires a real single-worktree checkout whose local `core.hooksPath` has already been activated; CI may instead use the existing local-hook activation workflow to install and verify in its disposable checkout.

## Proof ceiling

Repository/static tests plus an executed installer/check prove tracked Git hook presence and local `core.hooksPath` activation in the observed checkout. They do not prove Claude/Codex/DeepSeek provider hook behavior, every developer workstation, or future hook command correctness unless those surfaces are separately exercised.
