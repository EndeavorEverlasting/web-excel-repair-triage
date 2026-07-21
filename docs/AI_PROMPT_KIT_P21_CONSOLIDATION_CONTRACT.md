# AI Prompt Kit P21 Consolidation Contract

Date: 2026-07-14

## Identity

- Prompt ID: `P21`
- Copy-safe sheet: `P21_COPY_SAFE`
- Name: `Many-to-One Prompt Consolidator`
- Type: `CONSOLIDATE + EXECUTE`
- Class: `PLAN + BUILD / CONSOLIDATE`
- Operational color: `Amber`

P21 accepts several prompts, handoffs, instructions, sprint candidates, or artifact requirements and produces one bounded execution mission. It performs requirement analysis and conflict resolution. It is not a concatenator and must not emit another giant multi-sprint prompt.

## Requirement disposition ledger

Every source requirement receives exactly one disposition:

- `included`
- `merged`
- `deferred-to-docs`
- `superseded`
- `rejected-with-reason`
- `unresolved-blocker`

No source requirement may disappear silently. Merged and superseded entries identify the surviving requirement. Rejected and blocked entries carry an evidence-backed reason.

## Required output sections

The consolidated execution prompt contains these headings exactly:

```text
MISSION
SOURCE PROMPT DISPOSITION
CONFLICT RESOLUTION
IMMEDIATE OWNED SCOPE
FORBIDDEN SCOPE
REPOSITORY EVIDENCE REQUIRED
EXECUTION CONTRACT
VALIDATION
DEFERRED DOCUMENTATION BRANCH
FINAL HANDOFF
```

The deferred documentation lane records the proposed branch or PR lane, mission, owned scope, forbidden scope, target files, evidence sources, expected artifacts, validation, dependency on the immediate sprint, and parallel-safety statement. Branch naming is derived from the target repository's existing conventions.

## Artifact execution mode

When the source material describes a workbook, document, slide deck, archive, report, image, or other artifact, P21 requires generation of the actual artifact when the current environment has the source and tools. It preserves fixture names and hashes, requested filenames, package constraints, previews, field gates, and artifact links. An accepted structural fixture must not be replaced with a blank regenerated package.

## Proof contract

P21 preserves the strongest compatible safety and proof rules from the sources. Static checks are not reported as field acceptance. The final handoff names completed work, artifacts, validation, skipped checks, gaps, git state, remote or PR state, the exact next command, and a copy-paste handoff.
