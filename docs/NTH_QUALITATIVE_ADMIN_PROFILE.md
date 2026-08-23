# Neuron Track Hours Qualitative Admin Workbook Profile

This is the demand-loaded contract for the current **admin / management Neuron Track Hours workbook family**. It is separate from the older working/review workbook produced by `triage.nth_monthly_artifact`.

Use it when the requested deliverable should match the mature qualitative presentation established by the June 2026 completed-month and August 2026 MTD admin-share workbooks.

Machine authority: `configs/artifact_profiles/nth_qualitative_admin.v1.json`.
Generator: `python scripts/build_nth_qualitative_admin.py --spec <evidence.json> --out-dir Outputs/nth-qualitative-admin`.

## Authority boundary

The reference workbooks were inspected on 2026-08-19 to extract **structure, style, package, and language posture only**. Their workbook bytes are not committed and they are never runtime evidence inputs.

The committed profile stores only their SHA-256 fingerprints and structural observations. Direct `detail_rows` supplied to the generator remain the quantitative evidence packet:

- `total_paid_hours = sum(detail_rows.paid_hours)`;
- `completed_shift_records = count(detail_rows)`;
- technician totals/counts are grouped from those same rows;
- daily totals/counts are grouped from those same rows;
- caller-supplied totals are not accepted;
- planned/carryover rows remain `0` paid hours until completed attendance exists.

When the evidence packet itself was derived from the roster, the roster/source contract remains responsible for proving those detail rows. This profile does not turn a visual reference into attendance authority.

## Two canonical modes

### Completed month

Sheet order is exact:

1. `Executive Dashboard`
2. `Visual Summary`
3. `{Month YYYY} NTH Detail`
4. `Operational Themes`
5. `Billing Support Context`

Dashboard KPIs are `RECORDED NTH`, `SHIFT RECORDS`, `PRIOR BASELINE`, and `BILLING STATUS`. The current total and shift count are always derived. If a prior baseline is supplied, billing status is computed as `ALIGNED` or `REVIEW`; it is not a caller-authored conclusion.

### Month to date

Sheet order is exact:

1. `Executive Dashboard`
2. `Visual Summary`
3. `{Month YYYY} NTH Detail`
4. `Operational Themes`
5. `Carryover & Planned Work`
6. `Configuration & Inventory Context`

Dashboard KPIs are `MTD PAID HOURS`, `COMPLETED SHIFTS`, `THROUGH`, `MTD STATUS`, and the planned-day label such as `AUG 19`. Planned work is displayed as `PLANNED — NOT POSTED` and the planned/carryover sheet cannot contain nonzero posted paid hours.

## Stable visual contract

The current June/August family uses the same visual language:

- font family: **Carlito**;
- title: 16 pt bold white on navy;
- subtitle: 10 pt italic gray;
- section titles: 11 pt bold white on navy;
- KPI labels: 9 pt bold white;
- KPI values: 14 pt bold;
- body: 11 pt;
- total rows: bold light green;
- title row height: 30;
- default row height: 15.

Palette:

- navy `#173B5C`;
- subtitle gray `#4B5563`;
- body dark `#1F2937`;
- light gray `#F3F5F7`;
- light blue `#DCEAF7`;
- success green `#DDEED9`;
- attention yellow `#FFF1BF`;
- white `#FFFFFF`.

Number formats are `0.00` for hours and `m/d/yyyy` for dates. Exact style IDs and widths are tracked by the machine profile. `styles.xml` is generated from the compact canonical style registry in `triage/nth_qualitative_admin/style_template.py`; the shared `theme1.xml` remains a style-only template asset.

## Formula and OOXML contract

The current June and August references contain **zero worksheet formulas**. Do not add formulas merely because totals are derived. The generator performs the equations before serialization and writes values.

The accepted package is intentionally small:

- workbook + workbook relationships;
- styles;
- theme;
- **present but empty** `sharedStrings.xml`;
- one worksheet XML part per visible sheet;
- root relationships and content types.

The profile rejects calc chains, external links, drawings/charts, tables, pivots, connections, worksheet formulas, auto-filters, conditional formatting, data validation, drawings, and freeze panes because those structures are absent from the current accepted family. Strings are written directly as worksheet `t="str"` values, matching the references.

The generated style table and committed `theme1.xml` contain no attendance rows, technician names, management narratives, workbook cell values, or private source data. The style registry retains the reference family’s used style IDs, Carlito fonts, palette, alignments, and number formats without committing the opaque full donor style part.

## Language posture by surface

The workbook is deliberately **quantitative for direct paid attendance and qualitative for workstream interpretation**.

`Visual Summary` subtitle is fixed:

> Direct paid hours and completed shift records only. No percentage, peak, ranking, or inferred workstream-hour metrics.

Detail subtitle is fixed:

> Direct paid-hour rows with qualitative work context. The program label is neutral; workstream identity comes from the dated context.

Operational Themes subtitle is fixed:

> Themes may overlap within a paid shift. They explain the service delivered; they are not an invented hours allocation.

Completed-month Billing Support subtitle is fixed:

> Management context for explaining the service model. Direct paid attendance remains the quantitative authority.

MTD carryover subtitle is fixed:

> Planned and carryover context stays visible without creating paid hours.

MTD technical-scope subtitle is fixed:

> Technical scope controls bound claims. They do not allocate paid hours across workstreams.

The generator rejects unsupported percentage/ranking/peak language unless that narrative row explicitly declares direct quantitative evidence. It also rejects apparent task/workstream-hour allocations in detail narratives unless the row explicitly declares direct task/time evidence.

The automatic final executive rule is mode-specific:

- completed month: `Use paid hours by date/technician as the quantitative record. Describe workstreams qualitatively unless direct task/time evidence supports a split.`
- MTD: `Admin reporting stays quantitative for paid attendance and qualitative for workstream context; no task-hour split is inferred.`

## Input packet

Input is JSON with schema `nth-qualitative-admin-input/v1`. See:

- `configs/examples/nth_qualitative_admin_completed.synthetic.json`;
- `configs/examples/nth_qualitative_admin_mtd.synthetic.json`.

Required common fields include `mode`, `month_key`, `artifact_date`, `detail_rows`, `operational_themes`, and the applicable management context. `tracked_technicians` may include a technician with zero current hours so the management view can preserve an explicit tracked roster without manufacturing a shift.

Completed-month mode additionally requires `billing_support_context` and `external_use_boundary`; `prior_baseline` is optional.

MTD additionally requires `through_date`, `planned_date`, `mtd_status`, `carryover_planned_work`, `technical_scope_context`, and `technical_scope_closing_note`.

## Output and proof

The canonical filename family is generated automatically:

- `ADMIN_SHARE_NTH_<Month>_<Year>_QUALITATIVE_CURRENT_<artifact-date>.xlsx`;
- `ADMIN_SHARE_NTH_<Month>_<Year>_MTD_QUALITATIVE_CURRENT_<artifact-date>.xlsx`.

Each run emits workbook, `.manifest.json`, and `.validation.json` under the chosen output directory. Repository-local output directories must remain under `Outputs/`; `Candidates/`, `Active/`, and other repository paths are not output destinations.

Static validation proves package membership, canonical generated-style/theme identity, empty shared strings, zero formulas, sheet order, widths, row-height controls, fixed language posture, and detail-row count reconciliation. It does **not** prove that the evidence packet was correctly derived from private attendance, FUN acceptance, Excel/client acceptance, or any unsupported historical billing claim.
