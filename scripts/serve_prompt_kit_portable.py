#!/usr/bin/env python3
"""Build and serve the Prompt Kit with portable Favorites on a stable local origin."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "prompt-kit-portable-artifact/v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}
RUNTIME_MARKER = "prompt-kit-favorites/v1"
CLOSING_BODY = "</body>"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def require_file(path: Path, label: str) -> bytes:
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    payload = path.read_bytes()
    if not payload:
        raise ValueError(f"{label} is empty: {path}")
    return payload


def require_output_path(repo_root: Path, path: Path) -> None:
    outputs = (repo_root / "Outputs").resolve()
    try:
        path.relative_to(outputs)
    except ValueError as exc:
        raise ValueError(f"portable artifact output must remain under {outputs}") from exc


def backup_existing_output(repo_root: Path, path: Path) -> Path | None:
    """Preserve an existing generated file before replacement."""
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"portable output exists but is not a file: {path}")
    backup_root = (repo_root / "Outputs" / "backups" / "prompt-kit-portable").resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_root / f"{stamp}-{path.name}"
    shutil.copy2(path, destination)
    return destination


def compose_portable_html(source: str, runtime: str) -> str:
    """Append the portability runtime after all canonical Prompt Kit runtimes."""
    if RUNTIME_MARKER in source:
        raise ValueError(
            "canonical Prompt Kit site already contains the portable runtime; "
            "refusing duplicate injection"
        )
    if source.count(CLOSING_BODY) != 1:
        raise ValueError(
            "canonical Prompt Kit site must contain exactly one closing body marker"
        )
    if RUNTIME_MARKER not in runtime:
        raise ValueError("portable Favorites runtime is missing its schema marker")
    injection = f"<script>\n{runtime}\n</script>\n{CLOSING_BODY}"
    return source.replace(CLOSING_BODY, injection, 1)


def build_portable_artifact(
    *,
    repo_root: Path,
    source_path: Path,
    runtime_path: Path,
    output_path: Path,
    manifest_path: Path,
    origin: str,
) -> dict[str, Any]:
    """Generate the served artifact and its reproducible receipt."""
    require_output_path(repo_root, output_path)
    require_output_path(repo_root, manifest_path)

    source_bytes = require_file(source_path, "canonical Prompt Kit site")
    runtime_bytes = require_file(runtime_path, "portable Favorites runtime")
    source = source_bytes.decode("utf-8")
    runtime = runtime_bytes.decode("utf-8").strip()
    artifact = compose_portable_html(source, runtime)
    artifact_bytes = artifact.encode("utf-8")

    artifact_backup = backup_existing_output(repo_root, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(artifact_bytes)

    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stable_origin": origin,
        "source": {
            "path": str(source_path.relative_to(repo_root)),
            "sha256": sha256_bytes(source_bytes),
            "bytes": len(source_bytes),
        },
        "runtime": {
            "path": str(runtime_path.relative_to(repo_root)),
            "sha256": sha256_bytes(runtime_bytes),
            "bytes": len(runtime_bytes),
            "schema": RUNTIME_MARKER,
        },
        "artifact": {
            "path": str(output_path.relative_to(repo_root)),
            "sha256": sha256_bytes(artifact_bytes),
            "bytes": len(artifact_bytes),
        },
        "backups": {
            "artifact": str(artifact_backup.relative_to(repo_root)) if artifact_backup else None,
            "manifest": None,
        },
        "guardrails": {
            "loopback_only": True,
            "cache_disabled": True,
            "protected_inputs_untouched": True,
            "canonical_site_untouched": True,
            "health_hash_matches_served_artifact": True,
            "overwrite_backup_required": True,
        },
        "proof_ceiling": (
            "Generation and local HTTP serving prove a stable-origin artifact. "
            "Browser download, file-picker, profile transfer, and cross-device "
            "acceptance require observed browser proof."
        ),
    }
    manifest_backup = backup_existing_output(repo_root, manifest_path)
    if manifest_backup:
        receipt["backups"]["manifest"] = str(manifest_backup.relative_to(repo_root))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


class PortablePromptKitHandler(SimpleHTTPRequestHandler):
    """Serve only the generated artifact directory with no browser caching."""

    server_version = "PromptKitPortable/1.0"

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        super().end_headers()

    def _served_artifact_status(self) -> dict[str, Any]:
        artifact_path = Path(self.directory).resolve() / "index.html"
        try:
            payload = artifact_path.read_bytes()
        except OSError as exc:
            return {
                "status": "error",
                "schema_version": SCHEMA_VERSION,
                "artifact": "index.html",
                "error": str(exc),
            }
        return {
            "status": "ok",
            "schema_version": SCHEMA_VERSION,
            "artifact": "index.html",
            "artifact_sha256": sha256_bytes(payload),
            "artifact_bytes": len(payload),
        }

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path.rstrip("/") == "/healthz":
            payload = json.dumps(self._served_artifact_status()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path in {"", "/"}:
            self.path = "/index.html"
        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        print(f"PromptKitPortable: {format % args}", file=sys.stderr)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source", default="web/prompt-kit/index.html")
    parser.add_argument("--runtime", default="docs/prompt-kit-favorites-portability.js")
    parser.add_argument("--output", default="Outputs/prompt-kit-portable/index.html")
    parser.add_argument("--manifest", default="Outputs/prompt-kit-portable/manifest.json")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--serve", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    if not (repo_root / ".git").exists() and repo_root != Path(__file__).resolve().parents[1]:
        print(f"Prompt Kit portable build failed: not a Git root: {repo_root}", file=sys.stderr)
        return 2
    if args.host not in ALLOWED_HOSTS:
        print(
            "Prompt Kit portable server refuses non-loopback host: " f"{args.host}",
            file=sys.stderr,
        )
        return 2
    if not 1 <= args.port <= 65535:
        print("Prompt Kit portable server port is outside 1..65535", file=sys.stderr)
        return 2
    if not args.build_only and not args.serve:
        args.build_only = True

    source_path = resolve_path(repo_root, args.source)
    runtime_path = resolve_path(repo_root, args.runtime)
    output_path = resolve_path(repo_root, args.output)
    manifest_path = resolve_path(repo_root, args.manifest)
    origin = f"http://{args.host}:{args.port}/"

    try:
        receipt = build_portable_artifact(
            repo_root=repo_root,
            source_path=source_path,
            runtime_path=runtime_path,
            output_path=output_path,
            manifest_path=manifest_path,
            origin=origin,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Prompt Kit portable build failed: {exc}", file=sys.stderr)
        return 1

    print(f"PROMPT_KIT_PORTABLE_ARTIFACT={output_path}")
    print(f"PROMPT_KIT_PORTABLE_SHA256={receipt['artifact']['sha256']}")
    print(f"PROMPT_KIT_PORTABLE_MANIFEST={manifest_path}")
    print(f"PROMPT_KIT_PORTABLE_URL={origin}")

    if args.serve:
        handler = partial(PortablePromptKitHandler, directory=str(output_path.parent))
        try:
            server = ThreadingHTTPServer((args.host, args.port), handler)
        except OSError as exc:
            print(f"Prompt Kit portable server failed to bind: {exc}", file=sys.stderr)
            return 3
        print(
            "Prompt Kit portable server listening at "
            f"{origin} (artifact {receipt['artifact']['sha256']})"
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
