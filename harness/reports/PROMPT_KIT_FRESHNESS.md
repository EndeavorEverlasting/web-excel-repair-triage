# Prompt Kit freshness

## Status

Freshness is now a first-class acquisition guardrail. A user-reported Prompt Kit or prompt **version label** is treated as a freshness signal, not proof that the copy is current.

If a user says they are on a version such as `V39`, or says the kit was downloaded, installed, cached, or cloned earlier, the operator/agent must recommend a refresh before troubleshooting, tutorial guidance, or prompt selection unless currentness has already been proven in the current interaction.

## Required operator behavior

1. Say that the reported copy may be stale or unverified.
2. Route to the lowest-friction latest surface for the actual intent:
   - normal browser use → `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`;
   - phone/tablet install → `https://endeavoreverlasting.github.io/web-excel-repair-triage/` in the system browser;
   - Windows stable local app → `Open-Latest-PromptKit.cmd`;
   - editable checkout → preservation-first origin/worktree/branch/divergence gates, then `git merge --ff-only origin/main`;
   - explicit no-Git source snapshot → re-download canonical `main.zip`.
3. Continue normal guidance after the refresh/currentness gate.
4. If the user declines refresh, label the copy **stale-or-unverified** and keep that limitation visible.

## What this prevents

- continuing a support conversation against an old version merely because it has a familiar version number;
- assuming `V39`, `V40`, or any future label is current without checking the canonical route;
- telling a normal phone/browser user to clone or pull Git just to get the latest Prompt Kit;
- using a bare `git pull` as proof that an editable checkout is safely current.

## Validation

```bash
python -m py_compile scripts/validate_prompt_kit_freshness_guidance.py tests/test_prompt_kit_freshness_guidance.py
python scripts/validate_prompt_kit_freshness_guidance.py --summary
python -m unittest tests.test_prompt_kit_freshness_guidance -v
```

The focused validator also checks that `technician-needs-latest-prompt-kit` fires when a version label is reported and that the acquisition skill contains the same freshness-first routing.

## Proof ceiling

A passing validator proves the tracked harness requires the freshness prompt and maps it to the existing acquisition routes. It does not prove a specific browser cache, PWA/service worker, downloaded snapshot, Windows launcher execution, Termux checkout, or local Git state actually refreshed. Those still require observed runtime proof.
