# Prompt Kit Profile Routing

## Status

WORKING at repository/static proof level.

## What this closes

A Prompt Kit action must now be qualified in this order: active repository, current host profile, current shell/execution surface, target profile, user intent, profile-associated Triage path, then command or handoff.

The active repository remains `EndeavorEverlasting/web-excel-repair-triage`. `EndeavorEverlasting/AgentSwitchboard` is related repository-family evidence for machine-profile and path conventions only; this Triage harness does not transfer mutation ownership to AgentSwitchboard.

## Working routes

- Windows PowerShell + Windows target: Windows syntax only. Normal browser use resolves to `Start-Process`; local app work resolves `Open-Latest-PromptKit.cmd` from the profile-associated Triage checkout.
- Android Termux + Android target: Android/Termux syntax only.
- Windows host + Android target: `HANDOFF`; no `termux-open-url`, `command -v`, `/dev/null`, or other Android shell text is emitted as a runnable PowerShell command.
- Local Triage path: explicit Triage path > verified existing Triage checkout > sibling of verified `AGENT_SWITCHBOARD_REPO` > platform default.
- Browser-only use: no local repository path is required.

## Known traps now enforced

- A related repository is context, not permission to switch the active repo.
- A target device is not the current execution surface.
- PowerShell redirection to `/dev/null` is invalid and must never be generated for Windows.
- Termux helpers must never be pasted into a Windows PowerShell session.
- A remembered `C:\Users\...` path is not profile evidence.
- WSL is not a substitute for an Android target.

## Validators

```text
python scripts/validate_prompt_kit_profile_routing.py --summary
python -m unittest tests.test_prompt_kit_profile_routing -v
```

The root harness, staged pre-commit hook, pre-push hook, and Operational harness CI also run these gates.

## Gaps / proof ceiling

This proves deterministic repository-family relationship, profile/shell qualification, path selection, and command/handoff classification on the tested checkout. It does not prove a particular Triage checkout exists at the recommended path, AgentSwitchboard machine-profile detection ran successfully on the operator machine, a browser opened, Termux exists, Git authentication works, or a device executed the command.
