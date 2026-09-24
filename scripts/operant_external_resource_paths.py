"""Shared path semantics for Operant external resource donors."""
from __future__ import annotations


def normalize_resource_root(value: object) -> str:
    root = str(value).strip().strip("/")
    return "" if root in {"", "."} else root


def resource_path_parts(*, path: str, resource_root: object, resource_filename: object) -> list[str] | None:
    root = normalize_resource_root(resource_root)
    filename = str(resource_filename)
    suffix = "/" + filename
    if not path.endswith(suffix):
        return None
    prefix = f"{root}/" if root else ""
    if prefix and not path.startswith(prefix):
        return None
    relative = path[len(prefix) : -len(suffix)]
    parts = [part for part in relative.split("/") if part]
    return parts or None
