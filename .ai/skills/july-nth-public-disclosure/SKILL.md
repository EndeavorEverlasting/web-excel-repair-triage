# July NTH Public-Disclosure Producer Skill

Use this only after FUN has validated a July share-ready workbook with `fun-july-nth-public-disclosure-result/v1`.

## Inputs

- FUN validation JSON;
- the matching FUN July policy JSON;
- the pinned upstream schema lock.

## Procedure

1. Confirm the policy and validation IDs match.
2. Reject missing artifact identity, incomplete counts, upstream failure, any disclosure violation, any math-lock violation, or any scope violation.
3. Produce JSON and Markdown reports without echoing protected workbook text or policy patterns.
4. Fail if the generated report itself matches any protected disclosure rule.
5. Preserve the proof boundary: this report does not independently validate workbook bytes or math.

## Command

```bash
python scripts/report_july_nth_public_disclosure.py \
  artifacts/validation/july-nth-public-disclosure.json \
  --policy packet_profiles/july-2026-admin.public-disclosure-policy.json \
  --json-output artifacts/reports/july-nth-public-disclosure.json \
  --markdown-output artifacts/reports/july-nth-public-disclosure.md
```

## Delivery gate

A July admin workbook is not ready for delivery unless the FUN validation and triage producer report both state `PASS` and the existing math/artifact checks also pass.
