---
description: Inspect the repo harness: codebase map, validators, known traps, workflow specs
agent: build
---

Inspect the repository harness to understand structure, workflows, and pitfalls.

## Usage

- `/harness-inspect` — show full harness summary
- `/harness-inspect modules` — show module map
- `/harness-inspect traps` — show known traps
- `/harness-inspect validators` — show validator catalog
- `/harness-inspect workflows` — show workflow directions

## Output

Read and summarize the relevant harness file based on $ARGUMENTS:

- No args or "summary": read `.ai/codebase_map.json`, `.ai/known_traps.json`, `.ai/validators.json`
- "modules": read `.ai/codebase_map.json` and list all core_modules and sub_packages
- "traps": read `.ai/known_traps.json` and list all traps with status
- "validators": read `.ai/validators.json` and list all validators with commands
- "workflows": read `AGENTS.md` and list workflow directions with rules
