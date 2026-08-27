from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs" / "prompts.json"
TEST = ROOT / "tests" / "test_context_to_artifact_prompt.py"

prompts = json.loads(PROMPTS.read_text(encoding="utf-8"))
p56 = next((item for item in prompts if item.get("id") == "P56"), None)
if p56 is None:
    raise SystemExit("P56 not found in canonical base registry")

p56.update(
    {
        "sprintRole": "Generate the actual requested artifact from supplied evidence while matching repository/system claims to the capabilities the current agent can actually exercise",
        "useWhen": "The user supplies context, research, requirements, examples, or source files and expects a real artifact or implementation-ready contribution; especially when a target repository/system exists but the current agent may not have access to inspect or mutate it.",
        "inspectFirst": "Provided context, files, research dossier, explicit capability/tool access, and any actually accessible artifact-family or repository authority. If the target repository/system is inaccessible, do not invent its rules, paths, schemas, tests, CI, or runtime state; treat proposed integration as a later repo-capable handoff.",
        "expectedOutput": "The actual requested artifact. When repository access exists, include repository-backed manifests, registry updates, validation, path/hash, and integration proof as applicable. When repository access does not exist, produce complete standalone implementation artifacts plus a capability-bounded integration handoff that labels repository claims as SUPPLIED_CONTEXT, PROPOSED, or UNKNOWN_REQUIRES_REPO_INSPECTION.",
        "nextStep": "If the target repository/system was inaccessible, hand the verified standalone artifact packet to a repo-capable executor to discover canonical owners, adapt the contribution, run repository validators and runtime proof, and integrate through current policy; otherwise field-test or continue through the task-specific implementation/repair/integration owner.",
        "proofGate": "A real requested artifact exists and passes the strongest checks the current environment can actually run. The response states the capability mode and proof ceiling; inaccessible repository/system facts are never presented as inspected, tested, committed, integrated, or runtime-proven, and dossier-only output includes an executable repo-capable handoff.",
        "copyContent": """PROMPT SURFACE: STANDARD AI. THIS IS NOT A GOODNIGHT, HAVE FUN (GNHF) PROMPT.\n\nGENERATE THE ACTUAL ARTIFACT FROM THE PROVIDED EVIDENCE. DO NOT STOP AT AN OUTLINE OR SAMPLE, AND DO NOT PRETEND TO INSPECT OR MUTATE A SYSTEM YOU CANNOT ACCESS.\n\nRepository, system, or artifact family: xyz_target_or_artifact_family\nSource context / verified dossier / files: xyz_context_and_sources\nRequested artifact: xyz_artifact\nOutput format and destination: xyz_format_and_destination\nAcceptance requirements: xyz_acceptance_requirements\n\nCAPABILITY BOUNDARY — CHOOSE ONE MODE BEFORE MAKING TARGET-SPECIFIC CLAIMS\n- REPO_CAPABLE: the current environment actually exposes and verifies the target repository/filesystem plus the tools needed for the requested repository work. Use current repository evidence and repository-owned generators/validators.\n- DOSSIER_ONLY: the target repository/system exists but the current environment cannot inspect or mutate it. Work from supplied evidence and accessible files only. Do not claim repository inspection, branch/PR/CI state, tests, integration, runtime behavior, or canonical paths that were not actually observed.\n- ARTIFACT_ONLY: no repository is required for the requested output. State the bounded source authority, output location, and applicable artifact proof.\nCapability presence is not authority. A repository name in the request does not grant repository access. If a claimed capability is unavailable, downgrade the execution mode instead of fabricating evidence.\n\nSOURCE / CLAIM PROVENANCE\nWhen operating DOSSIER_ONLY, classify every material target-repository/system claim with one of these meanings:\n- SUPPLIED_CONTEXT — explicitly present in the user-provided dossier, files, or quoted evidence.\n- PROPOSED — a design or integration recommendation that a repo-capable executor must verify before adoption.\n- UNKNOWN_REQUIRES_REPO_INSPECTION — cannot be established from the supplied evidence.\nDo not convert remembered conventions, another repository, model preference, or a plausible path/module/schema into SUPPLIED_CONTEXT.\nA verified research dossier may be the authority boundary between gathering and synthesis: consume its pinned decisions and evidence without reflexively redoing research, while keeping later repository/runtime proof separate. Exact grounding or tool-call validation remains owned by P101; hallucination-cause diagnosis remains owned by P100.\n\nARTIFACT EXECUTION CONTRACT\n1. Convert supplied evidence into concrete acceptance criteria and identify which source material is authoritative, advisory, proposed, or unknown.\n2. Generate the actual requested deliverable now. This may be a document, spreadsheet, slide deck, archive, report, schema, manifest, implementation packet, standalone source code, deterministic tests/fixtures, or another concrete artifact family.\n3. REPO_CAPABLE: inspect the real canonical owners before choosing paths or imports; reuse existing templates, generators, contracts, serializers, test patterns, and output conventions rather than inventing competitors.\n4. DOSSIER_ONLY: make the contribution implementation-ready without impersonating repository access. Produce complete standalone code/schemas/tests/examples when requested. Do not use fake imports from hypothetical repository modules. Label suggested destinations `PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY`. Do not return a fake repository patch, fabricated SHA, PR, CI result, or integration claim.\n5. Preserve source truth. Keep normalized/canonical data separate from derived projections when the supplied design requires it; preserve provenance and version identity where practical.\n6. Run every artifact-level check available in the current environment. Inspect the generated artifact itself, not only a generator exit code. Record exact checks that could not run.\n7. Never inflate proof. Local standalone tests prove the standalone artifact at those inputs; they do not prove compatibility with an inaccessible repository, live service, browser/device, production environment, or operator workflow.\n8. Preserve source files and never embed secrets, credentials, private machine data, or unsupported target facts merely to make the artifact look complete.\n\nDOSSIER-ONLY REPOSITORY-CAPABLE HANDOFF\nWhen the artifact is intended for a repository/system the current agent cannot access, end with one self-contained handoff containing:\n- target repository/system identity exactly as supplied;\n- verified dossier/source identities and important accepted/rejected decisions;\n- generated standalone artifacts and hashes/versions when practical;\n- explicit SUPPLIED_CONTEXT / PROPOSED / UNKNOWN_REQUIRES_REPO_INSPECTION ledger;\n- proposed integration seams without claiming they exist;\n- forbidden assumptions and behaviors;\n- first executable repo-capable actions: refresh current truth, read governance, find the existing owner/registry/schema/CLI/test/output/validation seams, strengthen rather than duplicate authority, adapt the standalone contribution, run focused and registered validators, exercise the real required runtime/field path, then integrate through the repository's actual branch/PR/promotion policy;\n- completion gate and proof ceiling.\nDo not make the operator manually translate the packet or restate evidence already included in the dossier.\n\nFINAL RESPONSE\nReport capability mode; source/provenance ledger; actual artifact links or paths; checks actually run and results; target-repository claims by SUPPLIED_CONTEXT / PROPOSED / UNKNOWN_REQUIRES_REPO_INSPECTION when DOSSIER_ONLY; skipped proof; gaps and risks; proof ceiling; and one exact next action. If repository access was unavailable, include the repo-capable handoff rather than pretending integration occurred.""",
        "keywords": [
            "artifact",
            "generate artifact",
            "build artifact",
            "context to artifact",
            "create artifact",
            "output file",
            "implementation ready packet",
            "standalone implementation",
            "dossier only",
            "no repository access",
            "capability bounded",
            "repo capable handoff",
            "supplied context",
            "proposed location",
        ],
    }
)

PROMPTS.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

TEST.write_text(
    r'''from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "prompts.json"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


class ContextToArtifactPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        prompts = json.loads(BASE.read_text(encoding="utf-8"))
        cls.p56 = next(item for item in prompts if item["id"] == "P56")
        cls.content = cls.p56["copyContent"]

    def test_p56_retains_canonical_artifact_identity(self) -> None:
        self.assertEqual(self.p56["name"], "Context-to-Artifact Generator")
        self.assertEqual(self.p56["type"], "BUILD + ARTIFACT")
        self.assertIn("actual requested artifact", self.p56["expectedOutput"].lower())

    def test_p56_has_explicit_capability_modes_and_no_repo_access_failure_boundary(self) -> None:
        for marker in (
            "CAPABILITY BOUNDARY — CHOOSE ONE MODE",
            "REPO_CAPABLE",
            "DOSSIER_ONLY",
            "ARTIFACT_ONLY",
            "A repository name in the request does not grant repository access.",
            "Do not claim repository inspection",
        ):
            self.assertIn(marker, self.content)

    def test_p56_labels_repository_claim_authority_in_dossier_only_mode(self) -> None:
        for marker in (
            "SUPPLIED_CONTEXT",
            "PROPOSED",
            "UNKNOWN_REQUIRES_REPO_INSPECTION",
            "PROPOSED LOCATION — REQUIRES REPO-CAPABLE AGENT TO VERIFY",
        ):
            self.assertIn(marker, self.content)
        self.assertIn("fake repository patch", self.content)
        self.assertIn("fabricated SHA, PR, CI result", self.content)

    def test_p56_requires_real_standalone_artifacts_and_repo_capable_handoff(self) -> None:
        for marker in (
            "complete standalone code/schemas/tests/examples",
            "Do not use fake imports from hypothetical repository modules.",
            "DOSSIER-ONLY REPOSITORY-CAPABLE HANDOFF",
            "strengthen rather than duplicate authority",
            "repository's actual branch/PR/promotion policy",
        ):
            self.assertIn(marker, self.content)

    def test_p56_preserves_proof_ceiling(self) -> None:
        self.assertIn("Never inflate proof", self.content)
        self.assertIn("do not prove compatibility with an inaccessible repository", self.content)
        self.assertIn("proof ceiling", self.p56["proofGate"].lower())

    def test_generated_site_contains_strengthened_p56(self) -> None:
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "CAPABILITY BOUNDARY — CHOOSE ONE MODE",
            "DOSSIER-ONLY REPOSITORY-CAPABLE HANDOFF",
            "UNKNOWN_REQUIRES_REPO_INSPECTION",
        ):
            self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
''',
    encoding="utf-8",
)
