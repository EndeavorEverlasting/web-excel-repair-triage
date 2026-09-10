from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path("registry/prompts/spec-architecture-prompts.v1.json")
TESTS = Path("tests/test_spec_architecture_prompt_registry.py")

registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
prompt = next(item for item in registry["prompts"] if item["id"] == "P131")
content = prompt["copyContent"]

boundary = """SPRINT / ARTIFACT BOUNDARY
Before creating or changing artifacts, declare:
- REPOSITORY / WORKSPACE — canonical project/repository location;
- BRANCH / REF — exact branch/ref when repository-backed, otherwise N/A;
- MUTATION AUTHORITY — what this run may create or overwrite;
- OWNED SCOPE — presentation, case-study, evidence-table, chart-data, and scenario-data outputs for this request;
- FORBIDDEN SCOPE — source evidence, unrelated project files, secrets/private inputs, and any separately owned work.

Treat source evidence as read-only by default. Never overwrite, rename, move, delete, or reformat source evidence merely to produce the case study. Write generated presentation, case-study, evidence-table, chart-data, and scenario-data artifacts under `Outputs/`; if repository governance mandates a different generated-artifact root, place an `Outputs/` subdirectory under that canonical root rather than inventing another location. Create the directory when permitted.

Before any explicitly authorized overwrite of an existing generated artifact, create a timestamped backup under `Outputs/backups/YYYYMMDD-HHMMSS/` and record the original -> backup -> replacement mapping. Never use this overwrite path for source evidence. If mutation authority, output ownership, or the protected source-evidence boundary cannot be established, stop before file mutation and report the exact blocker.
"""

anchor = "AUDIENCE / PURPOSE\n[portfolio, interview, stakeholder demo, PM case study, data-analysis case study, internal retrospective, or resolve from context]\n\nMISSION"
assert content.count(anchor) == 1, "P131 audience/mission anchor changed"
content = content.replace(anchor, anchor.replace("\n\nMISSION", "\n\n" + boundary + "\nMISSION"), 1)
prompt["copyContent"] = content

prompt["inspectFirst"] = (
    "The project's current repository/source workspace and governance; exact branch/ref when repository-backed; "
    "mutation authority, owned/forbidden scope, protected source-evidence boundary, and canonical Outputs/ location; "
    "README/specs/plans; git history, PRs/issues/releases when accessible; project-management artifacts, task/evidence "
    "ledgers, time records, decisions, milestones, demos/screenshots and measured outcomes; current architecture/system "
    "boundaries; audience/privacy constraints; and any existing canonical artifact or presentation contract. Distinguish "
    "direct evidence from inference before calculating, charting, or mutating artifact files."
)
prompt["expectedOutput"] = (
    "An actual demo deck and companion case study when artifact tooling is available, plus a reusable evidence table and "
    "chart/scenario dataset written under the declared Outputs/ boundary: project origin and evolution, supported "
    "delivery/outcome evaluation, lessons and repeatable method, scale/expansion needs, current design and credible "
    "alternatives, time-spent and task/output distribution visuals, and baseline-versus-scenario perspective charts "
    "whose assumptions and deltas are explicit. Every material metric is labeled measured, derived, estimated, or "
    "counterfactual and traces to evidence or a stated model; source evidence remains preserved."
)
prompt["nextStep"] = (
    "Declare repository/ref, mutation authority, owned/forbidden scope, protected source evidence, and Outputs/ target; "
    "recover the project chronology and quantitative evidence; build the baseline evidence table; then create the "
    "narrative, outcome evaluation, actual-distribution charts, system-design alternatives, and counterfactual scenarios. "
    "Render the presentation/case-study artifacts, inspect them for factual and visual integrity, and revise until the "
    "evidence, calculations, artifact boundaries, and story agree."
)
prompt["proofGate"] = (
    "The delivered case study and presentation are grounded in accessible project evidence; repository/ref and mutation "
    "authority plus owned/forbidden scope are declared; generated artifacts stay under the declared Outputs/ boundary; "
    "source evidence is preserved; any authorized generated-artifact overwrite has a timestamped backup and mapping; "
    "inspiration through repeatable-method narrative is complete; outcome-quality claims are tied to supported criteria; "
    "time and distribution totals reconcile to their stated denominators; every pie chart sums to 100% within rounding; "
    "actual and counterfactual charts are visually and semantically separated; scenario changes state assumptions and "
    "conserve/reallocate a defined baseline rather than manufacturing hours or outcomes; system-design alternatives "
    "include tradeoffs; sensitive/private data is excluded from shareable artifacts; and generated artifacts are "
    "opened/rendered or otherwise inspected when the environment supports it."
)

REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

text = TESTS.read_text(encoding="utf-8")
anchor_test = '        self.assertIn("counterfactual pie chart", " ".join(prompt["keywords"]).lower())\n'
assert text.count(anchor_test) == 1, "P131 test anchor changed"
addition = '''

        boundary_start = content.index("SPRINT / ARTIFACT BOUNDARY")
        artifact_start = content.index("PRESENTATION / DEMO ARTIFACT")
        self.assertLess(boundary_start, artifact_start)
        boundary = content[boundary_start:artifact_start]
        for phrase in (
            "REPOSITORY / WORKSPACE",
            "BRANCH / REF",
            "MUTATION AUTHORITY",
            "OWNED SCOPE",
            "FORBIDDEN SCOPE",
            "source evidence as read-only by default",
            "under `Outputs/`",
            "timestamped backup",
            "Outputs/backups/YYYYMMDD-HHMMSS/",
            "Never use this overwrite path for source evidence",
            "stop before file mutation",
        ):
            self.assertIn(phrase, boundary)
        self.assertIn("source evidence remains preserved", prompt["expectedOutput"])
        self.assertIn("timestamped backup and mapping", prompt["proofGate"])
'''
text = text.replace(anchor_test, anchor_test + addition, 1)
TESTS.write_text(text, encoding="utf-8")

print("P131_ARTIFACT_BOUNDARY_PATCHED=true")
