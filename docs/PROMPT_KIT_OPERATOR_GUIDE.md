# Prompt Kit Operator Guide

This guide describes the Prompt Kit behavior that is implemented on the repository's current `main` release. It is for browser users, Windows technicians, repository developers, and administrators who need to find, copy, and prove the right prompt without memorizing hidden commands.

The generated release is `web/prompt-kit/index.html`. Do not hand-edit that file. Prompt content and browser behavior are owned by the tracked registry/runtime sources and rebuilt through `scripts/build_prompt_kit_registry.py`.

## Choose the supported entry point

| Operator / environment | Preferred entry point | Notes |
|---|---|---|
| Browser user on Windows, Linux, macOS, phone, or tablet | `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/` | No Git, Python, or repository checkout is required. |
| Windows user who wants a stable local origin and persistent Favorites | `Open-Latest-PromptKit.cmd` | Reuses or creates the canonical checkout safely, validates the release, builds the portable artifact, and serves it from `http://127.0.0.1:8765/`. |
| Windows technician who must choose the destination or generator surface | `Acquire-Latest-PromptKit.cmd` | Advanced path. The normal user path is `Open-Latest-PromptKit.cmd`. |
| Developer with an existing checkout | Run the builder parity check from the repository root | Keep generated HTML derived from the canonical sources. |
| User without Git who needs an offline snapshot | Download the `main` ZIP and open `web/prompt-kit/index.html` after extraction | A ZIP is a snapshot and does not provide the stable-origin Favorites behavior of the Windows launcher. |

There is no separate Linux-only Prompt Kit product. Linux operators should normally use the public browser release. Linux developers may use the repository checkout and cross-platform Python/Node validation commands documented below.

## Safety rules before using a local checkout

The Windows acquisition path is intentionally fail-closed. It must not reset or overwrite local work merely to open the Prompt Kit.

An existing canonical checkout is expected to be clean, on `main`, pointed at the canonical origin, and fast-forwardable. Dirty, divergent, wrong-branch, wrong-origin, local-only, or occupied destinations are preserved and refused rather than force-reset or replaced with ad-hoc `-latest` sibling clones.

If the local launcher refuses a checkout that contains work you care about:

1. do not run `git reset --hard`, delete the checkout, or create a second ordinary clone just to make the launcher happy;
2. preserve or commit the local work, or use an intentionally isolated worktree when repository work requires a separate writer;
3. use the public Prompt Kit URL when you only need to read/copy prompts and do not need the local stable-origin Favorites runtime.

## Tutorial 1 — Find the right prompt

Use this path when you know the outcome you want but do not know the Prompt Kit ID.

1. Open the Prompt Kit.
2. Select the glowing **Tutorial · Find My Prompt** control.
3. Answer the **four** current questions:
   - **Where are you starting?** — new/no checkout, already in a repository, or app/artifact open.
   - **Do you have a known problem you want to solve?** — failure, known task, repeated stall, or discovery/planning.
   - **What are you trying to accomplish?** — plan, coordinate, build, AI/agent production hardening, prove, ship, teach, or close out.
   - **How should the work be organized?** — one sprint, parallel lanes, dependency-ordered work, or live/runtime proof.
4. Read the **Primary recommendation** first. The page may show up to two additional candidates.
5. Use **Open** when you need to inspect the full prompt before committing to it, or **Copy** when you are ready to paste the prompt into a new chat.
6. If the primary prompt has registered continuation guidance, the **After the recommendation** preview shows the current `nextStep` path.
7. After opening a prompt, use the **Guided workflow** panel to read the current **NEXT-STEP CONTRACT** and **READY TO CONTINUE WHEN** evidence gate before moving on.

### What the browser finder actually does

The browser questionnaire is not a hard-coded prompt-ID decision tree. Each selected answer contributes ordinary search phrases. Those phrases are sent through the same `filterPromptsForQuery(PROMPTS, query)` path used by normal Prompt Kit search. For each phrase, the finder scores the first five shared-search results, aggregates evidence across answers, sorts by score/discovery rank, and returns at most three recommendations.

That keeps the finder aligned with the current registry, synonyms, metadata, and search behavior, but it also means the questionnaire is a routing aid rather than an authorization or correctness oracle. When you already know the exact specialist you need, searching its ID or exact name is more precise than intentionally answering broader questions until it appears.

### Important inherited-work route: P83

If another agent, chat, branch, PR, report, artifact, or implementation says work is complete or partially complete and you need to verify whether that claim is actually true, use **P83 — Agent Work Verifier & Iterative Advancer**.

The current four-question browser questionnaire does not have a dedicated "another agent claims this is complete" answer. In that situation, search **`P83`** or the exact name directly instead of forcing the broader questionnaire to infer the distinction.

P83 is specifically for treating inherited completion claims as hypotheses, checking the exact current evidence, correcting or finishing the work, independently deriving validation, and advancing the proven slice through integration when authorized. Generic prototyping, live-proof, regression, or integration prompts can be later steps; they do not replace the need to verify the inherited claim first.

## Tutorial 2 — Use, prove, and continue

Opening a prompt adds a registry-backed **Guided workflow** panel.

- **NOW** identifies the current prompt.
- **NEXT-STEP CONTRACT** renders the prompt's current registry `nextStep` text.
- **READY TO CONTINUE WHEN** renders the current expected output or proof gate.
- **NEXT** / **OPTION** cards are created only for prompt IDs actually referenced by `nextStep` and present in the current registry.
- **Open** inspects a registered next prompt; **Copy** copies it.
- **Mark this step complete** stores lightweight progress only in browser `sessionStorage`.
- When no explicit successor exists, use **Re-run Find My Prompt** after the completed work changes your context.

Marking a step complete is navigation state, not repository proof. It does not modify the prompt registry, create a commit, merge a PR, validate a runtime, or change saved Favorites.

## Tutorial 3 — Favorites and favorite-prompt shortcuts

### Save a Favorite

Select the star on a prompt card. Favorites are persisted under the browser-local key `promptKit.favoritePromptIds.v1`.

Favorites do **not** reorder the normal library. Use the explicit **Favorites** view (header control or `4`) when you want to see the saved collection without the ordinary library/category/type/search restrictions.

### Configure a prompt-ID shortcut

1. Favorite the target prompt first.
2. Open **Hotkeys** or press the unmodified backtick key (`` ` ``).
3. In **Favorite prompt shortcuts**, enter a canonical ID such as `P95` and save it.
4. The effective typed sequence is the lowercase ID, such as `p95`.
5. Type the sequence outside editable fields. Sequence state expires after **1.2 seconds**.

A configured prompt shortcut is accepted only when the target exists and is currently a Favorite. Browser storage must succeed before the new binding becomes active.

### What a configured shortcut does now

Completing a configured Favorite shortcut:

1. clears the transient browsing restrictions needed to reveal the target;
2. renders and scrolls the target prompt card into view;
3. copies the target's canonical prompt through the normal `copyPrompt` path;
4. **does not open prompt detail**.

The Hotkeys panel labels these bindings as **Copy + reveal P##**. A buffered prompt sequence gets the next digit before built-in digit navigation, so a valid sequence such as `p95` is not interrupted by the built-in `5` command.

### Core hotkeys

| Key | Action |
|---|---|
| `` ` `` | Show / hide Hotkeys |
| `/` | Focus search |
| `1` | All prompts |
| `2` | Standard prompts |
| `3` | GNHF prompts |
| `4` | Favorites |
| `5` | Doctrine |
| `R` | Toggle reference panel |
| `F` | Show / hide filters |
| `[` | Hide filters |
| `]` | Show filters |
| `T` | Scroll to top |
| `B` | Scroll to bottom |
| `Esc` | Close the active surface or clear temporary filters |

Navigation shortcuts are ignored while typing in input, textarea, select, or content-editable surfaces. Modified backtick chords are ignored.

## Copy and prompt-card interactions

- Single click/tap on a prompt card copies the prompt.
- Double-click opens prompt detail on desktop.
- **Open** is the explicit detail action and remains available on touch/coarse-pointer layouts.
- **Copy** is always available on cards and prompt detail.
- Successful copy uses the current green confirmation path.
- **Esc** closes the active detail/help surface before broader filter clearing.
- Activating the **AI Harness Prompt Kit** title resets temporary browsing state while preserving saved Favorites.

## Favorites backup and recovery

The Windows portable runtime adds **Export Favorites** and **Import Favorites**.

Export before clearing browser data, changing browser profiles/devices, or deliberately moving between the public GitHub Pages origin and the local loopback origin. Import validates and merges the backup; it does not delete Favorites already stored at the destination.

If Favorites appear missing after opening a direct `file://` copy at a different extraction path, the browser origin may have changed. Prefer the stable Windows loopback launcher for persistent local use or restore with the exported Favorites file.

## Troubleshooting

| Symptom | Safe action | What not to conclude |
|---|---|---|
| Finder recommendation feels too generic | Search the exact prompt ID/name, or use P65 conversationally when you truly need another guided selection pass. | A high-ranked finder result is not automatic authorization or proof that adjacent prompts are wrong. |
| Another agent says work is complete but observed behavior disagrees | Search/open **P83** directly and verify the inherited work against current evidence. | Do not treat the prior completion report as proof. |
| Favorite prompt shortcut is rejected | Confirm the ID exists and Favorite the prompt first. | Do not create another shortcut system or edit browser storage by hand. |
| Typed prompt sequence does nothing | Start outside an editable field and type the sequence within the 1.2-second buffer window. | A timed-out/ignored sequence does not prove the target prompt is missing. |
| Copy has no visible/browser clipboard effect | Try the explicit **Copy** control and check browser clipboard permissions. | Repository tests cannot certify clipboard policy in every browser/device. |
| Windows launcher refuses an existing checkout | Preserve the checkout; resolve its dirty/divergent/wrong-origin state deliberately, or use the public browser release meanwhile. | Do not force-reset or make a persistent `-latest` sibling clone. |
| Public site seems older than a PR | Check whether the change is actually merged to `main` and whether the Pages deployment completed. | A PR preview or green branch is not the public release. |
| Direct-file Favorites disappeared after moving/extracting the site | Use the stable local origin or restore an exported Favorites backup. | Do not assume the prompt registry itself lost the Favorite IDs. |

## Developer / administrator validation

From the repository root, use the repository-owned checks rather than hand-validating generated HTML:

```powershell
node --check docs/prompt-kit.js
node --check docs/prompt-kit-guided-recommendations.js
node --check docs/prompt-kit-journey.js
node --check docs/prompt-kit-polish.js
python -m unittest tests.test_prompt_kit_hotkey_completion -v
python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v
python scripts/validate_prompt_kit_discovery.py --summary
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

Windows portable-runtime validation additionally uses:

```powershell
python scripts/serve_prompt_kit_portable.py --build-only
python scripts/validate_prompt_kit_portability.py --require-artifact --output Outputs/prompt-kit-portability-validation.json --summary
```

The CI owner is `.github/workflows/prompt-kit-web.yml`.

## Proof ceiling

Repository validation can prove source syntax, finder structure, shared-search routing mechanics, registry-owned journey extraction, Favorite/shortcut policy, executable shortcut seam behavior, generated-site parity, and focused documentation assertions. The repository also contains browser-proof infrastructure for runtime-facing Prompt Kit claims.

Documentation alone does **not** prove clipboard permission on every browser/device, Windows field execution on a particular workstation, live GitHub Pages freshness, organizational acceptance of a recommendation, or the success of a copied prompt in an environment whose required permissions/runtime are unavailable. Name those steps as runtime/operator proof when they matter.
