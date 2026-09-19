# Skill: Prompt Semantic Coverage

**Capability ID**: `prompt-semantic-coverage`  
**Version**: 1.0.0  
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
- Migration disposition (ADD/STRENGTHEN/NO_CHANGE/TRANSFER/RETIRE)
- PSC rule PASS/FAIL receipt
- Exact proof ceiling

## Procedure

### ADD Operation

Before allocating new prompt ID:
1. Require candidate semantic profile
2. Check internal topology/profile overlap
3. Verify distinct residual proof (PSC008)
4. Pass `scripts/prompt_registry_ops.py add` with `semantic_profile` in draft

### EDIT / STRENGTHEN Operation

Before changing prompt text:
1. Load accepted profile as immutable prior
2. Compute declared capability deltas
3. Run proofs for protected PRIMARY/REQUIRED assignments
4. Reject unexplained downgrade (PSC004, PSC005)
5. Require migration when responsibility changes

### RETIRE Operation

Before removal:
1. Load accepted profile
2. Enumerate PRIMARY/REQUIRED capabilities
3. Calculate alternate owners
4. Require successor transfer for coverage that would disappear (PSC007)
5. Run `scripts/prompt_registry_ops.py retire --prompt-id P## --rationale "..."`

## Guardrails

### OWNED

- Profile/matrix validation
- Semantic diff calculation
- Coverage hole detection
- Lifecycle bridge in `scripts/prompt_registry_ops.py`
- PSC001-PSC016 enforcement

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
# ADD with semantic profile
python3 scripts/prompt_registry_ops.py add --input draft.json --dry-run

# RETIRE with coverage check
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
