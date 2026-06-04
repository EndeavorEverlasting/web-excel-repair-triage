# Admin Log Project Team Company-Style Contract

This contract captures the accepted presentation rules for the NW PRJ Tech Hours / Admin Log `Project Team` artifact.

The data authority is the active roster log. A prior admin workbook may be used as a visual donor only. Outdated donor values must not be treated as truth.

## Artifact purpose

Generate a holdover admin log that is professional enough to send while access to the live admin log is unavailable.

The workbook should look like the company admin-log family, not like a generic generated spreadsheet.

## Sheet contract

- Workbook contains one visible sheet: `Project Team`.
- Date coverage includes April 1, 2026 through May 31, 2026 unless explicitly scoped otherwise.
- April 1-5 must be included even if the visual donor starts later.
- Roster-log attendance data replaces stale donor values.
- No internal tool notes, build notes, source descriptions, or explanatory metadata may appear in the worksheet.
- Sidecars may contain build details. The workbook itself should remain clean.

## Top-left visual rules

These rules came from manual acceptance of the latest company-emulated artifact:

1. Column A is hidden, not deleted.
2. Agilant logos appear visually in the top-left logo region around `B1:B3`.
3. Logo cells should be aesthetically fitted inside the top rows.
4. The top logo region should match the donor workbook's visual mechanics as closely as possible.
5. Do not replace the logo area with invented text.

## Freeze-pane rule

Manual acceptance confirmed this behavior:

- Do not freeze the default generated header rows.
- Freeze visible Column B only.
- Because Column A is hidden, the practical Excel setting should freeze panes at `C1`, preserving Column B as the visible frozen column.

This makes horizontal scrolling usable while avoiding the awkward generated freeze pane that locked the wrong cells.

## Formatting expectations

The generated `Project Team` sheet should preserve the company-style rhythm:

- weekly blocks;
- dark separator bands;
- blue headers;
- pale subheaders;
- bordered grid;
- total rows;
- PM rows where present in the donor format;
- professional spacing without dead blank areas unless they are part of the accepted donor logo/header region.

## Data rules

- The roster log is the data source.
- The donor workbook is only a style/reference source.
- Status markers such as PTO, OFF, OUT SICK, N/A, and NON-PTO may be preserved when they appear in the roster source.
- Do not infer or invent top-of-sheet content.
- Do not expose internal automation details inside the workbook.

## Validation rules

Before submission, the candidate workbook must pass:

- workbook opens locally;
- Excel for Web opens without repair prompt;
- no `WORKBOOK REPAIRED` banner;
- no `inlineStr`, `#REF!`, `ns0:`, or unsupported formula tokens;
- `xl/sharedStrings.xml` exists when shared string references exist;
- visual check confirms Column A hidden, logos fitted in `B1:B3`, and visible Column B frozen.
