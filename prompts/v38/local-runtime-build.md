# LOCAL RUNTIME BUILD CONVERTER

Use this prompt with **Cosmos by Augment, Cursor, Codex, or another coding agent that has direct access to the local filesystem, terminal, Git repository, and development tools**.

## Mission

Convert the attached sprint, plan, handoff, or project request into a real local runtime build, then execute the build in the repository.

Do not merely factor the request into prompts, describe an implementation, return commands for the operator to run, or stop after a plan. Use the local workspace and integrated terminal to inspect the repository, implement the owned behavior, run it locally, validate it, commit it, push it, and open or update the pull request when the environment permits.

## Local-directory discipline

Before issuing or executing repository commands:

1. Identify the intended repository from the request, current workspace, open files, Git remotes, and nearby repository evidence.
2. Resolve the absolute local repository path.
3. Change into that directory with `Set-Location` or `cd`.
4. print `Get-Location` or `pwd`;
5. run `git rev-parse --show-toplevel` and confirm it matches the intended repository.

Never provide a sequence of repository commands while leaving the operator in an unknown or incorrect directory. When the supplied path is blank, stale, or a placeholder, recover the correct path from the current workspace and Git evidence instead of stalling.

## Execution contract

Name and preserve:

- repository and verified local path;
- branch, isolated worktree, or pull request;
- sprint;
- execution lane;
- owned scope;
- forbidden scope;
- expected tracked artifacts;
- generated local artifacts;
- validation order;
- proof target and proof ceiling.

Treat plans, prompts, scripts, manifests, schemas, validators, tests, logs, reports, branches, commits, and pull requests as one connected operational system.

## Required workflow

### 1. Establish the repository floor

Run only enough preflight to avoid damaging work:

```text
git status --short
git branch --show-current
git log --oneline --decorate -5
git worktree list --porcelain
git remote -v
```

If the active worktree contains unrelated changes, preserve them and create or reuse an isolated worktree. Do not reset, clean, overwrite, or discard unknown work.

### 2. Recover executable intent

Read repository rules, recent commits, open pull requests, handoff files, plans, scripts, validators, tests, artifact registries, workflow registries, and current generated-output policy.

Translate the sprint into a bounded local runtime contract. Identify which behavior belongs in application code, scripts, schemas, validators, fixtures, agent skills, prompts, or documentation. Prompts may orchestrate behavior but must not replace implementation.

### 3. Build the local runtime surface

Implement the smallest coherent runtime that makes the sprint executable locally. Reuse existing repository patterns before inventing new ones.

A runtime build may include:

- a CLI, PowerShell, shell, Python, Node, or repository-native entrypoint;
- environment and dependency checks;
- Plan and Apply modes where mutation is material;
- schemas, manifests, run context, and artifact registration;
- deterministic routing for local coding agents;
- fixtures and disposable proof targets;
- bounded process handling, timeouts, and failure cleanup;
- generated-output isolation and source immutability;
- machine-readable results and concise operator reports.

The runtime must fail closed when prerequisites, authorization, scope, repository identity, or proof artifacts are missing.

### 4. Execute locally

Run the new or repaired runtime in the agent's integrated terminal. Do not stop after creating scripts.

Use a sanitized fixture or disposable repository when the real target would involve credentials, private data, production systems, destructive actions, or unavailable operator artifacts. Do not invent runtime proof from static tests.

### 5. Validate in order

Run the strongest practical checks:

1. parser, schema, or static checks;
2. targeted tests for changed behavior;
3. relevant repository validators;
4. local runtime or disposable proof;
5. broader tests when practical;
6. secret, generated-output, and machine-local-path hygiene;
7. `git diff --check`;
8. final Git and worktree state;
9. final-head CI when available.

Report exact failures and distinguish owned failures from unrelated baseline failures. Do not weaken checks to obtain green results.

### 6. Commit and publish

Unless the sprint is already complete or exactly blocked:

```text
git diff --check
git status --short
git diff --stat
git diff
git add <owned tracked files>
git commit -m "<useful message>"
git push -u origin <branch>
```

Open or update the intended pull request. Do not force-push, merge, deploy, publish a release, or mutate a default branch unless the sprint explicitly owns that action.

## Failure conditions

The task is not complete when the agent only:

- rewrites or improves the sprint prompt;
- factors requirements without building the runtime;
- returns a plan, checklist, commands, or handoff;
- creates scripts but does not execute them;
- reports process exit without the required artifact or repository mutation;
- claims local proof from CI or static validation alone;
- asks the operator to locate the repository when the current workspace can resolve it;
- stops because conversation tokens are limited while a safe bounded repository mutation remains possible.

## Safety boundary

Do not expose or automate credentials, provider authentication, API keys, browser sessions, personal data, private workbook contents, customer data, production deployment, or destructive infrastructure actions. Keep generated runtime evidence and machine-local paths out of commits unless a sanitized fixture or explicit repository contract requires them.

## Final response

Return:

```text
CONTEXT
- repo:
- local path:
- branch/worktree:
- sprint:
- lane:
- scope:
- forbidden scope:

WORK COMMITTED
- summary:
- files changed:
- commit SHA:
- pushed:
- PR:

LOCAL RUNTIME PROOF
- entrypoint:
- command:
- artifact/result:
- proof achieved:
- proof ceiling:

VALIDATION
- command:
- result:
- skipped checks:

BLOCKERS / GAPS
- blocker:
- gap:
- risk:

FINAL GIT STATE
- git status --short:
- worktrees:

NEXT COMMAND
- one exact command:
```

A final response without a commit SHA, concrete Git/GitHub mutation, runtime artifact, exact blocker with an applicable patch, or proof that the sprint was already complete is invalid.