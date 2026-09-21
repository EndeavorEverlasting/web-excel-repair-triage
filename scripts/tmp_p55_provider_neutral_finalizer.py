from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/p55-provider-neutral-repo-bootstrap-20260920"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def patch_helper() -> None:
    path = ROOT / "scripts" / "prompt_registry_ops.py"
    text = path.read_text(encoding="utf-8")
    old_fields = 'EDITABLE_PROMPT_FIELDS = {"name", "copyContent", "sprintRole", "useWhen"}'
    new_fields = """EDITABLE_PROMPT_FIELDS = {
    "name", "class", "sprintRole", "useWhen", "inspectFirst",
    "expectedOutput", "proofGate", "copyContent", "keywords",
}"""
    if old_fields not in text:
        raise SystemExit("prompt_registry_ops editable-field anchor changed; refusing blind patch")
    text = text.replace(old_fields, new_fields, 1)

    old_loop = """    new_record = _clone_json(record)
    for field in changed_fields:
        value = patch[field]
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"Prompt edit field must be a non-empty string: {field}")
        new_record[field] = value.rstrip() if field == "copyContent" else value.strip()
"""
    new_loop = """    new_record = _clone_json(record)
    for field in changed_fields:
        value = patch[field]
        if field == "keywords":
            if not isinstance(value, list) or not value:
                raise SystemExit("Prompt edit keywords must be a non-empty list")
            normalized = [str(item).strip() for item in value]
            if any(not item for item in normalized):
                raise SystemExit("Prompt edit keywords must contain only non-empty strings")
            if len(normalized) != len({_normalize_text(item) for item in normalized}):
                raise SystemExit("Prompt edit keywords must not contain duplicates")
            new_record[field] = normalized
            continue
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"Prompt edit field must be a non-empty string: {field}")
        new_record[field] = value.rstrip() if field == "copyContent" else value.strip()
"""
    if old_loop not in text:
        raise SystemExit("prompt_registry_ops edit loop anchor changed; refusing blind patch")
    path.write_text(text.replace(old_loop, new_loop, 1), encoding="utf-8")


def patch_discovery() -> None:
    path = ROOT / "build_prompt_kit.py"
    text = path.read_text(encoding="utf-8")
    old = '    "local validation": "P54", "bootstrap": "P55", "github cli": "P55",\n'
    new = (
        '    "local validation": "P54", "bootstrap": "P55", "github cli": "P55",\n'
        '    "create repository": "P55", "create repo": "P55", "new repository": "P55",\n'
        '    "repository bootstrap": "P55", "name repository": "P55", "repository namespace": "P55",\n'
        '    "git provider": "P55", "publish repository": "P55",\n'
    )
    if old not in text:
        raise SystemExit("P55 synonym anchor changed; refusing blind patch")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_test() -> None:
    path = ROOT / "tests" / "test_p55_repository_bootstrap.py"
    path.write_text(
        """from __future__ import annotations

import unittest

import build_prompt_kit
from scripts import build_prompt_kit_registry, prompt_registry_ops


class P55RepositoryBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_kit_registry()
        }
        cls.p55 = cls.prompts["P55"]

    def test_p55_identity_is_context_grounded_and_provider_neutral(self) -> None:
        self.assertEqual(self.p55["name"], "Context-Grounded Repository Bootstrapper")
        self.assertEqual(
            self.p55["class"],
            "STANDARD AI / CONTEXT-GROUNDED REPOSITORY CREATION",
        )
        self.assertIn("Git-compatible provider", self.p55["sprintRole"])
        self.assertIn("incomplete", self.p55["useWhen"])
        self.assertIn("repository namespace", self.p55["keywords"])
        self.assertIn("Entire repository", self.p55["keywords"])

    def test_p55_completes_missing_parameters_under_explicit_policy(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "PARAMETER COMPLETION POLICY",
            "ASK",
            "INFER",
            "HYBRID",
            "HYBRID is the default",
            "Do not ask the operator to repeat information that can be recovered",
            "one compact question",
            "Freeze the manifest before repository mutation",
        ):
            self.assertIn(phrase, content)

    def test_p55_owns_namespace_screening_without_claiming_legal_clearance(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "NAMESPACE GATE",
            "exact-name collision",
            "root-name collision",
            "adjacent software/AI/developer-tool collision",
            "product-vs-subsystem naming level",
            "screening, not trademark or legal clearance",
            "existing canonical repository",
        ):
            self.assertIn(phrase, content)

    def test_p55_models_repository_provider_as_adapter(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "Repository provider: AUTO | GITHUB | ENTIRE | OTHER",
            "Provider adapter: AUTO | CLI | API | CONNECTOR | NATIVE_GIT",
            "GitHub CLI is one adapter",
            "do not invent provider syntax from memory",
            "current provider help, documentation, connector schema, or repository-owned adapter",
            "ENTIRE",
            "REMOTE_ONLY",
            "LOCAL_ONLY",
        ):
            self.assertIn(phrase, content)

    def test_p55_preserves_visibility_and_collision_safety(self) -> None:
        content = self.p55["copyContent"]
        for phrase in (
            "Never default to PUBLIC",
            "EXISTS_AND_MATCHES",
            "EXISTS_BUT_CONFLICTS",
            "CONFIRMED_NOT_FOUND",
            "UNKNOWN_AUTH",
            "UNKNOWN_PERMISSION",
            "UNKNOWN_NETWORK",
            "UNKNOWN_PROVIDER",
            "Do not interpret authentication, permission, or network failure as proof that a namespace is free",
        ):
            self.assertIn(phrase, content)

    def test_registry_edit_helper_can_keep_prompt_metadata_atomic(self) -> None:
        required = {
            "name",
            "class",
            "sprintRole",
            "useWhen",
            "inspectFirst",
            "expectedOutput",
            "proofGate",
            "copyContent",
            "keywords",
        }
        self.assertTrue(required.issubset(prompt_registry_ops.EDITABLE_PROMPT_FIELDS))

    def test_discovery_synonyms_route_repository_creation_to_p55(self) -> None:
        for term in (
            "create repository",
            "create repo",
            "new repository",
            "repository bootstrap",
            "name repository",
            "repository namespace",
            "git provider",
            "publish repository",
        ):
            self.assertEqual(build_prompt_kit.SYNONYMS[term], "P55")


if __name__ == "__main__":
    unittest.main()
""",
        encoding="utf-8",
    )


def write_patch() -> Path:
    copy_content = """PROMPT SURFACE: STANDARD AI / LOCAL AGENT. THIS IS NOT A GOODNIGHT, HAVE FUN (GNHF) PROMPT.

RECOVER THE PROJECT IDENTITY, COMPLETE THE REPOSITORY CREATION MANIFEST, THEN CREATE, ADOPT, OR PUBLISH THE CORRECT REPOSITORY THROUGH THE STRONGEST AUTHORIZED GIT-COMPATIBLE PROVIDER SURFACE. DO NOT RETURN A PLAN ONLY WHEN SAFE CREATION OR ADOPTION IS AUTHORIZED.

Repository/project intent: xyz_repository_or_project_intent
Requested repository name: xyz_repository_name_or_unspecified
Repository provider: AUTO | GITHUB | ENTIRE | OTHER
Provider adapter: AUTO | CLI | API | CONNECTOR | NATIVE_GIT
Parameter completion policy: ASK | INFER | HYBRID
Visibility: PRIVATE | PUBLIC | INTERNAL | UNSPECIFIED
Owner/organization: xyz_owner_or_unspecified
Description: xyz_description_or_unspecified
Local mode: NEW_CLONE | PUBLISH_EXISTING | ADOPT_EXISTING | REMOTE_ONLY | LOCAL_ONLY | AUTO
Local parent or source directory: xyz_path_or_unspecified
Bootstrap options: xyz_readme_license_gitignore_template_or_unspecified

EXECUTION BRIEF / SOURCE / DONE / SELF-CHECK
- ROLE: Act as the repository bootstrap owner. Recover identity, resolve missing parameters, screen namespace collisions, execute through the available provider adapter, and verify only the state actually observed.
- WHERE TO LOOK: Start with current conversation and operator guidance, then recoverable chats/handoffs, existing repositories, source artifacts, product vocabulary, repository/provider policy, current provider capabilities, local Git roots when available, and applicable Prompt Kit/repository rules.
- DEFINITION OF DONE: one canonical repository owner is selected or created; every creation parameter is RESOLVED, INFERRED, or USER_ONLY; required namespace/provider collision gates are dispositioned; the authorized create/adopt/publish action completes through an evidenced adapter; and remote/local proof is reported without promotion.
- SELF-CHECK: Before creation and before completion, re-read the manifest, namespace ledger, provider result, remote identity, and local Git evidence. Unsupported fields remain UNKNOWN or USER_ONLY.

CONTEXT-GROUNDED PRE-CREATION RECONSTRUCTION
1. Treat preceding/surrounding operator guidance, named or recoverable prior chats/handoffs, source files/spreadsheets/apps/scripts, connected repository-provider state, and discoverable local repositories as evidence. Do not ask the operator to repeat information that can be recovered.
2. Recover the durable product/project responsibility rather than naming from the first spreadsheet, script, prototype, folder, implementation detail, or temporary integration.
3. Check for an existing canonical repository before CREATE NEW. Prefer ADOPT / CONTINUE / REFACTOR / RENAME EXISTING OWNER over minting a competing repository when current evidence shows an owner already exists.
4. Preserve explicit operator naming unless collision or ownership evidence materially contradicts it.

REPOSITORY IDENTITY MANIFEST
Before mutation, produce a compact manifest. Every field records:
value | status | evidence | confidence
Status is exactly RESOLVED, INFERRED, or USER_ONLY.

The manifest covers at least:
- product/project identity and durable repository responsibility;
- repository name and owner/organization;
- repository provider and provider adapter;
- visibility and description;
- existing-owner disposition;
- creation/adoption/publish mode;
- local parent/source path when observable;
- default-branch and remote-name policy;
- README, license, gitignore/template choices;
- initial-history and push policy;
- namespace/collision result;
- parameter completion policy;
- unresolved consequential choices.

PARAMETER COMPLETION POLICY
ASK
- Recover all available evidence first.
- Do not invent a missing parameter.
- Ask one compact question containing only genuinely unresolved creation-blocking fields.

INFER
- Infer missing fields when current evidence supports a defensible value.
- Prefer conventional, reversible choices and record the rationale.
- Never infer credentials, destructive history rewrites, secret values, or PUBLIC visibility merely to complete the manifest.
- When visibility is otherwise unresolved and autonomous completion is explicitly selected, prefer PRIVATE when the selected provider supports it and record the inference.

HYBRID
- HYBRID is the default when no completion policy is supplied.
- Infer ordinary reversible metadata.
- Ask only consequential choices that remain unresolved after recovery.
- Missing visibility without an applicable project/organization policy remains USER_ONLY rather than silently becoming PUBLIC.

A parameter being absent from the operator sentence does not make it UNKNOWN until evidence recovery has been attempted.

NAMESPACE GATE
When a name is missing, generated, or plausibly colliding:
1. Identify durable repository responsibility and established operator/project vocabulary.
2. Generate a small candidate set only when needed.
3. Evaluate serious candidates for semantic fit, implementation durability, exact-name collision, root-name collision, adjacent software/AI/developer-tool collision, collisions with the operator existing repositories, product-vs-subsystem naming level, and misleading architectural implications.
4. Record:
candidate | metaphor/meaning | fit | collision signal | disposition | rationale | evidence
5. Exact compound uniqueness does not erase a problematic root-name collision.
6. Prefer strengthening an existing project/repository identity over creating a second identity for the same owner.
7. Provider/web lookup is namespace screening, not trademark or legal clearance.
8. Failure to perform a broader public-web screen is UNKNOWN global clearance, not proof of uniqueness. Provider namespace availability and existing-owner checks remain mandatory before creation.
9. Under INFER or HYBRID, select the clearly dominant candidate when evidence strongly separates it. Under ASK, present the bounded ledger when the naming choice remains consequential.

PROVIDER CAPABILITY GATE
Repository hosting and Git actions are replaceable adapters.

Repository provider: AUTO | GITHUB | ENTIRE | OTHER
Provider adapter: AUTO | CLI | API | CONNECTOR | NATIVE_GIT

- Resolve the provider and adapter actually available in the current environment.
- GitHub CLI is one adapter, not the repository-creation ontology.
- ENTIRE or another provider is valid when the current environment exposes the required authorized operation.
- Inspect current provider help, documentation, connector schema, or repository-owned adapter before constructing provider-specific mutation commands.
- For a changing or unfamiliar provider, do not invent provider syntax from memory.
- If the selected provider cannot perform the requested create/adopt/publish mode, preserve the complete manifest and stop at that exact capability/authorization gate rather than silently changing topology.

EXECUTION SURFACE
BOTH
- Local filesystem/Git and remote provider mutation are available. Verify both.

REMOTE_ONLY
- Remote provider mutation/read-back is available but local filesystem/Git proof is unavailable. Complete the remote side and report local root/origin/branch as UNOBSERVABLE.

LOCAL_ONLY
- Local Git/filesystem is available but remote mutation/auth is unavailable. Prepare and verify the local source, then stop at the exact remote provider gate.

VISIBILITY SAFETY
- Never default to PUBLIC.
- Explicit operator preference or durable repository/organization policy may resolve visibility.
- ASK: request unresolved visibility.
- HYBRID: unresolved visibility is USER_ONLY.
- INFER: when autonomous completion was selected and no stronger policy exists, prefer PRIVATE if supported and mark it INFERRED.
- Never publish existing history without explicit or policy-backed authority.

LOCAL DIRECTORY GATE
When a local filesystem is available:
1. Resolve the exact existing Git root for publish/adopt mode or intended parent for a new clone.
2. Verify root, status, branch, recent history, and remotes before publishing existing work.
3. Refuse wrong roots, ambiguous history, unowned dirty work, unexpected remotes, detached history requiring judgment, or unknown content in the intended child path.
4. Never delete, reset, overwrite, clean, or repurpose ambiguous work merely to satisfy repository creation.

REMOTE COLLISION GATE
Classify the provider lookup as exactly one of:
EXISTS_AND_MATCHES
EXISTS_BUT_CONFLICTS
CONFIRMED_NOT_FOUND
UNKNOWN_AUTH
UNKNOWN_PERMISSION
UNKNOWN_NETWORK
UNKNOWN_PROVIDER

Do not interpret authentication, permission, or network failure as proof that a namespace is free.
- EXISTS_AND_MATCHES -> adopt/reuse the existing owner.
- EXISTS_BUT_CONFLICTS -> resolve owner/name; do not overwrite.
- CONFIRMED_NOT_FOUND -> creation may proceed when the manifest has no blocking USER_ONLY field.
- UNKNOWN_* -> preserve the manifest and advance the exact lookup/auth/provider gate.

EXECUTION
Once the manifest contains no creation-blocking field:
1. Freeze the manifest before repository mutation.
2. Record selected provider, adapter, mode, owner/name, visibility, description, bootstrap choices, history/push policy, and local path posture.
3. Execute CREATE, ADOPT, or PUBLISH through the selected authorized adapter.
4. Preserve the exact command, API operation, connector action, or provider receipt.
5. Add only bootstrap artifacts authorized by the manifest. Do not silently add frameworks, CI, deployment topology, package managers, or application architecture merely because a repository is empty.
6. Read authoritative provider/local state back after mutation before retrying or claiming completion.

GITHUB ADAPTER
When GitHub CLI is selected and verified, use reviewed gh/git command shapes consistent with current help and repository policy. Never expose token material or automate authentication.
When a connected GitHub API/app/connector is selected, use the exposed lookup/create/read-back operations instead of pretending gh ran.

ENTIRE / OTHER PROVIDER ADAPTER
Use only currently evidenced provider operations. Confirm provider identity, namespace, selected repository identity, mutation result, and read-back fields exposed by that provider. Do not hard-code remembered CLI flags into this prompt.

VERIFICATION
REMOTE
- repository owner/name;
- visibility when exposed;
- repository URL/identity;
- default branch or empty-repository state when exposed;
- expected remote history when publishing.

LOCAL
- verified root;
- origin/remotes;
- branch and HEAD;
- clean/expected status;
- expected bootstrap files/history.

Do not claim LOCAL proof from REMOTE_ONLY execution or REMOTE proof from LOCAL_ONLY preparation.

FINAL RESPONSE
Report:
PROJECT IDENTITY MANIFEST
NAMESPACE LEDGER
PARAMETER RESOLUTION — supplied / recovered / inferred / user-only
EXISTING OWNER DISPOSITION
PROVIDER / ADAPTER
CREATION OR ADOPTION ACTION
REMOTE PROOF
LOCAL PROOF
FILES / BOOTSTRAP
BLOCKERS / USER-ONLY GATES
PROOF CEILING
FINAL REPOSITORY STATE
NEXT COMMAND

The task is incomplete if required repository parameters silently remain placeholders when they could have been recovered, inferred under the selected policy, or asked in one compact question.
"""
    patch = {
        "name": "Context-Grounded Repository Bootstrapper",
        "class": "STANDARD AI / CONTEXT-GROUNDED REPOSITORY CREATION",
        "sprintRole": (
            "Recover repository identity and namespace, complete missing creation parameters under an explicit autonomy policy, "
            "then create, adopt, or publish through the strongest authorized Git-compatible provider surface and verify reachable state"
        ),
        "useWhen": (
            "The operator wants a repository created, adopted, published, or split from an existing project and one or more repository "
            "parameters are incomplete, or the correct owner/name/provider must be recovered before mutation."
        ),
        "inspectFirst": (
            "Current and recoverable operator context; existing repositories and source artifacts; durable project vocabulary and namespace "
            "signals; owner/visibility policy; requested or inferable provider and adapter; local Git root when available; provider authentication/"
            "authorization and collision state; bootstrap/history choices; and repository mutation authority."
        ),
        "expectedOutput": (
            "A complete Repository Identity Manifest and namespace ledger with every field RESOLVED, INFERRED, or USER_ONLY; reuse of an existing "
            "canonical owner or a verified new/adopted/published repository; exact provider/adapter action evidence; strongest reachable remote/local "
            "Git proof; proof ceiling; and one executable next command."
        ),
        "proofGate": (
            "Context and existing-owner evidence are recovered before naming; every required creation parameter is supplied, inferred under the "
            "selected ASK/INFER/HYBRID policy, or explicitly USER_ONLY; exact/root/adjacent namespace collisions are dispositioned without treating "
            "screening as legal clearance; visibility never silently defaults to public; provider syntax/capability is evidenced rather than invented; "
            "authorized create/adopt/publish succeeds through the selected Git-compatible adapter; and remote/local claims match authoritative read-back."
        ),
        "copyContent": copy_content,
        "keywords": [
            "repository creation",
            "create repository",
            "new repository",
            "repository bootstrap",
            "name repository",
            "repository namespace",
            "git provider",
            "GitHub repository",
            "Entire repository",
            "publish repository",
            "context grounded bootstrap",
        ],
    }
    path = Path("/tmp/p55_patch.json")
    path.write_text(json.dumps(patch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    run("git", "fetch", "--all", "--prune", "--tags")
    run("git", "merge-base", "--is-ancestor", "0f132b337fd6d92456ea020ad347fc8068317c7c", "origin/main")

    patch_helper()
    patch_discovery()
    write_test()
    patch_path = write_patch()

    run(
        "python",
        "scripts/prompt_registry_ops.py",
        "edit",
        "--prompt-id",
        "P55",
        "--input",
        str(patch_path),
        "--disposition",
        "NO_CAPABILITY_CHANGE",
        "--evidence-ref",
        "tests/test_p55_repository_bootstrap.py",
        "--evidence-ref",
        "scripts/prompt_registry_ops.py",
        "--rationale",
        "Strengthen the existing P55 repository-creation owner for context recovery, explicit missing-parameter completion policy, namespace screening, and provider-neutral Git execution while preserving its accepted capability ownership.",
    )

    for command in (
        ("python", "-m", "unittest", "tests.test_p55_repository_bootstrap", "-v"),
        ("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "tests.test_prompt_kit_discovery", "tests.test_skill_prompt_registry", "-v"),
        ("python", "scripts/prompt_registry_ops.py", "validate"),
        ("python", "scripts/evaluate_prompt_language.py", "--summary"),
        ("python", "scripts/validate_prompt_kit_discovery.py", "--summary"),
        ("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"),
        ("git", "diff", "--check"),
    ):
        run(*command)

    run(
        "git",
        "rm",
        "-f",
        ".github/workflows/tmp-p55-provider-neutral-finalizer.yml",
        ".github/p55-provider-neutral-trigger",
        "scripts/tmp_p55_provider_neutral_finalizer.py",
    )
    run(
        "git",
        "add",
        "scripts/prompt_registry_ops.py",
        "build_prompt_kit.py",
        "tests/test_p55_repository_bootstrap.py",
        "docs/prompts.json",
        "harness/prompt-topology/prompt-capability-profiles.v1.json",
        "harness/prompt-topology/prompt-capability-migrations.v1.json",
        "harness/prompt-compilation/prompt-semantic-migrations.v1.json",
        "web/prompt-kit/index.html",
    )
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "feat(prompt-kit): strengthen P55 repository bootstrap")

    for command in (
        ("python", "-m", "unittest", "tests.test_p55_repository_bootstrap", "-v"),
        ("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "tests.test_prompt_kit_discovery", "tests.test_skill_prompt_registry", "-v"),
        ("python", "scripts/prompt_registry_ops.py", "validate"),
        ("python", "scripts/evaluate_prompt_language.py", "--summary"),
        ("python", "scripts/validate_prompt_kit_discovery.py", "--summary"),
        ("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"),
        ("git", "diff", "--check"),
    ):
        run(*command)

    run("git", "status", "--short")
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
