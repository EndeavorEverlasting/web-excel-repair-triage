#!/usr/bin/env python3
"""Fail-closed validator for Prompt Kit profile-qualified routing."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/prompt-kit-profile-qualified-routing.v1.json"
MANIFEST = ROOT / "harness/manifest.v1.json"
WORKFLOWS = ROOT / "harness/workflows.v1.json"
SKILL = ROOT / ".ai/skills/technician-prompt-kit-acquisition/SKILL.md"
RESOLVER = ROOT / "scripts/resolve_prompt_kit_profile_route.py"


class ProfileRoutingError(RuntimeError):
    pass


def load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileRoutingError(f"Unable to load {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProfileRoutingError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def load_resolver():
    spec = importlib.util.spec_from_file_location("prompt_kit_profile_route", RESOLVER)
    if spec is None or spec.loader is None:
        raise ProfileRoutingError("Unable to load profile route resolver")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileRoutingError(message)


def validate_contract() -> dict:
    contract = load_object(CONTRACT)
    require(contract.get("schema_version") == "prompt-kit-profile-qualified-routing/v1", "wrong contract schema")
    require(contract.get("repository") == "EndeavorEverlasting/web-excel-repair-triage", "active repository must remain Triage")
    related = contract.get("related_repositories", {}).get("agent_switchboard", {})
    require(related.get("full_name") == "EndeavorEverlasting/AgentSwitchboard", "AgentSwitchboard family relation is missing")
    require(related.get("mutation_allowed") is False, "related AgentSwitchboard repo must remain read-only from this Triage sprint")
    consumed = set(related.get("consumed_surfaces", []))
    require("Get-AgentSwitchboard-MachineProfile.cmd" in consumed, "machine-profile entry point is not registered")
    require("tooling/profiles/windows/Get-AgentSwitchboardMachineProfile.ps1" in consumed, "machine-profile implementation surface is not registered")
    windows = contract.get("profiles", {}).get("windows", {})
    forbidden = set(windows.get("forbidden_tokens", []))
    for token in ("termux-open-url", "command -v", "/dev/null", "pkg install"):
        require(token in forbidden, f"Windows route must forbid {token!r}")
    return contract


def validate_routes() -> None:
    module = load_resolver()
    windows_asb = r"C:\Users\Example\Desktop\Dev\AgentSwitchboard"
    route = module.resolve_route(
        "windows", "powershell", "windows", "local-app",
        agent_switchboard_repo=windows_asb,
        main_sha="4fd03b5dcc42d7842890a4d3b217cf00dc9c1341",
    )
    require(route.status == "ROUTED", "Windows local-app route did not route")
    require(route.associated_repo_path == r"C:\Users\Example\Desktop\Dev\web-excel-repair-triage", "Windows sibling path did not follow the related repository path")
    require(route.command and "Open-Latest-PromptKit.cmd" in route.command, "Windows local-app route did not use the repo launcher")
    for forbidden in ("termux-open-url", "command -v", "/dev/null", "pkg install"):
        require(forbidden not in route.command, f"Windows command leaked {forbidden!r}")

    handoff = module.resolve_route(
        "windows", "powershell", "android", "use",
        agent_switchboard_repo=windows_asb,
        main_sha="4fd03b5dcc42d7842890a4d3b217cf00dc9c1341",
    )
    require(handoff.status == "HANDOFF", "Android target from Windows must be a handoff")
    require(handoff.command is None, "Cross-profile handoff must not emit Android shell text as a Windows command")
    require(handoff.execution_surface == "android-termux", "Android handoff execution surface is wrong")

    android = module.resolve_route("android", "termux-bash", "android", "use", main_sha="abcdef123456")
    require(android.status == "ROUTED", "Android Termux route did not route")
    require(android.command and android.command.startswith("termux-open-url "), "Android route did not use Termux syntax")

    mismatch = module.resolve_route("windows", "termux-bash", "windows", "use")
    require(mismatch.status == "BLOCKED", "Host/shell mismatch must fail closed")
    require(mismatch.command is None, "Blocked shell mismatch must not emit a command")


def validate_repository_wiring() -> None:
    manifest = load_object(MANIFEST)
    domain = manifest.get("domain_contracts", {}).get("prompt_kit_profile_qualified_routing", {})
    require(domain.get("contract") == "harness/contracts/prompt-kit-profile-qualified-routing.v1.json", "manifest contract registration missing")
    require(domain.get("resolver") == "scripts/resolve_prompt_kit_profile_route.py", "manifest resolver registration missing")
    require(domain.get("validator") == "scripts/validate_prompt_kit_profile_routing.py", "manifest validator registration missing")
    require(domain.get("contract_tests") == "tests/test_prompt_kit_profile_routing.py", "manifest test registration missing")
    require(domain.get("skill") == ".ai/skills/technician-prompt-kit-acquisition/SKILL.md", "manifest skill ownership missing")

    workflows = load_object(WORKFLOWS)
    acquisition = next((w for w in workflows.get("workflows", []) if w.get("id") == "technician-acquisition"), None)
    require(isinstance(acquisition, dict), "technician-acquisition workflow missing")
    joined_scope = "\n".join(acquisition.get("owned_scope", []))
    require("profile-qualified" in joined_scope.lower(), "technician workflow does not own profile-qualified routing")
    require("AgentSwitchboard" in json.dumps(acquisition), "technician workflow does not preserve related-repository awareness")

    skill_text = SKILL.read_text(encoding="utf-8")
    for phrase in (
        "active repository remains Triage",
        "AgentSwitchboard is a related repository",
        "qualify the current host profile",
        "target profile differs",
        "profile-associated Triage path",
    ):
        require(phrase.lower() in skill_text.lower(), f"acquisition skill is missing required guidance: {phrase}")
    require("termux-open-url" in skill_text, "skill must retain the Android Termux route")
    require("Start-Process" in skill_text, "skill must define the Windows browser route")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        contract = validate_contract()
        validate_routes()
        validate_repository_wiring()
    except ProfileRoutingError as exc:
        print(f"Prompt Kit profile-qualified routing: FAIL: {exc}")
        return 1
    if args.summary:
        print(json.dumps({
            "status": "PASS",
            "schema": contract["schema_version"],
            "active_repository": contract["repository"],
            "related_repository": contract["related_repositories"]["agent_switchboard"]["full_name"],
            "profiles": sorted(contract["profiles"]),
            "proof_ceiling": contract["proof_ceiling"],
        }, indent=2))
    else:
        print("Prompt Kit profile-qualified routing: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
