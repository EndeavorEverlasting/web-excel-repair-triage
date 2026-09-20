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


def _environment() -> dict[str, str]:
    return {
        "kind": execution_environment_kind(),
        "engine": "chromium",
        "scenario": "compute-mode-user-prompt-run-precedence-and-effective-copy",
    }


def build_receipt(subject: dict[str, object], observations: list[dict[str, object]]) -> dict[str, object]:
    by_id = {item["id"]: item for item in observations}
    user_default = all(
        by_id[item]["passed"]
        for item in (
            "compute_mode_product_default",
            "compute_mode_user_switch",
            "compute_mode_user_default_reload",
            "compute_mode_global_efficient_canonical_copy",
        )
    )
    variant_copy = all(
        by_id[item]["passed"]
        for item in (
            "compute_mode_variant_default_exhaustive",
            "compute_mode_variant_efficient_selection",
            "compute_mode_variant_efficient_copy",
            "compute_mode_variant_reset_exhaustive",
            "compute_mode_variant_exhaustive_copy",
            "compute_mode_nonvariant_control_hidden",
        )
    )
    precedence = all(
        by_id[item]["passed"]
        for item in (
            "compute_mode_run_override_precedence",
            "compute_mode_run_override_clear",
        )
    )
    verdict = "PASS" if all(item["passed"] for item in observations) else "FAIL"
    return {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": verdict,
        "evidence_class": "browser_runtime_observed",
        "subject": subject,
        "environment": _environment(),
        "claims": [
            {
                "id": "compute_mode_user_default",
                "statement": "Compute Mode starts Exhaustive, accepts an Efficient global execution preference, persists it, and never silently shrinks canonical prompt copy",
                "status": "PASS" if user_default else "FAIL",
                "required_evidence_class": "browser_runtime_observed",
                "observation_ids": [
                    "compute_mode_product_default",
                    "compute_mode_user_switch",
                    "compute_mode_user_default_reload",
                    "compute_mode_global_efficient_canonical_copy",
                ],
            },
            {
                "id": "compute_mode_prompt_variant",
                "statement": "Variant-bearing prompt detail exposes an explicit Exhaustive/Efficient selector; Exhaustive is full canonical by default, Efficient changes preview/copy only after explicit prompt choice, and non-variant prompts pay no selector cost",
                "status": "PASS" if variant_copy else "FAIL",
                "required_evidence_class": "browser_runtime_observed",
                "observation_ids": [
                    "compute_mode_variant_default_exhaustive",
                    "compute_mode_variant_efficient_selection",
                    "compute_mode_variant_efficient_copy",
                    "compute_mode_variant_reset_exhaustive",
                    "compute_mode_variant_exhaustive_copy",
                    "compute_mode_nonvariant_control_hidden",
                ],
            },
            {
                "id": "compute_mode_precedence",
                "statement": "Execution-profile precedence remains run > prompt > user > product independently of prompt-copy variant selection",
                "status": "PASS" if precedence else "FAIL",
                "required_evidence_class": "browser_runtime_observed",
                "observation_ids": [
                    "compute_mode_run_override_precedence",
                    "compute_mode_run_override_clear",
                ],
            },
        ],
        "observations": observations,
    }

def build_failure_receipt(subject: dict[str, object], exc: Exception) -> dict[str, object]:
    observation_id = "compute_mode_browser_exception"
    return {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": "FAIL",
        "evidence_class": "browser_runtime_observed",
        "subject": subject,
        "environment": _environment(),
        "claims": [
            {
                "id": "compute_mode_browser_execution",
                "statement": "Compute Mode browser proof completed without an unhandled runtime exception",
                "status": "FAIL",
                "required_evidence_class": "browser_runtime_observed",
                "observation_ids": [observation_id],
            }
        ],
        "observations": [
            {
                "id": observation_id,
                "event": "Compute Mode browser proof raised a runtime exception",
                "occurred": True,
                "passed": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        ],
    }


def write_receipt(path: Path, receipt: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


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
                    "event": "Efficient header control persists the global execution preference and updates pressed state",
                    "occurred": True,
                    "passed": bool(switch_ok),
                    "state": switched,
                }
            )

            expected_canonical = page.evaluate(
                "PROMPTS.find(p => p.id === 'P07').copyContent"
            )
            expected_efficient = page.evaluate(
                "PROMPTS.find(p => p.id === 'P07').compiledEffectivePrompts.efficient"
            )
            card = page.locator('.prompt-card[data-prompt-id="P07"]')
            card.scroll_into_view_if_needed()
            card.locator('.prompt-copy-btn').click()
            page.wait_for_timeout(240)
            global_efficient_clipboard = canonical(page.evaluate("navigator.clipboard.readText()"))
            observations.append(
                {
                    "id": "compute_mode_global_efficient_canonical_copy",
                    "event": "Global Efficient execution preference does not silently shorten P07 card Copy",
                    "occurred": True,
                    "passed": global_efficient_clipboard == canonical(expected_canonical),
                    "actual_length": len(global_efficient_clipboard),
                    "expected_length": len(canonical(expected_canonical)),
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
                    "event": "Efficient global execution preference survives reload",
                    "occurred": True,
                    "passed": bool(
                        persisted["stored"] == "efficient"
                        and persisted["efficient"] == "true"
                    ),
                    "state": persisted,
                }
            )

            card = page.locator('.prompt-card[data-prompt-id="P07"]')
            card.scroll_into_view_if_needed()
            card.locator('.prompt-open-btn').click()
            variant_control = page.locator('#promptDetail [data-prompt-variant-control="P07"]')
            variant_control.wait_for(state="visible")
            exhaustive_button = variant_control.locator('[data-prompt-variant="exhaustive"]')
            efficient_button = variant_control.locator('[data-prompt-variant="efficient"]')
            prompt_content = page.locator('#promptDetail .pd-section').filter(has_text='Prompt Content').locator('pre')
            default_variant_ok = (
                exhaustive_button.get_attribute('aria-pressed') == 'true'
                and efficient_button.get_attribute('aria-pressed') == 'false'
                and canonical(prompt_content.inner_text()) == canonical(expected_canonical)
            )
            observations.append(
                {
                    "id": "compute_mode_variant_default_exhaustive",
                    "event": "P07 detail lazily exposes a prompt-variant selector whose default Exhaustive preview is the full canonical prompt",
                    "occurred": True,
                    "passed": bool(default_variant_ok),
                    "expected_length": len(canonical(expected_canonical)),
                    "actual_length": len(canonical(prompt_content.inner_text())),
                }
            )

            efficient_button.click()
            page.wait_for_timeout(100)
            variant_state = page.evaluate(
                """() => ({
                  overrides: JSON.parse(localStorage.getItem('promptKit.computeMode.promptOverrides.v1') || '{}'),
                  efficientPressed: document.querySelector('[data-prompt-variant="efficient"]').getAttribute('aria-pressed'),
                  exhaustivePressed: document.querySelector('[data-prompt-variant="exhaustive"]').getAttribute('aria-pressed')
                })"""
            )
            efficient_preview = canonical(prompt_content.inner_text())
            observations.append(
                {
                    "id": "compute_mode_variant_efficient_selection",
                    "event": "Explicit P07 Efficient selection stores one sparse prompt override and switches the visible prompt preview",
                    "occurred": True,
                    "passed": bool(
                        variant_state["overrides"].get("P07") == "efficient"
                        and variant_state["efficientPressed"] == "true"
                        and variant_state["exhaustivePressed"] == "false"
                        and efficient_preview == canonical(expected_efficient)
                    ),
                    "actual_length": len(efficient_preview),
                    "expected_length": len(canonical(expected_efficient)),
                }
            )

            page.locator('#promptDetailCopy').click()
            page.wait_for_timeout(240)
            efficient_clipboard = canonical(page.evaluate("navigator.clipboard.readText()"))
            observations.append(
                {
                    "id": "compute_mode_variant_efficient_copy",
                    "event": "Explicit P07 Efficient prompt choice copies the Efficient compiled variant",
                    "occurred": True,
                    "passed": efficient_clipboard == canonical(expected_efficient),
                    "actual_length": len(efficient_clipboard),
                    "expected_length": len(canonical(expected_efficient)),
                }
            )

            exhaustive_button = page.locator('#promptDetail [data-prompt-variant="exhaustive"]')
            exhaustive_button.click()
            page.wait_for_timeout(100)
            reset_state = page.evaluate(
                """() => ({
                  overrides: JSON.parse(localStorage.getItem('promptKit.computeMode.promptOverrides.v1') || '{}'),
                  exhaustivePressed: document.querySelector('[data-prompt-variant="exhaustive"]').getAttribute('aria-pressed')
                })"""
            )
            exhaustive_preview = canonical(prompt_content.inner_text())
            observations.append(
                {
                    "id": "compute_mode_variant_reset_exhaustive",
                    "event": "Selecting Exhaustive clears the P07 sparse override and restores the full canonical preview",
                    "occurred": True,
                    "passed": bool(
                        "P07" not in reset_state["overrides"]
                        and reset_state["exhaustivePressed"] == "true"
                        and exhaustive_preview == canonical(expected_canonical)
                    ),
                    "actual_length": len(exhaustive_preview),
                    "expected_length": len(canonical(expected_canonical)),
                }
            )

            page.locator('#promptDetailCopy').click()
            page.wait_for_timeout(240)
            exhaustive_clipboard = canonical(page.evaluate("navigator.clipboard.readText()"))
            observations.append(
                {
                    "id": "compute_mode_variant_exhaustive_copy",
                    "event": "P07 Exhaustive prompt choice copies the full canonical prompt",
                    "occurred": True,
                    "passed": exhaustive_clipboard == canonical(expected_canonical),
                    "actual_length": len(exhaustive_clipboard),
                    "expected_length": len(canonical(expected_canonical)),
                }
            )

            run_state = page.evaluate(
                """() => {
                  PromptKitComputeMode.setRunOverride('exhaustive');
                  const resolved = PromptKitComputeMode.resolveProfile({
                    runOverride: PromptKitComputeMode.getRunOverride(),
                    userDefault: PromptKitComputeMode.getUserDefault()
                  });
                  return {
                    runOverride: PromptKitComputeMode.getRunOverride(),
                    resolved: resolved.profile,
                    resolvedFrom: resolved.resolved_from,
                    storedUser: localStorage.getItem('promptKit.computeMode.userDefault.v1')
                  };
                }"""
            )
            observations.append(
                {
                    "id": "compute_mode_run_override_precedence",
                    "event": "Explicit run override resolves Exhaustive ahead of the persisted Efficient user preference without changing prompt-copy variant state",
                    "occurred": True,
                    "passed": bool(
                        run_state["runOverride"] == "exhaustive"
                        and run_state["resolved"] == "exhaustive"
                        and run_state["resolvedFrom"] == "explicit_run_override"
                        and run_state["storedUser"] == "efficient"
                    ),
                    "state": run_state,
                }
            )

            final_state = page.evaluate(
                """() => {
                  PromptKitComputeMode.clearRunOverride();
                  const resolved = PromptKitComputeMode.resolveProfile({
                    userDefault: PromptKitComputeMode.getUserDefault()
                  });
                  return {
                    runOverride: PromptKitComputeMode.getRunOverride(),
                    resolved: resolved.profile,
                    resolvedFrom: resolved.resolved_from,
                    storedUser: localStorage.getItem('promptKit.computeMode.userDefault.v1')
                  };
                }"""
            )
            observations.append(
                {
                    "id": "compute_mode_run_override_clear",
                    "event": "Clearing the run override restores the Efficient user execution preference",
                    "occurred": True,
                    "passed": bool(
                        final_state["runOverride"] is None
                        and final_state["resolved"] == "efficient"
                        and final_state["resolvedFrom"] == "user_default"
                        and final_state["storedUser"] == "efficient"
                    ),
                    "state": final_state,
                }
            )

            page.locator('#promptDetail .prompt-detail-close').click()
            plain_card = page.locator('.prompt-card[data-prompt-id="P00"]')
            plain_card.scroll_into_view_if_needed()
            plain_card.locator('.prompt-open-btn').click()
            nonvariant_count = page.locator('#promptDetail [data-prompt-variant-control]').count()
            observations.append(
                {
                    "id": "compute_mode_nonvariant_control_hidden",
                    "event": "Prompt detail without compiled variants renders no per-prompt variant selector",
                    "occurred": True,
                    "passed": nonvariant_count == 0,
                    "count": nonvariant_count,
                }
            )

            page.locator('#promptDetail .prompt-detail-close').click()
            card = page.locator('.prompt-card[data-prompt-id="P07"]')
            card.scroll_into_view_if_needed()
            card.locator('.prompt-open-btn').click()
            page.locator('#promptDetail [data-prompt-variant-control="P07"]').wait_for(state="visible")
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

    try:
        observations = observe(args.port, screenshot)
    except Exception as exc:
        receipt = build_failure_receipt(subject, exc)
        write_receipt(receipt_path, receipt)
        print(
            json.dumps(
                {
                    "verdict": "FAIL",
                    "receipt": str(receipt_path),
                    "screenshot": str(screenshot),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 1

    receipt = build_receipt(subject, observations)
    write_receipt(receipt_path, receipt)
    print(
        json.dumps(
            {
                "verdict": receipt["verdict"],
                "receipt": str(receipt_path),
                "screenshot": str(screenshot),
                "observations": observations,
            }
        )
    )
    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
