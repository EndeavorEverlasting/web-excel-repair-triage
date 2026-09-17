#!/usr/bin/env python3
"""One-shot Sprint 4 carrier mutation; removed after canonical generation succeeds."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before(path: Path, marker: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if addition.strip() in text:
        return
    count = text.count(marker)
    if count != 1:
        raise SystemExit(f"{path}: expected one insertion marker, found {count}: {marker!r}")
    path.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")


def patch_compiler() -> None:
    path = ROOT / "scripts" / "prompt_language_compiler.py"
    marker = "def render(\n"
    addition = '''def render_execution_profile_overlay(profile: dict[str, Any]) -> str:\n    """Render a context-free product overlay from validated execution-profile authority.\n\n    Full semantic compilation still uses render(...). This bounded overlay exists so the\n    static Prompt Kit can expose a user compute preference without fabricating runtime\n    evidence or a repository head.\n    """\n    profile = validate_profile(profile)\n    constraints = ", ".join(sorted(REQUIRED_NON_WEAKENABLE))\n    lines = [\n        "COMPILED EXECUTION PROFILE",\n        f"Execution profile: {profile['profile']}",\n        f"Compute policy: {profile['compute_policy']}",\n        f"Parallel policy: {profile['parallel_policy']}",\n        f"Hypothesis policy: {profile['hypothesis_policy']}",\n        f"Validation policy: {profile['validation_policy']}",\n        f"Stop policy: {profile['stop_policy']}",\n        f"Non-weakenable constraints remain mandatory: {constraints}.",\n        "This profile changes compute strategy only; canonical safety, scope, evidence, privacy, destructive-operation, and acceptance requirements remain authoritative.",\n    ]\n    return "\\n".join(lines) + "\\n"\n\n\n'''
    insert_before(path, marker, addition)


def patch_builder() -> None:
    path = ROOT / "scripts" / "build_prompt_kit_registry.py"
    replace_once(
        path,
        "from scripts import prompt_classification  # noqa: E402\n",
        "from scripts import prompt_classification  # noqa: E402\nfrom scripts import prompt_compute_mode  # noqa: E402\n",
    )
    replace_once(
        path,
        'PROFILE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-profiles.js"\n',
        'PROFILE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-profiles.js"\nCOMPUTE_MODE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-compute-mode.js"\n',
    )
    replace_once(
        path,
        '    ontology = build_ontology_model(prompts)\n    ontology_json = json.dumps(ontology, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")\n',
        '    ontology = build_ontology_model(prompts)\n    ontology_json = json.dumps(ontology, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")\n    compute_mode_manifest = prompt_compute_mode.build_product_manifest()\n    compute_mode_json = json.dumps(compute_mode_manifest, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")\n',
    )
    replace_once(
        path,
        '    profile_script = _read_runtime(PROFILE_RUNTIME, "Prompt Kit named profile behavior")\n',
        '    profile_script = _read_runtime(PROFILE_RUNTIME, "Prompt Kit named profile behavior")\n    compute_mode_script = _read_runtime(COMPUTE_MODE_RUNTIME, "Prompt Kit Compute Mode behavior")\n',
    )
    replace_once(
        path,
        '        f"<script>\\n{profile_script}\\n</script>\\n"\n        f"<script>\\n{polish_script}\\n</script>\\n"\n',
        '        f"<script>\\n{profile_script}\\n</script>\\n"\n        f"<script>\\nwindow.PROMPT_KIT_COMPUTE_MODE_MANIFEST = {compute_mode_json};\\n</script>\\n"\n        f"<script>\\n{compute_mode_script}\\n</script>\\n"\n        f"<script>\\n{polish_script}\\n</script>\\n"\n',
    )


def patch_base_runtime() -> None:
    path = ROOT / "docs" / "prompt-kit.js"
    replace_once(
        path,
        "function copyPrompt(id){var p=PROMPTS.find(function(x){return x.id===id});if(p&&p.copyContent){copyToClipboard(p.copyContent)}}",
        "function copyPrompt(id){var p=PROMPTS.find(function(x){return x.id===id});if(p&&p.copyContent){var content=window.PromptKitComputeMode?window.PromptKitComputeMode.effectivePrompt(window,p):p.copyContent;copyToClipboard(content)}}",
    )
    replace_once(
        path,
        "safeUseWhen=escapePromptHtml(p.useWhen),safeCopyContent=escapePromptHtml(p.copyContent||'');",
        "safeUseWhen=escapePromptHtml(p.useWhen),effectiveCopyContent=(window.PromptKitComputeMode?window.PromptKitComputeMode.effectivePrompt(window,p):(p.copyContent||'')),safeCopyContent=escapePromptHtml(effectiveCopyContent||'');",
    )
    replace_once(
        path,
        "<div class=\"pd-section\"><h4>Prompt Content</h4><pre>'+safeCopyContent+'</pre></div>",
        "<div class=\"pd-section\"><h4>Prompt Content</h4><pre data-prompt-effective-content>'+safeCopyContent+'</pre></div>",
    )
    replace_once(
        path,
        "el.innerHTML=html;var markCopied=",
        "el.innerHTML=html;if(window.PromptKitComputeMode&&window.PromptKitComputeMode.decorateDetail){window.PromptKitComputeMode.decorateDetail(window,el,p.id)}var markCopied=",
    )


def patch_polish_runtime() -> None:
    path = ROOT / "docs" / "prompt-kit-polish.js"
    replace_once(
        path,
        "window.showCopyConfirmation=function(id){\n  var promptId=String(id||'');\n  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];\n  var prompt=catalog.find(function(item){return item&&item.id===promptId});\n  var copyContent=prompt&&prompt.copyContent?prompt.copyContent:'';\n",
        "window.showCopyConfirmation=function(id,copyContentOverride){\n  var promptId=String(id||'');\n  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];\n  var prompt=catalog.find(function(item){return item&&item.id===promptId});\n  var copyContent=copyContentOverride!=null?String(copyContentOverride):(prompt&&prompt.copyContent?(window.PromptKitComputeMode?window.PromptKitComputeMode.effectivePrompt(window,prompt):prompt.copyContent):'');\n",
    )
    replace_once(
        path,
        "window.copyPrompt=function(id){\n  var p=PROMPTS.find(function(x){return x.id===id});\n  if(p&&p.copyContent)copyToClipboard(p.copyContent,function(){\n    showCopyConfirmation(id);\n",
        "window.copyPrompt=function(id){\n  var p=PROMPTS.find(function(x){return x.id===id});\n  if(p&&p.copyContent){\n    var effectiveCopyContent=window.PromptKitComputeMode?window.PromptKitComputeMode.effectivePrompt(window,p):p.copyContent;\n    copyToClipboard(effectiveCopyContent,function(){\n    showCopyConfirmation(id,effectiveCopyContent);\n",
    )
    replace_once(
        path,
        "  })\n};\n\nfunction clearTransientPromptFilters(){",
        "    })\n  }\n};\n\nfunction clearTransientPromptFilters(){",
    )


def patch_docs() -> None:
    sprint = ROOT / "harness" / "prompt-compilation" / "PROMPT_COMPILATION_SPRINT_MAP.md"
    replace_once(
        sprint,
        "**Status:** TRACKED / SPRINTS 1–3 INTEGRATED ON MAIN VIA #483/#485/#515",
        "**Status:** TRACKED / SPRINTS 1–3 INTEGRATED; SPRINT 4 IMPLEMENTED ON ISOLATED VALIDATION LANE",
    )
    replace_once(
        sprint,
        "**Ledger index:** TRQ-009 (Sprint 1), TRQ-010 (Sprint 2), TRQ-012 (Sprint 3 design/prototypes)",
        "**Ledger index:** TRQ-009 (Sprint 1), TRQ-010 (Sprint 2), TRQ-012 (Sprint 3 design/prototypes), TRQ-013 (Sprint 4 product wiring)",
    )
    sprint_text = sprint.read_text(encoding="utf-8")
    heading = "### Sprint 4 — Prompt Kit wiring + Compute Mode product surface"
    start = sprint_text.index(heading)
    status_pos = sprint_text.index("**Status:** PLANNED (dependency: Sprint 3 integrated)", start)
    sprint_text = sprint_text[:status_pos] + "**Status:** IMPLEMENTED / VALIDATION PENDING on `feat/prompt-compilation-compute-mode-20260916`" + sprint_text[status_pos + len("**Status:** PLANNED (dependency: Sprint 3 integrated)"):]
    owned = "**Owned:** wire compiler into effective-prompt generation path; user-facing Compute Mode (Exhaustive/Efficient) with per-prompt overrides; preserve builder-owned generation."
    owned_new = owned + "\n\n**Implementation slice:** compiler-owned context-free profile overlays; global user default plus per-prompt override with `run > prompt > user > product` resolver parity; Efficient removes only the shared `EXHAUSTIVE AVAILABLE COMPUTE RULE` section while preserving every other canonical prompt contract; content-only prompts remain unchanged; canonical website regeneration remains builder-owned."
    if owned not in sprint_text:
        raise SystemExit("Sprint 4 owned-scope marker changed")
    sprint.write_text(sprint_text.replace(owned, owned_new, 1), encoding="utf-8")

    readme = ROOT / "harness" / "prompt-compilation" / "README.md"
    text = readme.read_text(encoding="utf-8")
    if "Compute Mode product bridge" not in text:
        text = text.replace(
            "- Improvement Compiler: `scripts/prompt_improvement_compiler.py`\n",
            "- Improvement Compiler: `scripts/prompt_improvement_compiler.py`\n- Compute Mode product bridge: `scripts/prompt_compute_mode.py` + `docs/prompt-kit-compute-mode.js`\n",
            1,
        )
        text = text.replace(
            "python scripts/prompt_improvement_compiler.py run-journey --finding harness/prompt-compilation/improvement-journeys/IJ01-modality-recurrence/finding.json --summary\n",
            "python scripts/prompt_improvement_compiler.py run-journey --finding harness/prompt-compilation/improvement-journeys/IJ01-modality-recurrence/finding.json --summary\npython -m unittest tests.test_prompt_compute_mode -v\npython scripts/build_prompt_kit_registry.py --check\n",
            1,
        )
        readme.write_text(text, encoding="utf-8")

    architecture = ROOT / "harness" / "prompt-compilation" / "PROMPT_COMPILATION_ARCHITECTURE.md"
    text = architecture.read_text(encoding="utf-8")
    if "## Sprint 4 product wiring boundary" not in text:
        text += """\n\n## Sprint 4 product wiring boundary\n\nThe Prompt Kit product consumes compiler-owned **context-free execution-profile overlays** for the user Compute Mode surface. This is intentionally narrower than a context-bound `prompt-build-receipt/v1`: the static website must not fabricate a repository head, runtime capability state, or owner-native evidence merely to render a preference.\n\n- `scripts/prompt_compute_mode.py` derives profile overlays from the canonical Context Engine profile library and Language Engine revision.\n- `docs/prompt-kit-compute-mode.js` owns browser persistence and mirrors the canonical precedence `run > prompt > user > product`; it does not own lifecycle events or semantic policy.\n- Exhaustive keeps the canonical prompt body intact and adds the compiler-owned overlay.\n- Efficient removes only the shared `EXHAUSTIVE AVAILABLE COMPUTE RULE` block before adding the efficient overlay; safety, scope, evidence, privacy, destructive-operation, acceptance, and prompt-specific MUST obligations remain untouched.\n- Content-only prompts remain canonical and do not receive Compute Mode mutation.\n- A future runtime with observed owner-native context may invoke full `render(...)` and emit `prompt-build-receipt/v1`; the static browser surface does not promote itself to that proof level.\n"""
        architecture.write_text(text, encoding="utf-8")


def patch_ledger() -> None:
    path = ROOT / ".ai" / "WORK_QUEUE.md"
    text = path.read_text(encoding="utf-8")
    if "## TRQ-013 — Prompt Compilation Sprint 4 Compute Mode product wiring" in text:
        return
    block = """\n\n## TRQ-013 — Prompt Compilation Sprint 4 Compute Mode product wiring\n\n- **Status:** ACTIVE / VALIDATION PENDING\n- **Priority:** P1\n- **Owner:** feat/prompt-compilation-compute-mode-20260916\n- **Branch / PR:** `feat/prompt-compilation-compute-mode-20260916` / PR pending\n- **Scope:** wire compiler-owned execution-profile overlays into Prompt Kit effective-copy/detail paths; expose global Exhaustive/Efficient preference and per-prompt overrides with Context Engine precedence parity; regenerate the canonical website through the builder; add focused product/compiler regressions\n- **Forbidden:** #450/#431 donor salvage; TRQ-007 frozen treatment mutation; raw conversation ingestion; new Evidence Spine event ownership; auto-promotion/auto-merge of improvement candidates; hand-editing generated `web/prompt-kit/index.html`\n- **Dependencies:** Sprints 1–3 integrated (#483/#485/#515); `prompt-execution-profile/v1`; `scripts/prompt_context_engine.py`; `scripts/prompt_language_compiler.py`; builder-owned Prompt Kit generation\n- **References:** `registry/prompts/prompt-compute-mode.v1.json`, `scripts/prompt_compute_mode.py`, `docs/prompt-kit-compute-mode.js`, `scripts/build_prompt_kit_registry.py`, `tests/test_prompt_compute_mode.py`, `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`\n- **Acceptance gate:** both profiles derive from canonical Context Engine definitions; browser resolution preserves `run > prompt > user > product`; Efficient removes only the shared exhaustive-only section; canonical prompt-specific/safety/evidence/privacy/scope/acceptance requirements remain; content-only prompts are unchanged; copy/detail surfaces consume effective content; generated site matches the canonical builder; focused + existing compilation tests and repository CI pass; exact validated head integrates to default branch\n- **Gate:** exact-head CI + review + merge\n- **Last proof:** implementation lane created from refreshed `main@93a8886d77e043023eeecca05f5e2e8e13b89f06`; validation pending\n- **Next action:** run the Sprint 4 carrier, inspect exact generated diff and focused tests, then open/validate/merge the exact green head\n- **Updated:** 2026-09-16T21:52:00-04:00\n"""
    path.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def main() -> int:
    patch_compiler()
    patch_builder()
    patch_base_runtime()
    patch_polish_runtime()
    patch_docs()
    patch_ledger()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
