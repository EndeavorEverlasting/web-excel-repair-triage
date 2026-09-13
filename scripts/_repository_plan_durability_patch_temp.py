from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
PROMPTS = ROOT / "docs" / "prompts.json"
ROADMAP = ROOT / "harness" / "prompt-topology" / "PHASE_B_C_ROADMAP.md"
TEST = ROOT / "tests" / "test_repository_plan_durability.py"
MARKER = "REPOSITORY PLAN DURABILITY CONTRACT"


def patch_policy() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    suffix = (
        " When repository planning produces a materially actionable plan, persist the complete plan "
        "to tracked repository/provider state before treating planning as complete or handing execution "
        "to another agent; chat text is provisional rather than canonical repository state. If an active "
        "pull request exists, the approved plan must be present there directly or by an explicit canonical "
        "tracked-plan reference."
    )
    if "chat text is provisional rather than canonical repository state" not in policy["next_step_suffix"]:
        policy["next_step_suffix"] = policy["next_step_suffix"].rstrip() + suffix

    section = """REPOSITORY PLAN DURABILITY CONTRACT
- When work concerns a repository and planning produces a materially actionable roadmap, sprint map, architecture plan, migration plan, phase plan, implementation sequence, or other execution dependency, the complete accepted plan MUST live in durable repository/provider state; chat alone is not a canonical planning surface.
- Chat may carry a provisional sketch, critique, or short orientation note. Before the plan becomes an execution dependency, is called approved/ready, or is handed to another agent, persist the complete plan in the existing canonical tracked plan/spec/handoff path or in the active pull request. Reuse an existing plan owner/path before creating another plan file.
- If an active pull request exists, approval must be reflected in that PR immediately: include the complete plan there or identify the exact committed canonical plan path plus its status/commit. Do not leave the approved version only in chat.
- A plan approved in chat triggers synchronization, not closure: update the tracked plan or PR in the same execution thread before implementation/handoff continues.
- Multi-phase repository work must persist the whole phase map, not only the current phase: completed floor, successor phases, dependencies, owned and forbidden scope, expected artifacts, validation/proof gates, proof ceiling, and explicit deferred work. Future phases may remain unimplemented, but they may not exist only as conversational leftovers when they are already actionable.
- If a materially actionable repository plan changes, update the durable plan/PR before handing off or claiming the planning state current. Agents entering later must be able to recover the plan from refreshed repository/provider truth without needing the originating chat.
- Closeout is invalid when an actionable repository plan, approved plan revision, or successor-phase map exists only in chat. Persist it first, then report the canonical path/PR and exact revision.
"""
    appendix = policy["copy_content_appendix"]
    if MARKER not in appendix:
        needle = "\n\nREMOTE FRESHNESS / BRANCH FLOOR CONTRACT"
        if needle not in appendix:
            raise SystemExit("Remote freshness marker not found in shared appendix")
        policy["copy_content_appendix"] = appendix.replace(
            needle, "\n\n" + section.rstrip() + needle, 1
        )
    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_planning_owners() -> None:
    prompts = json.loads(PROMPTS.read_text(encoding="utf-8"))
    by_id = {prompt["id"]: prompt for prompt in prompts}
    for prompt_id in ("P02", "P04"):
        if prompt_id not in by_id:
            raise SystemExit(f"Missing canonical planning owner: {prompt_id}")

    p02 = by_id["P02"]
    p02["expectedOutput"] = (
        "A context-grounded launch order and executable build panels that have been privately prototyped, "
        "checked against recovered requirements and repo evidence, revised to a bounded fixed point, and—when "
        "they concern actionable repository work—persisted in the repository's canonical tracked plan/handoff "
        "surface or active PR before another agent depends on them. Chat presentation is an orientation/copy "
        "surface, not the sole durable owner."
    )
    p02["nextStep"] = (
        "Privately prototype and validate the launch pack; for actionable repository work, synchronize the "
        "complete accepted launch map into the existing canonical tracked plan/handoff path or active PR, then "
        "present the concise chat-facing copy panels and launch the first executable panel from that durable state."
    )
    p02["proofGate"] = (
        "Prior context is recovered as far as available; at least one deliberate prototype -> critique -> revise "
        "pass occurs; every identified gap has an executable owner or evidence no build is needed; and any "
        "materially actionable repository launch map is recoverable in full from tracked repository/provider "
        "state (and reflected in the active PR when one exists) before handoff or completion."
    )
    p02_marker = "DURABLE REPOSITORY PLAN HANDOFF"
    if p02_marker not in p02["copyContent"]:
        p02["copyContent"] = p02["copyContent"].rstrip() + """

DURABLE REPOSITORY PLAN HANDOFF
- A chat launch pack is provisional presentation, not canonical repository state. When the recovered work belongs to a repository and the resulting map is materially actionable, persist the complete accepted launch order, dependencies, lanes, proof gates, and deferred phases in the existing canonical tracked plan/handoff surface or active PR before another agent depends on it.
- If an active PR exists, synchronize approval there immediately: include the complete plan or the exact committed canonical plan path and revision. A plan approved in chat triggers repository/PR synchronization in the same execution thread.
- Do not close a repository-planning conversation with a plan that later agents can recover only by finding this chat.
"""

    p04 = by_id["P04"]
    p04["expectedOutput"] = (
        "Launch order first, ordered copy-panel sprint candidates, and harness/skill/capability/trigger/app-logic "
        "factoring ledgers, with the complete actionable repository plan persisted to the existing canonical "
        "tracked plan/spec/handoff owner or active PR rather than existing only in chat."
    )
    p04["nextStep"] = (
        "Persist the complete accepted factoring plan to the canonical repository plan/handoff path or active PR; "
        "then use P05 or P07 from that durable revision."
    )
    p04["proofGate"] = (
        "Dependencies, collision ownership, exact panel sequence, successor phases, and proof gates are explicit; "
        "for actionable repository work the complete plan is tracked and recoverable from repository/provider "
        "truth, and any active PR points to or contains the approved revision."
    )
    p04_marker = "DURABLE PLAN OUTPUT"
    if p04_marker not in p04["copyContent"]:
        p04["copyContent"] = p04["copyContent"].rstrip() + """

DURABLE PLAN OUTPUT
- Do not make chat the sole owner of an actionable repository plan. The chat response may be a concise orientation or copy surface, but the complete accepted sprint map must be committed to the existing canonical repository plan/spec/handoff path, or carried directly in the active PR when that is the repository's planning owner.
- Reuse the existing plan owner before inventing a second plan file. Persist the whole dependency map, not only the first lane: completed floor, ordered successor phases, parallel groups, collision ownership, owned/forbidden scope, expected artifacts, validation/proof gates, proof ceiling, and deferred work.
- If the operator approves or materially changes the plan in chat, synchronize that revision to the tracked plan/PR before handing execution to P05/P07 or another agent.
"""

    PROMPTS.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_roadmap() -> None:
    ROADMAP.write_text(
        """# Prompt Topology Successor Roadmap — Phase B / Phase C

**Status:** durable successor plan; Phase A is complete and is not reopened by this document.  
**Plan owner:** `harness/prompt-topology/PHASE_B_C_ROADMAP.md`  
**Semantic authority:** the current Prompt Kit registry plus `harness/prompt-topology/schema.v1.json`, `config.v1.json`, `phase-a-refinements.v1.json`, and the executable Phase A pipeline.  
**Historical Phase A integration:** `b627ce43254b603d8b197ca704aaebfc3730572e`.

## Why this file exists

The original topology design already specified visualization-only UMAP projection and downstream shapes, while `EXECUTABLE_PHASE_A.md` deliberately stopped before projection/viewer work. Phase A later became executable without creating one current successor plan. This file closes that durability gap: future agents should recover the successor roadmap from the repository, not from the chat that discussed it.

## Proven floor — Phase A COMPLETE

Phase A owns semantic truth:

`registry -> deterministic feature/embedding seam -> multi-channel graph -> deterministic PCA -> HDBSCAN/outliers -> persistent cluster reconciliation -> advisory opportunities -> artifacts/prompt-topology/topology.v1.json`

Phase A invariants remain binding throughout later phases:

- prompt IDs remain canonical node identity;
- semantic topology is derived evidence and never silently rewrites registry truth;
- projection/viewer output cannot influence clustering, classification, opportunities, or registry mutation;
- generated topology is reproducible from current canonical inputs;
- later visualization work consumes Phase A output rather than replacing it.

## Phase B — Deterministic 3D projection + spatial stability

### Dependency
A freshly rebuilt and validated Phase A topology for the current registry floor.

### Owned scope
- a renderer-neutral 3D projection artifact derived from Phase A node vectors/topology;
- deterministic projection implementation using the existing `config.v1.json` UMAP contract (`n_components=3`, cosine metric, fixed seed 42 unless the canonical config is explicitly revised);
- projection provenance and validator coverage;
- spatial-stability reconciliation against a previous accepted projection when one exists;
- visualization-only cluster envelopes, beginning with the existing bounding-sphere contract;
- focused CI evidence for determinism and semantic non-interference.

### Spatial-stability rule
Fixed randomness is necessary but not sufficient once the corpus changes. Phase B must align a new projection to the previous accepted projection using unchanged prompt IDs as anchors before publishing coordinates. The implementation may use a deterministic rigid/orthogonal Procrustes-style alignment or an equivalently bounded canonical method, but the chosen method must be encoded in config/schema and proven by fixtures. If the anchor set is insufficient, publish an explicit lineage/reset state rather than pretending coordinates are spatially continuous.

### Required artifacts
- `artifacts/prompt-topology/projection-3d.json` (or an explicitly versioned successor chosen by schema migration);
- projection provenance: algorithm, dimensions, parameters, random seed, Phase A content hash/input identity, prior projection identity when aligned, stability method/result;
- cluster envelope metadata downstream of coordinates;
- validation receipt proving node parity, determinism, and semantic non-interference.

### Acceptance gates
- identical Phase A inputs + identical projection config produce byte-identical canonical projection output;
- shuffled input order does not alter canonical output;
- every projected prompt references exactly one Phase A node and no unknown node appears;
- deleting/regenerating projection cannot change Phase A semantic topology/content hash;
- unchanged anchor nodes preserve orientation/continuity within an explicit tested tolerance after alignment;
- insufficient continuity evidence fails closed to a declared reset/lineage state;
- projection remains visualization-only.

### Forbidden in Phase B
Interactive viewer implementation, live usage/session telemetry, `CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, `COMPLEMENT`, vector database introduction, prompt renumbering, or registry mutation driven by coordinates.

## Phase C — Read-only interactive topology viewer

### Dependency
Accepted Phase B projection plus current validated Phase A semantic topology.

### Owned scope
- an interactive 3D explorer that consumes canonical Phase A + Phase B artifacts without recomputing semantic truth;
- node selection/search and readable prompt identity/title/family/cluster/outlier/opportunity context;
- family/cluster visibility controls and relationship-edge inspection;
- navigation that preserves stable prompt IDs and existing canonical Prompt Kit sequence semantics;
- graceful failure when projection or semantic artifacts are stale/mismatched;
- accessibility/performance checks appropriate to the chosen renderer.

### Viewer invariants
- renderer state is presentation state only;
- moving/hiding/filtering nodes cannot mutate registry, cluster identity, or topology artifacts;
- the viewer must bind displayed data to exact artifact/provenance identities and reject mismatched Phase A/Phase B generations;
- topology recommendation order may aid discovery but never silently replaces canonical sequence ordering.

### Acceptance gates
- viewer loads the exact canonical artifacts and exposes their identities/provenance;
- representative nodes, outliers, clusters, multi-channel edges, and opportunities can be inspected;
- stale/mismatched artifacts fail visibly rather than being combined;
- no viewer action changes semantic artifact hashes or canonical registry state;
- observed browser proof covers navigation, selection, filtering, and artifact-mismatch behavior.

### Forbidden in Phase C
Telemetry-driven topology mutation, automatic prompt rewriting, vector DB migration, prompt renumbering, or treating visual proximity as classification truth.

## Later / explicitly deferred lanes

### Behavioral telemetry channels
`CO_USAGE`, `TRANSITION`, `SUBSTITUTION`, and `COMPLEMENT` remain a later evidence layer. They require a separate privacy/provenance/session-identity contract and must join the graph as typed evidence without rewriting semantic channels by default.

### Vector database
Deferred. Current corpus scale does not justify it. Reconsider only when measured corpus/query/runtime evidence shows brute-force/local storage is the limiting factor.

### Prompt identity / ontology rewrites
Prompt renumbering remains forbidden. Family/ontology changes require their own explicit P07/P79-owned registry mutation and proof; neither projection nor viewer behavior authorizes them.

## Execution order

1. Refresh current default branch and rebuild/validate Phase A on the current registry.
2. Declare a new bounded **Prompt Topology Phase B** sprint from this file; implement and integrate projection + spatial-stability proof.
3. Refresh main and verify Phase B containment/provenance.
4. Declare a new bounded **Prompt Topology Phase C** sprint; implement and integrate the read-only viewer.
5. Only after Phase C proof, evaluate whether behavioral telemetry has enough evidence and privacy/provenance design to justify a separate successor sprint.

This roadmap is the durable execution dependency. Chat may summarize it, but future agents should sprint from this file and refreshed repository/provider truth.
""",
        encoding="utf-8",
    )


def write_test() -> None:
    TEST.write_text(
        '''from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry

POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
ROADMAP = ROOT / "harness" / "prompt-topology" / "PHASE_B_C_ROADMAP.md"
MARKER = "REPOSITORY PLAN DURABILITY CONTRACT"


class RepositoryPlanDurabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        raw = json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        cls.raw = {p["id"]: p for p in raw}
        cls.prompts = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}
        cls.roadmap = ROADMAP.read_text(encoding="utf-8")

    def test_shared_policy_makes_chat_only_repo_plans_noncanonical(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        self.assertIn(MARKER, appendix)
        for phrase in (
            "chat alone is not a canonical planning surface",
            "persist the complete plan",
            "active pull request",
            "plan approved in chat triggers synchronization",
            "Multi-phase repository work must persist the whole phase map",
            "Closeout is invalid",
        ):
            self.assertIn(phrase, appendix)

    def test_next_step_contract_requires_durable_plan_before_handoff(self) -> None:
        suffix = self.policy["next_step_suffix"]
        self.assertIn("chat text is provisional rather than canonical repository state", suffix)
        self.assertIn("active pull request", suffix)

    def test_p02_and_p04_raw_owners_no_longer_treat_chat_as_durable_owner(self) -> None:
        self.assertIn("DURABLE REPOSITORY PLAN HANDOFF", self.raw["P02"]["copyContent"])
        self.assertIn("DURABLE PLAN OUTPUT", self.raw["P04"]["copyContent"])
        self.assertIn("canonical tracked plan", self.raw["P02"]["expectedOutput"])
        self.assertIn("canonical", self.raw["P04"]["expectedOutput"])
        self.assertIn("active PR", self.raw["P04"]["proofGate"])

    def test_representative_planning_and_execution_prompts_receive_contract(self) -> None:
        for prompt_id in ("P02", "P04", "P07", "P95", "P141"):
            self.assertIn(prompt_id, self.prompts)
            self.assertIn(MARKER, self.prompts[prompt_id]["copyContent"])
            self.assertIn("chat alone is not a canonical planning surface", self.prompts[prompt_id]["copyContent"])

    def test_topology_successor_plan_is_durable_and_complete_enough_to_sprint(self) -> None:
        self.assertTrue(ROADMAP.is_file())
        for phrase in (
            "Phase A COMPLETE",
            "Phase B — Deterministic 3D projection + spatial stability",
            "Phase C — Read-only interactive topology viewer",
            "Behavioral telemetry channels",
            "Vector database",
            "Prompt identity / ontology rewrites",
            "Execution order",
            "Acceptance gates",
        ):
            self.assertIn(phrase, self.roadmap)

    def test_roadmap_preserves_semantic_visualization_boundary(self) -> None:
        for phrase in (
            "projection/viewer output cannot influence clustering",
            "projection remains visualization-only",
            "visual proximity as classification truth",
        ):
            self.assertIn(phrase, self.roadmap)


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    patch_policy()
    patch_planning_owners()
    write_roadmap()
    write_test()
