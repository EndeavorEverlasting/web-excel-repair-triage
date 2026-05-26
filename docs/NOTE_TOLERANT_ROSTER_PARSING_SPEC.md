# Note-Tolerant Roster Parsing Spec

This spec defines how scripts should parse roster punch cells that contain both time data and human notes.

Users should be able to record operational notes where they work. Code should separate the time signal from the context signal without breaking artifact generation.

## Accepted Input Pattern

A punch cell may contain:

1. a time value
2. optional separator text
3. optional human note

Examples:

```text
9:28:00 AM / Client support
9:28 AM - off-project coverage
17:30 / inventory follow-up
6:00 PM
```

## Required Output Fields

A parser should return a structured result similar to this:

```json
{
  "raw_value": "9:28:00 AM / Client support",
  "parsed_time": "09:28:00",
  "note": "Client support",
  "has_note": true,
  "parse_status": "parsed_with_note"
}
```

## Parse Status Values

| Status | Meaning |
|---|---|
| `parsed_time_only` | Cell contains a usable time and no note |
| `parsed_with_note` | Cell contains a usable time and a preserved note |
| `blank` | Cell is blank |
| `note_only` | Cell has note text but no usable time |
| `invalid_time` | Cell appears intended as a punch but the time cannot be parsed |

## Separators

Scripts should tolerate common separators between a time and a note:

```text
/
-
–
—
|
;
```

Do not require users to use one perfect delimiter.

## Classification Rules

A note may contain useful project signals, but raw notes are evidence, not final authority.

Rules:

1. Use the time portion for hour calculations.
2. Preserve the note portion for internal context.
3. Compare note-derived project signals against resolved worked-project logic.
4. If the note conflicts with the resolved project, create an exception or proposed override.
5. Do not silently reclassify admin output from a raw note alone.
6. Do not expose raw private notes in admin-facing outputs unless explicitly requested.

## Admin Artifact Behavior

Admin generation must continue when a punch cell contains a note.

Valid behavior:

- parse the time
- calculate hours
- classify using resolved rules and approved overrides
- keep raw note out of admin-facing output
- log an internal exception if needed

Invalid behavior:

- crash on note-bearing cells
- treat the entire cell as invalid because it includes a note
- copy private note text into admin output by default
- change project classification from note text without review

## Internal Context Behavior

Internal reports may preserve note text when useful.

Examples:

- exception report
- proposed override report
- task-tracker contextualization
- weekly review notes

These outputs should clearly label notes as source context, not approved classification.

## Pseudocode

```python
def parse_punch_cell(raw_value: object) -> dict:
    if raw_value is None or str(raw_value).strip() == "":
        return {"raw_value": raw_value, "parsed_time": None, "note": None, "has_note": False, "parse_status": "blank"}

    text = str(raw_value).strip()
    time_match = find_first_time_like_token(text)

    if not time_match:
        return {"raw_value": raw_value, "parsed_time": None, "note": text, "has_note": True, "parse_status": "note_only"}

    parsed_time = normalize_time(time_match.group(0))
    note = remove_time_and_leading_separator(text, time_match).strip()

    return {
        "raw_value": raw_value,
        "parsed_time": parsed_time,
        "note": note or None,
        "has_note": bool(note),
        "parse_status": "parsed_with_note" if note else "parsed_time_only",
    }
```

## Test Cases

| Raw value | Parsed time | Note | Status |
|---|---|---|---|
| `9:28:00 AM / Client support` | `09:28:00` | `Client support` | `parsed_with_note` |
| `9:28 AM - off-project coverage` | `09:28:00` | `off-project coverage` | `parsed_with_note` |
| `17:30 / inventory follow-up` | `17:30:00` | `inventory follow-up` | `parsed_with_note` |
| `6:00 PM` | `18:00:00` | null | `parsed_time_only` |
| blank | null | null | `blank` |
| `Client support only` | null | `Client support only` | `note_only` |

## Implementation Standard

Parser utilities should be deterministic and side-effect free.

They should not:

- modify workbooks directly
- decide final project classification alone
- write admin output directly

They should:

- parse raw cells
- return structured data
- preserve notes safely
- feed downstream resolver and exception logic

Tiny parser. Big discipline.
