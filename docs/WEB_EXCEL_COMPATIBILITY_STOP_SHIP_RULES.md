# Web Excel Compatibility — STOP-SHIP Rules (NW PRJ Dashboard)

## Failed artifact rule

```text
If Excel for Web repairs the workbook, the artifact is failed.
Do not bless it.
Do not continue from it without labeling it as a repaired source.
Rebuild clean if possible.
```

## Filename STOP-SHIP

Reject outputs or inputs when the basename contains:

- `repaired_`
- `Deprecated_repaired_`
- `web_repaired_` (legacy local pattern)

## Package STOP-SHIP tokens

Scan all XML parts (see `configs/web_excel_stop_ship_tokens.json`):

| Token / pattern | Why |
| --- | --- |
| `_xlfn.` | Unsupported function namespace |
| `_xludf.` | User-defined function leakage |
| `_xlpm.` | Lambda / PM namespace |
| `AGGREGATE(` | Known Web hazard |
| `#REF!` | Broken references (especially CF) |
| `#VALUE!` | Eval errors in stored XML |
| `#NAME?` | Unknown names |

## Structural STOP-SHIP

| Check | Failure |
| --- | --- |
| XML parse | Any `.xml` part fails `ElementTree` parse |
| Relationship targets | `.rels` Target does not resolve in package |
| Duplicate table names | Two `table` parts share `displayName` or `name` |
| R1C1 CF leakage | `RC\d` in `<f>` inside conditional formatting |
| Missing `CF_Dictionary` | NW PRJ dashboard profile detected, sheet absent |
| Column A override | Done row still matches queue-amber CF only |

## Excel Web repair symptoms

- File opens as repaired
- Filename becomes `Deprecated_repaired_...`
- Excel Web refuses to repair
- Tables disappear
- CF behaves but workbook structure is poisoned

**Likely causes:** duplicate tables, broken worksheet relationships, table relationship mismatch, inherited cruft, unsupported formulas/names, bad CF references.

## Integration

- Core battery: `triage/gate_checks.py`
- NW PRJ profile: `triage/nw_prj_dashboard_validator.py`
- Billing wrapper pattern: `triage/billing_bridge_validator.py`
- Contract doc: `docs/billing_bridge/WEB_EXCEL_VALIDATION.md`
