# Harness Current State

## Status

The repository has a tracked operational harness for agent entry, Prompt Kit delivery, safe technician acquisition, validation, and handoff.

## Working surfaces

- `AGENTS.md` is the canonical governance contract and is enforced by focused CI.
- `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md`, and `SKILLS.md` provide the human-readable harness spine.
- `harness/manifest.v1.json` provides the machine-readable component inventory and validation order.
- The Prompt Kit website is tracked at `web/prompt-kit/index.html` and must match the combined-registry builder exactly.
- `Run-PromptKitGenerator.cmd` opens the registered generator GUI.
- `Build-PromptKitWebsite.cmd` performs the safe one-click website build.
- `Acquire-Latest-PromptKit.cmd` provides the technician clone/update/open entry point.
- `scripts/Acquire-LatestPromptKit.ps1` implements destination selection, clean fast-forward update, validation, and post-success launch.
- `scripts/validate_harness.py` and `tests/test_harness_contract.py` enforce component, registry, skill, hook, and launcher contracts.
- `.githooks/pre-commit` provides an optional focused local gate.

## Technician acquisition behavior

The acquisition GUI:

1. clones canonical `main` when the selected destination is absent;
2. verifies canonical origin for existing repositories;
3. refuses dirty or non-`main` worktrees;
4. fetches `origin/main`;
5. refuses local-only commits or divergence;
6. fast-forwards with `git merge --ff-only` only;
7. verifies required website, generator, manifest, and builder files;
8. runs the exact combined-registry website check;
9. opens the selected website or generator GUI only after success.

It does not reset, clean, delete branches, force-push, stash, or automate credentials.

## Known gaps

- Native Windows visual and mouse acceptance remains a field proof. Linux CI can validate source contracts but cannot prove Windows Forms rendering or local desktop policy.
- The technician machine still needs Git for Windows, Windows PowerShell, Python 3, network access, and repository authorization.
- `README.md` documents many historical and current workbook engines. Agents must verify focused files and tests before relying on an older README section.
- The optional pre-commit hook is tracked but is not installed automatically; use `git config core.hooksPath .githooks` per worktree when desired.

## Validation order

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python -m triage.gitignore_hygiene
git diff --check
```

Run broader repository tests after these focused gates.

## Proof ceiling

Current repository proof covers tracked component presence, manifest/schema integrity, required skill sections, launcher command boundaries, protected-path rules, generated-site parity, and CI integration. It does not prove a particular technician's credentials, network, Git installation, Python installation, Windows GUI rendering, or operator acceptance.
