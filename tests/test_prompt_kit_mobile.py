from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-mobile.v1.json"
QUICK_CMD = ROOT / "Open-Latest-PromptKit.cmd"
PORTABLE_PS1 = ROOT / "scripts" / "Open-LatestPromptKitPortable.ps1"
ACQUIRE_CMD = ROOT / "Acquire-Latest-PromptKit.cmd"
ACQUIRE_PS1 = ROOT / "scripts" / "Acquire-LatestPromptKit.ps1"
ACCESS = ROOT / "PROMPT_KIT_ACCESS.md"
WEB_README = ROOT / "web" / "README.md"


class PromptKitMobileTests(unittest.TestCase):
    def test_mobile_contract_has_required_requirements(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "prompt-kit-mobile-contract/v1")
        self.assertEqual(
            {item["id"] for item in payload["requirements"]},
            {
                "title_reset",
                "explicit_mobile_open",
                "touch_copy_preserved",
                "horizontal_filter_rails",
                "single_column_cards",
                "mobile_detail_surface",
                "mobile_reference_surface",
                "distributed_navigation_preserved",
                "quick_windows_acquisition",
            },
        )

    def test_mobile_layout_reuses_existing_surface(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for marker in (
            "function ensureMobileSupport()",
            "@media(max-width:760px)",
            ".header{position:static",
            ".type-nav{padding:8px 0 10px;display:flex;flex-wrap:nowrap;overflow-x:auto",
            ".grid{grid-template-columns:minmax(0,1fr)",
            "height:100dvh;max-height:100dvh",
            ".ref-sidebar{width:100vw;max-width:100vw",
            "touch-action:manipulation",
        ):
            self.assertIn(marker, js)
        self.assertNotIn("mobilePrompt", js)
        self.assertNotIn("mobilePrompts", js)

    def test_title_is_keyboard_and_pointer_reset_control(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for marker in (
            "logo.id='homeReset'",
            "logo.tabIndex=0",
            "logo.setAttribute('role','button')",
            "function resetPromptKitView()",
            "activeCat='all';activeSection=null;activeType=null;activeColor=null",
            "collapsedSections={}",
            "search.value=''",
            "renderSections();renderTypes();render();",
            "homeReset.addEventListener('click',resetPromptKitView)",
            "if(e.key==='Enter'||e.key===' ')",
        ):
            self.assertIn(marker, js)

    def test_mobile_has_explicit_open_copy_and_wide_touch_sizing(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("card.setAttribute('role','group')", js)
        self.assertIn("openBtn.className='prompt-open-btn'", js)
        self.assertIn("openBtn.textContent='Open'", js)
        self.assertIn("showPromptDetail(p.id,card)", js)
        self.assertIn("btn.className='prompt-copy-btn'", js)
        self.assertIn("@media (hover:none), (pointer:coarse)", js)
        self.assertIn(
            ".prompt-open-btn,.prompt-copy-btn{opacity:1;min-width:64px;min-height:40px;padding:8px 12px;touch-action:manipulation}",
            js,
        )

    def test_category_collapse_control_is_touch_sized_and_native(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn('class="sd-label section-toggle"', js)
        self.assertIn('type="button"', js)
        self.assertIn('aria-expanded="', js)
        self.assertIn(
            ".section-divider .section-toggle{min-height:40px;touch-action:manipulation}",
            js,
        )

    def test_prompt_display_fields_are_escaped_before_html_rendering(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("function escapePromptHtml(value)", js)
        for marker in (
            "safeId=escapePromptHtml(p.id)",
            "safeName=escapePromptHtml(p.name)",
            "safeType=escapePromptHtml(p.type)",
            "safeUseWhen=escapePromptHtml(p.useWhen)",
            "safeSprintRole=escapePromptHtml(p.sprintRole)",
            "safeProofGate=escapePromptHtml(p.proofGate)",
        ):
            self.assertIn(marker, js)

    def test_quick_cmd_bootstraps_portable_main_and_propagates_exit(self) -> None:
        quick = QUICK_CMD.read_text(encoding="utf-8")
        portable = PORTABLE_PS1.read_text(encoding="utf-8")
        acquire = ACQUIRE_CMD.read_text(encoding="utf-8")
        self.assertIn(
            "https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/scripts/Open-LatestPromptKitPortable.ps1",
            quick,
        )
        self.assertIn('Open-LatestPromptKitPortable.ps1', quick)
        self.assertIn('-File "%SCRIPT%" -Destination "%PREFERRED_REPO%"', quick)
        self.assertIn("exit /b %EXIT_CODE%", quick)
        self.assertIn("Import-AcquisitionFunctions", portable)
        self.assertIn("Update-RepositorySafely", portable)
        self.assertIn("http://127.0.0.1:8765/", portable)
        self.assertIn('-File "%SCRIPT%" %*', acquire)
        self.assertIn("/main/scripts/Acquire-LatestPromptKit.ps1", acquire)

    def test_quick_acquisition_resolves_desktop_onedrive_and_backup_roots(self) -> None:
        ps1 = ACQUIRE_PS1.read_text(encoding="utf-8")
        for marker in (
            "[Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)",
            "OneDriveCommercial",
            "OneDriveConsumer",
            "OG Laptop Backup\\Desktop\\dev",
            "Get-ExistingPromptKitRepositories",
            "Normalize-RepositoryUrl $origin",
            "Preserving candidate and continuing:",
            "'merge', '--ff-only'",
            "Start-Process -FilePath $site",
        ):
            self.assertIn(marker, ps1)

    def test_universal_paths_do_not_embed_person_specific_usernames(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (QUICK_CMD, PORTABLE_PS1, ACQUIRE_CMD, ACQUIRE_PS1, ACCESS, WEB_README)
        ).lower()
        for forbidden in (
            r"c:\users\cheex",
            r"c:\users\richard",
            "pa_rperez26",
            "rperez26",
        ):
            self.assertNotIn(forbidden, combined)

    def test_access_docs_make_quick_launcher_primary_and_keep_gui_advanced(self) -> None:
        access = ACCESS.read_text(encoding="utf-8")
        readme = WEB_README.read_text(encoding="utf-8")
        self.assertIn("Open-Latest-PromptKit.cmd", access)
        self.assertIn("Acquire-Latest-PromptKit.cmd", access)
        self.assertIn("Open-Latest-PromptKit.cmd", readme)
        self.assertIn("Acquire-Latest-PromptKit.cmd", readme)
        self.assertIn("mobile", (access + readme).lower())
        self.assertIn("reset", (access + readme).lower())
        self.assertIn("collapsible", readme.lower())
        self.assertIn("prompt-kit-favorites/v1", access + readme)
        self.assertIn("http://127.0.0.1:8765/", access + readme)


if __name__ == "__main__":
    unittest.main()
