# Repo-Local AI Harness Spine v1

This harness acts as a dependable orchestrator for the repository's spreadsheet triage, repair, and generation engines. It guides human operators and AI agents through repeatable workflows, verifies output isolation policies, and compiles structured validation, operator, and handoff reports.

## Structure and Metadata

The harness is driven by repository-local schemas and registries located in the `.ai/` directory:

- [codebase-map.json](file:///C:/Users/Cheex/Desktop/dev/Web%20Excel%20Triage/.ai/codebase-map.json): Maps folder layout to engine domains.
- [workflow-registry.json](file:///C:/Users/Cheex/Desktop/dev/Web%20Excel%20Triage/.ai/workflow-registry.json): Defines the entry-point commands, parameters, validators, and proof ceilings.
- [artifact-registry.json](file:///C:/Users/Cheex/Desktop/dev/Web%20Excel%20Triage/.ai/artifact-registry.json): Declares expected deliverables, paths, and stop-ship validator profiles.
- `schemas/`: Contains JSON schemas for structured metadata output:
  - [run-context.json](file:///C:/Users/Cheex/Desktop/dev/Web%20Excel%20Triage/.ai/schemas/run-context.json)
  - [validation-report.json](file:///C:/Users/Cheex/Desktop/dev/Web%20Excel%20Triage/.ai/schemas/validation-report.json)
  - [operator-report.json](file:///C:/Users/Cheex/Desktop/dev/Web%20Excel%20Triage/.ai/schemas/operator-report.json)
  - [handoff.json](file:///C:/Users/Cheex/Desktop/dev/Web%20Excel%20Triage/.ai/schemas/handoff.json)

---

## Command Surface

Operators and agents invoke the harness through `python -m triage.harness.cli` or using the PowerShell control wrapper:

```powershell
.\scripts\harness.ps1 <command> [args...]
```

### Supported Verbs

1. **`doctor`**: Checks Python dependencies, git environment, and registry integrity.
2. **`workflows`**: Lists all registered workflows in the repository.
3. **`explain <workflow>`**: Describes inputs, outputs, validators, and proof ceiling for a given workflow.
4. **`run <workflow> --key value`**: Runs the workflow script/module, allocating a dated directory under `Outputs/` and recording `run-context.json`.
5. **`validate <run_dir>`**: Runs the registered package and profile validators against the generated files.
6. **`report <run_dir>`**: Produces an English markdown report containing fingerprints, validation results, skipped gates, and git state.
7. **`handoff <run_dir>`**: Summarizes the run for the next session, writing a structured handoff digest.
