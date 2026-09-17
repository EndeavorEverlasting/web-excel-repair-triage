#!/usr/bin/env python3
"""Prototype a provenance-rich semantic extraction seam for pinned upstream skills.

This module is intentionally separate from the production external-resource sync.
It accepts one pinned skill body, extracts deterministic directive candidates, and
emits a receipt that later semantic/comparison stages can consume without copying
upstream bodies into Prompt Kit's canonical metadata projection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "operant-external-skill-semantic-prototype/v1"
RAW_GITHUB_HOST = "raw.githubusercontent.com"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+?)\s*$")
DIRECTIVE_RE = re.compile(
    r"\b(must|never|always|do not|don't|keep|use|stop|confirm|prefer|require|should|"
    r"follow|resolve|install|fetch|verify|record|capture|poll|retry|cleanup|remove|"
    r"regenerate|check|run|create|start|wait|report|preserve|avoid|ensure)\b",
    re.IGNORECASE,
)
SIGNAL_TERMS: dict[str, tuple[str, ...]] = {
    "isolation": ("worktree", "branch", "parallel", "shared resource", "shared database", "port"),
    "freshness": ("fetch", "latest", "current head", "head sha", "revision", "origin/main", "default branch"),
    "collision": ("open pr", "changed files", "uncommitted", "conflict", "another agent", "reuse"),
    "dependency": ("install dependencies", "node_modules", "virtualenv", "lockfile", "runtime version"),
    "cleanup": ("cleanup", "remove", "delete", "merged or closed", "after merge"),
    "evidence": ("evidence", "proof", "assertion", "recording", "screenshot", "verify", "tested against"),
    "review": ("review", "comment", "thread", "confidence", "greptile", "pull request", "merge request"),
    "retry": ("poll", "retry", "attempt", "timeout", "iteration", "stale", "wait for"),
    "ownership": ("canonical", "owner", "authority", "another agent", "assigned branch", "existing owner"),
    "style": ("prose", "filler", "puffery", "wording", "writing", "tone"),
}


def body_sha256(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str], int]:
    """Return minimal front-matter metadata and the first body line index."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = next((idx for idx in range(1, len(lines)) if lines[idx].strip() == "---"), None)
    if end is None:
        raise ValueError("unterminated front matter")
    meta: dict[str, str] = {}
    idx = 1
    while idx < end:
        line = lines[idx]
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            idx += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if value in {">", "|"}:
            folded: list[str] = []
            idx += 1
            while idx < end and (not lines[idx].strip() or lines[idx].startswith((" ", "\t"))):
                if lines[idx].strip():
                    folded.append(lines[idx].strip())
                idx += 1
            meta[key] = " ".join(folded)
            continue
        meta[key] = value.strip('"\'')
        idx += 1
    return meta, end + 1


def signal_names(text: str) -> list[str]:
    lower = text.lower()
    return sorted(name for name, terms in SIGNAL_TERMS.items() if any(term in lower for term in terms))


def _append_candidate(
    candidates: list[dict[str, Any]],
    *,
    structure: str,
    section: str | None,
    start_line: int,
    end_line: int,
    pieces: list[str],
    require_directive_language: bool,
) -> None:
    text = " ".join(piece.strip() for piece in pieces if piece.strip()).strip()
    if not text or (require_directive_language and not DIRECTIVE_RE.search(text)):
        return
    candidates.append(
        {
            "structure": structure,
            "section": section,
            "line_start": start_line,
            "line_end": end_line,
            "text": text,
            "signals": signal_names(text),
        }
    )


def extract_directive_candidates(body: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    lines = body.splitlines()
    metadata, body_start = parse_front_matter(lines)
    candidates: list[dict[str, Any]] = []
    section: str | None = None
    fenced = False
    paragraph: list[str] = []
    paragraph_start: int | None = None
    list_item: list[str] = []
    list_start: int | None = None

    def flush_paragraph(before_line: int) -> None:
        nonlocal paragraph, paragraph_start
        if paragraph and paragraph_start is not None:
            _append_candidate(
                candidates,
                structure="policy_paragraph",
                section=section,
                start_line=paragraph_start,
                end_line=max(before_line, paragraph_start),
                pieces=paragraph,
                require_directive_language=True,
            )
        paragraph = []
        paragraph_start = None

    def flush_list(before_line: int) -> None:
        nonlocal list_item, list_start
        if list_item and list_start is not None:
            _append_candidate(
                candidates,
                structure="list_item",
                section=section,
                start_line=list_start,
                end_line=max(before_line, list_start),
                pieces=list_item,
                require_directive_language=False,
            )
        list_item = []
        list_start = None

    for zero_idx in range(body_start, len(lines)):
        line_no = zero_idx + 1
        raw = lines[zero_idx]
        stripped = raw.strip()
        if stripped.startswith("```"):
            flush_list(line_no - 1)
            flush_paragraph(line_no - 1)
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = HEADING_RE.match(stripped)
        if heading:
            flush_list(line_no - 1)
            flush_paragraph(line_no - 1)
            section = heading.group(2).strip()
            continue
        matched_list = LIST_RE.match(raw)
        if matched_list:
            flush_list(line_no - 1)
            flush_paragraph(line_no - 1)
            list_start = line_no
            list_item = [matched_list.group(1).strip()]
            continue
        if not stripped:
            flush_list(line_no - 1)
            flush_paragraph(line_no - 1)
            continue
        if list_item and raw.startswith((" ", "\t")):
            list_item.append(stripped)
            continue
        if list_item:
            flush_list(line_no - 1)
        if paragraph_start is None:
            paragraph_start = line_no
        paragraph.append(stripped)

    flush_list(len(lines))
    flush_paragraph(len(lines))

    for idx, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = f"D{idx:03d}"
    return metadata, candidates


def validate_pinned_raw_url(url: str, *, repository: str, source_sha: str, path: str) -> None:
    parsed = urllib.parse.urlparse(url)
    expected_path = f"/{repository}/{source_sha}/{path}"
    if parsed.scheme != "https" or parsed.netloc != RAW_GITHUB_HOST or parsed.path != expected_path:
        raise ValueError("source URL must be an exact raw.githubusercontent.com URL pinned to repository/source_sha/path")


def fetch_pinned_body(url: str, *, repository: str, source_sha: str, path: str) -> str:
    validate_pinned_raw_url(url, repository=repository, source_sha=source_sha, path=path)
    request = urllib.request.Request(url, headers={"User-Agent": "OperantSemanticPrototype/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"pinned skill fetch failed: {exc}") from exc


def build_receipt(
    *,
    source_id: str,
    resource_id: str,
    repository: str,
    source_sha: str,
    path: str,
    body: str,
    expected_body_sha256: str | None = None,
) -> dict[str, Any]:
    observed = body_sha256(body)
    if expected_body_sha256 and observed != expected_body_sha256:
        raise ValueError(
            f"body sha256 mismatch for {resource_id}: expected {expected_body_sha256}, observed {observed}"
        )
    metadata, directives = extract_directive_candidates(body)
    if not directives:
        raise ValueError(f"no directive candidates extracted from {resource_id}")
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "source_id": source_id,
            "resource_id": resource_id,
            "repository": repository,
            "source_sha": source_sha,
            "path": path,
            "body_sha256": observed,
        },
        "document": {
            "name": metadata.get("name"),
            "description": metadata.get("description"),
        },
        "summary": {
            "directive_count": len(directives),
            "signal_counts": {
                signal: sum(signal in row["signals"] for row in directives)
                for signal in sorted(SIGNAL_TERMS)
            },
        },
        "directive_candidates": directives,
        "proof_ceiling": (
            "Deterministic Markdown/front-matter parsing and provenance-rich directive candidates only. "
            "Signals are lexical hints, not proof of semantic equivalence, adoption fitness, or upstream authority."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--path", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--body-file", type=Path)
    group.add_argument("--url")
    parser.add_argument("--expected-body-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.body_file:
            body = args.body_file.read_text(encoding="utf-8")
        else:
            body = fetch_pinned_body(
                args.url,
                repository=args.repository,
                source_sha=args.source_sha,
                path=args.path,
            )
        receipt = build_receipt(
            source_id=args.source_id,
            resource_id=args.resource_id,
            repository=args.repository,
            source_sha=args.source_sha,
            path=args.path,
            body=body,
            expected_body_sha256=args.expected_body_sha256,
        )
        payload = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"External skill semantic prototype failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
