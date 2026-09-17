#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import textwrap
from pathlib import Path

PROMPTS = Path("docs/prompts.json")
HISTORY = Path("harness/contracts/prompt-quality-history.v1.json")
P07_TEST = Path("tests/test_p07_effective_prompt_identity.py")
BUILDER = Path("scripts/build_prompt_kit_registry.py")
COMPILER = Path("scripts/prompt_language_compiler.py")
BASE_JS = Path("docs/prompt-kit.js")
COMPUTE_JS = Path("docs/prompt-kit-compute-mode.js")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def strengthen_p07() -> tuple[str, str]:
    before = PROMPTS.read_bytes()
    from_sha = git_blob_sha(before)
    prompts = json.loads(before.decode("utf-8"))
    p07 = next((item for item in prompts if item.get("id") == "P07"), None)
    if p07 is None:
        raise SystemExit("P07 not found in docs/prompts.json")
    sentinel = "NON-SILENT CONTINUATION / TERMINATION CONTRACT (MANDATORY)"
    if sentinel in p07["copyContent"]:
        raise SystemExit("P07 already contains the non-silent continuation contract")

    section = textwrap.dedent(
        """
        NON-SILENT CONTINUATION / TERMINATION CONTRACT (MANDATORY)
        P07 is an execution prompt, not a planning or status-report prompt. Do not stop, summarize as if finished, hand control back, ask the operator to continue, or offer to do later what can still be done now while SAFE & EXECUTABLE progress-bearing work remains inside the authorized scope.

        CHECKPOINTS ARE NOT STOP CONDITIONS
        A plan, one patch, one passing test, a generated artifact, a commit, a push, an open PR, review-ready state, green CI, a mergeable branch, or a progress report is evidence of movement. None is a terminal state when another safe authorized action can materially advance the requested outcome.

        MANDATORY CONTINUATION LOOP
        1. After every evidence-changing pass, reconstruct the requested target state, acceptance criteria, proof requirements, and applicable end-state contracts.
        2. Disposition every material remaining item exactly once as PROVEN DONE, SAFE & EXECUTABLE, REQUIRED SUCCESSOR WORK, BLOCKED, UNSAFE, or OUT OF SCOPE.
        3. If any item is SAFE & EXECUTABLE and progress-bearing, execute it now. Do not replace execution with a recommendation, next-steps list, permission-seeking, or operator handoff.
        4. If the next required action belongs to an available canonical owner, tool, workflow, or agent and the governing scope permits routing, invoke or route that owner and continue through the returned evidence instead of terminating at the handoff.
        5. If at least two meaningful dependency-ready lanes are independent and safe autonomous capacity exists, dispatch them concurrently and rejoin their evidence. Serial calls, lane enumeration, or saying work could be parallelized do not count as parallel execution.
        6. When validation fails, inspect the failure, repair the cause when owned, and rerun the affected gate. A failed or skipped check never becomes a completion claim.
        7. After each meaningful pass, communicate compactly as CHANGED / PROVED / NEXT and continue. If progress stops because of a boundary, name the boundary immediately; never go silent at an unexplained edge.
        8. Before any terminal response, perform a residual-compute sweep across implementation, regressions, focused and broad validation, review findings, integration, generated artifacts, deployment/runtime observation, operator acceptance, and durability/handoff obligations that apply to the requested outcome.

        TERMINAL GATE
        A terminal response is allowed only when no SAFE & EXECUTABLE progress-bearing item remains in the active authority; every material requested-scope item has a supported disposition; authorized integration is complete or an exact integration blocker is proven; REQUIRED SUCCESSOR WORK is durably owned with its first executable action; and the proof ceiling is explicit.

        Any response that ends while SAFE & EXECUTABLE progress-bearing work remains is a P07 contract failure. `I can continue`, `ready for review`, `PR opened`, `CI is green`, `commit created`, and generic `next steps` are not valid terminal substitutes for work the agent can still perform.

        QUIESCENCE / REAL BLOCKERS
        Do not manufacture churn merely to remain active. When the decisive next transition requires an unavailable credential, protected runtime, physical device, user-only decision, external event, blocking review, or unavailable execution adapter, persist the blocker once with evidence, consequence, smallest advancing action, and proof ceiling. Two materially identical blocker observations with an unchanged proof-relevance fingerprint require quiescence rather than repetitive mutations.

        RECURRENCE RULE
        Repeated premature stopping is itself a system defect. When the same stop failure recurs, strengthen the canonical prompt, validator, test, trigger, workflow, or ownership contract that allowed it; do not merely tell the next agent to try harder.
        """
    ).strip()

    p07["copyContent"] = p07["copyContent"].rstrip() + "\n\n" + section + "\n"
    p07["version"] = "1.9.0"
    p07["purpose"] = (
        "Execute the next repository sprint to an evidence-backed fixed point, continuing automatically "
        "while safe executable progress-bearing work remains."
    )
    p07["nextStep"] = (
        "Continue autonomously through every safe executable progress-bearing action until the terminal gate "
        "is satisfied; when blocked, name the exact boundary and smallest advancing action instead of silently stopping."
    )
    p07["proofGate"] = (
        "Canonical P07 and every compiled effective profile preserve the non-silent continuation contract; "
        "focused regressions, prompt-quality history, generated-site parity, deterministic repository floor, "
        "integration, and live website publication gates pass at their claimed proof level."
    )
    after = (json.dumps(prompts, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    PROMPTS.write_bytes(after)
    return from_sha, git_blob_sha(after)


def repair_compiled_identity() -> None:
    replace_once(
        BUILDER,
        '            compiled[profile_name] = result["effective_prompt"]\n',
        '            canonical = str(item.get("copyContent") or "").rstrip()\n'
        '            overlay = str(result["effective_prompt"]).strip()\n'
        '            compiled[profile_name] = (\n'
        '                canonical\n'
        '                + "\\n\\nEXECUTION PROFILE OVERLAY\\n"\n'
        '                + "The canonical prompt obligations remain in force; this profile only adjusts execution strategy.\\n\\n"\n'
        '                + overlay\n'
        '                + "\\n"\n'
        '            )\n',
    )
    replace_once(
        COMPILER,
        'def find_weakening(text: str, policy: dict[str, Any]) -> list[str]:\n'
        '    hits: list[str] = []\n'
        '    for pattern in policy["must_weakening_patterns"]:\n'
        '        if re.search(pattern, text, flags=re.IGNORECASE):\n'
        '            hits.append(pattern)\n'
        '    return hits\n',
        'def find_weakening(text: str, policy: dict[str, Any]) -> list[str]:\n'
        '    marker = "EXECUTION PROFILE OVERLAY"\n'
        '    scan_text = text.split(marker, 1)[1] if marker in text else text\n'
        '    hits: list[str] = []\n'
        '    for pattern in policy["must_weakening_patterns"]:\n'
        '        if re.search(pattern, scan_text, flags=re.IGNORECASE):\n'
        '            hits.append(pattern)\n'
        '    return hits\n',
    )


def repair_ui_identity() -> None:
    replace_once(
        BASE_JS,
        "function copyPrompt(id){var p=PROMPTS.find(function(x){return x.id===id});if(p&&p.copyContent){copyToClipboard(p.copyContent)}}",
        "function resolvePromptDetailContent(prompt){if(typeof PromptKitComputeMode!=='undefined'&&PromptKitComputeMode&&typeof PromptKitComputeMode.resolveCopyContent==='function')return PromptKitComputeMode.resolveCopyContent(prompt);return prompt&&prompt.copyContent!=null?String(prompt.copyContent):''}\n"
        "function copyPrompt(id){var p=PROMPTS.find(function(x){return x.id===id});var content=resolvePromptDetailContent(p);if(p&&content){copyToClipboard(content)}}",
    )
    replace_once(BASE_JS, "safeCopyContent=escapePromptHtml(p.copyContent||'')", "safeCopyContent=escapePromptHtml(resolvePromptDetailContent(p))")
    replace_once(
        BASE_JS,
        "<div class=\"pd-section\"><h4>Prompt Content</h4><pre>'+safeCopyContent+'</pre></div>",
        "<div class=\"pd-section\"><h4>Prompt Content</h4><pre data-prompt-effective-content=\"true\">'+safeCopyContent+'</pre></div>",
    )

    replace_once(COMPUTE_JS, "function refreshDetail(doc,storage,promptId){", "function refreshDetail(doc,storage,promptId,promptCatalog){")
    replace_once(
        COMPUTE_JS,
        "  var resolution=resolveProfile({\n",
        "  var prompt=null;\n"
        "  if(Array.isArray(promptCatalog)){\n"
        "    for(var pi=0;pi<promptCatalog.length;pi++){\n"
        "      if(String(promptCatalog[pi]&&promptCatalog[pi].id||'').toUpperCase()===String(promptId||'').toUpperCase()){prompt=promptCatalog[pi];break}\n"
        "    }\n"
        "  }\n"
        "  var contentNode=detail.querySelector('[data-prompt-effective-content]');\n"
        "  if(prompt&&contentNode)contentNode.textContent=resolveCopyContent(prompt,{storage:storage});\n"
        "  var resolution=resolveProfile({\n",
    )
    text = COMPUTE_JS.read_text(encoding="utf-8")
    text = text.replace("refreshDetail(doc,storage,promptId)\n", "refreshDetail(doc,storage,promptId,root.PROMPTS)\n")
    text = text.replace("refreshDetail(doc,storage,openId.getAttribute('data-prompt-id'))", "refreshDetail(doc,storage,openId.getAttribute('data-prompt-id'),root.PROMPTS)")
    text = text.replace("refreshDetail(doc,storage,id)", "refreshDetail(doc,storage,id,root.PROMPTS)")
    text = text.replace("return refreshDetail(doc,storage,promptId)}", "return refreshDetail(doc,storage,promptId,root.PROMPTS)}")
    COMPUTE_JS.write_text(text, encoding="utf-8")


def expire_history_exception() -> None:
    history = json.loads(HISTORY.read_text(encoding="utf-8"))
    exceptions = history["effective_identity"]["temporary_exceptions"]
    filtered = [item for item in exceptions if item.get("prompt_id") != "P07"]
    if len(filtered) != len(exceptions) - 1:
        raise SystemExit("expected exactly one P07 temporary prompt-quality exception")
    history["effective_identity"]["temporary_exceptions"] = filtered
    HISTORY.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strengthen_tests() -> None:
    text = P07_TEST.read_text(encoding="utf-8")
    if "test_canonical_p07_forbids_premature_terminal_states" in text:
        raise SystemExit("non-stop P07 regression already exists")
    marker = '\n\nif __name__ == "__main__":\n'
    method = textwrap.dedent(
        '''
        def test_canonical_p07_forbids_premature_terminal_states(self) -> None:
            required = (
                "NON-SILENT CONTINUATION / TERMINATION CONTRACT (MANDATORY)",
                "CHECKPOINTS ARE NOT STOP CONDITIONS",
                "If any item is SAFE & EXECUTABLE and progress-bearing, execute it now.",
                "If progress stops because of a boundary, name the boundary immediately; never go silent at an unexplained edge.",
                "A terminal response is allowed only when no SAFE & EXECUTABLE progress-bearing item remains",
                "Any response that ends while SAFE & EXECUTABLE progress-bearing work remains is a P07 contract failure.",
                "Repeated premature stopping is itself a system defect.",
            )
            for phrase in required:
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, self.base)
            for profile in ("exhaustive", "efficient"):
                rendered = self.p07["compiledEffectivePrompts"][profile]
                with self.subTest(profile=profile):
                    for phrase in required:
                        self.assertIn(phrase, rendered)
        '''
    ).rstrip()
    if marker not in text:
        raise SystemExit("could not find unittest footer in P07 focused test")
    P07_TEST.write_text(text.replace(marker, "\n\n" + method + marker), encoding="utf-8")

    for path in (Path("tests/test_prompt_kit_product_interactions.py"), Path("tests/test_prompt_kit_mobile.py")):
        content = path.read_text(encoding="utf-8")
        content = content.replace(
            "safeCopyContent=escapePromptHtml(p.copyContent||'')",
            "safeCopyContent=escapePromptHtml(resolvePromptDetailContent(p))",
        )
        path.write_text(content, encoding="utf-8")


def main() -> int:
    before, after = strengthen_p07()
    repair_compiled_identity()
    repair_ui_identity()
    expire_history_exception()
    strengthen_tests()
    print(f"P07 registry blob: {before} -> {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
