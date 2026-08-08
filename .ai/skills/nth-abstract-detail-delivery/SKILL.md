# NTH Abstract-Detail Delivery

## Trigger

Use when an NTH workbook, Math Packet, administrative summary, chart, or artifact report contains technician-level evidence and is approaching share review or FUN acceptance.

## Mission

Preserve the detail while keeping the document centered on workstreams rather than people.

## Contract

- Identity may appear in ordinary attendance or dated work identity columns.
- A normal row may describe the person's work in the same format as every other row.
- Titles, KPI cards, summaries, charts, controls, notes, definitions, posture text, defenses, and reports remain abstract.
- A special bucket, reconciliation KPI, clock narrative, or named exception built around one technician is a regression.
- Internal identity exceptions require an exact FUN policy cell and a material-authority reason.

## Producer workflow

1. Resolve the final workbook bytes and audience.
2. Resolve the matching FUN `fun-nth-identity-abstraction-policy/v1` policy.
3. Confirm that every allowed name range is an ordinary identity column or an explicit identity-critical exception.
4. Rewrite higher-level text around the workstream, date window, evidence class, scope boundary, and proof ceiling.
5. Run the FUN identity-abstraction validator against actual XLSX bytes.
6. Feed the result to:

   ```text
   python scripts/report_nth_identity_abstraction.py \
     --validation <identity-abstraction-result.json> \
     --policy <identity-policy.json> \
     --json-out <abstract-detail-report.json> \
     --markdown-out <abstract-detail-report.md>
   ```

7. Require report PASS before artifact-manifest export or delivery.
8. Preserve the JSON and Markdown report beside the manifest and producer receipt.

## May 26–29 recall

- Configuration and technical readiness are the subject of the allocation.
- Normal technician rows and normal technician-total identity columns may keep names.
- State excluded project-team work as a scope boundary without making the excluded person the subject.
- Do not publish `Extended NTH Coverage`, a one-person reconciliation KPI, a named clock model, or a named Friday boundary.
- Keep `38 remaining` as testing/IDT, never a labor multiplier.
- Do not create a device productivity KPI.

## PASS evidence

Report:

- artifact filename, size, SHA-256, and type;
- policy ID;
- identities scanned count;
- allowed ordinary-row occurrence count;
- identity, special-label, and package-surface violation counts;
- final disposition;
- proof ceiling.

Never repeat scanned identity tokens in the report or handoff.
