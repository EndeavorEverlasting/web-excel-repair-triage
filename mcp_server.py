"""
mcp_server.py
-------------
Model Context Protocol (MCP) server for the Web-Excel Repair Triage tool.

Exposes each triage phase as a callable MCP tool so that Augment Code
("auggie") can invoke them directly from the chat panel without opening
the Streamlit UI.

Usage
-----
  # Install the MCP dependency first (once):
  pip install "mcp[cli]"

  # Run the server (keep this terminal open):
  python mcp_server.py

  # Then register it in Augment Code — see README § MCP Configuration.

Tools exposed
-------------
  run_gate_checks      – Phase 1: structural hazard scan
  run_diff             – Phase 2: part-level diff (needs repaired file)
  detect_patterns      – Phase 3: classify diff into named patterns
  generate_recipe      – Phase 4: build a merged patch recipe JSON
  apply_patch_recipe   – Phase 5: apply a recipe dict to a .xlsx
  graph_probe          – Phase 6: upload & probe via Microsoft Graph API
  run_full_pipeline    – All phases in one call
"""
from __future__ import annotations
import json
import dataclasses
from typing import Optional

from mcp.server.fastmcp import FastMCP

from triage.agents import (
    GateCheckAgent,
    DiffAgent,
    PatternAgent,
    RecipeAgent,
    PatchAgent,
    GraphProbeAgent,
    TriageOrchestrator,
)

# ── Server instance ────────────────────────────────────────────────────────────
mcp = FastMCP(
    "excel-triage",
    instructions=(
        "Tools for diagnosing and repairing .xlsx workbooks that trigger the "
        "'Fix this workbook?' / WORKBOOK REPAIRED banner in Excel for Web. "
        "Always start with run_gate_checks. If you have a repaired file, also "
        "call run_diff and detect_patterns before generate_recipe."
    ),
)

# ── Shared agent instances (stateless, safe to reuse) ─────────────────────────
_gate    = GateCheckAgent()
_diff    = DiffAgent()
_pattern = PatternAgent()
_recipe  = RecipeAgent()
_patch   = PatchAgent()
_graph   = GraphProbeAgent()
_orch    = TriageOrchestrator()


# ── Tool definitions ───────────────────────────────────────────────────────────

@mcp.tool()
def run_gate_checks(candidate_path: str) -> dict:
    """
    Phase 1 — Run all 10 structural gate checks on a candidate .xlsx.

    Parameters
    ----------
    candidate_path : str
        Absolute or relative path to the .xlsx file to inspect.

    Returns
    -------
    dict
        GateReport as a dict: pass_all, failing_gates, samples, triage hints.
    """
    report = _gate.run(candidate_path)
    return report.to_dict()


@mcp.tool()
def run_diff(candidate_path: str, repaired_path: str) -> dict:
    """
    Phase 2 — Compute a part-level diff between candidate and repaired .xlsx.

    Parameters
    ----------
    candidate_path : str
        The workbook you submitted to Excel for Web.
    repaired_path : str
        The workbook Excel for Web returned after repair.

    Returns
    -------
    dict
        DiffReport: added/removed/changed/unchanged parts with XML diffs.
    """
    report = _diff.run(candidate_path, repaired_path)
    return report.to_dict()


@mcp.tool()
def detect_patterns(candidate_path: str, repaired_path: str) -> list:
    """
    Phase 3 — Classify the diff into named repair patterns.

    Parameters
    ----------
    candidate_path : str
        The original candidate .xlsx.
    repaired_path : str
        The Excel-repaired .xlsx.

    Returns
    -------
    list
        List of pattern dicts: name, confidence, description, suggested_patch.
    """
    diff_report = _diff.run(candidate_path, repaired_path)
    patterns = _pattern.run(diff_report)
    return [
        {
            "name": p.name,
            "confidence": p.confidence,
            "description": p.description,
            "affected_parts": p.affected_parts,
            "suggested_patch": p.suggested_patch,
        }
        for p in patterns
    ]


@mcp.tool()
def generate_recipe(
    candidate_path: str,
    repaired_path: Optional[str] = None,
) -> str:
    """
    Phase 4 — Generate a merged patch recipe JSON string.

    Runs gate checks always; also runs diff + patterns if repaired_path
    is provided, producing a richer recipe.

    Parameters
    ----------
    candidate_path : str
        Path to the candidate .xlsx.
    repaired_path : str, optional
        Path to the Excel-repaired .xlsx.  Omit for gate-only recipe.

    Returns
    -------
    str
        Pretty-printed JSON patch recipe.  Save to a .json file, edit any
        <FILL_IN_...> placeholders, then call apply_patch_recipe.
    """
    gate = _gate.run(candidate_path)
    patterns = []
    if repaired_path:
        diff_report = _diff.run(candidate_path, repaired_path)
        patterns = _pattern.run(diff_report)
    recipe = _recipe.run(
        source_file=candidate_path,
        gate_report=gate,
        patterns=patterns if patterns else None,
    )
    return recipe.to_json()


@mcp.tool()
def apply_patch_recipe(
    candidate_path: str,
    recipe_json: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Phase 5 — Apply a patch recipe to a candidate .xlsx.

    Parameters
    ----------
    candidate_path : str
        Source .xlsx to patch.
    recipe_json : str
        JSON string of the patch recipe (output of generate_recipe or
        a manually edited recipe file).
    output_path : str, optional
        Where to write the patched file.  Defaults to
        Outputs/<stem>_patched.xlsx.

    Returns
    -------
    str
        Path of the written output file.
    """
    recipe_dict = json.loads(recipe_json)
    if output_path is None:
        from pathlib import Path
        src = Path(candidate_path)
        output_path = str(Path("Outputs") / (src.stem + "_patched.xlsx"))
        Path("Outputs").mkdir(exist_ok=True)
    return _patch.run(candidate_path, recipe_dict, output_path)


@mcp.tool()
def graph_probe(
    token: str,
    candidate_path: str,
    remote_name: Optional[str] = None,
) -> dict:
    """
    Phase 6 — Upload a .xlsx to OneDrive and probe it via Microsoft Graph.

    Parameters
    ----------
    token : str
        Bearer token with Files.ReadWrite scope (from Graph Explorer).
    candidate_path : str
        Local path to the .xlsx to upload and test.
    remote_name : str, optional
        Filename to use on OneDrive.  Defaults to the local filename.

    Returns
    -------
    dict
        GraphResult: success, step, status_code, worksheets, error.
    """
    result = _graph.run(token, candidate_path, remote_name)
    return dataclasses.asdict(result)


@mcp.tool()
def run_full_pipeline(
    candidate_path: str,
    repaired_path: Optional[str] = None,
    token: Optional[str] = None,
) -> dict:
    """
    Run all triage phases in sequence and return a combined summary.

    Parameters
    ----------
    candidate_path : str
        Path to the candidate .xlsx.
    repaired_path : str, optional
        Path to the Excel-repaired .xlsx (enables diff + patterns).
    token : str, optional
        Graph Bearer token (enables Graph probe).

    Returns
    -------
    dict
        Keys: gate_report, diff_report, patterns, recipe, recipe_json,
        graph_result.
    """
    return _orch.run_full_pipeline(candidate_path, repaired_path, token)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()

