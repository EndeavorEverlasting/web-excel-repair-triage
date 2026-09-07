from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
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
                "mobile_quick_controls_gesture_parity",
                "favorites_quick_access",
                "favorites_group_jump_navigation",
                "favorites_empty_state_and_persistence",
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

    def test_mobile_favorites_quick_action_is_persistent_and_reuses_canonical_view(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        for marker in (
            "id='mobileFavoritesQuick'",
            "className='mobile-favorites-quick'",
            "setAttribute('data-view','favorites')",
            "setAttribute('aria-label','Open saved favorite prompts')",
            "textContent='★ Favorites'",
            "activateFavoritesView()",
            "if(search)headerTop.insertBefore(mobileFavoritesQuick,search);else headerTop.appendChild(mobileFavoritesQuick)",
            ".mobile-favorites-quick{display:none",
            ".header-top>.mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}",
        ):
            self.assertIn(marker, polish)
        self.assertEqual(polish.count("id='mobileFavoritesQuick'"), 1)
        self.assertNotIn("mobileFavoritePromptIds", polish)
        self.assertNotIn("mobileFavoritesStorage", polish)

    def test_favorites_group_jump_navigation_reuses_rendered_sections(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        for marker in (
            "function renderFavoritesGroupJumpNavigation()",
            "nav.id='favoritesGroupJumpNav'",
            "nav.setAttribute('aria-label','Saved favorite groups')",
            "label.textContent='Saved groups'",
            "grid.querySelectorAll('.section-divider[data-category]')",
            "countNode=divider.querySelector('.sd-count')",
            "link.setAttribute('data-favorite-group',name)",
            "target.scrollIntoView({block:'start',behavior:hotkeyScrollBehavior()})",
            "installFavoritesGroupJumpNavigation()",
            "wrapped=function(){baseRender();renderFavoritesGroupJumpNavigation()}",
            ".favorite-group-jump{",
        ):
            self.assertIn(marker, polish)
        self.assertIn("if(activeSection!=='__favorites__')return", polish)
        self.assertNotIn("favoriteGroupsStorage", polish)
        self.assertNotIn("favoriteCollections", polish)

    def test_favorites_empty_state_reuses_canonical_membership_and_has_two_recovery_paths(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        for marker in (
            "function renderFavoritesEmptyState(grid)",
            "storedFavoritePromptCount()",
            "currentFavoritePromptCount()",
            "catalog.filter(function(prompt){return prompt&&isFavoritePrompt(prompt.id)}).length",
            "state.id='favoritesEmptyState'",
            "state.setAttribute('data-empty-kind','none-saved')",
            "title.textContent='No Favorites yet'",
            "action.textContent='Browse all prompts'",
            "action.setAttribute('aria-label','Browse all prompts')",
            "state.setAttribute('data-empty-kind','unavailable')",
            "title.textContent='Saved Favorites unavailable in this version'",
            "action.textContent='Browse current prompts'",
            "action.setAttribute('aria-label','Browse current prompts')",
            "activateAllPromptsView()",
            "state.setAttribute('data-empty-kind','filtered')",
            "title.textContent='No Favorites match these filters'",
            "action.textContent='Clear Favorites filters'",
            "action.setAttribute('aria-label','Clear Favorites filters')",
            "clearTransientPromptFilters();renderTypes();render()",
            "if(!dividers.length){renderFavoritesEmptyState(grid);return}",
            "ensureFavoritesJourneyStyles();",
        ):
            self.assertIn(marker, polish)
        self.assertIn("favoritePromptIds", polish)
        self.assertNotIn("favoritesEmptyStorage", polish)
        self.assertNotIn("favoritesSessionStorage", polish)

    def test_mobile_favorites_definitive_journey_is_linear_and_complete(self) -> None:
        proof = (ROOT / "tests" / "prompt_kit_favorite_browser_proof.py").read_text(encoding="utf-8")
        for marker in (
            "mobile_favorites_definitive_journey",
            "promptKit.favoritePromptIds.v1",
            "saved_in_canonical_key",
            "persisted_after_reload",
            "favorites_appear_after_reload",
            "JSON.stringify(['P79','P999999'])",
            "unknown_id_preserved_before_mutation",
            "unknown_id_preserved_after_mutation",
            "membership_unchanged_after_clear",
            "get_by_role(\"button\", name=\"Browse all prompts\")",
            "get_by_role(\"button\", name=\"Clear Favorites filters\")",
            "get_by_role(\"button\", name=\"Browse current prompts\")",
            "browse_current.click()",
            "Saved Favorites unavailable in this version",
            "recovery_controls_tappable",
            "subject = prepare_exact_head_subject()",
            "canonical_clipboard_text(actual)",
            "canonical_clipboard_text(after_enter)",
        ):
            self.assertIn(marker, proof)
        self.assertLess(
            proof.index("saved_in_canonical_key = all"),
            proof.index("mobile_page.reload(wait_until=\"domcontentloaded\")"),
        )
        self.assertLess(
            proof.index('name="Browse all prompts"'),
            proof.index("definitely-no-favorite-match-xyz"),
        )
        self.assertLess(
            proof.index("definitely-no-favorite-match-xyz"),
            proof.index("JSON.stringify(['P79','P999999'])"),
        )
        self.assertLess(
            proof.index("JSON.stringify(['P79','P999999'])"),
            proof.index("unknown_id_preserved_after_mutation = \"P999999\" in stored_after_mutation"),
        )
        self.assertLess(
            proof.index("unknown_id_preserved_after_mutation = \"P999999\" in stored_after_mutation"),
            proof.index("browse_current.click()"),
        )
        self.assertNotIn("mobile_favorites_persistence_and_empty_state", proof)
        self.assertNotIn("mobile_favorites_quick_access", proof)
        self.assertNotIn("mobile_favorites_group_jump_navigation", proof)
        self.assertNotIn("unknown_favorite_portability_recovery", proof)

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
        for marker in (
            "BOOTSTRAP_COMMIT=2e8795f1136d2737461c0770127728496eaa4edc",
            "BOOTSTRAP_BLOB=eee14a8da3a96dc3ca6e671e65b4b87255718500",
            "api.github.com/repos/EndeavorEverlasting/web-excel-repair-triage/contents/scripts/Open-LatestPromptKitPortable.ps1",
            'Open-LatestPromptKitPortable.ps1',
            '-File "%SCRIPT%" -Destination "%PREFERRED_REPO%"',
            '"%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"',
            "exit /b %EXIT_CODE%",
        ):
            self.assertIn(marker, quick)
        self.assertNotIn(
            "raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/scripts/Open-LatestPromptKitPortable.ps1",
            quick,
        )
        self.assertNotIn(r"%~dp0dev\web-excel-repair-triage", quick)
        for marker in (
            "$AcquireBootstrapCommit = 'b91b2c8c925cbd3f702cab13e36edba5483f9b8a'",
            "$AcquireBootstrapBlob = '9d5e428adeacc8cdde9f1e850b40785cb85e9137'",
            "$StableHost = '127.0.0.1'",
            '$StableUrl = "http://${StableHost}:$Port/"',
            "Import-AcquisitionFunctions",
            "Update-RepositorySafely",
            "no '-latest' sibling clone was created",
        ):
            self.assertIn(marker, portable)
        self.assertIn('-File "%SCRIPT%" %*', acquire)
        self.assertIn("/main/scripts/Acquire-LatestPromptKit.ps1", acquire)

    def test_quick_acquisition_resolves_single_desktop_dev_root(self) -> None:
        ps1 = ACQUIRE_PS1.read_text(encoding="utf-8")
        for marker in (
            "[Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)",
            "Join-Path $desktop 'dev'",
            "Join-Path $root $RepositoryFolderName",
            "Get-ExistingPromptKitRepositories",
            "Normalize-RepositoryUrl $origin",
            "Preserving canonical checkout and refusing a duplicate clone:",
            "no '-latest' sibling clone was created",
            "'merge', '--ff-only'",
            "Start-Process -FilePath $site",
        ):
            self.assertIn(marker, ps1)
        for forbidden in (
            "OneDriveCommercial",
            "OneDriveConsumer",
            "OG Laptop Backup\\Desktop\\dev",
            '$RepositoryFolderName-latest',
            '"$RepositoryFolderName-$suffix"',
        ):
            self.assertNotIn(forbidden, ps1)

    def test_native_git_stderr_is_exit_code_authoritative_and_separate(self) -> None:
        ps1 = ACQUIRE_PS1.read_text(encoding="utf-8")
        start = ps1.index("function Invoke-Git {")
        end = ps1.index("function Resolve-PythonCommand", start)
        invoke_git = ps1[start:end]
        for marker in (
            "$previousErrorActionPreference = $ErrorActionPreference",
            "$stderrPath = [System.IO.Path]::GetTempFileName()",
            "$ErrorActionPreference = 'Continue'",
            "$output = & git @Arguments 2> $stderrPath",
            "$exitCode = $LASTEXITCODE",
            "$stderr = @(Get-Content -LiteralPath $stderrPath -ErrorAction SilentlyContinue)",
            "$ErrorActionPreference = $previousErrorActionPreference",
            "Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue",
            "if ($exitCode -ne 0)",
            "return $stdoutText.Trim()",
        ):
            self.assertIn(marker, invoke_git)
        self.assertNotIn("2>&1", invoke_git)
        self.assertLess(
            invoke_git.index("$ErrorActionPreference = 'Continue'"),
            invoke_git.index("$output = & git @Arguments 2> $stderrPath"),
        )
        self.assertLess(
            invoke_git.index("$exitCode = $LASTEXITCODE"),
            invoke_git.index("$ErrorActionPreference = $previousErrorActionPreference"),
        )

    def test_acquisition_gui_blocks_close_while_handler_is_running(self) -> None:
        ps1 = ACQUIRE_PS1.read_text(encoding="utf-8")
        for marker in (
            "$form.Tag = 'idle'",
            "$form.Add_FormClosing({",
            "if ([string]$sender.Tag -eq 'acquiring')",
            "$eventArgs.Cancel = $true",
            "$form.Tag = 'acquiring'",
            "$closeButton.Enabled = $false",
            "$form.Tag = 'idle'",
            "if (-not $form.IsDisposed)",
            "$closeButton.Enabled = $true",
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
