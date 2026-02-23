# Web-Excel Repair Triage

A local, browser-based tool that diagnoses why `.xlsx` workbooks trigger the
**"Fix this workbook?" / WORKBOOK REPAIRED** banner in Excel for Web (OneDrive /
SharePoint), and proposes minimal byte-level patch recipes to eliminate it.

---

## Quick Start

```bash
# 1. Clone (once per machine)
git clone https://github.com/<you>/web-excel-repair-triage.git
cd web-excel-repair-triage

# 2. Install the single dependency
pip install -r requirements.txt

# 3. Run
python -m streamlit run app.py
```

The app opens automatically at **http://localhost:8501**.  
To use a different port: `python -m streamlit run app.py --server.port 8502`

> **Python 3.11+** required. The core engine uses only stdlib (`zipfile`,
> `hashlib`, `re`, `difflib`, `urllib`) — no openpyxl, no lxml.

---

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `Active/` | Production-ready, currently working workbooks |
| `Candidates/` | Next-version workbooks under test for promotion to Active |
| `Repaired/` | What Excel for Web outputs after it "repairs" a Candidate |
| `Deprecated/` | Confirmed non-working / retired workbooks |
| `Outputs/` | Generated triage outputs — patched `.xlsx` files and saved recipe `.json` files |
| `triage/` | Core Python engine (scanner, gate checks, diff, patcher, …) |
| `Scripts to Start with/` | Original prototype scripts (kept for reference) |
| `Web Excel Compatibility Rules/` | Reference workbooks documenting OOXML rules |

### Workbook lifecycle

```
Candidates/ ──► (run triage) ──► Outputs/ (patched .xlsx + recipe .json)
                                      │
                          passes probe ▼
                               Active/
                                      │
                     Excel repairs it ▼
                              Repaired/   ◄── upload to Part Diff tab
                                      │
                       confirmed broken ▼
                             Deprecated/
```

---

## Using the App

### Sidebar — File Inputs

1. **Candidate .xlsx** — the workbook you want to test (drag from `Candidates/`)
2. **Repaired .xlsx** *(optional)* — drop the file Excel for Web produced after
   repair (from `Repaired/`). Enables the Diff, Patterns, and full Patch Recipe tabs.
3. **Bearer Token** *(optional)* — a Microsoft Graph API access token for the
   Graph Probe tab.

The sidebar also shows **folder shortcuts** listing every `.xlsx` and `.json` file
in each lifecycle folder — full filenames, never truncated — so you can quickly
identify which files to upload.  The `Outputs/` folder is included so you can
see previously generated patches at a glance.

---

### Tab 1 — 📊 Overview

Scorecard of all 10 gate checks.  Green card = pass, red card = fail with a
finding count. At a glance you can see whether the workbook is clean.

### Tab 2 — 🚦 Gate Checks

Expandable detail for each check. Failing checks are expanded automatically and
show a JSON sample of the first offending items.

| Gate | What it catches |
|------|----------------|
| Stopship Tokens | `_xlfn.`, `_xludf.`, `_xlpm.`, `AGGREGATE(` in formula strings |
| CF #REF Hits | `#REF!` inside conditional-formatting formula attributes |
| TableColumn LF | Linefeed (`&#10;`) in `<tableColumn name=…>` — breaks Web Excel |
| CalcChain Invalid | `calcChain.xml` entries that point to cells with no formula |
| Shared Ref OOB | Shared-formula `ref=` range whose last row exceeds the sheet's data |
| Shared Ref BBox | Shared-formula `ref=` that doesn't match the actual bounding box of cells using that formula |
| Styles DXF Integrity | `dxfs/@count` mismatch or `cfRule/@dxfId` pointing to a non-existent `<dxf>` |
| XML Well-formed | Any part that fails Python's `xml.etree.ElementTree` parse |
| Illegal Control Chars | Control characters (U+0000–U+001F except tab/LF/CR) in XML text nodes |
| Rels Missing Targets | `.rels` relationship entries whose target file is absent from the ZIP |

### Tab 3 — 🔀 Part Diff

Requires a Repaired file. Shows:
- Summary counts (added / removed / changed / unchanged ZIP entries)
- Per-changed-part size delta and unified XML diff
- **Copy button** on every diff block (top-right of the code block)
- **Download diff** button per part, plus **Download ALL diffs** as a single `.txt`

### Tab 4 — 🧩 Patterns

Automatically classifies the diff into named repair patterns:

| Pattern | Confidence | Meaning |
|---------|-----------|---------|
| `CALCCHAIN_DROP` | HIGH | Excel deleted `calcChain.xml` — invalid cell references in it |
| `DXFS_INSERTION` | HIGH | Excel appended missing `<dxf>` blocks to `styles.xml` |
| `CF_DXFID_CLONE` | MEDIUM | Excel remapped `cfRule/@dxfId` references |
| `SHAREDSTRINGS_REBUILD` | MEDIUM | Shared-strings table was rewritten |
| `TABLE_STYLE_NORM` | LOW | Table style references were normalized |
| `SHARED_REF_TRIM` | MEDIUM | Shared-formula `ref=` attributes were trimmed |
| `RELS_CLEANUP` | HIGH | Orphaned relationship entries were removed |

Each pattern card shows a **patch hint** with a copy button.

### Tab 5 — 🩹 Patch & Export

- **Auto-generated recipe**: JSON patch recipe built from gate findings and
  detected patterns. Metrics show how many operations need manual review.
- **Copy button** on the recipe JSON block (top-right).
- **Download** the recipe as `<stem>_recipe_<timestamp>.json`.
- **Save to Outputs/** button writes the recipe to disk immediately.
- **Apply & Export**: applies the recipe to a copy of the Candidate, saves the
  patched `.xlsx` to `Outputs/` on disk, and offers a browser download.
- **Override**: upload your own edited recipe JSON to apply custom patches.

#### Patch Operation Reference

| `operation` | Required fields | Effect |
|-------------|----------------|--------|
| `delete_part` | *(none)* | Remove the ZIP entry entirely (e.g. drop `calcChain.xml`) |
| `literal_replace` | `match`, `replacement`, `occurrence` | Replace the Nth occurrence of a byte string — **no XML parse** |
| `append_block` | `anchor`, `block`, `position` | Insert text `before` or `after` an anchor string |
| `set_part` | `content` | Replace the entire ZIP entry with new text |

> **Key constraint:** this tool never re-serializes XML. All mutations are
> byte/string-level, guaranteeing no whitespace or attribute-order drift.

#### `patch_recipe.json` schema

```json
{
  "schema_version": "1.0",
  "id": "unique-uuid-string",
  "created": "2026-02-23T12:00:00",
  "source_file": "MyWorkbook.xlsx",
  "patches": [
    {
      "id": "patch-uuid",
      "part": "xl/calcChain.xml",
      "operation": "delete_part",
      "description": "Drop invalid calcChain — Excel for Web will rebuild it"
    },
    {
      "id": "patch-uuid-2",
      "part": "xl/styles.xml",
      "operation": "literal_replace",
      "description": "Fix dxfs count attribute",
      "match": "count=\"3\"",
      "replacement": "count=\"4\"",
      "occurrence": 1
    },
    {
      "id": "patch-uuid-3",
      "part": "xl/worksheets/sheet1.xml",
      "operation": "append_block",
      "description": "Insert missing dxf entry",
      "anchor": "</dxfs>",
      "block": "<dxf><fill><patternFill patternType=\"none\"/></fill></dxf>",
      "position": "before"
    }
  ]
}
```

Placeholders like `<FILL_IN_MATCH>` appear when the engine cannot determine the
exact byte string automatically — edit these before applying.

### Tab 6 — 🌐 Graph Probe

Calls the Microsoft Graph API to verify that Excel for Web can open the workbook
**without** triggering repair — without manually uploading anything through the
browser.

**Setup** — get a token with `Files.ReadWrite` scope:
1. Go to [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
2. Sign in with your Microsoft account
3. Copy the **Access token** from the *Access token* tab
4. Paste into the **Bearer Token** field in the sidebar

Tokens expire after ~1 hour.

**Modes**:
- **Upload & test** — uploads your Candidate directly from the app, runs the probe, result in seconds.
- **By drive+item** — probe an existing file by OneDrive drive ID + item ID.
- **By share URL** — probe via a OneDrive sharing URL.

---

## GitHub Setup (first time)

```bash
# Inside the project folder:
git init
git add .
git commit -m "Initial commit — Web-Excel Repair Triage"

# Create an empty repo on GitHub (no README, no .gitignore), then:
git remote add origin https://github.com/<you>/web-excel-repair-triage.git
git branch -M main
git push -u origin main
```

### Pulling on another machine

```bash
git clone https://github.com/<you>/web-excel-repair-triage.git
cd web-excel-repair-triage
pip install -r requirements.txt
python -m streamlit run app.py
```

That's it — the full triage tool is running in your browser.

---

## Architecture Notes

- `.xlsx` files are ZIP archives. This tool **never re-serializes XML**; all
  mutations are byte/string-level (`str.replace`, slice-and-splice). This
  guarantees no whitespace or attribute-order changes that could confuse Excel.
- Gate checks process each ZIP part once using split-based cell scanning
  (`xml.split("</c>")`) — O(n), not O(n²) regex backtracking. A 7,000-row
  workbook scans in < 1 s.
- The patch recipe is a plain JSON file — you can author, edit, version-control,
  and share recipes independently of the workbooks.
- `Outputs/` is the single landing zone for all generated files. Patched `.xlsx`
  files are excluded from git (re-generatable); recipe `.json` files are tracked
  by default (valuable, small, human-readable).

### Module map

| Module | Responsibility |
|--------|---------------|
| `triage/scanner.py` | ZIP traversal, part extraction, SHA-256 hashing |
| `triage/gate_checks.py` | 10 structural hazard checks → `GateReport` |
| `triage/diff.py` | Part-level diff between two `.xlsx` files → `DiffReport` |
| `triage/patterns.py` | Classify `DiffReport` into named `Pattern` objects |
| `triage/report.py` | Build and merge `PatchRecipe` objects; serialize to JSON |
| `triage/patcher.py` | Apply a `PatchRecipe` to a ZIP, write output file |
| `triage/graph_probe.py` | Microsoft Graph API upload-and-test probe |
| `app.py` | Streamlit UI — 6 tabs wiring all modules together |

---

## Contributing / Development

```bash
# Run the app in dev mode (auto-reloads on file save)
python -m streamlit run app.py --server.runOnSave true

# Syntax-check all modules
python -c "
import ast, pathlib
for f in pathlib.Path('.').rglob('*.py'):
    try: ast.parse(f.read_text(encoding='utf-8'))
    except SyntaxError as e: print(f'{f}: {e}')
print('All OK')
"
```

**Adding a new gate check:**
1. Add a function `check_<name>(parts: dict[str, bytes]) -> list[str]` in `triage/gate_checks.py`
2. Register it in `ALL_CHECKS` at the bottom of that file
3. Add a row to the gate table in `app.py` (`ALL_GATES`) and in this README

**Adding a new patch operation:**
1. Add a handler in `triage/patcher.py` → `_apply_one(op, part_bytes) -> bytes`
2. Document the required fields in the schema table above

