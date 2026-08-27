from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TESTS = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
p92 = next((item for item in payload["prompts"] if item.get("id") == "P92"), None)
if not p92 or p92.get("name") != "Canonical Path Prompt":
    raise SystemExit("P92 Canonical Path Prompt identity not found")

p92["sprintRole"] = (
    "Establish and enforce one repository-owned canonical development checkout and production/use path per supported machine/profile, "
    "derive literal paths from current environment evidence, keep ordinary mutation in development rather than an active production path, resolve material "
    "terminal/shell/kernel/runtime context before path-sensitive commands, prevent duplicate working copies, and separate remote integration from local deployment proof"
)
p92["useWhen"] = (
    "Agents or humans are using, cloning, installing, launching, updating, or modifying a repository and its canonical development or production path is missing, "
    "ambiguous, inconsistent across tools, or varies with OS, user profile, special-folder/cloud state, shell/runtime, or machine profile; especially when a local "
    "production/use path may be actively serving users while development continues, or when GitHub main is current but the workstation checkout/install may be stale."
)
p92["inspectFirst"] = (
    "Current remote/default-branch truth; repository governance and harness entrypoints; existing canonical-path or machine/profile contracts; current working directory "
    "and verified checkout candidates; native OS home/profile and special-folder resolution; cloud roots/redirection when relevant; terminal host, actual shell/interpreter, "
    "kernel/OS/runtime boundary, execution target, and path semantics when command choice depends on them; launcher/installer/updater/worktree contracts; production-use state "
    "including running processes, services, launchers, servers/watchers, scheduled jobs, sync/updater activity, or operator sessions that can consume the path; the repository-owned "
    "promotion/update mechanism and rollback/restart boundary; dirty or unique work; and tests/CI that claim path or deployment readiness."
)
p92["expectedOutput"] = (
    "A canonical-path ledger plus a repo-owned harness contract, PATH INPUT RECEIPT, material EXECUTION CONTEXT RECEIPT, and PROD_USE_STATE that identify the machine/profile "
    "resolution rule, development mutation path, production/use path, optional worktree root, entrypoint, and dev-to-production promotion/update boundary; safe disposition of "
    "noncanonical copies; and separate evidence for remote integration, development freshness, production freshness, and real-entrypoint behavior without exposing active production "
    "consumers to partial development state."
)
p92["nextStep"] = (
    "Resolve current repository, machine/profile, execution-context, and production-use truth; keep ordinary edits in the canonical development checkout or approved worktree; "
    "validate the candidate there; then use the repository-owned promotion/update mechanism to refresh production only at a safe boundary and prove the real entrypoint."
)
p92["proofGate"] = (
    "Exactly one path owner exists per supported profile; literals derive from current environment evidence rather than hard-coded usernames; material execution context fails closed "
    "instead of guessing shell/path semantics; development, production/use, and worktree roles are explicit; the production/use path is not the default development mutation target; "
    "UNKNOWN production use state blocks production mutation but not safe development work; a shared physical dev/prod path is treated as production-impacting; active consumers cannot "
    "observe a partially copied, rebuilt, reset, or otherwise half-promoted candidate; noncanonical copies are diagnosed without destructive cleanup; remote merge is never local deployment "
    "proof; and the strongest safe same-entrypoint check confirms the resolved production version or names the exact runtime blocker."
)

content = p92["copyContent"]

if "5A. EXECUTION CONTEXT RECEIPT BEFORE PATH-SENSITIVE COMMANDS" not in content:
    anchor = (
        "Resolution precedence: tracked canonical-path/profile contract -> authorized machine/profile override -> native home/special-folder/environment resolution -> verified existing-checkout evidence. "
        "Lower-precedence evidence may expose drift but may not silently replace the owner. If current host and target profile differ, route/handoff rather than fabricate a target path locally.\n\n"
        "6. FAIL CLOSED ON PATH DRIFT"
    )
    replacement = (
        "Resolution precedence: tracked canonical-path/profile contract -> authorized machine/profile override -> native home/special-folder/environment resolution -> verified existing-checkout evidence. "
        "Lower-precedence evidence may expose drift but may not silently replace the owner. If current host and target profile differ, route/handoff rather than fabricate a target path locally.\n\n"
        "5A. EXECUTION CONTEXT RECEIPT BEFORE PATH-SENSITIVE COMMANDS\n"
        "When command syntax, path semantics, launcher behavior, or agent/tool availability depends on execution context, record the terminal surface/host, actual shell/interpreter, "
        "kernel/OS/runtime boundary, execution target (local, WSL, container, VM, SSH/remote, or CI), and material path/filesystem semantics. A terminal application is not the shell, "
        "and a shell prompt does not prove the kernel/runtime or target. If these facts materially affect the next mutation and cannot be recovered, set `EXECUTION_CONTEXT=UNKNOWN` and "
        "do not emit a guessed shell-specific or target-specific write command. If host and target differ, route/handoff or use an explicitly target-scoped invocation.\n\n"
        "5B. DEVELOPMENT MUTATION VS ACTIVE PRODUCTION USE\n"
        "Production/use path is a consumer path, not the default development mutation target. Record `PROD_USE_STATE` as ACTIVE, QUIESCED, OFFLINE, or UNKNOWN from current evidence. "
        "ACTIVE includes a process, service, launcher, server/watcher, scheduled job, sync/updater, operator session, or other consumer that can observe the path. UNKNOWN is not idle: it blocks "
        "production-path mutation while safe development work may continue.\n"
        "- When development and production are separate, edit/build/test only in the canonical development checkout or approved worktree, then cross the tracked sync/install/update/promotion boundary. "
        "Do not copy a partially built tree into production or use ad-hoc file edits as deployment.\n"
        "- When development and production resolve to the same physical path, record that relation explicitly. Any write is production-impacting; do not call it a dev-only change. Either the tracked "
        "contract must prove in-place mutation is safe for the current use state, or isolate development before changing files.\n"
        "- Do not `git pull`, reset, rebuild, overwrite, or regenerate files in an ACTIVE production/use path merely because it is local. When consumers could observe files mid-update, use the "
        "repository-native safe boundary: quiescence, staged/atomic or versioned replacement, restart/reload coordination, or an equivalent mechanism that prevents partial candidate state. "
        "Do not invent a deployment mechanism when the repository already owns one.\n"
        "- After promotion/update, resolve the production version from the real entrypoint and preserve the repository-defined restore/rollback path when the update can fail after mutation.\n\n"
        "6. FAIL CLOSED ON PATH DRIFT"
    )
    content = replace_once(content, anchor, replacement, "P92 execution + active-production insertion")

content = replace_once(
    content,
    "- Could a launcher use a stale install while remote main/dev checkout are current?\n",
    "- Could a launcher use a stale install while remote main/dev checkout are current?\n"
    "- Could an ACTIVE or UNKNOWN production consumer observe files while development, sync, build, or update mutates its path?\n"
    "- Could development and production resolve to the same physical directory so a supposedly dev-only write is actually live?\n"
    "- Could the terminal host mask a different shell, kernel/runtime, execution target, or path semantics and make the next command wrong?\n",
    "P92 second-pass production/execution questions",
)
content = replace_once(
    content,
    "Report the PATH INPUT RECEIPT/resolution source; canonical development/use/worktree paths; owning contract/resolver;",
    "Report the PATH INPUT RECEIPT/resolution source; material EXECUTION CONTEXT RECEIPT; PROD_USE_STATE; canonical development/use/worktree paths and their physical relation; owning contract/resolver and dev-to-production promotion/update boundary;",
    "P92 deliver receipts",
)
content = replace_once(
    content,
    "Close only when future agents/operators can derive the same development and production locations from repository-owned evidence, environment-dependent literals resolve reproducibly without hard-coded usernames, path drift is blocked or diagnosed, unique work is preserved, and remote integration is no longer confused with local deployment.",
    "Close only when future agents/operators can derive the same development and production locations from repository-owned evidence, environment-dependent literals resolve reproducibly without hard-coded usernames, path drift is blocked or diagnosed, unique work is preserved, ordinary mutation stays in development unless a same-path production-safe contract is proved, active production cannot observe partial candidate state, and remote integration is no longer confused with local deployment.",
    "P92 closure production safety",
)
p92["copyContent"] = content

for keyword in (
    "development local path",
    "production local path",
    "development vs production path",
    "active production path",
    "production in use",
    "production mutation safety",
    "safe local promotion",
    "terminal context",
    "shell context",
    "kernel context",
    "runtime context",
):
    if keyword not in p92["keywords"]:
        p92["keywords"].append(keyword)

if len(p92["copyContent"]) >= 12000:
    raise SystemExit(f"P92 raw prompt grew beyond bounded budget: {len(p92['copyContent'])}")

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
anchor = '            "tracked canonical-path/profile contract -> authorized machine/profile override",\n'
addition = (
    anchor
    + '            "5A. EXECUTION CONTEXT RECEIPT BEFORE PATH-SENSITIVE COMMANDS",\n'
    + '            "A terminal application is not the shell",\n'
    + '            "EXECUTION_CONTEXT=UNKNOWN",\n'
    + '            "5B. DEVELOPMENT MUTATION VS ACTIVE PRODUCTION USE",\n'
    + '            "Production/use path is a consumer path, not the default development mutation target",\n'
    + '            "PROD_USE_STATE",\n'
    + '            "UNKNOWN is not idle",\n'
    + '            "same physical path",\n'
    + '            "Any write is production-impacting",\n'
    + '            "prevents partial candidate state",\n'
)
if '"5B. DEVELOPMENT MUTATION VS ACTIVE PRODUCTION USE"' not in tests:
    tests = replace_once(tests, anchor, addition, "P92 focused phrase assertions")

tests = replace_once(
    tests,
    '        self.assertIn("remote merged SHA is never treated as local deployment proof", p92_prompt["proofGate"])\n',
    '        self.assertIn("remote merged SHA is never treated as local deployment proof", p92_prompt["proofGate"])\n'
    '        self.assertIn("production/use path is not the default development mutation target", p92_prompt["proofGate"])\n'
    '        self.assertIn("UNKNOWN production use state blocks production mutation", p92_prompt["proofGate"])\n'
    '        self.assertIn("running processes, services, launchers", p92_prompt["inspectFirst"])\n',
    "P92 metadata safety assertions",
)
tests = replace_once(
    tests,
    '        self.assertLess(len(self.raw["P92"]["copyContent"]), 9000)\n',
    '        self.assertLess(len(self.raw["P92"]["copyContent"]), 12000)\n',
    "P92 bounded size assertion",
)
TESTS.write_text(tests, encoding="utf-8")
