from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
BUILDER = ROOT / "build_prompt_kit.py"
TESTS = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"


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
        "Resolve current repository and machine/profile truth, derive the host path inputs from native OS/environment evidence including special-folder and OneDrive redirection state when relevant, "
        "find or repair the single canonical path contract, reconcile conflicting checkouts without destroying unique work, then prove development and production paths separately before calling the app locally ready."
    )
    prompt["proofGate"] = (
        "The repository has exactly one authoritative path owner per supported machine/profile; literal paths are reproducibly derived from current OS/home/special-folder/cloud evidence rather than a hard-coded username; "
        "local Desktop and redirected Desktop/OneDrive states resolve according to the same tracked rule; ambiguous or unavailable roots fail closed; development, production/use, and temporary worktree roles are explicit; "
        "normal harness/launcher/update flows consume the owner; noncanonical locations are blocked or clearly diagnosed without destructive cleanup; a remote merged SHA is never treated as local deployment proof; "
        "and the strongest safe same-entrypoint check confirms the resolved production path or reports an exact inaccessible-runtime blocker."
    )

    old_section = """8. MACHINE / PROFILE PORTABILITY
Canonical does not mean one literal path string for every computer or OS. It means one repository-owned resolution rule for each supported profile. A Windows development path and an Android/Termux path may differ, but both must be explicit profile records. Never emit a command for one shell/profile merely because it is valid on another. If current host and target profile differ, route or hand off according to the existing harness contract rather than fabricating a local path.
"""
    new_section = """8. ENVIRONMENT-DERIVED MACHINE / PROFILE PATH RESOLUTION
Canonical means one repository-owned resolution rule per supported profile, not one literal path string. Before emitting or accepting a path, build a PATH INPUT RECEIPT from current evidence: OS/platform plus shell/filesystem semantics; native home/profile source (username/account is runtime input, never a portable constant); repository/profile root rule and allowed overrides; actual OS special-folder location when Desktop/Documents participate; relevant OneDrive/cloud-folder state; verified checkout candidate; and material symlink/junction/mount/drive/case semantics.

For OneDrive/cloud-backed folders classify at least NOT_APPLICABLE, ABSENT, ROOT_AVAILABLE, ROOT_UNAVAILABLE, TARGET_FOLDER_REDIRECTED, MULTIPLE_ROOTS, or UNKNOWN. An installed/running client is not proof that Desktop/Documents are redirected. If a repository rule says `Desktop\\Dev`, resolve Desktop through the OS first: on Windows do not assume `%USERPROFILE%\\Desktop`; use the actual Known Folder location. If OneDrive exists but the target folder is not redirected, do not rewrite the path into OneDrive. Ambiguous roots/redirection -> CONFLICT/UNKNOWN; an unavailable canonical root -> blocker, not silent fallback or a second clone.

Resolution precedence: tracked canonical-path/profile contract -> authorized machine/profile override -> native home/special-folder/environment resolution -> verified existing-checkout evidence. Lower-precedence evidence may verify or expose drift; it does not silently replace a higher-precedence canonical owner. Current host and target profile may differ, so do not fabricate a local path for another profile.
"""
    if old_section not in prompt["copyContent"]:
        raise RuntimeError("P92 portability section marker changed")
    prompt["copyContent"] = prompt["copyContent"].replace(old_section, new_section)

    old_second_pass = """- Could a path resolver fall back silently when the canonical record is missing?
Add the smallest practical regression or validator for every concrete gap found and rerun the affected path proof."""
    new_second_pass = """- Could a path resolver fall back silently when the canonical record is missing?
- Could the same logical development-root rule resolve differently after OS, user-profile, Desktop Known Folder, or OneDrive redirection state changes?
Add the smallest practical regression or validator for every concrete gap found and rerun the affected path proof."""
    if old_second_pass not in prompt["copyContent"]:
        raise RuntimeError("P92 second-pass marker changed")
    prompt["copyContent"] = prompt["copyContent"].replace(old_second_pass, new_second_pass)

    old_deliver = """Report the canonical development path, production/use path, worktree root if applicable, owning harness contract/resolver, noncanonical copies and their safe disposition, remote/default-branch SHA, local freshness proof, production freshness proof, entrypoint proof, files/commit/PR/integration state, and exact blocker for any machine that could not be inspected."""
    new_deliver = """Report the path-input receipt/resolution source, canonical development path, production/use path, worktree root if applicable, owning harness contract/resolver, noncanonical copies and their safe disposition, remote/default-branch SHA, local freshness proof, production freshness proof, entrypoint proof, files/commit/PR/integration state, and exact blocker for any machine that could not be inspected."""
    if old_deliver not in prompt["copyContent"]:
        raise RuntimeError("P92 deliver marker changed")
    prompt["copyContent"] = prompt["copyContent"].replace(old_deliver, new_deliver)

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
    if after >= 9000:
        raise RuntimeError(f"P92 raw prompt exceeds anti-bloat ceiling: {after}")
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
