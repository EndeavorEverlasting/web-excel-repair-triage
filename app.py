"""
app.py — Web-Excel Repair Triage  (Streamlit UI)
Run:  python -m streamlit run app.py
"""
from __future__ import annotations
import datetime
import json
import os
import tempfile
from pathlib import Path

import streamlit as st

# ── page config (MUST be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="Web-Excel Repair Triage",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from triage.gate_checks import run_all, GateReport
from triage.diff import diff_packages, DiffReport
from triage.patterns import detect_all, Pattern
from triage.report import recipe_from_gates, recipe_from_patterns, merge_recipes, PatchRecipe
from triage.patcher import apply_recipe, PatchError, PatchWarning

# ── output folder ─────────────────────────────────────────────────────────────
OUTPUTS_DIR = Path("Outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)

# ── CSS theme ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background:#0d1117; }
  .main-header {
    background: linear-gradient(90deg,#0e4c2f 0%,#1a7a4a 100%);
    padding:18px 28px; border-radius:8px; margin-bottom:18px; color:#ffffff;
  }
  .main-header h1 { margin:0; font-size:1.7rem; letter-spacing:.5px; }
  .main-header p  { margin:4px 0 0; font-size:.9rem; opacity:.85; }
  .gate-pass { background:#0d3320; border-left:4px solid #28a745;
               padding:10px 14px; border-radius:6px; margin:4px 0; }
  .gate-fail { background:#3d1515; border-left:4px solid #dc3545;
               padding:10px 14px; border-radius:6px; margin:4px 0; }
  .file-info { background:#0d1f33; border-left:4px solid #4a9ede;
               padding:8px 12px; border-radius:6px; margin:4px 0;
               font-size:.80rem; word-break:break-all; }
  .folder-file { background:#111; border-radius:4px; padding:4px 8px;
                 margin:2px 0; font-size:.75rem; word-break:break-all;
                 color:#ccc; }
  .tutorial-box { background:#0a1a0a; border:1px solid #1a4a2a;
                  border-radius:6px; padding:12px 16px; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

# ── header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🔬 Web-Excel Repair Triage</h1>
  <p>Gate checks · Part diff · Pattern detection · Patch engine · Graph probe</p>
</div>
""", unsafe_allow_html=True)

# ── helpers ──────────────────────────────────────────────────────────────────
def _fmt_bytes(n: int) -> str:
    if n < 1024: return f"{n} B"
    if n < 1_048_576: return f"{n/1024:.1f} KB"
    return f"{n/1_048_576:.1f} MB"

def _file_info_html(label: str, name: str, size: int, colour: str = "#4a9ede") -> str:
    return (f'<div class="file-info" style="border-color:{colour}">'
            f'<b>{label}</b><br>'
            f'<span style="color:#eee">{name}</span><br>'
            f'<span style="color:#888">{_fmt_bytes(size)}</span></div>')

# ── sidebar: file uploads ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Input Files")
    cand_file = st.file_uploader("Candidate .xlsx", type=["xlsx"], key="candidate")
    if cand_file:
        st.markdown(_file_info_html("📄 Candidate", cand_file.name, cand_file.size, "#28a745"),
                    unsafe_allow_html=True)

    rep_file = st.file_uploader("Repaired .xlsx  *(optional)*", type=["xlsx"], key="repaired")
    if rep_file:
        st.markdown(_file_info_html("🔧 Repaired", rep_file.name, rep_file.size, "#ffc107"),
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔑 Graph Probe *(optional)*")
    graph_token = st.text_input("Bearer Token (GRAPH_TOKEN)", type="password",
                                value=os.environ.get("GRAPH_TOKEN", ""))
    probe_mode = st.selectbox("Probe mode", ["Upload & test", "By drive+item", "By share URL"])
    g_drive = g_item = g_share = ""
    if probe_mode == "By drive+item":
        g_drive = st.text_input("Drive ID")
        g_item  = st.text_input("Item ID")
    elif probe_mode == "By share URL":
        g_share = st.text_input("Share URL")

    st.markdown("---")
    st.markdown("### 📁 Folder Shortcuts")
    for folder in ("Candidates", "Active", "Repaired", "Deprecated", "Outputs"):
        p = Path(folder)
        if not p.exists():
            continue
        files = sorted(p.glob("*.xlsx")) + sorted(p.glob("*.json"))
        if not files:
            continue
        with st.expander(f"{folder}/ ({len(files)} file{'s' if len(files)!=1 else ''})"):
            for f in files:
                size_str = _fmt_bytes(f.stat().st_size)
                st.markdown(f'<div class="folder-file">📄 {f.name}<br>'
                            f'<span style="color:#666">{size_str}</span></div>',
                            unsafe_allow_html=True)

# ── helper: save upload to temp file ─────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _save_temp(name: str, data: bytes) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", prefix=name[:20] + "_")
    tmp.write(data)
    tmp.flush()
    return tmp.name

# ── main tabs ────────────────────────────────────────────────────────────────
tab_names = [
    "📊 Overview",
    "🚦 Gate Checks",
    "🔀 Part Diff",
    "🧩 Patterns",
    "🩹 Patch & Export",
    "🌐 Graph Probe",
    "🌍 Browser Excel Probe",
    "🖥 Desktop Excel Probe",
]
tabs = st.tabs(tab_names)

if not cand_file:
    for tab in tabs:
        with tab:
            st.info("Upload a **Candidate .xlsx** in the sidebar to begin.")
    st.stop()

# Save uploads (cache by file content so re-uploads don't re-read)
cand_bytes = cand_file.read()
cand_path  = _save_temp(cand_file.name, cand_bytes)
rep_path   = _save_temp(rep_file.name, rep_file.read()) if rep_file else None

# ── run gate checks (cached by file content) ─────────────────────────────────
@st.cache_data(show_spinner="Running gate checks…")
def _run_gates(path: str) -> dict:
    return run_all(path).to_dict()

gate_dict = _run_gates(cand_path)

# ── run diff (if repaired file present) ──────────────────────────────────────
@st.cache_data(show_spinner="Diffing packages…")
def _run_diff(cpath: str, rpath: str) -> dict:
    return diff_packages(cpath, rpath).to_dict()

diff_dict = _run_diff(cand_path, rep_path) if rep_path else None

# ═══════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════
with tabs[0]:
    with st.expander("ℹ️  How this tab works", expanded=False):
        st.markdown("""
**Overview** gives you a one-glance verdict on your Candidate workbook.

1. Upload a **Candidate .xlsx** in the sidebar (the file you want to test).
2. All 10 structural gate checks run automatically — each one lights up green ✅ or red ❌.
3. If you also upload a **Repaired .xlsx** (what Excel for Web saved after repairing your file),
   the *Changed parts* metric shows how many ZIP entries differ.

**What to do with failures:**
- Go to the **Gate Checks** tab for detail and JSON samples of offending items.
- Go to **Patch & Export** to download an auto-generated fix recipe.
- Go to **Part Diff** (with a Repaired file) to see exactly what Excel changed.
        """)

    col1, col2, col3 = st.columns(3)
    fg = gate_dict["failing_gates"]
    n_fail = len(fg)
    verdict = "✅ PASS" if not fg else f"❌ {n_fail} GATE(S) FAILING"
    col1.metric("Gate verdict", verdict)
    col2.metric("Failing gates", n_fail)
    if diff_dict:
        col3.metric("Changed parts", diff_dict["summary"]["changed"])
    else:
        col3.metric("Repaired file", "not provided")

    st.markdown("#### Gate Scorecard")
    ALL_GATES = [
        ("stopship_tokens",       "Stop-ship tokens (_xlfn, _xludf, AGGREGATE)"),
        ("cf_ref_hits",           "#REF! in conditional formatting"),
        ("tablecolumn_lf",        "Linefeed in tableColumn name="),
        ("calcchain_invalid",     "calcChain invalid entries"),
        ("shared_ref_oob",        "Shared formula ref OOB (exceeds max row)"),
        ("shared_ref_bbox",       "Shared formula bbox mismatch"),
        ("styles_dxf_integrity",  "dxfs count / cfRule dxfId integrity"),
        ("xml_wellformed",        "XML well-formedness errors"),
        ("illegal_control_chars", "Illegal control characters in XML"),
        ("rels_missing_targets",  "Missing relationship targets"),
    ]
    for key, label in ALL_GATES:
        count = fg.get(key, 0)
        css = "gate-fail" if count else "gate-pass"
        icon = "❌" if count else "✅"
        st.markdown(f'<div class="{css}">{icon} <b>{label}</b> — {count} finding(s)</div>',
                    unsafe_allow_html=True)

    at = gate_dict.get("triage", {}).get("activetab", {})
    if at:
        st.markdown("#### 📑 Workbook View")
        st.json(at)

# ═══════════════════════════════════════════════════════════════════════
# TAB 2: GATE CHECKS (detail)
# ═══════════════════════════════════════════════════════════════════════
_GATE_TO_SAMPLE = {
    "stopship_tokens":       "stopship",
    "cf_ref_hits":           "cf_ref",
    "tablecolumn_lf":        "tablecolumn_lf",
    "calcchain_invalid":     "calcchain_invalid",
    "shared_ref_oob":        "shared_ref_oob",
    "shared_ref_bbox":       "shared_ref_bbox",
    "styles_dxf_integrity":  "styles_dxf",
    "xml_wellformed":        "xml_wellformed",
    "illegal_control_chars": "illegal_control",
    "rels_missing_targets":  "rels_missing",
}

_GATE_HELP = {
    "stopship_tokens":
        "Formulas containing `_xlfn.`, `_xludf.`, `_xlpm.`, or `AGGREGATE(` use functions "
        "unsupported by Excel for Web.  These *always* trigger the repair banner.",
    "cf_ref_hits":
        "`#REF!` inside a conditional-formatting formula attribute means the CF rule references "
        "a deleted or out-of-range cell.  Excel for Web treats this as a structural error.",
    "tablecolumn_lf":
        "A linefeed character (`&#10;`) inside a `<tableColumn name=…>` attribute breaks the "
        "table name uniqueness check in Excel for Web.",
    "calcchain_invalid":
        "`xl/calcChain.xml` lists cells in calculation order.  If it references cells that have "
        "no formula, Excel for Web deletes the whole file and triggers repair.",
    "shared_ref_oob":
        "A shared formula's `ref=` attribute declares a range whose last row is beyond the "
        "sheet's actual data extent.  Excel for Web clips this and marks the file as repaired.",
    "shared_ref_bbox":
        "The declared `ref=` bounding box doesn't match the actual set of cells that carry "
        "`si=` (shared-formula index).  Excel recalculates the bbox and marks the file repaired.",
    "styles_dxf_integrity":
        "`dxfs/@count` disagrees with the actual number of `<dxf>` children, or a `cfRule/@dxfId` "
        "points to an index beyond the pool.  Both trigger style-repair.",
    "xml_wellformed":
        "Any ZIP part that is not valid XML (unclosed tags, illegal entities, etc.) causes "
        "Excel for Web to abort parsing and fall back to repair mode.",
    "illegal_control_chars":
        "Control characters U+0000–U+001F (except `\\t`, `\\n`, `\\r`) are illegal in XML 1.0 "
        "text nodes.  They sneak in via copy-paste from terminal output or databases.",
    "rels_missing_targets":
        "A `.rels` relationship entry references a part (e.g. `../drawings/drawing1.xml`) "
        "that does not exist in the ZIP.  Excel for Web cannot resolve the reference.",
}

with tabs[1]:
    with st.expander("ℹ️  How this tab works", expanded=False):
        st.markdown("""
**Gate Checks** runs 10 structural hazard checks against every XML part in your workbook.

- **Failing gates** (❌) are auto-expanded so you see the problem immediately.
- Each gate shows a **JSON sample** of the first offending items — use the **copy icon** in the
  top-right of each code block to grab the raw JSON.
- Hover the gate name for a plain-English explanation of what the check catches.
- Use the findings here to guide editing in the **Patch & Export** tab.
        """)

    samples = gate_dict.get("samples", {})
    for key, label in ALL_GATES:
        count = gate_dict["failing_gates"].get(key, 0)
        hits  = samples.get(_GATE_TO_SAMPLE.get(key, key), [])
        with st.expander(f"{'❌' if count else '✅'} {label} ({count})", expanded=bool(count)):
            help_txt = _GATE_HELP.get(key, "")
            if help_txt:
                st.caption(help_txt)
            if hits:
                st.code(json.dumps(hits, indent=2), language="json")
            else:
                st.success("No findings.")

# ═══════════════════════════════════════════════════════════════════════
# TAB 3: PART DIFF
# ═══════════════════════════════════════════════════════════════════════
with tabs[2]:
    if not diff_dict:
        st.info("Upload a **Repaired .xlsx** in the sidebar to enable the diff view.")
    else:
        with st.expander("ℹ️  How this tab works", expanded=False):
            st.markdown("""
**Part Diff** compares your Candidate and Repaired files at the **ZIP-entry level**.

- Every `.xlsx` is a ZIP archive. This tab shows which internal XML parts changed.
- **Added** = parts Excel for Web created from scratch.
- **Removed** = parts Excel for Web deleted (e.g. `xl/calcChain.xml`).
- **Changed** = parts whose SHA-256 hash differs; a unified diff is shown.

**Copying diffs:**  use the **copy icon** (top-right of each code block) to grab the full diff
text for pasting into a recipe or sharing with a colleague.  You can also download each diff
as a `.txt` file using the button below the code block.
            """)

        sm = diff_dict["summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Added",     sm["added"])
        c2.metric("Removed",   sm["removed"])
        c3.metric("Changed",   sm["changed"])
        c4.metric("Unchanged", sm["unchanged"])

        if diff_dict["added"]:
            with st.expander(f"➕ Added parts ({sm['added']})", expanded=True):
                for n in diff_dict["added"]:
                    st.code(n, language="text")
        if diff_dict["removed"]:
            with st.expander(f"➖ Removed parts ({sm['removed']})", expanded=True):
                for n in diff_dict["removed"]:
                    st.code(n, language="text")

        st.markdown("#### Changed Parts — XML Diff")
        all_diffs: list[str] = []
        for entry in diff_dict["changed"]:
            delta    = entry.get("size_delta", 0) or 0
            sign     = "+" if delta >= 0 else ""
            part_key = entry["part"].replace("/", "_").replace(".", "_")
            with st.expander(f"🔀 {entry['part']}  ({sign}{delta} bytes)", expanded=False):
                cols = st.columns(2)
                cols[0].metric("Candidate size", entry.get("candidate_size"))
                cols[1].metric("Repaired size",  entry.get("repaired_size"))
                xd = entry.get("xml_diff", "")
                if xd:
                    st.code(xd, language="diff")
                    st.download_button(
                        f"⬇️ Download diff — {entry['part']}",
                        xd.encode("utf-8"),
                        file_name=f"{part_key}.diff.txt",
                        mime="text/plain",
                        key=f"dl_diff_{part_key}",
                    )
                    all_diffs.append(f"{'='*60}\n{entry['part']}\n{'='*60}\n{xd}\n")
                else:
                    st.caption("(binary part — no text diff)")

        if all_diffs:
            st.markdown("---")
            st.download_button(
                "⬇️ Download ALL diffs as one .txt file",
                "\n".join(all_diffs).encode("utf-8"),
                file_name=f"{Path(cand_file.name).stem}_all_diffs.txt",
                mime="text/plain",
                key="dl_all_diffs",
            )

# ═══════════════════════════════════════════════════════════════════════
# TAB 4: PATTERNS
# ═══════════════════════════════════════════════════════════════════════
with tabs[3]:
    if not diff_dict:
        st.info("Upload a **Repaired .xlsx** to enable pattern detection.")
    else:
        with st.expander("ℹ️  How this tab works", expanded=False):
            st.markdown("""
**Pattern Detection** classifies the diff between Candidate and Repaired into named repair recipes.

| Confidence | Meaning |
|-----------|---------|
| 🔴 HIGH | The pattern signature is unambiguous; the patch hint is directly actionable |
| 🟠 MEDIUM | Likely match; verify the XML diff before applying |
| 🟡 LOW | Possible match; manual review strongly recommended |

Each pattern card shows the **patch hint** — a plain-English recipe you can feed directly
into the **Patch & Export** tab.  Copy the hint text, go to Tab 5, and use it to author or
refine the `patch_recipe.json`.
            """)

        @st.cache_data(show_spinner="Detecting patterns…")
        def _detect_patterns(cp: str, rp: str):
            from triage.diff import diff_packages
            from triage.patterns import detect_all
            dr   = diff_packages(cp, rp)
            pats = detect_all(dr)
            return [{"name": p.name, "description": p.description,
                     "parts": p.affected_parts, "confidence": p.confidence,
                     "patch_hint": p.suggested_patch} for p in pats]

        patterns = _detect_patterns(cand_path, rep_path)
        if not patterns:
            st.success("No known repair patterns detected in this diff.")
        else:
            st.warning(f"{len(patterns)} repair pattern(s) detected — see patch hints below.")
            for pat in patterns:
                conf_colour = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}.get(pat["confidence"], "⚪")
                with st.expander(
                    f"{conf_colour} **{pat['name']}**  [{pat['confidence']}]", expanded=True
                ):
                    st.markdown(pat["description"])
                    st.markdown(f"**Affected parts:** `{'`, `'.join(pat['parts'])}`")
                    if pat["patch_hint"]:
                        st.info(f"💡 Patch hint: {pat['patch_hint']}")
                        st.code(pat["patch_hint"], language="text")  # copy button

# ═══════════════════════════════════════════════════════════════════════
# TAB 5: PATCH & EXPORT
# ═══════════════════════════════════════════════════════════════════════
with tabs[4]:
    with st.expander("ℹ️  How this tab works — Patch Recipe Guide", expanded=False):
        st.markdown("""
**The patch recipe (`patch_recipe.json`) is the core output of this tool.**

It is a plain JSON file describing one or more byte-level fixes to apply to your Candidate.
Because it is plain text, you can: edit it, commit it to Git, share it, and re-apply it on
any machine — all without needing the original workbook open.

#### How to use it

1. **Review the auto-generated recipe** below.  It is built from:
   - Gate failures (always present)
   - Pattern matches (present when a Repaired file is uploaded)
2. **Download** → edit in any text editor → fix any `<FILL_IN_…>` placeholders.
3. **Upload your edited recipe** using the override uploader, then click **Apply & Export**.
4. The patched `.xlsx` is saved to `Outputs/` on disk **and** offered as a browser download.

#### Patch operations

| `operation` | Required fields | What it does |
|-------------|----------------|--------------|
| `delete_part` | *(none)* | Removes the ZIP entry entirely (e.g. drop `calcChain.xml`) |
| `literal_replace` | `match`, `replacement`, `occurrence` | Replaces the Nth occurrence of a byte string — **no XML parse** |
| `append_block` | `anchor`, `block`, `position` | Inserts text before/after an anchor string |
| `set_part` | `content` | Replaces the whole ZIP entry with new text |

> **Key constraint:** this tool never re-serializes XML.  All mutations are
> byte/string-level, guaranteeing no whitespace or attribute-order drift.
        """)

    st.markdown("### 🩹 Auto-generated Patch Recipe")

    @st.cache_data(show_spinner="Building patch recipe…")
    def _gate_recipe_dict(cp: str) -> dict:
        return recipe_from_gates(run_all(cp)).to_dict()

    @st.cache_data(show_spinner="Building full recipe…")
    def _full_recipe(cp: str, rp: str) -> dict:
        from triage.diff import diff_packages
        from triage.patterns import detect_all
        dr   = diff_packages(cp, rp)
        pats = detect_all(dr)
        gr   = run_all(cp)
        r1   = recipe_from_gates(gr)
        r2   = recipe_from_patterns(cp, pats)
        return merge_recipes(r1, r2).to_dict()

    recipe_dict = _full_recipe(cand_path, rep_path) if (diff_dict and rep_path) \
                  else _gate_recipe_dict(cand_path)
    recipe_json = json.dumps(recipe_dict, indent=2)

    n_patches = len(recipe_dict.get("patches", []))
    needs_review = sum(1 for p in recipe_dict.get("patches", [])
                       if "<FILL_IN" in json.dumps(p) or "<REVIEW" in json.dumps(p))
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Patch operations", n_patches)
    rc2.metric("Need manual review", needs_review)
    rc3.metric("Ready to apply", n_patches - needs_review)

    st.code(recipe_json, language="json")   # ← built-in copy button

    stem = Path(cand_file.name).stem
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    col_a, col_b = st.columns(2)
    col_a.download_button(
        "⬇️ Download patch_recipe.json",
        recipe_json,
        file_name=f"{stem}_recipe_{ts}.json",
        mime="application/json",
        key="dl_recipe",
    )
    if col_b.button("💾 Save recipe to Outputs/"):
        out_recipe = OUTPUTS_DIR / f"{stem}_recipe_{ts}.json"
        out_recipe.write_text(recipe_json, encoding="utf-8")
        st.success(f"Saved → {out_recipe}")

    st.markdown("---")
    st.markdown("### ▶️ Apply Recipe & Export Patched .xlsx")
    uploaded_recipe = st.file_uploader(
        "Override recipe JSON (optional — upload your edited recipe here)",
        type=["json"], key="recipe_upload",
    )

    if st.button("Apply & Export", type="primary"):
        warn_exc: PatchWarning | None = None
        try:
            final_recipe = json.loads(uploaded_recipe.read()) if uploaded_recipe else recipe_dict
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_out:
                out_path = tmp_out.name
            apply_recipe(cand_path, final_recipe, out_path)
        except PatchWarning as pw:
            # File was written successfully; stubs were intentionally skipped.
            warn_exc = pw
            out_path = pw.output_path
        except PatchError as e:
            st.error(f"Patch error: {e}")
            out_path = None
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            out_path = None

        if out_path and Path(out_path).exists():
            patched_bytes = Path(out_path).read_bytes()
            patched_name  = f"{stem}_patched.xlsx"

            # Save to Outputs/ on disk
            disk_out = OUTPUTS_DIR / patched_name
            disk_out.write_bytes(patched_bytes)

            if warn_exc:
                stub_lines = "\n".join(f"• {s}" for s in warn_exc.skipped)
                st.warning(
                    f"⚠️ Patch applied — {len(warn_exc.skipped)} stub(s) skipped "
                    f"(fill in match/replacement manually before re-running):\n\n{stub_lines}"
                )
            else:
                st.success(f"✅ Patch applied — {len(patched_bytes):,} bytes.  "
                           f"Saved to `{disk_out}`")

            st.download_button(
                "⬇️ Download patched .xlsx",
                patched_bytes,
                file_name=patched_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_patched",
            )

# ═══════════════════════════════════════════════════════════════════════
# TAB 6: GRAPH PROBE
# ═══════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("### 🌐 Microsoft Graph — Web Excel Openability Probe")

    with st.expander("ℹ️  How this tab works — getting a Bearer Token", expanded=False):
        st.markdown("""
**Graph Probe** uploads your workbook to OneDrive via the Microsoft Graph API and checks
whether Excel for Web would trigger the repair banner — **without you having to open a browser**.

#### Getting a Bearer Token (one-time setup)

1. Go to [portal.azure.com](https://portal.azure.com) → **Azure Active Directory** →
   **App registrations** → **New registration**.
2. Name it anything (e.g. `ExcelTriageTool`), set redirect URI to `http://localhost`.
3. Under **API permissions** add `Files.ReadWrite` (delegated).
4. Use the [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) to sign in
   and copy the **Access token** from the *Access token* tab.
5. Paste it into the **Bearer Token** field in the sidebar.

Tokens expire after ~1 hour.  For automation, use a service principal with a client secret.

#### Probe modes

| Mode | When to use |
|------|-------------|
| **Upload & test** | File is local — the tool uploads it, reads the repair flag, then deletes it |
| **By drive+item** | File is already in OneDrive — provide Drive ID and Item ID from the Graph URL |
| **By share URL** | You have a sharing link — the tool resolves it to a drive+item pair |
        """)

    st.caption("Requires a valid Bearer token with **Files.ReadWrite** scope on the target OneDrive.")

    if not graph_token:
        st.warning("Enter a **Bearer Token** in the sidebar to enable this feature.")
    else:
        if st.button("🚀 Run Graph Probe", type="primary"):
            from triage.graph_probe import probe_by_item, probe_by_share_url, probe_upload_and_test
            with st.spinner("Probing Excel for Web via Graph API…"):
                try:
                    if probe_mode == "Upload & test":
                        result = probe_upload_and_test(
                            graph_token,
                            cand_path,
                            remote_name=cand_file.name,
                            out_root="Outputs/graph_runs",
                        )
                    elif probe_mode == "By drive+item":
                        result = probe_by_item(graph_token, g_drive, g_item, out_root="Outputs/graph_runs")
                    else:
                        result = probe_by_share_url(graph_token, g_share, out_root="Outputs/graph_runs")

                    if result.success:
                        st.success(f"✅ Graph probe PASSED — {len(result.worksheets)} worksheets visible.")
                        st.code(json.dumps({"worksheets": result.worksheets}, indent=2), language="json")

                        # Show a small preview of sheet content if available.
                        if getattr(result, "preview_text", None):
                            st.markdown("#### Sheet preview (Graph range read)")
                            st.caption(
                                f"Sheet={getattr(result, 'preview_sheet', None)}  "
                                f"Address={getattr(result, 'preview_address', None)}"
                            )
                            try:
                                import pandas as pd  # type: ignore

                                st.dataframe(pd.DataFrame(result.preview_text))
                            except Exception:
                                st.code(json.dumps(result.preview_text, indent=2), language="json")

                        if getattr(result, "preview_image", None):
                            try:
                                st.image(result.preview_image, caption="Graph sheet preview")
                            except Exception:
                                st.write(result.preview_image)

                        if getattr(result, "out_dir", None):
                            st.caption(f"Artifacts: {result.out_dir}")
                    else:
                        st.error(f"❌ Graph probe FAILED at step '{result.step}' "
                                 f"(HTTP {result.status_code})")
                        if result.error:
                            st.code(result.error)
                except Exception as ex:
                    st.error(f"Exception during probe: {ex}")


# ═══════════════════════════════════════════════════════════════════════
# TAB 7: BROWSER EXCEL PROBE
# ═══════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("### 🌍 Browser — Excel for the web UI Probe")
    st.caption(
        "Opens the workbook sharing link in a real browser and looks for worksheet UI evidence "
        "(DOM heuristics; screenshots optional). Useful when you want to confirm the *actual* "
        "Excel web UI loads a sheet within ~15 seconds."
    )

    st.info(
        "This feature is optional and requires Playwright. If you haven't installed it yet: "
        "`pip install playwright` then `python -m playwright install`."
    )

    web_url = st.text_input(
        "Workbook share URL",
        value="",
        placeholder="https://... (OneDrive/SharePoint sharing link that opens in Excel for the web)",
        help="You must supply a share link that opens the workbook in Excel for the web.",
    )


    col1, col2, col3 = st.columns(3)
    with col1:
        web_headless = st.checkbox("Headless", value=False)
        web_timeout = st.number_input(
            "Timeout (seconds)",
            min_value=5,
            max_value=60,
            value=15,
            step=5,
        )
    with col2:
        web_browser = st.selectbox(
            "Browser engine",
            options=["chromium", "firefox", "webkit"],
            index=0,
            help="Playwright engine; Excel for the web is most reliable with Chromium.",
        )
        web_channel = st.selectbox(
            "Browser channel",
            options=["(default)", "msedge", "chrome"],
	            index=2,
	            help="Use 'chrome' to reuse your Microsoft 365 sign-in (recommended if you normally use Chrome).",
        )
    with col3:
        web_user_data_dir = st.text_input(
            "User data dir (optional)",
            value="",
	            placeholder=r"C:\Users\<you>\AppData\Local\Google\Chrome\User Data",
            help=(
                "If the workbook requires sign-in, provide a browser profile directory so the probe "
                "can reuse your existing session (persistent context)."
            ),
        )
        web_take_screenshot = st.checkbox("Try screenshot (best-effort)", value=False)

    if st.button("▶️ Run Browser Probe", type="primary"):
        if not web_url.strip():
            st.warning("Enter a workbook share URL.")
        else:
            try:
                from triage.web_excel_browser import probe_open_in_web_excel_isolated

                with st.spinner("Opening workbook in browser (timeboxed)…"):
                    r = probe_open_in_web_excel_isolated(
                        url=web_url.strip(),
                        out_root="Outputs/web_runs",
                        timeout_seconds=int(web_timeout),
                        headless=bool(web_headless),
                        user_data_dir=(web_user_data_dir.strip() or None),
                        browser=str(web_browser),
                        channel=(None if web_channel == "(default)" else str(web_channel)),
                        take_screenshot=bool(web_take_screenshot),
                    )

                if r.sheet_observed and not r.repair_banner_detected:
                    st.success(
                        f"✅ Sheet observed in web UI. Elapsed={getattr(r,'elapsed_seconds',None)}s  Out={r.out_dir}"
                    )
                elif r.needs_login:
                    st.warning(
                        f"⚠️ Probe hit a sign-in wall (needs_login=True). Provide a user data dir. Out={r.out_dir}"
                    )
                else:
                    st.error(
                        f"❌ Browser probe did not observe a sheet UI. RepairBanner={r.repair_banner_detected} "
                        f"TimedOut={getattr(r,'timed_out',False)} Out={r.out_dir}"
                    )

                st.markdown("#### Report")
                st.json(r.to_dict())

                if r.out_dir:
                    st.caption(f"Artifacts: {r.out_dir}")
            except Exception as ex:
                st.error(f"Browser probe failed: {ex}")


# ═══════════════════════════════════════════════════════════════════════
# TAB 8: DESKTOP EXCEL PROBE
# ═══════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown("### 🖥 Desktop Excel — Open/Repair Probe")
    st.caption(
        "Launches desktop Microsoft Excel, opens the workbook, auto-clicks common repair dialogs, "
        "captures screenshots, and copies any new %TEMP%/error*.xml recovery logs into Outputs/."
    )

    col1, col2 = st.columns(2)
    with col1:
        desktop_visible = st.checkbox("Show Excel UI (recommended for screenshots)", value=True)
        desktop_try_repair = st.checkbox("Try repair (CorruptLoad=repair)", value=True)
    with col2:
        desktop_save_repaired = st.checkbox("Save repaired copy (SaveCopyAs)", value=True)
        desktop_timeout = st.number_input(
            "Timeout (seconds)",
            min_value=5,
            max_value=60,
            value=15,
            step=5,
            help="Probe is intended to decide open-state quickly; keep this short so we can iterate.",
        )

    if st.button("▶️ Run Desktop Excel Probe", type="primary"):
        try:
            from triage.excel_desktop import probe_open_in_desktop_excel_isolated

            with st.spinner("Running desktop Excel probe (this will launch Excel)…"):
                r = probe_open_in_desktop_excel_isolated(
                    candidate_path=cand_path,
                    out_root="Outputs/excel_runs",
                    visible=desktop_visible,
                    try_repair=desktop_try_repair,
                    save_repaired_copy=desktop_save_repaired,
                    timeout_seconds=int(desktop_timeout),
                )

            st.success(
                f"Probe complete. Opened={r.opened} Fatal={r.fatal} TimedOut={getattr(r,'timed_out',False)} "
                f"Elapsed={getattr(r,'elapsed_seconds',None)}s  Out={r.out_dir}"
            )
            st.markdown("#### Report")
            st.json(r.to_dict())

            if r.screenshots:
                st.markdown("#### Screenshots")
                for p in r.screenshots[:30]:
                    try:
                        st.image(p, caption=os.path.basename(p))
                    except Exception:
                        st.write(p)

            if r.recovery_logs:
                st.markdown("#### Recovery XML")
                for rec in r.recovery_logs[:10]:
                    st.write(rec.get("copied", ""))
                    snip = rec.get("snippet", "")
                    if snip:
                        st.code(snip[:1500])
        except Exception as ex:
            st.error(f"Desktop probe failed: {ex}")

