from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

LOCK_SCHEMA = "web-excel-fun-nth-contract-lock/v1"
PACKET_SCHEMA = "fun-nth-packet-spec/v1"
MANIFEST_SCHEMA = "fun-nth-artifact-manifest/v1"
RECEIPT_SCHEMA = "web-excel-fun-nth-producer-receipt/v1"
CANONICAL_FUN_REPOSITORY = "EndeavorEverlasting/FUN"
CANONICAL_CONSUMER_REPOSITORY = "EndeavorEverlasting/web-excel-repair-triage"
ALLOWED_ARTIFACT_TYPES = {"share_ready", "internal", "fixture"}
ALLOWED_PUBLICATION_POSTURES = {"sanitized_fixture", "private_runtime", "protected_runtime"}
ALLOWED_EXPORT_PROFILE_KEYS = {
    "schema",
    "packet_id",
    "sheet_contract",
    "cell_assertions",
    "reconciliations",
    "required_text",
    "row_color_contracts",
}


class FunNthExportError(ValueError):
    """Raised when producer inputs cannot safely emit the FUN contract."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FunNthExportError(f"missing JSON input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FunNthExportError(f"invalid JSON input {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise FunNthExportError(f"JSON input must be an object: {path}")
    return payload


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FunNthExportError(f"{label} must be a non-empty string")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise FunNthExportError(f"{label} must be an array")
    return value


def verify_contract_lock(lock_path: Path, repository_root: Path) -> dict[str, Any]:
    lock = _load_json(lock_path)
    if lock.get("schema") != LOCK_SCHEMA:
        raise FunNthExportError("unsupported FUN contract lock schema")
    if lock.get("canonical_owner") != CANONICAL_FUN_REPOSITORY:
        raise FunNthExportError("FUN contract lock canonical owner drifted")
    if lock.get("consumer_repository") != CANONICAL_CONSUMER_REPOSITORY:
        raise FunNthExportError("FUN contract lock consumer repository drifted")
    fun_commit = _require_nonempty_string(lock.get("fun_commit"), "fun_commit")
    if len(fun_commit) != 40 or any(ch not in "0123456789abcdef" for ch in fun_commit):
        raise FunNthExportError("fun_commit must be a lowercase 40-character Git SHA")

    contracts = _require_list(lock.get("contracts"), "contracts")
    if len(contracts) != 3:
        raise FunNthExportError("FUN contract lock must pin exactly three schemas")
    expected_ids = {PACKET_SCHEMA, MANIFEST_SCHEMA, "fun-nth-validation-result/v1"}
    seen_ids: set[str] = set()
    for record in contracts:
        if not isinstance(record, dict):
            raise FunNthExportError("contract records must be objects")
        schema_id = _require_nonempty_string(record.get("schema_id"), "schema_id")
        if schema_id in seen_ids:
            raise FunNthExportError(f"duplicate schema_id in contract lock: {schema_id}")
        seen_ids.add(schema_id)
        snapshot = repository_root / _require_nonempty_string(
            record.get("snapshot_path"), "snapshot_path"
        )
        if not snapshot.is_file():
            raise FunNthExportError(f"missing pinned FUN schema snapshot: {snapshot}")
        data = snapshot.read_bytes()
        if len(data) != record.get("size"):
            raise FunNthExportError(f"schema size drift: {snapshot}")
        if sha256_bytes(data) != record.get("sha256"):
            raise FunNthExportError(f"schema SHA-256 drift: {snapshot}")
        schema_payload = json.loads(data.decode("utf-8"))
        const = schema_payload.get("properties", {}).get("schema", {}).get("const")
        if const != schema_id:
            raise FunNthExportError(
                f"schema identity mismatch: lock={schema_id} snapshot={const}"
            )
    if seen_ids != expected_ids:
        raise FunNthExportError(f"FUN contract lock schema set drifted: {sorted(seen_ids)}")
    return lock


def validate_packet_spec(packet: Mapping[str, Any]) -> None:
    if packet.get("schema") != PACKET_SCHEMA:
        raise FunNthExportError("packet specification schema must be fun-nth-packet-spec/v1")
    _require_nonempty_string(packet.get("packet_id"), "packet_id")
    share_surface = packet.get("share_surface")
    if not isinstance(share_surface, Mapping):
        raise FunNthExportError("packet share_surface must be an object")
    _require_nonempty_string(share_surface.get("artifact_name"), "share_surface.artifact_name")
    approved_tabs = _require_list(share_surface.get("approved_tabs"), "share_surface.approved_tabs")
    if not approved_tabs or len(approved_tabs) != len(set(approved_tabs)):
        raise FunNthExportError("share_surface.approved_tabs must be non-empty and unique")
    for tab in approved_tabs:
        _require_nonempty_string(tab, "approved tab")
    forbidden = _require_list(
        share_surface.get("forbidden_content"), "share_surface.forbidden_content"
    )
    for item in forbidden:
        _require_nonempty_string(item, "forbidden content")
    boundaries = _require_list(packet.get("proof_boundaries"), "proof_boundaries")
    if not boundaries:
        raise FunNthExportError("packet proof_boundaries must not be empty")


def validate_export_profile(
    profile: Mapping[str, Any], packet: Mapping[str, Any], artifact_type: str
) -> None:
    extras = set(profile) - ALLOWED_EXPORT_PROFILE_KEYS
    if extras:
        raise FunNthExportError(
            "export profile contains unsupported fields; producer may not carry evidence "
            f"claims or labor logic: {sorted(extras)}"
        )
    if profile.get("schema") != "web-excel-fun-nth-export-profile/v1":
        raise FunNthExportError("unsupported NTH export profile schema")
    if profile.get("packet_id") != packet.get("packet_id"):
        raise FunNthExportError("export profile packet_id does not match packet specification")
    sheet_contract = profile.get("sheet_contract")
    if not isinstance(sheet_contract, Mapping):
        raise FunNthExportError("sheet_contract must be an object")
    allowed_sheets = _require_list(sheet_contract.get("allowed_sheets"), "allowed_sheets")
    if not allowed_sheets or len(allowed_sheets) != len(set(allowed_sheets)):
        raise FunNthExportError("allowed_sheets must be non-empty and unique")
    approved_tabs = packet["share_surface"]["approved_tabs"]
    if artifact_type == "share_ready" and allowed_sheets != approved_tabs:
        raise FunNthExportError(
            "share_ready allowed_sheets must exactly match packet approved_tabs in order"
        )
    if artifact_type == "share_ready" and sheet_contract.get("hidden_sheets_forbidden") is not True:
        raise FunNthExportError("share_ready artifacts must forbid hidden sheets")
    forbidden_text = sheet_contract.get("forbidden_text", [])
    _require_list(forbidden_text, "forbidden_text")
    missing_forbidden = [
        item for item in packet["share_surface"]["forbidden_content"] if item not in forbidden_text
    ]
    if missing_forbidden:
        raise FunNthExportError(
            f"sheet_contract does not preserve packet forbidden content: {missing_forbidden}"
        )
    _require_list(profile.get("cell_assertions"), "cell_assertions")
    _require_list(profile.get("reconciliations"), "reconciliations")
    for optional in ("required_text", "row_color_contracts"):
        if optional in profile:
            _require_list(profile[optional], optional)


@dataclass(frozen=True)
class ExportResult:
    manifest: dict[str, Any]
    receipt: dict[str, Any]


def build_fun_nth_export(
    *,
    artifact_path: Path,
    packet_spec_path: Path,
    export_profile_path: Path,
    lock_path: Path,
    repository_root: Path,
    artifact_type: str,
    builder_version: str,
    producer_commit: str,
    publication_posture: str,
    generation_mode: str,
    drive_file_id: str | None = None,
    drive_folder_id: str | None = None,
) -> ExportResult:
    if artifact_type not in ALLOWED_ARTIFACT_TYPES:
        raise FunNthExportError(f"unsupported artifact_type: {artifact_type}")
    if publication_posture not in ALLOWED_PUBLICATION_POSTURES:
        raise FunNthExportError(f"unsupported publication_posture: {publication_posture}")
    if artifact_type == "fixture" and publication_posture != "sanitized_fixture":
        raise FunNthExportError("fixture artifacts must use sanitized_fixture posture")
    if artifact_type != "fixture" and publication_posture == "sanitized_fixture":
        raise FunNthExportError("production artifact types cannot use sanitized_fixture posture")
    _require_nonempty_string(builder_version, "builder_version")
    _require_nonempty_string(producer_commit, "producer_commit")
    _require_nonempty_string(generation_mode, "generation_mode")
    if len(producer_commit) != 40 or any(
        ch not in "0123456789abcdef" for ch in producer_commit
    ):
        raise FunNthExportError("producer_commit must be a lowercase 40-character Git SHA")
    if not artifact_path.is_file() or artifact_path.stat().st_size <= 0:
        raise FunNthExportError(f"artifact is missing or empty: {artifact_path}")

    lock = verify_contract_lock(lock_path, repository_root)
    packet = _load_json(packet_spec_path)
    profile = _load_json(export_profile_path)
    validate_packet_spec(packet)
    validate_export_profile(profile, packet, artifact_type)

    artifact_bytes = artifact_path.read_bytes()
    artifact = {
        "filename": artifact_path.name,
        "sha256": sha256_bytes(artifact_bytes),
        "size": len(artifact_bytes),
        "artifact_type": artifact_type,
        "builder_version": builder_version,
    }
    if drive_file_id:
        artifact["drive_file_id"] = drive_file_id
    if drive_folder_id:
        artifact["drive_folder_id"] = drive_folder_id

    manifest: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "packet_id": packet["packet_id"],
        "artifact": artifact,
        "sheet_contract": dict(profile["sheet_contract"]),
        "cell_assertions": list(profile["cell_assertions"]),
        "reconciliations": list(profile["reconciliations"]),
    }
    for optional in ("required_text", "row_color_contracts"):
        if optional in profile:
            manifest[optional] = list(profile[optional])

    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    packet_bytes = packet_spec_path.read_bytes()
    profile_bytes = export_profile_path.read_bytes()
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "producer": {
            "repository": CANONICAL_CONSUMER_REPOSITORY,
            "commit": producer_commit,
            "builder_version": builder_version,
            "generation_mode": generation_mode,
        },
        "upstream_contract": {
            "repository": CANONICAL_FUN_REPOSITORY,
            "commit": lock["fun_commit"],
            "lock_path": str(lock_path.relative_to(repository_root)).replace("\\", "/"),
            "lock_sha256": sha256_file(lock_path),
            "schemas": [
                {
                    "schema_id": item["schema_id"],
                    "source_path": item["source_path"],
                    "snapshot_path": item["snapshot_path"],
                    "sha256": item["sha256"],
                }
                for item in lock["contracts"]
            ],
        },
        "inputs": {
            "packet_spec": {
                "path": str(packet_spec_path),
                "sha256": sha256_bytes(packet_bytes),
            },
            "export_profile": {
                "path": str(export_profile_path),
                "sha256": sha256_bytes(profile_bytes),
            },
        },
        "outputs": {
            "artifact": artifact,
            "manifest_sha256": sha256_bytes(manifest_bytes),
        },
        "publication_posture": publication_posture,
        "proof_level": "producer contract and byte-identity proof",
        "proof_ceiling": (
            "The producer proves contract pinning, manifest construction, and local artifact "
            "identity. FUN remains final byte-level acceptance and evidence authority."
        ),
    }
    return ExportResult(manifest=manifest, receipt=receipt)


def write_export_result(
    result: ExportResult, *, manifest_path: Path, receipt_path: Path
) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(result.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt_path.write_text(
        json.dumps(result.receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
