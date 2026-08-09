#!/usr/bin/env python3
"""Fail-closed validator for Prompt Kit profile-qualified routing."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/prompt-kit-profile-qualified-routing.v1.json"
MANIFEST = ROOT / "harness/manifest.v1.json"
WORKFLOWS = ROOT / "harness/workflows.v1.json"
SKILL = ROOT / ".ai/skills/technician-prompt-kit-acquisition/SKILL.md"
RESOLVER = ROOT / "scripts/resolve_prompt_kit_profile_route.py"
PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
LAUNCHER_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/"

EXPECTED_RELATED = {
    "agent_switchboard": {
        "full_name": "EndeavorEverlasting/AgentSwitchboard",
        "relationship": "repository-family profile and machine-path authority",
        "mutation_allowed": False,
        "consumed_surfaces": [
            ".ai/harness/repository-family.registry.json",
            "Get-AgentSwitchboard-MachineProfile.cmd",
            "tooling/profiles/windows/Get-AgentSwitchboardMachineProfile.ps1",
        ],
        "boundary": "Use AgentSwitchboard evidence to qualify the host profile and path conventions. Triage remains authoritative for Prompt Kit behavior, acquisition, artifacts, validators, and Triage repository mutations.",
    }
}
EXPECTED_RESOLUTION_ORDER = [
    "active repository",
    "current host profile",
    "current shell/execution surface",
    "target profile",
    "user intent",
    "profile-associated repository path",
    "command or cross-device handoff",
]
EXPECTED_PATH_RESOLUTION = {
    "explicit_triage_path_environment": "WEB_EXCEL_TRIAGE_REPO",
    "verified_existing_checkout": "A checkout whose origin resolves to EndeavorEverlasting/web-excel-repair-triage.",
    "related_repo_sibling": "When a verified AGENT_SWITCHBOARD_REPO is available, use its parent directory plus web-excel-repair-triage as the preferred sibling destination.",
    "windows_default": r"%USERPROFILE%\dev\web-excel-repair-triage",
    "windows_default_command_expression": r"Join-Path $env:USERPROFILE 'dev\web-excel-repair-triage'",
    "android_default": "$HOME/web-excel-repair-triage",
    "android_default_command_expression": '"$HOME/web-excel-repair-triage"',
    "rule": "Never substitute a remembered user-specific absolute path for profile/path evidence.",
}
EXPECTED_PROFILES = {
    "windows": {
        "shell": "powershell",
        "execution_surface": "windows-powershell",
        "normal_use_command_template": "Start-Process '<public_prompt_kit_url>'",
        "install_command_template": "Start-Process '<public_launcher_url>'",
        "local_app_entry_point": "Open-Latest-PromptKit.cmd",
        "forbidden_tokens": ["termux-open-url", "command -v", "/dev/null", "pkg install", "$PREFIX"],
    },
    "android": {
        "shell": "termux-bash",
        "execution_surface": "android-termux",
        "normal_use_command_template": "termux-open-url '<public_prompt_kit_url>'",
        "install_command_template": "termux-open-url '<public_launcher_url>'",
        "editable_checkout_default": "$HOME/web-excel-repair-triage",
        "forbidden_tokens": ["Start-Process", "Set-Location", "%USERPROFILE%"],
    },
    "browser": {
        "shell": "browser",
        "execution_surface": "browser",
        "normal_use_command_template": "<public_prompt_kit_url>",
        "install_command_template": "<public_launcher_url>",
        "repository_path_required": False,
    },
}
EXPECTED_HANDOFF_RULES = [
    "Qualify the current host profile and shell before emitting a shell command.",
    "If target profile differs from current host profile, emit a HANDOFF with the target execution surface and do not emit a target-shell command as runnable in the current shell.",
    "A Windows PowerShell prompt is positive evidence for the Windows execution surface and negative evidence for direct Termux execution.",
    "An Android target requested from Windows must remain an Android-device action; repairing or invoking WSL is not a substitute.",
    "Normal browser use does not require a repository path, clone, or terminal.",
    "Local launcher or editable-checkout work must use the profile-associated Triage path rather than an unrelated repository path.",
    "Browser-only execution cannot perform local-app or editable-checkout intent; classify those requests as BLOCKED or hand them off to a supported local profile.",
]
EXPECTED_PROOF_CEILING = "Static repository-family relationship, profile/path qualification, shell-safe route selection, and handoff classification only. No device command execution, browser opening, checkout existence, Git authentication, or runtime success is proven."


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
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileRoutingError(message)


def validate_contract_payload(contract: dict) -> None:
    require(contract.get("schema_version") == "prompt-kit-profile-qualified-routing/v1", "wrong contract schema")
    require(contract.get("repository") == "EndeavorEverlasting/web-excel-repair-triage", "active repository must remain Triage")
    require(contract.get("default_branch") == "main", "default branch must remain main")
    require(
        contract.get("active_repository_rule")
        == "The active repository remains EndeavorEverlasting/web-excel-repair-triage. Related repositories may supply profile or path evidence but may not become the mutation target implicitly.",
        "active repository rule drifted",
    )
    require(contract.get("related_repositories") == EXPECTED_RELATED, "related repository contract drifted")
    require(contract.get("resolution_order") == EXPECTED_RESOLUTION_ORDER, "resolution order drifted")
    require(contract.get("path_resolution") == EXPECTED_PATH_RESOLUTION, "path resolution contract drifted")
    require(contract.get("profiles") == EXPECTED_PROFILES, "profile shell/surface contract drifted")
    require(contract.get("handoff_rules") == EXPECTED_HANDOFF_RULES, "handoff rules drifted")
    require(contract.get("public_prompt_kit_url") == PUBLIC_URL, "public Prompt Kit URL drifted")
    require(contract.get("public_launcher_url") == LAUNCHER_URL, "public launcher URL drifted")
    require(contract.get("proof_ceiling") == EXPECTED_PROOF_CEILING, "proof ceiling drifted")


def validate_contract() -> dict:
    contract = load_object(CONTRACT)
    validate_contract_payload(contract)
    return contract


def validate_routes() -> None:
    module = load_resolver()
    require(module.PUBLIC_URL == PUBLIC_URL, "resolver Prompt Kit URL drifted from contract")
    require(module.LAUNCHER_URL == LAUNCHER_URL, "resolver launcher URL drifted from contract")

    windows_asb = r"C:\Users\Example\Desktop\Dev\AgentSwitchboard"
    route = module.resolve_route(
        "windows", "powershell", "windows", "local-app",
        agent_switchboard_repo=windows_asb,
        main_sha="4fd03b5dcc42d7842890a4d3b217cf00dc9c1341",
    )
    require(route.status == "ROUTED", "Windows local-app route did not route")
    require(route.associated_repo_path == r"C:\Users\Example\Desktop\Dev\web-excel-repair-triage", "Windows sibling path did not follow the related repository path")
    require(route.command and "Open-Latest-PromptKit.cmd" in route.command, "Windows local-app route did not use the repo launcher")
    for forbidden in ("termux-open-url", "command -v", "/dev/null", "pkg install", "$PREFIX"):
        require(forbidden not in route.command, f"Windows command leaked {forbidden!r}")

    quoted_path = module.resolve_route(
        "windows", "powershell", "windows", "edit",
        triage_repo=r"C:\Users\O'Brien\web-excel-repair-triage",
    )
    require("O''Brien" in (quoted_path.command or ""), "PowerShell repository path is not single-quote escaped")

    default_windows = module.resolve_route("windows", "powershell", "windows", "edit")
    require("$env:USERPROFILE" in (default_windows.command or ""), "Windows default path is not natively expandable")
    require("%USERPROFILE%" not in (default_windows.command or ""), "Windows command contains literal CMD-style default path")

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
    require(PUBLIC_URL in android.command, "Android use route drifted from Prompt Kit URL")

    android_install = module.resolve_route("android", "termux-bash", "android", "install", main_sha="abcdef123456")
    require(LAUNCHER_URL in (android_install.command or ""), "Android install route must use the phone launcher")
    require("/prompt-kit/" not in (android_install.command or ""), "Android install route incorrectly uses direct Prompt Kit path")

    default_android = module.resolve_route("android", "termux-bash", "android", "edit")
    require('"$HOME/web-excel-repair-triage"' in (default_android.command or ""), "Android default path is not natively expandable")

    quoted_android = module.resolve_route(
        "android", "termux-bash", "android", "edit",
        triage_repo="/data/data/com.termux/files/home/O'Brien/web-excel-repair-triage",
    )
    require("'\"'\"'" in (quoted_android.command or ""), "Android repository path is not POSIX single-quote escaped")

    browser_edit = module.resolve_route("browser", "browser", "browser", "edit")
    require(browser_edit.status == "BLOCKED", "browser-only edit must fail closed")
    require(browser_edit.command is None, "blocked browser edit must not emit a command")

    mismatch = module.resolve_route("windows", "termux-bash", "windows", "use")
    require(mismatch.status == "BLOCKED", "Host/shell mismatch must fail closed")
    require(mismatch.command is None, "Blocked shell mismatch must not emit a command")

    try:
        module.resolve_route("windows", "powershell", "windows", "use", main_sha="abc';Write-Host PWNED")
    except ValueError:
        pass
    else:
        raise ProfileRoutingError("malformed main_sha was accepted")


def validate_repository_wiring() -> None:
    manifest = load_object(MANIFEST)
    domain = manifest.get("domain_contracts", {}).get("prompt_kit_profile_qualified_routing", {})
    require(domain.get("contract") == "harness/contracts/prompt-kit-profile-qualified-routing.v1.json", "manifest contract registration missing")
    require(domain.get("resolver") == "scripts/resolve_prompt_kit_profile_route.py", "manifest resolver registration missing")
    require(domain.get("validator") == "scripts/validate_prompt_kit_profile_routing.py", "manifest validator registration missing")
    require(domain.get("contract_tests") == "tests/test_prompt_kit_profile_routing.py", "manifest test registration missing")
    require(domain.get("human_workflow") == "harness/workflows/prompt-kit-profile-qualified-routing.md", "manifest human workflow registration missing")
    require(domain.get("skill") == ".ai/skills/technician-prompt-kit-acquisition/SKILL.md", "manifest skill ownership missing")
    require(domain.get("operator_report") == "harness/reports/PROMPT_KIT_PROFILE_ROUTING.md", "manifest report ownership missing")
    require(domain.get("artifact_id") == "prompt-kit-profile-routing-report", "manifest artifact ownership missing")
    require(domain.get("related_profile_authority") == "EndeavorEverlasting/AgentSwitchboard", "manifest related profile authority drifted")

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
    except (ProfileRoutingError, ValueError) as exc:
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
