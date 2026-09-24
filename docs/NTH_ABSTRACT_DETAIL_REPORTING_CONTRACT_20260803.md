# NTH Abstract-Detail Producer Reporting Contract

## Cross-repository seam

`EndeavorEverlasting/FUN` owns the evidence and acceptance doctrine for keeping administrative workbook details abstract. `web-excel-repair-triage` owns producer-side preflight and report generation.

The producer must not rely on an operator or future agent remembering the preferred wording. It must carry the FUN identity-abstraction policy with the workbook, run the FUN-compatible validator against actual XLSX bytes, and emit a report that fails closed.

## Required posture

- Technician identity is allowed in ordinary attendance or dated work identity columns.
- A normal work row may describe the technician's work using the same structure as every other row.
- Titles, subtitles, KPI cards, charts, summaries, controls, notes, administrative definitions, presentation posture, workstream defenses, and reports describe the workstream and evidence boundary instead of the person.
- A special workstream, audit bucket, reconciliation KPI, clock narrative, or boundary created around one technician is a regression.
- Internal evidence may use a named exception only when FUN policy explicitly allows the exact cell and records why identity is material.

## Producer loop

1. Resolve the final workbook bytes and intended audience.
2. Resolve the matching `fun-nth-identity-abstraction-policy/v1` policy.
3. Build or repair the workbook with names confined to ordinary identity columns.
4. Run FUN's identity-abstraction validator or a byte-equivalent pinned implementation.
5. Feed the `fun-nth-identity-abstraction-result/v1` JSON to `scripts/report_nth_identity_abstraction.py`.
6. Require a PASS report before emitting the FUN artifact manifest or presenting the workbook for delivery.
7. Preserve the report with the artifact manifest and producer receipt.

## Report requirements

The report contains:

- artifact filename, size, SHA-256, and artifact type;
- policy identifier;
- count of identities scanned;
- count of allowed ordinary-row identity occurrences;
- count of identity violations;
- count of special-case-label violations;
- count of chart/drawing/package identity violations;
- PASS or FAIL disposition;
- proof ceiling.

The report never repeats the scanned identity tokens. Locations may be reported as sheet/cell or package part. This keeps the triage report itself aligned with the workbook posture.

## May 26–29 recall

The accepted delivery pattern is:

- Configuration and technical readiness are the subject of the allocation, not a technician;
- normal technician rows and normal technician-total name columns may retain names;
- excluded project-team scope is stated as a scope boundary without turning the excluded person into a note or control;
- no `Extended NTH Coverage`, one-person reconciliation KPI, named clock model, or named Friday boundary appears on the administrative surface;
- `38 remaining` remains testing/IDT and is not a labor multiplier;
- no device-throughput KPI is created.

## Failure behavior

The producer report is FAIL when:

- the upstream validation result is missing, malformed, or not PASS;
- policy identifiers do not match;
- any identity appears outside an approved range;
- any identity is cached in a chart, drawing, comment, or other non-cell package surface;
- any forbidden special-case label appears;
- required counts or artifact identity fields are absent.

A failed report blocks delivery. It does not silently downgrade to a warning.

## Proof ceiling

This producer report proves that the supplied validation result satisfies the abstract-detail delivery contract. It does not independently prove workbook bytes, evidence truth, attendance truth, allocation truth, or client acceptance; those remain with the FUN validator and existing artifact/evidence harnesses.
