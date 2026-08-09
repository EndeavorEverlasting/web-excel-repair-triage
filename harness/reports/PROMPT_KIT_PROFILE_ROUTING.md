# Prompt Kit Profile Routing

## Status

WORKING at repository/static proof level; final device/runtime acceptance remains separate.

## What this closes

A Prompt Kit action must now be qualified in this order: active repository, current host profile, current shell/execution surface, target profile, user intent, profile-associated Triage path, then command or handoff.

The active repository remains `EndeavorEverlasting/web-excel-repair-triage`. `EndeavorEverlasting/AgentSwitchboard` is related repository-family evidence for machine-profile and path conventions only; this Triage harness does not transfer mutation ownership to AgentSwitchboard.

## Working routes

- Windows PowerShell + Windows target: Windows syntax only. Normal browser use resolves to `Start-Process`; install intent resolves to the public phone/install launcher; local app work resolves `Open-Latest-PromptKit.cmd` from the profile-associated Triage checkout.
- Android Termux + Android target: Android/Termux syntax only. Normal use opens the direct Prompt Kit; install intent opens the public phone/install launcher.
- Windows host + Android target: `HANDOFF`; no `termux-open-url`, `command -v`, `/dev/null`, or other Android shell text is emitted as a runnable PowerShell command.
- Local Triage path: explicit Triage path > verified existing Triage checkout > sibling of verified `AGENT_SWITCHBOARD_REPO` > platform default.
- Windows platform-default commands expand `$env:USERPROFILE`; Android platform-default commands expand `$HOME` rather than passing unexpanded placeholder text.
- Browser-only use/install is supported without a repository path. Browser-only `edit` or `local-app` intent fails closed and must hand off to a supported local profile.

## Command hardening

- Externally supplied Windows repository paths are emitted as PowerShell single-quoted literals with embedded single quotes doubled.
- Externally supplied Android repository paths are emitted as POSIX single-quoted literals with embedded single quotes safely escaped.
- Cache-busting `main_sha` input accepts only 7–64 hexadecimal characters before any URL or shell command is built.
- Invalid SHA text, shell/profile mismatch, or unsupported browser-local work produces `BLOCKED` rather than a partially formed command.
- Cross-profile requests produce `HANDOFF` with `command: null`; target-shell syntax is never represented as runnable on the current shell.

## Known traps now enforced

- A related repository is context, not permission to switch the active repo.
- A target device is not the current execution surface.
- PowerShell redirection to `/dev/null` is invalid and must never be generated for Windows.
- Termux helpers must never be pasted into a Windows PowerShell session.
- A remembered `C:\Users\...` path is not profile evidence.
- WSL is not a substitute for an Android target.
- “Install” is not the same as “open the direct Prompt Kit”; install routes use the phone/install launcher.
- A browser cannot silently become an editable-checkout or local-launcher execution surface.

## Validators

```text
python scripts/validate_prompt_kit_profile_routing.py --summary
python -m unittest tests.test_prompt_kit_profile_routing -v
```

The focused validator compares the complete registered routing contract, exercises shell/path/target behavior, and rejects representative contract mutations. The root harness, staged pre-commit hook, pre-push hook, and Operational harness CI also run these gates.

The Operational harness workflow preserves `harness-completeness-report.json` with `if: always()` so a fail-closed completeness error remains inspectable instead of disappearing behind an exit code.

## Gaps / proof ceiling

This proves deterministic repository-family relationship, profile/shell qualification, path selection, shell-safe command construction, install/use distinction, and command/handoff classification on the tested checkout. It does not prove a particular Triage checkout exists at the recommended path, AgentSwitchboard machine-profile detection ran successfully on the operator machine, a browser opened, Termux exists, Git authentication works, a launcher ran, or a device executed the command.
