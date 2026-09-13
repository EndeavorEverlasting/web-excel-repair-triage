from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA_VERSION = "operant-release-pr-request/v1"


def build_body(*, version: str, source_sha: str) -> str:
    return f"""## Operant deterministic release

This PR was derived AFK from accepted mainline development by `scripts/operant_version.py`.

- next version: `{version}`
- source mainline: `{source_sha}`
- plan: `Outputs/operant-version-plan.json` in the workflow run
- authority: `OPERANT_VERSION`
- validation: Operant version + identity tests, generated-site parity, stale-candidate rejection, and `git diff --check`
- first-PR publication authority: external provider/agent because repository Actions settings prohibit `GITHUB_TOKEN` from creating pull requests; Actions may refresh an already-open release PR

Merge is the explicit release gate. After this exact version change reaches `main`, the mainline owner validates it again and creates `operant-v{version}` plus the GitHub Release at the exact merged commit.
"""


def build_request(
    *,
    version: str,
    source_sha: str,
    head: str,
    base: str,
    existing_pr_url: str = "",
) -> dict[str, object]:
    title = f"chore(operant): release v{version}"
    requires_external_creation = not bool(existing_pr_url)
    return {
        "schema_version": SCHEMA_VERSION,
        "publication_owner": "external-provider" if requires_external_creation else "github-actions-refresh",
        "publication_mode": "external-create" if requires_external_creation else "refresh-existing-pr",
        "requires_external_pr_creation": requires_external_creation,
        "existing_pr_url": existing_pr_url or None,
        "base": base,
        "head": head,
        "title": title,
        "body": build_body(version=version, source_sha=source_sha),
        "version": version,
        "source_sha": source_sha,
        "merge_gate": "explicit",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit the machine-readable publication request for an Operant release candidate PR."
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base", default="main")
    parser.add_argument("--existing-pr-url", default="")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--body-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_request(
        version=args.version,
        source_sha=args.source_sha,
        head=args.head,
        base=args.base,
        existing_pr_url=args.existing_pr_url,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.body_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.body_output.write_text(str(payload["body"]), encoding="utf-8")

    print(
        "OPERANT_RELEASE_PR_REQUEST_PASS "
        f"version={args.version} head={args.head} base={args.base} "
        f"mode={payload['publication_mode']} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
