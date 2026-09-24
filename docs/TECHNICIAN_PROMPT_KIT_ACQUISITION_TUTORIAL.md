# Technician Tutorial: Get the Latest Prompt Kit

## Audience and result

This tutorial is for a Windows technician who needs the current Prompt Kit website and current registered generators without memorizing Git commands.

At the end, the repository is either freshly cloned from canonical `main` or safely fast-forwarded to current `origin/main`. The tool then opens either:

- `web\prompt-kit\index.html`; or
- `Run-PromptKitGenerator.cmd`.

The workflow does not deploy to another machine and does not modify a remote target box.

## What you need

On the Windows workstation:

1. Windows PowerShell 5.1 or newer.
2. Git for Windows available on `PATH`.
3. Python 3 available as either `py -3` or `python`.
4. Browser or Git network access to the canonical repository.
5. Repository access if GitHub requests authentication.

The launcher does not store credentials and does not automate provider or GitHub authentication.

## Get the CMD file with the mouse

### When somebody sends you the CMD file

Save `Acquire-Latest-PromptKit.cmd` somewhere easy to find, such as the Desktop. Double-click it.

### When downloading it from GitHub

1. Open the repository in a browser.
2. Open [`Acquire-Latest-PromptKit.cmd`](../Acquire-Latest-PromptKit.cmd).
3. Use GitHub's **Download raw file** control.
4. Save the file with the exact name `Acquire-Latest-PromptKit.cmd`.
5. Double-click the saved file.

The standalone CMD downloads only the tracked companion PowerShell GUI from canonical `main` into `%TEMP%\WebExcelPromptKit`. After the repository exists, the repo-local CMD uses the companion script already in the checkout.

## Use the acquisition window

The window title is **Get Latest Prompt Kit**.

### Controls

| Control | What to do |
|---|---|
| **Destination folder** | Keep the displayed default or enter the full destination repository path. |
| **Browse...** | Select the parent folder. The GUI appends `web-excel-repair-triage`. |
| **After validation** | Choose **Open Prompt Kit website** or **Open generator selection GUI**. |
| **Get Latest and Open** | Start the safe clone/update, validation, and open sequence. |
| **Close** | Exit without changing the repository. |
| Log area | Read timestamped progress and the exact failure message. |

The default destination is based on the current Windows profile, not a hard-coded technician name:

```text
%USERPROFILE%\Desktop\dev\web-excel-repair-triage
```

### First use: repository is absent

1. Confirm the destination folder.
2. Choose what to open after validation.
3. Click **Get Latest and Open**.
4. The tool creates the parent folder when needed.
5. It clones only canonical branch `main` from:

   ```text
   https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
   ```

6. It confirms the required site and generator files exist.
7. It runs the exact generated-site validation.
8. It opens your selected surface.

Expected successful log messages include:

```text
Starting safe acquisition.
Cloning the canonical repository into ...
Repository and Prompt Kit validation passed.
Opening Prompt Kit website.
```

The final message box says:

```text
The latest validated Prompt Kit is ready.
```

### Later use: repository already exists

The tool updates only when all of the following are true:

- the destination is a Git repository;
- `origin` points to the canonical repository;
- `git status --porcelain` is empty;
- the current branch is `main`;
- local `main` has no commits missing from `origin/main`.

It then fetches `origin/main` and uses a fast-forward-only merge. It does not reset, clean, overwrite, rebase, or discard work.

Expected successful log messages include either:

```text
Fetching the latest main branch.
Fast-forwarding main by N commit(s).
Repository and Prompt Kit validation passed.
```

or:

```text
Fetching the latest main branch.
Repository is already current.
Repository and Prompt Kit validation passed.
```

## What validation proves

Before opening anything, the acquisition tool verifies these tracked files:

```text
web\prompt-kit\index.html
Run-PromptKitGenerator.cmd
Build-PromptKitWebsite.cmd
configs\prompt_kit\generators.v1.json
scripts\build_prompt_kit_registry.py
```

It also verifies that the generator manifest uses schema `prompt-kit-generators/v1`, contains at least one generator, and that the checked-in website exactly matches the combined prompt registry build.

## Troubleshooting

### Windows PowerShell was not found

**Message:**

```text
Windows PowerShell was not found.
```

**Action:** Use a supported Windows installation or ask the administrator to restore Windows PowerShell. The standalone CMD currently invokes Windows PowerShell from `%SystemRoot%`.

### The GUI script could not be downloaded

**Message:**

```text
Could not download the acquisition GUI from the canonical repository.
Check network access to GitHub and try again.
```

**Action:** Confirm browser access to GitHub, proxy/VPN policy, and repository availability. Do not download scripts from an unofficial mirror.

### Git was not found

**Message:**

```text
Git was not found. Install Git for Windows and try again.
```

**Action:** Install Git for Windows through the approved software process, then reopen the CMD.

### Python 3 was not found

**Message:**

```text
Python 3 was not found. Install Python 3 and select Add Python to PATH.
```

**Action:** Install the approved Python 3 package and confirm either `py -3 --version` or `python --version` works in a new terminal.

### Destination exists but is not a Git repository

**Message begins:**

```text
The destination exists but is not a Git repository:
```

**Action:** Choose a different empty destination, or move/rename the unrelated folder. Do not let the tool overwrite it.

### Existing repository has an unexpected origin

**Message begins:**

```text
The existing repository has an unexpected origin:
```

**Action:** Stop. Confirm you selected the intended checkout. A developer or administrator may inspect `git remote -v`; the technician workflow will not rewrite the origin.

### Local modifications or untracked files exist

**Message:**

```text
The repository has local modifications or untracked files. Preserve or commit that work before updating.
```

**Action:** Do not delete or reset anything. Ask the work owner to commit, move, or otherwise preserve the files. Run the acquisition tool again only after the checkout is clean.

### Repository is not on `main`

**Message begins:**

```text
The repository is on branch '...', not 'main'. Switch safely before updating.
```

**Action:** Do not switch branches blindly. Ask the branch owner to commit and push their work, then return the checkout to `main` safely.

### Local `main` contains commits not on `origin/main`

**Message begins:**

```text
Local main contains N commit(s) not on origin/main. No reset or overwrite was attempted.
```

**Action:** Stop and escalate to a developer. The local commits must be preserved and reviewed. The tool intentionally refuses to reset or overwrite them.

### Clone, fetch, or authentication fails

The error dialog includes the Git command, exit code, and Git output.

**Action:** Check network access, GitHub authentication, proxy/VPN policy, and repository permissions. Never paste tokens into the CMD or documentation.

### Required Prompt Kit file is missing

**Message begins:**

```text
Required Prompt Kit file is missing:
```

**Action:** Confirm the checkout is canonical `main`. Re-run only after the repository is clean. If the file is absent on current `main`, report a repository defect.

### Generator manifest is unsupported or empty

Possible messages:

```text
Generator manifest schema is missing or unsupported.
Generator manifest contains no registered generators.
```

**Action:** Report the failure to the repository maintainer. Do not edit the manifest locally merely to bypass validation.

### Prompt Kit exact-output validation failed

**Message begins:**

```text
Prompt Kit exact-output validation failed.
```

**Action:** Preserve the log and report the mismatch. The site may be stale relative to the tracked prompt registries. Do not open or distribute it as current.

## Safe rollback and recovery

### You closed the GUI before clicking the button

Nothing changed.

### A new clone failed partway

Do not assume the destination is usable. Preserve the error log. An administrator may inspect the incomplete folder. Delete it only after confirming it is a new failed clone with no technician-created files.

### An existing checkout updated successfully but you expected different content

Do not run `git reset` or delete files. The update was fast-forward-only. Record the current commit and escalate to a developer for review.

### The tool refused the checkout

That refusal is the safety behavior. Preserve the local work and resolve the named condition; do not bypass the check.

## Operator proof checklist

Record:

- workstation class or asset identifier without private credentials;
- date and time;
- selected destination;
- whether the repo was cloned, updated, or already current;
- whether the website or generator GUI opened;
- final log line;
- any error message;
- operator acceptance: pass or fail.

A passing CI workflow proves tracked contracts. Only this real Windows run proves the mouse-accessible GUI on the technician machine.
