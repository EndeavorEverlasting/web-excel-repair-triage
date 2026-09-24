# Billing Summary Text Quality

## Scope

This document applies to leadership-facing billing summaries and project-hours exports.

It does not apply to the internal admin log copy format-preservation workflow.

## Rule

Billing-summary text must be complete, human-readable, and leadership-safe.

Do not ship truncated generated text.

Work Context fields must not contain ellipses or mid-word clipped text. A value such as `Provided operating control, reporting, tracker maintenance, and configuration...` is broken output, not a usable summary.

## Work Context standard

Each Work Context value should be a complete phrase or sentence that explains what the hours supported.

Good examples:

```text
Operating Control / Reporting / Tracker / Configuration Support: Provided operating control, reporting, tracker maintenance, and configuration support.
Configuration / inventory support: Provided weekday coverage for configuration support, staging, and inventory control.
Project control / reporting / tracker closeout: Provided project control, reporting, tracker closeout, and limited client-facing coordination.
Configuration workflow / inventory control / QA readiness / ticket follow-through: Supported Cybernet configuration, inventory organization, QA readiness, and ticket follow-through.
```

## Forbidden visible text markers

Fail the artifact if any leadership-facing workbook contains visible text markers that indicate unfinished output, including ellipses, mid-word clipping, to-be-completed labels, or draft filler.

The rule applies especially to:

- Tracker Import tabs,
- Work Context columns,
- Context Reason columns,
- Project Hours exports,
- executive/admin summary notes,
- chart captions if present.

## Required validation

Before exporting a billing summary, scan all visible sheets for truncation markers and unfinished text.

Suggested Python validation:

```python
FORBIDDEN_TEXT_TOKENS = ["...", "…", "TBD", "TODO", "context goes here"]


def scan_for_forbidden_text(workbook) -> list[dict]:
    hits = []
    for ws in workbook.worksheets:
        if getattr(ws, "sheet_state", "visible") != "visible":
            continue
        for row in ws.iter_rows():
            for cell in row:
                value = str(cell.value or "")
                for token in FORBIDDEN_TEXT_TOKENS:
                    if token.lower() in value.lower():
                        hits.append({
                            "sheet": ws.title,
                            "cell": cell.coordinate,
                            "token": token,
                            "value": value,
                        })
    return hits
```

If this scan returns hits, the generator must stop and require correction before the workbook is blessed.

## Stop-ship checks

Do not send a leadership-facing billing summary if:

- Work Context text is truncated,
- an ellipsis appears in visible workbook text,
- generated context is cut mid-word,
- generic labels replace actual task context,
- the workbook has charts but the underlying context text is sloppy,
- or the workbook passes structural validation but fails human-readable review.

## Relationship to visual quality

Charts help, but they do not excuse weak text.

A charted workbook with truncated Work Context is still failed output.

The operator should be able to open the Tracker Import tab and understand why each row was included without guessing what a clipped sentence was supposed to say.
