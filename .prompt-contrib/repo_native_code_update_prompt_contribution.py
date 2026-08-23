from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> str:
    completed = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    return completed.stdout


def strengthen_p07() -> None:
    path = ROOT / "docs" / "prompts.json"
    prompts = json.loads(path.read_text(encoding="utf-8"))
    p07 = next(prompt for prompt in prompts if prompt["id"] == "P07")

    marker = "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT"
    section = """REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT
- Treat repository-owned generators, derivation engines, codegen CLIs, and update workflows as first-class mutation lanes rather than invisible side effects. Resolve their canonical input, generator entrypoint, declared output surfaces, trigger, validator, and provenance before editing an output they own.
- If a path is generated or derived, repair the canonical source input/template/generator and regenerate it. Do not hand-edit generated output merely because an agent can make the diff faster. If ownership is ambiguous, inspect the nearest manifest/registry/workflow/builder once and fail closed rather than creating competing truth.
- Enforce one writer per generated mutation surface. While the repository-native generator owns a surface, human/agent lanes may inspect, test, falsify, or modify non-overlapping canonical inputs, but they must not race the generator or overwrite its output. Shared registries, manifests, lockfiles, and generated entrypoints require serialized ownership at the mutation seam.
- A generated diff is proposed repository work, not automatic completion. Inspect the exact diff, run the owning validator/tests/build, preserve normal review/protection/integration gates, and prove the accepted default branch contains both the canonical source change and its required generated result.
- Prefer the tracked canonical generator/CLI over ad-hoc workflow replay scripts. Provider automation should delegate to canonical repo-owned logic rather than becoming a second implementation of generation behavior.
- On generator/input/output conflicts, stale base state, partial writes, or concurrent movement, preserve unique work and reconcile at the canonical source boundary; never force-reset or silently let generated output erase separately owned changes.
"""
    if marker not in p07["copyContent"]:
        anchor = "AUTONOMOUS EXECUTION / USER-ONLY GATE"
        if anchor not in p07["copyContent"]:
            raise SystemExit("P07 autonomous-gate anchor missing")
        p07["copyContent"] = p07["copyContent"].replace(anchor, section + "\n" + anchor, 1)

    additions = {
        "expectedOutput": " Repository-owned generators and derived-code mechanisms are coordinated as explicit mutation lanes: agents change canonical inputs/owners, generated outputs are regenerated and independently validated, and no competing writer silently overwrites those surfaces.",
        "nextStep": " If the next owned surface is generated, resolve and execute its canonical generator from the current floor instead of hand-editing the derived output.",
        "proofGate": " Generated-surface proof additionally requires canonical source/generator ownership, one writer per generated surface, regenerated output from the accepted inputs, exact-diff validation, and default-branch containment; an ad-hoc replay or hand-edited generated file is not equivalent proof.",
    }
    for field, addition in additions.items():
        if addition.strip() not in p07[field]:
            p07[field] += addition
    for keyword in ("generated code ownership", "repo-native generator", "generated surface"):
        if keyword not in p07["keywords"]:
            p07["keywords"].append(keyword)

    path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def draft() -> dict[str, object]:
    return {
        "name": "Repository-Native Code Update Harness Builder",
        "type": "BUILD + HARNESS",
        "class": "HARNESS / REPO-NATIVE CODE GENERATION",
        "sprintRole": "Build or strengthen a repository-owned mechanism that deterministically generates bounded code updates from canonical inputs while coexisting safely with human and agent developers",
        "progress": "YES",
        "useWhen": "The repository should be able to generate or refresh owned code changes itself through a tracked generator, CLI, derivation engine, or provider workflow instead of relying exclusively on agent/human hand edits.",
        "inspectFirst": "Fresh default-branch and overlapping-work truth; existing generators/builders/registries/manifests/workflows; source-vs-generated ownership; current codegen or derivation conventions; protected/forbidden paths; validators/tests/CI; branch protection and bot permissions; prior generation failures, replay scripts, and loop/collision risks.",
        "expectedOutput": "A tracked repo-native update mechanism with canonical structured inputs, one authoritative generator entrypoint, explicit owned and forbidden output paths, deterministic/idempotent generation, provenance, collision and recursion guards, atomic/fail-closed writes, focused tests, provider or same-entrypoint execution proof, and normal Git/CI integration alongside agent developers.",
        "nextStep": "Implement the smallest real generator seam and exercise it on one representative canary input, then rerun the same inputs to prove a clean zero-diff repeat before broadening its owned surfaces or triggers.",
        "proofGate": "The real repository entrypoint generates only declared owned paths from pinned canonical inputs, rejects an out-of-scope mutation attempt, survives failure without partial destructive state, emits reviewable provenance, passes owning validators, produces the expected first-run diff and a zero-diff repeat run, cannot recursively trigger itself without a guard, and the exact accepted result is contained by the current default branch.",
        "color": "Cyan",
        "category": "standard",
        "profile": "spec-architecture",
        "copyContent": """BUILD A REPOSITORY-NATIVE CODE UPDATE MECHANISM. DO NOT TURN THIS INTO UNBOUNDED SELF-MODIFICATION OR ANOTHER AGENT PROMPT.

Repo/product: xyz_repo_or_product
Mechanism scope: xyz_generated_surface_or_capability
Canonical input(s), if known: xyz_input_registry_schema_template_or_source
Desired trigger, if known: xyz_manual_pr_push_schedule_event_or_cli
Forbidden scope: xyz_forbidden_paths_or_actions

MISSION
Add or strengthen a tracked mechanism by which the repository can deterministically generate bounded code updates from canonical inputs in addition to changes authored by human or agent developers. The repository-owned mechanism must have a smaller authority surface than a general coding agent: explicit inputs, a canonical generator entrypoint, declared output ownership, fail-closed boundaries, validation, provenance, and ordinary Git integration. Implement the mechanism and prove the real call path; do not stop at a workflow sketch.

1. RECOVER EXISTING GENERATION AUTHORITY
Refresh remote/default-branch truth first. Inspect existing builders, code generators, schemas, registries, manifests, derivation engines, workflows, hooks, generated-file banners, tests, and operator docs. Build a compact ownership map: canonical input -> generator -> generated surface -> trigger -> validator -> integration gate. Reuse a compatible owner instead of creating a second codegen system. An ad-hoc provider replay script is transport, not automatically the canonical generator.

2. DRAW THE SOURCE / GENERATED BOUNDARY
For every generated surface define:
- authoritative input(s) and schema/version;
- one canonical generator/CLI/function;
- exact owned output paths or path patterns;
- forbidden paths and data classes;
- whether outputs are committed, ephemeral, or both;
- provenance linking generator version/head and material input identity;
- validator/build/test that proves the output is acceptable.
Generated output must not become competing truth. Human and agent developers repair the canonical input/template/generator and regenerate unless repository policy explicitly names a different owner.

3. MAKE GENERATION DETERMINISTIC AND IDEMPOTENT
Same accepted inputs plus pinned generator/dependency versions must produce semantically identical output. Normalize unstable ordering, timestamps, machine-local paths, random identifiers, locale, and environment leakage unless those values are intentionally part of the contract. First execution may create a bounded diff; an immediate repeat with unchanged inputs must produce zero tracked diff. Where byte-for-byte determinism is impractical, define the narrower semantic equivalence and test it explicitly.

4. FAIL CLOSED AT THE MUTATION BOUNDARY
Validate inputs and resolve all destinations before destructive writes. Prefer staging plus atomic replacement, transaction-like commit, or rollback to last-known-good over partial multi-file mutation. Reject path traversal, symlink escape where relevant, undeclared output paths, malformed/partial inputs, missing required generator dependencies, and attempts to place secrets/private evidence into public generated surfaces. A failed run must report what did and did not change. Do not force-reset, force-push, or erase dirty/separately owned work to make generation convenient.

5. COEXIST WITH AGENT AND HUMAN DEVELOPERS
Treat the repository generator as a real mutation owner. Enforce one writer per generated surface at a time. If another branch, worktree, developer, or agent has changed the canonical input or generated output since the generation floor, refresh and reconcile before writing. On conflict, stop or rebase/reconcile at the canonical source boundary; do not let generated output silently overwrite separately owned work. Agent sprints may inspect or falsify generated surfaces in parallel, but mutation ownership of shared registries/manifests/lockfiles/generated entrypoints must be serialized.

6. CHOOSE TRIGGERS WITHOUT CREATING A RECURSIVE BOT
Expose the smallest useful real entrypoint first, usually a repo CLI/script that can also run in CI/provider automation. Then wire only justified triggers such as manual dispatch, relevant input-path changes, pull requests, schedules, or external events. Provider workflows should delegate to the same canonical generator instead of duplicating its logic. Add loop guards so a generation commit or generated-path change cannot trigger an infinite generate-commit-generate cycle. Use path filters, actor/event guards, provenance/correlation identity, concurrency control, or equivalent mechanisms appropriate to the provider.

7. KEEP GENERATED CHANGES REVIEWABLE
Repository-generated code is proposed code, not privileged truth. Produce a reviewable diff and concise generation receipt containing the canonical input identity, generator identity, owned outputs touched, validation result, and proof ceiling. Respect normal branch protection, required checks, review, and merge authority. Do not bypass protected integration merely because a bot produced the patch. If direct bot-to-main updates are already an explicit repository policy, prove the exact safeguards rather than assuming them.

8. PROTOTYPE THE REAL CALL STACK
Exercise the real entrypoint on the smallest representative canary:
canonical input -> validation -> generator -> staged output -> owned-path guard -> write -> validator/test -> Git diff/receipt.
Then exercise meaningful failures: malformed or partial input, out-of-scope destination, stale/conflicting state, and interrupted/failed generation where practical. Avoid ceremonial matrix volume; attack the failure modes most capable of corrupting or racing repository state.

9. PROVE REPEATABILITY AND INTEGRATION
Required minimum proof for a mechanism claimed working:
- first run from a clean known floor produces exactly the expected bounded diff;
- focused generator tests and owning validators pass;
- a second unchanged-input run produces zero tracked diff;
- one undeclared-output attempt is rejected before unsafe mutation;
- generated provenance/receipt identifies its inputs and generator;
- provider workflow proof, when provider automation is claimed, executes the same canonical generator rather than a substitute path;
- refresh before integration and rerun affected proof if the floor moved;
- current default branch contains the accepted canonical generator/input change and required generated output.
Separate static/schema, unit/helper, same-entrypoint synthetic, provider runtime, and user/production proof. Do not call helper-only proof live automation.

10. STOP AT A BOUNDED FIXED POINT
After the first green run, inspect the diff, repeat-run behavior, failure receipts, trigger behavior, collision policy, generated artifacts, and CI/provider evidence once more. Repair concrete in-scope gaps immediately and rerun affected proof. Stop when the declared generated surface is safely reproducible and no practical in-scope corruption, recursion, stale-state, or competing-writer gap remains. Broaden authority only through a later explicit scope change.

DELIVER
Report the ownership map; canonical generator and trigger; canonical inputs; owned/forbidden outputs; first-run and repeat-run diff results; failure/collision/loop-guard proof; validators; generated receipt/provenance; commit/PR/integration state; proof ceiling; and the exact next generator command or external blocker. The mechanism is not closed merely because a workflow file exists or a bot produced one successful commit.""",
        "keywords": [
            "repository self update",
            "self updating repository",
            "repo-native code generation",
            "repository-native generator",
            "generated code ownership",
            "codegen harness",
            "code update mechanism",
            "deterministic code generation",
            "idempotent generator",
            "generated surface",
            "generator workflow",
            "bot generated code",
            "one writer per generated surface",
            "zero diff repeat run",
            "generation provenance",
            "code generation loop guard",
        ],
    }


def add_prompt_via_helper() -> dict[str, object]:
    temp = Path(tempfile.gettempdir()) / "repo-native-code-update-prompt.json"
    temp.write_text(json.dumps(draft(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("HELPER INSPECT")
    run(sys.executable, "scripts/prompt_registry_ops.py", "inspect")
    print("HELPER ADD")
    output = run(
        sys.executable,
        "scripts/prompt_registry_ops.py",
        "add",
        "--input",
        str(temp),
        "--registry",
        "spec-architecture",
    )
    receipt = json.loads(output)
    if receipt.get("status") != "added" or not receipt.get("site_parity"):
        raise SystemExit(f"unexpected helper receipt: {receipt}")
    print("HELPER RECEIPT", json.dumps(receipt, sort_keys=True))
    return receipt


def add_focused_tests(receipt: dict[str, object]) -> None:
    prompt_id = str(receipt["id"])

    p07_test = ROOT / "tests" / "test_p02_p07_autonomous_iteration.py"
    text = p07_test.read_text(encoding="utf-8")
    if "def test_p07_coordinates_repository_generated_mutation_lanes" not in text:
        anchor = "    def test_p07_serial_fallback_is_fail_closed_and_not_user_scheduled(self) -> None:\n"
        addition = '''    def test_p07_coordinates_repository_generated_mutation_lanes(self) -> None:\n        prompt = self.effective["P07"]\n        content = prompt["copyContent"]\n        for phrase in (\n            "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT",\n            "first-class mutation lanes",\n            "repair the canonical source input/template/generator and regenerate it",\n            "one writer per generated mutation surface",\n            "A generated diff is proposed repository work, not automatic completion",\n            "Prefer the tracked canonical generator/CLI over ad-hoc workflow replay scripts",\n            "reconcile at the canonical source boundary",\n        ):\n            self.assertIn(phrase, content)\n        self.assertIn("derived-code mechanisms are coordinated as explicit mutation lanes", prompt["expectedOutput"])\n        self.assertIn("canonical generator", prompt["nextStep"])\n        self.assertIn("Generated-surface proof additionally requires", prompt["proofGate"])\n\n'''
        if anchor not in text:
            raise SystemExit("P07 focused-test anchor missing")
        p07_test.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")

    spec_test = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"
    text = spec_test.read_text(encoding="utf-8")
    if "def test_repo_native_code_update_harness_has_bounded_generator_authority" not in text:
        anchor = "    def test_new_source_prompts_are_intentionally_bounded(self) -> None:\n"
        addition = f'''    def test_repo_native_code_update_harness_has_bounded_generator_authority(self) -> None:\n        matches = [p for p in self.full.values() if p["name"] == "Repository-Native Code Update Harness Builder"]\n        self.assertEqual(len(matches), 1)\n        prompt = matches[0]\n        content = prompt["copyContent"]\n        raw = self.raw[prompt["id"]]\n        self.assertEqual(prompt["id"], "{prompt_id}")\n        self.assertEqual(prompt["profile"], "spec-architecture")\n        self.assertEqual(prompt["color"], "Cyan")\n        self.assertEqual(prompt["class"], "HARNESS / REPO-NATIVE CODE GENERATION")\n        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])\n        self.assertIn(self.policy["marker"], content)\n        for phrase in (\n            "DO NOT TURN THIS INTO UNBOUNDED SELF-MODIFICATION",\n            "DRAW THE SOURCE / GENERATED BOUNDARY",\n            "MAKE GENERATION DETERMINISTIC AND IDEMPOTENT",\n            "FAIL CLOSED AT THE MUTATION BOUNDARY",\n            "COEXIST WITH AGENT AND HUMAN DEVELOPERS",\n            "RECURSIVE BOT",\n            "one writer per generated surface",\n            "zero tracked diff",\n            "Provider workflows should delegate to the same canonical generator",\n            "out-of-scope destination",\n            "generated provenance/receipt",\n            "The mechanism is not closed merely because a workflow file exists",\n        ):\n            self.assertIn(phrase, content)\n        self.assertNotEqual(prompt["id"], "P01")\n        self.assertNotEqual(prompt["id"], "P07")\n        self.assertNotEqual(prompt["id"], "P13")\n        self.assertNotEqual(prompt["id"], "P46")\n        self.assertGreater(len(raw["copyContent"]), 3500)\n        self.assertLess(len(raw["copyContent"]), 8000)\n        self.assertIn("Repository-Native Code Update Harness Builder", build_prompt_kit_registry.render())\n\n'''
        if anchor not in text:
            raise SystemExit("spec-architecture focused-test anchor missing")
        spec_test.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")


def second_pass(prompt_id: str) -> None:
    sys.path.insert(0, str(ROOT))
    from scripts import build_prompt_kit_registry

    prompts = build_prompt_kit_registry.load_prompt_kit_registry()
    by_id = {prompt["id"]: prompt for prompt in prompts}
    new = by_id[prompt_id]
    if new["name"] != "Repository-Native Code Update Harness Builder":
        raise SystemExit("allocated identity did not resolve to expected prompt")
    if "generator" not in by_id["P01"]["copyContent"].lower() and "generators" not in by_id["P01"]["copyContent"].lower():
        raise SystemExit("P01 no longer provides adjacent generator/harness coverage")
    if "SELF-IMPROVING" not in by_id["P13"]["copyContent"]:
        raise SystemExit("P13 no longer provides repeated-pain self-improvement coverage")
    if by_id["P46"]["class"] != "GNHF / HARNESS BUILDER":
        raise SystemExit("P46 adjacency changed unexpectedly")
    if "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT" not in by_id["P07"]["copyContent"]:
        raise SystemExit("P07 coexistence strengthening missing")
    for phrase in (
        "last-known-good",
        "partial",
        "secrets/private evidence",
        "one writer per generated surface",
        "infinite generate-commit-generate cycle",
        "same canonical generator",
        "zero tracked diff",
        "default branch contains",
    ):
        if phrase not in new["copyContent"]:
            raise SystemExit(f"second-pass semantic gap: {phrase}")
    print(json.dumps({"new_id": prompt_id, "owner_map": {"P01": "ALREADY COVERED", "P07": "STRENGTHEN", "P13": "ALREADY COVERED", "P46": "ALREADY COVERED / GNHF-SPECIFIC", prompt_id: "ADD"}}, indent=2))


def main() -> int:
    strengthen_p07()
    receipt = add_prompt_via_helper()
    prompt_id = str(receipt["id"])
    add_focused_tests(receipt)
    second_pass(prompt_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
