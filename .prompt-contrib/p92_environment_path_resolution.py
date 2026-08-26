from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
BUILDER = ROOT / "build_prompt_kit.py"
TESTS = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"

P92_COPY = r'''ESTABLISH AND ENFORCE THE CANONICAL DEVELOPMENT AND PRODUCTION PATH FOR THIS REPOSITORY. DO NOT LET AGENTS OR HUMANS INVENT A NEW LOCATION BECAUSE ANOTHER PATH IS CONVENIENT.

Repo/app: xyz_repo_or_app
Machine/profile: xyz_machine_profile_or_resolve_from_evidence
Observed current path, if any: xyz_current_path_or_unknown
Observed production/use entrypoint, if any: xyz_entrypoint_or_unknown

MISSION
Give the repository one durable, machine/profile-aware answer to `Where do we develop it?` and `Where do we run/use it?` Encode the resolution rule in the harness so agents, scripts, launchers, and operators derive the same locations instead of scattering clones, worktrees, installs, or partial app copies. Remote repository completion is not local workstation deployment.

1. REFRESH TRUTH BEFORE CHOOSING A PATH
- Refresh remote/default-branch truth and read current governance, harness maps/contracts, machine/profile routing, launchers, installers/updaters, and worktree conventions.
- Inspect the actual current working directory and bounded known checkout/install candidates when observable.
- Never invent a literal user path from model preference, another machine, remembered chat, or a convenient Desktop/AppData/OneDrive location. Remembered paths are evidence to verify; tracked repository/profile contracts own the durable rule.

2. DEFINE PATH ROLES
For each supported machine/profile record:
- CANONICAL DEVELOPMENT CHECKOUT — normal writable Git checkout.
- CANONICAL PRODUCTION / USE PATH — installed, synchronized, served, or operator-facing location.
- CANONICAL WORKTREE ROOT — optional isolation root; temporary worktrees are not alternate canonical checkouts.
- CANONICAL ENTRYPOINT — launcher/command/script that consumes the use path.
- PATH RELATION — whether development and production are the same location or require explicit sync/install/promotion.
Do not collapse roles merely because one machine currently shares a directory.

3. CODIFY ONE AUTHORITY
Reuse an existing machine/profile/path registry or contract. Otherwise add one owner in the repository's existing harness convention and make it discoverable from the harness entrypoint. Do not standardize a filename across repositories or create a second path authority.
Encode repository identity, profile key, path-resolution rule, development/use/worktree roles, entrypoint, and precedence. Use variables where portability requires them; do not commit secrets or person-private evidence. Wire the owner into existing doctor/preflight, intake, launcher, updater/sync, resolver, worktree helper, validation profile, or status flow where applicable.

4. PREVENT PATH SPRAWL AND COMPUTER BLOAT
Before clone/install/worktree/CD instructions, resolve the canonical rule and classify observed locations as CLONE, WORKTREE, INSTALL, MIRROR, CACHE, OUTPUT, or BACKUP. Refuse a second normal mutable checkout when the canonical one is usable; isolate parallel writers under the approved worktree root.
Inventory noncanonical copies before cleanup. Preserve dirty, unpushed, unique, or separately owned work. Never force-reset or delete merely to make the machine tidy.

5. ENVIRONMENT-DERIVED MACHINE / PROFILE PATH RESOLUTION
Canonical is one repo-owned rule per profile, not one literal string. Build a PATH INPUT RECEIPT from current evidence: OS/platform and path semantics; native home/profile source; actual OS special-folder locations used by the rule; allowed machine/profile override; OneDrive/cloud root and target-folder state when relevant; verified checkout evidence; and material symlink/junction/mount/drive/case behavior. Username/account is runtime input, never a portable constant.

For OneDrive/cloud state distinguish NOT_APPLICABLE, ABSENT, ROOT_AVAILABLE, ROOT_UNAVAILABLE, TARGET_FOLDER_REDIRECTED, MULTIPLE_ROOTS, and UNKNOWN as applicable. An installed/running client is not proof Desktop/Documents are redirected. If the rule says `Desktop\Dev`, resolve Desktop through the OS; on Windows do not assume `%USERPROFILE%\Desktop`, and do not rewrite it under OneDrive unless the actual Known Folder location is redirected there. Ambiguous roots/redirection -> CONFLICT/UNKNOWN. An unavailable canonical root is a blocker, never permission for silent fallback or a second clone.

Resolution precedence: tracked canonical-path/profile contract -> authorized machine/profile override -> native home/special-folder/environment resolution -> verified existing-checkout evidence. Lower-precedence evidence may expose drift but may not silently replace the owner. If current host and target profile differ, route/handoff rather than fabricate a target path locally.

6. FAIL CLOSED ON PATH DRIFT
When identity matters, a mismatch must report canonical rule/path, observed path, attempted role, evidence source, and exact safe next action. Use CANONICAL + PROVED, NONCANONICAL + PRESERVE, NONCANONICAL + DISPOSABLE, MISSING, CONFLICT, or UNKNOWN. UNKNOWN is not permission to guess.

7. REMOTE INTEGRATION IS NOT LOCAL DEPLOYMENT
Track separately:
- REMOTE_INTEGRATED — intended commit is contained in refreshed remote default branch.
- DEV_CHECKOUT_CURRENT — canonical development checkout contains the required integrated commit and is safely reconciled.
- PROD_PATH_CURRENT — canonical production/use path consumed the required version through its real mechanism.
- ENTRYPOINT_PROVED — real operator entrypoint resolves the canonical production path and observes intended behavior.
A GitHub merge proves only remote integration. Updating the dev checkout does not prove a separate install/use path was refreshed.

8. MAP BOTH PATHS WHEN TEST PROOF IS INVOLVED
After location identity is proved, compare:
A. REAL: operator action -> canonical production/use path -> launcher/wrapper -> shell/interpreter -> config/environment -> services/native boundaries -> result.
B. TEST: test runner -> checkout/fixture/helper -> exercised boundaries -> assertions.
Mark material boundaries SAME + PROVED, SAME + WEAKER INPUT, SIMULATED/MOCKED, BYPASSED, PRODUCTION-ONLY, or UNKNOWN. Green helper tests do not prove a production wrapper, installed copy, or workstation path they never invoked. Use same-entrypoint synthetic proof when live execution is unavailable but the real launcher can be exercised safely.

9. SECOND PASS — TRY TO CREATE THE BUG AGAIN
Ask:
- Could another agent entering fresh still choose a different directory?
- Could OS/user/home, Desktop Known Folder, OneDrive redirection, mount/junction, or profile state make the same logical rule resolve differently?
- Could a launcher use a stale install while remote main/dev checkout are current?
- Could a parallel agent create a second mutable checkout?
- Could a mirror/cache/backup be mistaken for source authority?
- Could a resolver silently fall back when canonical evidence is missing?
Add the smallest practical regression for concrete gaps; stop at a bounded fixed point.

10. DELIVER
Report the PATH INPUT RECEIPT/resolution source; canonical development/use/worktree paths; owning contract/resolver; noncanonical-copy disposition; remote SHA; local/prod/entrypoint proof; files/commit/PR/integration state; and exact blocker for any uninspected machine.

CLOSURE RULE
Close only when future agents/operators can derive the same development and production locations from repository-owned evidence, environment-dependent literals resolve reproducibly without hard-coded usernames, path drift is blocked or diagnosed, unique work is preserved, and remote integration is no longer confused with local deployment.'''


def update_p92() -> tuple[int, int]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    prompt = next(item for item in data["prompts"] if item["id"] == "P92")
    if prompt["name"] != "Canonical Path Prompt":
        raise RuntimeError("P92 canonical owner identity changed")

    before = len(prompt["copyContent"])
    prompt["sprintRole"] = (
        "Establish and enforce one repository-owned canonical development checkout and production/use path per supported machine/profile, "
        "derive literal paths from current OS/user/special-folder/cloud-sync evidence instead of hard-coded usernames, prevent duplicate working copies, "
        "and separate remote integration proof from local workstation deployment proof"
    )
    prompt["useWhen"] = (
        "Agents or humans are using, cloning, installing, launching, or updating a repository and its canonical development or production path is missing, "
        "ambiguous, inconsistent across tools, or varies with OS, user profile, special-folder redirection, OneDrive/cloud state, shell, or machine profile; "
        "especially when GitHub main is current but the workstation checkout/install may still be stale."
    )
    prompt["inspectFirst"] = (
        "Current remote/default-branch truth; repository governance and harness entrypoints; existing canonical-path or machine/profile contracts; current working directory "
        "and verified checkout candidates; native OS home/profile and special-folder resolution; username/account only as runtime evidence; OneDrive/cloud roots plus target-folder "
        "redirection/availability state when relevant; shell/filesystem/symlink/junction/mount semantics; launcher/installer/updater/worktree contracts; dirty or unique work; and tests/CI "
        "that claim path or deployment readiness."
    )
    prompt["expectedOutput"] = (
        "A canonical-path ledger plus a repo-owned harness contract and path-input receipt that identify the machine/profile resolution rule, OS/home/special-folder/cloud inputs, "
        "development checkout, production/use path, optional worktree root, and entrypoint; resolvers/validators that consume the contract; safe disposition of noncanonical copies without "
        "deleting unique work; and separate evidence for remote integration, local development freshness, production/install freshness, and real-entrypoint behavior."
    )
    prompt["nextStep"] = (
        "Resolve current repository and machine/profile truth, derive host path inputs from native OS/environment evidence including special-folder and OneDrive redirection state when relevant, "
        "find or repair the single canonical path contract, reconcile conflicting checkouts without destroying unique work, then prove development and production paths separately before calling the app locally ready."
    )
    prompt["proofGate"] = (
        "The repository has exactly one authoritative path owner per supported machine/profile; literal paths are reproducibly derived from current OS/home/special-folder/cloud evidence rather than a hard-coded username; "
        "local Desktop and redirected Desktop/OneDrive states resolve according to the same tracked rule; ambiguous or unavailable roots fail closed; development, production/use, and temporary worktree roles are explicit; "
        "normal harness/launcher/update flows consume the owner; noncanonical locations are blocked or clearly diagnosed without destructive cleanup; a remote merged SHA is never treated as local deployment proof; "
        "and the strongest safe same-entrypoint check confirms the resolved production path or reports an exact inaccessible-runtime blocker."
    )
    prompt["copyContent"] = P92_COPY

    for keyword in (
        "onedrive path",
        "onedrive repository path",
        "onedrive desktop",
        "known folder redirection",
        "user profile path",
        "home directory path",
        "os path resolution",
        "environment-derived path",
        "path input receipt",
    ):
        if keyword not in prompt["keywords"]:
            prompt["keywords"].append(keyword)

    after = len(prompt["copyContent"])
    print(f"P92 candidate chars: before={before} after={after} delta={after-before}")
    if after >= 9000:
        raise RuntimeError(f"P92 raw prompt exceeds anti-bloat ceiling: before={before} after={after}")
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return before, after


def update_synonyms() -> None:
    text = BUILDER.read_text(encoding="utf-8")
    marker = '    "repo location": "P92", "repository location": "P92", "path drift": "P92", "scattered clones": "P92",\n'
    addition = marker + (
        '    "onedrive path": "P92", "onedrive repository path": "P92", "onedrive desktop": "P92",\n'
        '    "known folder redirection": "P92", "user profile path": "P92", "home directory path": "P92",\n'
        '    "os path resolution": "P92", "environment-derived path": "P92", "path input receipt": "P92",\n'
    )
    if marker not in text:
        raise RuntimeError("P92 synonym marker changed")
    if '"onedrive path": "P92"' not in text:
        text = text.replace(marker, addition, 1)
    BUILDER.write_text(text, encoding="utf-8")


def update_tests() -> None:
    text = TESTS.read_text(encoding="utf-8")
    phrase_marker = '            "Could another agent entering fresh still choose a different directory?",\n'
    phrase_addition = phrase_marker + (
        '            "ENVIRONMENT-DERIVED MACHINE / PROFILE PATH RESOLUTION",\n'
        '            "PATH INPUT RECEIPT",\n'
        '            "TARGET_FOLDER_REDIRECTED",\n'
        '            "An installed/running client is not proof",\n'
        '            "do not assume `%USERPROFILE%\\\\Desktop`",\n'
        '            "Ambiguous roots/redirection -> CONFLICT/UNKNOWN",\n'
        '            "tracked canonical-path/profile contract -> authorized machine/profile override",\n'
    )
    if phrase_marker not in text:
        raise RuntimeError("P92 phrase assertion marker changed")
    if '"PATH INPUT RECEIPT"' not in text:
        text = text.replace(phrase_marker, phrase_addition, 1)

    synonym_marker = '            "scattered clones",\n'
    synonym_addition = synonym_marker + (
        '            "onedrive path",\n'
        '            "onedrive repository path",\n'
        '            "known folder redirection",\n'
        '            "user profile path",\n'
        '            "os path resolution",\n'
    )
    p92_start = text.index('        p92_prompt = self.full["P92"]')
    marker_at = text.index(synonym_marker, p92_start)
    if '            "onedrive path",\n' not in text[marker_at: marker_at + 1000]:
        text = text[:marker_at] + text[marker_at:].replace(synonym_marker, synonym_addition, 1)

    metadata_marker = '        self.assertIn("remote merged SHA is never treated as local deployment proof", p92_prompt["proofGate"])\n'
    metadata_addition = metadata_marker + (
        '        self.assertIn("OneDrive/cloud roots", p92_prompt["inspectFirst"])\n'
        '        self.assertIn("hard-coded username", p92_prompt["proofGate"])\n'
    )
    if metadata_marker not in text:
        raise RuntimeError("P92 metadata assertion marker changed")
    if 'p92_prompt["inspectFirst"]' not in text[p92_start:p92_start + 5000]:
        text = text.replace(metadata_marker, metadata_addition, 1)

    TESTS.write_text(text, encoding="utf-8")


def main() -> None:
    before, after = update_p92()
    update_synonyms()
    update_tests()
    print(f"P92 raw chars: before={before} after={after} delta={after-before}")
    print("P92 owner strengthened; no new prompt identity created")


if __name__ == "__main__":
    main()
