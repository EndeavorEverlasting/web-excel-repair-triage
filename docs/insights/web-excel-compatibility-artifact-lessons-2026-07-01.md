# Web Excel Compatibility Artifact Lessons — 2026-07-01

## Context

These notes codify Web Excel compatibility insights uncovered during the June 2026 billing and Neuron Track Hours artifact repairs.

The key lesson is that Excel Web compatibility is not proven by any one of these signals alone:

- ZIP package opens
- workbook imports locally
- workbook renders as an image
- desktop Excel can repair the file
- screenshots look correct

Those are necessary checks, not acceptance.

## Primary insight

A workbook can be a valid `.xlsx` ZIP and still fail before Web Excel can offer a useful repair.

The failure mode is usually package-shape drift: content types, relationships, chart/drawing parts, tables, shared strings, calculation state, or XML serialization changed away from the known-good path.

When Web Excel refuses to open or refuses to attempt repair, do not treat it as a cosmetic formatting issue. Treat it as an OOXML package failure.

## Compatibility insights from the repair pass

| Insight | Operational consequence |
|---|---|
| Valid ZIP is not enough. | Always inspect package parts and XML, not only `zipfile.testzip()`. |
| Local import/render is not enough. | Local tools can tolerate structures that Web Excel rejects or silently repairs. |
| Known-good workbook shape has value. | Prefer in-place mutation of accepted artifacts over full regeneration. |
| Relationship targets matter. | Audit `.rels` files for targets that do not resolve inside the package and for unexpected absolute internal targets. |
| Content types are a gate. | `[Content_Types].xml` must declare safe defaults and explicit workbook overrides. |
| Chart/drawing topology is fragile. | Do not move chart parts or drawing relationship paths unless performing a structural migration. |
| Tables are structural, not decorative. | Duplicate names, stale refs, or mismatched table relationships are stop-ship risks. |
| Calc chain is stale after programmatic edits. | Remove `xl/calcChain.xml` from generated or repaired artifacts. |
| Shared string strategy should not drift casually. | Text storage changes can create avoidable package churn. |
| Formula compatibility tokens are package-level signals. | `_xlfn`, `_xlws`, `_xludf`, `AGGREGATE`, dynamic arrays, and formula errors are stop-ship unless explicitly contained and accepted. |
| One-tab user scope is a structural constraint. | If only one tab needs adjustment, unrelated workbook XML must remain stable or the change needs justification. |

## Relationship-target audit

During workbook triage, relationship integrity must be validated beyond simple ZIP checks.

For every `.rels` part:

1. Ignore explicitly external relationships.
2. Resolve internal targets against the relationship source part.
3. Confirm the resolved package part exists.
4. Flag targets that escape the package root.
5. Flag unexpected absolute internal targets as package-shape drift unless the workbook family has already proven that pattern safe.

This is especially important for drawing/chart relationships, workbook-to-sheet relationships, table relationships, and root package relationships.

## Field-judge rule

Excel Web is the field judge.

A candidate is not accepted until:

1. package checks pass,
2. target sheets render correctly,
3. non-target sheets remain stable,
4. Excel Web opens without repair or refusal.

If Excel Web repairs the file, the artifact is failed. If Excel Web refuses to repair, the artifact is a package failure until proven otherwise.

## Artifact repair posture

When a workbook fails Web Excel:

1. Preserve the failing candidate for autopsy.
2. Compare it against the last accepted workbook.
3. Identify package part drift before changing business logic.
4. Prefer reverting to the accepted package structure and reapplying only the intended value/style deltas.
5. Record the resulting package manifest.

## June 2026 examples

### Billing summary artifact

The initial handoff used a sloppy filename and weak compatibility proof. A clean filename was not enough; the artifact needed package inspection and a stricter Web Excel posture.

Lesson:

- user-facing filenames matter, but package structure matters more.
- `zipfile.testzip()` is not a meaningful Web Excel acceptance gate by itself.

### Neuron Track Hours artifact

The correct path was to start from the last good workbook and update the June 2026 task-tracking tab while preserving the rest of the workbook.

Lesson:

- a one-tab formatting request is not permission to regenerate the full workbook.
- visual parity with April/May must be paired with package-shape preservation.

### Executive summary cleanup

Removing executive-facing reconciliation residue was a content fix, but it should not disturb workbook structure.

Lesson:

- dashboard text changes are value/content mutations.
- they should not introduce structural churn in charts, tables, relationships, or content types.

## Stop-ship expansion

Add these as Web Excel stop-ship or review-gate signals:

- valid ZIP but Web Excel refuses repair
- missing relationship target
- relationship target resolves outside package root
- unexpected absolute internal relationship target
- chart relationship without chart part
- chart part under unexpected drawing subpath
- bad or missing workbook content type override
- stale `calcChain.xml`
- duplicate table names
- namespace pollution from serializer output
- package contains formula error text

## Acceptance sentence

A Web Excel-safe artifact is not merely a workbook that opens somewhere. It is a workbook whose data, visual surface, and OOXML package shape remain inside the known-good compatibility lane.
