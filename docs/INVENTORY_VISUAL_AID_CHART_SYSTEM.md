# Inventory Visual Aid Chart System

## Purpose

Inventory workbooks need a visual stock summary. The chart is not decoration. It is a fast sense-check for operators and leadership.

The 1 Marcus recon workbook should preserve a Web Excel-safe stock chart whenever possible.

## Why the attempted pivot chart went sideways

Part numbers are categorical labels. They are not a continuous numeric x-axis.

When a vertical bar chart uses many part numbers as the category axis, Excel prints those discrete labels along the bottom. The result is cramped, unreadable, and easy to mistake for numeric scale noise.

The correct pattern is a horizontal Top-N bar chart:

- category labels on the left
- quantity as the bar length
- sorted descending by quantity
- limited to the top 10 to 15 rows by default

## Chart contract

Machine-readable config:

```text
configs/inventory_visual_aid_chart_v1.json
```

Required posture:

1. Build a bounded helper table for charting.
2. Sort helper rows by quantity descending.
3. Limit the default chart to the top 15 stock lines.
4. Use a horizontal bar chart.
5. Use `PartKeyDisplay` or part key plus short item type as the category label.
6. Keep quantity on the numeric axis.
7. Do not use raw source rows directly when the source contains dozens of part numbers.
8. Do not use a native pivot chart as the primary visual aid for Web Excel-safe outputs.

## 1 Marcus recommended layout

For `1M Recon Pivot Module`:

- helper table: `TopStockChartSource`
- helper columns: `Rank`, `PartKeyDisplay`, `Item Type`, `Qty`
- chart title: `Top stock quantities by part number`
- chart anchor: near `J13`
- chart type: horizontal bar

## Preservation rule

Do not remove a working inventory chart during cleanup or restyling unless it is structurally invalid and causes Web Excel failure.

If the chart must be removed for package safety, the generator must replace it with a safe helper-table visual aid or explicitly report the missing chart as a degraded output.

## Web Excel rules

Allowed:

- standard bar chart
- bounded helper range
- plain formulas or static helper values feeding the chart
- solid style colors from `spreadsheet_style_v1`

Avoid:

- pivot charts
- slicers
- chart references to entire columns
- volatile formula feeds
- chart layouts that are the only place the underlying data appears

## Acceptance criteria

A generated inventory recon workbook should pass when:

- the workbook opens in Excel for Web without repair
- the chart remains visible after save, close, and reopen
- the chart uses a bounded helper range
- part numbers appear as readable left-side category labels
- the quantity axis remains numeric
- workbook formulas and rollup logic do not depend on the chart existing
