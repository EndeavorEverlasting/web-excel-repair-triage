"""Python-owned enforcement for Lua-flagged agent command safety.

Lua classifies command text. Python validates every returned finding, derives the
outcome, blocks unsafe handoff, owns the bounded repair loop, and releases the
embedded Lua state after every inspection.
"""
from __future__ import annotations

import gc
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKER_PATH = Path(__file__).with_name("checker.lua")
DEFAULT_CONTRACT_PATH = ROOT / "harness" / "lua" / "contracts" / "command-safety-findings.v1.json"
MAX_COMMAND_CHARS = 65536
MAX_LUA_MEMORY_BYTES = 2_000_000
MARKER_SEPARATOR = "\x1f"
UNSAFE_LUA_GLOBALS = (
    "os", "io", "package", "require", "dofile", "loadfile", "load",
    "loadstring", "debug", "python",
)


class CommandSafetyError(RuntimeError):
    """Base class for host-owned command safety failures."""


class CommandCheckerFailure(CommandSafetyError):
    """Lua/runtime/schema failure. This is never a PASS."""

    def __init__(self, message: str, ledger: Sequence["RepairPass"] = ()) -> None:
        self.ledger = tuple(ledger)
        super().__init__(message)


class CommandBlockedError(CommandSafetyError):
    """Blocking findings prevented command execution or user handoff."""

    def __init__(self, result: "InspectionResult", ledger: Sequence["RepairPass"] = ()) -> None:
        self.result = result
        self.ledger = tuple(ledger)
        ids = ", ".join(item.rule_id for item in result.findings if item.severity == "BLOCK")
        super().__init__(f"command blocked by Lua findings: {ids or 'unknown blocking finding'}")


class CommandSafetyLoopExhausted(CommandSafetyError):
    """Bounded host repair loop failed to reach a deliberate fixed point."""

    def __init__(self, ledger: Sequence["RepairPass"]) -> None:
        self.ledger = tuple(ledger)
        super().__init__("command safety repair loop exhausted before two clean validation passes")


@dataclass(frozen=True)
class CommandProfile:
    shell: str
    platform: str
    required_launcher: str | None = None
    required_markers: tuple[str, ...] = ()
    failure_propagation_required: bool = True
    allow_warnings: bool = True

    def validate(self) -> None:
        if self.shell not in {"powershell", "cmd", "bash"}:
            raise ValueError(f"unsupported command shell: {self.shell!r}")
        if self.platform not in {"windows", "linux", "macos"}:
            raise ValueError(f"unsupported command platform: {self.platform!r}")
        if self.required_launcher is not None and not self.required_launcher.strip():
            raise ValueError("required_launcher must be non-empty when supplied")
        for marker in self.required_markers:
            if not isinstance(marker, str) or not marker.strip():
                raise ValueError("required_markers must contain non-empty strings")
            if MARKER_SEPARATOR in marker:
                raise ValueError("required marker contains reserved separator")


@dataclass(frozen=True)
class FindingLocation:
    start_line: int
    end_line: int


@dataclass(frozen=True)
class CommandFinding:
    rule_id: str
    severity: str
    category: str
    shell_or_language: str
    location: FindingLocation
    evidence: str
    host_action: str
    remediation_hint: str
    retryable: bool


@dataclass(frozen=True)
class InspectionResult:
    status: str
    checker_version: str
    findings: tuple[CommandFinding, ...]

    @property
    def blocking(self) -> tuple[CommandFinding, ...]:
        return tuple(item for item in self.findings if item.severity == "BLOCK")

    @property
    def warnings(self) -> tuple[CommandFinding, ...]:
        return tuple(item for item in self.findings if item.severity == "WARN")


@dataclass(frozen=True)
class RepairPass:
    pass_number: int
    command_sha256: str
    outcome: str
    rule_ids: tuple[str, ...]
    disposition: str


@dataclass(frozen=True)
class RepairLoopResult:
    command: str
    result: InspectionResult
    ledger: tuple[RepairPass, ...]


RepairCallback = Callable[[str, tuple[CommandFinding, ...]], str]


def _load_contract(path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandCheckerFailure(f"command safety contract could not be loaded: {exc}") from exc
    if not isinstance(payload, dict):
        raise CommandCheckerFailure("command safety contract must be a JSON object")
    return payload


def _lua_to_python(value: Any) -> Any:
    """Convert Lupa table values without accepting arbitrary Python objects."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    items_method = getattr(value, "items", None)
    if not callable(items_method):
        raise CommandCheckerFailure(f"Lua checker returned unsupported value type: {type(value).__name__}")
    items = list(items_method())
    numeric = all(
        not isinstance(key, bool)
        and isinstance(key, (int, float))
        and int(key) == key
        and int(key) >= 1
        for key, _ in items
    )
    if numeric:
        ordered = sorted((int(key), item) for key, item in items)
        if [key for key, _ in ordered] != list(range(1, len(ordered) + 1)):
            raise CommandCheckerFailure("Lua array result must use contiguous 1-based indexes")
        return [_lua_to_python(item) for _, item in ordered]
    result: dict[str, Any] = {}
    for key, item in items:
        if not isinstance(key, str) or not key:
            raise CommandCheckerFailure("Lua object result contains a non-string key")
        result[key] = _lua_to_python(item)
    return result


def _expect_exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    actual = set(value)
    if actual != keys:
        raise CommandCheckerFailure(
            f"{label} shape drifted; missing={sorted(keys - actual)} extra={sorted(actual - keys)}"
        )


def validate_lua_result(
    payload: Any,
    *,
    profile: CommandProfile,
    contract: Mapping[str, Any] | None = None,
) -> InspectionResult:
    """Validate Lua's result before the host derives PASS/WARN/BLOCK."""
    profile.validate()
    cfg = dict(contract or _load_contract())
    if cfg.get("schema_version") != "lua-command-safety-contract/v1":
        raise CommandCheckerFailure("unsupported command safety contract schema")
    required_top = set(cfg.get("required_top_level_fields", []))
    required_finding = set(cfg.get("required_finding_fields", []))
    if not required_top or not required_finding:
        raise CommandCheckerFailure("command safety contract lacks required field declarations")
    if not isinstance(payload, Mapping):
        raise CommandCheckerFailure("Lua checker result must be an object")
    _expect_exact_keys(payload, required_top, "Lua result")
    if payload.get("schema_version") != cfg.get("result_schema_version"):
        raise CommandCheckerFailure("Lua result schema version drifted")
    checker_version = payload.get("checker_version")
    if checker_version != cfg.get("checker_version"):
        raise CommandCheckerFailure("Lua checker version drifted")
    raw_findings = payload.get("findings")
    if not isinstance(raw_findings, list):
        raise CommandCheckerFailure("Lua result findings must be an array")

    severities = set(cfg.get("severities", []))
    categories = set(cfg.get("categories", []))
    shell_values = set(cfg.get("shell_or_language_values", []))
    action_by_severity = dict(cfg.get("host_action_by_severity", {}))
    findings: list[CommandFinding] = []
    seen_rules: set[str] = set()

    for index, raw in enumerate(raw_findings):
        label = f"finding[{index}]"
        if not isinstance(raw, Mapping):
            raise CommandCheckerFailure(f"{label} must be an object")
        _expect_exact_keys(raw, required_finding, label)
        rule_id = raw.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise CommandCheckerFailure(f"{label}.rule_id must be a non-empty string")
        if rule_id in seen_rules:
            raise CommandCheckerFailure(f"duplicate finding rule_id: {rule_id}")
        seen_rules.add(rule_id)
        severity = raw.get("severity")
        if severity not in severities:
            raise CommandCheckerFailure(f"{label}.severity is invalid: {severity!r}")
        category = raw.get("category")
        if category not in categories:
            raise CommandCheckerFailure(f"{label}.category is invalid: {category!r}")
        shell_value = raw.get("shell_or_language")
        if shell_value not in shell_values or shell_value not in {profile.shell, "generic"}:
            raise CommandCheckerFailure(
                f"{label}.shell_or_language does not match selected shell: {shell_value!r}"
            )
        location = raw.get("location")
        if not isinstance(location, Mapping):
            raise CommandCheckerFailure(f"{label}.location must be an object")
        _expect_exact_keys(location, {"start_line", "end_line"}, f"{label}.location")
        start_line = location.get("start_line")
        end_line = location.get("end_line")
        if (
            isinstance(start_line, bool)
            or isinstance(end_line, bool)
            or not isinstance(start_line, int)
            or not isinstance(end_line, int)
            or start_line < 1
            or end_line < start_line
        ):
            raise CommandCheckerFailure(f"{label}.location has an impossible line range")
        evidence = raw.get("evidence")
        hint = raw.get("remediation_hint")
        if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > 240:
            raise CommandCheckerFailure(f"{label}.evidence must be 1..240 characters")
        if not isinstance(hint, str) or not hint.strip():
            raise CommandCheckerFailure(f"{label}.remediation_hint must be non-empty")
        host_action = raw.get("host_action")
        if host_action != action_by_severity.get(severity):
            raise CommandCheckerFailure(f"{label}.host_action does not match severity {severity!r}")
        retryable = raw.get("retryable")
        if not isinstance(retryable, bool):
            raise CommandCheckerFailure(f"{label}.retryable must be boolean")
        findings.append(
            CommandFinding(
                rule_id=rule_id,
                severity=severity,
                category=category,
                shell_or_language=shell_value,
                location=FindingLocation(start_line=start_line, end_line=end_line),
                evidence=evidence,
                host_action=host_action,
                remediation_hint=hint,
                retryable=retryable,
            )
        )

    if any(item.severity == "BLOCK" for item in findings):
        status = "BLOCK"
    elif findings:
        status = "WARN"
    else:
        status = "PASS"
    return InspectionResult(status=status, checker_version=str(checker_version), findings=tuple(findings))


def _promote_warnings(result: InspectionResult) -> InspectionResult:
    promoted = tuple(
        CommandFinding(
            rule_id=item.rule_id,
            severity="BLOCK",
            category=item.category,
            shell_or_language=item.shell_or_language,
            location=item.location,
            evidence=item.evidence,
            host_action="BLOCK_AND_REPAIR",
            remediation_hint=item.remediation_hint,
            retryable=item.retryable,
        )
        for item in result.warnings
    )
    return InspectionResult(status="BLOCK", checker_version=result.checker_version, findings=promoted)


class LuaCommandInspector:
    """Short-lived, default-deny embedded Lua inspector."""

    def __init__(
        self,
        *,
        checker_path: Path = DEFAULT_CHECKER_PATH,
        contract_path: Path = DEFAULT_CONTRACT_PATH,
        checker_source: str | None = None,
    ) -> None:
        self.checker_path = checker_path
        self.contract_path = contract_path
        self.checker_source = checker_source

    def _source(self) -> str:
        if self.checker_source is not None:
            return self.checker_source
        try:
            return self.checker_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CommandCheckerFailure(f"Lua checker source could not be read: {exc}") from exc

    def inspect(self, command: str, profile: CommandProfile) -> InspectionResult:
        profile.validate()
        if not isinstance(command, str) or not command.strip():
            raise CommandCheckerFailure("command must be a non-empty string")
        if len(command) > MAX_COMMAND_CHARS:
            raise CommandCheckerFailure(f"command exceeds {MAX_COMMAND_CHARS} character inspection bound")

        try:
            from lupa.lua54 import LuaError, LuaRuntime
        except ImportError as exc:
            raise CommandCheckerFailure(
                "embedded Lua runtime unavailable; install requirements-command-safety.txt"
            ) from exc

        lua = None
        globals_obj = None
        inspect_fn = None
        raw = None
        try:
            lua = LuaRuntime(
                unpack_returned_tuples=True,
                register_eval=False,
                register_builtins=False,
                max_memory=MAX_LUA_MEMORY_BYTES,
            )
            globals_obj = lua.globals()
            for name in UNSAFE_LUA_GLOBALS:
                globals_obj[name] = None
            lua.execute(self._source(), mode="t", name="@command-safety-checker")
            inspect_fn = globals_obj["inspect_command"]
            if inspect_fn is None:
                raise CommandCheckerFailure("Lua checker did not define inspect_command")
            raw = inspect_fn(
                command,
                profile.shell,
                profile.platform,
                profile.required_launcher or "",
                MARKER_SEPARATOR.join(profile.required_markers),
                profile.failure_propagation_required,
            )
            payload = _lua_to_python(raw)
            result = validate_lua_result(
                payload,
                profile=profile,
                contract=_load_contract(self.contract_path),
            )
        except CommandCheckerFailure:
            raise
        except (LuaError, MemoryError, OSError, RuntimeError, TypeError, ValueError) as exc:
            raise CommandCheckerFailure(f"Lua checker execution failed: {exc}") from exc
        finally:
            raw = None
            inspect_fn = None
            globals_obj = None
            if lua is not None:
                try:
                    lua.gccollect()
                except Exception:
                    pass
            lua = None
            gc.collect()
        return result


class CommandSafetyGate:
    """Host-owned enforcement and bounded repair loop."""

    def __init__(self, inspector: LuaCommandInspector | None = None) -> None:
        self.inspector = inspector or LuaCommandInspector()

    def inspect(self, command: str, profile: CommandProfile) -> InspectionResult:
        return self.inspector.inspect(command, profile)

    def enforce(self, command: str, profile: CommandProfile) -> InspectionResult:
        result = self.inspect(command, profile)
        if result.blocking:
            raise CommandBlockedError(result)
        if result.warnings and not profile.allow_warnings:
            raise CommandBlockedError(_promote_warnings(result))
        return result

    def run_repair_loop(
        self,
        command: str,
        profile: CommandProfile,
        *,
        repair: RepairCallback | None = None,
        max_passes: int = 5,
        clean_passes_required: int = 2,
    ) -> RepairLoopResult:
        if max_passes < clean_passes_required or clean_passes_required < 2:
            raise ValueError("repair loop must allow at least two deliberate clean validation passes")
        candidate = command
        clean_streak = 0
        ledger: list[RepairPass] = []

        for pass_number in range(1, max_passes + 1):
            try:
                result = self.inspect(candidate, profile)
            except CommandCheckerFailure as exc:
                digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
                ledger.append(
                    RepairPass(pass_number, digest, "CHECKER_FAILURE", (), "FAIL_CLOSED")
                )
                raise CommandCheckerFailure(str(exc), ledger) from exc

            digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
            rule_ids = tuple(item.rule_id for item in result.findings)
            if result.blocking:
                clean_streak = 0
                ledger.append(
                    RepairPass(pass_number, digest, "BLOCK", rule_ids, "BLOCKED_REPAIR")
                )
                if repair is None:
                    raise CommandBlockedError(result, ledger)
                repaired = repair(candidate, result.blocking)
                if not isinstance(repaired, str) or not repaired.strip() or repaired == candidate:
                    raise CommandSafetyLoopExhausted(ledger)
                candidate = repaired
                continue

            if result.warnings and not profile.allow_warnings:
                ledger.append(
                    RepairPass(pass_number, digest, "WARN", rule_ids, "WARN_NOT_PERMITTED")
                )
                raise CommandBlockedError(_promote_warnings(result), ledger)

            clean_streak += 1
            disposition = "PASS_FIXED_POINT" if clean_streak >= clean_passes_required else "PASS_REVIEW_REQUIRED"
            ledger.append(
                RepairPass(pass_number, digest, result.status, rule_ids, disposition)
            )
            if clean_streak >= clean_passes_required:
                return RepairLoopResult(command=candidate, result=result, ledger=tuple(ledger))

        raise CommandSafetyLoopExhausted(ledger)


def result_to_dict(result: InspectionResult) -> dict[str, Any]:
    return {
        "status": result.status,
        "checker_version": result.checker_version,
        "findings": [
            {**asdict(item), "location": asdict(item.location)}
            for item in result.findings
        ],
    }


def repair_loop_to_dict(result: RepairLoopResult) -> dict[str, Any]:
    return {
        "safe_to_handoff": result.result.status in {"PASS", "WARN"},
        "command_sha256": hashlib.sha256(result.command.encode("utf-8")).hexdigest(),
        "result": result_to_dict(result.result),
        "passes": [asdict(item) for item in result.ledger],
    }
