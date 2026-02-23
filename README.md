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
| `triage/` | Core Python engine (scanner, gate checks, diff, patcher, …) |
| `Scripts to Start with/` | Original prototype scripts (kept for reference) |
| `Web Excel Compatibility Rules/` | Reference workbooks documenting OOXML rules |

---

## Using the App

### Sidebar — File Inputs

1. **Candidate .xlsx** — the workbook you want to test (drag from `Candidates/`)
2. **Repaired .xlsx** *(optional)* — drop the file Excel for Web produced after
   repair (from `Repaired/`). Enables the Diff, Patterns, and full Patch Recipe tabs.
3. **Bearer Token** *(optional)* — a Microsoft Graph API access token for the
   Graph Probe tab.

The sidebar also shows **folder shortcuts** listing your Active, Candidate, and
Repaired files so you can quickly identify which files to upload.

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
- Per-changed-part size delta
- Expandable unified diff of the XML content

### Tab 4 — 🧩 Patterns

Automatically classifies the diff into known repair patterns:

| Pattern | Meaning |
|---------|---------|
| `CALCCHAIN_DROP` | Excel deleted `calcChain.xml` |
| `DXFS_INSERTION` | Excel appended missing `<dxf>` blocks to `styles.xml` |
| `CF_DXFID_CLONE` | Excel remapped `cfRule/@dxfId` references |
| `SHAREDSTRINGS_REBUILD` | Shared-strings table was rewritten |
| `TABLE_STYLE_NORM` | Table style references were normalized |
| `SHARED_REF_TRIM` | Shared-formula `ref=` attributes were trimmed |
| `RELS_CLEANUP` | Orphaned relationship entries were removed |

Each pattern shows a confidence badge (HIGH / MEDIUM / LOW) and a patch hint.

### Tab 5 — 🩹 Patch & Export

- **Auto-generated recipe**: JSON patch recipe built from gate findings and
  detected patterns. You can download it as `patch_recipe.json`.
- **Apply Recipe**: click **Apply & Export** to write patches into a copy of the
  Candidate and download the result as `*_patched.xlsx`.
- **Override**: upload your own edited `patch_recipe.json` to apply custom patches.

#### Patch Operation Reference

| `operation` | Fields | Effect |
|-------------|--------|--------|
| `literal_replace` | `match`, `replacement`, `occurrence` | Replace Nth occurrence of a byte string (no XML parse) |
| `append_block` | `anchor`, `block`, `position` (`before`/`after`) | Insert a text block relative to an anchor string |
| `delete_part` | *(none)* | Remove the ZIP entry entirely |
| `set_part` | `content` | Replace the entire ZIP entry with new text |

### Tab 6 — 🌐 Graph Probe

Calls the Microsoft Graph API to verify that Excel for Web can open the workbook
**without** triggering repair — without manually uploading anything through the
browser.

**Setup** — get a token with `Files.ReadWrite` scope:
```
https://developer.microsoft.com/en-us/graph/graph-explorer
```
Log in, copy the **Access token** from the top-right, paste into the sidebar.

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
  (O(n), not O(n²) regex backtracking) — a 7,000-row workbook scans in < 1 s.
- The patch recipe is a plain JSON file — you can author, edit, version-control,
  and share recipes independently of the workbooks.

