"""
triage/agents.py
----------------
One agent class per triage phase.  Each agent wraps a single triage module
and exposes a clean .run() interface so they can be called from the Streamlit
UI, from scripts, or from the MCP server (mcp_server.py).

Agent classes
-------------
  GateCheckAgent    – run_all()          → GateReport
  DiffAgent         – diff_packages()    → DiffReport
  PatternAgent      – detect_all()       → List[Pattern]
  RecipeAgent       – merge_recipes()    → PatchRecipe
  PatchAgent        – apply_recipe()     → str (output path)
  GraphProbeAgent   – probe_upload_and_test() → GraphResult
  WebExcelBrowserProbeAgent – probe_open_in_web_excel_isolated() → WebExcelBrowserResult
  ExcelDesktopProbeAgent – probe_open_in_desktop_excel_isolated() → ExcelDesktopProbeResult
  TriageOrchestrator – chains all agents → dict summary

All agents are stateless; instantiate once and call .run() as many times
as needed.
"""
from __future__ import annotations
from typing import List, Optional

from triage.gate_checks import run_all as _gate_run_all, GateReport
from triage.diff import diff_packages, DiffReport
from triage.patterns import detect_all, Pattern
from triage.report import (
    recipe_from_gates,
    recipe_from_patterns,
    merge_recipes,
    PatchRecipe,
)
from triage.patcher import apply_recipe
from triage.graph_probe import probe_upload_and_test, GraphResult
from triage.excel_desktop import (
    ExcelDesktopProbeResult,
    probe_open_in_desktop_excel,
    probe_open_in_desktop_excel_isolated,
)
from triage.web_excel_browser import (
    WebExcelBrowserResult,
    probe_open_in_web_excel_isolated,
)
from triage.dv_engine import (
    extract_dv_spec,
    apply_dv_spec,
    DVSpec,
)
from triage.cf_engine import (
    extract_cf_dictionary,
    apply_cf_dictionary,
    CFDictionary,
)

from triage.path_policy import is_active_path


# ──────────────────────────────────────────────────────────────────────────────
# Phase agents
# ──────────────────────────────────────────────────────────────────────────────

class GateCheckAgent:
    """
    Phase 1 — Structural gate checks.
    Scans a candidate .xlsx for the 10 known OOXML hazards.
    """

    def run(self, candidate_path: str) -> GateReport:
        """
        Parameters
        ----------
        candidate_path : str
            Absolute or relative path to the .xlsx file to inspect.

        Returns
        -------
        GateReport
            Dataclass with .failing_gates, .pass_all, .samples, etc.
            Call .to_dict() for a JSON-serialisable representation.
        """
        return _gate_run_all(candidate_path)


class DiffAgent:
    """
    Phase 2 — Part-level diff between candidate and repaired .xlsx.
    Requires both files; produces a DiffReport with per-part SHA-256 deltas
    and unified XML diffs.
    """

    def run(self, candidate_path: str, repaired_path: str) -> DiffReport:
        """
        Parameters
        ----------
        candidate_path : str
            The workbook you submitted to Excel for Web.
        repaired_path : str
            The workbook Excel for Web returned after repair.

        Returns
        -------
        DiffReport
            .added / .removed / .changed / .unchanged part lists.
            Call .to_dict() for a JSON-serialisable representation.
        """
        return diff_packages(candidate_path, repaired_path)


class PatternAgent:
    """
    Phase 3 — Classify a DiffReport into named repair patterns.
    Patterns map to known Excel-for-Web repair behaviours.
    """

    def run(self, diff_report: DiffReport) -> List[Pattern]:
        """
        Parameters
        ----------
        diff_report : DiffReport
            Output of DiffAgent.run().

        Returns
        -------
        List[Pattern]
            Each Pattern has .name, .description, .confidence, .suggested_patch.
        """
        return detect_all(diff_report)


class RecipeAgent:
    """
    Phase 4 — Build a merged PatchRecipe from gate findings and/or patterns.
    When both are available the recipes are merged and deduplicated.
    """

    def run(
        self,
        source_file: str,
        gate_report: Optional[GateReport] = None,
        patterns: Optional[List[Pattern]] = None,
    ) -> PatchRecipe:
        """
        Parameters
        ----------
        source_file : str
            Path to the candidate .xlsx (stored in recipe metadata).
        gate_report : GateReport, optional
            Output of GateCheckAgent.run().
        patterns : List[Pattern], optional
            Output of PatternAgent.run().

        Returns
        -------
        PatchRecipe
            Merged recipe.  Call .to_json() or .to_dict() to serialise.
        """
        recipes = []
        if gate_report is not None:
            recipes.append(recipe_from_gates(gate_report))
        if patterns:
            recipes.append(recipe_from_patterns(source_file, patterns))
        if not recipes:
            return PatchRecipe(source_file=source_file)
        if len(recipes) == 1:
            return recipes[0]
        return merge_recipes(*recipes)


class PatchAgent:
    """
    Phase 5 — Apply a PatchRecipe (as a dict) to a candidate .xlsx.
    Writes the patched file to disk and returns the output path.
    """

    def run(
        self,
        candidate_path: str,
        recipe: dict,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Parameters
        ----------
        candidate_path : str
            Source .xlsx to patch.
        recipe : dict
            A PatchRecipe serialised to dict (use PatchRecipe.to_dict()).
        output_path : str, optional
            Where to write the patched file.  Defaults to
            <stem>_patched.xlsx next to the source.

        Returns
        -------
        str
            Absolute path of the written output file.
        """
        return apply_recipe(candidate_path, recipe, output_path)


class GraphProbeAgent:
    """
    Phase 6 — Upload a .xlsx to OneDrive and verify Excel for Web opens it
    without triggering the repair banner.
    """

    def run(
        self,
        token: str,
        candidate_path: str,
        remote_name: Optional[str] = None,
    ) -> GraphResult:
        """
        Parameters
        ----------
        token : str
            Microsoft Graph Bearer token with Files.ReadWrite scope.
        candidate_path : str
            Local path to the .xlsx to upload and probe.
        remote_name : str, optional
            Filename to use on OneDrive.  Defaults to the local filename.

        Returns
        -------
        GraphResult
            .success, .step, .status_code, .worksheets, .error.
            Call dataclasses.asdict(result) for a JSON-serialisable dict.
        """
        return probe_upload_and_test(token, candidate_path, remote_name)


class ExcelDesktopProbeAgent:
    """
    Optional — Desktop Excel validation.
    Launches Microsoft Excel (desktop), attempts to open/repair the workbook,
    auto-clicks common recovery dialogs, captures screenshots, and collects
    recoveryLog XML (error*.xml) written to %TEMP%.
    """

    def run(
        self,
        candidate_path: str,
        out_root: str = "Outputs/excel_runs",
        visible: bool = True,
        try_repair: bool = True,
        save_repaired_copy: bool = True,
        timeout_seconds: int = 90,
        isolate_process: bool = True,
    ) -> ExcelDesktopProbeResult:
        fn = probe_open_in_desktop_excel_isolated if isolate_process else probe_open_in_desktop_excel
        return fn(
            candidate_path=candidate_path,
            out_root=out_root,
            visible=visible,
            try_repair=try_repair,
            save_repaired_copy=save_repaired_copy,
            timeout_seconds=timeout_seconds,
        )


class WebExcelBrowserProbeAgent:
    """Optional — real browser UI probe for Excel for the web.

    Opens a workbook sharing link in a browser (via Playwright), checks for DOM
    evidence of a worksheet UI and common repair banner strings, and then closes
    the browser under a strict timeout.
    """

    def run(
        self,
        url: str,
        out_root: str = "Outputs/web_runs",
        timeout_seconds: int = 15,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        browser: str = "chromium",
        channel: Optional[str] = None,
        take_screenshot: bool = False,
    ) -> WebExcelBrowserResult:
        return probe_open_in_web_excel_isolated(
            url=url,
            out_root=out_root,
            timeout_seconds=timeout_seconds,
            headless=headless,
            user_data_dir=user_data_dir,
            browser=browser,
            channel=channel,
            take_screenshot=take_screenshot,
        )


class DVAgent:
    """
    Data Validation engine agent.
    Extracts DV rules from a workbook or applies a DV spec to one.
    """

    def extract(self, path: str) -> DVSpec:
        """Extract all data-validation rules from the workbook at *path*."""
        return extract_dv_spec(path)

    def apply(
        self,
        xlsx_bytes: bytes,
        spec: DVSpec,
        sheet_name_mapping: dict[str, str] | None = None,
    ) -> bytes:
        """Apply a DVSpec to in-memory xlsx bytes, returning patched bytes."""
        return apply_dv_spec(xlsx_bytes, spec, sheet_name_mapping=sheet_name_mapping)

    def apply_file(
        self,
        source_path: str,
        spec: DVSpec,
        output_path: str | None = None,
        sheet_name_mapping: dict[str, str] | None = None,
    ) -> str:
        """Apply a DVSpec to a file on disk.  Returns the output path."""
        import pathlib
        src = pathlib.Path(source_path)
        if is_active_path(src):
            raise ValueError(
                "ENDEAVOR: Apply DV spec — refused. Active/ is read-only (golden standards). "
                f"Copy the workbook into Deprecated/ before applying DV. Source={source_path}"
            )
        if output_path is None:
            output_path = str(src.with_stem(src.stem + "_dv"))
        if is_active_path(output_path):
            raise ValueError(
                "ENDEAVOR: Apply DV spec — refused. Will not write outputs into Active/. "
                f"Choose Outputs/ or Deprecated/. Output={output_path}"
            )
        patched = apply_dv_spec(src.read_bytes(), spec, sheet_name_mapping=sheet_name_mapping)
        out = pathlib.Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(patched)
        return str(out)


class CFAgent:
    """
    Conditional Formatting engine agent.
    Extracts CF dictionary from a workbook or applies one.
    """

    def extract(self, path: str) -> CFDictionary:
        """Extract the full CF dictionary from the workbook at *path*."""
        return extract_cf_dictionary(path)

    def apply(
        self,
        xlsx_bytes: bytes,
        cfd: CFDictionary,
        sheet_name_mapping: dict[str, str] | None = None,
        mode: str = "append",
    ) -> bytes:
        """Apply a CFDictionary to in-memory xlsx bytes."""
        return apply_cf_dictionary(xlsx_bytes, cfd, sheet_name_mapping=sheet_name_mapping, mode=mode)

    def apply_file(
        self,
        source_path: str,
        cfd: CFDictionary,
        output_path: str | None = None,
        sheet_name_mapping: dict[str, str] | None = None,
        mode: str = "append",
    ) -> str:
        """Apply a CFDictionary to a file on disk.  Returns the output path."""
        import pathlib
        src = pathlib.Path(source_path)
        if is_active_path(src):
            raise ValueError(
                "ENDEAVOR: Apply CF dictionary — refused. Active/ is read-only (golden standards). "
                f"Copy the workbook into Deprecated/ before applying CF. Source={source_path}"
            )
        if output_path is None:
            output_path = str(src.with_stem(src.stem + "_cf"))
        if is_active_path(output_path):
            raise ValueError(
                "ENDEAVOR: Apply CF dictionary — refused. Will not write outputs into Active/. "
                f"Choose Outputs/ or Deprecated/. Output={output_path}"
            )
        patched = apply_cf_dictionary(src.read_bytes(), cfd, sheet_name_mapping=sheet_name_mapping, mode=mode)
        out = pathlib.Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(patched)
        return str(out)


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator — chains all phases
# ──────────────────────────────────────────────────────────────────────────────

class TriageOrchestrator:
    """
    Runs the full triage pipeline in one call.
    Each phase is optional; pass None to skip.

    Typical usage
    -------------
    >>> orch = TriageOrchestrator()
    >>> result = orch.run_full_pipeline(
    ...     candidate_path="Candidates/MyBook.xlsx",
    ...     repaired_path="Repaired/MyBook.xlsx",   # optional
    ...     token=None,                              # skip Graph probe
    ... )
    >>> print(result["recipe_json"])
    """

    def __init__(self) -> None:
        self.gate_agent    = GateCheckAgent()
        self.diff_agent    = DiffAgent()
        self.pattern_agent = PatternAgent()
        self.recipe_agent  = RecipeAgent()
        self.patch_agent   = PatchAgent()
        self.graph_agent   = GraphProbeAgent()

    def run_full_pipeline(
        self,
        candidate_path: str,
        repaired_path: Optional[str] = None,
        token: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> dict:
        """
        Run all available phases and return a summary dict.

        Keys in the returned dict
        -------------------------
        gate_report   : dict   – GateReport.to_dict()
        diff_report   : dict | None
        patterns      : list   – [Pattern.__dict__, ...]
        recipe        : dict   – PatchRecipe.to_dict()
        recipe_json   : str    – pretty-printed JSON
        graph_result  : dict | None
        """
        summary: dict = {}

        # Phase 1 — gate checks (always)
        gate = self.gate_agent.run(candidate_path)
        summary["gate_report"] = gate.to_dict()

        # Phase 2 & 3 — diff + patterns (only if repaired file provided)
        diff: Optional[DiffReport] = None
        patterns: List[Pattern] = []
        if repaired_path:
            diff = self.diff_agent.run(candidate_path, repaired_path)
            summary["diff_report"] = diff.to_dict()
            patterns = self.pattern_agent.run(diff)
            summary["patterns"] = [
                {"name": p.name, "confidence": p.confidence,
                 "description": p.description, "suggested_patch": p.suggested_patch}
                for p in patterns
            ]
        else:
            summary["diff_report"] = None
            summary["patterns"] = []

        # Phase 4 — recipe
        recipe = self.recipe_agent.run(
            source_file=candidate_path,
            gate_report=gate,
            patterns=patterns if patterns else None,
        )
        summary["recipe"] = recipe.to_dict()
        summary["recipe_json"] = recipe.to_json()

        # Phase 6 — graph probe (only if token provided)
        if token:
            import dataclasses
            gr = self.graph_agent.run(token, candidate_path)
            summary["graph_result"] = dataclasses.asdict(gr)
        else:
            summary["graph_result"] = None

        return summary

