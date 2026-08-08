# Technician Prompt Kit Acquisition

## Trigger

Use this skill when a user or technician needs to **open, install, download, clone, update, or locally edit** the Prompt Kit on a phone, tablet, Windows PC, macOS, or Linux machine.

Route by intent before prescribing commands:

1. **Use/open/share only** → public Prompt Kit URL; no clone.
2. **Phone/tablet install** → public phone launcher and browser Add to Home Screen / Install App surface; no clone.
3. **Windows local app with stable Favorites origin** → `Open-Latest-PromptKit.cmd`; the launcher owns safe acquisition/update.
4. **Edit/commit/push/run repository tooling locally** → real Git checkout. On Android, use Termux from F-Droid when a shell checkout is required.
5. **No Git client but a source snapshot is explicitly wanted** → repository ZIP, clearly labeled as a snapshot.

Do not use this skill to repair arbitrary Git history, recover local commits, switch feature branches, authenticate providers, or claim device behavior that has not been observed.

## Required inputs

- User intent: use/install/share versus edit/commit/push/local tooling.
- Device/platform: Android, iPhone/iPad, Windows, macOS, Linux, or other browser-capable device.
- Canonical repository URL: `https://github.com/EndeavorEverlasting/web-excel-repair-triage.git`.
- Default branch: `main`.
- Public Prompt Kit URL: `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`.
- Public phone launcher URL: `https://endeavoreverlasting.github.io/web-excel-repair-triage/`.
- Git and repository access only when a real checkout is required.
- Windows PowerShell/Python only for the repository-owned Windows local-app path.

## Outputs

Depending on the selected route:

- the public Prompt Kit opened directly in the browser;
- an Android/iOS home-screen installation path through the public launcher;
- a validated Windows stable-origin local app launched through `Open-Latest-PromptKit.cmd`;
- a clean editable checkout on `main` for source work;
- or a clearly identified point-in-time ZIP snapshot.

The handoff must state which route was selected, why it matched the user intent, what prerequisites were required, and which runtime gates remain unproven.

## Procedure

### 1. Normal browser use

Open:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

Do not require a clone merely to use the Prompt Kit. Normal browser use must not require Git, ZIP extraction, PowerShell, Python, Termux, or a local server.

### 2. Android or iPhone/iPad install

Open the phone launcher:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/
```

- Android: open in Chrome, then use **Install app** or **Add to Home screen** when offered.
- iPhone/iPad: open in Safari, use **Share → Add to Home Screen**.
- If the GitHub mobile app opens its in-app browser, use **Open in browser** first.

The tracked generated HTML path is not a phone acquisition step. Keep normal phone users on the public launcher instead of source-file navigation.

### 3. Windows stable-origin local app

Use `Open-Latest-PromptKit.cmd`. The repository-owned launcher owns clone-or-fast-forward behavior, validation, portable Favorites, and loopback serving. Do not reconstruct that workflow by hand when the launcher is available.

### 4. Real editable checkout

Use this route only when the user intends to edit source, commit, push, inspect repository files locally, or run repository tooling.

Generic clone:

```bash
git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
cd web-excel-repair-triage
```

Existing clean checkout update:

```bash
git pull --ff-only origin main
```

For Android, install **Termux from F-Droid** rather than relying on the Play Store build, then run:

```bash
pkg update
pkg install git
cd ~
git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
cd web-excel-repair-triage
git status
```

Later updates remain fast-forward only:

```bash
cd ~/web-excel-repair-triage
git pull --ff-only origin main
```

A real checkout is the correct Android route when the user wants to edit, commit, push, or keep source locally. It is not required for normal Prompt Kit use.

### 5. ZIP snapshot fallback

When the user explicitly wants source files but has no Git client, use:

```text
https://github.com/EndeavorEverlasting/web-excel-repair-triage/archive/refs/heads/main.zip
```

Explain that ZIP is a snapshot. It does not provide normal Git updates and is not the preferred Favorites-preserving or app-like route.

## Guardrails

- Do not require a clone merely to use the Prompt Kit.
- Distinguish use/install intent from edit/commit/push intent before giving shell commands.
- Never run destructive Git cleanup or tell the operator to discard dirty, divergent, or local-only work merely to update the kit.
- Never overwrite an existing non-canonical checkout.
- Never embed credentials or user-specific absolute paths.
- Prefer repository-owned launchers over reconstructed Windows command sequences.
- Treat ZIP as a snapshot, not a synchronized checkout.
- Do not claim that browser installation, Termux/F-Droid availability, Git authentication, Favorites persistence, clipboard behavior, or push access succeeded without observing that device/runtime.

## Validation

Focused cross-device contract:

```bash
python -m py_compile scripts/validate_prompt_kit_cross_device_access.py tests/test_prompt_kit_cross_device_access.py
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
```

Connected harness gates:

```bash
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_skill_prompt_registry -v
python tests/test_prompt_kit_header_contract.py
```

Runtime acceptance remains separate:

- phone/browser: open the public launcher/site and observe install/open behavior;
- Android editable checkout: run the Termux clone/update commands on the device;
- Windows local app: execute `Open-Latest-PromptKit.cmd` and verify its stable-origin health proof.

## Proof ceiling

Repository and CI checks prove the device-routing contract, canonical URLs/commands, registered ownership, preservation-first Git posture, and current documentation/launcher references on the tested commit. They do not prove a specific device's browser menus, PWA installation, Termux or F-Droid availability, network, Git credentials, browser storage, clipboard behavior, Windows policy, or successful remote push.
