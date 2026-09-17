#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from prepare_observed_behavior_subject import ExactHeadError, prepare_exact_head_subject


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def canonical(text: str) -> str:
    return str(text).replace("\r\n", "\n").replace("\r", "\n")


def execution_environment_kind(env=None) -> str:
    runtime_env = os.environ if env is None else env
    return (
        "github_actions_headless_browser"
        if str(runtime_env.get("GITHUB_ACTIONS", "")).lower() == "true"
        else "local_headless_browser"
    )


def observe(port: int, screenshot: Path):
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    observations: list[dict[str, object]] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
                reduced_motion="reduce",
                viewport={"width": 1440, "height": 900},
            )
            page = context.new_page()
            page.goto(
                f"http://127.0.0.1:{port}/web/prompt-kit/index.html",
                wait_until="domcontentloaded",
            )
            page.locator("#promptComputeMode").wait_for(state="visible")

            initial = page.evaluate(
                """() => ({
                  stored: localStorage.getItem('promptKit.computeMode.userDefault.v1'),
                  exhaustive: document.querySelector('#promptComputeMode [data-compute-mode="exhaustive"]').getAttribute('aria-pressed'),
                  efficient: document.querySelector('#promptComputeMode [data-compute-mode="efficient"]').getAttribute('aria-pressed'),
                  resolved: PromptKitComputeMode.resolveProfile({}).profile
                })"""
            )
            initial_default_ok = (
                initial["stored"] is None
                and initial["exhaustive"] == "true"
                and initial["efficient"] == "false"
                and initial["resolved"] == "exhaustive"
            )
            observations.append(
                {
                    "id": "compute_mode_product_default",
                    "event": "Fresh browser starts in Exhaustive product-default mode without inventing a stored user preference",
                    "occurred": True,
                    "passed": bool(initial_default_ok),
                    "state": initial,
                }
            )

            page.locator('#promptComputeMode [data-compute-mode="efficient"]').click()
            page.wait_for_timeout(80)
            switched = page.evaluate(
                """() => ({
                  stored: localStorage.getItem('promptKit.computeMode.userDefault.v1'),
                  exhaustive: document.querySelector('#promptComputeMode [data-compute-mode="exhaustive"]').getAttribute('aria-pressed'),
                  efficient: document.querySelector('#promptComputeMode [data-compute-mode="efficient"]').getAttribute('aria-pressed')
                })"""
            )
            switch_ok = (
                switched["stored"] == "efficient"
                and switched["exhaustive"] == "false"
                and switched["efficient"] == "true"
            )
            observations.append(
                {
                    "id": "compute_mode_user_switch",
                    "event": "Efficient header control persists the user default and updates pressed state",
                    "occurred": True,
                    "passed": bool(switch_ok),
                    "state": switched,
                }
            )

            expected_efficient = page.evaluate(
                "PROMPTS.find(p => p.id === 'P07').compiledEffectivePrompts.efficient"
            )
            card = page.locator('[data-prompt-id="P07"]')
            card.scroll_into_view_if_needed()
            card.locator('.prompt-copy-btn').click()
            page.wait_for_timeout(240)
            efficient_clipboard = canonical(page.evaluate("navigator.clipboard.readText()"))
            observations.append(
                {
                    "id": "compute_mode_efficient_copy",
                    "event": "P07 card Copy uses the compiled Efficient effective prompt selected by the user default",
                    "occurred": True,
                    "passed": efficient_clipboard == canonical(expected_efficient),
                    "actual_length": len(efficient_clipboard),
                    "expected_length": len(canonical(expected_efficient)),
                }
            )

            page.reload(wait_until="domcontentloaded")
            page.locator("#promptComputeMode").wait_for(state="visible")
            persisted = page.evaluate(
                """() => ({
                  stored: localStorage.getItem('promptKit.computeMode.userDefault.v1'),
                  efficient: document.querySelector('#promptComputeMode [data-compute-mode="efficient"]').getAttribute('aria-pressed')
                })"""
            )
            observations.append(
                {
                    "id": "compute_mode_user_default_reload",
                    "event": "Efficient user default survives reload",
                    "occurred": True,
                    "passed": bool(
                        persisted["stored"] == "efficient"
                        and persisted["efficient"] == "true"
                    ),
                    "state": persisted,
                }
            )

            card = page.locator('[data-prompt-id="P07"]')
            card.scroll_into_view_if_needed()
            card.locator('.prompt-open-btn').click()
            page.locator("#promptComputeOverride").wait_for(state="visible")
            inherited_source = page.locator(
                "#promptDetail .prompt-compute-mode-source"
            ).inner_text()
            inherited_ok = (
                page.locator("#promptComputeOverride").input_value() == ""
                and "effective efficient" in inherited_source
                and "user_default" in inherited_source
            )
            observations.append(
                {
                    "id": "compute_mode_detail_inherits_user_default",
                    "event": "P07 detail shows inherited Efficient mode and user_default provenance",
                    "occurred": True,
                    "passed": bool(inherited_ok),
                    "source": inherited_source,
                }
            )

            page.locator("#promptComputeOverride").select_option("exhaustive")
            page.wait_for_timeout(80)
            prompt_override_state = page.evaluate(
                """() => ({
                  overrides: JSON.parse(localStorage.getItem('promptKit.computeMode.promptOverrides.v1') || '{}'),
                  source: document.querySelector('#promptDetail .prompt-compute-mode-source').textContent
                })"""
            )
            override_ok = (
                prompt_override_state["overrides"].get("P07") == "exhaustive"
                and "effective exhaustive" in prompt_override_state["source"]
                and "prompt_override" in prompt_override_state["source"]
            )
            observations.append(
                {
                    "id": "compute_mode_prompt_override",
                    "event": "P07 prompt override persists Exhaustive and outranks the Efficient user default",
                    "occurred": True,
                    "passed": bool(override_ok),
                    "state": prompt_override_state,
                }
            )

            expected_exhaustive = page.evaluate(
                "PROMPTS.find(p => p.id === 'P07').compiledEffectivePrompts.exhaustive"
            )
            page.evaluate("navigator.clipboard.writeText('sentinel-compute-mode')")
            page.locator("#promptDetail .pd-section h4").nth(1).click()
            page.wait_for_timeout(260)
            exhaustive_clipboard = canonical(page.evaluate("navigator.clipboard.readText()"))
            observations.append(
                {
                    "id": "compute_mode_prompt_override_copy",
                    "event": "Prompt-detail neutral-surface Copy uses the Exhaustive compiled prompt selected by the P07 override",
                    "occurred": True,
                    "passed": exhaustive_clipboard == canonical(expected_exhaustive),
                    "actual_length": len(exhaustive_clipboard),
                    "expected_length": len(canonical(expected_exhaustive)),
                }
            )

            page.locator("#promptComputeOverride").select_option("")
            page.wait_for_timeout(80)
            restored_source = page.locator(
                "#promptDetail .prompt-compute-mode-source"
            ).inner_text()
            override_cleared = page.evaluate(
                """() => !Object.prototype.hasOwnProperty.call(
                  JSON.parse(localStorage.getItem('promptKit.computeMode.promptOverrides.v1') || '{}'),
                  'P07'
                )"""
            )
            observations.append(
                {
                    "id": "compute_mode_prompt_override_clear",
                    "event": "Clearing the P07 override restores the Efficient user-default resolution",
                    "occurred": True,
                    "passed": bool(
                        override_cleared
                        and "effective efficient" in restored_source
                        and "user_default" in restored_source
                    ),
                    "source": restored_source,
                }
            )

            run_state = page.evaluate(
                """() => {
                  PromptKitComputeMode.setRunOverride('exhaustive');
                  PromptKitComputeMode.getController().refreshDetail('P07');
                  return {
                    runOverride: PromptKitComputeMode.getRunOverride(),
                    source: document.querySelector('#promptDetail .prompt-compute-mode-source').textContent,
                    storedUser: localStorage.getItem('promptKit.computeMode.userDefault.v1')
                  };
                }"""
            )
            observations.append(
                {
                    "id": "compute_mode_run_override_precedence",
                    "event": "Explicit run override resolves Exhaustive ahead of the persisted Efficient user default without mutating that default",
                    "occurred": True,
                    "passed": bool(
                        run_state["runOverride"] == "exhaustive"
                        and run_state["storedUser"] == "efficient"
                        and "effective exhaustive" in run_state["source"]
                        and "explicit_run_override" in run_state["source"]
                    ),
                    "state": run_state,
                }
            )

            run_sentinel = "sentinel-compute-mode-run"
            page.evaluate("value => navigator.clipboard.writeText(value)", run_sentinel)
            page.locator("#promptDetail .pd-section h4").nth(1).click()
            page.wait_for_timeout(260)
            run_clipboard = canonical(page.evaluate("navigator.clipboard.readText()"))
            observations.append(
                {
                    "id": "compute_mode_run_override_copy",
                    "event": "P07 Copy honors the explicit Exhaustive run override",
                    "occurred": run_clipboard != run_sentinel,
                    "passed": run_clipboard == canonical(expected_exhaustive),
                    "actual_length": len(run_clipboard),
                    "expected_length": len(canonical(expected_exhaustive)),
                }
            )

            final_state = page.evaluate(
                """() => {
                  PromptKitComputeMode.clearRunOverride();
                  PromptKitComputeMode.getController().refreshDetail('P07');
                  return {
                    runOverride: PromptKitComputeMode.getRunOverride(),
                    source: document.querySelector('#promptDetail .prompt-compute-mode-source').textContent,
                    storedUser: localStorage.getItem('promptKit.computeMode.userDefault.v1')
                  };
                }"""
            )
            observations.append(
                {
                    "id": "compute_mode_run_override_clear",
                    "event": "Clearing the run override restores Efficient user-default resolution",
                    "occurred": True,
                    "passed": bool(
                        final_state["runOverride"] is None
                        and final_state["storedUser"] == "efficient"
                        and "effective efficient" in final_state["source"]
                        and "user_default" in final_state["source"]
                    ),
                    "state": final_state,
                }
            )

            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=False)
            context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return observations


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--screenshot", required=True)
    parser.add_argument("--port", type=int, default=8774)
    args = parser.parse_args(argv)
    receipt_path = Path(args.receipt)
    screenshot = Path(args.screenshot)
    try:
        subject = prepare_exact_head_subject()
    except ExactHeadError as exc:
        print(
            f"exact-head preflight failed; Chromium was not launched\n{exc}",
            file=sys.stderr,
        )
        return 2

    observations = observe(args.port, screenshot)
    by_id = {item["id"]: item for item in observations}
    user_default = all(
        by_id[item]["passed"]
        for item in (
            "compute_mode_product_default",
            "compute_mode_user_switch",
            "compute_mode_user_default_reload",
        )
    )
    effective_copy = all(
        by_id[item]["passed"]
        for item in (
            "compute_mode_efficient_copy",
            "compute_mode_prompt_override_copy",
            "compute_mode_run_override_copy",
        )
    )
    precedence = all(
        by_id[item]["passed"]
        for item in (
            "compute_mode_detail_inherits_user_default",
            "compute_mode_prompt_override",
            "compute_mode_prompt_override_clear",
            "compute_mode_run_override_precedence",
            "compute_mode_run_override_clear",
        )
    )
    verdict = "PASS" if all(item["passed"] for item in observations) else "FAIL"
    receipt = {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": verdict,
        "evidence_class": "browser_runtime_observed",
        "subject": subject,
        "environment": {
            "kind": execution_environment_kind(),
            "engine": "chromium",
            "scenario": "compute-mode-user-prompt-run-precedence-and-effective-copy",
        },
        "claims": [
            {
                "id": "compute_mode_user_default",
                "statement": "Compute Mode starts Exhaustive, accepts an Efficient user default, and persists that default across reload",
                "status": "PASS" if user_default else "FAIL",
                "required_evidence_class": "browser_runtime_observed",
                "observation_ids": [
                    "compute_mode_product_default",
                    "compute_mode_user_switch",
                    "compute_mode_user_default_reload",
                ],
            },
            {
                "id": "compute_mode_effective_copy",
                "statement": "P07 Copy returns the compiled effective prompt selected by Efficient user default, Exhaustive prompt override, and Exhaustive run override",
                "status": "PASS" if effective_copy else "FAIL",
                "required_evidence_class": "browser_runtime_observed",
                "observation_ids": [
                    "compute_mode_efficient_copy",
                    "compute_mode_prompt_override_copy",
                    "compute_mode_run_override_copy",
                ],
            },
            {
                "id": "compute_mode_precedence",
                "statement": "Browser runtime enforces run > prompt > user > product precedence and clearing overrides restores the next lower authority",
                "status": "PASS" if precedence else "FAIL",
                "required_evidence_class": "browser_runtime_observed",
                "observation_ids": [
                    "compute_mode_detail_inherits_user_default",
                    "compute_mode_prompt_override",
                    "compute_mode_prompt_override_clear",
                    "compute_mode_run_override_precedence",
                    "compute_mode_run_override_clear",
                ],
            },
        ],
        "observations": observations,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "receipt": str(receipt_path),
                "screenshot": str(screenshot),
                "observations": observations,
            }
        )
    )
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
