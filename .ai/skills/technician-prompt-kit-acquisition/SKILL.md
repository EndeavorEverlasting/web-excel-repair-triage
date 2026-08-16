# Technician Prompt Kit Acquisition

## Trigger

Use when someone needs to open, install, share, refresh, clone, or locally edit the Prompt Kit, or when a previously acquired/version-labeled copy may be stale.

Select by intent:
1. use/open/share → public site;
2. phone/tablet install → public launcher + browser install/home-screen surface;
3. Windows stable local app → `Open-Latest-PromptKit.cmd`;
4. edit/commit/run repo tooling → real Git checkout;
5. explicit no-Git source snapshot → `main.zip`.

Deep delivery/evidence law lives in `harness/specs/operator-delivery.md`; do not duplicate it here.

## Required inputs

- user intent and platform;
- freshness signal/currentness evidence;
- canonical repo/default branch from tracked access documentation;
- local Git/runtime access only if the selected route needs it.

## Outputs

One selected acquisition route plus:
- freshness decision (`current` or `stale-or-unverified`);
- canonical URL/launcher/checkout path for that route;
- preservation-first update behavior;
- validation/runtime proof actually observed;
- remaining proof ceiling.

## Procedure

1. **Freshness gate.** A reported old version, download, cache, install, or checkout is not currentness proof. Route the user to the lowest-friction canonical refresh surface first; if refresh is declined, keep `stale-or-unverified` visible.
2. **Browser use.** Open the public Prompt Kit URL from `PROMPT_KIT_ACCESS.md`. No clone, ZIP, Python, PowerShell, Termux, or local server is required.
3. **Phone/tablet.** Use the public phone launcher from `PROMPT_KIT_ACCESS.md`; use the system browser's install/Add-to-Home-Screen feature where supported.
4. **Windows local app.** Use `Open-Latest-PromptKit.cmd`; the repository launcher owns safe acquisition/update, validation, stable-origin serving, and Favorites behavior. Do not reconstruct it manually.
5. **Editable checkout.** Only for source/tooling intent. Verify canonical origin, clean worktree, branch `main`, fetch `origin main`, prove zero local-only commits, then integrate with `git merge --ff-only origin/main`. Preserve and stop on dirty/divergent/wrong-origin/wrong-branch state.
6. **ZIP.** Use canonical `main.zip` only when a point-in-time source snapshot is explicitly wanted; label it a snapshot.
7. Run the validator/launcher owned by the chosen route and report observed proof separately from assumptions.

## Guardrails

- Do not translate “get latest” into Git work for ordinary browser users.
- Never discard dirty/divergent/local-only work to update Prompt Kit.
- Never embed credentials or user-specific absolute paths.
- Prefer repository-owned launchers and tracked access docs over reconstructed commands.
- Do not claim browser install, storage/Favorites, network, Git auth, or push success without observing it.
- Public URL/launcher and detailed preservation rules are canonical in tracked contracts, not this skill.

## Validation

```bash
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
python scripts/validate_prompt_kit_freshness_guidance.py --summary
python -m unittest tests.test_prompt_kit_freshness_guidance -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
git diff --check
```

Runtime acceptance remains separate and device-specific.

## Proof ceiling

Repository tests prove routing, canonical references, preservation-first policy, and registered ownership on the tested commit. They do not prove a specific device/browser installation, cache refresh, network, credentials, local storage/Favorites, Windows policy, or remote push.
