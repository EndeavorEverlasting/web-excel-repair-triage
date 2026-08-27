#!/usr/bin/env python3
"""Build and serve the Prompt Kit with portable Favorites and optional private feedback bridge."""
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

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import prompt_kit_afk_local_loop as afk_local  # noqa: E402
from scripts import prompt_kit_feedback_bridge as feedback_bridge  # noqa: E402

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
            "Browser download, file-picker, profile transfer, private feedback dispatch, "
            "and cross-device acceptance require observed runtime proof."
        ),
    }
    manifest_backup = backup_existing_output(repo_root, manifest_path)
    if manifest_backup:
        receipt["backups"]["manifest"] = str(manifest_backup.relative_to(repo_root))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


class PortablePromptKitHandler(SimpleHTTPRequestHandler):
    """Serve the generated artifact and, when enabled, a guarded loopback feedback endpoint."""

    server_version = "PromptKitPortable/1.1"

    def __init__(
        self,
        *args: object,
        directory: str | None = None,
        repo_root: Path | None = None,
        feedback_repo: str | None = None,
        feedback_bridge_enabled: bool = False,
        **kwargs: object,
    ) -> None:
        self.repo_root = (repo_root or REPO_ROOT).resolve()
        self.feedback_repo = feedback_repo
        self.feedback_bridge_enabled = feedback_bridge_enabled
        super().__init__(*args, directory=directory, **kwargs)

    def _allowed_origin(self) -> str | None:
        origin = str(self.headers.get("Origin") or "").strip()
        if not origin:
            return None
        if origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:"):
            return origin
        if self.feedback_repo:
            owner = self.feedback_repo.split("/", 1)[0].casefold()
            if origin.casefold() == f"https://{owner}.github.io":
                return origin
        return None

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        allowed = self._allowed_origin()
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
        super().end_headers()

    def _json_response(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

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

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path.rstrip("/") != "/feedback" or not self.feedback_bridge_enabled or not self._allowed_origin():
            self._json_response(403, {"status": "FORBIDDEN"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Prompt-Kit-Bridge")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path.rstrip("/") != "/feedback":
            self._json_response(404, {"status": "NOT_FOUND"})
            return
        if not self.feedback_bridge_enabled or not self.feedback_repo:
            self._json_response(404, {"status": "BRIDGE_DISABLED"})
            return
        if not self._allowed_origin() or self.headers.get("X-Prompt-Kit-Bridge") != "v1":
            self._json_response(403, {"status": "FORBIDDEN"})
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            self._json_response(400, {"status": "INVALID_LENGTH"})
            return
        if length < 1 or length > feedback_bridge.MAX_ENVELOPE_BYTES:
            self._json_response(413, {"status": "INVALID_SIZE"})
            return
        payload = self.rfile.read(length)
        try:
            result = feedback_bridge.accept_private_feedback(
                repo_root=self.repo_root,
                repo=self.feedback_repo,
                payload=payload,
            )
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            self._json_response(400, {"status": "REJECTED", "error": str(exc)[:500]})
            return
        status = 202 if result.get("status") != "DUPLICATE" else 200
        self._json_response(status, result)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        normalized = self.path.rstrip("/")
        if normalized == "/healthz":
            self._json_response(200, self._served_artifact_status())
            return
        if normalized == "/feedback/healthz":
            self._json_response(
                200,
                {
                    "status": "ok" if self.feedback_bridge_enabled else "disabled",
                    "schema_version": feedback_bridge.PRIVATE_DISPATCH_SCHEMA,
                    "bridge_enabled": self.feedback_bridge_enabled,
                    "repository": self.feedback_repo if self.feedback_bridge_enabled else None,
                    "pending_private_events": feedback_bridge.pending_count(self.repo_root),
                },
            )
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
    parser.add_argument("--feedback-bridge", action="store_true", help="enable private browser feedback POST /feedback on the loopback server")
    parser.add_argument("--feedback-repo", help="GitHub owner/repo; defaults to the repository resolved by local gh")
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
    if args.feedback_bridge and not args.serve:
        print("Prompt Kit feedback bridge requires --serve", file=sys.stderr)
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
        feedback_repo = afk_local.detect_repo(repo_root, args.feedback_repo) if args.feedback_bridge else None
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(f"Prompt Kit portable build failed: {exc}", file=sys.stderr)
        return 1

    print(f"PROMPT_KIT_PORTABLE_ARTIFACT={output_path}")
    print(f"PROMPT_KIT_PORTABLE_SHA256={receipt['artifact']['sha256']}")
    print(f"PROMPT_KIT_PORTABLE_MANIFEST={manifest_path}")
    print(f"PROMPT_KIT_PORTABLE_URL={origin}")
    if args.feedback_bridge:
        print(f"PROMPT_KIT_FEEDBACK_BRIDGE={origin}feedback")
        print(f"PROMPT_KIT_FEEDBACK_REPO={feedback_repo}")

    if args.serve:
        handler = partial(
            PortablePromptKitHandler,
            directory=str(output_path.parent),
            repo_root=repo_root,
            feedback_repo=feedback_repo,
            feedback_bridge_enabled=args.feedback_bridge,
        )
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
