# Artifact Derivation Workflow

## Pick up a task
1. Classify request language. `create`, `generate`, `build`, `produce`, `make`, `draft`, and `export` default to **create_new**.
2. Use the artifact registry and repository/provider evidence to find the closest existing artifact. Treat it as a read-only reference.
3. Record stable source identities and resolve the owning artifact engine.
4. Choose a distinct output identity under the engine's normal output surface.
5. Run the derivation preflight before opening any writer/save path.

## Validate before committing or publishing
Run `python scripts/validate_artifact_derivation_harness.py --request-text "<operator request>" --source <source-id> --output <new-output-id> --summary`, then the owning engine's tests/preflight/manifest checks, repository harness validation, artifact hygiene, and `git diff --check` as applicable.

## Failure handling
- same source/output identity: choose another output identity;
- output already exists: version/candidate the output rather than replacing it;
- protected input output (`Candidates/`, `Active/`): reject;
- ambiguous wording: default to create_new;
- explicit in-place update: require the operator to name the existing target and rerun with `--intent update_existing --explicit-update`;
- no useful source: derive from other authoritative evidence or mark the source gap; do not invent data.

## Handoff
Record operator intent, source identity/identities, output identity, owning generator, validator/preflight results, whether output pre-existed, and proof ceiling. For create_new, explicitly state that source mutation was not authorized or performed.
