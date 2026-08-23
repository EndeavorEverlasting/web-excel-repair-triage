from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "spec-architecture-prompts"


def run(*args: str) -> str:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    if proc.returncode:
        raise SystemExit(proc.returncode)
    return proc.stdout


def combined_prompts() -> list[dict]:
    sys.path.insert(0, str(ROOT))
    from scripts import build_prompt_kit_registry
    return build_prompt_kit_registry.load_prompt_kit_registry()


def strengthen_owners() -> None:
    path = ROOT / "docs" / "prompts.json"
    prompts = json.loads(path.read_text(encoding="utf-8"))
    by_id = {prompt["id"]: prompt for prompt in prompts}

    p07 = by_id["P07"]
    p07_marker = "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT"
    p07_section = """REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT
- Treat repository-owned generators, derivation engines, codegen CLIs, and update workflows as first-class mutation lanes rather than invisible side effects. Resolve their canonical input, generator entrypoint, declared output surfaces, trigger, validator, and provenance before editing an output they own.
- If a path is generated or derived, repair the canonical source input/template/generator and regenerate it. Do not hand-edit generated output merely because an agent can make the diff faster. If ownership is ambiguous, inspect the nearest manifest/registry/workflow/builder once and fail closed rather than creating competing truth.
- Enforce one writer per generated mutation surface. While the repository-native generator owns a surface, human/agent lanes may inspect, test, falsify, or modify non-overlapping canonical inputs, but they must not race the generator or overwrite its output. Shared registries, manifests, lockfiles, and generated entrypoints require serialized ownership at the mutation seam.
- A generated diff is proposed repository work, not automatic completion. Inspect the exact diff, run the owning validator/tests/build, preserve normal review/protection/integration gates, and prove the accepted default branch contains both the canonical source change and its required generated result.
- Prefer the tracked canonical generator/CLI over ad-hoc workflow replay scripts. Provider automation should delegate to canonical repo-owned logic rather than becoming a second implementation of generation behavior.
- On generator/input/output conflicts, stale base state, partial writes, or concurrent movement, preserve unique work and reconcile at the canonical source boundary; never force-reset or silently let generated output erase separately owned changes.
"""
    if p07_marker not in p07["copyContent"]:
        anchor = "AUTONOMOUS EXECUTION / USER-ONLY GATE"
        if anchor not in p07["copyContent"]:
            raise SystemExit("P07 autonomous-gate anchor missing")
        p07["copyContent"] = p07["copyContent"].replace(anchor, p07_section + "\n" + anchor, 1)
    for keyword in ("generated code ownership", "repo-native generator", "generated surface"):
        if keyword not in p07["keywords"]:
            p07["keywords"].append(keyword)
    p07_additions = {
        "expectedOutput": " Repository-owned generators and derived-code mechanisms are coordinated as explicit mutation lanes: agents change canonical inputs/owners, generated outputs are regenerated and independently validated, and no competing writer silently overwrites those surfaces.",
        "nextStep": " If the next owned surface is generated, resolve and execute its canonical generator from the current floor instead of hand-editing the derived output.",
        "proofGate": " Generated-surface proof additionally requires canonical source/generator ownership, one writer per generated surface, regenerated output from the accepted inputs, exact-diff validation, and default-branch containment; an ad-hoc replay or hand-edited generated file is not equivalent proof.",
    }
    for field, addition in p07_additions.items():
        if addition.strip() not in p07[field]:
            p07[field] += addition

    p11 = by_id["P11"]
    p11_marker = "CI/CD COMPOSITION CONTRACT"
    p11_section = """CI/CD COMPOSITION CONTRACT
- Expose this harness validator through one canonical repository command that runs the same validation logic locally and in CI. A GitHub Actions job may invoke that command; the workflow must not reimplement the validator in YAML.
- Treat the machine-readable PASS/SKIP/FAIL result as one CI gate with the exact repository head/commit it observed. If that head or a required harness dependency moves, rerun it; do not carry the earlier receipt forward as proof for a different revision.
- Preserve this prompt's offline/synthetic boundary. Application or product end-to-end tests, browser/service/device workflows, deployment checks, and provider-runtime proof remain distinct gates that a CI/CD promotion pipeline may compose after this harness gate. Do not silently absorb them into P11 or call synthetic harness proof live E2E behavior.
- A required validator reported SKIP is not a successful CI gate. The calling pipeline must distinguish required, optional, environment-blocked, and inapplicable checks and fail closed when a required proof cannot run.
- Emit enough structured evidence for a promotion pipeline to correlate the harness receipt with head SHA, validator set, required/skipped checks, and final status without parsing optimistic prose.
"""
    if p11_marker not in p11["copyContent"]:
        p11["copyContent"] += "\n" + p11_section
    for keyword in ("CI/CD harness gate", "harness E2E validation", "machine-readable CI gate"):
        if keyword not in p11["keywords"]:
            p11["keywords"].append(keyword)
    for field, addition in {
        "expectedOutput": " The validator is also composable as a canonical CI gate without expanding its offline/synthetic proof boundary.",
        "proofGate": " CI use additionally pins the receipt to the exact head SHA and treats required SKIP as non-passing; application E2E and provider-runtime proof remain separate gates.",
    }.items():
        if addition.strip() not in p11[field]:
            p11[field] += addition

    p15 = by_id["P15"]
    p15_marker = "CANONICAL PROMOTION PIPELINE CONTRACT"
    p15_section = """CANONICAL PROMOTION PIPELINE CONTRACT
- When the repository has a canonical GitHub Actions/CI/CD promotion workflow, use that workflow as the normal integration path rather than manually pushing, merging, tagging, or deploying around it. P15 remains the integration executor; it does not duplicate the pipeline implementation.
- Pin the candidate head SHA and required base/dependency floor before promotion. Required CI, harness validation, application E2E tests, artifact provenance, approvals, environments, and branch-protection/merge-queue gates must apply to that exact candidate. If the head/base moves, invalidate affected proof and rerun before promotion.
- Never convert `workflow succeeded` into a broader claim than its jobs prove. A pipeline that ran static checks but skipped required harness or E2E gates is not promotion-ready.
- Automated push/merge/release is permitted only when repository policy explicitly authorizes that destination and the exact required gates are green. Do not bypass review/protection with an automation token merely because the token can write.
- After automated promotion, refresh the default branch and verify containment of the proven integration SHA plus the expected artifact/release identity; a later default head is acceptable when ancestry and affected proof remain valid.
"""
    if p15_marker not in p15["copyContent"]:
        anchor = "VALIDATION\n"
        if anchor not in p15["copyContent"]:
            raise SystemExit("P15 validation anchor missing")
        p15["copyContent"] = p15["copyContent"].replace(anchor, p15_section + "\n" + anchor, 1)
    for keyword in ("canonical promotion pipeline", "CI/CD promotion", "GitHub Actions integration gate"):
        if keyword not in p15["keywords"]:
            p15["keywords"].append(keyword)
    for field, addition in {
        "expectedOutput": " When a canonical promotion pipeline exists, integration proceeds through its exact-head gates and reports the resulting provider receipt and containment proof.",
        "proofGate": " A provider workflow is sufficient only for the exact candidate it validated and only when all required harness/E2E/protection gates actually ran and passed.",
    }.items():
        if addition.strip() not in p15[field]:
            p15[field] += addition

    path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def generation_draft() -> dict:
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
        "color": "Cyan", "category": "standard", "profile": "spec-architecture",
        "copyContent": """BUILD A REPOSITORY-NATIVE CODE UPDATE MECHANISM. DO NOT TURN THIS INTO UNBOUNDED SELF-MODIFICATION OR ANOTHER AGENT PROMPT.

Repo/product: xyz_repo_or_product
Mechanism scope: xyz_generated_surface_or_capability
Canonical input(s), if known: xyz_input_registry_schema_template_or_source
Desired trigger, if known: xyz_manual_pr_push_schedule_event_or_cli
Forbidden scope: xyz_forbidden_paths_or_actions

MISSION
Add or strengthen a tracked mechanism by which the repository can deterministically generate bounded code updates from canonical inputs in addition to changes authored by human or agent developers. The repository-owned mechanism must have a smaller authority surface than a general coding agent: explicit inputs, a canonical generator entrypoint, declared output ownership, fail-closed boundaries, validation, provenance, and ordinary Git integration. Implement the mechanism and prove the real call path; do not stop at a workflow sketch.

1. RECOVER EXISTING GENERATION AUTHORITY
Refresh remote/default-branch truth first. Inspect existing builders, generators, schemas, registries, manifests, workflows, hooks, generated-file banners, tests, and operator docs. Build canonical input -> generator -> generated surface -> trigger -> validator -> integration gate. Reuse a compatible owner instead of creating a second codegen system. An ad-hoc provider replay script is transport, not automatically the canonical generator.

2. DRAW THE SOURCE / GENERATED BOUNDARY
Define authoritative inputs/schema/version, one canonical generator, exact owned output paths, forbidden paths/data classes, committed-vs-ephemeral status, provenance, and the validator/build/test for every generated surface. Generated output must not become competing truth. Humans and agents repair canonical input/template/generator and regenerate unless policy explicitly names another owner.

3. MAKE GENERATION DETERMINISTIC AND IDEMPOTENT
Same accepted inputs plus pinned generator/dependency versions must produce semantically identical output. Normalize unstable ordering, timestamps, machine-local paths, random identifiers, locale, and environment leakage unless intentional. First execution may create a bounded diff; an immediate unchanged-input repeat must produce zero tracked diff.

4. FAIL CLOSED AT THE MUTATION BOUNDARY
Validate inputs and destinations before destructive writes. Prefer staging plus atomic replacement, transaction-like commit, or rollback to last-known-good over partial mutation. Reject path traversal, symlink escape where relevant, undeclared outputs, malformed/partial inputs, missing dependencies, and secrets/private evidence entering public generated surfaces. Report what changed on failure. Never force-reset/push or erase separately owned work for convenience.

5. COEXIST WITH AGENT AND HUMAN DEVELOPERS
Enforce one writer per generated surface. Refresh/reconcile if another lane changed canonical input or generated output since the generation floor. On conflict, reconcile at the canonical source boundary; never let generated output silently overwrite separately owned work.

6. CHOOSE TRIGGERS WITHOUT CREATING A RECURSIVE BOT
Expose the smallest real repo CLI/script first; provider workflows delegate to it instead of duplicating logic. Add only justified triggers and loop guards so generated commits cannot cause an infinite generate-commit-generate cycle.

7. KEEP GENERATED CHANGES REVIEWABLE
Generated code is proposed code, not privileged truth. Produce a reviewable diff and generation receipt with input identity, generator identity, outputs, validation result, and proof ceiling. Respect branch protection/review/integration gates.

8. PROTOTYPE THE REAL CALL STACK
Exercise canonical input -> validation -> generator -> staged output -> owned-path guard -> write -> validator/test -> Git diff/receipt. Exercise malformed input, out-of-scope destination, stale/conflicting state, and failed/interrupted generation where practical.

9. PROVE REPEATABILITY AND INTEGRATION
Prove expected first-run diff, focused tests/validators, zero-diff repeat, rejection of undeclared output, provenance, same-entrypoint provider execution when claimed, and default-branch containment. Separate static/schema, unit/helper, same-entrypoint synthetic, provider runtime, and user/production proof.

10. STOP AT A BOUNDED FIXED POINT
Inspect diff, repeat behavior, failure receipts, trigger behavior, collision policy, artifacts, and CI evidence again. Repair concrete gaps. Stop when the declared surface is reproducible and no practical corruption, recursion, stale-state, or competing-writer gap remains.

DELIVER
Report ownership map; generator/trigger; inputs; owned/forbidden outputs; first/repeat diff; failure/collision/loop proof; validators; receipt/provenance; commit/integration; proof ceiling; exact next generator command or blocker. A workflow file or one bot commit alone is not completion.""",
        "keywords": ["repository self update", "repo-native code generation", "repository-native generator", "generated code ownership", "codegen harness", "deterministic code generation", "idempotent generator", "generated surface", "bot generated code", "one writer per generated surface", "zero diff repeat run", "generation provenance", "code generation loop guard"],
    }


def promotion_draft() -> dict:
    return {
        "name": "Validated CI/CD Promotion Pipeline Builder",
        "type": "BUILD + HARNESS",
        "class": "HARNESS / CI-CD PROMOTION",
        "sprintRole": "Design and implement a repository-owned GitHub Actions/CI/CD promotion mechanism that validates the exact candidate head through canonical harness and end-to-end test gates before automated push, merge, release, or deployment",
        "progress": "YES",
        "useWhen": "A repository should automatically validate code authored by humans, agents, or repo-native generators and then safely push, merge, release, or deploy that exact code through GitHub Actions/CI/CD rather than relying on manual promotion steps.",
        "inspectFirst": "Fresh default-branch/PR/workflow truth; current GitHub Actions and CI/CD files; branch protection, merge queue, environment/review rules and token permissions; canonical test/build/harness commands including P11-style harness validation; application E2E suites; artifact/package provenance; deployment/release paths; existing bot writers, concurrency groups, caches, retries, and prior pipeline failures.",
        "expectedOutput": "A tracked promotion architecture and implemented pipeline that delegates to repo-owned validation commands, pins proof to one exact candidate SHA, runs required harness validation and application E2E gates distinctly, preserves artifact provenance, fails closed on stale/moved/skipped/failed proof, serializes write authority, uses least privilege and loop guards, and performs only repository-authorized push/merge/release/deploy actions with provider-runtime evidence.",
        "nextStep": "Implement the smallest canary promotion path for one non-production candidate, trigger the real GitHub Actions workflow, prove one successful exact-head promotion and representative blocking failures, then broaden destinations only after those gates are stable.",
        "proofGate": "The actual provider workflow validates one pinned candidate SHA through required static/unit/integration gates, the canonical harness validator, and applicable application E2E tests; required SKIP/FAIL/stale-head/moved-base/unauthorized-destination cases block promotion; artifacts are traceable to that SHA; concurrent/recursive writers are guarded; least-privilege permissions are explicit; and post-promotion default-branch/release/deployment evidence contains the proven candidate without bypassing repository protection.",
        "color": "Cyan", "category": "standard", "profile": "spec-architecture",
        "copyContent": """DESIGN AND IMPLEMENT A VALIDATED REPOSITORY PROMOTION PIPELINE. USE GITHUB ACTIONS / CI-CD TO PUSH OR PROMOTE CODE ONLY AFTER THE EXACT CANDIDATE PASSES ITS REQUIRED HARNESS AND END-TO-END GATES. DO NOT CONFUSE PIPELINE AUTOMATION WITH CODE GENERATION OR BYPASS REPOSITORY PROTECTION.

Repo/product: xyz_repo_or_product
Promotion destination(s): xyz_branch_merge_release_deploy_targets
Existing CI/harness entrypoints, if known: xyz_commands_or_workflows
Required E2E surface, if known: xyz_cli_browser_service_device_or_other
Forbidden scope: xyz_forbidden_destinations_or_actions

MISSION
Build or strengthen the repository-owned mechanism that takes code already authored by humans, agent developers, or bounded repo-native generators and safely advances that exact revision through GitHub Actions/CI/CD validation to an authorized push, merge, release, or deployment. The pipeline is an evidence-and-promotion system, not another source-code author. It must compose canonical repo commands rather than duplicate them in YAML, distinguish harness end-to-end validation from application end-to-end testing, pin proof to an exact candidate identity, fail closed when proof is stale or incomplete, and produce provider-runtime evidence for the real promotion path.

1. RECOVER CURRENT PROMOTION AUTHORITY
Refresh all remote refs/tags and resolve the actual default branch. Inspect open/recent overlapping PRs/workflows, GitHub Actions, scripts/task runners, branch protection, merge queue, environments, required reviewers/checks, release/deploy machinery, bot identities, tokens/permissions, caches, artifacts, and current harness/test owners. Build event -> candidate SHA/base -> validation jobs -> artifacts -> approval/protection gates -> mutation/promotion action -> post-promotion proof. Reuse a compatible pipeline; do not create a second integration authority merely because another YAML file is easy.

2. SEPARATE AUTHORING, VALIDATION, AND PROMOTION
Code generation/authoring ends before promotion begins. A repo-native generator may propose a diff and humans/agents may author code, but this pipeline owns only validation and authorized advancement of the candidate. Preserve generated-surface ownership and one-writer rules. Never let CI rewrite source opportunistically unless a separately owned canonical generator explicitly requires that step.

3. BUILD THE VALIDATION DAG FROM CANONICAL COMMANDS
Define the cheapest-to-strongest graph appropriate to the repo: structural/schema/format -> lint/type/static -> unit -> integration -> build/package -> canonical harness E2E validator -> application/product E2E -> release/deploy-specific checks -> promotion. Do not require categories the product does not have, but every required existing gate needs one owner, command, inputs, outputs, and blocking semantics. GitHub Actions invokes repo-owned commands; YAML orchestrates and does not become a second test implementation.

4. KEEP HARNESS E2E AND APPLICATION E2E DISTINCT
Harness end-to-end validation verifies repository contracts, validators, registries, fixtures, workflows, and proof machinery together. Application end-to-end testing validates user/system behavior through the real product entrypoint: CLI, browser, API/service, packaged binary, device/runtime, or another owned interface. Synthetic/offline harness PASS cannot substitute for live/application E2E, and an application smoke test cannot substitute for harness integrity. Compose both when required and report each proof level separately.

5. PIN EVERY GATE TO ONE CANDIDATE IDENTITY
Capture candidate head SHA, required base/merge-base, dependency/lock identities, and artifact identity before promotion. Every required job/receipt must be attributable to that candidate. If head, base, owning validator, required workflow, generated input, or artifact moves materially after proof, invalidate and rerun affected gates. Never promote whatever is currently on the branch after validating an earlier SHA. For merge queues/synthetic merge refs, record source head plus tested merge candidate.

6. DESIGN GITHUB ACTIONS TRIGGERS AND DEPENDENCIES EXPLICITLY
Use only justified events: pull_request for candidate validation, merge_group when merge queue is used, push for post-integration/release work, workflow_dispatch for bounded operator initiation, schedule/external events only when needed. Encode job dependencies so promotion cannot start before all required gates succeed. Path filters are optimization, not permission to skip a gate whose inputs changed indirectly. Prefer reusable workflows/actions when they remove duplicated orchestration without creating a second implementation.

7. FAIL CLOSED ON SKIP, STALE PROOF, AND PARTIAL SUCCESS
Classify gates REQUIRED / OPTIONAL / INAPPLICABLE / ENVIRONMENT-BLOCKED. REQUIRED plus SKIP is not green. Cancelled, timed-out, neutral, stale, or missing required results cannot satisfy promotion. `continue-on-error` is forbidden for promotion-critical gates unless downstream explicitly consumes and rejects the failure. Bounded retries may address identified transient infrastructure failures; deterministic test failures do not become green by repetition.

8. CONTROL WRITE AUTHORITY, CONCURRENCY, AND RECURSION
Use least-privilege GitHub token/action permissions and environment-scoped credentials. Separate read/validate jobs from write/promote jobs. Serialize mutation with concurrency or merge queue so two successful runs cannot race a branch/tag/deployment. Add actor/event/path/provenance guards so a bot promotion commit cannot recursively trigger another writer forever. Reject unauthorized destinations even if the token can technically write. Never echo secrets into logs/artifacts.

9. MAKE ARTIFACTS AND CACHES PART OF THE PROOF CHAIN
Prefer build-once/promote-the-same-artifact for deployable artifacts. Record source SHA, dependency/lock identity, build/run identity, checksums or equivalent immutable artifact identity, and destination. Cache hits may speed work but may not masquerade as fresh validation; keys/restoration rules must prevent stale artifacts or test outputs from satisfying a new candidate. Validate reused artifacts where trust boundaries require it.

10. DESIGN TEST ENVIRONMENT LIFECYCLE
For application E2E, define fixture/test-data creation, service/container/browser/runtime startup, readiness checks, isolated namespaces/accounts where applicable, bounded waits/retries, teardown, and cleanup. E2E tests must be repeatable and must not corrupt production/user state. When production-like infrastructure is unavailable, preserve the exact proof ceiling rather than silently downgrading the gate.

11. PROTOTYPE SUCCESS AND BLOCKING PATHS
Exercise the real provider workflow on the smallest safe canary candidate. Prove: green exact-head path reaches the authorized promotion action; harness-validator failure blocks it; application-E2E failure blocks it when required; required SKIP blocks; stale/moved candidate blocks; unauthorized target blocks; concurrent writer/merge-queue behavior is safe; recursion guard prevents a bot loop. Prefer targeted fault injection/fixtures over damaging real branches/environments.

12. OBSERVE AND AUDIT THE PIPELINE
Emit a concise workflow summary plus machine-readable promotion receipt containing provider run ID, event/actor, candidate SHA/base identity, required jobs/conclusions, harness receipt identity, E2E receipt/artifacts, promoted artifact identity, target, mutation result, final integration/deployment SHA, and proof ceiling. Logs must make the first failing gate obvious without manual DAG reconstruction.

13. PROVE POST-PROMOTION CONTAINMENT
After push/merge/release/deploy, refresh provider truth. For default-branch integration, verify the proven integration SHA is an ancestor of refreshed default head; do not fail because later valid commits landed. For release/deploy, verify the published/deployed artifact resolves to the proven candidate/artifact identity and required health/smoke checks pass. A queued or accepted command is not successful deployment.

14. STOP AT A BOUNDED FIXED POINT
Inspect successful and negative-path runs, permissions, concurrency, trigger filters, artifact lineage, receipts, and post-promotion state once more. Repair concrete holes and rerun affected proof. Stop when one representative promotion path is reproducible, required failures reliably block it, and no practical bypass/stale-proof/race/recursive-writer gap remains. Expand destinations only through explicit scope.

DELIVER
Report promotion graph; canonical commands/workflows; exact-head identity model; harness-vs-application-E2E gates; trigger/dependency design; permissions/concurrency/loop guards; artifact provenance; success and blocking-run evidence; provider run/receipt; post-promotion containment; commit/PR/mainline state; proof ceiling; exact next canary command or authorization blocker. A green YAML syntax check, local-only test run, open PR, or workflow that can write without proving required gates is not completion.""",
        "keywords": ["CI/CD pipeline", "GitHub Actions", "automated push", "validated promotion", "promotion pipeline", "harness E2E", "end-to-end testing", "application E2E", "exact head SHA", "required checks", "merge queue", "branch protection", "provider workflow", "artifact provenance", "least privilege CI", "workflow concurrency", "bot loop guard", "build once promote same artifact", "post-promotion containment"],
    }


def add_if_missing(draft: dict, receipt_name: str) -> str:
    names = {p["name"]: p for p in combined_prompts()}
    if draft["name"] in names:
        prompt = names[draft["name"]]
        print(json.dumps({"status": "already_present", "id": prompt["id"], "name": prompt["name"]}, indent=2))
        return prompt["id"]
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(draft, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        draft_path = handle.name
    output = run(sys.executable, "scripts/prompt_registry_ops.py", "add", "--input", draft_path, "--registry", REGISTRY)
    receipt = json.loads(output)
    if receipt.get("status") != "added" or receipt.get("site_parity") is not True:
        raise SystemExit(f"bad helper receipt for {receipt_name}: {receipt}")
    print(f"{receipt_name}={json.dumps(receipt, sort_keys=True)}")
    return str(receipt["id"])


def patch_tests() -> None:
    p07_test = ROOT / "tests" / "test_p02_p07_autonomous_iteration.py"
    text = p07_test.read_text(encoding="utf-8")
    if "def test_p07_coordinates_repository_generated_mutation_lanes" not in text:
        anchor = "    def test_p07_serial_fallback_is_fail_closed_and_not_user_scheduled(self) -> None:\n"
        addition = '''    def test_p07_coordinates_repository_generated_mutation_lanes(self) -> None:\n        prompt = self.effective["P07"]\n        content = prompt["copyContent"]\n        for phrase in (\n            "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT",\n            "first-class mutation lanes",\n            "repair the canonical source input/template/generator and regenerate it",\n            "one writer per generated mutation surface",\n            "A generated diff is proposed repository work, not automatic completion",\n            "canonical source boundary",\n        ):\n            self.assertIn(phrase, content)\n\n'''
        if anchor not in text:
            raise SystemExit("P07 focused-test anchor missing")
        p07_test.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")

    spec_test = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"
    text = spec_test.read_text(encoding="utf-8")
    if "def test_repository_automation_prompts_have_distinct_generation_and_promotion_roles" not in text:
        anchor = "    def test_new_source_prompts_are_intentionally_bounded(self) -> None:\n"
        addition = '''    def test_repository_automation_prompts_have_distinct_generation_and_promotion_roles(self) -> None:\n        generation = [p for p in self.full.values() if p["name"] == "Repository-Native Code Update Harness Builder"]\n        promotion = [p for p in self.full.values() if p["name"] == "Validated CI/CD Promotion Pipeline Builder"]\n        self.assertEqual(len(generation), 1)\n        self.assertEqual(len(promotion), 1)\n        generation = generation[0]\n        promotion = promotion[0]\n        self.assertNotEqual(generation["id"], promotion["id"])\n        self.assertEqual(generation["class"], "HARNESS / REPO-NATIVE CODE GENERATION")\n        self.assertEqual(promotion["class"], "HARNESS / CI-CD PROMOTION")\n        self.assertEqual(promotion["profile"], "spec-architecture")\n        self.assertEqual(promotion["actionabilityPolicy"], self.policy["policy_id"])\n        self.assertIn(self.policy["marker"], promotion["copyContent"])\n        for phrase in (\n            "SEPARATE AUTHORING, VALIDATION, AND PROMOTION",\n            "KEEP HARNESS E2E AND APPLICATION E2E DISTINCT",\n            "PIN EVERY GATE TO ONE CANDIDATE IDENTITY",\n            "REQUIRED plus SKIP is not green",\n            "least-privilege",\n            "build-once/promote-the-same-artifact",\n            "recursively trigger another writer forever",\n            "PROVE POST-PROMOTION CONTAINMENT",\n            "provider run ID",\n        ):\n            self.assertIn(phrase, promotion["copyContent"])\n        self.assertIn("code already authored", promotion["copyContent"])\n        self.assertIn("repository-owned mechanism", generation["copyContent"])\n        self.assertIn("Validated CI/CD Promotion Pipeline Builder", build_prompt_kit_registry.render())\n\n'''
        if anchor not in text:
            raise SystemExit("spec-architecture focused-test anchor missing")
        spec_test.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")

    delivery_test = ROOT / "tests" / "test_prompt_kit_mainline_delivery.py"
    text = delivery_test.read_text(encoding="utf-8")
    if "def test_p11_and_p15_compose_with_canonical_cicd_without_role_collapse" not in text:
        anchor = "    def test_repo_quick_access_explains_mainline_deployment_gate(self):\n"
        addition = '''    def test_p11_and_p15_compose_with_canonical_cicd_without_role_collapse(self):\n        prompts = {item["id"]: item for item in load_json("docs/prompts.json")}\n        p11 = prompts["P11"]\n        p15 = prompts["P15"]\n        for phrase in (\n            "CI/CD COMPOSITION CONTRACT",\n            "same validation logic locally and in CI",\n            "offline/synthetic boundary",\n            "Application or product end-to-end tests",\n            "required validator reported SKIP is not a successful CI gate",\n        ):\n            self.assertIn(phrase, p11["copyContent"])\n        for phrase in (\n            "CANONICAL PROMOTION PIPELINE CONTRACT",\n            "canonical GitHub Actions/CI/CD promotion workflow",\n            "Pin the candidate head SHA",\n            "skipped required harness or E2E gates",\n            "Automated push/merge/release is permitted only",\n            "verify containment of the proven integration SHA",\n        ):\n            self.assertIn(phrase, p15["copyContent"])\n        self.assertEqual(p11["class"], "VALIDATE / GATE")\n        self.assertEqual(p15["class"], "MERGE / RELEASE")\n\n'''
        if anchor not in text:
            raise SystemExit("mainline delivery focused-test anchor missing")
        delivery_test.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")


def reverse_harvest(generation_id: str, promotion_id: str) -> None:
    prompts = combined_prompts()
    by_id = {p["id"]: p for p in prompts}
    by_name = {p["name"]: p for p in prompts}
    generation = by_name["Repository-Native Code Update Harness Builder"]
    promotion = by_name["Validated CI/CD Promotion Pipeline Builder"]
    assert generation["id"] == generation_id
    assert promotion["id"] == promotion_id
    assert generation_id != promotion_id
    assert by_id["P11"]["class"] == "VALIDATE / GATE"
    assert by_id["P15"]["class"] == "MERGE / RELEASE"
    assert "CI/CD COMPOSITION CONTRACT" in by_id["P11"]["copyContent"]
    assert "CANONICAL PROMOTION PIPELINE CONTRACT" in by_id["P15"]["copyContent"]
    assert "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT" in by_id["P07"]["copyContent"]
    for phrase in ("GitHub Actions", "harness end-to-end", "application end-to-end", "exact candidate", "branch protection", "merge queue", "provider run ID", "post-promotion"):
        assert phrase.casefold() in promotion["copyContent"].casefold(), phrase
    print(json.dumps({"ledger": [["repo-native code generation", generation_id, "ADD"], ["generated-surface coexistence", "P07", "STRENGTHEN"], ["harness E2E as CI gate", "P11", "STRENGTHEN"], ["merge/release through canonical promotion", "P15", "STRENGTHEN"], ["validated CI/CD promotion architecture", promotion_id, "ADD"], ["generic harness construction", "P01", "ALREADY COVERED"], ["deployment execution", "P19", "ALREADY COVERED / DOWNSTREAM"]], "prompt_count": len(prompts)}, indent=2))


def main() -> int:
    strengthen_owners()
    generation_id = add_if_missing(generation_draft(), "GENERATION_HELPER_RECEIPT")
    promotion_id = add_if_missing(promotion_draft(), "PROMOTION_HELPER_RECEIPT")
    patch_tests()
    reverse_harvest(generation_id, promotion_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
