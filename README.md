# Web-Excel Repair Triage

> **Diagnose, diff, patch, and verify `.xlsx` workbooks that trigger the
> "Fix this workbook?" / WORKBOOK REPAIRED banner in Excel for Web —
> without touching OneDrive manually.**

---

## What Is This?

When you open an `.xlsx` file in Excel for Web (OneDrive / SharePoint), the
browser sometimes shows a yellow banner:

> **"We found a problem with some content in 'MyFile.xlsx'. Do you want us to
> try to recover as much as we can?"**

or silently repairs the file and shows **WORKBOOK REPAIRED** in the title bar.
This means Excel for Web found a structural defect in the OOXML package and
auto-corrected it — often changing the file in ways that break formulas,
conditional formatting, or shared-string references.

**Web-Excel Repair Triage** is a local, browser-based tool that:

| Capability | How |
|-----------|-----|
| 🔍 **Diagnoses** the exact structural defect | 10 gate checks scan the raw ZIP/XML |
| 🔀 **Diffs** your file against Excel's repaired version | SHA-256 per ZIP part + unified XML diff |
| 🧩 **Classifies** the repair into named patterns | 7 known Excel-for-Web repair behaviours |
| 🩹 **Generates** a minimal byte-level patch recipe | JSON recipe — no XML reserialization |
| ⚙️ **Applies** the patch and exports a clean `.xlsx` | Byte-safe patcher, no openpyxl/lxml |
| 🌐 **Verifies** the fix via Microsoft Graph API | Upload → createSession → listWorksheets |
| 🤖 **Exposes all phases as MCP tools** | Augment Code ("auggie") can call them directly |

### Who is it for?

- **Excel power users** who build complex workbooks and need to understand why
  OneDrive keeps repairing them.
- **Developers** who generate `.xlsx` files programmatically and need to
  validate OOXML compliance before deployment.
- **IT / SharePoint admins** who need a repeatable, auditable repair workflow.

### Key design decisions

- **No XML reserialization** — all patches are byte/string-level (`str.replace`,
  slice-and-splice). Zero risk of whitespace or attribute-order drift.
- **Python stdlib only** for the core engine — `zipfile`, `hashlib`, `re`,
  `difflib`, `urllib`. Streamlit is the only UI dependency.
- **Patch recipes are plain JSON** — version-control them, share them, apply
  them in CI pipelines.
- **MCP-first** — every triage phase is also an MCP tool, so Augment Code can
  orchestrate the full pipeline from a chat prompt.

---

## Quick Start

> **Estimated time: 5 minutes** — even if you have never used a terminal before.

### Step 0 — Things you need (one-time setup)

| Requirement | How to get it | Check you have it |
|-------------|---------------|-------------------|
| **Python 3.11 or newer** | [python.org/downloads](https://www.python.org/downloads/) — use the big yellow button, run the installer, **tick "Add python.exe to PATH"** | Open a terminal, type `python --version` → should print `3.11` or higher |
| **git** | [git-scm.com/downloads](https://git-scm.com/downloads) — default options are fine | Type `git --version` → should print a version number |

**How to open a terminal on Windows:**
Press **Win + R**, type `powershell`, press Enter.
Or open the Start menu and search for **PowerShell**.

---

### Step 1 — Get the code (once per machine)

```powershell
git clone https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
cd "web-excel-repair-triage"
```

This downloads the project into a folder called `web-excel-repair-triage`
on your Desktop (wherever PowerShell was pointing when you ran it).
If you already have the folder, skip this — just `cd` into it.

---

### Step 2 — Install dependencies (once per machine)

```powershell
pip install streamlit "mcp[cli]"
```

`pip` is Python's package manager — it comes with Python automatically.
This installs two packages:

| Package | What it does |
|---------|-------------|
| `streamlit` | Turns the Python script into a browser app |
| `mcp[cli]` | Lets Augment Code ("auggie") call the triage tools directly |

You will see a lot of text scroll by. When it stops and you see `Successfully installed`, you are done.

---

### Step 3 — Open the app

```powershell
python -m streamlit run app.py
```

**What you should see in the terminal:**

```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

Your browser will open automatically. If it does not, copy
**http://localhost:8501** and paste it into your browser's address bar.

> **To stop the app:** click back into the terminal and press **Ctrl + C**.
> **To restart it:** run the same `python -m streamlit run app.py` command again.
> **Different port:** `python -m streamlit run app.py --server.port 8502`

---

### Every time after that (daily use)

```powershell
# 1. Open PowerShell
# 2. Navigate to the project folder:
cd "C:\path\to\web-excel-repair-triage"

# 3. Start the app:
python -m streamlit run app.py
```

That is all. Steps 0–2 only happen once.

---

### Pulling updates from GitHub

If someone pushed new features and you want them:

```powershell
git pull
python -m streamlit run app.py
```

No reinstalling needed unless `requirements.txt` changed (the terminal will tell you if it did).

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

## Patch Recipe Versioning Workflow

The patch recipe is the core artifact of the triage process. Here is the
full iterative lifecycle for generating and refining a recipe until the
workbook passes the Graph probe.

### Version 1 — Gate-only auto-recipe (no repaired file needed)

```
Tab 1 / Tab 2  →  run gate checks on Candidate
Tab 5          →  click "Generate Recipe"
               →  auto-recipe v1 is created (gate findings only)
               →  save to Outputs/ as  MyBook_recipe_v1.json
```

The `version` field in the JSON will be `"1"`. Operations that need manual
input contain `<FILL_IN_...>` placeholders.

### Version 2 — Richer recipe (gate + diff patterns)

```
Tab 3          →  upload Repaired file → run diff
Tab 4          →  patterns detected automatically
Tab 5          →  click "Generate Recipe" again
               →  recipe now includes pattern-derived operations
               →  save as  MyBook_recipe_v2.json
```

### Filling in placeholders

Open the recipe JSON in any text editor. Replace every `<FILL_IN_...>` value
with the exact byte string from the XML diff (Tab 3 copy button). Example:

```json
// Before (auto-generated):
"match": "<FILL_IN_MATCH>",
"replacement": "<FILL_IN_REPLACEMENT>"

// After (manually edited):
"match": "count=\"3\"",
"replacement": "count=\"5\""
```

### Bumping the version

Each time you edit and re-apply a recipe, increment the `version` field:

```json
{ "version": "3", "source_file": "MyBook.xlsx", ... }
```

This makes it easy to track which iteration produced which patched file.

### Apply → Test → Iterate

```
Tab 5  →  upload edited recipe JSON (Override section)
       →  click "Apply & Export"
       →  patched file saved to Outputs/MyBook_patched.xlsx

Tab 6  →  upload patched file as Candidate
       →  click "Upload & Test"
       →  if PASS → promote to Active/
       →  if FAIL → read error, edit recipe, bump version, repeat
```

### Recipe as code

Because recipes are plain JSON, you can:
- **Version-control** them alongside the workbook in git
- **Share** them with colleagues who have the same workbook
- **Apply** them in a CI pipeline: `python -c "from triage.patcher import apply_recipe_from_file; apply_recipe_from_file('Candidates/MyBook.xlsx', 'Outputs/MyBook_recipe_v3.json', 'Outputs/MyBook_patched.xlsx')"`
- **Ask auggie** to generate or refine a recipe via the MCP tools (see § MCP Configuration below)

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
| `triage/agents.py` | One agent class per phase + `TriageOrchestrator` |
| `mcp_server.py` | MCP server — exposes all agents as callable tools |
| `app.py` | Streamlit UI — 6 tabs wiring all modules together |

---

## AI Agents

`triage/agents.py` wraps each triage module in a clean agent class so the
pipeline can be driven from code, scripts, or the MCP server — not just the UI.

### Agent classes

| Agent | Phase | `.run()` signature | Returns |
|-------|-------|--------------------|---------|
| `GateCheckAgent` | 1 | `run(candidate_path)` | `GateReport` |
| `DiffAgent` | 2 | `run(candidate_path, repaired_path)` | `DiffReport` |
| `PatternAgent` | 3 | `run(diff_report)` | `List[Pattern]` |
| `RecipeAgent` | 4 | `run(source_file, gate_report, patterns)` | `PatchRecipe` |
| `PatchAgent` | 5 | `run(candidate_path, recipe_dict, output_path)` | `str` (path) |
| `GraphProbeAgent` | 6 | `run(token, candidate_path, remote_name)` | `GraphResult` |
| `TriageOrchestrator` | All | `run_full_pipeline(candidate, repaired, token)` | `dict` |

### Using agents from a script

```python
from triage.agents import TriageOrchestrator

orch = TriageOrchestrator()
result = orch.run_full_pipeline(
    candidate_path="Candidates/MyBook.xlsx",
    repaired_path="Repaired/MyBook.xlsx",   # optional
    token=None,                              # set to Graph token to probe
)

print(result["gate_report"]["pass_all"])    # True / False
print(result["recipe_json"])                # pretty-printed JSON recipe
```

### Using a single agent

```python
from triage.agents import GateCheckAgent, RecipeAgent

gate = GateCheckAgent().run("Candidates/MyBook.xlsx")
print(gate.failing_gates)   # {"calcchain_invalid": 3, ...}

recipe = RecipeAgent().run(
    source_file="Candidates/MyBook.xlsx",
    gate_report=gate,
)
print(recipe.to_json())
```

### Extending the pipeline

To add a new phase:
1. Add a module in `triage/` with a pure function that takes/returns dataclasses.
2. Add an agent class in `triage/agents.py` wrapping that function.
3. Add an `@mcp.tool()` in `mcp_server.py` wrapping the agent.
4. Wire it into `TriageOrchestrator.run_full_pipeline()`.

---

## MCP Configuration (Augment Code / "auggie")

The MCP server (`mcp_server.py`) exposes all 7 triage tools so that Augment
Code can call them directly from the chat panel — no Streamlit UI needed.

### Step 1 — Install the dependency

```bash
pip install "mcp[cli]"
```

### Step 2 — Start the MCP server

Keep this running in a terminal while you use Augment Code:

```bash
# From the project root:
python mcp_server.py
```

The server communicates over **stdio** (standard input/output), which is the
default transport for local MCP servers. No port or network config needed.

### Step 3 — Register in Augment Code (VS Code)

Open the Augment panel → **⚙ Settings** (gear icon, top-right) → **MCP** section.

Click **Import from JSON** and paste:

```json
{
  "mcpServers": {
    "excel-triage": {
      "command": "python",
      "args": ["${workspaceFolder}/mcp_server.py"]
    }
  }
}
```

> **`${workspaceFolder}`** expands to the project root automatically when
> Augment Code is open in the `web-excel-repair-triage` folder.

Click **Save**. The server appears in the MCP list. Augment will restart it
automatically each session.

### Step 4 — Use the tools from auggie

Once registered, you can ask auggie things like:

```
Run gate checks on Candidates/MyBook.xlsx and tell me what's failing.
```
```
Generate a patch recipe for Candidates/MyBook.xlsx using Repaired/MyBook.xlsx.
```
```
Apply the recipe in Outputs/MyBook_recipe_v2.json to Candidates/MyBook.xlsx
and save the result to Outputs/MyBook_patched.xlsx.
```
```
Run the full triage pipeline on Candidates/MyBook.xlsx and Repaired/MyBook.xlsx.
```

Auggie will call the appropriate MCP tool, stream the result back, and can
chain multiple tools in a single conversation turn.

### MCP tools reference

| Tool | Description |
|------|-------------|
| `run_gate_checks(candidate_path)` | Phase 1 — 10 structural checks |
| `run_diff(candidate_path, repaired_path)` | Phase 2 — part-level diff |
| `detect_patterns(candidate_path, repaired_path)` | Phase 3 — pattern classification |
| `generate_recipe(candidate_path, repaired_path?)` | Phase 4 — build recipe JSON |
| `apply_patch_recipe(candidate_path, recipe_json, output_path?)` | Phase 5 — apply patch |
| `graph_probe(token, candidate_path, remote_name?)` | Phase 6 — Graph API probe |
| `run_full_pipeline(candidate_path, repaired_path?, token?)` | All phases in one call |

### Environment variables (optional)

If you prefer not to pass the Graph token in every prompt, set it as an
environment variable and the server will pick it up:

```bash
# Windows PowerShell:
$env:GRAPH_TOKEN = "eyJ0eXAiOiJKV1Q..."
python mcp_server.py
```

Then in auggie: *"Run a graph probe on Candidates/MyBook.xlsx"* — the server
reads `GRAPH_TOKEN` automatically.

### Alternative: VS Code `settings.json`

If you prefer to configure MCP via the VS Code settings file directly:

```json
// .vscode/settings.json  (or user settings)
{
  "augment.advanced": {
    "mcpServers": [
      {
        "name": "excel-triage",
        "command": "python",
        "args": ["${workspaceFolder}/mcp_server.py"],
        "env": {
          "GRAPH_TOKEN": "<paste-token-here>"
        }
      }
    ]
  }
}
```

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

