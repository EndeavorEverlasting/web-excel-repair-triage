# Neuron Track Hours Monthly Artifact

## Trigger

Use this skill when a Neuron Track Hours workbook must be constructed, repaired, analyzed, audited, or reduced to a client-facing send copy. Route through `harness/nth/triggers.v1.json` and load the active month from `harness/nth/monthly-rule-packs.v1.json` before task attribution or final packaging.

Do not use a prior month's rule pack by habit. Do not use client-facing mode as the working source of truth.

## Required inputs

- Canonical repository governance in `AGENTS.md`.
- `harness/nth/manifest.v1.json` and `harness/nth/monthly-rule-packs.v1.json`.
- The roster/attendance source for the covered period.
- The internal NTH workbook or the source evidence needed to construct it.
- Explicit date/person evidence and operator-confirmed facts.
- The requested delivery mode: `internal` or `client`.
- For client mode, a validated internal workbook and the active month client tab contract.

## Outputs

- **Internal mode:** a complete working NTH artifact with the evidence and supporting surfaces needed to audit attendance, task attribution, exceptions, and delivery decisions.
- **Client mode:** a narrowed send copy derived from the validated internal workbook, containing only the active month's approved client tabs.
- A validation result proving attendance totals, task-distribution rules, mode contract, and client/internal parity appropriate to the requested output.
- A handoff naming the active month rule pack, source attendance, artifacts, checks run, proof ceiling, and exact next action.

## Procedure

1. Read `AGENTS.md`, the NTH harness manifest, the active month rule pack, and the NTH workflow before touching a workbook.
2. Resolve the covered month and refuse silent carry-forward from an older month. When the active month lacks a confirmed rule pack, preserve attendance truth and stop task-allocation assumptions at the explicit evidence available.
3. Establish the roster/attendance total first. Device counts, configured-device capacity, deployment counts, or site throughput may support context but never create labor hours.
4. Apply evidence precedence in order: explicit date/person evidence and operator-confirmed facts; active month rule pack and role cadence; aggregate allocation guardrail; general fallback assumptions.
5. Assign one dominant primary workstream to each paid shift. Complimentary work may describe concurrent work across other workstreams, but it must not create or duplicate paid hours.
6. Keep Configuration and Deployment distinct. Treat PM / Operational Control as real work only when it dominates the period, and do not mechanically spread Rich's client/PM/ticket workload to technicians.
7. Apply the active month's aggregate allocation only as a reasonableness test. Never reclassify stronger evidenced work solely to force a target ratio.
8. In July 2026, enforce the June-26-forward 60% Configuration / 40% other-work guardrail, Rich's one full Client Correspondence / Coordination day per week usually on Thursday, the known July 2 and July 23 anchors, the July 3 holiday, the July 10 mixed operational day, and Alejandro Perales' zero scheduled project hours on July 24.
9. Build and validate **internal mode first** during construction, repair, analysis, or audit. Preserve the complete supporting workbook and internal evidence surfaces needed to prove the result.
10. Create **client mode only as a derived copy** of a validated internal workbook. For July 2026, the delivered workbook must contain exactly `Executive Summary` and `July 2026`; internal-only sheets are omitted, not merely hidden.
11. Before client delivery, compare internal and client artifacts for the same attendance totals, dates, primary-workstream truth, and governed task attribution. Reducing detail must not invent a different operational story.
12. Keep management-facing surfaces free of internal percentages, allocation mechanics, confidence/evidence-posture jargon, task ledgers, methodology, validation, doctrine, and forensic machinery unless the operator explicitly promotes a specific item.
13. Treat historical attribution questions as reviews unless the historical source was actually mutated. Do not call an unchanged historical workbook reconciled, corrected, revised, or updated.
14. Run the NTH harness validator, NTH contract tests, root harness validator, focused workbook checks applicable to the artifact, repository hygiene, and `git diff --check`. Report skipped runtime checks honestly.

## Guardrails

- Never write generated workbooks, reports, or evidence into `Candidates/` or `Active/`.
- Never overwrite a historical source workbook merely to make current categorization cleaner.
- Never create hours from device counts, projections, capacity, or task percentages.
- Never duplicate a shift across primary and complimentary work.
- Never force the aggregate allocation ratio over stronger date/person evidence.
- Never manufacture multiple full correspondence days in one week because client work appears in supporting notes.
- Never ship the internal workbook as the client copy when the active month has a narrower delivery contract.
- Never hide internal-only sheets as a substitute for removing them from the client package.
- Never claim Excel for Web, client acceptance, or historical-source correctness from static repository checks alone.

## Validation

Run the domain harness gates first:

```powershell
python scripts\validate_nth_harness.py
python -m unittest tests.test_nth_harness_contract -v
```

Then run the root harness and repository hygiene gates:

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m triage.gitignore_hygiene
git diff --check
```

For a concrete workbook, also run the focused workbook/artifact validators owned by that artifact family and record the exact artifact paths and results. A client copy is not validated merely because its internal source passed; cross-mode parity and the active client tab contract must also be checked.

## Proof ceiling

This skill and its repository contracts prove that agents can resolve the active NTH month, apply the governed attribution order, distinguish internal and client delivery modes, enforce July's known task-distribution and exception rules, and fail closed on missing rule-pack or delivery prerequisites. They do not by themselves prove that a generated workbook opens cleanly in Excel for Web, that a client accepts it, that timestamp-level subtask reconstruction is historically exact, or that an unchanged historical workbook was corrected.
