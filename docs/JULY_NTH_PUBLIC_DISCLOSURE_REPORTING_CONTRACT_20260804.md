# July NTH Public-Disclosure Reporting Contract

## Purpose

Triage consumes the FUN July public-disclosure result and produces a share-readiness report without repeating the protected language that caused the failure.

This integration applies only to the July share-ready NTH workbook family.

## Upstream authority

FUN remains authoritative for:

- reading the actual XLSX package;
- applying the July-only forbidden-disclosure rules;
- checking required sheets and filename scope;
- checking the locked July numeric cells;
- issuing `fun-july-nth-public-disclosure-result/v1`.

Triage does not reinterpret workbook text or change the allocation.

## Fail-closed rules

The producer report fails when:

- the FUN schema or policy ID is wrong;
- the upstream result is not `PASS`;
- any cell or package disclosure violation exists;
- any locked numeric cell changed;
- the artifact falls outside the July scope;
- the validation result is incomplete;
- the report itself matches a protected disclosure rule.

## Output posture

Reports may identify a rule ID and workbook location. They do not echo the matched private sentence, pattern, rationale, stakeholder name, or evidence detail.

## Required outputs

- JSON: `triage-july-nth-public-disclosure-report/v1`;
- Markdown disposition report;
- artifact filename, size, and SHA-256;
- rule, package, math-lock, and scope violation counts;
- PASS or FAIL.

## Proof ceiling

The report confirms that a complete passing FUN result was received and safely summarized. It does not independently prove workbook math, attendance truth, payroll compliance, legal conclusions, or admin acceptance.
