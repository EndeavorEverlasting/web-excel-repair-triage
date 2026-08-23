from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
GUIDED_JS = ROOT / "docs" / "prompt-kit-guided-recommendations.js"
JOURNEY_JS = ROOT / "docs" / "prompt-kit-journey.js"
POLISH_JS = ROOT / "docs" / "prompt-kit-polish.js"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-discovery.v1.json"
DISPLAY_ORDER = ROOT / "registry" / "prompts" / "prompt-display-order.v1.json"
TUTORIAL_PROMPTS = ROOT / "registry" / "prompts" / "tutorial-discovery-prompts.v1.json"
ACCESS_GUIDE = ROOT / "PROMPT_KIT_ACCESS.md"
README = ROOT / "README.md"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
PUBLIC_PROMPT_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
PUBLIC_LAUNCHER_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/"
DIRECT_ZIP_URL = "https://github.com/EndeavorEverlasting/web-excel-repair-triage/archive/refs/heads/main.zip"
DIRECT_CMD_URL = "https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/Open-Latest-PromptKit.cmd"
CLONE_COMMAND = "git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git"


class PromptKitDiscoveryTests(unittest.TestCase):
    def test_contract_covers_field_regressions(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "prompt-kit-discovery-contract/v1")
        self.assertEqual(
            {item["id"] for item in payload["requirements"]},
            {
                "section_heading_contrast",
                "ranked_search",
                "synonym_routing",
                "body_noise_suppression",
                "local_favorites",
                "favorites_first",
                "favorite_accessibility",
                "guided_questionnaire",
                "guided_uses_shared_search",
                "metadata_recommendations",
                "guided_next_step_journey",
                "guided_completion_state",
                "tutorial_beacon",
                "card_action_rail",
                "clipboard_confirmation",
                "stable_identity_resequence",
                "registry_prompt_fallback",
                "distribution_front_door",
                "generated_site_parity",
            },
        )
        expected = {item["id"]: item["expected"] for item in payload["requirements"]}
        self.assertIn("explicit local filter", expected["favorites_first"])
        self.assertIn("canonical library defaults to ascending numeric sequence", expected["stable_identity_resequence"])

    def test_section_button_has_explicit_dark_surface_contrast(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn(".section-divider .section-toggle{color:var(--text-primary)", js)
        self.assertIn(".section-divider .section-toggle .sd-count{color:var(--text-secondary)}", js)

    def test_ranked_search_uses_synonyms_without_copy_body_flood(self) -> None:
        js = JS.read_text(encoding="utf-8")
        start = js.index("function normalizeSearchText")
        end = js.index("function promptSequenceValue")
        helpers = js[start:end]
        script = (
            "var SYNONYMS={artifact:'P56',closeout:'P12',handoff:'P12'};\n"
            "function promptSequenceValue(p){var n=parseInt(String(p.seq||0),10);return isNaN(n)?999999:n}\n"
            + helpers
            + r'''
var prompts=[
 {id:'P56',seq:'56',name:'Context to Artifact Builder',type:'BUILD + ARTIFACT',class:'standard',useWhen:'Generate the actual artifact from supplied context',sprintRole:'implementor',proofGate:'artifact proof',copyContent:'build the file',keywords:['artifact','generate']},
 {id:'P07',seq:'7',name:'Sprint Executor',type:'BUILD',class:'standard',useWhen:'Execute repository work',sprintRole:'implementor',proofGate:'commit proof',copyContent:'report expected artifacts and artifact registry',keywords:['sprint']},
 {id:'P12',seq:'12',name:'Final Handoff Compressor',type:'CLOSEOUT',class:'standard',useWhen:'Close out completed work cleanly',sprintRole:'closer',proofGate:'handoff proof',copyContent:'compress the final state',keywords:['handoff']},
 {id:'P20',seq:'20',name:'Opportunity Builder',type:'OPPORTUNITY',class:'standard',useWhen:'Turn opportunity into work',sprintRole:'planner',proofGate:'plan proof',copyContent:'the final response names artifact paths',keywords:['opportunity']}
];
var artifact=filterPromptsForQuery(prompts,'artifact').map(function(p){return p.id});
var close=filterPromptsForQuery(prompts,'close').map(function(p){return p.id});
process.stdout.write(JSON.stringify({artifact:artifact,close:close}));
'''
        )
        completed = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        result = json.loads(completed.stdout)
        self.assertEqual(result["artifact"][0], "P56")
        self.assertNotIn("P07", result["artifact"], "copyContent-only artifact noise must be suppressed")
        self.assertNotIn("P20", result["artifact"], "copyContent-only artifact noise must be suppressed")
        self.assertIn("P12", result["close"], "partial close must resolve closeout synonym and metadata")

    def test_favorites_persist_as_explicit_filter_without_reordering_default(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for marker in (
            "promptKit.favoritePromptIds.v1",
            "window.localStorage.getItem(FAVORITES_STORAGE_KEY)",
            "window.localStorage.setItem(FAVORITES_STORAGE_KEY",
            "favBtn.className='prompt-favorite-btn'",
            "favBtn.setAttribute('aria-pressed'",
            "data-section=\"__favorites__\"",
            "activeSection==='__favorites__'",
        ):
            self.assertIn(marker, js)
        self.assertNotIn("name:'Favorites',glow:'#fbbf24'", js)
        start = js.index("function promptSequenceValue")
        end = js.index("function renderSections")
        helpers = js[start:end]
        script = r'''
var SECTIONS=[
 {name:'Foundation',types:['SETUP'],glow:'#64748b'},
 {name:'Build & Repair',types:['BUILD'],glow:'#22c55e'}
];
''' + helpers + r'''
var groups=groupPromptsBySection([
 {id:'P10',seq:'10',type:'BUILD'},
 {id:'P02',seq:'2',type:'SETUP'},
 {id:'P03',seq:'3',type:'BUILD'}
]);
process.stdout.write(JSON.stringify(groups.map(function(g){return {name:g.name,ids:g.prompts.map(function(p){return p.id})}})));
'''
        completed = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        groups = json.loads(completed.stdout)
        flattened = [prompt_id for group in groups for prompt_id in group["ids"]]
        self.assertEqual(flattened, ["P02", "P03", "P10"])

    def test_guided_questionnaire_uses_shared_search_and_no_prompt_id_router(self) -> None:
        guided = GUIDED_JS.read_text(encoding="utf-8")
        for marker in (
            "id:'startingPoint'",
            "I do not have the repository checked out yet",
            "I have a repository but it is unfamiliar",
            "id:'intent'",
            "What is your job to be done?",
            "id:'stage'",
            "id:'discriminator'",
            "filterPromptsForQuery(PROMPTS,query)",
            "(allPrompts||PROMPTS).find",
            "slice(0,3)",
            "copyPrompt(",
            "showPromptDetail(",
            "promptFinderBtn",
            "actions.appendChild(addButton)",
        ):
            self.assertIn(marker, guided)
        self.assertNotIn("var R=", guided)
        self.assertNotIn("replaceChild(button,old)", guided)
        question_ids = ("startingPoint", "intent", "stage", "discriminator")
        self.assertEqual(sum(guided.count(f"id:'{item}'") for item in question_ids), 4)
        self.assertLessEqual(len(question_ids), 5)

    def test_guided_journey_uses_registry_next_step_and_session_state(self) -> None:
        journey = JOURNEY_JS.read_text(encoding="utf-8")
        for marker in (
            "promptKit.guidance.completed.v1",
            "function guidanceNextIds(prompt)",
            "prompt.nextStep",
            "buildPromptGuidanceModel",
            "NEXT-STEP CONTRACT",
            "READY TO CONTINUE WHEN",
            "Mark this step complete",
            "sessionStorage",
            "stableGuidanceOrigin",
            "closest('#promptDetail')",
            "finder-journey-preview",
            "prefers-reduced-motion:reduce",
        ):
            self.assertIn(marker, journey)
        self.assertNotIn("NEXT_PROMPT_MAP", journey)
        self.assertNotIn("localStorage", journey)
        self.assertNotIn("MAX_NEXT", journey)

    def test_tutorial_entry_point_is_visible_glowing_and_reduced_motion_safe(self) -> None:
        guided = GUIDED_JS.read_text(encoding="utf-8")
        for marker in (
            "✦ Tutorial · Find My Prompt",
            ".finder-prompt-btn",
            "animation:prompt-finder-beacon 2.4s ease-in-out infinite",
            "@keyframes prompt-finder-beacon",
            "@media(prefers-reduced-motion:reduce)",
        ):
            self.assertIn(marker, guided)

    def test_prompt_actions_share_one_non_overlapping_rail(self) -> None:
        polish = POLISH_JS.read_text(encoding="utf-8")
        for marker in (
            ".prompt-card-actions{position:absolute;top:12px;right:12px",
            ".prompt-card .prompt-header{padding-right:176px",
            "actions.className='prompt-card-actions'",
            "actions.appendChild(favBtn)",
            "actions.appendChild(openBtn)",
            "actions.appendChild(copyBtn)",
            "grid-template-columns:44px minmax(72px,1fr) minmax(72px,1fr)",
            ".prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{position:static!important",
        ):
            self.assertIn(marker, polish)
        self.assertNotIn("card.querySelector('.prompt-header').appendChild(favBtn)", polish)

    def test_successful_copy_has_green_glowing_confirmation(self) -> None:
        polish = POLISH_JS.read_text(encoding="utf-8")
        for marker in (
            "showCopyConfirmation",
            "✓ Copied to clipboard",
            ".toast.success",
            "var(--success)",
            "prompt-copy-confirm",
            "copy-confirmed",
            "@media(prefers-reduced-motion:reduce)",
        ):
            self.assertIn(marker, polish)

    def test_display_order_keeps_recommendation_priority_metadata_without_changing_ids(self) -> None:
        payload = json.loads(DISPLAY_ORDER.read_text(encoding="utf-8"))
        promoted = payload["promoted_prompt_ids"]
        self.assertEqual(payload["schema_version"], "prompt-display-order/v1")
        self.assertEqual(payload["fallback"], "sequence_ascending")
        self.assertEqual(promoted[0], "P65")
        self.assertEqual(len(promoted), len(set(promoted)))
        self.assertLess(promoted.index("P61"), promoted.index("P64"))

    def test_tutorial_registry_contains_portfolio_and_conversational_fallback(self) -> None:
        payload = json.loads(TUTORIAL_PROMPTS.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in payload["prompts"]}
        self.assertEqual(payload["schema_version"], "prompt-registry-extension/v1")
        self.assertEqual(set(by_id), {"P64", "P65", "P96", "P98"})
        self.assertIn("RANK TUTORIAL PATHS WORTH SPRINTING", by_id["P64"]["copyContent"])
        self.assertIn("one concise question at a time", by_id["P65"]["copyContent"])
        self.assertIn("Do not invent prompt IDs", by_id["P65"]["copyContent"])
        self.assertEqual(by_id["P96"]["name"], "Stateful Socratic Technical Tutor Workspace")
        self.assertIn("active retrieval", by_id["P96"]["copyContent"].lower())
        self.assertEqual(by_id["P98"]["name"], "Teach Workspace Protocol Bootstrapper")

    def test_repo_front_door_exposes_browser_phone_zip_cmd_and_clone(self) -> None:
        readme = README.read_text(encoding="utf-8")
        access = ACCESS_GUIDE.read_text(encoding="utf-8")
        for marker in (
            PUBLIC_PROMPT_URL,
            PUBLIC_LAUNCHER_URL,
            DIRECT_ZIP_URL,
            DIRECT_CMD_URL,
            CLONE_COMMAND,
        ):
            self.assertIn(marker, readme)
            self.assertIn(marker, access)
        self.assertIn("<!-- PROMPT_KIT_QUICK_ACCESS_START -->", readme)
        self.assertIn("<!-- PROMPT_KIT_QUICK_ACCESS_END -->", readme)

    def test_generated_site_contains_exact_behavior_sources(self) -> None:
        js = JS.read_text(encoding="utf-8")
        guided = GUIDED_JS.read_text(encoding="utf-8")
        journey = JOURNEY_JS.read_text(encoding="utf-8")
        polish = POLISH_JS.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn(js, deployed)
        self.assertIn(guided, deployed)
        self.assertIn(journey, deployed)
        self.assertIn(polish, deployed)
        self.assertIn('"id": "P64"', deployed)
        self.assertIn('"id": "P65"', deployed)
        self.assertIn("✦ Tutorial · Find My Prompt", deployed)
        self.assertIn("prompt-kit-journey-styles", deployed)
        self.assertIn("prompt-card-actions", deployed)

    def test_tutorial_presents_one_find_use_prove_continue_experience(self) -> None:
        guided = GUIDED_JS.read_text(encoding="utf-8")
        journey = JOURNEY_JS.read_text(encoding="utf-8")
        # The questionnaire results frame the path as one four-phase experience.
        for marker in (
            "Find → Use → Prove → Continue",
            "phaseRailHtml",
            "primaryPhaseBody",
            "finder-phase-rail",
            "finder-phase-block",
            "Phase 1 · Found",
            "Phase 2 · Use",
            "Phase 3 · Prove",
            "Phase 4 · Continue",
        ):
            self.assertIn(marker, guided)
        # The prompt-detail journey panel carries the same four-phase rail and
        # marks Find as complete (activePhase=1) so the user sees continuity.
        for marker in (
            "guidePhaseRailHtml",
            "guide-phase-rail",
            "Find → Use → Prove → Continue",
            "Phase 2 · Use this prompt",
            "PHASE 3 · PROVE",
            "PHASE 4 · CONTINUE",
        ):
            self.assertIn(marker, journey)
        # The finder-results inline phase body must suppress the legacy
        # duplicate preview so the user sees one path, not two.
        self.assertIn("finder-phase-rail", journey)


if __name__ == "__main__":
    unittest.main()
