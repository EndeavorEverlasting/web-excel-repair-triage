from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_BRANCH = "feat/prompt-kit-versioning-system-establisher-20260908"
CARRIER = ".github/workflows/tmp-hierarchy-state-transition-repair.yml"
CANONICAL_CARRIER_BLOB = "27c12dfe62a0250311c0ddad0144802707bf6bac"
TEMP_FILES = [
    ".github/workflows/tmp-versioning-owner-discovery.yml",
    "tmp/versioning_prompt_executor.py",
]


def run(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, text=True, capture_output=capture)
    if capture:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=os.sys.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    return result


def git_output(*args: str) -> str:
    return run(["git", *args], capture=True).stdout.strip()


run(["git", "config", "user.name", "github-actions[bot]"])
run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
run(["git", "fetch", "origin", "main", REPO_BRANCH, "--prune"])

carrier_head = git_output("rev-parse", "origin/main")
semantic_base = git_output("rev-parse", f"{carrier_head}^")
carrier_blob = git_output("rev-parse", f"{semantic_base}:{CARRIER}")
changed = [line for line in git_output("diff", "--name-only", semantic_base, carrier_head).splitlines() if line]
print(json.dumps({"carrier_head": carrier_head, "semantic_base": semantic_base, "carrier_blob": carrier_blob, "carrier_changed_files": changed}, indent=2))
if carrier_blob != CANONICAL_CARRIER_BLOB:
    raise SystemExit(f"semantic base does not contain canonical carrier: {carrier_blob}")
if changed != [CARRIER]:
    raise SystemExit(f"temporary carrier head contains unexpected files: {changed}")

run(["git", "merge", "--no-edit", semantic_base])
for path in TEMP_FILES:
    if Path(path).exists():
        run(["git", "rm", path])

# Baseline after reconciling the current semantic main floor, before the new prompt exists.
from scripts.build_prompt_kit_registry import load_prompt_registry

baseline_prompts = load_prompt_registry()
baseline = {"count": len(baseline_prompts), "ids": [str(p["id"]) for p in baseline_prompts]}
Path("/tmp/versioning-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

copy_content = r'''ESTABLISH AND ENFORCE ONE VERSIONING SYSTEM FOR THIS REPOSITORY. DO NOT MERELY EXPLAIN THE CURRENT LABELS, ADD A DECORATIVE VERSION NUMBER, OR START TAGGING RELEASES WITHOUT FIRST DEFINING THE AUTHORITY THAT MAKES THOSE TAGS MEAN SOMETHING.

Repository / product: xyz_repo_or_product
Current version clues, if known: xyz_tags_manifests_labels_or_unknown
Compatibility / consumers: xyz_consumers_or_resolve_from_evidence
Release target, if any: xyz_release_target_or_not_yet

MISSION
Turn ambiguous, missing, or fragmented versioning into one durable repository-native system. Establish how a human-facing product release is identified, how the next version is derived from changes, which files and surfaces must agree, how tags, releases, and changelogs are produced, and how compatibility or rollback is handled. Preserve exact commit/artifact identity as proof; a friendly release label supplements exact identity and must never replace it.

1. REFRESH AND INVENTORY THE REAL VERSION SURFACES
- Refresh the remote default branch and inspect current tags and releases before mutation.
- Find every version-like surface that can be mistaken for product authority: package/application manifests, plugin metadata, desktop/mobile bundle versions, UI labels, API versions, schema/protocol versions, database migration generations, generated artifacts, docs, release workflows, changelogs, and Git tags.
- Classify each as PRODUCT RELEASE VERSION, SCHEMA/PROTOCOL VERSION, BUILD/ARTIFACT IDENTITY, DEPENDENCY VERSION, or DESCRIPTIVE DISPLAY ONLY.
- Do not promote a schema version, capability version, visible vXX label, date, or commit abbreviation into product authority merely because it already exists.
- Identify current consumers and compatibility promises. If no meaningful compatibility boundary exists, say so instead of pretending SemVer semantics exist.

2. REUSE PRIOR ART WITHOUT CARGO-CULTING IT
- Inspect release/version tooling already present in the repository and ecosystem before creating a new mechanism.
- Consider established patterns such as Changesets-style reviewed version PRs and synchronized manifest/plugin versions, release-please or semantic-release style automation, conventional changelog tooling, or a small repository-owned version command when those fit the stack.
- Adopt mechanics, not slogans. Do not install a heavyweight release framework when a small deterministic owner is sufficient.
- Preserve one source of truth. Generated or mirrored version fields must derive from or be validated against that owner.

3. CHOOSE THE VERSION SCHEME FROM PRODUCT SEMANTICS
Select and justify the smallest scheme that matches the actual product:
- SemVer when MAJOR/MINOR/PATCH can be tied to a real public compatibility contract.
- CalVer when time or cadence is the primary release identity and compatibility is governed separately.
- A monotonic release/build sequence, or another documented scheme, when neither SemVer nor CalVer truthfully models the product.
Do not choose SemVer merely because it is familiar. Record why the selected scheme fits and what evidence would justify changing schemes later.

4. DEFINE DETERMINISTIC BUMP AND NO-BUMP RULES
Create a change-to-version matrix. For SemVer, define what this repository specifically means by breaking/major, compatible feature/minor, and compatible fix/patch. For another scheme, define equivalent advancement rules.
Explicitly decide how to handle:
- docs-only, tests-only, refactors, internal tooling, and generated-file-only changes;
- user-visible fixes and features;
- breaking API, config, data-format, or CLI behavior;
- prereleases, release candidates, hotfixes, and backports when relevant.
The rule must let two competent executors derive the same next version from the same accepted change set. If human judgment remains, name the narrow judgment gate instead of disguising it as automation.

5. ESTABLISH ONE CANONICAL VERSION AUTHORITY
- Name the authoritative file, metadata source, or release record: one canonical version authority for the human-facing product release.
- List every synchronized version surface and whether it is generated, mirrored, or independently schema-versioned.
- Add a deterministic check that fails when synchronized version surfaces drift.
- Keep schema/protocol versions and API versions independent when their compatibility lifecycle is not identical to the product release lifecycle.
- A Git tag must resolve to the exact validated release commit/artifact; a UI badge alone is never freshness proof.

6. BOOTSTRAP WITHOUT REWRITING HISTORY
- Infer a defensible starting version from existing releases, tags, and product maturity when possible; otherwise choose and document an explicit cutover version.
- Do not rename old tags, rewrite published history, decrement a version, or reuse a released version number to make history look cleaner.
- Record the cutover rule so old ad-hoc labels remain interpretable without remaining authoritative.

7. INSTALL THE RELEASE MECHANICS
Implement the smallest repository-native path that fits the chosen policy:
- a version/bump or version-PR command;
- synchronized manifest/update logic where required;
- changelog or release-note generation from reviewed change evidence;
- tag/release creation wiring only after owning validation succeeds;
- CI or hooks that reject impossible versions, version drift, reused tags, or releases from an unvalidated or stale commit.
Where release publication needs credentials, protected environments, stores, registries, or production authority, install and prove everything up to that boundary and name the exact downstream gate.

8. COMPATIBILITY, DEPRECATION, MIGRATION, AND ROLLBACK
- Define what a consumer can infer from a version change.
- For breaking changes, require migration and deprecation evidence appropriate to the product.
- Treat rollback as redeploying or restoring a previously identified artifact or commit, not decrementing or reusing a version.
- If a release must be withdrawn, preserve its historical identity and document replacement or yank behavior rather than erasing it.

9. PROVE THE SYSTEM BEFORE CALLING IT DONE
Add focused tests, fixtures, or dry-run proofs that cover at least:
- representative no-bump and bump cases;
- the highest-impact compatibility or breaking case for the chosen scheme;
- synchronization of all declared product-version mirrors;
- idempotent version calculation from the same accepted change set;
- tag/release identity pointing at the exact validated commit/artifact;
- failure when a version surface drifts or a released version would be reused.
Run the repository's owning validators and builds plus git diff checks. Do not claim a published/runtime release merely from static or CI policy proof.

10. CONVERGE, THEN RELEASE THROUGH THE DOWNSTREAM OWNER
Integrate the exact validated versioning-system change into the refreshed default branch when authorized. Report the canonical version authority, current or cutover version, scheme and bump matrix, synchronized surfaces, automation entrypoint, changelog/tag path, compatibility and rollback rules, validation evidence, and proof ceiling.
Once the system is established, ordinary merge/release execution is downstream work. Reuse the repository's existing release executor rather than turning this prompt into a perpetual release prompt.

DEFINITION OF DONE
The repository has one human-friendly release-version authority whose semantics are deterministic and enforced; exact Git/artifact identity remains available for forensic freshness; competing version-like surfaces are classified instead of conflated; release mechanics cannot silently drift mirrors or reuse history; compatibility and rollback meaning is documented; representative bump behavior is tested; and the validated system is integrated into the current default branch or stopped at one exact external publication or authority blocker.'''

draft = {
    "name": "Repository Versioning System Establisher",
    "type": "BUILD + FACTOR",
    "class": "REPOSITORY / VERSIONING + RELEASE IDENTITY",
    "sprintRole": "Establish one evidence-based, enforceable repository/product versioning authority, bump policy, synchronized version surfaces, and release identity path before ordinary release execution begins",
    "progress": "YES",
    "useWhen": "A repository or product has no coherent human-facing release version, has multiple drifting version labels, uses commit hashes or schema versions without an operator-facing release sequence, applies version bumps inconsistently, or needs a durable versioning system before normal merge/release execution can be trusted.",
    "inspectFirst": "Current default branch and recent tags/releases; package/plugin/app manifests; visible version labels; schemas/protocol versions; changelog/release-note tooling; CI/release workflows; artifact identity contracts; consumers and compatibility promises; rollback/deprecation history; then credible existing release/versioning tooling already present in the stack.",
    "expectedOutput": "A repository-native versioning authority and policy with justified scheme selection, deterministic bump rules, synchronized product-version surfaces, changelog/tag/release wiring, compatibility/migration/rollback rules, bootstrap/cutover evidence, focused regression proof, and integration into the current default branch; actual publishing remains a downstream gate when release credentials or production authority are separate.",
    "nextStep": "Implement the selected version authority and its smallest enforceable automation now, prove bump and synchronization behavior with fixtures or dry runs, integrate the exact green change into the current default branch, then hand ordinary release execution to the repository release owner.",
    "proofGate": "One canonical human-facing product release authority is named; exact Git/artifact identity remains distinct; the scheme choice is evidence-based rather than cargo-culted; bump/no-bump semantics and synchronized surfaces are machine-checkable; migration does not rewrite history or reuse released versions; compatibility, deprecation, rollback, changelog, tag, and release behavior are explicit; focused tests and registered validators pass; and the validated owned change is contained in the refreshed default branch.",
    "color": "Teal",
    "category": "standard",
    "profile": "spec-architecture",
    "copyContent": copy_content,
    "keywords": [
        "versioning system",
        "repository versioning",
        "product version",
        "semantic versioning",
        "semver",
        "calver",
        "version authority",
        "version bump",
        "release identity",
        "release tags",
        "changelog",
        "changesets",
        "release automation",
        "version drift",
        "compatibility version",
        "version policy",
    ],
}
Path("/tmp/versioning-prompt-draft.json").write_text(json.dumps(draft, indent=2), encoding="utf-8")

helper = run(
    [
        "python",
        "scripts/prompt_registry_ops.py",
        "add",
        "--input",
        "/tmp/versioning-prompt-draft.json",
        "--registry",
        "spec-architecture-prompts",
    ],
    capture=True,
)
Path("/tmp/versioning-helper-receipt.json").write_text(helper.stdout, encoding="utf-8")
receipt = json.loads(helper.stdout)
if receipt.get("site_parity") is not True:
    raise SystemExit(f"helper site parity failed: {receipt}")
if receipt.get("registry_id") != "spec-architecture-prompts":
    raise SystemExit(f"wrong helper registry: {receipt}")
if receipt.get("name") != "Repository Versioning System Establisher":
    raise SystemExit(f"wrong helper result: {receipt}")
allocated_id = str(receipt["id"])
Path("/tmp/allocated-id").write_text(allocated_id, encoding="utf-8")

focused_test = f'''import unittest\n\nfrom scripts.build_prompt_kit_registry import load_prompt_registry\n\n\nclass RepositoryVersioningSystemPromptTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.prompts = load_prompt_registry()\n        cls.prompt = next(p for p in cls.prompts if p.get("name") == "Repository Versioning System Establisher")\n        cls.p15 = next(p for p in cls.prompts if p.get("id") == "P15")\n\n    def test_helper_allocated_identity_and_downstream_owner_remain_distinct(self):\n        self.assertEqual(self.prompt["id"], {allocated_id!r})\n        self.assertNotEqual(self.prompt["id"], self.p15["id"])\n        p15_text = " ".join(str(self.p15.get(k, "")) for k in ("name", "sprintRole", "useWhen", "copyContent")).lower()\n        self.assertIn("release", p15_text)\n        self.assertIn("merge", p15_text)\n\n    def test_versioning_owner_establishes_policy_before_release_execution(self):\n        text = self.prompt["copyContent"].lower()\n        required = [\n            "one canonical version authority",\n            "exact commit/artifact identity",\n            "semver",\n            "calver",\n            "do not choose semver merely because it is familiar",\n            "change-to-version matrix",\n            "synchronized version surface",\n            "changelog",\n            "do not rename old tags",\n            "rollback",\n            "deprecation",\n            "idempotent version calculation",\n            "released version would be reused",\n            "ordinary merge/release execution is downstream work",\n        ]\n        for phrase in required:\n            self.assertIn(phrase, text)\n\n    def test_scheme_selection_preserves_schema_and_release_identity_boundaries(self):\n        text = self.prompt["copyContent"].lower()\n        self.assertIn("product release version", text)\n        self.assertIn("schema/protocol version", text)\n        self.assertIn("ui badge alone is never freshness proof", text)\n        self.assertIn("do not claim a published/runtime release", text)\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
Path("tests/test_repository_versioning_system_prompt.py").write_text(focused_test, encoding="utf-8")

run(["python", "-m", "unittest", "tests.test_repository_versioning_system_prompt", "-v"])
run(["python", "scripts/prompt_registry_ops.py", "validate"])
run(["python", "scripts/validate_prompt_kit_discovery.py", "--summary"])
run(["python", "-m", "unittest", "tests.test_prompt_kit_discovery", "-v"])
run(["python", "-m", "unittest", "tests.test_prompt_language_audit", "-v"])
run(["python", "scripts/evaluate_prompt_language.py", "--output", "/tmp/prompt-language-audit.json", "--summary"])
run(["python", "-m", "unittest", "tests.test_skill_prompt_registry", "-v"])
run(["python", "scripts/validate_prompt_kit_order_navigation.py", "--output", "/tmp/prompt-kit-order-navigation-audit.json", "--summary"])
run(["python", "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "-v"])
run(["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"])
run(["git", "diff", "--check"])

# Whole-chat harvest pass 2: repeat the registered external search and falsify duplicate/overlap assumptions.
external = run(
    [
        "python",
        "scripts/search_operant_external_catalog.py",
        "--source",
        "prompts-chat",
        "--query",
        "repository versioning semantic versioning release strategy",
        "--limit",
        "10",
    ],
    capture=True,
)
Path("/tmp/prompts-chat-versioning-pass2.json").write_text(external.stdout, encoding="utf-8")
external_payload = json.loads(external.stdout)
if external_payload.get("automatic_prompt_authoring") is not False:
    raise SystemExit("external search unexpectedly authorizes prompts")
if external_payload.get("policy", {}).get("promotion_owner_prompt") != "P79":
    raise SystemExit("P79 is no longer the external promotion owner")
if int(external_payload.get("hit_count", 0)) <= 0:
    raise SystemExit("pass-2 registered catalog search returned no evidence")
if any(h.get("disposition") not in {"REFERENCE_ONLY", "ADAPT"} for h in external_payload.get("hits", [])):
    raise SystemExit("unexpected external hit disposition")

prompts = load_prompt_registry()
if len(prompts) != baseline["count"] + 1:
    raise SystemExit(f"prompt count changed by more than one: {baseline['count']} -> {len(prompts)}")
added = [p for p in prompts if str(p["id"]) not in baseline["ids"]]
if len(added) != 1 or added[0].get("name") != "Repository Versioning System Establisher":
    raise SystemExit(f"unexpected new prompt set: {[(p.get('id'), p.get('name')) for p in added]}")
if str(added[0]["id"]) != allocated_id:
    raise SystemExit("helper allocation and registry identity diverged")
if "P15" not in baseline["ids"]:
    raise SystemExit("P15 was not present in baseline")
text = str(added[0]["copyContent"]).lower()
for phrase in (
    "semver",
    "calver",
    "one canonical version authority",
    "change-to-version matrix",
    "bootstrap without rewriting history",
    "ordinary merge/release execution is downstream work",
):
    if phrase not in text:
        raise SystemExit(f"pass-2 semantic gap: {phrase}")

run(["python", "-m", "unittest", "tests.test_repository_versioning_system_prompt", "-v"])
run(["python", "scripts/prompt_registry_ops.py", "validate"])
run(["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"])
run(["git", "diff", "--check"])

run(["git", "add", "-A"])
run(["git", "diff", "--cached", "--check"])
print("--- staged status ---")
print(git_output("diff", "--cached", "--name-status"))
run(["git", "commit", "-m", "feat(prompt-kit): add repository versioning system establisher"])
run(["git", "push", "origin", f"HEAD:{REPO_BRANCH}"])
print(json.dumps({"feature_head": git_output("rev-parse", "HEAD"), "allocated_id": allocated_id, "baseline_prompt_count": baseline["count"], "final_prompt_count": len(prompts), "site_parity": receipt["site_parity"]}, indent=2))
