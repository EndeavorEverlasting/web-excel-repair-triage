# Repository-Native Update Harness — Current State

## Working
- Canary surface `canary-constants` owned under `harness/repo-native-update/generated/canary_constants.py`.
- Canonical CLI: `scripts/run_repo_native_update.py` with atomic write, path guards, receipts, and `--check`.
- Static validator and focused unittest cover malformed input, undeclared output, forbidden prefixes, drift, and idempotency.
- Trigger is local CLI only (Actions-minutes workaround); no new GitHub Actions workflow.

## Broken
None known in the local harness contract.

## Missing
- Phase 2 broader surfaces (deferred).
- Phase 3 provider delegate that calls the same CLI (deferred; Actions minutes currently exhausted).

## Proof ceiling
Local deterministic generation plus static/unit proof. No Actions/provider runtime claim.

## Operator next action
```bash
python scripts/run_repo_native_update.py generate --surface canary-constants --check
```
