# Excel Desktop Recovery Triage Harness

This harness removes the manual step of reading an Excel repair prompt, locating
its `recoveryLog` XML, and then opening the referenced OOXML parts by hand.

## Static or supplied-log triage

```powershell
python -m triage.excel_recovery_triage `
  "Outputs/roster_blank_runtime/roster_review_blank.xlsx" `
  --recovery-log "C:\path\to\error588520_01.xml" `
  --json-out "Outputs/roster_blank_runtime/excel_recovery_triage.json" `
  --markdown-out "Outputs/roster_blank_runtime/excel_recovery_triage.md"
```

The command:

- parses removed parts, removed records, and repaired records;
- extracts and normalizes referenced OOXML part paths;
- parses every `.xml` and `.rels` package part;
- records part size and SHA-256;
- verifies `xl/styles.xml` and conditional-formatting `dxfId` references;
- correlates recovery actions with package failures;
- returns `STOP_SHIP` when Excel repair actions or XML failures are present.

It does not mutate or repair the workbook.

## Automated Windows desktop probe

```powershell
.\scripts\Invoke-ExcelDesktopRepairProbe.ps1 `
  -Workbook "Outputs\roster_blank_runtime\roster_review_blank.xlsx" `
  -OutDir "Outputs\roster_blank_runtime\desktop_probe"
```

The PowerShell probe:

1. snapshots existing Excel `error*.xml` logs;
2. opens the workbook read-only through Excel COM with alerts suppressed;
3. closes without saving;
4. copies newly generated recovery logs into the run directory;
5. runs the Python triage command;
6. emits `desktop_probe.json`, `excel_recovery_triage.json`, and
   `excel_recovery_triage.md`.

## Proof ceiling

A captured recovery log proves that desktop Excel repaired or removed content
from that exact workbook. Static OOXML inspection can identify package failures
and strong root-cause candidates. Neither result proves that a replacement
workbook is accepted in Excel for Web or approved for delivery.
