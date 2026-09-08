from __future__ import annotations

import re
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"{label}: anchor missing")
    return text.replace(old, new, 1)


def patch_guided() -> None:
    path = Path("docs/prompt-kit-guided-recommendations.js")
    text = path.read_text(encoding="utf-8")
    helper_anchor = "function renderPromptFinderResults(){"
    helpers = r"""function promptFinderFallbackQuery(answers){var order=['goal','problemKnown','shape','startingPoint'];for(var i=0;i<order.length;i++){var question=questionById(order[i]),option=optionById(question,answers&&answers[order[i]]);if(option&&Array.isArray(option.queries)&&option.queries.length){var query=String(option.queries[0]||'').trim();if(query)return query}}return 'agent workflow'}
function openPromptFinderExternalFallback(){var query=promptFinderFallbackQuery(S.answers);if(window.OperantExternalResources&&typeof window.OperantExternalResources.openForUseCase==='function'){var origin=S.origin;window.closePromptFinder();window.OperantExternalResources.openForUseCase(query,origin);return}var search=document.getElementById('search');window.closePromptFinder();if(search){search.value=query;search.dispatchEvent(new Event('input',{bubbles:true}));search.focus()}}"""
    if "function promptFinderFallbackQuery(answers)" not in text:
        if helper_anchor not in text:
            raise SystemExit("guided fallback helper anchor missing")
        text = text.replace(helper_anchor, helpers + "\n" + helper_anchor, 1)

    pattern = re.compile(
        r"function renderPromptFinderResults\(\)\{.*?\}\nfunction openPromptFinder\(origin\)",
        re.S,
    )
    replacement = r"""function renderPromptFinderResults(){var results=scorePromptFinderAnswers(S.answers),fallbackQuery=promptFinderFallbackQuery(S.answers),body='<p class="finder-intro">These recommendations use the same registry, synonym, metadata, and search-ranking logic as the main Prompt Kit. Start with the primary prompt.</p>';if(results.length)results.forEach(function(x,i){body+=card(x,i)});else body+='<p>No registered prompt matched strongly enough. Continue with the registered external resource floor.</p>';body+='<article class="finder-result finder-external"><small>External fallback</small><h3>Prompt Kit does not cover this use case</h3><p>Search the registered external sources for <strong>'+escapePromptHtml(fallbackQuery)+'</strong>. Indexed skill matches are ranked first; the on-demand prompt catalog remains available as a source library.</p><div><button data-finder-external="1">Search external resources</button></div></article><button class="finder-back" id="finderRestart">Start over</button>';var el=document.getElementById('promptDetail');el.innerHTML=shell('Recommended Prompt Path',body);el.querySelectorAll('[data-finder-open]').forEach(function(b){b.onclick=function(){showPromptDetail(b.getAttribute('data-finder-open'),S.origin)}});el.querySelectorAll('[data-finder-copy]').forEach(function(b){b.onclick=function(){copyPrompt(b.getAttribute('data-finder-copy'));b.textContent='Copied!';setTimeout(function(){b.textContent='Copy'},1200)}});var external=el.querySelector('[data-finder-external]');if(external)external.onclick=openPromptFinderExternalFallback;document.getElementById('finderRestart').onclick=function(){S.step=0;S.answers={};renderPromptFinderQuestion()};var first=el.querySelector('[data-finder-open]')||external||document.getElementById('finderRestart');if(first)first.focus()}
function openPromptFinder(origin)"""
    if not pattern.search(text):
        raise SystemExit("guided results function anchor missing")
    text = pattern.sub(replacement, text, count=1)
    text = replace_once(
        text,
        "window.closePromptFinder=function(){closePromptDetail()};window.openPromptFinder=openPromptFinder;window.scorePromptFinderAnswers=scorePromptFinderAnswers;window.PROMPT_FINDER_QUESTIONS=PROMPT_FINDER_QUESTIONS;",
        "window.closePromptFinder=function(){closePromptDetail()};window.openPromptFinder=openPromptFinder;window.scorePromptFinderAnswers=scorePromptFinderAnswers;window.promptFinderFallbackQuery=promptFinderFallbackQuery;window.PROMPT_FINDER_QUESTIONS=PROMPT_FINDER_QUESTIONS;",
        "guided fallback export",
    )
    path.write_text(text, encoding="utf-8")


def patch_resources() -> None:
    path = Path("docs/prompt-kit-external-resources.js")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "grid-template-rows:auto auto minmax(0,1fr) auto",
        "grid-template-rows:auto auto auto minmax(0,1fr) auto",
        "external resource panel rows",
    )
    text = replace_once(
        text,
        ".operant-resource-list{overflow:auto;display:grid;gap:8px;align-content:start}",
        ".operant-resource-sources{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.operant-resource-source{display:grid;gap:4px;padding:9px;border:1px solid var(--border);border-radius:8px;background:var(--bg)}.operant-resource-source strong{font-size:10px;color:var(--text-primary);overflow-wrap:anywhere}.operant-resource-source span{font-size:9px;color:var(--text-muted)}.operant-resource-source a{font-size:9px;color:var(--accent);text-decoration:none}.operant-resource-list{overflow:auto;display:grid;gap:8px;align-content:start}",
        "external source cards styles",
    )
    text = replace_once(
        text,
        "@media(max-width:640px){.operant-resource-backdrop{padding:3vh 8px}",
        "@media(max-width:640px){.operant-resource-sources{grid-template-columns:1fr}.operant-resource-backdrop{padding:3vh 8px}",
        "external source cards mobile styles",
    )
    text = replace_once(
        text,
        '<input class="operant-resource-search" type="search" placeholder="Search external skills and existing Operant coverage" aria-label="Search external resources"><div class="operant-resource-list" aria-live="polite"></div>',
        '<input class="operant-resource-search" type="search" placeholder="Search external skills and existing Operant coverage" aria-label="Search external resources"><div class="operant-resource-sources" aria-label="Registered external source libraries"></div><div class="operant-resource-list" aria-live="polite"></div>',
        "external source cards surface",
    )

    helper_anchor = "function renderExternalResourcePage(){"
    helpers = r"""function sourceRepositoryUrl(floor){var repository=String(floor&&floor.repository||'').trim();return repository?'https://github.com/'+repository:'#'}
function renderExternalSourceChoices(){var surface=document.getElementById('operantExternalResources');if(!surface||!externalResourceIndex)return;var host=surface.querySelector('.operant-resource-sources');if(!host)return;var filtered=externalResourceIndex.resources.filter(resourceMatches);var floors=(externalResourceIndex.source_floor||[]).map(function(floor,index){var matchCount=filtered.filter(function(item){return item.source_id===floor.id}).length;var catalogBonus=floor.search_mode==='on_demand'&&externalResourceQuery?1:0;return {floor:floor,index:index,matchCount:matchCount,catalogBonus:catalogBonus}}).sort(function(a,b){return b.matchCount-a.matchCount||b.catalogBonus-a.catalogBonus||a.index-b.index});host.innerHTML='';floors.forEach(function(entry){var floor=entry.floor,card=document.createElement('article');card.className='operant-resource-source';card.setAttribute('data-source-id',String(floor.id||''));var title=document.createElement('strong');title.textContent=String(floor.repository||floor.id||'External source');var meta=document.createElement('span');if(floor.enumeration==='catalog_csv')meta.textContent=String(floor.catalog_entry_count||0)+' catalog prompts · on-demand';else meta.textContent=String(floor.resource_count||0)+' indexed skills'+(entry.matchCount?' · '+entry.matchCount+' matching':'');var link=document.createElement('a');link.href=sourceRepositoryUrl(floor);link.target='_blank';link.rel='noopener noreferrer';link.textContent='Open source library';card.appendChild(title);card.appendChild(meta);card.appendChild(link);host.appendChild(card)})}"""
    if "function renderExternalSourceChoices()" not in text:
        if helper_anchor not in text:
            raise SystemExit("external source helper anchor missing")
        text = text.replace(helper_anchor, helpers + "\n\n" + helper_anchor, 1)

    text = replace_once(
        text,
        "if(!externalResourceIndex){list.innerHTML='<div class=\"operant-resource-empty\">Loading current resource index…</div>';count.textContent='Fetching metadata only…';previous.hidden=true;next.hidden=true;return}\n  var filtered=externalResourceIndex.resources.filter(resourceMatches);",
        "if(!externalResourceIndex){list.innerHTML='<div class=\"operant-resource-empty\">Loading current resource index…</div>';count.textContent='Fetching metadata only…';previous.hidden=true;next.hidden=true;return}\n  renderExternalSourceChoices();\n  var filtered=externalResourceIndex.resources.filter(resourceMatches);",
        "external source rendering seam",
    )

    pattern = re.compile(
        r"function openExternalResources\(\)\{.*?\}\n\nfunction closeExternalResources",
        re.S,
    )
    replacement = r"""function openExternalResources(request){
  ensureExternalResourceSurface();
  var surface=document.getElementById('operantExternalResources');
  var input=surface.querySelector('.operant-resource-search');
  var requestedQuery='';
  if(typeof request==='string')requestedQuery=request;else if(request&&typeof request.query==='string')requestedQuery=request.query;
  externalResourceQuery=String(requestedQuery||'').trim().toLowerCase();
  input.value=String(requestedQuery||'');
  surface.hidden=false;
  externalResourcePage=0;
  renderExternalResourcePage();
  loadExternalResources().then(function(){renderExternalResourcePage();input.focus()}).catch(function(error){var list=surface.querySelector('.operant-resource-list');list.innerHTML='<div class="operant-resource-empty">Resource catalog unavailable. Existing prompts remain fully usable.</div>';surface.querySelector('.operant-resource-count').textContent=String(error&&error.message||'Resource load failed')})
}
function openExternalResourcesForUseCase(query,origin){openExternalResources({query:query,origin:origin||null})}

function closeExternalResources"""
    if not pattern.search(text):
        raise SystemExit("external resource open function anchor missing")
    text = pattern.sub(replacement, text, count=1)
    text = replace_once(
        text,
        "window.OperantExternalResources={schema:OPERANT_EXTERNAL_RESOURCE_SCHEMA,open:openExternalResources,close:closeExternalResources,load:loadExternalResources,render:renderExternalResourcePage};",
        "window.OperantExternalResources={schema:OPERANT_EXTERNAL_RESOURCE_SCHEMA,open:openExternalResources,openForUseCase:openExternalResourcesForUseCase,close:closeExternalResources,load:loadExternalResources,render:renderExternalResourcePage};",
        "external fallback API export",
    )
    path.write_text(text, encoding="utf-8")


def patch_tutorial() -> None:
    path = Path("docs/PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md")
    text = path.read_text(encoding="utf-8")
    section = """## When Prompt Kit does not cover the use case

The tutorial must not trap a user inside Prompt Kit when the current registry does not fit the job. Internal Prompt Kit routing remains first because Operant prompts are canonical for Operant behavior. When the finder produces no registered candidate, or when the user reviews the candidates and selects **Search external resources** because none fits, the tutorial continues into the existing lazy **Resources** surface instead of looping back to another internal prompt.

The fallback mapping is deterministic and reuses existing authority:

1. The finder derives one compact external search query from the selected **goal** option first; if goal evidence is unavailable it falls back in order to **known problem**, **work shape**, then **starting point**. It uses the first canonical query phrase already attached to that answer rather than inventing a second routing vocabulary.
2. The Resources surface lazily loads `resources.v1.json` only after the user takes the fallback. Indexed skill sources with concrete matches rank first. An on-demand catalog receives a deterministic fallback preference when the local sidecar has no matching row, while stable source-floor order breaks ties.
3. The registered source floor is the authority for the external libraries: `f/prompts.chat` (prompt catalog), `mattpocock/skills` (agent skills), and `deepseek-ai/deepseek-harness` (agent/harness skills). The browser derives repository links from that source floor rather than maintaining a second URL table in the tutorial.
4. Resources that already have strong internal coverage continue to point back to the existing Operant prompt. External-only resources remain directly usable references; they do not auto-create Prompt Kit prompts. P79 still owns strengthen-before-add review, and license review remains required before copying or adapting donor content.

This fallback is a capability-gap route, not a declaration that an upstream resource is better. The user can edit the prefilled resource search before opening a donor library.

"""
    if section not in text:
        anchor = "## Conversational fallback\n"
        if anchor not in text:
            raise SystemExit("tutorial external fallback insertion anchor missing")
        text = text.replace(anchor, section + anchor, 1)
    text = replace_once(
        text,
        "P65 asks one concise question at a time, recommends one primary prompt and no more than two follow-ons, and refuses to fabricate prompt IDs that are not present in its supplied/current routing vocabulary.",
        "P65 asks one concise question at a time, recommends one primary prompt and no more than two follow-ons, and refuses to fabricate prompt IDs that are not present in its supplied/current routing vocabulary. Use P65 for conversational distinctions inside Prompt Kit; when Prompt Kit itself does not cover the capability, use the tutorial's external Resources fallback instead.",
        "tutorial P65 boundary",
    )
    text = replace_once(
        text,
        "node --check docs/prompt-kit-guided-recommendations.js\nnode --check docs/prompt-kit-journey.js",
        "node --check docs/prompt-kit-guided-recommendations.js\nnode --check docs/prompt-kit-external-resources.js\nnode --check docs/prompt-kit-journey.js",
        "tutorial external runtime validation command",
    )
    text = replace_once(
        text,
        "python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v",
        "python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance tests.test_operant_external_resources -v",
        "tutorial external regression command",
    )
    text = replace_once(
        text,
        "Repository validation can prove registry integrity, the current four-question shared-search implementation, registry-owned next-step extraction, session-only completion state, JavaScript syntax, current Favorite/shortcut semantics, generated-site parity, and focused documentation assertions.",
        "Repository validation can prove registry integrity, the current four-question shared-search implementation, deterministic Prompt Kit-to-Resources fallback wiring, registered source-floor links, registry-owned next-step extraction, session-only completion state, JavaScript syntax, current Favorite/shortcut semantics, generated-site parity, and focused documentation assertions.",
        "tutorial proof ceiling",
    )
    path.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    path = Path("tests/test_operant_external_resources.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'RUNTIME = ROOT / "docs" / "prompt-kit-external-resources.js"\nSITE = ROOT / "web" / "prompt-kit" / "index.html"',
        'RUNTIME = ROOT / "docs" / "prompt-kit-external-resources.js"\nGUIDED_RUNTIME = ROOT / "docs" / "prompt-kit-guided-recommendations.js"\nFINDER_TUTORIAL = ROOT / "docs" / "PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"\nSITE = ROOT / "web" / "prompt-kit" / "index.html"',
        "external regression constants",
    )
    text = replace_once(
        text,
        '        cls.runtime = RUNTIME.read_text(encoding="utf-8")\n        cls.site = SITE.read_text(encoding="utf-8")',
        '        cls.runtime = RUNTIME.read_text(encoding="utf-8")\n        cls.guided = GUIDED_RUNTIME.read_text(encoding="utf-8")\n        cls.tutorial = FINDER_TUTORIAL.read_text(encoding="utf-8")\n        cls.site = SITE.read_text(encoding="utf-8")',
        "external regression setup",
    )
    if "def test_prompt_finder_routes_internal_gaps_to_registered_external_floor" not in text:
        anchor = "    def test_full_validator_accepts_current_projection(self) -> None:\n"
        addition = '''    def test_prompt_finder_routes_internal_gaps_to_registered_external_floor(self) -> None:\n        for marker in (\n            "function promptFinderFallbackQuery(answers)",\n            "var order=['goal','problemKnown','shape','startingPoint']",\n            "data-finder-external",\n            "Prompt Kit does not cover this use case",\n            "OperantExternalResources.openForUseCase",\n            "window.promptFinderFallbackQuery=promptFinderFallbackQuery",\n        ):\n            self.assertIn(marker, self.guided)\n        self.assertNotIn(\n            "No registered prompt matched strongly enough. Search for P65",\n            self.guided,\n        )\n        for marker in (\n            "function renderExternalSourceChoices()",\n            "externalResourceIndex.source_floor",\n            "catalogBonus",\n            "https://github.com/",\n            "openForUseCase:openExternalResourcesForUseCase",\n            "Registered external source libraries",\n        ):\n            self.assertIn(marker, self.runtime)\n        for repository in ("f/prompts.chat", "mattpocock/skills", "deepseek-ai/deepseek-harness"):\n            self.assertIn(repository, self.tutorial)\n        self.assertIn("When Prompt Kit does not cover the use case", self.tutorial)\n        self.assertIn("data-finder-external", self.site)\n        self.assertIn("openForUseCase:openExternalResourcesForUseCase", self.site)\n\n'''
        if anchor not in text:
            raise SystemExit("external regression insertion anchor missing")
        text = text.replace(anchor, addition + anchor, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_guided()
    patch_resources()
    patch_tutorial()
    patch_tests()


if __name__ == "__main__":
    main()
