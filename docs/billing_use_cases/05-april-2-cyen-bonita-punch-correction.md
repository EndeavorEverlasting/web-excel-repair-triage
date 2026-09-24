# Use Case: April 2 Cyen Bonita Punch Correction

Captured: 2026-06-03

## Problem

Cyen had a note-bearing Bonita punch on April 2. The intended correction was that the row should be parsed as a normal workday with Bonita/Neuron project context, not misread as an accidental 6:00 AM clock-out.

The exact operational lesson is date-specific and name-specific:

- Staff: Cyen
- Date: April 2, 2026
- Project signal: Bonita
- Failure mode: interpreting a note-bearing `6:00 PM / Bonita` style value as 6:00 AM or malformed text

## Required behavior

The roster parser must accept note-bearing punch text as valid input when it contains a valid time.

Examples that should parse:

```text
9:00 AM / Bonita
6:00 PM / Bonita
9:00:00 AM / Bonita
6:00:00 PM / Bonita
```

## Parsing rule

Separate the time token from the note token.

Return structured fields:

```text
raw_value
parsed_time
note
has_note
parse_status
project_signal
```

Recommended statuses:

```text
parsed_time_only
parsed_with_note
blank
note_only
invalid_time
```

## Billing rule

A valid time with a note must not be rejected merely because the cell contains note text. The note should be preserved for internal review and may supply project evidence, but final project assignment still follows resolved project logic and approved overrides.

## Test expectations

Synthetic tests should cover:

- `9:00 AM / Bonita`
- `6:00 PM / Bonita`
- `9:00:00 AM / Bonita`
- `6:00:00 PM / Bonita`
- lowercase/uppercase note variants
- invalid time with note
- note-only cell

## Regression guard

April 2, 2026 Cyen Bonita work must not be converted into a 6:00 AM clock-out in generated billing summaries.
