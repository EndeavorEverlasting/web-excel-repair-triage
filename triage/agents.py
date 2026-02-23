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

