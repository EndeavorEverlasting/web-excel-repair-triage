# Agent Switchboard Harness Doctrine

This file is the canonical agent harness for this repository. It inherits from the AgentSwitchboard baseline contract and adds repository-specific rules.

## Required Reading Order

Before proposing or changing work, read in this order:

1. `AGENTS.md` — product-specific billing pipeline rules
2. `HARNESS.md` — this file, the harness doctrine
3. `README.md` and repository-specific operating docs
4. Current plans, handoffs, tests, validators, and recent Git history

## Mandatory Sprint Declaration

Every writing sprint must establish:

- repository and branch or worktree
- lane and mission
- owned scope
- forbidden scope
- dependencies and collision risks
- expected tracked artifacts
- validation commands
- proof ceiling
- commit and PR expectation

If the worktree is dirty and the lane does not own the dirt, preserve it and use an isolated worktree.

## Executable Loop

Every agent action must follow this loop:

```
request -> evidence review -> bounded decision -> repo/Git/GitHub mutation -> artifacts -> validation -> report -> next decision
```

## Operating Discipline

- **Evidence before action.** Inspect the repository, current Git state, relevant contracts, and existing patterns before inventing.
- **Floor before furniture.** Repair unsafe repository state and shared contract gaps before dependent features.
- **Bound the sprint.** State owned scope, forbidden scope, expected artifacts, validation, and proof ceiling.
- **Isolate writers.** One branch and worktree per active writing lane. Never share uncommitted state between agents.
- **Reuse before replacing.** Existing healthy tools, directories, helpers, contracts, and artifacts should be used.
- **Separate skills from code.** Skills describe procedures and judgment. Deterministic behavior belongs in scripts, modules, validators, schemas, registries, and workflows.
- **Treat prompts as artifacts.** Prompts may orchestrate harness operations; they are not the harness.
- **Checkpoint before expansion.** Commit coherent progress before broad validation, expensive runtime proof, or scope growth.
- **Route failures with evidence.** Return exact command output, structured errors, and artifact paths.
- **Do not inflate proof.** Static checks do not prove runtime behavior; synthetic proof does not prove live-target behavior.
- **Protect sensitive data.** Never commit secrets, credentials, personal data, private hostnames, raw customer evidence, huge logs, crash dumps, or machine-local junk.
- **Deliver tracked progress.** When safe and authorized, modify tracked files, validate, commit, push, and open or update a PR.

## Action-Commitment Rule

Any prompt that claims it will install, set up, build, execute, repair, configure, upgrade, deploy, merge, or release something must require the corresponding mutation and proof.

A title or expected output that claims action while the prompt permits acknowledgment, advice, or a plan is invalid.

## Capability and Authority Rule

A tool may perform an action only when all four are true:

1. The environment exposes the capability
2. The capability has been verified in the current environment
3. The task authorizes the action
4. Repository policy does not forbid it

Capability presence is not authority.

## Completion Standard

A task is complete only when the final response and repository state agree about:

- files changed
- generated artifacts and their tracked/untracked policy
- validation actually run
- skipped checks and exact follow-up commands
- commit SHA
- push and PR state
- remaining blockers and risks
- proof level and proof ceiling
- final Git status
- one exact next command

## Forbidden Responses

- acknowledgment only
- summary only
- rewritten prompt only
- plan only
- handoff only
- preflight only
- a request for permission when the bounded mutation is safe

## Operator Source Immutability

Candidates/ and Active/ are read-only operator inputs (backup/emulator files).

- Never write, overwrite, or copy engine output into these paths.
- Never set --output equal to --input.
- All generated workbooks, sidecars, and forensic reports go under Outputs/.
- Overwrites elsewhere require timestamped backup under Outputs/backups/.
- Delivery requires baseline fingerprint compare against the declared source; fail if sheets are deleted.
