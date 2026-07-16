# Package Static Analysis Skill

Use this skill when Web-Excel Repair Triage needs to interpret, compare, or preserve sanitized evidence produced by SysAdminSuite for an EXE, MSI, MST, MSP, archive, installer wrapper, script, shortcut, or configuration package.

## Canonical authority

SysAdminSuite owns package inspection and evidence generation:

- `EndeavorEverlasting/SysAdminSuite`
- `.claude/skills/package-static-analysis/SKILL.md`
- `harness/api/package-static-analysis-skill.json`
- `schemas/harness/package-static-analysis-result.schema.json`
- `tools/package-analysis/analyze_package.py`
- `scripts/Invoke-SasPackageStaticAnalysis.ps1`

This repository may consume sanitized `package_analysis.json` evidence. It must not fork the analyzer or become a second authority for executable behavior.

## Workflow

1. Run the canonical SysAdminSuite analyzer against an operator-local package outside this repository.
2. Keep the package, virtual environment, raw output, and private evidence outside Git.
3. Copy into this repository only a deliberately sanitized evidence fixture when a regression test requires one.
4. Validate the evidence schema version and all static-only proof flags before interpretation.
5. Compare hashes, file classes, indicator counts, parser availability, skipped files, and errors without reconstructing redacted values.
6. Use triage tooling only for sanitized report composition, evidence comparison, issue classification, and durable lessons.
7. Route new analyzer capabilities, parser changes, and package-intake behavior back to SysAdminSuite.
8. Route real installation, rollback, service, reboot, application, or device behavior to a separate authorized VM/runtime lane.

## Data handling

- Never commit private installers, extracted payloads, wheelhouses, raw strings, endpoints, UNC paths, credentials, activation data, or real client configuration.
- Never reverse endpoint fingerprints or enrich them with external lookup.
- Never follow shortcuts or contact package sources from this repository.
- Never mark a package safe, installable, or accepted from static evidence alone.
- Sanitized fixtures must preserve proof flags and structural facts while using fictional names and values.

## Proof ceiling

This skill supports interpretation and triage of static-only evidence. It does not prove Authenticode trust, supported silent arguments, installation success, application launch, service health, reboot behavior, rollback, clinical integration, SSO, or physical-device compatibility.
