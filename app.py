"""
app.py — Web-Excel Repair Triage  (Streamlit UI)
Run:  python -m streamlit run app.py
"""
from __future__ import annotations
import dataclasses
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
from triage.path_policy import is_deprecated_path
from triage.promote import PromotionError, promote_to_active
from triage.repo_engine import scan_repo as repo_scan_repo, write_report as repo_write_report
from triage.insight_ingest import ingest_xml_insights
from triage.repo_apply import apply_recommendations
from triage.storage_policy import budget_status, default_outputs_budget_bytes
from triage.tutorial import get_tutorial_sections

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


def _rerun_safe() -> None:
    """Compatibility wrapper (Streamlit renamed experimental_rerun → rerun)."""
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()  # type: ignore[attr-defined]
        except Exception:
            return


def _render_tutorial() -> None:
    """First-run onboarding tutorial (dismissible + re-openable from sidebar)."""
    if "tutorial_dismissed" not in st.session_state:
        st.session_state["tutorial_dismissed"] = False

    # Sidebar toggle to bring it back.
    with st.sidebar:
        st.markdown("---")
        if st.session_state.get("tutorial_dismissed", False):
            if st.button("👋 Show tutorial", key="tutorial_show"):
                st.session_state["tutorial_dismissed"] = False
                _rerun_safe()

    expanded = not bool(st.session_state.get("tutorial_dismissed", False))
    with st.expander("👋 Tutorial (first run)", expanded=expanded):
        st.markdown('<div class="tutorial-box">', unsafe_allow_html=True)
        for sec in get_tutorial_sections():
            st.markdown(f"**{sec.title}**")
            st.markdown(sec.markdown)

        c1, c2 = st.columns([1, 6])
        with c1:
            if st.button("✅ Got it", key="tutorial_dismiss"):
                st.session_state["tutorial_dismissed"] = True
                _rerun_safe()
        with c2:
            st.caption("Tip: you can bring this back any time from the sidebar.")
        st.markdown("</div>", unsafe_allow_html=True)


_render_tutorial()

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


def _html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _gate_tooltip(gate_dict: dict) -> str:
    fg = gate_dict.get("failing_gates", {}) or {}
    samples = gate_dict.get("samples", {}) or {}

    if not fg:
        return "PASS (no failing gates)"

    # failing_gates keys do not always match samples keys (historical naming).
    sample_key_for_gate = {
        "stopship_tokens": "stopship",
        "cf_ref_hits": "cf_ref",
        "styles_dxf_integrity": "styles_dxf",
        "illegal_control_chars": "illegal_control",
        "rels_missing_targets": "rels_missing",
    }

    def _sample_summary(gate_key: str, sample: dict) -> str:
        # Keep these single-line-ish for HTML title tooltips.
        if gate_key == "stopship_tokens":
            return f"{sample.get('part')} → {sample.get('token')} ({(sample.get('formula_snippet') or '')[:60]})"
        if gate_key == "calcchain_invalid":
            return f"{sample.get('sheet_part')}:{sample.get('cell')} ({sample.get('reason')})"
        if gate_key == "cf_policy_deploymenttracker":
            rid = sample.get("rule_id")
            sev = sample.get("severity")
            return f"{rid} ({sev}) on {sample.get('table_part')}"
        if gate_key == "cf_ref_hits":
            return f"{sample.get('part')} → #REF! in conditionalFormatting"
        if gate_key == "tablecolumn_lf":
            v = (sample.get("value") or "").replace("\n", "\\n").replace("\r", "\\r")
            return f"{sample.get('part')} → tableColumn/@name has newline: {v[:40]}"
        if gate_key == "shared_ref_oob":
            return f"{sample.get('part')} si={sample.get('si')} ref={sample.get('ref')} (maxRow={sample.get('sheet_max_row')})"
        if gate_key == "shared_ref_bbox":
            return f"{sample.get('part')} si={sample.get('si')} declared={sample.get('declared_ref')} actual={sample.get('actual_ref')}"
        if gate_key == "styles_dxf_integrity":
            return f"{sample.get('part')} → {sample.get('issue')}"
        if gate_key == "xml_wellformed":
            return f"{sample.get('part')} → {sample.get('error')}"
        if gate_key == "illegal_control_chars":
            return f"{sample.get('part')} → illegal control bytes (examples={sample.get('examples')})"
        if gate_key == "rels_missing_targets":
            return f"{sample.get('rels')} → missing {sample.get('resolved')} (from {sample.get('target')})"
        # Fallback
        return str(sample)[:160]

    lines = ["Failing gates (counts + example):"]
    for gate_key, count in fg.items():
        sk = sample_key_for_gate.get(gate_key, gate_key)
        samp_list = samples.get(sk) or []
        if samp_list:
            lines.append(f"- {gate_key}: {count} | e.g. {_sample_summary(gate_key, samp_list[0])}")
        else:
            lines.append(f"- {gate_key}: {count}")

    tip = "\n".join(lines)
    # Prevent absurdly-large title attributes.
    return tip[:2000]


def _render_batch_runner() -> None:
    st.markdown("### 🧪 Batch Runner")
    st.caption(
        "Run endeavor-specific automated testing across a folder of .xlsx files. "
        "Each file is shown as a hoverable card so you can spot flaws quickly."
    )

    preferred = ("Deprecated", "Candidates", "Repaired", "Active")
    folder_choices = [p for p in preferred if Path(p).exists()]
    if not folder_choices:
        folder_choices = ["(no standard folders found)"]
    default_index = folder_choices.index("Deprecated") if "Deprecated" in folder_choices else 0
    folder = st.selectbox("Folder", folder_choices, index=default_index)
    custom = st.text_input("Or custom folder path", value="")
    root = Path(custom) if custom.strip() else Path(folder)
    max_files = st.number_input("Max files", min_value=1, max_value=500, value=50, step=1)
    write_outputs = st.checkbox("Write run artifacts under Outputs/batch_runs/", value=True)

    purpose = (
        "ENDEAVOR: Batch gate check + Deployment Tracker CF policy check. "
        "Goal: identify web-compatibility hazards and policy regressions early, "
        "with errors tailored to the check being performed."
    )
    st.info(purpose)

    if str(root).strip().lower().startswith("active") or root.name.lower() == "active":
        st.warning(
            "Active/ is read-only (golden standards). "
            "Batch Runner will only *analyze* files here; do not repair/patch from Active/."
        )

    # Persisted state so result cards + action buttons continue to work across reruns.
    batch_state: dict = st.session_state.setdefault("batch_runner_state", {})

    b_run, b_clear = st.columns([3, 1])
    run_now = b_run.button("▶ Run batch gates", type="primary")
    clear_now = b_clear.button("🧹 Clear", help="Clear the last Batch Runner results")
    if clear_now:
        batch_state.clear()

    if run_now:
        if not root.exists() or not root.is_dir():
            st.error(f"Folder not found: {root}")
            return

        files = sorted(root.glob("*.xlsx"), key=lambda p: p.name)[: int(max_files)]
        if not files:
            st.warning("No .xlsx files found.")
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = OUTPUTS_DIR / "batch_runs" / f"batch_{ts}"
        if write_outputs:
            out_dir.mkdir(parents=True, exist_ok=True)

        results: list[dict] = []
        prog = st.progress(0)
        for idx, p in enumerate(files, start=1):
            try:
                gd = run_all(str(p)).to_dict()
                results.append({"file": str(p), "gate": gd})
                if write_outputs:
                    (out_dir / (p.stem + "_gates.json")).write_text(
                        json.dumps(gd, indent=2), encoding="utf-8"
                    )
            except Exception as e:  # pragma: no cover (UI only)
                results.append({"file": str(p), "error": repr(e)})
            prog.progress(int(idx * 100 / len(files)))

        if write_outputs:
            run_report = {
                "endeavor": "BATCH_GATES_AND_CF_POLICY",
                "purpose": purpose,
                "root": str(root),
                "timestamp": ts,
                "count": len(results),
                "results": [
                    {
                        "file": r["file"],
                        "pass": ("gate" in r and r["gate"].get("pass")),
                        "failing_gates": (r.get("gate", {}) or {}).get("failing_gates", {}),
                        "error": r.get("error"),
                    }
                    for r in results
                ],
            }
            (out_dir / "run_report.json").write_text(json.dumps(run_report, indent=2), encoding="utf-8")

        batch_state.update(
            {
                "root": str(root),
                "timestamp": ts,
                "write_outputs": bool(write_outputs),
                "out_dir": str(out_dir) if write_outputs else None,
                "results": results,
            }
        )

    results = batch_state.get("results")
    if not results:
        st.info("Run **Batch gates** to populate results, then use per-file or bulk workflow buttons.")
        return

    if batch_state.get("out_dir"):
        st.success(f"Saved run artifacts → {batch_state['out_dir']}")
    st.caption(f"Showing last run: root={batch_state.get('root')}  ts={batch_state.get('timestamp')}")

    st.markdown("#### Results (hover a card for details)")
    st.caption(
        "Workflow: workbooks in Deprecated/ can be auto-fixed / iterated, then copied into Active/ only when they PASS gates."
    )

    # Workflow state (per session): origin Deprecated workbook -> latest working variant.
    wf_latest: dict[str, str] = st.session_state.setdefault("wf_latest", {})
    wf_gates: dict[str, dict] = st.session_state.setdefault("wf_gates", {})

    def _safe_stem(s: str, limit: int = 60) -> str:
        stem = Path(s).stem
        out = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in stem)
        out = out.strip("._-") or "workbook"
        return out[:limit]

    def _current_variant(origin_key: str) -> Path:
        return Path(wf_latest.get(origin_key, origin_key))

    def _current_gate_dict(origin_key: str, origin_gate: dict | None) -> dict | None:
        cur = _current_variant(origin_key)
        if str(cur) == origin_key:
            return origin_gate
        return wf_gates.get(str(cur))

    st.markdown("##### Automation controls")
    c1, c2 = st.columns(2)
    desktop_max_iters = c1.number_input(
        "Desktop iterate: max iterations",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="batch_desktop_max_iters",
    )
    desktop_timeout = c2.number_input(
        "Desktop iterate: timeout (seconds)",
        min_value=5,
        max_value=600,
        value=15,
        step=5,
        key="batch_desktop_timeout",
    )

    st.markdown("##### Bulk workflow buttons")
    st.caption(
        "Philosophy: one-click *local* iteration first (desktop Excel), then one-click *web* iteration (Graph probe loop)."
    )
    bulk_only_failing = st.checkbox(
        "Bulk targets: only files whose CURRENT variant FAILS gates",
        value=True,
        key="bulk_only_failing",
        help="If a file already has a passing working variant, bulk iterate will skip it.",
    )
    bulk_limit = st.number_input(
        "Bulk limit (safety)",
        min_value=1,
        max_value=max(1, len(results)),
        value=min(10, len(results)),
        step=1,
        key="bulk_limit",
    )
    graph_max_iters = st.number_input(
        "Web iterate (Graph): max iterations",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="bulk_graph_max_iters",
    )
    graph_patch_between = st.checkbox(
        "Web iterate (Graph): apply gate patches between probes",
        value=True,
        key="bulk_graph_patch_between",
        help="If enabled: probe → if FAIL → gate recipe patch → probe again.",
    )

    bulk_promote_confirm = st.checkbox(
        "Bulk promote: I understand this copies PASSing variants into Active/",
        value=False,
        key="bulk_promote_confirm",
    )
    bulk_promote_overwrite = st.checkbox(
        "Bulk promote: allow overwrite",
        value=False,
        key="bulk_promote_overwrite",
    )

    col_a, col_b, col_c = st.columns(3)
    if col_a.button("🔁 Iterate locally (Desktop) — bulk", type="primary", key="bulk_desktop_iter_btn"):
        endeavor = (
            "ENDEAVOR: Bulk local iteration — run desktop Excel iterate loop across Deprecated files, "
            "update working variants, and persist artifacts under Outputs/workflow_runs/."
        )
        from triage.desktop_iterate import iterate_until_desktop_clean

        tsb = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = OUTPUTS_DIR / "workflow_runs" / f"batch_local_{tsb}"
        batch_dir.mkdir(parents=True, exist_ok=True)

        # Select targets.
        targets: list[tuple[str, dict | None]] = []
        for r in results:
            if "gate" not in r:
                continue
            origin_key = str(Path(r["file"]))
            if not is_deprecated_path(origin_key):
                continue
            origin_gate = r.get("gate")
            cur_gate = _current_gate_dict(origin_key, origin_gate)
            cur_pass = bool((cur_gate or {}).get("pass"))
            if bulk_only_failing and cur_pass:
                continue
            targets.append((origin_key, origin_gate))
            if len(targets) >= int(bulk_limit):
                break

        if not targets:
            st.info("No eligible Deprecated targets selected for bulk local iteration.")
        else:
            prog = st.progress(0)
            bulk_rows: list[dict] = []
            for idx, (origin_key, origin_gate) in enumerate(targets, start=1):
                origin_path = Path(origin_key)
                cur_path = _current_variant(origin_key)
                file_dir = batch_dir / _safe_stem(origin_key)
                file_dir.mkdir(parents=True, exist_ok=True)
                try:
                    it = iterate_until_desktop_clean(
                        candidate_path=str(cur_path),
                        out_root=str(file_dir / "desktop_iter"),
                        max_iters=int(desktop_max_iters),
                        timeout_seconds=int(desktop_timeout),
                    )
                    (file_dir / "desktop_iterate.json").write_text(
                        json.dumps(dataclasses.asdict(it), indent=2), encoding="utf-8"
                    )

                    wf_latest[origin_key] = str(it.final_path)
                    final_path = Path(it.final_path)
                    post_gate = run_all(str(final_path)).to_dict()
                    wf_gates[str(final_path)] = post_gate
                    (file_dir / "post_gates.json").write_text(
                        json.dumps(post_gate, indent=2), encoding="utf-8"
                    )

                    bulk_rows.append(
                        {
                            "origin": origin_key,
                            "start_variant": str(cur_path),
                            "final_variant": str(final_path),
                            "desktop_clean": bool(it.success_clean),
                            "gate_pass": bool(post_gate.get("pass")),
                            "artifacts_dir": str(file_dir),
                        }
                    )
                except Exception as e:  # pragma: no cover (UI only)
                    bulk_rows.append(
                        {
                            "origin": origin_key,
                            "start_variant": str(cur_path),
                            "error": f"{type(e).__name__}: {e}",
                            "artifacts_dir": str(file_dir),
                        }
                    )
                prog.progress(int(idx * 100 / len(targets)))

            report = {
                "endeavor": "BULK_LOCAL_ITERATE_DESKTOP",
                "purpose": endeavor,
                "timestamp": tsb,
                "count": len(bulk_rows),
                "results": bulk_rows,
            }
            report_path = batch_dir / "bulk_local_report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            st.success(f"Bulk local iteration complete. Report: {report_path}")

    if col_b.button("🌐 Iterate in web (Graph) — bulk", key="bulk_graph_iter_btn"):
        endeavor = (
            "ENDEAVOR: Bulk web iteration (Graph) — probe Excel-for-Web via Microsoft Graph. "
            "Optionally apply deterministic gate patches between probes, then re-probe. "
            "Artifacts saved under Outputs/workflow_runs/."
        )
        if not graph_token:
            st.error(
                "ENDEAVOR: Bulk web iteration (Graph) — refused. Provide a Bearer token in the sidebar Graph Probe section."
            )
        else:
            from triage.graph_probe import probe_upload_and_test

            tsb = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_dir = OUTPUTS_DIR / "workflow_runs" / f"batch_web_{tsb}"
            batch_dir.mkdir(parents=True, exist_ok=True)

            targets: list[tuple[str, dict | None]] = []
            for r in results:
                if "gate" not in r:
                    continue
                origin_key = str(Path(r["file"]))
                if not is_deprecated_path(origin_key):
                    continue
                origin_gate = r.get("gate")
                cur_gate = _current_gate_dict(origin_key, origin_gate)
                cur_pass = bool((cur_gate or {}).get("pass"))
                if bulk_only_failing and cur_pass:
                    continue
                targets.append((origin_key, origin_gate))
                if len(targets) >= int(bulk_limit):
                    break

            if not targets:
                st.info("No eligible Deprecated targets selected for bulk web iteration.")
            else:
                prog = st.progress(0)
                bulk_rows: list[dict] = []
                for idx, (origin_key, origin_gate) in enumerate(targets, start=1):
                    cur_path = _current_variant(origin_key)
                    file_dir = batch_dir / _safe_stem(origin_key)
                    file_dir.mkdir(parents=True, exist_ok=True)
                    try:
                        cur = Path(cur_path)
                        steps: list[dict] = []
                        for itn in range(1, int(graph_max_iters) + 1):
                            # Reuse a stable remote name per workbook+batch run to avoid cluttering OneDrive.
                            remote_name = f"{_safe_stem(origin_key, limit=40)}_{tsb}.xlsx"
                            g = probe_upload_and_test(
                                graph_token,
                                str(cur),
                                remote_name=remote_name,
                                out_root=str(file_dir / "graph_runs"),
                            )
                            g_dict = dataclasses.asdict(g)
                            (file_dir / f"graph_probe_iter{itn}.json").write_text(
                                json.dumps(g_dict, indent=2), encoding="utf-8"
                            )
                            steps.append({"iter": itn, "probe": g_dict, "path": str(cur)})

                            if g.success:
                                break
                            if not graph_patch_between:
                                break

                            gate_obj = run_all(str(cur))
                            recipe = recipe_from_gates(gate_obj)
                            (file_dir / f"gate_recipe_iter{itn}.json").write_text(
                                json.dumps(recipe.to_dict(), indent=2), encoding="utf-8"
                            )
                            if not recipe.patches:
                                steps.append({"iter": itn, "note": "No gate patches generated; stopping."})
                                break

                            patched_path = file_dir / f"{_safe_stem(str(cur))}_webiter{itn}_patched.xlsx"
                            warn_exc = None
                            try:
                                apply_recipe(str(cur), recipe.to_dict(), str(patched_path))
                            except PatchWarning as pw:
                                warn_exc = pw
                                patched_path = Path(pw.output_path)
                            cur = patched_path
                            wf_latest[origin_key] = str(cur)
                            post_gate = run_all(str(cur)).to_dict()
                            wf_gates[str(cur)] = post_gate
                            (file_dir / f"post_gates_after_patch_iter{itn}.json").write_text(
                                json.dumps(post_gate, indent=2), encoding="utf-8"
                            )
                            if warn_exc:
                                steps.append(
                                    {
                                        "iter": itn,
                                        "patch_warning": True,
                                        "skipped": list(getattr(warn_exc, "skipped", []) or []),
                                    }
                                )

                        # Final gate snapshot
                        final_gate = run_all(str(cur)).to_dict()
                        wf_gates[str(cur)] = final_gate
                        (file_dir / "final_gates.json").write_text(
                            json.dumps(final_gate, indent=2), encoding="utf-8"
                        )

                        bulk_rows.append(
                            {
                                "origin": origin_key,
                                "final_variant": str(cur),
                                "gate_pass": bool(final_gate.get("pass")),
                                "steps": steps,
                                "artifacts_dir": str(file_dir),
                            }
                        )
                    except Exception as e:  # pragma: no cover (UI only)
                        bulk_rows.append(
                            {
                                "origin": origin_key,
                                "start_variant": str(cur_path),
                                "error": f"{type(e).__name__}: {e}",
                                "artifacts_dir": str(file_dir),
                            }
                        )
                    prog.progress(int(idx * 100 / len(targets)))

                report = {
                    "endeavor": "BULK_WEB_ITERATE_GRAPH",
                    "purpose": endeavor,
                    "timestamp": tsb,
                    "count": len(bulk_rows),
                    "results": bulk_rows,
                }
                report_path = batch_dir / "bulk_web_report.json"
                report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
                st.success(f"Bulk web iteration complete. Report: {report_path}")

    if col_c.button("⬆️ Promote all PASS variants — bulk", key="bulk_promote_btn"):
        endeavor = (
            "ENDEAVOR: Bulk promote — copy PASSing Deprecated working variants into Active/ (golden standards). "
            "Writes per-file promotion reports under Outputs/workflow_runs/."
        )
        if not bulk_promote_confirm:
            st.warning(
                "ENDEAVOR: Bulk promote — confirmation required. Tick the bulk promote confirmation checkbox first."
            )
        else:
            tsb = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_dir = OUTPUTS_DIR / "workflow_runs" / f"batch_promote_{tsb}"
            batch_dir.mkdir(parents=True, exist_ok=True)

            prog = st.progress(0)
            bulk_rows: list[dict] = []
            eligible: list[str] = []
            for r in results:
                if "gate" not in r:
                    continue
                origin_key = str(Path(r["file"]))
                if not is_deprecated_path(origin_key):
                    continue
                eligible.append(origin_key)
            eligible = eligible[: int(bulk_limit)]
            if not eligible:
                st.info("No eligible Deprecated origins found for bulk promote.")
            else:
                for idx, origin_key in enumerate(eligible, start=1):
                    origin_path = Path(origin_key)
                    cur = _current_variant(origin_key)
                    cur_gate = wf_gates.get(str(cur))
                    if cur_gate is None:
                        try:
                            cur_gate = run_all(str(cur)).to_dict()
                            wf_gates[str(cur)] = cur_gate
                        except Exception as e:  # pragma: no cover
                            bulk_rows.append(
                                {
                                    "origin": origin_key,
                                    "variant": str(cur),
                                    "error": f"Gate check failed before promote: {type(e).__name__}: {e}",
                                }
                            )
                            prog.progress(int(idx * 100 / len(eligible)))
                            continue

                    if not bool((cur_gate or {}).get("pass")):
                        bulk_rows.append(
                            {
                                "origin": origin_key,
                                "variant": str(cur),
                                "skipped": True,
                                "reason": "Current variant does not PASS gates",
                            }
                        )
                        prog.progress(int(idx * 100 / len(eligible)))
                        continue

                    try:
                        pr = promote_to_active(
                            origin_deprecated_path=str(origin_path),
                            source_path=str(cur),
                            allow_overwrite=bool(bulk_promote_overwrite),
                            outputs_dir=str(batch_dir / "promotions"),
                            extra={
                                "gate_pass": True,
                                "promoted_variant": str(cur),
                            },
                        )
                        bulk_rows.append(
                            {
                                "origin": origin_key,
                                "variant": str(cur),
                                "dest": pr.dest_path,
                                "report": pr.report_path,
                            }
                        )
                    except PromotionError as e:
                        bulk_rows.append(
                            {"origin": origin_key, "variant": str(cur), "error": str(e)}
                        )
                    except Exception as e:  # pragma: no cover
                        bulk_rows.append(
                            {
                                "origin": origin_key,
                                "variant": str(cur),
                                "error": f"{type(e).__name__}: {e}",
                            }
                        )
                    prog.progress(int(idx * 100 / len(eligible)))

                report = {
                    "endeavor": "BULK_PROMOTE_TO_ACTIVE",
                    "purpose": endeavor,
                    "timestamp": tsb,
                    "count": len(bulk_rows),
                    "results": bulk_rows,
                }
                report_path = batch_dir / "bulk_promote_report.json"
                report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
                st.success(f"Bulk promote complete. Report: {report_path}")

    st.markdown("---")

    for r in results:
        file_path = Path(r["file"])
        name = file_path.name

        left, right = st.columns([7, 3], gap="small")

        if "error" in r:
            tip = _html_escape(f"ERROR\n{r['error']}")
            left.markdown(
                f'<div class="gate-fail"><span title="{tip}">❌ {name}</span></div>',
                unsafe_allow_html=True,
            )
            right.write("")
            continue

        origin_gate = r["gate"]
        origin_key = str(file_path)
        cur_path = _current_variant(origin_key)
        cur_gate = _current_gate_dict(origin_key, origin_gate)
        display_gate = cur_gate or origin_gate

        tip = _html_escape(_gate_tooltip(display_gate))
        css = "gate-pass" if display_gate.get("pass") else "gate-fail"
        icon = "✅" if display_gate.get("pass") else "❌"
        left.markdown(
            f'<div class="{css}"><span title="{tip}">{icon} {name}</span></div>',
            unsafe_allow_html=True,
        )

        # Actions: only for Deprecated/.
        if not is_deprecated_path(file_path):
            right.caption("Actions disabled (not Deprecated/)")
            continue

        current_path = cur_path
        current_gate = cur_gate

        with right:
	        if str(current_path) != origin_key:
	            st.caption(f"Working variant: {current_path.name}")

	        if st.button("🔄 Re-check gates", key=f"wf_regates::{origin_key}"):
	            with st.spinner("Re-running gates on current variant…"):
	                try:
	                    current_gate = run_all(str(current_path)).to_dict()
	                    wf_gates[str(current_path)] = current_gate
	                    st.success(f"Gate verdict: {'PASS' if current_gate.get('pass') else 'FAIL'}")
	                except Exception as e:  # pragma: no cover (UI only)
	                    st.error(f"ENDEAVOR: Re-check gates — failed. {type(e).__name__}: {e}")

	        if st.button("🩹 Auto-fix once (gate recipe)", key=f"wf_autofix::{origin_key}"):
	            endeavor = (
	                "ENDEAVOR: Auto-fix once (gate recipe) — apply deterministic patches derived from failing gates, "
	                "write artifacts under Outputs/workflow_runs/, then re-check gates."
	            )
	            with st.spinner("Applying deterministic gate recipe…"):
	                try:
	                    ts2 = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
	                    out_dir2 = OUTPUTS_DIR / "workflow_runs" / f"{file_path.stem}_{ts2}"
	                    out_dir2.mkdir(parents=True, exist_ok=True)

	                    gate_obj = run_all(str(current_path))
	                    pre_dict = gate_obj.to_dict()
	                    recipe = recipe_from_gates(gate_obj)
	                    (out_dir2 / "pre_gates.json").write_text(json.dumps(pre_dict, indent=2), encoding="utf-8")
	                    (out_dir2 / "recipe.json").write_text(json.dumps(recipe.to_dict(), indent=2), encoding="utf-8")

	                    if not recipe.patches:
	                        st.info("No deterministic patches generated (already clean or requires manual work).")
	                    else:
	                        patched_path = out_dir2 / f"{file_path.stem}_autofix_{ts2}.xlsx"
	                        warn_exc = None
	                        try:
	                            apply_recipe(str(current_path), recipe.to_dict(), str(patched_path))
	                        except PatchWarning as pw:
	                            warn_exc = pw
	                            patched_path = Path(pw.output_path)

	                        post_dict = run_all(str(patched_path)).to_dict()
	                        (out_dir2 / "post_gates.json").write_text(json.dumps(post_dict, indent=2), encoding="utf-8")

	                        wf_latest[origin_key] = str(patched_path)
	                        wf_gates[str(patched_path)] = post_dict
	                        current_path = patched_path
	                        current_gate = post_dict

	                        if warn_exc:
	                            st.warning(
	                                "PatchWarning: some stub operations were skipped. "
	                                f"Skipped={len(warn_exc.skipped)}"
	                            )

	                        st.success(f"Auto-fix wrote: {patched_path.name}")
	                        st.caption(f"Artifacts: {out_dir2}")
	                except PatchError as e:
	                    st.error(str(e))
	                except Exception as e:  # pragma: no cover (UI only)
	                    st.error(f"{endeavor}\nFAILED: {type(e).__name__}: {e}")

	        if st.button("🔁 Desktop iterate loop", key=f"wf_desktop_iter::{origin_key}"):
	            endeavor = (
	                "ENDEAVOR: Desktop iterate loop — open/repair in desktop Excel, mine fixes, patch, repeat. "
	                "Outputs saved under Outputs/workflow_runs/."
	            )
	            with st.spinner("Running desktop iterate loop (this will launch Excel)…"):
	                try:
	                    from triage.desktop_iterate import iterate_until_desktop_clean

	                    ts2 = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
	                    out_dir2 = OUTPUTS_DIR / "workflow_runs" / f"{file_path.stem}_{ts2}"
	                    out_root = out_dir2 / "desktop_iter"
	                    out_root.mkdir(parents=True, exist_ok=True)

	                    it = iterate_until_desktop_clean(
	                        candidate_path=str(current_path),
	                        out_root=str(out_root),
	                        max_iters=int(desktop_max_iters),
	                        timeout_seconds=int(desktop_timeout),
	                    )
	                    (out_dir2 / "desktop_iterate.json").write_text(
	                        json.dumps(dataclasses.asdict(it), indent=2), encoding="utf-8"
	                    )

	                    wf_latest[origin_key] = str(it.final_path)
	                    current_path = Path(it.final_path)

	                    post_dict = run_all(str(current_path)).to_dict()
	                    wf_gates[str(current_path)] = post_dict
	                    current_gate = post_dict
	                    (out_dir2 / "post_gates.json").write_text(json.dumps(post_dict, indent=2), encoding="utf-8")

	                    st.success(
	                        f"Desktop iterate finished: {'CLEAN' if it.success_clean else 'NOT CLEAN'} — {current_path.name}"
	                    )
	                    st.caption(f"Artifacts: {out_dir2}")
	                except Exception as e:  # pragma: no cover (UI only)
	                    st.error(f"{endeavor}\nFAILED: {type(e).__name__}: {e}")

	        if st.button("↩ Reset variant", key=f"wf_reset::{origin_key}"):
	            wf_latest.pop(origin_key, None)
	            st.info("Reset to original Deprecated file.")

	        # Promote is enabled only when *current* gates pass.
	        pass_now = bool((current_gate or {}).get("pass"))
	        if not pass_now:
	            st.caption("Promote disabled (current variant must PASS gates)")
	        else:
	            confirm = st.checkbox(
	                "Confirm promote",
	                key=f"promote_confirm::{origin_key}",
	                help="This will COPY the workbook into Active/ as a golden standard.",
	            )
	            allow_overwrite = st.checkbox(
	                "Allow overwrite",
	                value=False,
	                key=f"promote_overwrite::{origin_key}",
	                help="Off by default. If a file with the same name exists in Active/, promotion is refused.",
	            )
	            if st.button(
	                "⬆️ Promote → Active",
	                type="primary",
	                key=f"promote_btn::{origin_key}",
	            ):
	                if not confirm:
	                    st.warning(
	                        "ENDEAVOR: Promote to Active — confirmation required. "
	                        "Tick 'Confirm promote' before copying into Active/."
	                    )
	                else:
	                    try:
	                        pr = promote_to_active(
	                            origin_deprecated_path=str(file_path),
	                            source_path=str(current_path),
	                            allow_overwrite=bool(allow_overwrite),
	                            extra={
	                                "gate_pass": True,
	                                "failing_gates": (current_gate or {}).get("failing_gates", {}) or {},
	                                "promoted_variant": str(current_path),
	                            },
	                        )
	                        st.success(f"Promoted → {pr.dest_path}")
	                        st.caption(f"Report: {pr.report_path}")
	                    except PromotionError as e:
	                        st.error(str(e))
	                    except Exception as e:  # pragma: no cover (UI only)
	                        st.error(f"ENDEAVOR: Promote to Active — failed. {type(e).__name__}: {e}")

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


def _render_repo_engine() -> None:
    st.markdown("### 🗂 Repo Engine")
    st.caption(
        "Scan and classify the workspace into lifecycle buckets (Active/Candidates/Repaired/Deprecated/Outputs). "
        "This view is non-destructive: it does not move/delete files."
    )

    st.info(
        "ENDEAVOR: Repo engine — classify artifacts, surface risks, and preserve XML forensic insights. "
        "Goal: keep golden standards in Active/, do work in Deprecated/, and keep Outputs/ organized."
    )

    # Storage budget (safe-by-default). We enforce by skipping new artifact writes
    # when budget is exceeded (no automatic deletion).
    default_budget_b = int(default_outputs_budget_bytes())
    if "repo_engine_outputs_budget_mb" not in st.session_state:
        st.session_state["repo_engine_outputs_budget_mb"] = max(50, int(default_budget_b / (1024 * 1024)))
    budget_mb = st.number_input(
        "Outputs storage budget (MB)",
        min_value=50,
        max_value=200_000,
        value=int(st.session_state["repo_engine_outputs_budget_mb"]),
        step=50,
        key="repo_engine_outputs_budget_mb",
        help="Used to cap new writes into Outputs/. When exceeded, new copies are skipped (no auto-cleanup).",
    )
    outputs_budget_b = int(budget_mb) * 1024 * 1024
    bs = budget_status("Outputs", outputs_budget_b)
    st.caption(
        f"Outputs/ usage: {_fmt_bytes(bs.used_bytes)} / {_fmt_bytes(bs.budget_bytes)} "
        f"(remaining {_fmt_bytes(bs.remaining_bytes)})"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 1) Scan & classify")
        root_choice = st.selectbox(
            "Root to scan",
            ["(repo root)", "Active", "Deprecated", "Candidates", "Repaired", "Outputs"],
            index=1 if Path("Deprecated").exists() else 0,
            key="repo_engine_root_choice",
        )
        custom_root = st.text_input("Or custom folder path", value="", key="repo_engine_custom_root")
        recursive = st.checkbox("Recursive", value=True, key="repo_engine_recursive")
        max_files = st.number_input("Max files", min_value=1, max_value=20000, value=2000, step=100, key="repo_engine_max")
        run_gates = st.checkbox("Also run gate checks on .xlsx (bounded)", value=False, key="repo_engine_run_gates")
        gates_max = st.number_input("Gate-check max workbooks", min_value=0, max_value=2000, value=50, step=10, key="repo_engine_gates_max")
        do_scan = st.button("🔎 Scan now", type="primary", key="repo_engine_scan_btn")

    with col_b:
        st.markdown("#### 2) Ingest external XML insights")
        default_src = tempfile.gettempdir()
        src = st.text_input(
            "External folder or XML file path",
            value=default_src,
            help="Example: %TEMP% or a folder where you saved error*.xml recovery logs.",
            key="repo_engine_xml_src",
        )
        ingest_recursive = st.checkbox("Recursive ingest", value=True, key="repo_engine_ingest_recursive")
        ingest_max = st.number_input("Max XML files", min_value=1, max_value=5000, value=500, step=50, key="repo_engine_ingest_max")
        do_ingest = st.button("📥 Ingest XML", key="repo_engine_ingest_btn")

    if do_scan:
        try:
            root = None
            if custom_root.strip():
                root = custom_root.strip()
            elif root_choice != "(repo root)":
                root = root_choice

            with st.spinner("Scanning and classifying…"):
                res = repo_scan_repo(
                    root=root,
                    recursive=bool(recursive),
                    max_files=int(max_files),
                    run_gates=bool(run_gates),
                    gates_max_files=int(gates_max),
                )
                report_path = repo_write_report(res)

            # Persist recommendations in session state so we can apply them without
            # forcing another scan.
            st.session_state["repo_engine_last_recs"] = [r.__dict__ for r in (res.recommendations or [])]
            st.session_state["repo_engine_last_summary"] = dict(res.summary or {})
            st.session_state["repo_engine_last_report"] = str(report_path)

            st.success(f"Repo scan complete. Report written: {report_path}")
            st.markdown("#### Summary")
            st.json(res.summary)

            if res.recommendations:
                st.markdown("#### Recommendations (non-destructive)")
                st.json([r.__dict__ for r in res.recommendations[:200]])
                if len(res.recommendations) > 200:
                    st.caption(f"Showing first 200 of {len(res.recommendations)} recommendations.")
            else:
                st.caption("No recommendations produced for the scanned set.")
        except Exception as e:  # pragma: no cover (UI only)
            st.error(f"ENDEAVOR: Repo scan — failed. {type(e).__name__}: {e}")

    if do_ingest:
        try:
            if not src.strip():
                st.warning("Enter a source path to ingest from.")
            else:
                insights_budget_b = int(min(outputs_budget_b // 4, 1024**3))  # <= 1GiB, <= 25% of Outputs budget
                with st.spinner("Ingesting XML insights…"):
                    ir = ingest_xml_insights(
                        [src.strip()],
                        recursive=bool(ingest_recursive),
                        max_files=int(ingest_max),
                        budget_bytes=insights_budget_b,
                    )
                st.success(
                    f"Ingest complete. Copied={ir.copied}  SkippedDup={ir.skipped_duplicates}  Errors={ir.errors}"
                )
                st.caption(f"Insights budget: {_fmt_bytes(insights_budget_b)}")
                st.caption(f"Report: {ir.report_path}")
                # Show a small sample.
                st.json(ir.to_dict() if len(ir.insights) <= 25 else {**ir.to_dict(), "insights": [x.__dict__ for x in ir.insights[:25]]})
        except Exception as e:  # pragma: no cover (UI only)
            st.error(f"ENDEAVOR: Insight ingest — failed. {type(e).__name__}: {e}")

    st.markdown("---")
    st.markdown("#### 3) Apply recommendations (opt-in)")
    st.caption(
        "This step can copy/move files to match lifecycle semantics. "
        "By default it copies (non-destructive). Overwrites require confirmation and create backups."
    )

    last_recs = st.session_state.get("repo_engine_last_recs") or []
    applyable = [r for r in last_recs if r.get("suggested_dest")]
    actions_present = sorted({r.get("action") for r in applyable if r.get("action")})
    if not actions_present:
        st.info("Run a scan to generate applyable recommendations.")
        return

    selected_actions = st.multiselect(
        "Recommendation actions to apply",
        options=actions_present,
        default=[a for a in actions_present if a in {"IMPORT_TO_DEPRECATED", "RELOCATE_DEPRECATED_ARTIFACT_TO_OUTPUTS"}],
        key="repo_engine_apply_actions",
    )
    move_mode = st.checkbox("Move instead of copy (deletes sources)", value=False, key="repo_engine_apply_move")
    allow_overwrite = st.checkbox("Allow overwrite at destination (with backup)", value=False, key="repo_engine_apply_overwrite")
    confirm_phrase = ""
    if allow_overwrite:
        confirm_phrase = st.text_input(
            "Type OVERWRITE to confirm overwriting when destination differs",
            value="",
            key="repo_engine_apply_confirm",
        )
        st.caption("Overwrites create a backup under Outputs/backups/ before writing.")

    if st.button("✅ Apply selected recommendations", type="primary", key="repo_engine_apply_btn"):
        try:
            with st.spinner("Applying recommendations…"):
                ar = apply_recommendations(
                    applyable,
                    selected_actions=list(selected_actions),
                    move_instead_of_copy=bool(move_mode),
                    allow_overwrite=bool(allow_overwrite),
                    confirmation_phrase=str(confirm_phrase or ""),
                    budget_root="Outputs",
                    budget_bytes=int(outputs_budget_b),
                )
            st.success(f"Apply complete. ok={ar.summary.get('ok')} skipped={ar.summary.get('skipped')} error={ar.summary.get('error')}")
            st.caption(f"Report: {ar.report_path}")
            st.json(ar.to_dict() if len(ar.ops) <= 25 else {**ar.to_dict(), "ops": [o.__dict__ for o in ar.ops[:25]]})
        except Exception as e:  # pragma: no cover (UI only)
            st.error(f"ENDEAVOR: Apply recommendations — failed. {type(e).__name__}: {e}")

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
    "🧪 Batch Runner",
    "🗂 Repo Engine",
]
tabs = st.tabs(tab_names)

_TAB_BATCH = tab_names.index("🧪 Batch Runner")
_TAB_ENGINE = tab_names.index("🗂 Repo Engine")

if not cand_file:
    for i, tab in enumerate(tabs):
        with tab:
            if i == _TAB_BATCH:
                _render_batch_runner()
            elif i == _TAB_ENGINE:
                _render_repo_engine()
            else:
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
2. All 11 structural gate checks run automatically — each one lights up green ✅ or red ❌.
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
        ("cf_policy_deploymenttracker", "CF policy: Deployment Tracker (severity colors + required rules)"),
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
    "cf_policy_deploymenttracker": "cf_policy_deploymenttracker",
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
    "cf_policy_deploymenttracker":
        "Deployment Tracker policy check: verifies key conditional-formatting rules exist on the "
        "Device_Configuration table and that severity  HIGH/MEDIUM/LOW maps to the intended "
        "fill colors (red/purple/yellow).",
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
**Gate Checks** runs 11 structural hazard checks against every XML part in your workbook.

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


# ═══════════════════════════════════════════════════════════════════════
# TAB: BATCH RUNNER
# ═══════════════════════════════════════════════════════════════════════
with tabs[_TAB_BATCH]:
    _render_batch_runner()


# TAB: REPO ENGINE
# ═══════════════════════════════════════════════════════════════════════
with tabs[_TAB_ENGINE]:
    _render_repo_engine()

