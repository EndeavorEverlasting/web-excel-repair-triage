from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

DOCUMENT_LOCK_SCHEMA = "web-excel-fun-nth-document-reference-lock/v1"
CANONICAL_FUN_REPOSITORY = "EndeavorEverlasting/FUN"
CANONICAL_CONSUMER_REPOSITORY = "EndeavorEverlasting/web-excel-repair-triage"
PASS_STATUS = "PASS"


class FunNthDocumentReferenceError(ValueError):
    """Raised when a protected Drive identity is absent, ambiguous, or not accepted."""


@dataclass(frozen=True)
class RegisteredDocument:
    id: str
    packet_id: str
    artifact_type: str
    publication_posture: str
    drive_file_id: str
    drive_folder_id: str
    title: str
    status: str
    validation_status: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FunNthDocumentReferenceError(f"missing document-reference lock: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FunNthDocumentReferenceError(f"invalid document-reference lock {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise FunNthDocumentReferenceError("document-reference lock must be an object")
    return payload


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FunNthDocumentReferenceError(f"{label} must be a non-empty string")
    return value.strip()


def load_document_reference_lock(path: Path) -> tuple[dict[str, Any], tuple[RegisteredDocument, ...]]:
    lock = _load_json(path)
    if lock.get("schema") != DOCUMENT_LOCK_SCHEMA:
        raise FunNthDocumentReferenceError("unsupported document-reference lock schema")
    if lock.get("canonical_owner") != CANONICAL_FUN_REPOSITORY:
        raise FunNthDocumentReferenceError("document-reference canonical owner drifted")
    if lock.get("consumer_repository") != CANONICAL_CONSUMER_REPOSITORY:
        raise FunNthDocumentReferenceError("document-reference consumer repository drifted")

    fun_commit = _required_string(lock.get("fun_commit"), "fun_commit")
    if len(fun_commit) != 40 or any(ch not in "0123456789abcdef" for ch in fun_commit):
        raise FunNthDocumentReferenceError("fun_commit must be a lowercase 40-character Git SHA")
    _required_string(lock.get("source_path"), "source_path")
    blob_sha = _required_string(lock.get("git_blob_sha"), "git_blob_sha")
    if len(blob_sha) != 40 or any(ch not in "0123456789abcdef" for ch in blob_sha):
        raise FunNthDocumentReferenceError("git_blob_sha must be a lowercase 40-character Git SHA")

    raw_documents = lock.get("documents")
    if not isinstance(raw_documents, list) or not raw_documents:
        raise FunNthDocumentReferenceError("document-reference lock must contain documents")

    documents: list[RegisteredDocument] = []
    ids: set[str] = set()
    drive_ids: set[str] = set()
    for index, raw in enumerate(raw_documents):
        if not isinstance(raw, dict):
            raise FunNthDocumentReferenceError(f"documents[{index}] must be an object")
        document = RegisteredDocument(
            id=_required_string(raw.get("id"), f"documents[{index}].id"),
            packet_id=_required_string(raw.get("packet_id"), f"documents[{index}].packet_id"),
            artifact_type=_required_string(raw.get("artifact_type"), f"documents[{index}].artifact_type"),
            publication_posture=_required_string(
                raw.get("publication_posture"), f"documents[{index}].publication_posture"
            ),
            drive_file_id=_required_string(raw.get("drive_file_id"), f"documents[{index}].drive_file_id"),
            drive_folder_id=_required_string(
                raw.get("drive_folder_id"), f"documents[{index}].drive_folder_id"
            ),
            title=_required_string(raw.get("title"), f"documents[{index}].title"),
            status=_required_string(raw.get("status"), f"documents[{index}].status"),
            validation_status=_required_string(
                raw.get("validation_status"), f"documents[{index}].validation_status"
            ),
        )
        if document.id in ids:
            raise FunNthDocumentReferenceError(f"duplicate document id: {document.id}")
        if document.drive_file_id in drive_ids:
            raise FunNthDocumentReferenceError(
                f"duplicate Drive file id: {document.drive_file_id}"
            )
        ids.add(document.id)
        drive_ids.add(document.drive_file_id)
        documents.append(document)
    return lock, tuple(documents)


def resolve_registered_document(
    *,
    lock_path: Path,
    packet_id: str,
    artifact_type: str,
    artifact_filename: str,
    drive_file_id: str,
    drive_folder_id: str | None,
    require_validation_pass: bool = True,
) -> tuple[dict[str, Any], RegisteredDocument]:
    lock, documents = load_document_reference_lock(lock_path)
    matches = [document for document in documents if document.drive_file_id == drive_file_id]
    if not matches:
        raise FunNthDocumentReferenceError(
            f"Drive file id is not registered for NTH use: {drive_file_id}"
        )
    if len(matches) != 1:
        raise FunNthDocumentReferenceError(
            f"Drive file id resolves ambiguously: {drive_file_id}"
        )
    document = matches[0]
    if document.packet_id != packet_id:
        raise FunNthDocumentReferenceError(
            f"Drive document packet mismatch: {document.packet_id} != {packet_id}"
        )
    if document.artifact_type != artifact_type:
        raise FunNthDocumentReferenceError(
            f"Drive document artifact type mismatch: {document.artifact_type} != {artifact_type}"
        )
    if drive_folder_id and document.drive_folder_id != drive_folder_id:
        raise FunNthDocumentReferenceError(
            f"Drive folder mismatch: {document.drive_folder_id} != {drive_folder_id}"
        )
    if document.title != artifact_filename:
        raise FunNthDocumentReferenceError(
            f"artifact filename does not match registered Drive title: {artifact_filename} != {document.title}"
        )
    if require_validation_pass and document.validation_status != PASS_STATUS:
        raise FunNthDocumentReferenceError(
            "registered Drive document is not accepted for final manifest production: "
            f"{document.id} status={document.status} validation={document.validation_status}"
        )
    return lock, document
