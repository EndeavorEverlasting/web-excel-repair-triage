# Prompt Kit Administrator Verification Runbook

## Audience and purpose

This runbook is for developers and administrators preparing the Prompt Kit acquisition and generator workflow for technicians.

It verifies repository contracts, prerequisites, safety boundaries, and evidence. It does not replace a technician's Windows mouse test.

## Platform responsibilities

| Surface | Responsibility |
|---|---|
| Windows technician workstation | Run `Acquire-Latest-PromptKit.cmd`, use the GUI, and confirm the selected site or generator opens. |
| Browser | Render the local static Prompt Kit and support operator search/copy review. |
| Linux or CI | Compile and run static validators, registry checks, documentation checks, and artifact hygiene. |
| Administrator box | Confirm approved Git/Python installation, network policy, GitHub access, and evidence collection. |
| Remote target machine | No step. This workflow does not deploy to, scan, or modify a target machine. |

## Tracked implementation to inspect

Before certifying the workflow, inspect:

```text
Acquire-Latest-PromptKit.cmd
scripts\Acquire-LatestPromptKit.ps1
Run-PromptKitGenerator.cmd
Build-PromptKitWebsite.cmd
scripts\prompt_kit_generator_gui.py
scripts\build_prompt_kit_registry.py
configs\prompt_kit\generators.v1.json
web\prompt-kit\index.html
harness\manifest.v1.json
```

The acquisition implementation must continue to use canonical repository URL:

```text
https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
```

and default branch:

```text
main
```

## Prerequisite verification on Windows

Use an approved terminal and a non-private test location.

```powershell
& {
    Set-Location -LiteralPath $HOME

    $Checks = @(
        @{ Name = 'Windows PowerShell'; Command = { $PSVersionTable.PSVersion.ToString() } },
        @{ Name = 'Git'; Command = { git --version } },
        @{ Name = 'Python launcher'; Command = { py -3 --version } }
    )

    foreach ($Check in $Checks) {
        try {
            $Result = & $Check.Command 2>&1
            "PASS: $($Check.Name): $Result"
        }
        catch {
            "FAIL: $($Check.Name): $($_.Exception.Message)"
        }
    }
}
```

If `py -3` is unavailable but `python --version` succeeds, the tracked scripts use the `python` fallback.

Confirm Tkinter separately:

```powershell
& {
    Set-Location -LiteralPath $HOME
    python -c "import tkinter; print('PASS: tkinter available')"
}
```

Do not store tokens, passwords, or private repository URLs in scripts or screenshots.

## Static repository verification

From the repository root:

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_operator_documentation -v
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Expected result: every command exits zero. A failing contract is a release blocker until repaired or explicitly dispositioned by the repository owner.

## Safe field-test matrix

Use a disposable or dedicated technician test folder. Do not use an active developer checkout for refusal tests.

| Case | Setup | Expected result |
|---|---|---|
| Fresh clone | Destination does not exist | Clone canonical `main`, validate, open selected surface. |
| Already current | Clean canonical `main` at `origin/main` | Report already current, validate, open selected surface. |
| Remote ahead | Clean canonical local `main` behind `origin/main` | Fetch, fast-forward only, validate, open selected surface. |
| Dirty checkout | Add an untracked harmless test file in disposable clone | Refuse update; no reset or cleanup. Remove the test file manually after evidence capture. |
| Wrong branch | Create and switch to a disposable branch in disposable clone | Refuse update; no branch switch. Return to `main` manually after evidence capture. |
| Local-only commit | Create a harmless local commit in disposable clone | Refuse update; no reset. Preserve or delete the disposable clone only after evidence capture. |
| Wrong origin | Use a disposable repository with another origin at the selected path | Refuse update; do not rewrite origin. |
| Non-Git destination | Create an ordinary folder at the exact destination | Refuse clone; do not overwrite folder. |
| Missing Python | Test only in an approved isolated environment | Refuse during exact-output validation with a clear prerequisite message. |

Never manufacture refusal cases inside a checkout containing real uncommitted work.

## Windows mouse acceptance procedure

1. Obtain `Acquire-Latest-PromptKit.cmd` from canonical `main`.
2. Double-click it from outside a repository checkout.
3. Confirm the **Get Latest Prompt Kit** window opens.
4. Click **Browse...** and choose a safe parent folder.
5. Confirm the resulting destination ends in `web-excel-repair-triage`.
6. Select **Open Prompt Kit website**.
7. Click **Get Latest and Open**.
8. Confirm the log reaches `Repository and Prompt Kit validation passed.`
9. Confirm the local HTML site opens.
10. Close the site and run the CMD again.
11. Select **Open generator selection GUI**.
12. Confirm the repository reports current or fast-forwards safely and the generator GUI opens.
13. Record pass/fail and the tested commit.

## Evidence to capture

Capture only non-sensitive evidence:

- repository commit SHA;
- branch `main`;
- test case name;
- workstation class or asset identifier;
- success or exact failure message;
- whether website or generator GUI opened;
- CI run URLs or PR checks;
- operator acceptance result.

Screenshots may show the GUI and non-sensitive log text. Redact usernames, private folder names, authentication dialogs, tokens, and unrelated desktop content.

## Failure triage

### Network or authentication failure

Confirm approved proxy/VPN policy, browser access to GitHub, repository permission, and Git credential configuration. Do not embed credentials in the CMD or companion script.

### Dirty or divergent checkout refusal

Treat as a successful safety check. Preserve the work and escalate to its owner. Do not bypass using reset, clean, force checkout, or deletion.

### Exact-output mismatch

Run:

```powershell
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

If it fails, compare tracked prompt registries and the generated site through a normal developer branch and PR. Do not ask the technician to rebuild or commit over a dirty checkout.

### GUI unavailable but command-line validators pass

Static proof is not Windows GUI proof. Check Windows PowerShell, WinForms policy, Python/Tkinter, endpoint controls, and execution-policy restrictions. Preserve the exact error and keep the field test failed until corrected.

## Rollback policy

The acquisition tool has no destructive rollback command because it performs only clone or fast-forward update.

- For a failed new clone, delete the destination only after proving it contains no operator-created work.
- For an unexpected successful fast-forward, record the before/after commits when available and use a developer-owned recovery branch or normal Git review. Do not instruct technicians to reset.
- For a refused existing checkout, make no repository change until the local work owner resolves it.

## Release proof gate

Ready for technician distribution requires:

1. documentation validator passing;
2. harness, registry, site-parity, and hygiene validators passing;
3. PR merged to `main`;
4. standalone CMD downloaded from the merged commit;
5. at least one Windows mouse acceptance run on the intended workstation class.

Without item 5, report static/CI proof only.
