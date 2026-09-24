# Repository Glossary

Vocabulary and navigation only. This file does not specify product behavior. When an entry names executable owners, those owners and their validators/tests are authoritative.

| Term | Short meaning | Authoritative owner / pointer | Status / alias |
| --- | --- | --- | --- |
| Governance | Repository-wide agent operating rules and precedence. | `AGENTS.md` | Read first. |
| Context router | Progressive-disclosure route from governance to one task domain. | `harness/CONTEXT.md` | Navigation only. |
| Prompt Operations | Binding domain contract for Prompt Kit registry changes, audits, parity, and orchestration. | `harness/specs/prompt-operations.md` | Prompt Kit write-policy owner. |
| Prompt registry | Canonical prompt records consumed by the effective registry build. | `docs/prompts.json`, `registry/prompts/*.json`, `scripts/prompt_registry_ops.py` | Generated HTML is not a registry owner. |
| Prompt contribution helper | Grounded path for adding a genuinely new prompt identity. | `scripts/prompt_registry_ops.py` and its focused tests | Use after proving ADD rather than STRENGTHEN. |
| Canonical Prompt Kit website | Tracked generated website produced from registered prompt sources. | `web/prompt-kit/index.html`; builder `scripts/build_prompt_kit_registry.py` | Generated artifact; rebuild, do not hand-author as source truth. |
| Release identity | Contract that binds the canonical website artifact to its validation/reporting seam. | `harness/contracts/prompt-kit-release-identity.v1.json`, `scripts/validate_prompt_kit_release_identity.py` | Repository proof, not deployment proof. |
| Prompt Kit interaction contract | Machine contract for user-visible Prompt Kit interaction invariants. | `harness/contracts/prompt-kit-interactions.v1.json`, `scripts/validate_prompt_kit_interactions.py` | Runtime observation may still be required. |
| Prompt profile | User-facing profile/tab projection over canonical prompts. | `docs/prompt-kit-profiles.js`, `tests/test_prompt_kit_profiles.py` | `docs/PROMPT_KIT_FIVE_TAB_PROFILES.md` is supporting design prose while its tests/active work depend on it. |
| Favorite | Browser preference selecting a prompt for Favorite-oriented surfaces and shortcuts. | Current Prompt Kit runtime plus focused Favorite/hotkey tests and interaction contracts | Do not infer behavior from old release notes. |
| Portability | Stable local Prompt Kit serving and portable preference behavior. | `harness/contracts/prompt-kit-portability.v1.json`, `scripts/serve_prompt_kit_portable.py`, `scripts/validate_prompt_kit_portability.py` | `docs/PROMPT_KIT_PORTABILITY.md` is the registered doctrine pointer. |
| Acquisition | Safe get/update/open workflow for a technician or operator. | `PROMPT_KIT_ACCESS.md`, `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`, `Acquire-Latest-PromptKit.cmd` | Operational documentation is intentionally retained. |
| Operator documentation | Human procedures for acquisition, generator use, verification, and field-proof boundaries. | `docs/README.md` and the runbooks it links | Operational input; keep concise but executable. |
| Expert insight intake | Boundary for bringing externally captured expert knowledge toward Prompt Kit review. | `docs/PROMPT_KIT_EXPERT_INSIGHT_INTAKE.md`, referenced by `harness/specs/prompt-operations.md` | External rows are evidence until publication/ownership gates are met. |
| Observed proof | Evidence produced by actually executing the required runtime event sequence. | `harness/observed-proof/`, `scripts/validate_observed_behavior_receipt.py` | Static/build/synthetic evidence does not promote itself to runtime proof. |
| Program prototype | Executable architecture experiment used to compare Prompt Kit design seams. | `docs/prompt-kit-program-prototype.js`, `tests/test_prompt_kit_program_prototype.py` | `docs/PROMPT_KIT_PROGRAM_ARCHITECTURE.md` is retained while active prototype work depends on it; it is not general runtime truth. |

For implementation details, follow the owner above rather than extending this glossary with copied rules.