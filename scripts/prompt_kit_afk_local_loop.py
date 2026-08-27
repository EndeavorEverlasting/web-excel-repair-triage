#!/usr/bin/env python3
"""Trusted-local AFK feedback loop for Prompt Kit development.

The browser never receives GitHub credentials. A loopback bridge may pass private
feedback here; this coordinator uses the operator's existing local `gh` identity
to route actionable feedback to an optional worker adapter and to integrate only
explicitly opted-in, green `afk-feedback` pull requests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_SCHEMA = "prompt-kit-afk-state/v1"
REQUEST_SCHEMA = "prompt-kit-afk-work-request/v1"
MERGE_LABEL = "afk-feedback"
DEFAULT_STATE = Path("Outputs/prompt-kit-afk/state.json")
DEFAULT_REQUEST_ROOT = Path("Outputs/prompt-kit-afk/requests")
SUCCESS_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
PENDING_STATES = {"QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "EXPECTED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_json(args: list[str], *, cwd: Path) -> Any:
    proc = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\n{detail}")
    return json.loads(proc.stdout or "null")


def _run(args: list[str], *, cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def detect_repo(repo_root: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    data = _run_json(["gh", "repo", "view", "--json", "nameWithOwner"], cwd=repo_root)
    value = str((data or {}).get("nameWithOwner", "")).strip()
    if "/" not in value:
        raise RuntimeError("unable to resolve GitHub repository from local gh identity")
    return value


def resolve_output(repo_root: Path, value: Path) -> Path:
    path = value if value.is_absolute() else repo_root / value
    path = path.resolve()
    outputs = (repo_root / "Outputs").resolve()
    try:
        path.relative_to(outputs)
    except ValueError as exc:
        raise ValueError(f"AFK state must remain under {outputs}") from exc
    return path


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": STATE_SCHEMA, "consumed": {}, "merges": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != STATE_SCHEMA:
        raise ValueError(f"unsupported AFK state: {path}")
    payload.setdefault("consumed", {})
    payload.setdefault("merges", [])
    return payload


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def fingerprint(kind: str, payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256((kind + "\n" + canonical).encode("utf-8")).hexdigest()


def feedback_classification(event: dict[str, Any]) -> str:
    event_type = str(event.get("event_type", ""))
    value = str(event.get("value", ""))
    if event_type == "prompt_feedback" or (event_type == "prompt_vote" and value == "dislike"):
        return "ACTIONABLE_REPAIR"
    if event_type in {"prompt_usage", "prompt_vote"}:
        return "INFORMATION_ONLY"
    return "OUT_OF_SCOPE"


def build_feedback_request(event: dict[str, Any], repo: str) -> dict[str, Any]:
    classification = feedback_classification(event)
    return {
        "schema_version": REQUEST_SCHEMA,
        "created_at": utc_now(),
        "classification": classification,
        "signal": {
            "kind": "prompt_feedback",
            "event_id": event.get("event_id"),
            "prompt_id": event.get("prompt_id"),
            "event_type": event.get("event_type"),
            "value": event.get("value"),
            "comment": event.get("comment"),
            "timestamp": event.get("timestamp"),
        },
        "target": {"repository": repo, "integration_target": "main"},
        "owner": "P07 Repo Sprint Executor",
        "route_hint": "Use P32 for established CI failures and P105 for exact-candidate promotion gates.",
        "mission": (
            "Validate this feedback against current repository/provider truth, repair the smallest "
            "still-valid Prompt Kit surface, keep/add the regression, run owning gates, and integrate "
            "a coherent green slice. Do not stop at a report or open PR."
        ),
        "forbidden_scope": [
            "force-push",
            "credential changes",
            "branch-protection bypass",
            "test weakening",
            "production deployment without its owning gate",
        ],
        "acceptance": [
            "signal identity preserved",
            "current main refreshed",
            "repair or exact blocker produced",
            "owning validators/tests rerun",
            f"resulting PR labeled {MERGE_LABEL!r} only after bounded validation",
        ],
    }


def parse_worker_command(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("PROMPT_KIT_AFK_WORKER_COMMAND must be a JSON argv array") from exc
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise ValueError("PROMPT_KIT_AFK_WORKER_COMMAND must be a non-empty JSON argv array")
    return value


def write_request(request_root: Path, request: dict[str, Any]) -> Path:
    signal_id = str(request.get("signal", {}).get("event_id") or fingerprint("request", request)[:20])
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in signal_id)[:120]
    path = request_root / f"{safe}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != request:
            # Preserve the original signal; version a changed request rather than overwriting it.
            path = request_root / f"{safe}-{fingerprint('request', request)[:10]}.json"
    if not path.exists():
        path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def invoke_worker(worker_argv: list[str], request_path: Path, *, repo_root: Path) -> dict[str, Any]:
    if not worker_argv:
        return {"status": "BLOCKED_WORKER_UNCONFIGURED", "request": str(request_path)}
    proc = _run(worker_argv + [str(request_path)], cwd=repo_root)
    return {
        "status": "WORKER_COMPLETED" if proc.returncode == 0 else "WORKER_FAILED",
        "returncode": proc.returncode,
        "request": str(request_path),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def check_state(item: dict[str, Any]) -> tuple[str, str]:
    status = str(item.get("status") or item.get("state") or "").upper()
    conclusion = str(item.get("conclusion") or item.get("state") or "").upper()
    name = str(item.get("name") or item.get("context") or item.get("workflowName") or "unnamed-check")
    if status in PENDING_STATES or conclusion in PENDING_STATES or not conclusion:
        return "PENDING", name
    if conclusion in SUCCESS_CONCLUSIONS:
        return "GREEN", name
    return "FAILED", name


def evaluate_pr(pr: dict[str, Any], unresolved_threads: int) -> dict[str, Any]:
    labels = {
        str(item.get("name", "")) if isinstance(item, dict) else str(item)
        for item in (pr.get("labels") or [])
    }
    if MERGE_LABEL not in labels:
        return {"decision": "INFORMATION_ONLY", "reason": f"missing {MERGE_LABEL} label"}
    if pr.get("isDraft"):
        return {"decision": "PROMOTION_BLOCKED", "reason": "draft PR"}
    mergeable = str(pr.get("mergeable") or "UNKNOWN").upper()
    if mergeable not in {"MERGEABLE", "TRUE"}:
        return {"decision": "ACTIONABLE_REPAIR" if mergeable == "CONFLICTING" else "PROMOTION_BLOCKED", "reason": f"mergeable={mergeable}"}
    review = str(pr.get("reviewDecision") or "").upper()
    if review == "CHANGES_REQUESTED":
        return {"decision": "ACTIONABLE_REPAIR", "reason": "changes requested"}
    if unresolved_threads:
        return {"decision": "ACTIONABLE_REPAIR", "reason": f"unresolved review threads={unresolved_threads}"}
    checks = pr.get("statusCheckRollup") or []
    if not checks:
        return {"decision": "PROMOTION_BLOCKED", "reason": "no check rollup"}
    failed: list[str] = []
    pending: list[str] = []
    for item in checks:
        state, name = check_state(item if isinstance(item, dict) else {})
        if state == "FAILED":
            failed.append(name)
        elif state == "PENDING":
            pending.append(name)
    if failed:
        return {"decision": "ACTIONABLE_REPAIR", "reason": "failing checks", "checks": failed}
    if pending:
        return {"decision": "PROMOTION_BLOCKED", "reason": "pending checks", "checks": pending}
    return {"decision": "PROMOTE", "reason": "labeled, mergeable, review-clean, all observed checks green"}


def unresolved_thread_count(repo_root: Path, repo: str, number: int) -> int:
    owner, name = repo.split("/", 1)
    query = """query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100){nodes{isResolved}}}}}"""
    data = _run_json(
        ["gh", "api", "graphql", "-f", f"query={query}", "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"number={number}"],
        cwd=repo_root,
    )
    nodes = (((data or {}).get("data") or {}).get("repository") or {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])
    return sum(1 for node in nodes if isinstance(node, dict) and not node.get("isResolved"))


def list_afk_prs(repo_root: Path, repo: str) -> list[dict[str, Any]]:
    data = _run_json(
        [
            "gh", "pr", "list", "--repo", repo, "--state", "open", "--label", MERGE_LABEL,
            "--limit", "20", "--json", "number,headRefOid,mergeable,reviewDecision,statusCheckRollup,isDraft,labels,url,title",
        ],
        cwd=repo_root,
    )
    return data if isinstance(data, list) else []


def merge_pr(repo_root: Path, repo: str, number: int, head_sha: str, *, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"status": "DRY_RUN_PROMOTE", "pr": number, "head_sha": head_sha}
    proc = _run(
        [
            "gh", "api", "--method", "PUT", f"repos/{repo}/pulls/{number}/merge",
            "-f", "merge_method=squash", "-f", f"sha={head_sha}",
        ],
        cwd=repo_root,
    )
    if proc.returncode:
        return {"status": "MERGE_FAILED", "pr": number, "head_sha": head_sha, "error": (proc.stderr or proc.stdout).strip()}
    payload = json.loads(proc.stdout or "{}")
    return {"status": "MERGED" if payload.get("merged") else "MERGE_REJECTED", "pr": number, "head_sha": head_sha, "merge_sha": payload.get("sha"), "message": payload.get("message")}


def provider_request(pr: dict[str, Any], gate: dict[str, Any], repo: str) -> dict[str, Any]:
    return {
        "schema_version": REQUEST_SCHEMA,
        "created_at": utc_now(),
        "classification": gate["decision"],
        "signal": {
            "kind": "provider_pr_gate",
            "event_id": f"pr-{pr.get('number')}-{pr.get('headRefOid')}-{fingerprint('gate', gate)[:10]}",
            "pr_number": pr.get("number"),
            "head_sha": pr.get("headRefOid"),
            "reason": gate.get("reason"),
            "checks": gate.get("checks", []),
            "url": pr.get("url"),
        },
        "target": {"repository": repo, "integration_target": "main"},
        "owner": "P32 Failing CI Repair" if gate.get("reason") == "failing checks" else "P07 Repo Sprint Executor",
        "route_hint": "Return the repaired exact candidate through P105 promotion; preserve the afk-feedback label only while AFK integration remains authorized.",
        "mission": "Repair the exact current provider gate, rerun affected proof, consume new feedback, and leave a green mergeable candidate or an exact blocker.",
        "forbidden_scope": ["force-push", "test weakening", "credential expansion", "self-approval of protected deployment"],
        "acceptance": ["exact head preserved or superseded explicitly", "gate rerun", "review queue rechecked", "integration state reported"],
    }


def one_pass(
    *,
    repo_root: Path,
    repo: str,
    state_path: Path,
    request_root: Path,
    worker_argv: list[str],
    feedback_event: dict[str, Any] | None,
    dry_run: bool,
) -> dict[str, Any]:
    state = load_state(state_path)
    changed = False
    actions: list[dict[str, Any]] = []

    if feedback_event:
        signal = fingerprint("feedback", feedback_event)
        classification = feedback_classification(feedback_event)
        if signal not in state["consumed"]:
            if classification == "ACTIONABLE_REPAIR":
                request = build_feedback_request(feedback_event, repo)
                path = write_request(request_root, request)
                worker = invoke_worker(worker_argv, path, repo_root=repo_root)
                actions.append({"signal": signal, "classification": classification, "worker": worker})
            else:
                actions.append({"signal": signal, "classification": classification})
            state["consumed"][signal] = {"at": utc_now(), "classification": classification}
            changed = True

    for pr in list_afk_prs(repo_root, repo):
        number = int(pr["number"])
        unresolved = unresolved_thread_count(repo_root, repo, number)
        gate = evaluate_pr(pr, unresolved)
        gate_signal = fingerprint("pr-gate", {"number": number, "head": pr.get("headRefOid"), "gate": gate})
        if gate["decision"] == "PROMOTE":
            result = merge_pr(repo_root, repo, number, str(pr.get("headRefOid") or ""), dry_run=dry_run)
            actions.append({"signal": gate_signal, "gate": gate, "promotion": result})
            if result["status"] in {"MERGED", "DRY_RUN_PROMOTE"}:
                state["consumed"][gate_signal] = {"at": utc_now(), "classification": "PROMOTION"}
                state["merges"].append(result | {"at": utc_now()})
                changed = True
        elif gate["decision"] == "ACTIONABLE_REPAIR" and gate_signal not in state["consumed"]:
            request = provider_request(pr, gate, repo)
            path = write_request(request_root, request)
            worker = invoke_worker(worker_argv, path, repo_root=repo_root)
            actions.append({"signal": gate_signal, "gate": gate, "worker": worker})
            state["consumed"][gate_signal] = {"at": utc_now(), "classification": "ACTIONABLE_REPAIR"}
            changed = True
        else:
            actions.append({"signal": gate_signal, "gate": gate})

    if len(state["consumed"]) > 2000:
        newest = list(state["consumed"].items())[-2000:]
        state["consumed"] = dict(newest)
        changed = True
    if len(state["merges"]) > 200:
        state["merges"] = state["merges"][-200:]
        changed = True
    if changed:
        save_state(state_path, state)
    return {"schema_version": STATE_SCHEMA, "repository": repo, "changed": changed, "actions": actions}


def read_feedback_event(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("event"), dict):
        payload = payload["event"]
    if not isinstance(payload, dict):
        raise ValueError("feedback event file must contain one event object")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repo")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--request-root", type=Path, default=DEFAULT_REQUEST_ROOT)
    parser.add_argument("--feedback-event", type=Path)
    parser.add_argument("--worker-command", help="JSON argv array; defaults to PROMPT_KIT_AFK_WORKER_COMMAND")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    state_path = resolve_output(repo_root, args.state)
    request_root = resolve_output(repo_root, args.request_root)
    worker_argv = parse_worker_command(args.worker_command or os.environ.get("PROMPT_KIT_AFK_WORKER_COMMAND"))
    repo = detect_repo(repo_root, args.repo)
    feedback_event = read_feedback_event(args.feedback_event)
    if args.poll_seconds and args.poll_seconds < 60:
        raise SystemExit("--poll-seconds must be 0 or at least 60 seconds")

    first = True
    try:
        while True:
            report = one_pass(
                repo_root=repo_root,
                repo=repo,
                state_path=state_path,
                request_root=request_root,
                worker_argv=worker_argv,
                feedback_event=feedback_event if first else None,
                dry_run=args.dry_run,
            )
            print(json.dumps(report, sort_keys=True))
            first = False
            if not args.poll_seconds:
                break
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        return 130
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Prompt Kit AFK loop failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
