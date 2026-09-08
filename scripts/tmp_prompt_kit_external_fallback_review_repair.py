from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"{label}: anchor missing")
    return text.replace(old, new, 1)


def patch_runtime() -> None:
    path = Path("docs/prompt-kit-external-resources.js")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "var externalResourceLoadPromise=null;",
        "var externalResourceLoadPromise=null;\nvar externalResourceOrigin=null;",
        "origin state",
    )
    text = replace_once(
        text,
        "function sourceRepositoryUrl(floor){var repository=String(floor&&floor.repository||'').trim();return repository?'https://github.com/'+repository:'#'}",
        "function sourceRepositoryUrl(floor){var repository=String(floor&&floor.repository||'').trim(),sha=String(floor&&floor.resolved_sha||'').trim(),catalogPath=String(floor&&floor.catalog_path||'').trim();if(!repository||!sha)return '#';return 'https://github.com/'+repository+(catalogPath?'/blob/'+sha+'/'+catalogPath:'/tree/'+sha)}",
        "commit-pinned floor links",
    )
    text = replace_once(
        text,
        "  var requestedQuery='';\n  if(typeof request==='string')requestedQuery=request;else if(request&&typeof request.query==='string')requestedQuery=request.query;",
        "  var requestedQuery='';\n  var requestedOrigin=request&&typeof request==='object'?request.origin:null;\n  externalResourceOrigin=requestedOrigin&&typeof requestedOrigin.focus==='function'?requestedOrigin:(document.activeElement&&typeof document.activeElement.focus==='function'?document.activeElement:null);\n  if(typeof request==='string')requestedQuery=request;else if(request&&typeof request.query==='string')requestedQuery=request.query;",
        "capture focus origin",
    )
    text = replace_once(
        text,
        "  loadExternalResources().then(function(){renderExternalResourcePage();input.focus()}).catch(function(error){var list=surface.querySelector('.operant-resource-list');list.innerHTML='<div class=\"operant-resource-empty\">Resource catalog unavailable. Existing prompts remain fully usable.</div>';surface.querySelector('.operant-resource-count').textContent=String(error&&error.message||'Resource load failed')})",
        "  loadExternalResources().then(function(){renderExternalResourcePage();if(!surface.hidden)input.focus()}).catch(function(error){var list=surface.querySelector('.operant-resource-list');list.innerHTML='<div class=\"operant-resource-empty\">Resource catalog unavailable. Existing prompts remain fully usable.</div>';surface.querySelector('.operant-resource-count').textContent=String(error&&error.message||'Resource load failed')})",
        "hidden-panel async focus guard",
    )
    text = replace_once(
        text,
        "function closeExternalResources(){var surface=document.getElementById('operantExternalResources');if(surface)surface.hidden=true}",
        "function closeExternalResources(){var surface=document.getElementById('operantExternalResources');if(surface)surface.hidden=true;var origin=externalResourceOrigin;externalResourceOrigin=null;if(origin&&typeof origin.focus==='function'&&document.contains(origin))origin.focus()}",
        "restore focus on close",
    )
    path.write_text(text, encoding="utf-8")


def patch_tutorial() -> None:
    path = Path("docs/PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "3. The registered source floor is the authority for the external libraries: `f/prompts.chat` (prompt catalog), `mattpocock/skills` (agent skills), and `deepseek-ai/deepseek-harness` (agent/harness skills). The browser derives repository links from that source floor rather than maintaining a second URL table in the tutorial.",
        "3. The registered source floor is the authority for the external libraries: `f/prompts.chat` (prompt catalog), `mattpocock/skills` (agent skills), and `deepseek-ai/deepseek-harness` (agent/harness skills). The browser derives commit-pinned repository links from each floor's `resolved_sha` (and the catalog path when present) rather than maintaining a second URL table in the tutorial.",
        "tutorial pinned source wording",
    )
    text = replace_once(
        text,
        "This fallback is a capability-gap route, not a declaration that an upstream resource is better. The user can edit the prefilled resource search before opening a donor library.",
        "This fallback is a capability-gap route, not a declaration that an upstream resource is better. The user can edit the prefilled resource search before opening a donor library. Closing Resources returns keyboard focus to the control that launched the resource path.",
        "tutorial focus wording",
    )
    path.write_text(text, encoding="utf-8")


def patch_static_test() -> None:
    path = Path("tests/test_operant_external_resources.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '            "https://github.com/",\n            "openForUseCase:openExternalResourcesForUseCase",',
        '            "resolved_sha",\n            "catalogPath?\'/blob/\'+sha+\'/\'+catalogPath:\'/tree/\'+sha",\n            "externalResourceOrigin",\n            "if(!surface.hidden)input.focus()",\n            "document.contains(origin)",\n            "openForUseCase:openExternalResourcesForUseCase",',
        "static review regression markers",
    )
    path.write_text(text, encoding="utf-8")


def patch_browser_proof() -> None:
    path = Path("tests/prompt_kit_external_resources_browser_proof.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    source_shas = {row["id"]: row["resolved_sha"] for row in expected["source_floor"]}\n',
        '    source_shas = {row["id"]: row["resolved_sha"] for row in expected["source_floor"]}\n    expected_floor_links = {\n        row["id"]: (\n            f\'https://github.com/{row["repository"]}/blob/{row["resolved_sha"]}/{row["catalog_path"]}\'\n            if row.get("catalog_path")\n            else f\'https://github.com/{row["repository"]}/tree/{row["resolved_sha"]}\'\n        )\n        for row in expected["source_floor"]\n    }\n',
        "browser expected floor links",
    )
    text = replace_once(
        text,
        '            loaded_requests = len(resource_requests)\n            rendered_rows = page.locator(".operant-resource-row").count()\n            loaded_panel_visible = not page.locator("#operantExternalResources").evaluate("el => el.hidden")\n',
        '            loaded_requests = len(resource_requests)\n            rendered_rows = page.locator(".operant-resource-row").count()\n            loaded_panel_visible = not page.locator("#operantExternalResources").evaluate("el => el.hidden")\n            source_card_links = page.locator(".operant-resource-source").evaluate_all(\n                "cards => Object.fromEntries(cards.map(card => [card.dataset.sourceId, card.querySelector(\'a\').href]))"\n            )\n            floor_links_pinned = source_card_links == expected_floor_links\n',
        "browser source card observation",
    )
    text = replace_once(
        text,
        '            page.keyboard.press("Escape")\n            closed_by_escape = page.locator("#operantExternalResources").evaluate("el => el.hidden")\n\n            portable_request_floor = len(resource_requests)\n',
        '            page.keyboard.press("Escape")\n            closed_by_escape = page.locator("#operantExternalResources").evaluate("el => el.hidden")\n            manual_focus_restored = page.evaluate("document.activeElement && document.activeElement.id") == "externalResourcesButton"\n\n            page.evaluate("window.OperantExternalResources.openForUseCase(\'code review\', document.getElementById(\'promptFinderBtn\'))")\n            page.wait_for_function("() => !document.getElementById(\'operantExternalResources\').hidden")\n            page.keyboard.press("Escape")\n            fallback_focus_restored = page.evaluate("document.activeElement && document.activeElement.id") == "promptFinderBtn"\n\n            portable_request_floor = len(resource_requests)\n',
        "browser focus restoration observation",
    )
    text = replace_once(
        text,
        '        {\n            "id": "render_is_bounded",',
        '        {\n            "id": "source_floor_links_are_commit_pinned",\n            "event": "source-library cards navigate to the registered resolved SHA rather than a moving default branch",\n            "occurred": True,\n            "passed": floor_links_pinned,\n            "source_links": source_card_links,\n            "expected_links": expected_floor_links,\n        },\n        {\n            "id": "render_is_bounded",',
        "browser source link observation record",
    )
    text = replace_once(
        text,
        '        {\n            "id": "escape_closes_resources",\n            "event": "Escape closes the progressive-disclosure resource panel",\n            "occurred": True,\n            "passed": bool(closed_by_escape),\n        },\n',
        '        {\n            "id": "escape_closes_resources",\n            "event": "Escape closes the progressive-disclosure resource panel",\n            "occurred": True,\n            "passed": bool(closed_by_escape),\n        },\n        {\n            "id": "resource_close_restores_keyboard_origin",\n            "event": "closing Resources restores focus for both the header launcher and the finder fallback origin",\n            "occurred": True,\n            "passed": manual_focus_restored and fallback_focus_restored,\n            "manual_focus_restored": manual_focus_restored,\n            "fallback_focus_restored": fallback_focus_restored,\n        },\n',
        "browser focus observation record",
    )
    text = replace_once(
        text,
        '            "status": "PASS" if by_id["search_preserves_pinned_source_navigation"]["passed"] and by_id["portable_package_serves_sidecar"]["passed"] and by_id["escape_closes_resources"]["passed"] else "FAIL",\n            "required_evidence_class": "browser_runtime_observed",\n            "observation_ids": ["search_preserves_pinned_source_navigation", "portable_package_serves_sidecar", "escape_closes_resources"],',
        '            "status": "PASS" if by_id["search_preserves_pinned_source_navigation"]["passed"] and by_id["source_floor_links_are_commit_pinned"]["passed"] and by_id["portable_package_serves_sidecar"]["passed"] and by_id["escape_closes_resources"]["passed"] and by_id["resource_close_restores_keyboard_origin"]["passed"] else "FAIL",\n            "required_evidence_class": "browser_runtime_observed",\n            "observation_ids": ["search_preserves_pinned_source_navigation", "source_floor_links_are_commit_pinned", "portable_package_serves_sidecar", "escape_closes_resources", "resource_close_restores_keyboard_origin"],',
        "browser resource navigation claim",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_runtime()
    patch_tutorial()
    patch_static_test()
    patch_browser_proof()


if __name__ == "__main__":
    main()
