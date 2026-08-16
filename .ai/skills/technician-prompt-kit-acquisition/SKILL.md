# Technician Prompt Kit Acquisition

## Trigger

Use this skill when someone needs to open, install, share, refresh, clone, update, or locally edit the Prompt Kit.

Also trigger this skill when the user reports a Prompt Kit or prompt version label and currentness has not been proven, or when a downloaded, installed, cached, or cloned copy may be stale.

Route by intent:
1. use/open/share → public site;
2. phone/tablet install → public launcher + browser install/home-screen surface;
3. Windows stable local app → `Open-Latest-PromptKit.cmd`;
4. edit/commit/run repository tooling → real Git checkout;
5. explicit no-Git source snapshot → canonical `main.zip`.

Deep delivery/evidence law lives in `harness/specs/operator-delivery.md`; do not duplicate it here.

## Required inputs

- user intent and platform;
- freshness signal/currentness evidence;
- canonical repository/default branch and public URLs from tracked access documentation;
- local Git/runtime access only when the selected route needs it.

## Outputs

One selected acquisition route plus:
- freshness decision (`current` or `stale-or-unverified`);
- canonical URL, launcher, or checkout path;
- preservation-first update behavior;
- validation/runtime proof actually observed;
- remaining proof ceiling.

## Procedure

### 0. Freshness gate before guidance

A version label is a freshness signal, not proof of currentness. Before troubleshooting, tutorial guidance, or prompt selection, treat an older or previously acquired copy as potentially stale.

Recommend the lowest-friction refresh route first:
- browser use → `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`;
- phone/tablet → `https://endeavoreverlasting.github.io/web-excel-repair-triage/`;
- Windows stable local app → `Open-Latest-PromptKit.cmd`;
- editable checkout → use the preservation-first sequence in section 4 and integrate only with `git merge --ff-only origin/main`;
- ZIP snapshot → re-download canonical `main.zip` and keep calling it a point-in-time snapshot.

If refresh is explicitly declined, continue only while labeling the copy `stale-or-unverified`.

### 1. Normal browser use

Open:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

Do not require a clone merely to use the Prompt Kit. Normal browser use needs no repository checkout, ZIP extraction, Python, PowerShell, Termux, or local server.

### 2. Android or iPhone/iPad install

Open the public launcher:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/
```

Use the system browser. If an in-app browser intercepts the link, choose **Open in browser** first. On Android use the browser's install surface when offered; on iPhone/iPad use **Add to Home Screen**. This route is for use/install, not source work.

### 3. Windows stable local app

Run `Open-Latest-PromptKit.cmd`. The repository-owned launcher owns safe acquisition/update, validation, stable-origin serving, and Favorites behavior. Do not reconstruct that workflow manually when the launcher is available.

### 4. Real editable checkout

Use this route only for source editing, commits, pushes, or repository tooling.

Fresh clone:

```bash
git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
cd web-excel-repair-triage
```

For an existing checkout, run these gates in order:

```bash
git remote get-url origin
git status --porcelain
git branch --show-current
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git merge --ff-only origin/main
```

Interpret them strictly:
1. `git remote get-url origin` must equal `https://github.com/EndeavorEverlasting/web-excel-repair-triage.git`.
2. `git status --porcelain` must return no output; otherwise preserve the work and stop.
3. `git branch --show-current` must return `main`.
4. `git fetch origin main --prune` updates remote-tracking state only.
5. `git rev-list --left-right --count HEAD...origin/main` must report **0** in the first (local-only) count; otherwise preserve divergent/local-only work and stop.
6. Only then run `git merge --ff-only origin/main`.

For Android source work, use **Termux from F-Droid** rather than relying on an obsolete Play Store build, then install Git:

```bash
pkg update
pkg install git
```

Use the same clone and existing-checkout gates above. Normal Android Prompt Kit use does not require Termux.

### 5. ZIP snapshot fallback

When a source snapshot is explicitly wanted without Git, use the canonical `main.zip` route from `PROMPT_KIT_ACCESS.md`. Explain that it is point-in-time and does not provide normal Git updates.

## Guardrails

- Treat a reported version or previously acquired copy as a freshness trigger until currentness is proven.
- Recommend refresh before troubleshooting or prompt selection against a stale-or-unverified copy.
- Do not require a clone merely to use the Prompt Kit.
- Distinguish use/install intent from edit/commit/push intent before shell commands.
- Preserve dirty, divergent, wrong-branch, wrong-origin, or local-only work; never discard it merely to refresh the kit.
- Never embed credentials or user-specific absolute paths.
- Prefer repository-owned launchers and tracked access docs over reconstructed commands.
- Treat ZIP as a snapshot, not a synchronized checkout.
- Do not claim browser install, storage/Favorites, network, Git auth, or push success without observing it.

## Validation

```bash
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
python scripts/validate_prompt_kit_freshness_guidance.py --summary
python -m unittest tests.test_prompt_kit_freshness_guidance -v
python scripts/validate_context_architecture.py --summary
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
git diff --check
```

Runtime acceptance remains separate and device-specific.

## Proof ceiling

Repository tests prove routing, canonical references, freshness guidance, preservation-first Git policy, and registered ownership on the tested commit. They do not prove a specific device/browser installation, cache refresh, network, credentials, local storage/Favorites, Windows policy, or remote push.
