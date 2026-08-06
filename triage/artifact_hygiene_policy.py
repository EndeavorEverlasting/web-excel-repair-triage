"""Path-only policy for staged and tracked artifact hygiene.

The policy intentionally classifies paths without opening file contents so hook
output cannot echo sensitive workbook, log, credential, or crash-dump data.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

REMEDIATION = (
    "Move live/generated evidence back to ignored local output, or commit a "
    "sanitized fixture under an approved fixture/docs path."
)

PROTECTED_PREFIXES: tuple[str, ...] = (
    "attached_assets/",
    "Candidates/",
    "ArtifactIntake/",
    "artifacts/",
    "outputs/",
    "Outputs/",
    "Repaired/",
    "Deprecated/outputs_pre_i100/",
    "billing_runs/",
    "billing_runs_tmp/",
    "Workbook Payload Artifacts/",
    "RecoveredArtifacts/",
    "References/",
    "logs/",
    "saves/",
    "crash_dumps/",
    ".local-tools/",
    "node_modules/",
)

APPROVED_SANITIZED_PREFIXES: tuple[str, ...] = (
    "tests/fixtures/",
    "harness/fixtures/",
    "docs/fixtures/",
)

MACHINE_LOCAL_SEGMENTS: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        ".venv",
        "venv",
        "node_modules",
        ".ipynb_checkpoints",
    }
)

RUNTIME_SUFFIXES: tuple[str, ...] = (
    ".log",
    ".trace",
    ".stackdump",
    ".dmp",
    ".crash",
    ".core",
    ".pid",
    ".tmp",
    ".temp",
    ".autosave",
    ".save",
    ".bak",
)

SECRET_SUFFIXES: tuple[str, ...] = (
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".kdbx",
)

SECRET_BASENAMES: frozenset[str] = frozenset(
    {
        ".env",
        "credentials.json",
        "credential.json",
        "secrets.json",
        "secret.json",
        "tokens.json",
        "token.json",
        "auth.json",
    }
)

ALLOWED_PROTECTED_METADATA: frozenset[str] = frozenset({".gitkeep", "README.md"})

ALLOWED_TRACKED_EXACT_PATHS: frozenset[str] = frozenset(
    {
        "Outputs/cf_dict_deprecated.json",
        "Outputs/dv_spec_deprecated.json",
        ".env.example",
    }
)


@dataclass(frozen=True)
class HygieneFinding:
    path: str
    reason: str


def normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized


def _under_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def _has_machine_segment(path: str) -> bool:
    return any(part in MACHINE_LOCAL_SEGMENTS for part in PurePosixPath(path).parts)


def _is_secret_like(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    if name in SECRET_BASENAMES:
        return True
    if name.startswith(".env."):
        return True
    if any(name.endswith(suffix) for suffix in SECRET_SUFFIXES):
        return True
    return name.startswith("credentials.") or name.startswith("secrets.")


def classify_path(path: str) -> HygieneFinding | None:
    """Return one path-only finding, or ``None`` when the path is commit-safe."""
    normalized = normalize_path(path)
    if not normalized:
        return None

    if normalized in ALLOWED_TRACKED_EXACT_PATHS:
        return None

    if _is_secret_like(normalized):
        return HygieneFinding(normalized, "secret_or_credential_material")

    if _has_machine_segment(normalized):
        return HygieneFinding(normalized, "machine_local_tool_or_cache")

    if _under_prefix(normalized, APPROVED_SANITIZED_PREFIXES):
        return None

    name = PurePosixPath(normalized).name
    if _under_prefix(normalized, PROTECTED_PREFIXES):
        if name in ALLOWED_PROTECTED_METADATA:
            return None
        return HygieneFinding(normalized, "generated_or_runtime_artifact")

    lower = normalized.lower()
    if any(lower.endswith(suffix) for suffix in RUNTIME_SUFFIXES):
        return HygieneFinding(normalized, "runtime_log_save_or_crash_artifact")

    return None


def scan_paths(paths: Iterable[str]) -> list[HygieneFinding]:
    findings: list[HygieneFinding] = []
    seen: set[str] = set()
    for raw in paths:
        normalized = normalize_path(raw)
        if normalized in seen:
            continue
        seen.add(normalized)
        finding = classify_path(normalized)
        if finding is not None:
            findings.append(finding)
    return sorted(findings, key=lambda item: item.path.casefold())


def render_findings(findings: Iterable[HygieneFinding]) -> str:
    lines: list[str] = []
    for finding in findings:
        lines.append(
            f"[harness] refusing staged generated/runtime artifact: {finding.path}"
        )
        lines.append(REMEDIATION)
    return "\n".join(lines)
