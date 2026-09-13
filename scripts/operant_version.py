#!/usr/bin/env python3
"""Deterministic Operant product-version planning, application, and validation.

The human-facing version is repository data, not a manually maintained badge.
Git/artifact identity remains the forensic freshness authority.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "OPERANT_VERSION"
IDENTITY_CONTRACT = ROOT / "harness/contracts/operant-product-identity.v1.json"
CHANGELOG = ROOT / "docs/OPERANT_CHANGELOG.md"
GENERATED_SITE = ROOT / "web/prompt-kit/index.html"
TAG_PREFIX_DEFAULT = "operant-v"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z][a-z0-9-]*)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
RELEASE_TYPES = ("major", "minor", "patch")
RANK = {None: 0, "patch": 1, "minor": 2, "major": 3}


class VersioningError(RuntimeError):
    """Fail-closed version-policy error."""


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "SemVer":
        match = SEMVER_RE.fullmatch(value.strip())
        if not match:
            raise VersioningError(f"invalid Operant SemVer: {value!r}")
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump(self, release_type: str) -> "SemVer":
        if release_type == "major":
            return SemVer(self.major + 1, 0, 0)
        if release_type == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if release_type == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        raise VersioningError(f"unsupported release type: {release_type!r}")


def _run_git(*args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if check and completed.returncode != 0:
        raise VersioningError(
            f"git {' '.join(args)} failed ({completed.returncode}): {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _load_contract() -> dict:
    try:
        payload = json.loads(IDENTITY_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VersioningError(f"cannot read Operant identity contract: {exc}") from exc
    if payload.get("schema_version") != "operant-product-identity/v1":
        raise VersioningError("unsupported Operant identity contract schema")
    policy = payload.get("release_versioning")
    if not isinstance(policy, dict) or policy.get("schema_version") != "operant-release-versioning/v1":
        raise VersioningError("missing operant-release-versioning/v1 policy")
    return payload


def _policy() -> dict:
    return _load_contract()["release_versioning"]


def current_version() -> SemVer:
    try:
        return SemVer.parse(VERSION_FILE.read_text(encoding="utf-8").strip())
    except OSError as exc:
        raise VersioningError(f"missing canonical Operant version authority: {VERSION_FILE}") from exc


def display_version(version: SemVer | str) -> str:
    return str(version)


def _release_rule(value: object, label: str) -> str:
    if value not in RELEASE_TYPES:
        raise VersioningError(f"release policy {label} must be one of {RELEASE_TYPES}: {value!r}")
    return str(value)


def classify_message(
    message: str,
    current: SemVer,
    policy: dict | None = None,
) -> str | None:
    """Map one accepted Conventional Commit to repository-owned release semantics."""
    policy = policy or _policy()
    pre_one = policy.get("pre_1_policy", {})
    no_bump_types = {str(value).lower() for value in policy.get("no_bump_types", [])}
    first_line = message.strip().splitlines()[0] if message.strip() else ""
    match = CONVENTIONAL_RE.match(first_line)
    if not match:
        raise VersioningError(
            "release-relevant commit is not Conventional Commit formatted: " + repr(first_line)
        )
    commit_type = match.group("type").lower()
    breaking = bool(match.group("bang")) or bool(
        re.search(r"(?mi)^BREAKING[ -]CHANGE:\s+\S", message)
    )
    if breaking:
        if current.major == 0:
            return _release_rule(pre_one.get("breaking"), "pre_1_policy.breaking")
        return "major"
    if commit_type == "feat":
        return _release_rule(pre_one.get("feature"), "pre_1_policy.feature")
    if commit_type in {"fix", "perf", "revert"}:
        return _release_rule(
            pre_one.get("fix_or_performance"),
            "pre_1_policy.fix_or_performance",
        )
    if commit_type in no_bump_types:
        return None
    raise VersioningError(
        f"release-relevant commit type {commit_type!r} has no deterministic bump rule"
    )


def highest_release_type(values: Iterable[str | None]) -> str | None:
    result: str | None = None
    for value in values:
        if value not in RANK:
            raise VersioningError(f"unknown release type: {value!r}")
        if RANK[value] > RANK[result]:
            result = value
    return result


def derive_next_version(current: SemVer, release_type: str | None) -> SemVer:
    return current if release_type is None else current.bump(release_type)


def _matches(path: str, patterns: Sequence[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns)


def is_release_relevant(paths: Sequence[str], message: str, policy: dict | None = None) -> bool:
    policy = policy or _policy()
    product_patterns = policy.get("product_paths", [])
    generated_only = policy.get("generated_only_paths", [])
    shared_paths = set(policy.get("shared_paths", []))
    scopes = {scope.lower() for scope in policy.get("shared_scopes", [])}
    normalized = [path.replace("\\", "/") for path in paths if path.strip()]
    if not normalized:
        return False
    if all(_matches(path, generated_only) for path in normalized):
        return False
    if any(_matches(path, product_patterns) and not _matches(path, generated_only) for path in normalized):
        return True
    if any(path in shared_paths for path in normalized):
        first_line = message.strip().splitlines()[0] if message.strip() else ""
        match = CONVENTIONAL_RE.match(first_line)
        return bool(match and (match.group("scope") or "").lower() in scopes)
    return False


def _commit_paths(sha: str) -> list[str]:
    text = _run_git("diff-tree", "--no-commit-id", "--name-only", "-r", sha)
    return [line.strip() for line in text.splitlines() if line.strip()]


def _commit_message(sha: str) -> str:
    return _run_git("show", "-s", "--format=%B", sha)


def _commit_subject(sha: str) -> str:
    return _run_git("show", "-s", "--format=%s", sha)


def _latest_release_tag(tag_prefix: str) -> tuple[str, SemVer] | None:
    tags = _run_git("tag", "--merged", "HEAD", "--list", f"{tag_prefix}*", "--sort=-v:refname")
    for tag in tags.splitlines():
        if not tag.startswith(tag_prefix):
            continue
        raw = tag[len(tag_prefix) :]
        try:
            return tag, SemVer.parse(raw)
        except VersioningError:
            continue
    return None


def _baseline(current: SemVer, policy: dict) -> tuple[str, str | None]:
    tag_prefix = policy.get("tag_prefix", TAG_PREFIX_DEFAULT)
    latest = _latest_release_tag(tag_prefix)
    if latest:
        tag, tagged_version = latest
        if tagged_version != current:
            raise VersioningError(
                f"canonical version {current} drifts from latest reachable Operant release {tag}"
            )
        return _run_git("rev-list", "-n", "1", tag), tag
    bootstrap = policy.get("bootstrap", {})
    sha = bootstrap.get("identity_merge_sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise VersioningError("missing 40-hex bootstrap identity merge SHA")
    _run_git("cat-file", "-e", f"{sha}^{{commit}}")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=ROOT, check=False
    ).returncode != 0:
        raise VersioningError(f"bootstrap SHA is not an ancestor of HEAD: {sha}")
    return sha, None


def plan(
    base: str | None = None,
    head: str = "HEAD",
    *,
    current: SemVer | None = None,
) -> dict:
    policy = _policy()
    resolved_current = current if current is not None else current_version()
    baseline, baseline_tag = (
        _baseline(resolved_current, policy) if base is None else (base, None)
    )
    revs = _run_git("rev-list", "--reverse", "--no-merges", f"{baseline}..{head}")
    relevant: list[dict] = []
    classifications: list[str | None] = []
    for sha in [line for line in revs.splitlines() if line]:
        message = _commit_message(sha)
        paths = _commit_paths(sha)
        if not is_release_relevant(paths, message, policy):
            continue
        release_type = classify_message(message, resolved_current, policy)
        classifications.append(release_type)
        relevant.append(
            {
                "sha": sha,
                "subject": _commit_subject(sha),
                "release_type": release_type,
                "paths": paths,
            }
        )
    release_type = highest_release_type(classifications)
    next_version = derive_next_version(resolved_current, release_type)
    return {
        "schema_version": "operant-version-plan/v1",
        "current_version": str(resolved_current),
        "release_type": release_type,
        "next_version": str(next_version),
        "baseline_sha": baseline,
        "baseline_tag": baseline_tag,
        "head_sha": _run_git("rev-parse", head),
        "relevant_commits": relevant,
    }


def _tag_names() -> list[str]:
    return [line for line in _run_git("tag", "--list").splitlines() if line]


def assert_version_not_released(version: SemVer | str, tags: Iterable[str] | None = None) -> None:
    policy = _policy()
    tag = f"{policy.get('tag_prefix', TAG_PREFIX_DEFAULT)}{version}"
    names = set(tags if tags is not None else _tag_names())
    if tag in names:
        raise VersioningError(f"released Operant version would be reused: {tag}")


def _changelog_section(plan_payload: dict, version: str, release_date: str | None = None) -> str:
    groups = {
        "major": "Breaking changes",
        "minor": "Features / breaking pre-1.0 changes",
        "patch": "Fixes / performance",
    }
    by_kind: dict[str, list[dict]] = {kind: [] for kind in RELEASE_TYPES}
    for commit in plan_payload.get("relevant_commits", []):
        kind = commit.get("release_type")
        if kind in by_kind:
            by_kind[kind].append(commit)
    stamped = release_date or date.today().isoformat()
    lines = [f"## {version} - {stamped}", ""]
    for kind in RELEASE_TYPES:
        commits = by_kind[kind]
        if not commits:
            continue
        lines.extend([f"### {groups[kind]}", ""])
        for commit in commits:
            lines.append(f"- {commit['subject']} (`{commit['sha'][:8]}`)")
        lines.append("")
    if not any(by_kind.values()):
        lines.extend(["- Deterministic repository versioning maintenance.", ""])
    return "\n".join(lines).rstrip() + "\n\n"


_CHANGELOG_HEADER_RE = re.compile(
    r"^## (?P<version>\d+\.\d+\.\d+) - (?P<date>\d{4}-\d{2}-\d{2})\s*$",
    re.MULTILINE,
)


def _split_changelog_sections(text: str) -> tuple[str, list[tuple[str, str, str]]]:
    """Return (preamble, [(version, date, body_including_heading), ...])."""
    matches = list(_CHANGELOG_HEADER_RE.finditer(text))
    if not matches:
        return text, []
    preamble = text[: matches[0].start()]
    sections: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group("version"), match.group("date"), text[match.start() : end]))
    return preamble, sections


def replace_candidate_changelog_section(
    changelog_text: str,
    plan_payload: dict,
    version: str,
    previous_versions: Sequence[str] | None = None,
) -> str:
    """Replace open-candidate section(s) with the recomputed section for version."""
    header = (
        "# Operant Changelog\n\n"
        "Human-facing Operant releases. Git commit/artifact identity remains the forensic freshness proof.\n\n"
    )
    if not changelog_text.startswith("# Operant Changelog"):
        raise VersioningError("unexpected Operant changelog format")
    preamble, sections = _split_changelog_sections(changelog_text)
    if not preamble.strip():
        preamble = header
    drop = {str(value) for value in (previous_versions or ())}
    drop.add(version)
    retained = [body for ver, _date, body in sections if ver not in drop]
    release_date = next((d for ver, d, _body in sections if ver == version), None)
    insertion = _changelog_section(plan_payload, version, release_date=release_date)
    return preamble.rstrip() + "\n\n" + insertion + "".join(retained).lstrip()


def _version_at_ref(ref: str) -> SemVer | None:
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}:OPERANT_VERSION"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        return None
    text = _run_git("show", f"{ref}:OPERANT_VERSION")
    return SemVer.parse(text.strip().splitlines()[0])


def release_anchor(version: SemVer | str, head: str = "HEAD") -> str:
    """Resolve the integrated commit that owns a released version boundary.

    Release PRs may land as more than one commit. The release identity belongs to
    the latest exact release commit carrying the requested canonical version, not
    necessarily to the commit whose diff first changed OPERANT_VERSION.
    """
    resolved = version if isinstance(version, SemVer) else SemVer.parse(str(version))
    expected_subject = f"chore(operant): release v{resolved}"
    history = _run_git("log", "--format=%H%x09%s", head)
    for line in history.splitlines():
        sha, separator, subject = line.partition("\t")
        if separator and subject == expected_subject and _version_at_ref(sha) == resolved:
            return sha
    raise VersioningError(
        f"cannot resolve integrated release anchor for Operant v{resolved} from {head}"
    )


def validate_release_candidate(base: str = "origin/main", head: str = "HEAD") -> list[str]:
    """Reject automation release candidates that no longer match a recomputed mainline plan.

    Non-release heads (authority matches base) pass without further checks so ordinary
    feature PRs can reuse the same workflow job. When the default branch does not yet
    carry OPERANT_VERSION, the establishing PR also passes.
    """
    findings: list[str] = []
    try:
        base_sha = _run_git("rev-parse", base)
        head_sha = _run_git("rev-parse", head)
        base_version = _version_at_ref(base)
        head_version = current_version() if head == "HEAD" else _version_at_ref(head)
    except VersioningError as exc:
        return [str(exc)]

    if base_version is None:
        return findings
    if head_version is None:
        findings.append(f"release candidate head is missing OPERANT_VERSION: {head}")
        return findings
    if head_version == base_version:
        return findings

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", base_sha, head_sha], cwd=ROOT, check=False
    ).returncode != 0:
        findings.append(
            f"stale Operant release candidate: {base} is not an ancestor of {head}"
        )

    try:
        expected = plan(base=None, head=base, current=base_version)
    except VersioningError as exc:
        return findings + [f"cannot recompute release plan from {base}: {exc}"]

    if expected.get("release_type") is None:
        findings.append(
            f"stale Operant release candidate: {base} no longer has a release-worthy change"
        )
        return findings

    expected_version = SemVer.parse(str(expected["next_version"]))
    if head_version != expected_version:
        findings.append(
            "stale Operant release candidate version: "
            f"head={head_version} expected={expected_version}"
        )

    changelog_text = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else ""
    _preamble, sections = _split_changelog_sections(changelog_text)
    matching = [body for ver, _date, body in sections if ver == str(expected_version)]
    if not matching:
        findings.append(
            f"stale Operant release candidate changelog: missing section for {expected_version}"
        )
    else:
        release_date = next(d for ver, d, _body in sections if ver == str(expected_version))
        expected_section = _changelog_section(
            expected, str(expected_version), release_date=release_date
        ).rstrip()
        actual_section = matching[0].rstrip()
        if _changelog_commit_fingerprint(actual_section) != _changelog_commit_fingerprint(
            expected_section
        ):
            findings.append(
                f"stale Operant release candidate changelog for {expected_version}: "
                "relevant commits no longer match recomputed plan"
            )
    return findings


def _changelog_commit_fingerprint(section: str) -> tuple[str, ...]:
    """Normalize a changelog section to ordered subject+sha markers for stale detection."""
    markers: list[str] = []
    for line in section.splitlines():
        match = re.match(r"^- (.+) \(`([0-9a-f]{8})`\)$", line.strip())
        if match:
            markers.append(f"{match.group(1)}|{match.group(2)}")
    return tuple(markers)


def _write_temp(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(raw_temp)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def _atomic_write_many(updates: dict[Path, str]) -> None:
    """Prepare every write first; on replace failure restore already-replaced targets."""
    originals = {path: path.read_bytes() if path.exists() else None for path in updates}
    prepared: list[tuple[Path, Path]] = []
    replaced: list[Path] = []
    try:
        for path, text in updates.items():
            prepared.append((path, _write_temp(path, text.encode("utf-8"))))
        for path, temp_path in prepared:
            os.replace(temp_path, path)
            replaced.append(path)
    except Exception as exc:
        rollback_errors: list[str] = []
        for path in reversed(replaced):
            try:
                prior = originals[path]
                if prior is None:
                    path.unlink(missing_ok=True)
                else:
                    os.replace(_write_temp(path, prior), path)
            except Exception as rollback_exc:  # pragma: no cover - catastrophic filesystem failure
                rollback_errors.append(f"{path}: {rollback_exc}")
        detail = f"; rollback failures: {', '.join(rollback_errors)}" if rollback_errors else ""
        raise VersioningError(f"Operant version mirror transaction failed: {exc}{detail}") from exc
    finally:
        for _, temp_path in prepared:
            temp_path.unlink(missing_ok=True)


def apply_plan(plan_payload: dict) -> None:
    if plan_payload.get("schema_version") != "operant-version-plan/v1":
        raise VersioningError("unsupported version-plan schema")
    current = current_version()
    if plan_payload.get("current_version") != str(current):
        raise VersioningError("version plan current_version is stale")
    release_type = plan_payload.get("release_type")
    if release_type is None:
        raise VersioningError("version plan contains no release-worthy change")
    next_version = SemVer.parse(str(plan_payload.get("next_version", "")))
    expected = derive_next_version(current, release_type)
    if next_version != expected:
        raise VersioningError(f"plan next_version drifted: expected {expected}, got {next_version}")
    assert_version_not_released(next_version)

    payload = _load_contract()
    payload["product_version"] = str(next_version)
    payload.setdefault("compatibility", {})["visible_version"] = str(next_version)
    contract_text = json.dumps(payload, indent=2) + "\n"

    header = "# Operant Changelog\n\nHuman-facing Operant releases. Git commit/artifact identity remains the forensic freshness proof.\n\n"
    existing = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else header
    previous_candidate = None
    if existing.startswith("# Operant Changelog"):
        _preamble, sections = _split_changelog_sections(existing)
        if sections and SemVer.parse(sections[0][0]) > current:
            previous_candidate = sections[0][0]
    changelog_text = replace_candidate_changelog_section(
        existing if existing.startswith("# Operant Changelog") else header + existing,
        plan_payload,
        str(next_version),
        previous_versions=[previous_candidate] if previous_candidate else None,
    )

    _atomic_write_many(
        {
            VERSION_FILE: f"{next_version}\n",
            IDENTITY_CONTRACT: contract_text,
            CHANGELOG: changelog_text,
        }
    )


def validate(require_tag: bool = False) -> list[str]:
    findings: list[str] = []
    try:
        version = current_version()
        payload = _load_contract()
    except VersioningError as exc:
        return [str(exc)]
    if payload.get("product_version") != str(version):
        findings.append("identity contract product_version does not match OPERANT_VERSION")
    if payload.get("compatibility", {}).get("visible_version") != str(version):
        findings.append("identity contract visible_version does not match OPERANT_VERSION")
    policy = payload.get("release_versioning", {})
    if policy.get("authority_file") != "OPERANT_VERSION":
        findings.append("release policy authority_file drifted")
    if policy.get("scheme") != "semver":
        findings.append("release policy scheme drifted")
    if policy.get("tag_prefix") != TAG_PREFIX_DEFAULT:
        findings.append("release policy tag prefix drifted")
    pre_one = policy.get("pre_1_policy", {})
    expected_pre_one = {
        "breaking": "minor",
        "feature": "minor",
        "fix_or_performance": "patch",
    }
    for key, expected in expected_pre_one.items():
        if pre_one.get(key) != expected:
            findings.append(f"pre-1 release rule {key} drifted: {pre_one.get(key)!r}")
    required_no_bump = {"docs", "test", "tests", "refactor", "style", "chore", "ci", "build"}
    if set(policy.get("no_bump_types", [])) != required_no_bump:
        findings.append("no-bump commit-type policy drifted")
    if not CHANGELOG.exists():
        findings.append("Operant changelog is missing")
    if not GENERATED_SITE.exists():
        findings.append("generated Operant site is missing")
    else:
        html = GENERATED_SITE.read_text(encoding="utf-8")
        expected_markers = (
            f"<title>AFK Agent Flow {version}</title>",
            f"AFK Agent Flow <span>{version}</span>",
            f'id="versionBadge">{version}</div>',
        )
        for marker in expected_markers:
            if marker not in html:
                findings.append(f"generated Operant version mirror missing: {marker}")
    if require_tag:
        tag = f"{TAG_PREFIX_DEFAULT}{version}"
        try:
            target = _run_git("rev-list", "-n", "1", tag)
            expected_target = release_anchor(version)
            if target != expected_target:
                findings.append(
                    f"release tag {tag} points to {target}, expected release anchor {expected_target}"
                )
        except VersioningError as exc:
            findings.append(str(exc))
    return findings


def _read_plan(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VersioningError(f"cannot read version plan {path}: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan", help="derive the next version from accepted Git history")
    plan_parser.add_argument("--base")
    plan_parser.add_argument("--head", default="HEAD")
    plan_parser.add_argument("--output", type=Path)
    apply_parser = sub.add_parser("apply", help="apply a previously derived version plan")
    apply_parser.add_argument("--plan", required=True, type=Path)
    validate_parser = sub.add_parser("validate", help="validate canonical authority and mirrors")
    validate_parser.add_argument("--require-tag", action="store_true")
    candidate_parser = sub.add_parser(
        "validate-release-candidate",
        help="reject stale automation release candidates against recomputed mainline plan",
    )
    candidate_parser.add_argument("--base", default="origin/main")
    candidate_parser.add_argument("--head", default="HEAD")
    anchor_parser = sub.add_parser(
        "release-anchor",
        help="print the integrated commit that owns the current release boundary",
    )
    anchor_parser.add_argument("--head", default="HEAD")
    sub.add_parser("current", help="print the canonical Operant version")
    args = parser.parse_args(argv)
    try:
        if args.command == "current":
            print(current_version())
            return 0
        if args.command == "release-anchor":
            print(release_anchor(current_version(), head=args.head))
            return 0
        if args.command == "plan":
            payload = plan(args.base, args.head)
            text = json.dumps(payload, indent=2)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text + "\n", encoding="utf-8")
            print(text)
            return 0
        if args.command == "apply":
            apply_plan(_read_plan(args.plan))
            print(f"OPERANT_VERSION_APPLY_PASS version={current_version()}")
            return 0
        if args.command == "validate":
            findings = validate(require_tag=args.require_tag)
            if findings:
                print("OPERANT_VERSION_FAIL")
                for finding in findings:
                    print(f"- {finding}")
                return 1
            print(f"OPERANT_VERSION_PASS version={current_version()}")
            return 0
        if args.command == "validate-release-candidate":
            findings = validate_release_candidate(base=args.base, head=args.head)
            if findings:
                print("OPERANT_RELEASE_CANDIDATE_FAIL")
                for finding in findings:
                    print(f"- {finding}")
                return 1
            print("OPERANT_RELEASE_CANDIDATE_PASS")
            return 0
    except VersioningError as exc:
        print(f"OPERANT_VERSION_FAIL: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
