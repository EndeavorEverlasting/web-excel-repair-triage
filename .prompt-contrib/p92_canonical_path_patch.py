from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
BASE_PROMPTS = ROOT / "docs/prompts.json"
TEST = ROOT / "tests/test_spec_architecture_prompt_registry.py"
BUILDER = ROOT / "build_prompt_kit.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
p92 = next(item for item in payload["prompts"] if item["id"] == "P92")

expected_identity = {
    "id": "P92",
    "seq": "92",
    "name": "Production-Path Proof Gap Auditor",
    "type": "VERIFY + REPAIR",
    "class": "TESTING / PRODUCTION PATH",
    "color": "Cyan",
    "copySheet": "P92_COPY_SAFE",
    "category": "standard",
    "profile": "spec-architecture",
}
actual_identity = {key: p92[key] for key in expected_identity}
if actual_identity != expected_identity:
    raise SystemExit(f"P92 identity drift before hardening: {actual_identity!r}")

p92.update(
    {
        "name": "Canonical Path Prompt",
        "class": "HARNESS / CANONICAL PATH",
        "sprintRole": (
            "Establish and enforce one repository-owned, machine/profile-aware canonical development checkout and production/use path for an app, "
            "prevent agents and humans from scattering duplicate working copies, and separate remote integration proof from local workstation deployment proof"
        ),
        "useWhen": (
            "Agents or humans are using, cloning, installing, launching, or updating a repository and its canonical development or production path is missing, "
            "ambiguous, inconsistent across tools, or contradicted by field reality; especially when GitHub main is current but the workstation checkout/install may still be stale."
        ),
        "inspectFirst": (
            "Current remote/default-branch truth; repository governance and harness entrypoints; existing machine/profile, path, launcher, installer, updater, and worktree contracts; "
            "known local checkouts/installs when observable; current working directory; real operator entrypoint; dirty/unique work; and tests/CI that claim path or deployment readiness."
        ),
        "expectedOutput": (
            "A canonical-path ledger plus a repo-owned harness contract that names the development checkout, production/use path, optional worktree root, profile/platform key, and entrypoint; "
            "resolvers/validators or existing harness integration that consume that contract; safe disposition of noncanonical copies without deleting unique work; "
            "and separate evidence for remote integration, local development freshness, production/install freshness, and real-entrypoint behavior."
        ),
        "nextStep": (
            "Resolve current repository and machine/profile truth, find or create the single canonical path contract, reconcile any conflicting checkout without destroying unique work, "
            "wire the contract into the repository's normal harness/launcher/update path, then prove the canonical development and production paths separately before calling the app locally ready."
        ),
        "proofGate": (
            "The repository has exactly one authoritative path owner per supported machine/profile; development, production/use, and temporary worktree roles are explicit; normal harness/launcher/update flows consume it; "
            "noncanonical locations are blocked or clearly diagnosed without destructive cleanup; a remote merged SHA is never treated as local deployment proof; and the strongest safe same-entrypoint check confirms the resolved production path or reports an exact inaccessible-runtime blocker."
        ),
        "copyContent": """ESTABLISH AND ENFORCE THE CANONICAL DEVELOPMENT AND PRODUCTION PATH FOR THIS REPOSITORY. DO NOT LET AGENTS OR HUMANS INVENT A NEW LOCATION BECAUSE ANOTHER PATH IS CONVENIENT.

Repo/app: xyz_repo_or_app
Machine/profile: xyz_machine_profile_or_resolve_from_evidence
Observed current path, if any: xyz_current_path_or_unknown
Observed production/use entrypoint, if any: xyz_entrypoint_or_unknown

MISSION
Give this repository one durable answer to two different questions: `Where do we develop it?` and `Where do we run/use it in production?` Encode those answers in the repository harness so future agents, scripts, launchers, and human operators resolve the same locations instead of scattering clones, worktrees, installs, generated state, or partial app copies across the computer.

This prompt also closes a recurring proof error: remote repository completion is not local workstation deployment. A feature merged into GitHub `main@SHA` proves remote integration only. It does not prove the canonical local checkout contains that SHA, that a separate production/install path was refreshed, or that the operator entrypoint can use the new file.

1. REFRESH TRUTH BEFORE CHOOSING A PATH
- Refresh remote/provider truth and resolve the actual default branch; do not infer the repository floor from a stale local branch.
- Read current repository governance, harness maps/registries/contracts, machine/profile routing, launchers, installers/updaters, and worktree conventions before adding another path surface.
- Inspect the actual current working directory and known checkout/install locations when the environment exposes them.
- Never invent a repository-specific path from model preference, a different AI's convention, a remembered path from another machine, or a convenient temp/Desktop/AppData/OneDrive directory.
- A remembered chat path is evidence to verify, not authority by itself. Tracked repository/profile contracts own the durable answer.

2. DEFINE PATH ROLES EXPLICITLY
For each supported machine/profile, resolve and record:
- CANONICAL DEVELOPMENT CHECKOUT — the normal writable Git checkout used for development and repository maintenance;
- CANONICAL PRODUCTION / USE PATH — the installed, synchronized, served, or operator-facing location from which the app is actually used;
- CANONICAL WORKTREE ROOT — optional, for isolated parallel or recovery worktrees; temporary worktrees are not alternate canonical checkouts;
- CANONICAL ENTRYPOINT — launcher/command/script that consumes the production/use path;
- PATH RELATION — whether development and production are intentionally the same location or require an explicit sync/install/promotion step.
Do not collapse these roles merely because one machine currently happens to use the same directory for both.

3. CODIFY IT IN THE APP'S HARNESS
Reuse an existing machine/profile/path registry when one already owns this data. Otherwise create the repository's normal minimal versioned path contract, preferring `harness/canonical-paths.v1.json` when no stronger local convention exists. The durable contract must be machine-readable and discoverable from the harness entrypoint.

At minimum encode the repository identity, machine/profile key, canonical development checkout, canonical production/use path, optional worktree root, canonical entrypoint, and path-resolution precedence. Use environment/profile variables where portability requires them; do not commit secrets or user-private evidence.

Wire the contract into existing repository-native behavior where applicable: doctor/preflight, repo intake, launcher, updater/sync command, path resolver, worktree helper, validation profile, or operator status command. Do not create a second harness merely to store the same fact.

4. PREVENT PATH SPRAWL AND COMPUTER BLOAT
Before cloning, installing, generating a worktree, or telling the operator to `cd` somewhere:
- resolve the canonical contract first;
- search the bounded expected locations for an existing canonical checkout/install when safe;
- distinguish CLONE, WORKTREE, INSTALL, MIRROR, CACHE, OUTPUT, and BACKUP rather than treating every repo-looking directory as interchangeable;
- refuse to create a second normal development checkout when the canonical one exists and is usable;
- keep parallel writers in isolated worktrees under the approved worktree root rather than sharing mutable state;
- do not promote Temp, Downloads, random Desktop folders, OneDrive mirrors/backups, or app-data caches into canonical source locations unless the repository contract explicitly owns that role.

When noncanonical copies already exist, inventory and classify them first. Preserve dirty, unpushed, unique, or separately owned work. Consolidate, archive, or remove only through the repository's normal safe cleanup policy; never force-reset or delete merely to make the machine look tidy.

5. FAIL CLOSED ON PATH DRIFT
A harness, launcher, updater, or operator command that detects a path mismatch should report the canonical path, the observed path, the role being attempted, and the exact safe next action. It should not silently create another clone or continue from an UNKNOWN location when path identity matters.

Use evidence states such as:
- CANONICAL + PROVED;
- NONCANONICAL + PRESERVE;
- NONCANONICAL + DISPOSABLE;
- MISSING;
- CONFLICT;
- UNKNOWN.
UNKNOWN is not permission to guess.

6. REMOTE INTEGRATION IS NOT LOCAL DEPLOYMENT
Track these proof levels separately:
- REMOTE_INTEGRATED — intended commit is contained in the refreshed remote default branch;
- DEV_CHECKOUT_CURRENT — the canonical development checkout contains the required integrated commit and is safely reconciled;
- PROD_PATH_CURRENT — the canonical production/use path has consumed the required version through its real sync/install/promotion mechanism;
- ENTRYPOINT_PROVED — the real operator entrypoint resolves the canonical production path and observes the intended behavior.

Do not say an app is updated on PTOP, an Admin Box, a server, or another machine merely because GitHub merged the code. If the local checkout has not fetched/reconciled it, a newly added command or file may simply not exist there. If production is a separate installed path, updating the development checkout still does not prove the production copy was refreshed.

7. MAP BOTH PATHS WHEN TEST PROOF IS INVOLVED
After filesystem/location identity is proved, preserve the original production-path audit discipline:
A. REAL: operator action -> canonical production/use path -> launcher/wrapper -> shell/interpreter -> configuration/environment -> services/native boundaries -> result.
B. TEST: test runner -> checkout/fixture/helper -> exercised boundaries -> assertions.
For each material boundary mark SAME + PROVED, SAME + WEAKER INPUT, SIMULATED/MOCKED, BYPASSED, PRODUCTION-ONLY, or UNKNOWN. Green helper tests do not prove a production wrapper, installed copy, or workstation path they never invoked. Use same-entrypoint synthetic proof when live execution is unavailable but the real launcher can be exercised safely.

8. MACHINE / PROFILE PORTABILITY
Canonical does not mean one literal path string for every computer or OS. It means one repository-owned resolution rule for each supported profile. A Windows development path and an Android/Termux path may differ, but both must be explicit profile records. Never emit a command for one shell/profile merely because it is valid on another. If current host and target profile differ, route or hand off according to the existing harness contract rather than fabricating a local path.

9. SECOND PASS — TRY TO CREATE THE BUG AGAIN
After the first repair, ask:
- Could another agent entering fresh still choose a different directory?
- Could a launcher use a stale install while GitHub/main and the dev checkout are current?
- Could a parallel agent create a second mutable checkout instead of a worktree?
- Could a backup/mirror/cache be mistaken for source authority?
- Could a path resolver fall back silently when the canonical record is missing?
Add the smallest practical regression or validator for every concrete gap found and rerun the affected path proof. Stop at a bounded fixed point; do not manufacture path bureaucracy.

10. DELIVER
Report the canonical development path, production/use path, worktree root if applicable, owning harness contract/resolver, noncanonical copies and their safe disposition, remote/default-branch SHA, local freshness proof, production freshness proof, entrypoint proof, files/commit/PR/integration state, and exact blocker for any machine that could not be inspected.

CLOSURE RULE
The path problem is closed only when future agents and human operators can derive the same development and production locations from repository-owned evidence, the harness prevents or diagnoses practical path drift, unique work is preserved, and remote integration is no longer confused with local deployment.""",
        "keywords": [
            "canonical path",
            "canonical repository path",
            "canonical checkout",
            "development path",
            "production path",
            "production use path",
            "local deployment path",
            "repo location",
            "repository location",
            "path drift",
            "duplicate checkout",
            "scattered clones",
            "repository bloat",
            "machine profile path",
            "worktree root",
            "remote integration local deployment",
            "production path proof gap",
            "green tests field failure",
            "entrypoint audit",
            "test path mismatch",
            "runtime boundary",
            "production-only boundary",
            "proof ceiling",
        ],
    }
)
REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

base_prompts = json.loads(BASE_PROMPTS.read_text(encoding="utf-8"))
p01 = next(item for item in base_prompts if item["id"] == "P01")
if p01["name"] != "Harness Infrastructure Builder":
    raise SystemExit(f"P01 identity drift before hardening: {p01['name']!r}")
if "CANONICAL PATH CONTRACT" in p01["copyContent"]:
    raise SystemExit("P01 already contains canonical path contract; refuse duplicate insertion")
p01["inspectFirst"] = (
    "Existing AGENTS.md/governance contract, repo structure, test runners, validators, scripts, manifests, docs, generated-output policy, branch/PR conventions, "
    "any partial harness artifacts, and existing machine/profile/path/launcher/install/update conventions so a harness does not invent a competing repository location."
)
p01["expectedOutput"] = (
    "Implemented and validated harness components committed to the repository: codebase map, workflow specs, artifact registry, validators, hooks (where useful), scoped skills, operator reports, "
    "and a machine-readable canonical development/production path contract or an explicit evidence-backed NOT-APPLICABLE disposition."
)
p01["proofGate"] = (
    "Each required harness component is tracked and validated; the harness resolves or explicitly dispositioned canonical development/production paths per supported machine/profile without inventing competing locations; "
    "remote integration is not promoted to local deployment proof; commit exists; push or PR state is reported."
)
anchor = "\n\nBUILD PROCEDURE\n"
section = """

8. CANONICAL PATH CONTRACT
   - Every app harness must answer where normal development occurs and where the app is actually used/installed/served in production for each supported machine/profile, or record why that distinction is not applicable.
   - Reuse an existing path/profile registry when one exists. Otherwise add one machine-readable canonical owner and route agents, launchers, updaters, worktree helpers, and operator status through it.
   - Distinguish canonical development checkout, production/use path, temporary worktree root, and real operator entrypoint. Do not let a fresh agent choose a new directory from model preference.
   - Prevent path sprawl: a second mutable clone is not a substitute for the canonical checkout; preserve unique/dirty work and use approved isolated worktrees for parallel writers.
   - Treat `remote main contains SHA`, `canonical development checkout is current`, `production/use path is current`, and `real entrypoint observes it` as different proof states. GitHub merge success alone is not workstation deployment proof.
   - P92 Canonical Path Prompt owns deep repair/audit of this contract; P01 must ensure the harness has the seam so P92 has one canonical owner to inspect and strengthen.
"""
if anchor not in p01["copyContent"]:
    raise SystemExit("P01 build-procedure anchor missing")
p01["copyContent"] = p01["copyContent"].replace(anchor, section + anchor, 1)
BASE_PROMPTS.write_text(json.dumps(base_prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

builder = BUILDER.read_text(encoding="utf-8")
anchor = '    "set terminal directory": "P61", "set working directory": "P61", "repository checkout": "P61",\n'
addition = (
    anchor
    + '    "canonical path": "P92", "canonical repository path": "P92", "canonical checkout": "P92",\n'
    + '    "development path": "P92", "production path": "P92", "local deployment path": "P92",\n'
    + '    "repo location": "P92", "repository location": "P92", "path drift": "P92", "scattered clones": "P92",\n'
)
if '"canonical path": "P92"' not in builder:
    if anchor not in builder:
        raise SystemExit("P61 discovery anchor missing")
    builder = builder.replace(anchor, addition, 1)
BUILDER.write_text(builder, encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
test = test.replace(
    '"P92": ("Production-Path Proof Gap Auditor", "TESTING / PRODUCTION PATH"),',
    '"P92": ("Canonical Path Prompt", "HARNESS / CANONICAL PATH"),',
    1,
)
old_assertions = '''        p92 = self.full["P92"]["copyContent"]
        self.assertIn("MAP BOTH PATHS", p92)
        self.assertIn("PRODUCTION-ONLY", p92)
        self.assertIn("Green helper tests do not prove a production wrapper", p92)
        self.assertIn("same-entrypoint synthetic proof", p92)
'''
new_assertions = '''        p92_prompt = self.full["P92"]
        p92 = p92_prompt["copyContent"]
        self.assertEqual(p92_prompt["name"], "Canonical Path Prompt")
        self.assertEqual(p92_prompt["class"], "HARNESS / CANONICAL PATH")
        for phrase in (
            "ESTABLISH AND ENFORCE THE CANONICAL DEVELOPMENT AND PRODUCTION PATH",
            "CANONICAL DEVELOPMENT CHECKOUT",
            "CANONICAL PRODUCTION / USE PATH",
            "harness/canonical-paths.v1.json",
            "PREVENT PATH SPRAWL AND COMPUTER BLOAT",
            "REMOTE INTEGRATION IS NOT LOCAL DEPLOYMENT",
            "REMOTE_INTEGRATED",
            "DEV_CHECKOUT_CURRENT",
            "PROD_PATH_CURRENT",
            "ENTRYPOINT_PROVED",
            "UNKNOWN is not permission to guess",
            "MAP BOTH PATHS WHEN TEST PROOF IS INVOLVED",
            "PRODUCTION-ONLY",
            "Green helper tests do not prove a production wrapper",
            "same-entrypoint synthetic proof",
            "Could another agent entering fresh still choose a different directory?",
        ):
            self.assertIn(phrase, p92)
        self.assertIn("remote merged SHA is never treated as local deployment proof", p92_prompt["proofGate"])
        self.assertLess(len(self.raw["P92"]["copyContent"]), 9000)
        for synonym in (
            "canonical path",
            "canonical repository path",
            "canonical checkout",
            "development path",
            "production path",
            "local deployment path",
            "path drift",
            "scattered clones",
        ):
            self.assertEqual(build_prompt_kit.SYNONYMS[synonym], "P92")

        p01 = self.full["P01"]["copyContent"]
        self.assertIn("CANONICAL PATH CONTRACT", p01)
        self.assertIn("Every app harness must answer where normal development occurs", p01)
        self.assertIn("Do not let a fresh agent choose a new directory from model preference", p01)
        self.assertIn("GitHub merge success alone is not workstation deployment proof", p01)
        self.assertIn("P92 Canonical Path Prompt owns deep repair/audit of this contract", p01)
'''
if old_assertions not in test:
    raise SystemExit("P92 focused assertion anchor missing")
test = test.replace(old_assertions, new_assertions, 1)
TEST.write_text(test, encoding="utf-8")

print(json.dumps({
    "status": "patched",
    "strengthened": ["P01", "P92"],
    "p92_name": p92["name"],
    "p92_class": p92["class"],
    "p92_copy_chars": len(p92["copyContent"]),
    "p01_copy_chars": len(p01["copyContent"]),
}, indent=2))
