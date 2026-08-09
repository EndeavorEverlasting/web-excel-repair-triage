# Prompt Kit Profile-Qualified Routing Workflow

## Trigger

Use this workflow inside `EndeavorEverlasting/web-excel-repair-triage` whenever Prompt Kit guidance would emit a shell command, choose a local repository/launcher path, or hand work from one device profile to another.

## Repository boundary

- Active repository and mutation owner: `EndeavorEverlasting/web-excel-repair-triage`.
- Related repository-family profile/path authority: `EndeavorEverlasting/AgentSwitchboard`.
- AgentSwitchboard is consumed read-only for machine-profile and path-convention evidence. Its relevance never silently changes the active repository.

## Required route order

1. Confirm the active repository is Triage.
2. Qualify the current host profile.
3. Qualify the current shell/execution surface.
4. Qualify the target profile/device.
5. Classify intent: `use`, `install`, `local-app`, or `edit`.
6. If local Triage tooling is required, resolve the profile-associated Triage path.
7. Emit either a command safe for the current shell or a cross-profile `HANDOFF`.

## Path resolution

For local launcher/source work, use this order:

1. explicit/proven Triage path (`WEB_EXCEL_TRIAGE_REPO` when supplied by the operator environment);
2. verified existing Triage checkout;
3. sibling `web-excel-repair-triage` next to verified `AGENT_SWITCHBOARD_REPO`;
4. platform default (`%USERPROFILE%\dev\web-excel-repair-triage` on Windows, `$HOME/web-excel-repair-triage` on Android).

Do not use a remembered user-specific absolute path.

## Shell isolation

- Windows PowerShell: use Windows syntax only. `termux-open-url`, `command -v`, `/dev/null`, `pkg install`, and `$PREFIX` are invalid route output.
- Android Termux: use Termux/bash syntax only. PowerShell `Start-Process` and `Set-Location` are invalid route output.
- Cross-profile target: return `HANDOFF`; do not provide the target-shell command as runnable in the current shell.
- Windows → Android does not become a WSL repair task. The Android action remains on the Android device.

## Deterministic entry point

```text
python scripts/resolve_prompt_kit_profile_route.py --host-profile <windows|android|browser> --shell <powershell|termux-bash|browser> --target-profile <windows|android|browser> --intent <use|install|local-app|edit> [--triage-repo <path>] [--agent-switchboard-repo <path>] [--main-sha <sha>]
```

Exit `0` means a current-surface route was produced. Exit `2` means `BLOCKED` or `HANDOFF`; treat its JSON as routing evidence, not as a failed product runtime.

## Validation and failure handling

Run:

```text
python scripts/validate_prompt_kit_profile_routing.py --summary
python -m unittest tests.test_prompt_kit_profile_routing -v
```

On failure, repair the Triage contract/resolver/skill/registry/hook owner. Do not weaken fixtures, switch to AgentSwitchboard mutation, reconstruct a cross-profile command manually, or claim device execution.

## Handoff

Report active repository, related evidence source, host profile, shell, target profile, intent, selected execution surface, profile-associated Triage path when needed, route status, command or handoff action, validation result, and runtime proof ceiling.

## Proof ceiling

Repository/static/CI routing proof only. No filesystem path existence, browser behavior, Termux availability, Git authentication, launcher execution, or target-device success is proven.
