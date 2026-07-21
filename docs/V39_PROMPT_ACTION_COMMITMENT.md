# V39 Prompt Action-Commitment Contract

## Failure that established the contract

P00 was presented as **Install universal harness discipline**, but its payload only described behavior. The workbook also classified it as non-progress work, declared that no repository mutation was allowed, and directed the operator to use another prompt next.

An agent could therefore acknowledge the doctrine without installing anything and still appear compliant. That is no longer an acceptable prompt shape.

## Rule

A prompt whose name, role, expected output, or operator guidance claims that it will install, set up, build, execute, repair, configure, upgrade, deploy, merge, or release something must require the corresponding action and proof.

Action claims and mutation authority must agree. A prompt is invalid when it claims an operational result but permits an acknowledgment, explanation, rewritten prompt, plan, handoff, or preflight as its successful completion.

## P00 and P01 ownership

- **P00** installs the repository's baseline harness doctrine into the existing repo-native authority surface. It also adds or repairs a focused enforcement test or validator, commits the change, pushes the safe branch, and opens or updates a PR.
- **P01** remains the broader repo-local harness builder. It owns maps, workflows, registries, scoped skills, hooks, reports, and other harness surfaces beyond the baseline doctrine installation.

P00 must not merely recite the doctrine. P01 must not be used as an excuse to leave P00's claimed installation unperformed.

## Machine-readable authority

`configs/prompt_kit/v39_core_prompt_action_overrides.json` registers inherited prompts that require action hardening. Each registered prompt declares its execution shape, Prompt Library metadata, exact copy-safe payload, required action markers, invalid completion shapes, and commit and PR proof gates.

The V39 generator rewrites the inherited prompt tab and matching Prompt Library row. When the accepted source workbook contains them, it also repairs contradictory entries in `START_HERE`, `Prompt_Class_Legend`, `Prompt_Sequence`, and `Import_Checklist`.

## Validation

`tests/test_prompt_kit_v39_action_commitment.py` proves that P00 begins with an imperative installation command, requires tracked-file mutation and Git/PR proof, rejects non-action completion shapes, is progress-bearing in Prompt Library, and fails closed if commit evidence is removed or progress is downgraded.

The generated manifest records the hardened prompt IDs and states that acknowledgment-only completion is forbidden.

## Proof ceiling

Repository tests prove prompt text, workbook metadata, links, package structure, and fail-closed generation. They do not prove that an external agent successfully installed doctrine in another repository. That claim requires the target repository's changed files, passing validator output, commit SHA, branch state, push confirmation, and PR mutation evidence.
