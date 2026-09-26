# Skill: Prompt Semantic Coverage

**Capability ID**: `prompt-semantic-coverage`
**Version**: 1.1.0
**Status**: Canonical

## Trigger

**Trigger ID**: `prompt-semantic-lifecycle-change`

Activate when:
- Canonical prompt ADD/EDIT/RETIRE operation requested
- Semantic migration touching prompt behavior
- Capability catalog, profile, or migration changes
- Validator reports semantic coverage regression
- P79 prompt lifecycle operation triggered

DO NOT activate when:
- Generated-site-only rebuild
- Documentation-only change
- Runtime observation with no canonical prompt mutation
- Unrelated registry metadata presentation changes proven semantically inert

## Required inputs

- Canonical prompt registry (`docs/prompts.json`, `registry/prompts/*.json`)
- Current accepted profiles (`harness/prompt-topology/prompt-capability-profiles.v1.json`)
- Capability catalog (`harness/prompt-topology/semantic-capability-catalog.v1.json`)
- Migration history (`harness/prompt-topology/prompt-capability-migrations.v1.json`)
- Candidate prompt/migration
- Topology/prior-art evidence

## Outputs

- Semantic diff report
- Coverage/overlap analysis
- Migration/profile disposition (ADD/ADOPT_PROFILE/STRENGTHEN/NO_CAPABILITY_CHANGE/INTENTIONAL_CHANGE/TRANSFER/RETIRE)
- PSC rule PASS/FAIL receipt
- Exact proof ceiling

## Procedure

### ADD Operation

Before allocating new prompt ID:
1. Require `semantic_profile.direct_assignments` using catalog `capability_id`, `presence`, `ownership`, `capability_relation`, and `delivery_source`.
2. PRIMARY/REQUIRED assignments carry `evidence_refs` plus `rationale`.
3. Check internal topology/profile overlap; an overlapping candidate supplies reviewed `distinct_residual.summary`, `evidence_refs`, and `reviewed_against` prompt IDs.
4. Verify distinct residual proof (PSC008) before identity allocation.
5. Run `scripts/prompt_registry_ops.py add`; successful ADD persists the canonical record, ACCEPTED profile, capability migration, Prompt Quality History migration, and generated site as one rollback-safe lifecycle operation.

### ADOPT PROFILE Operation

Use this only for an existing canonical prompt that predates semantic-profile coverage or lives in a later extension registry and has no semantic profile history yet.

1. Inspect the exact canonical prompt plus current catalog/coverage.
2. Build a reviewed semantic profile from the prompt's existing behavior; do not infer a new prompt body or allocate a new identity.
3. Run `python3 scripts/prompt_registry_ops.py adopt-profile --prompt-id P## --input profile.json --evidence-ref <proof> --rationale "reason"`.
4. The helper must refuse any existing ACCEPTED/PROVISIONAL/RETIRED history for that prompt, bind the exact canonical record hash, validate PSC002/003/011/016, update the accepted-profile count, rebuild parity, and roll back atomically on failure.
5. Profile adoption does not change the canonical prompt body and therefore must not fabricate a Prompt Quality History migration. Subsequent body mutation uses the normal EDIT/STRENGTHEN lifecycle against the newly accepted immutable prior.

### EDIT / STRENGTHEN Operation

Before changing prompt text:
1. Load the target ACCEPTED profile as immutable prior; if none exists, route to this skill owner instead of inventing one in place.
2. Put only changed canonical semantic fields in a JSON patch.
3. Run `python3 scripts/prompt_registry_ops.py edit --prompt-id P## --input patch.json --disposition <NO_CAPABILITY_CHANGE|STRENGTHEN|INTENTIONAL_CHANGE|TRANSFER> --evidence-ref <proof> --rationale "<reason>"`.
4. NO_CAPABILITY_CHANGE preserves assignments; other dispositions require the proposed `semantic_profile`.
5. Reject unexplained downgrade (PSC004/PSC005), require linked capability/source-history migrations, rebuild the site, and fail closed on any partial transition.

### RETIRE Operation

Before removal:
1. Load the ACCEPTED profile and enumerate PRIMARY/REQUIRED capabilities.
2. Calculate equal-or-stronger alternate owners.
3. Bind reviewed successors with repeatable `--transfer CAPABILITY_ID=P##` arguments when needed.
4. Run `python3 scripts/prompt_registry_ops.py retire --prompt-id P## --rationale "..."`.
5. The helper must refuse coverage holes (PSC007), remove the canonical record, retain a RETIRED tombstone and linked histories, rebuild the site, and keep the retired identity reserved.

## Guardrails

### OWNED

- Profile/matrix validation
- Semantic diff calculation
- Coverage hole detection
- Lifecycle bridge in `scripts/prompt_registry_ops.py`
- PSC001-PSC018 enforcement

### FORBIDDEN

- Automatic ID allocation outside P79
- Accepted-profile overwrite from generated inference
- Runtime-behavior claim from static evidence
- Raw/private transcript persistence
- PROVISIONAL profiles replacing ACCEPTED history

## Validation

### Audit
```bash
python3 scripts/validate_prompt_semantic_coverage.py
```

### Tests
```bash
python3 -m unittest tests.test_prompt_semantic_coverage tests.test_prompt_semantic_validator_1b -v
```

### P79 Integration
```bash
# ADD with canonical semantic_profile in draft.json
python3 scripts/prompt_registry_ops.py add --input draft.json --dry-run

# EDIT with explicit capability disposition/evidence
python3 scripts/prompt_registry_ops.py edit --prompt-id P07 --input patch.json --disposition NO_CAPABILITY_CHANGE --evidence-ref tests/test_prompt_semantic_coverage.py --rationale "reviewed wording strengthening" --dry-run

# RETIRE with coverage check / optional successor binding
python3 scripts/prompt_registry_ops.py retire --prompt-id P42 --rationale "reason" --dry-run
```

## Proof ceiling

**INTEGRATED**: Repository/static semantic lifecycle enforcement and accepted profile regression protection.

**SEPARATE**: Downstream runtime model behavior observation, which remains separate runtime proof.

## PSC Rules Enforced

- **PSC001**: Profile coverage complete
- **PSC002**: Profile binds canonical prompt
- **PSC003**: Known capability only
- **PSC004**: REQUIRED presence non-weakening
- **PSC005**: PRIMARY ownership non-weakening
- **PSC006**: Transfer equal or stronger
- **PSC007**: Retire no coverage hole
- **PSC008**: ADD requires distinct residual
- **PSC009**: Body change requires profile disposition
- **PSC010**: Same agent rescoring cannot reset prior
- **PSC011**: New PRIMARY/REQUIRED requires proof
- **PSC012**: Global PRIMARY crowding review
- **PSC013**: Source history complete
- **PSC014**: Lifecycle transition atomic
- **PSC015**: Source and capability migration link
- **PSC016**: Inherited source integrity
- **PSC017**: Existing prompt profile adoption
- **PSC018**: Holistic non-weakening mutation lifecycle — deliberate compression strengthens semantic density without dropping accepted behavior/ownership; all future ADD/EDIT/TRANSFER/RETIRE migrations carry a lifecycle receipt

## Related Skills

- **prompt-language-audit**: Wording/actionability/coverage audit
- **skill-evaluation**: Executable effectiveness/runtime evaluation
- **P79 prompt/topology route**: Identity/admission owner

## Implementation

**Validator**: `scripts/validate_prompt_semantic_coverage.py`
**Lifecycle Bridge**: `scripts/prompt_registry_ops.py`
**Tests**: `tests/test_prompt_semantic_coverage.py`, `tests/test_prompt_semantic_validator_1b.py`
**Catalog**: `harness/prompt-topology/semantic-capability-catalog.v1.json`
**Profiles**: `harness/prompt-topology/prompt-capability-profiles.v1.json`
**Migrations**: `harness/prompt-topology/prompt-capability-migrations.v1.json`

## Sprint Context

**Sprint 2**: P79 lifecycle convergence + required-check enforcement

This skill completes the semantic capability coverage program by wiring validated baseline + validator into every canonical prompt lifecycle mutation path and making semantic coverage a blocking required check.
