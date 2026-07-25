# Harness Current State

## Status

The repository has a tracked operational harness for safe entry, routing, prompt passage, canary visibility, prompt efficiency evaluation, LLM-as-judge evidence, validation, artifacts, technician acquisition, and handoff.

## Working surfaces

- Root maps, workflow, artifact, skill, capability, and trigger indexes.
- Root and prompt-registry manifests.
- Compact per-prompt execution profiles and ordered passage audit.
- Identity-free `OBJECTIVE` / `REPOS` canary contract.
- Hybrid prompt-efficiency evaluator with code-based, LLM-judge, human, and user lanes.
- Prompt-registry and model-response judge packet support.
- Strict validation of judge schema, coverage, dimensions, scores, verdicts, and duplicate judge IDs.
- Prompt-language, interaction, hygiene, and exact-site parity gates.
- Pre-push and CI artifact generation.

## Technician acquisition behavior

The acquisition surface clones canonical `main` when absent or clean-fast-forwards an existing clean canonical `main`. It refuses divergence, local-only work, wrong origin, destructive reset/clean, embedded credentials, and opening before validation.

## Prompt-language audit behavior

Audit mode covers every canonical and effective prompt, requires equal prompt/disposition counts, and records stable findings. Strict mode is the bounded prompt-repair completion gate.

## Prompt efficiency and judge behavior

Code checks run first and measure prompt/response size, approximate tokens, repeated lines, oversized lines, weak-model structure, required metadata, response emptiness, and response canaries. Judge packets are ordered one case at a time. Strict efficiency requires zero code warnings, complete independent judge coverage, passing verdicts, passing average score, all dimensions above their floor, and stronger floors for token economy and weak-model resilience.

## Known gaps

- Canonical prompt optimization remains a separate prompt-product lane; this harness reports debt but does not mutate prompts.
- Current canary inclusion may remain incomplete until the product lane lands.
- CI cannot claim LLM-judge success without supplied validated judge results; it emits packets and a non-strict report only.
- Judge results remain model opinion and may require human dispute resolution.
- Real weak-model completion and operator speed require model-run and user evidence.
- Browser, clipboard, focus, Windows GUI, credentials, network, protected runtime, and production acceptance remain field proof.

## Validation order

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_registry_harness -v
python -m unittest tests.test_prompt_efficiency_eval -v
python scripts\audit_prompt_registry_harness.py --output Outputs\prompt-registry-harness-audit.json --summary
python scripts\evaluate_prompt_efficiency.py --output Outputs\prompt-efficiency-eval.json --emit-judge-packets Outputs\prompt-efficiency-judge-packets.json --summary
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts\validate_prompt_kit_interactions.py --output Outputs\prompt-kit-interaction-audit.json --summary
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

## Proof ceiling

The harness proves tracked contracts, deterministic routing, complete static registry/profile coverage, measurable prompt/response findings, safe output routing, and validated judge-result structure when results are supplied. It does not by itself prove universal model adherence, human truth, real-user speed, protected runtime behavior, browser acceptance, or production success.
