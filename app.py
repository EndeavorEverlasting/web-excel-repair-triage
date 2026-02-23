"""
app.py — Web-Excel Repair Triage  (Streamlit UI)
Run:  streamlit run app.py
"""
from __future__ import annotations
import io
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
from triage.patcher import apply_recipe, PatchError

# ── CSS theme ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* dark sidebar */
  [data-testid="stSidebar"] { background:#0d1117; }
  /* header strip */
  .main-header {
    background: linear-gradient(90deg,#0e4c2f 0%,#1a7a4a 100%);
    padding:18px 28px; border-radius:8px; margin-bottom:18px;
    color:#ffffff;
  }
  .main-header h1 { margin:0; font-size:1.7rem; letter-spacing:.5px; }
  .main-header p  { margin:4px 0 0; font-size:.9rem; opacity:.85; }
  /* gate cards */
  .gate-pass { background:#0d3320; border-left:4px solid #28a745;
               padding:10px 14px; border-radius:6px; margin:4px 0; }
  .gate-fail { background:#3d1515; border-left:4px solid #dc3545;
               padding:10px 14px; border-radius:6px; margin:4px 0; }
  .gate-warn { background:#332500; border-left:4px solid #ffc107;
               padding:10px 14px; border-radius:6px; margin:4px 0; }
  /* patch card */
  .patch-card { background:#0d1f33; border-left:4px solid #4a9ede;
                padding:10px 14px; border-radius:6px; margin:6px 0; font-family:monospace; font-size:.82rem; }
  /* diff line colours */
  .diff-add { color:#7fff7f; }
  .diff-rem { color:#ff7f7f; }
</style>
""", unsafe_allow_html=True)

# ── header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🔬 Web-Excel Repair Triage</h1>
  <p>Structural gate checks · Part diff · Pattern detection · Patch engine · Graph probe</p>
</div>
""", unsafe_allow_html=True)

# ── sidebar: file uploads ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Input Files")
    cand_file = st.file_uploader("Candidate .xlsx", type=["xlsx"], key="candidate")
    rep_file  = st.file_uploader("Repaired .xlsx (optional)", type=["xlsx"], key="repaired")

    st.markdown("---")
    st.markdown("### 🔑 Graph Probe (optional)")
    graph_token = st.text_input("Bearer Token (GRAPH_TOKEN)", type="password",
                                value=os.environ.get("GRAPH_TOKEN",""))
    probe_mode  = st.selectbox("Probe mode", ["Upload & test", "By drive+item", "By share URL"])
    if probe_mode == "By drive+item":
        g_drive = st.text_input("Drive ID")
        g_item  = st.text_input("Item ID")
    elif probe_mode == "By share URL":
        g_share = st.text_input("Share URL")

    st.markdown("---")
    st.markdown("### 📁 Folder Shortcuts")
    for folder in ("Candidates", "Active", "Repaired", "Deprecated"):
        p = Path(folder)
        if p.exists():
            files = sorted(p.glob("*.xlsx"))
            if files:
                with st.expander(f"{folder}/ ({len(files)})"):
                    for f in files:
                        st.caption(f.name)

# ── helper: save upload to temp file ─────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _save_temp(name: str, data: bytes) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", prefix=name[:20]+"_")
    tmp.write(data)
    tmp.flush()
    return tmp.name

# ── main tabs ────────────────────────────────────────────────────────────────
tab_names = ["📊 Overview", "🚦 Gate Checks", "🔀 Part Diff", "🧩 Patterns", "🩹 Patch & Export", "🌐 Graph Probe"]
tabs = st.tabs(tab_names)

if not cand_file:
    for tab in tabs:
        with tab:
            st.info("Upload a **Candidate .xlsx** in the sidebar to begin.")
    st.stop()

# Save uploads
cand_path = _save_temp(cand_file.name, cand_file.read())
rep_path  = _save_temp(rep_file.name, rep_file.read()) if rep_file else None

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

with tabs[1]:
    samples = gate_dict.get("samples", {})
    for key, label in ALL_GATES:
        count = gate_dict["failing_gates"].get(key, 0)
        hits  = samples.get(_GATE_TO_SAMPLE.get(key, key), [])
        with st.expander(f"{'❌' if count else '✅'} {label} ({count})", expanded=bool(count)):
            if hits:
                st.json(hits)
            else:
                st.success("No findings.")

# ═══════════════════════════════════════════════════════════════════════
# TAB 3: PART DIFF
# ═══════════════════════════════════════════════════════════════════════
with tabs[2]:
    if not diff_dict:
        st.info("Upload a **Repaired .xlsx** in the sidebar to enable the diff view.")
    else:
        sm = diff_dict["summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Added",     sm["added"])
        c2.metric("Removed",   sm["removed"])
        c3.metric("Changed",   sm["changed"])
        c4.metric("Unchanged", sm["unchanged"])

        if diff_dict["added"]:
            with st.expander(f"➕ Added parts ({sm['added']})", expanded=True):
                for n in diff_dict["added"]:
                    st.code(n)
        if diff_dict["removed"]:
            with st.expander(f"➖ Removed parts ({sm['removed']})", expanded=True):
                for n in diff_dict["removed"]:
                    st.code(n)
        st.markdown("#### Changed Parts — XML Diff")
        for entry in diff_dict["changed"]:
            delta = entry.get("size_delta", 0) or 0
            sign  = "+" if delta >= 0 else ""
            with st.expander(f"🔀 {entry['part']}  ({sign}{delta} bytes)", expanded=False):
                cols = st.columns(2)
                cols[0].metric("Candidate size", entry.get("candidate_size"))
                cols[1].metric("Repaired size",  entry.get("repaired_size"))
                xd = entry.get("xml_diff","")
                if xd:
                    st.text_area("Unified diff", xd, height=320, key=f"diff_{entry['part']}")
                else:
                    st.caption("(binary part — no text diff)")

# ═══════════════════════════════════════════════════════════════════════
# TAB 4: PATTERNS
# ═══════════════════════════════════════════════════════════════════════
with tabs[3]:
    if not diff_dict:
        st.info("Upload a **Repaired .xlsx** to enable pattern detection.")
    else:
        # Re-run diff as objects (not cached dicts) for pattern detection
        @st.cache_data(show_spinner="Detecting patterns…")
        def _detect_patterns(cp: str, rp: str):
            from triage.diff import diff_packages
            from triage.patterns import detect_all
            dr = diff_packages(cp, rp)
            pats = detect_all(dr)
            return [{"name": p.name, "description": p.description,
                     "parts": p.affected_parts, "confidence": p.confidence,
                     "patch_hint": p.suggested_patch} for p in pats]

        patterns = _detect_patterns(cand_path, rep_path)
        if not patterns:
            st.success("No known repair patterns detected in this diff.")
        else:
            st.warning(f"{len(patterns)} repair pattern(s) detected.")
            for pat in patterns:
                conf_colour = {"HIGH":"🔴","MEDIUM":"🟠","LOW":"🟡"}.get(pat["confidence"],"⚪")
                with st.expander(f"{conf_colour} **{pat['name']}**  [{pat['confidence']}]", expanded=True):
                    st.markdown(pat["description"])
                    st.markdown(f"**Affected parts:** `{'`, `'.join(pat['parts'])}`")
                    if pat["patch_hint"]:
                        st.info(f"💡 Patch hint: {pat['patch_hint']}")

# ═══════════════════════════════════════════════════════════════════════
# TAB 5: PATCH & EXPORT
# ═══════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("### 🩹 Auto-generated Patch Recipe")

    gate_report = run_all(cand_path)
    gate_recipe  = recipe_from_gates(gate_report)

    if diff_dict and rep_path:
        @st.cache_data(show_spinner=False)
        def _full_recipe(cp, rp):
            from triage.diff import diff_packages
            from triage.patterns import detect_all
            from triage.report import recipe_from_patterns, merge_recipes, recipe_from_gates
            from triage.gate_checks import run_all
            dr  = diff_packages(cp, rp)
            pats = detect_all(dr)
            gr  = run_all(cp)
            r1  = recipe_from_gates(gr)
            r2  = recipe_from_patterns(cp, pats)
            return merge_recipes(r1, r2).to_dict()
        recipe_dict = _full_recipe(cand_path, rep_path)
    else:
        recipe_dict = gate_recipe.to_dict()

    recipe_json = json.dumps(recipe_dict, indent=2)

    st.json(recipe_dict)
    st.download_button("⬇️ Download patch_recipe.json", recipe_json,
                       file_name="patch_recipe.json", mime="application/json")

    st.markdown("---")
    st.markdown("### ▶️ Apply Recipe & Download Patched .xlsx")
    uploaded_recipe = st.file_uploader("Override recipe JSON (optional)", type=["json"], key="recipe_upload")

    if st.button("Apply & Export", type="primary"):
        try:
            final_recipe = json.loads(uploaded_recipe.read()) if uploaded_recipe else recipe_dict
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_out:
                out_path = tmp_out.name
            apply_recipe(cand_path, final_recipe, out_path)
            patched_bytes = Path(out_path).read_bytes()
            st.success(f"Patch applied! {len(patched_bytes):,} bytes.")
            st.download_button("⬇️ Download patched .xlsx", patched_bytes,
                               file_name=f"{Path(cand_file.name).stem}_patched.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except PatchError as e:
            st.error(f"Patch error:\n{e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# TAB 6: GRAPH PROBE
# ═══════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("### 🌐 Microsoft Graph — Web Excel Openability Probe")
    st.caption("Requires a valid Bearer token with **Files.ReadWrite** scope on the target OneDrive.")

    if not graph_token:
        st.warning("Enter a **Bearer Token** in the sidebar to enable this feature.")
    else:
        if st.button("🚀 Run Graph Probe", type="primary"):
            from triage.graph_probe import (
                probe_upload_and_test, probe_by_item, probe_by_share_url, GraphResult
            )
            with st.spinner("Probing Excel for Web via Graph API…"):
                try:
                    if probe_mode == "Upload & test":
                        result = probe_upload_and_test(graph_token, cand_path,
                                                       remote_name=cand_file.name)
                    elif probe_mode == "By drive+item":
                        result = probe_by_item(graph_token, g_drive, g_item)
                    else:
                        result = probe_by_share_url(graph_token, g_share)

                    if result.success:
                        st.success(f"✅ Graph probe PASSED — {len(result.worksheets)} worksheets visible.")
                        st.json({"worksheets": result.worksheets})
                    else:
                        st.error(f"❌ Graph probe FAILED at step '{result.step}' "
                                 f"(HTTP {result.status_code})")
                        if result.error:
                            st.code(result.error)
                except Exception as ex:
                    st.error(f"Exception during probe: {ex}")

