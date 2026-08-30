#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match in {relative}, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write_json(relative: str, payload: dict) -> None:
    (ROOT / relative).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


# 1. Governance: resolve the product naming gate without claiming migration complete.
old_boundary = """Prompt Kit began here as a spreadsheet and is separable. Intended home: a dedicated repository under `UnderDeskDev`, not yet named or created; agents must not invent its name or claim migration complete.\nUntil proven, Prompt Kit sources here remain operationally authoritative and must not be silently moved. It may source, pin, mirror, package, link to, or consume Prompt Kit releases, but must not become a competing Prompt Kit authority; keep cross-repo dependencies explicit and versioned."""
new_boundary = """**Operant** is the operator-approved product identity for the agentic capability/execution system formerly called Prompt Kit. It began here as a spreadsheet artifact and is separable. Intended home: `UnderDeskDev/Operant`; that repository is not yet created/proven, so agents must not claim migration complete.\nUntil cutover is proven, legacy `prompt-kit` paths and sources here remain authoritative compatibility surfaces. This repo may pin, mirror, package, link to, or consume Operant releases, but must not become a competing Operant authority; cross-repo dependencies stay explicit and versioned."""
replace_once("AGENTS.md", old_boundary, new_boundary)

replace_once(
    "tests/test_governance_contract.py",
    "def test_prompt_kit_separation_is_explicit_and_transition_safe(self) -> None:",
    "def test_operant_separation_is_explicit_and_transition_safe(self) -> None:",
)
for old, new in (
    ('"dedicated repository under `UnderDeskDev`",', '"`UnderDeskDev/Operant`",'),
    ('"not yet named or created",', '"not yet created/proven",'),
    ('"must not invent its name",', '"operator-approved product identity",'),
    ('"Prompt Kit sources here remain operationally authoritative",', '"legacy `prompt-kit` paths and sources here remain authoritative compatibility surfaces",'),
    ('"source, pin, mirror, package, link to, or consume Prompt Kit releases",', '"pin, mirror, package, link to, or consume Operant releases",'),
    ('"must not become a competing Prompt Kit authority",', '"must not become a competing Operant authority",'),
):
    replace_once("tests/test_governance_contract.py", old, new)

# 2. Machine-readable product identity. Legacy paths stay stable until cross-repo cutover.
identity = {
    "schema_version": "operant-product-identity/v1",
    "product_id": "operant",
    "product_name": "Operant",
    "product_version": "0.1.0",
    "status": "transition",
    "tagline": "Agentic Capability & Execution System",
    "purpose": "Map capabilities, skills, implementations, agents, hooks, and evidence into fast, evidence-bounded execution routes.",
    "ontology_lenses": [
        "capabilities",
        "skills",
        "implementations",
        "agents",
        "evidence",
    ],
    "legacy_identity": {
        "names": ["AI Harness Prompt Kit", "Prompt Kit"],
        "latest_legacy_display_version": "v40",
        "compatibility_prefixes": ["prompt-kit", "PromptKit"],
        "rule": "Legacy names and paths are compatibility identifiers, not the current product brand.",
    },
    "authority": {
        "current_repository": "EndeavorEverlasting/web-excel-repair-triage",
        "target_repository": "UnderDeskDev/Operant",
        "target_repository_state": "not-created-or-unproven",
        "cutover_rule": "Current repository remains authoritative until the dedicated repository passes source, build, evidence, consumer, and release-identity parity and the old repository is reduced to an explicit versioned consumer.",
    },
    "compatibility": {
        "visible_brand": "Operant",
        "visible_version": "0.1",
        "preserve_paths": [
            "web/prompt-kit/index.html",
            "docs/prompt-kit*.js",
            "registry/prompts/",
            "Open-Latest-PromptKit.cmd",
            "Acquire-Latest-PromptKit.cmd",
        ],
        "internal_path_renames_deferred": True,
        "reason": "Avoid breaking launchers, public URLs, storage keys, workflows, and stale/open branch references before dedicated-repository cutover.",
    },
}
write_json("harness/contracts/operant-product-identity.v1.json", identity)

# 3. User-visible product brand: preserve internal filenames/keys, retire v40 as the visible product identity.
replace_once("build_prompt_kit.py", "<title>AI Harness Prompt Kit v40</title>", "<title>Operant 0.1</title>")
replace_once(
    "build_prompt_kit.py",
    "AI Harness Prompt Kit <span>v40</span></h1>'\n                '<div style=\"font-size:10px;color:var(--text-muted)\">Agent Control Panel</div>",
    "Operant <span>0.1</span></h1>'\n                '<div style=\"font-size:10px;color:var(--text-muted)\">Capabilities · Skills · Implementations · Evidence</div>",
)
replace_once("build_prompt_kit.py", 'id=\"versionBadge\">v40</div>', 'id=\"versionBadge\">0.1</div>')

old_version_test = '''    def test_visible_version_is_consistently_v40(self) -> None:\n        html = build_prompt_kit_registry.render()\n        self.assertIn('<title>AI Harness Prompt Kit v40</title>', html)\n        self.assertIn('AI Harness Prompt Kit <span>v40</span>', html)\n        self.assertIn('id=\\\"versionBadge\\\">v40</div>', html)\n        self.assertNotIn('AI Harness Prompt Kit <span>v39</span>', html)\n'''
new_version_test = '''    def test_visible_product_identity_is_operant(self) -> None:\n        html = build_prompt_kit_registry.render()\n        self.assertIn('<title>Operant 0.1</title>', html)\n        self.assertIn('Operant <span>0.1</span>', html)\n        self.assertIn('Capabilities · Skills · Implementations · Evidence', html)\n        self.assertIn('id=\\\"versionBadge\\\">0.1</div>', html)\n        self.assertNotIn('AI Harness Prompt Kit <span>v40</span>', html)\n'''
replace_once("tests/test_prompt_kit_order_navigation_product.py", old_version_test, new_version_test)

replace_once(
    "PROMPT_KIT_ACCESS.md",
    "# Get the Latest Prompt Kit Website\n",
    "# Get Operant\n\n> **Transition:** Operant is the current product identity. Existing `Prompt Kit`, `prompt-kit`, and `PromptKit` names below are compatibility paths and launcher/storage identifiers until the dedicated `UnderDeskDev/Operant` cutover is proven.\n",
)
replace_once(
    "PROMPT_KIT_ACCESS.md",
    "Tap/click the **AI Harness Prompt Kit** title",
    "Tap/click the **Operant** title",
)

# 4. Register the existing safe local hook implementation as a capability instead of inventing another hook framework.
skill_path = ".ai/skills/repository-hook-integration/SKILL.md"
skill_text = """# Repository Hook Integration\n\n## Trigger\n\nUse when a repository needs its tracked pre-commit/pre-push hooks activated, verified, repaired, or reconciled with an existing local Git hook authority. Use current provider-specific hook documentation as donor evidence when Claude, Codex, DeepSeek Harness, Husky, Lefthook, or another adapter is involved; do not assume dialect compatibility.\n\n## Required inputs\n\n- Current repository root, branch/worktree state, and `AGENTS.md`.\n- Existing `.githooks/`, `scripts/install_local_hooks.py`, and local/default Git hook configuration.\n- Requested hook purpose and any existing provider-specific hook owner.\n- Owned/forbidden scope and proof requirement.\n\n## Outputs\n\n- Preserved or activated canonical repository hook authority.\n- Exact activation/check command and result.\n- Explicit coexistence blocker when another hook path or linked worktree makes mutation unsafe.\n- Provider-adapter disposition: reuse, bridge, defer, or reject; never silent replacement.\n\n## Procedure\n\n1. Refresh repository truth and inspect tracked hook ownership before installing anything.\n2. Prefer the repository's existing `.githooks` + `scripts/install_local_hooks.py` owner. Do not add Husky/Lefthook/provider hooks merely because upstream examples use them.\n3. Inspect `core.hooksPath`, default Git hooks, linked worktrees, and tracked executable modes. Preserve competing or ambiguous hook setups.\n4. If the existing owner can satisfy the request, activate it with `python scripts/install_local_hooks.py`; use `--check` for read-only verification.\n5. Add a provider-specific adapter only when the request requires semantics the canonical Git hooks cannot express. Keep that adapter behind the same capability boundary and prove its own activation independently.\n6. Run focused activation regressions, harness validation, and patch hygiene before integration.\n\n## Guardrails\n\n- Never change global Git hook configuration.\n- Never overwrite a different local `core.hooksPath` without explicit reviewed replacement intent.\n- Never bypass existing default hooks silently.\n- Refuse shared `core.hooksPath` mutation when linked worktrees make the effect ambiguous.\n- A Claude/Codex/DeepSeek hook example is donor procedure, not repository authority.\n- Hook activation proves interception wiring, not the correctness of every command executed by the hook.\n\n## Validation\n\n```bash\npython -m unittest tests.test_repository_hook_integration tests.test_local_hook_activation -v\npython scripts/install_local_hooks.py --check\npython scripts/validate_harness.py --report Outputs/harness-completeness-report.json\ngit diff --check\n```\n\nThe `--check` command requires a real single-worktree checkout whose local `core.hooksPath` has already been activated; CI may instead use the existing local-hook activation workflow to install and verify in its disposable checkout.\n\n## Proof ceiling\n\nRepository/static tests plus an executed installer/check prove tracked Git hook presence and local `core.hooksPath` activation in the observed checkout. They do not prove Claude/Codex/DeepSeek provider hook behavior, every developer workstation, or future hook command correctness unless those surfaces are separately exercised.\n"""
skill_file = ROOT / skill_path
skill_file.parent.mkdir(parents=True, exist_ok=True)
skill_file.write_text(skill_text, encoding="utf-8")

caps = load_json("harness/capabilities.v1.json")
if not any(item.get("id") == "repository-hook-integration" for item in caps["capabilities"]):
    caps["capabilities"].append({
        "id": "repository-hook-integration",
        "version": "1.0.0",
        "status": "canonical",
        "skill": skill_path,
        "trigger_ids": ["repository-hook-installation-needed"],
        "operation": "Discover the existing repository hook authority, preserve incompatible hook setups, activate the tracked Git hook path, and prove activation without creating a competing hook framework.",
        "inputs": [
            "repository Git/worktree state",
            ".githooks/",
            "scripts/install_local_hooks.py",
            "existing core.hooksPath and default hooks",
            "provider-specific hook context when required"
        ],
        "outputs": [
            "preserved or configured hook authority",
            "activation/check evidence",
            "coexistence or worktree blocker when unsafe",
            "provider-adapter disposition"
        ],
        "implementation": {"kind": "script", "path": "scripts/install_local_hooks.py"},
        "proof_ceiling": "Tracked Git hook and observed local core.hooksPath activation proof only; provider-specific Claude/Codex/DeepSeek hooks and other workstations require separate runtime proof."
    })
write_json("harness/capabilities.v1.json", caps)

triggers = load_json("harness/triggers.v1.json")
if not any(item.get("id") == "repository-hook-installation-needed" for item in triggers["triggers"]):
    triggers["triggers"].append({
        "id": "repository-hook-installation-needed",
        "capability_id": "repository-hook-integration",
        "skill": skill_path,
        "workflow": "WORKFLOW.md#c-harness-infrastructure-change",
        "conditions": [
            "tracked repository hooks exist but are not activated or verified",
            "pre-commit or pre-push enforcement needs installation",
            "existing Git hook ownership must be reconciled before adding an agent/provider hook",
            "a Claude, Codex, DeepSeek Harness, Husky, Lefthook, or other hook donor must be adapted without replacing repository authority"
        ],
        "forbidden_conditions": [
            "global Git hook configuration would be changed",
            "linked worktrees make shared core.hooksPath mutation ambiguous",
            "an existing different hooksPath or default hook would be overwritten without reviewed replacement intent",
            "provider-specific hook behavior is being claimed without its own runtime proof"
        ]
    })
write_json("harness/triggers.v1.json", triggers)

manifest = load_json("harness/manifest.v1.json")
if skill_path not in manifest["skills"]:
    manifest["skills"].append(skill_path)
manifest["domain_contracts"]["operant_product_identity"] = {
    "contract": "harness/contracts/operant-product-identity.v1.json",
    "contract_tests": "tests/test_operant_product_identity.py",
    "workflow": "WORKFLOW.md#c-harness-infrastructure-change",
    "harness_gate": "python -m unittest tests.test_operant_product_identity -v"
}
write_json("harness/manifest.v1.json", manifest)

# Keep fail-closed registry counts aligned.
validator = (ROOT / "scripts/validate_harness.py").read_text(encoding="utf-8")
old_caps = '''REQUIRED_CAPABILITY_IDS = {\n    "harness-infrastructure-maintenance",\n    "prompt-language-audit",\n    "skill-evaluation",\n    "skill-factoring",\n    "technician-prompt-kit-acquisition",\n    "prompt-kit-browser-proof-scratch-cleanup",\n    "prompt-kit-responsive-layout",\n    "prompt-kit-feedback-afk-routing",\n}\n'''
new_caps = old_caps.replace('    "prompt-kit-feedback-afk-routing",\n', '    "prompt-kit-feedback-afk-routing",\n    "repository-hook-integration",\n')
if validator.count(old_caps) != 1:
    raise SystemExit("validate_harness capability block drifted")
validator = validator.replace(old_caps, new_caps, 1)
old_triggers = '''REQUIRED_TRIGGER_IDS = {\n    "harness-infrastructure-change",\n    "prompt-language-change",\n    "lazy-next-action-report",\n    "skill-quality-unproven",\n    "skill-boundary-defect",\n    "technician-needs-latest-prompt-kit",\n    "prompt-kit-browser-proof-temp-path",\n    "prompt-kit-responsive-overlap",\n    "prompt-kit-actionable-feedback",\n}\n'''
new_triggers = old_triggers.replace('    "prompt-kit-actionable-feedback",\n', '    "prompt-kit-actionable-feedback",\n    "repository-hook-installation-needed",\n')
if validator.count(old_triggers) != 1:
    raise SystemExit("validate_harness trigger block drifted")
validator = validator.replace(old_triggers, new_triggers, 1)
(ROOT / "scripts/validate_harness.py").write_text(validator, encoding="utf-8")

# Human indexes remain projections of the machine registries.
replace_once(
    "SKILLS.md",
    "| Harness infrastructure maintenance | harness maps/contracts/workflows/skills drift or context architecture | `.ai/skills/harness-infrastructure-maintenance/SKILL.md` |\n",
    "| Harness infrastructure maintenance | harness maps/contracts/workflows/skills drift or context architecture | `.ai/skills/harness-infrastructure-maintenance/SKILL.md` |\n| Repository hook integration | tracked Git hooks need safe activation, coexistence review, or provider-adapter factoring | `.ai/skills/repository-hook-integration/SKILL.md` |\n",
)
replace_once(
    "SKILLS.md",
    "- structure/ownership/context bloat → Harness infrastructure maintenance;\n",
    "- structure/ownership/context bloat → Harness infrastructure maintenance;\n- tracked hook activation/coexistence/provider adaptation → Repository hook integration;\n",
)
replace_once(
    "CAPABILITIES.md",
    "| `harness-infrastructure-maintenance` | `.ai/skills/harness-infrastructure-maintenance/SKILL.md` | `scripts/validate_harness.py` | Canonical harness repairs plus `harness-completeness-report/v1`. |\n",
    "| `harness-infrastructure-maintenance` | `.ai/skills/harness-infrastructure-maintenance/SKILL.md` | `scripts/validate_harness.py` | Canonical harness repairs plus `harness-completeness-report/v1`. |\n| `repository-hook-integration` | `.ai/skills/repository-hook-integration/SKILL.md` | `scripts/install_local_hooks.py` | Preserved or activated tracked hook authority plus activation/coexistence evidence. |\n",
)
replace_once(
    "CAPABILITIES.md",
    "## Prompt Kit acquisition capability\n",
    "## Repository hook integration capability\n\n`repository-hook-integration` makes the existing `.githooks` + local `core.hooksPath` installer the canonical Git-hook implementation. Upstream Claude/Codex/DeepSeek/Husky/Lefthook mechanisms are adapter donors, not parallel authorities; add an adapter only when the canonical Git hooks cannot express the required interception semantics, and prove that adapter separately.\n\nFocused implementation proof remains `tests/test_local_hook_activation.py` plus `.github/workflows/local-hook-activation.yml`.\n\n## Prompt Kit acquisition capability\n",
)
replace_once(
    "TRIGGERS.md",
    "| `harness-infrastructure-change` | Maps, workflow/artifact/validator registries, completeness checks, hooks, skills, reports, or ownership are missing, stale, disconnected, or failing. | `harness-infrastructure-maintenance` | The task changes `AGENTS.md`, implements product behavior only, requires secrets, or requests destructive cleanup. |\n",
    "| `harness-infrastructure-change` | Maps, workflow/artifact/validator registries, completeness checks, hooks, skills, reports, or ownership are missing, stale, disconnected, or failing. | `harness-infrastructure-maintenance` | The task changes `AGENTS.md`, implements product behavior only, requires secrets, or requests destructive cleanup. |\n| `repository-hook-installation-needed` | Tracked hooks need activation/verification, or an external agent/provider hook must be reconciled with repository hook ownership. | `repository-hook-integration` | Global Git config, ambiguous linked-worktree mutation, silent replacement of another hook owner, or unproved provider-hook behavior would result. |\n",
)
replace_once(
    "TRIGGERS.md",
    "## Prompt Kit acquisition routing rule\n",
    "## Repository hook integration routing rule\n\nRoute hook-install requests to the tracked `.githooks` owner first. Existing `core.hooksPath`, default hooks, and linked worktrees are preconditions, not cleanup targets. Claude/Codex/DeepSeek/Husky/Lefthook examples may inform an adapter, but they do not supersede repository ownership merely because they are installed or popular.\n\n## Prompt Kit acquisition routing rule\n",
)

# 5. Focused regression contracts.
operant_test = '''from __future__ import annotations\n\nimport json\nimport sys\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nSCRIPTS = ROOT / "scripts"\nif str(SCRIPTS) not in sys.path:\n    sys.path.insert(0, str(SCRIPTS))\n\nimport build_prompt_kit_registry\n\n\nclass OperantProductIdentityTests(unittest.TestCase):\n    def test_identity_contract_preserves_transition_boundary(self) -> None:\n        payload = json.loads((ROOT / "harness/contracts/operant-product-identity.v1.json").read_text(encoding="utf-8"))\n        self.assertEqual(payload["schema_version"], "operant-product-identity/v1")\n        self.assertEqual(payload["product_name"], "Operant")\n        self.assertEqual(payload["product_version"], "0.1.0")\n        self.assertEqual(payload["authority"]["target_repository"], "UnderDeskDev/Operant")\n        self.assertEqual(payload["authority"]["target_repository_state"], "not-created-or-unproven")\n        self.assertTrue(payload["compatibility"]["internal_path_renames_deferred"])\n        self.assertIn("web/prompt-kit/index.html", payload["compatibility"]["preserve_paths"])\n        self.assertIn("Prompt Kit", payload["legacy_identity"]["names"])\n\n    def test_visible_brand_is_operant_without_renaming_compatibility_paths(self) -> None:\n        html = build_prompt_kit_registry.render()\n        self.assertIn("<title>Operant 0.1</title>", html)\n        self.assertIn("Operant <span>0.1</span>", html)\n        self.assertIn("Capabilities · Skills · Implementations · Evidence", html)\n        self.assertNotIn("<title>AI Harness Prompt Kit v40</title>", html)\n        self.assertTrue((ROOT / "web/prompt-kit").is_dir())\n\n    def test_governance_and_access_surface_name_operant(self) -> None:\n        governance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")\n        access = (ROOT / "PROMPT_KIT_ACCESS.md").read_text(encoding="utf-8")\n        self.assertIn("**Operant** is the operator-approved product identity", governance)\n        self.assertIn("`UnderDeskDev/Operant`", governance)\n        self.assertIn("legacy `prompt-kit` paths", governance)\n        self.assertTrue(access.startswith("# Get Operant"))\n        self.assertIn("compatibility paths", access)\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
(ROOT / "tests/test_operant_product_identity.py").write_text(operant_test, encoding="utf-8")

hook_test = '''from __future__ import annotations\n\nimport json\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass RepositoryHookIntegrationTests(unittest.TestCase):\n    def load(self, path: str) -> dict:\n        return json.loads((ROOT / path).read_text(encoding="utf-8"))\n\n    def test_capability_trigger_skill_and_implementation_are_connected(self) -> None:\n        capabilities = self.load("harness/capabilities.v1.json")["capabilities"]\n        triggers = self.load("harness/triggers.v1.json")["triggers"]\n        manifest = self.load("harness/manifest.v1.json")\n        capability = next(item for item in capabilities if item["id"] == "repository-hook-integration")\n        trigger = next(item for item in triggers if item["id"] == "repository-hook-installation-needed")\n        self.assertEqual(capability["implementation"], {"kind": "script", "path": "scripts/install_local_hooks.py"})\n        self.assertEqual(trigger["capability_id"], capability["id"])\n        self.assertEqual(trigger["skill"], capability["skill"])\n        self.assertIn(trigger["id"], capability["trigger_ids"])\n        self.assertIn(capability["skill"], manifest["skills"])\n\n    def test_existing_installer_remains_preservation_first(self) -> None:\n        source = (ROOT / "scripts/install_local_hooks.py").read_text(encoding="utf-8")\n        for marker in (\n            "require_single_worktree",\n            "existing_default_hooks",\n            "core.hooksPath",\n            "--replace",\n            "No global hook setting is changed",\n        ):\n            self.assertIn(marker, source)\n        self.assertTrue((ROOT / ".githooks/pre-commit").is_file())\n        self.assertTrue((ROOT / ".githooks/pre-push").is_file())\n\n    def test_skill_requires_provider_adapters_to_remain_subordinate(self) -> None:\n        text = (ROOT / ".ai/skills/repository-hook-integration/SKILL.md").read_text(encoding="utf-8")\n        for marker in (\n            "Claude",\n            "Codex",\n            "DeepSeek Harness",\n            "adapter",\n            "do not assume dialect compatibility",\n            "Never change global Git hook configuration",\n        ):\n            self.assertIn(marker, text)\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
(ROOT / "tests/test_repository_hook_integration.py").write_text(hook_test, encoding="utf-8")

# AGENTS remains under the tracked progressive-disclosure budget.
length = len((ROOT / "AGENTS.md").read_text(encoding="utf-8"))
if length > 5200:
    raise SystemExit(f"AGENTS.md exceeds 5200-character budget: {length}")

print("Operant identity + repository hook capability mutation complete")
