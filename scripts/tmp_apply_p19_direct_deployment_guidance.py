#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "registry/prompts/prompt-overrides.v1.json"
BASE_PROMPTS = ROOT / "docs/prompts.json"
FOCUSED_TEST = ROOT / "tests/test_prompt_kit_mainline_delivery.py"

P19_COPY = r'''EXECUTE THE INSTALLATION OR DEPLOYMENT WORKFLOW SAFELY, GUIDE ANY REQUIRED OPERATOR ACTION DIRECTLY, AND CAPTURE PROOF.
Repo: xyz_repo_or_path
Environment: xyz_environment
Targets: xyz_targets
Package, service, or app: xyz_package
Owned scope: xyz_owned_scope
Forbidden scope: xyz_forbidden_scope

MISSION
Use repo-owned installers, launchers, deployment scripts, manifests, APIs, and rollback procedures to install, configure, upgrade, or deploy the requested software, service, or app. Make the workflow idempotent and evidence-bound. When the agent can safely execute a step with available authority, execute it. When a browser, admin console, desktop UI, mobile UI, device, or other protected surface requires the operator to act, give the direct next interaction instead of making the operator hunt.

0. RECOVER CONTEXT + PIN THE DEPLOYMENT SUBJECT
- Recover the app/product, environment, target, current operator screen, prior errors, intended generation, accepted/rejected deployment state, and earlier course corrections from accessible chat/handoff/repository evidence before asking the operator to repeat them.
- Resolve the exact deployment subject before mutation or guidance: repository/project/app identity, target environment, commit SHA when applicable, build/artifact/version/deployment ID, and source/generation markers that distinguish the intended candidate.
- If evidence identifies a known wrong, stale, legacy, or superseded generation, record the rejection marker and do not deploy, bind, or certify that candidate.
- Do not treat a project name, deployment slot, or the word `latest` as exact candidate identity when multiple generations can exist.
- If the current evidence cannot distinguish consequential candidates, fail closed at that exact identity gate rather than guessing.

1. CHOOSE THE EXECUTION SURFACE
- Prefer a safe authorized repo-owned CLI, API, launcher, or deployment helper for agent-capable work because it is usually more deterministic and auditable than focus-dependent automation.
- If the operator must act in a graphical surface, stay in that surface and guide it directly. Do not bounce the operator to a different tool merely because the agent knows that tool better.
- Distinguish browser/web console, desktop/admin UI, mobile UI, device/physical action, and CLI/API steps. Never present one surface's controls as though they belong to another.
- Start from the operator's actual current screen or state when known; do not reset the flow to a homepage or root menu unless that reset is required.

2. DIRECT OPERATOR INTERFACE GUIDANCE — NO HUNTING
When a user-only click, tap, type, select, scan, or physical action is required, make the instruction executable from the visible interface. For each such step provide:
- DIRECT ENTRY POINT: the exact URL/deep link when known from evidence, or the precise product/site area and first navigation control when a direct URL is not established.
- CONTROL: the exact visible button, tab, menu, field, row, link, or selector label.
- RELATIVE LOCATION: anchor the control to something visible, for example `upper-right toolbar`, `left sidebar under Deployments`, `row action menu beside the active version`, or `dialog footer next to Cancel`.
- ACTION: one concrete action — click, tap, select, type, paste, scan, or confirm — including the exact value when evidence establishes it.
- EXPECTED STATE: the screen, label, status, selected value, dialog, URL, or other immediate state that should appear after the action.
- CONTINUATION: when the next step depends on the resulting UI state, give one operator action at a time and request only the resulting screenshot, visible state, or exact error needed to continue. Resume from that observed state instead of replaying the whole deployment flow.

Do not substitute vague navigation such as `find`, `look for`, `go to settings`, `open the deployment page`, `navigate to deployments`, or `click the deploy button` without the direct route, visible control label, relative location, and expected state. A direction that still forces the operator to search the interface is incomplete.
If the supplied screenshot or UI text disagrees with remembered product layout, trust the observed interface. Do not invent a missing label or location; use the visible anchors to provide the smallest evidence-backed alternate route and state any remaining uncertainty.
Clearly distinguish `AGENT ACTION` from `OPERATOR ACTION` so work is not silently pushed back to the user.
For deterministic consecutive UI steps whose controls and expected states are already evidenced, a short ordered sequence is allowed. Otherwise advance one state-dependent operator action at a time.

3. VERSION / GENERATION BINDING — PREVENT WRONG-APP DEPLOYS
- Before deploy, redeploy, promote, or version selection, confirm that the exact intended candidate is the one being selected or bound to the target.
- Preserve known negative markers for the wrong generation when the conversation or repository provides them; post-deploy acceptance should prove the intended generation and, where practical, reject the known wrong one.
- Bind every deployment claim to the exact commit/build/artifact/version/deployment identity observed. `Deployment succeeded` without subject identity is not enough when multiple candidates can exist.
- After deployment, verify at least one target-facing marker that distinguishes the intended generation when the product exposes one: version/commit text, route, screen content, schema marker, behavior, or another repository-defined acceptance signal.

4. DEPLOYMENT SAFETY
- inspect current state before mutation
- use approved sources and verified packages
- preserve existing configuration unless migration is intended
- handle existing directories, packages, services, credentials, and prior partial state idempotently
- bound waits and retries
- avoid terminal-focus automation when a direct command or API exists
- do not mutate personal data, saves, accounts, unrelated environments, or forbidden targets
- do not leave staging payloads, secrets, credentials, or temporary artifacts behind
- record rollback, uninstall, previous-version, or traffic-reversal steps appropriate to the deployment surface
- distinguish package copied, request accepted, deployment/version created, target binding changed, health passed, and behavior observed

5. FAILURE RECOVERY WITHOUT RESTARTING THE WHOLE FLOW
- When an action fails or the interface differs, capture the exact current state, visible labels, error text, candidate identity, and highest proven deployment gate.
- Repair the nearest failed gate and continue from the proven floor. Do not make the operator repeat already successful navigation or redeploy already-proven components unless later evidence invalidated that state.
- If a prior instruction was wrong, explicitly replace it and continue from the operator's current screen. Do not layer a second contradictory route on top of the first.
- Treat repeated course correction as evidence that a route, label, identity, or proof assumption is under-specified; resolve that assumption before issuing more steps.

6. DEPLOYMENT PROOF LADDER
Keep proof levels separate and claim only the highest level actually observed:
1. candidate/package prepared or copied
2. deployment command/request accepted
3. deployment object/version/build exists
4. intended exact version/generation is bound to the intended target
5. configuration/health/log/smoke checks pass
6. user-facing behavior is observed in the real target surface
Static, CI, repository, or API evidence must not silently become browser/device/production/operator acceptance. If the final live surface is inaccessible, name the exact operator observation still required.

VALIDATION
Validate exact subject identity, package/version, deployment/target binding, service/process state, configuration, health endpoint or smoke behavior, logs, cleanup, rollback readiness, and the strongest available target-facing marker. Re-read the current deployment state before the final claim so a stale selection, wrong generation, or moved target is not certified.

FINAL RESPONSE
- deployment subject identity:
- environment and targets:
- execution surface:
- state detected before:
- AGENT ACTIONS completed:
- OPERATOR ACTION NOW: <direct entry point> -> <visible control + relative location> -> <exact action>
- expected immediate state:
- changes applied / resulting versions or services:
- proof artifacts or logs:
- validation:
- cleanup:
- rollback:
- proof achieved / proof ceiling:
- next continuation from the observed state:

Perform the deployment when the environment and authority permit. If an operator-only gate remains, give the direct executable interaction rather than generic navigation. Never make the operator hunt for the control you mean.'''

P19_FIELDS = {
    "sprintRole": "Install or deploy idempotently with exact subject identity, direct operator interface guidance, and proof",
    "useWhen": "Software, services, agents, packages, or apps must be installed, configured, upgraded, or deployed, including when a human must navigate browser, admin-console, desktop, mobile, device, or other live deployment controls.",
    "inspectFirst": "Recoverable chat/handoff context; current operator screen; repo-owned installers, launchers, manifests, APIs, and rollback rules; target/environment; exact candidate identity (commit/build/artifact/version/deployment ID); current deployment state; available execution surfaces; known wrong/legacy generation markers.",
    "expectedOutput": "Applied deployment or direct operator-ready UI actions with a direct entry point, exact visible control, relative location, expected state, exact candidate/version binding, health proof, cleanup/rollback record, and continuation from the observed state.",
    "nextStep": "Continue from the highest proven deployment gate. Use P08 only when live behavior beyond deployment still needs validation; use P12 only after deployment/health proof and the operator-acceptance ceiling are explicit.",
    "proofGate": "The exact deployment subject/version is bound to the intended target; agent-run steps have current evidence; every required user-only UI step names the direct entry point, visible control, relative location, action, and expected state; wrong/legacy generation is excluded when evidence defines it; and live behavior is claimed only when the real target surface was observed.",
    "copyContent": P19_COPY,
    "keywords": [
        "deploy", "install", "installation", "deployment", "setup", "environment", "launch",
        "deployment guidance", "deployment ui", "browser deploy", "admin console", "operator action",
        "deployment version", "release target", "direct entry point"
    ],
}

P13_ROUTE = (
    "- If the recurrence is deployment/install execution or operator navigation through a live deployment surface, "
    "route the specialist repair to P19. Keep recurrence ownership here; do not absorb P19's direct-entrypoint, "
    "interface-navigation, version-binding, or deployment-proof doctrine into P13."
)
P13_ROUTE_ANCHOR = "- If the recurrence is a questionable done/closed/handoff claim"

TEST_METHOD = r'''
    def test_p19_gives_direct_operator_deployment_guidance_without_hunting(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p19 = next(item for item in payload["overrides"] if item["id"] == "P19")
        copy = p19["copyContent"]
        for phrase in (
            "RECOVER CONTEXT + PIN THE DEPLOYMENT SUBJECT",
            "DIRECT OPERATOR INTERFACE GUIDANCE — NO HUNTING",
            "DIRECT ENTRY POINT",
            "exact visible button, tab, menu, field, row, link, or selector label",
            "RELATIVE LOCATION",
            "EXPECTED STATE",
            "one operator action at a time",
            "Do not substitute vague navigation",
            "VERSION / GENERATION BINDING — PREVENT WRONG-APP DEPLOYS",
            "highest proven deployment gate",
            "DEPLOYMENT PROOF LADDER",
            "OPERATOR ACTION NOW",
            "Never make the operator hunt",
        ):
            self.assertIn(phrase, copy)
        self.assertIn("browser", p19["useWhen"])
        self.assertIn("current operator screen", p19["inspectFirst"])
        self.assertIn("direct entry point", p19["expectedOutput"])
        self.assertIn("visible control", p19["proofGate"])
        self.assertIn("wrong/legacy generation", p19["proofGate"])
        self.assertLess(len(copy), 12000)

'''
TEST_ANCHOR = "    def test_p65_can_route_repeated_friction_without_browser_finder(self):\n"
P13_TEST_NEEDLE = '            "route certification to P48",\n'
P13_TEST_INSERT = '            "route the specialist repair to P19",\n'


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify() -> None:
    payload = load_json(OVERRIDES)
    by_id = {item["id"]: item for item in payload["overrides"]}
    p19 = by_id.get("P19")
    if p19 is None:
        raise SystemExit("P19 override missing")
    for key, value in P19_FIELDS.items():
        if p19.get(key) != value:
            raise SystemExit(f"P19 field mismatch: {key}")
    p13 = by_id.get("P13")
    if p13 is None or P13_ROUTE not in p13.get("copyContent", ""):
        raise SystemExit("P13->P19 specialist route missing")
    tests = FOCUSED_TEST.read_text(encoding="utf-8")
    if "test_p19_gives_direct_operator_deployment_guidance_without_hunting" not in tests:
        raise SystemExit("focused P19 regression missing")
    if P13_TEST_INSERT.strip() not in tests:
        raise SystemExit("focused P13 routing assertion missing")
    print("P19_DIRECT_DEPLOYMENT_GUIDANCE_VERIFY_PASS")


def apply() -> None:
    payload = load_json(OVERRIDES)
    base = load_json(BASE_PROMPTS)
    base_p19 = next((item for item in base if item.get("id") == "P19"), None)
    if base_p19 is None:
        raise SystemExit("base P19 not found in docs/prompts.json")

    overrides = payload.get("overrides")
    if not isinstance(overrides, list):
        raise SystemExit("prompt overrides must be a list")
    by_id = {item.get("id"): item for item in overrides}

    p19 = dict(base_p19)
    p19.update(P19_FIELDS)
    existing_index = next((i for i, item in enumerate(overrides) if item.get("id") == "P19"), None)
    if existing_index is None:
        overrides.append(p19)
    else:
        overrides[existing_index] = p19
    overrides.sort(key=lambda item: int(str(item.get("seq", "9999"))))

    p13 = next((item for item in overrides if item.get("id") == "P13"), None)
    if p13 is None:
        raise SystemExit("P13 override missing")
    copy = str(p13.get("copyContent", ""))
    if P13_ROUTE not in copy:
        if P13_ROUTE_ANCHOR not in copy:
            raise SystemExit("P13 specialist routing anchor missing")
        copy = copy.replace(P13_ROUTE_ANCHOR, P13_ROUTE + "\n" + P13_ROUTE_ANCHOR, 1)
        p13["copyContent"] = copy

    write_json(OVERRIDES, payload)

    tests = FOCUSED_TEST.read_text(encoding="utf-8")
    if "test_p19_gives_direct_operator_deployment_guidance_without_hunting" not in tests:
        if TEST_ANCHOR not in tests:
            raise SystemExit("focused-test insertion anchor missing")
        tests = tests.replace(TEST_ANCHOR, TEST_METHOD + TEST_ANCHOR, 1)
    if P13_TEST_INSERT.strip() not in tests:
        if P13_TEST_NEEDLE not in tests:
            raise SystemExit("P13 routing test anchor missing")
        tests = tests.replace(P13_TEST_NEEDLE, P13_TEST_NEEDLE + P13_TEST_INSERT, 1)
    FOCUSED_TEST.write_text(tests, encoding="utf-8")
    verify()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify()
    else:
        apply()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
