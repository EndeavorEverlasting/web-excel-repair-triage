"""triage/tutorial.py

Tutorial content for the Streamlit UI.

Design goal:
- Keep tutorial data pure (no Streamlit dependency) so it can be unit-tested.
- The UI (app.py) decides how/when to render it (first-run expander, sidebar toggle).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialSection:
    title: str
    markdown: str


def get_tutorial_sections() -> list[TutorialSection]:
    """Return the default onboarding tutorial sections (markdown strings)."""
    return [
        TutorialSection(
            title="What this tool does",
            markdown=(
                "Diagnose why an `.xlsx` triggers **Fix this workbook?** / **WORKBOOK REPAIRED** in Excel for Web, "
                "then generate/apply **byte-safe** patch recipes and verify the result."
            ),
        ),
        TutorialSection(
            title="1) Choose inputs",
            markdown=(
                "- **Candidate .xlsx**: the workbook you want to validate.\n"
                "- **Repaired .xlsx** *(optional)*: the file Excel for Web (or desktop Excel recovery) produced. "
                "Enables **Part Diff** + **Patterns**.\n"
                "- **Bearer Token** *(optional)*: enables the **Graph Probe** tab (upload -> createSession -> listWorksheets)."
            ),
        ),
        TutorialSection(
            title="2) Recommended flow (fast)",
            markdown=(
                "1. Upload Candidate -> check **Overview** (pass/fail at a glance).\n"
                "2. If it fails: open in Excel for Web -> export the *repaired* file -> upload it as **Repaired**.\n"
                "3. Use **Part Diff** + **Patterns** -> generate a recipe in **Patch & Export**.\n"
                "4. Apply/export -> re-test (Graph Probe or Browser/Desktop probes)."
            ),
        ),
        TutorialSection(
            title="Lifecycle folders (mental model)",
            markdown=(
                "- `Active/` = read-only golden standards\n"
                "- `Deprecated/` = working area for iterations\n"
                "- `Outputs/` = generated artifacts (reports/recipes/patched files)"
            ),
        ),
    ]
