#!/usr/bin/env python3
"""GitHub runtime adapter for the provider-neutral repository promotion contract."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "harness/promotion/required-checks.v1.json"
CONTRACT_PATH = ROOT / "harness/contracts/repository-promotion.v1.json"
SHA = re.compile(r"^[0-9a-f]{40}$")


class ProviderError(RuntimeError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class GitHub:
    def __init__(self) -> None:
        self.repo = os.environ.get("GITHUB_REPOSITORY", "")
        self.server_url = os.environ.get("GITHUB_SERVER_URL", "").rstrip("/")
        self.api = os.environ.get("GITHUB_API_URL", "").rstrip("/")
        self.graphql_url = os.environ.get("GITHUB_GRAPHQL_URL", "")
        self.token = os.environ.get("GITHUB_TOKEN", "")
        if "/" not in self.repo or not self.server_url or not self.api or not self.graphql_url or not self.token:
            raise ProviderError("PROVIDER_PARTIAL_TRUTH", "required GitHub runtime identity is unavailable")

    def call(self, method: str, url: str, body: dict[str, Any] | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode()
        for attempt in range(3):
            req = urllib.request.Request(
                url if url.startswith("http") else self.api + url,
                method=method,
                data=data,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "repository-promotion-adapter/1",
                    **({"Content-Type": "application/json"} if data else {}),
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    raw = response.read()
                    return json.loads(raw.decode()) if raw else {}
            except urllib.error.HTTPError as exc:
                rate = exc.code == 429 or (exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0")
                transient = rate or exc.code in {502, 503, 504}
                if transient and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                if rate:
                    raise ProviderError("PROVIDER_RATE_LIMITED", f"GitHub API rate limited: {method} {url}") from exc
                if exc.code >= 500:
                    raise ProviderError("PROVIDER_UNAVAILABLE", f"GitHub API unavailable: HTTP {exc.code}") from exc
                raise ProviderError("PROVIDER_PARTIAL_TRUTH", f"required GitHub truth unavailable: HTTP {exc.code} {method} {url}") from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise ProviderError("PROVIDER_UNAVAILABLE", f"GitHub API unavailable: {exc}") from exc
        raise ProviderError("PROVIDER_UNAVAILABLE", "GitHub API retry ceiling reached")

    def rest(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        return self.call(method, path, body)

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        data = self.call("POST", self.graphql_url, {"query": query, "variables": variables})
        if data.get("errors") or not isinstance(data.get("data"), dict):
            raise ProviderError("PROVIDER_PARTIAL_TRUTH", "GitHub GraphQL returned incomplete required truth")
        return data["data"]


def event_target(event: dict[str, Any], event_name: str) -> tuple[int | None, int | None]:
    if event_name == "workflow_run":
        run = event.get("workflow_run") or {}
        prs = run.get("pull_requests") or []
        if len(prs) == 1 and isinstance(prs[0], dict):
            return int(prs[0]["number"]), int(run["id"])
        return None, int(run.get("id") or 0) or None
    if event_name == "workflow_dispatch":
        raw = (event.get("inputs") or {}).get("pr_number")
        return (int(raw), None) if str(raw or "").isdigit() else (None, None)
    pr = event.get("pull_request")
    return (int(pr["number"]), None) if isinstance(pr, dict) and isinstance(pr.get("number"), int) else (None, None)


def exact_list(payload: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", f"provider response lacks {key}")
    total = int(payload.get("total_count", len(payload[key])))
    if total > len(payload[key]):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", f"{key} exceeds bounded provider page")
    return [item for item in payload[key] if isinstance(item, dict)]


def review_truth(gh: GitHub, number: int) -> dict[str, Any]:
    owner, repo = gh.repo.split("/", 1)
    query = """query($owner:String!,$repo:String!,$number:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$number){reviewDecision reviewThreads(first:100){nodes{isResolved} pageInfo{hasNextPage}}}}}"""
    data = gh.graphql(query, {"owner": owner, "repo": repo, "number": number})
    pr = ((data.get("repository") or {}).get("pullRequest"))
    threads = (pr or {}).get("reviewThreads")
    if not isinstance(pr, dict) or not isinstance(threads, dict):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "review decision/thread truth is unavailable")
    if (threads.get("pageInfo") or {}).get("hasNextPage"):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "review threads exceed bounded provider page")
    nodes = threads.get("nodes")
    if not isinstance(nodes, list):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "review thread nodes are unavailable")
    return {"decision": pr.get("reviewDecision"), "unresolved_threads": sum(1 for item in nodes if isinstance(item, dict) and item.get("isResolved") is False), "approvals": 0}


def branch_policy(gh: GitHub, target: str) -> dict[str, Any]:
    branch = gh.rest("GET", f"/repos/{gh.repo}/branches/{urllib.parse.quote(target, safe='')}")
    rulesets = gh.rest("GET", f"/repos/{gh.repo}/rulesets?includes_parents=true&per_page=100")
    if not isinstance(rulesets, list):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "ruleset list is unavailable")
    merge_queue = False
    active: list[dict[str, Any]] = []
    for item in rulesets:
        if not isinstance(item, dict) or str(item.get("enforcement", "")).lower() != "active":
            continue
        rid = item.get("id")
        if not isinstance(rid, int):
            raise ProviderError("PROVIDER_PARTIAL_TRUTH", "active ruleset lacks ID")
        detail = gh.rest("GET", f"/repos/{gh.repo}/rulesets/{rid}")
        active.append({"id": rid, "name": detail.get("name")})
        merge_queue = merge_queue or any(isinstance(rule, dict) and rule.get("type") == "merge_queue" for rule in (detail.get("rules") or []))
    return {"complete": True, "branch_protected": bool(branch.get("protected")), "active_rulesets": active, "merge_queue_required": merge_queue}


def validation_run(gh: GitHub, number: int, head_sha: str, explicit: int | None) -> dict[str, Any]:
    if explicit:
        candidates = [gh.rest("GET", f"/repos/{gh.repo}/actions/runs/{explicit}")]
        has_more = False
    else:
        payload = gh.rest("GET", f"/repos/{gh.repo}/actions/workflows/promotion-candidate.yml/runs?event=pull_request&per_page=100")
        if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
            raise ProviderError("PROVIDER_PARTIAL_TRUTH", "provider response lacks workflow_runs")
        candidates = [item for item in payload["workflow_runs"] if isinstance(item, dict)]
        has_more = int(payload.get("total_count", len(candidates))) > len(candidates)
    matches = [run for run in candidates if run.get("name") == "Promotion Candidate Validation" and run.get("head_sha") == head_sha and any(isinstance(pr, dict) and pr.get("number") == number for pr in (run.get("pull_requests") or []))]
    if matches:
        return sorted(matches, key=lambda item: str(item.get("created_at", "")), reverse=True)[0]
    if has_more:
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "no exact candidate validation run found on bounded newest page while older provider pages remain")
    raise ProviderError("PROVIDER_PARTIAL_TRUTH", "no exact candidate validation run is attributable to this PR head")


def run_base_sha(run: dict[str, Any], number: int) -> str:
    for pr in run.get("pull_requests") or []:
        if isinstance(pr, dict) and pr.get("number") == number:
            value = str((pr.get("base") or {}).get("sha") or "")
            if SHA.fullmatch(value):
                return value
    raise ProviderError("PROVIDER_PARTIAL_TRUTH", "validation run lacks its tested base SHA")


def snapshot(gh: GitHub, number: int, policy: dict[str, Any], explicit_run: int | None) -> dict[str, Any]:
    repo = gh.rest("GET", f"/repos/{gh.repo}")
    target = str(repo.get("default_branch") or "")
    pr = gh.rest("GET", f"/repos/{gh.repo}/pulls/{number}")
    head, base = pr.get("head") or {}, pr.get("base") or {}
    head_sha, base_sha = str(head.get("sha") or ""), str(base.get("sha") or "")
    if not SHA.fullmatch(head_sha) or not SHA.fullmatch(base_sha) or not target:
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "PR/default-branch exact identity is incomplete")
    run = validation_run(gh, number, head_sha, explicit_run)
    jobs = exact_list(gh.rest("GET", f"/repos/{gh.repo}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100"), "jobs")
    artifacts = exact_list(gh.rest("GET", f"/repos/{gh.repo}/actions/runs/{run['id']}/artifacts?per_page=100"), "artifacts")
    files = gh.rest("GET", f"/repos/{gh.repo}/pulls/{number}/files?per_page=100")
    if not isinstance(files, list) or len(files) >= 100:
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "PR file truth is incomplete or exceeds bounded page")
    return {
        "provider_status": "AVAILABLE", "provider_host": gh.server_url, "target": target, "repository": gh.repo,
        "pr": {"number": number, "state": pr.get("state"), "merged": bool(pr.get("merged")), "draft": bool(pr.get("draft")), "mergeable": pr.get("mergeable"), "head_sha": head_sha, "base_sha": base_sha, "base_ref": str(base.get("ref") or ""), "head_ref": str(head.get("ref") or ""), "head_repository": str((head.get("repo") or {}).get("full_name") or ""), "author_association": str(pr.get("author_association") or ""), "body": str(pr.get("body") or ""), "merge_commit_sha": pr.get("merge_commit_sha")},
        "expected_head_sha": head_sha,
        "validation": {"run_id": int(run["id"]), "head_sha": str(run.get("head_sha") or ""), "base_sha": run_base_sha(run, number), "policy_version": policy["policy_version"], "conclusion": str(run.get("conclusion") or "").lower(), "checks": [{"name": str(job.get("name") or ""), "conclusion": str(job.get("conclusion") or "").lower()} for job in jobs], "artifacts": [{"name": str(a.get("name") or ""), "id": a.get("id"), "expired": bool(a.get("expired"))} for a in artifacts], "changed_paths": [str(item.get("filename") or "").replace("\\", "/") for item in files]},
        "reviews": review_truth(gh, number), "branch_policy": branch_policy(gh, target),
    }


def contained(gh: GitHub, integration_sha: str, target: str) -> bool:
    if not SHA.fullmatch(integration_sha):
        return False
    result = gh.rest("GET", f"/repos/{gh.repo}/compare/{integration_sha}...{urllib.parse.quote(target, safe='')}")
    return str(result.get("status") or "") in {"ahead", "identical"}


def merge_direct(gh: GitHub, number: int, head: str, method: str) -> dict[str, Any]:
    result = gh.rest("PUT", f"/repos/{gh.repo}/pulls/{number}/merge", {"sha": head, "merge_method": method})
    if result.get("merged") is not True or not SHA.fullmatch(str(result.get("sha") or "")):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", f"expected-head merge rejected: {result.get('message')}")
    return {"mode": "direct_merge", "integration_sha": str(result["sha"]), "message": result.get("message")}


def enqueue(gh: GitHub, number: int, head: str) -> dict[str, Any]:
    owner, repo = gh.repo.split("/", 1)
    lookup = gh.graphql("query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){id headRefOid}}}", {"o": owner, "r": repo, "n": number})
    pr = ((lookup.get("repository") or {}).get("pullRequest"))
    if not isinstance(pr, dict) or pr.get("headRefOid") != head or not pr.get("id"):
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "candidate moved before merge-queue admission")
    result = gh.graphql("mutation($id:ID!,$head:GitObjectID!){enqueuePullRequest(input:{pullRequestId:$id,expectedHeadOid:$head}){mergeQueueEntry{id}}}", {"id": pr["id"], "head": head})
    entry = ((result.get("enqueuePullRequest") or {}).get("mergeQueueEntry") or {}).get("id")
    if not entry:
        raise ProviderError("PROVIDER_PARTIAL_TRUTH", "merge queue returned no entry identity")
    return {"mode": "merge_queue", "queue_entry_id": entry}


def base_receipt(contract: dict[str, Any], pr_number: int | None, event_name: str) -> dict[str, Any]:
    return {"schema_version": contract["receipt_schema"]["schema_version"], "status": "UNKNOWN", "provider_status": "UNKNOWN", "provider_adapter": "github-actions-v1", "provider_host": os.environ.get("GITHUB_SERVER_URL"), "repository": os.environ.get("GITHUB_REPOSITORY"), "event_name": event_name, "event_id": os.environ.get("GITHUB_RUN_ID"), "actor": os.environ.get("GITHUB_ACTOR"), "pr_number": pr_number, "candidate_head_sha": None, "candidate_base_sha": None, "target": "main", "policy_version": None, "required_checks": [], "review_decision": None, "unresolved_review_threads": None, "validation_run_id": None, "validation_artifacts": [], "mutation": None, "integration_sha": None, "containment": False, "proof_ceiling": "No provider promotion proof.", "created_at": datetime.now(timezone.utc).isoformat()}


def summary(receipt: dict[str, Any]) -> None:
    print(f"Promotion adapter: status={receipt.get('status')} provider={receipt.get('provider_status')} pr={receipt.get('pr_number')} head={receipt.get('candidate_head_sha')} target={receipt.get('target')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    policy, contract = load(POLICY_PATH), load(CONTRACT_PATH)
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event = load(args.event_path)
    number, explicit_run = event_target(event, event_name)
    receipt = base_receipt(contract, number, event_name)
    try:
        if number is None:
            raise ProviderError("PROVIDER_PARTIAL_TRUTH", "provider event does not identify exactly one promotion candidate")
        gh = GitHub()
        first = snapshot(gh, number, policy, explicit_run)
        receipt.update({"provider_status":"AVAILABLE","provider_host":gh.server_url,"candidate_head_sha":first["pr"]["head_sha"],"candidate_base_sha":first["pr"]["base_sha"],"target":first["target"],"policy_version":policy["policy_version"],"required_checks":first["validation"]["checks"],"review_decision":first["reviews"]["decision"],"unresolved_review_threads":first["reviews"]["unresolved_threads"],"validation_run_id":first["validation"]["run_id"],"validation_artifacts":first["validation"]["artifacts"]})
        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_repository_promotion import evaluate_readiness
        decision = evaluate_readiness(first, policy)
        receipt["decision"] = decision
        if decision["decision"] == "ALREADY_MERGED":
            integration = first["pr"].get("merge_commit_sha")
            if not isinstance(integration, str) or not contained(gh, integration, first["target"]):
                raise ProviderError("PROVIDER_PARTIAL_TRUTH", "already-merged PR lacks verified default-branch containment")
            receipt.update({"status":"ALREADY_MERGED_VERIFIED","mutation":{"mode":"existing_merge"},"integration_sha":integration,"containment":True,"proof_ceiling":"Provider merge and default-branch containment are verified for the already-integrated candidate."})
            write(args.output, receipt); summary(receipt); return 0
        if decision["blocker"]:
            receipt.update({"status":decision["reason"],"proof_ceiling":"Promotion blocked before provider mutation."})
            write(args.output, receipt); summary(receipt); return 2
        second = snapshot(gh, number, policy, first["validation"]["run_id"])
        second_decision = evaluate_readiness(second, policy)
        if second_decision["decision"] != decision["decision"] or second["pr"]["head_sha"] != first["pr"]["head_sha"] or second["pr"]["base_sha"] != first["pr"]["base_sha"]:
            raise ProviderError("PROVIDER_PARTIAL_TRUTH", "provider truth changed between readiness evaluation and final mutation read")
        method = policy["destinations"][first["target"]]["merge_method"]
        mutation = enqueue(gh, number, first["pr"]["head_sha"]) if decision["decision"] == "READY_QUEUE" else merge_direct(gh, number, first["pr"]["head_sha"], method)
        receipt["mutation"] = mutation
        if mutation["mode"] == "merge_queue":
            receipt.update({"status":"QUEUED","proof_ceiling":"Candidate entered provider merge queue; integration is not yet proven."})
            write(args.output, receipt); summary(receipt); return 0
        integration = mutation["integration_sha"]
        ok = contained(gh, integration, first["target"])
        if not ok:
            raise ProviderError("PROVIDER_PARTIAL_TRUTH", "provider merge returned but default-branch containment was not observed")
        receipt.update({"status":"PROMOTED","integration_sha":integration,"containment":True,"proof_ceiling":"Provider-side expected-head merge and refreshed default-branch containment are observed for this exact candidate."})
        write(args.output, receipt); summary(receipt); return 0
    except ProviderError as exc:
        receipt.update({"status":exc.status,"provider_status":exc.status,"error":str(exc),"proof_ceiling":"Provider promotion is not proven because authoritative provider truth or mutation evidence is incomplete."})
        write(args.output, receipt); summary(receipt); return 3


if __name__ == "__main__":
    raise SystemExit(main())
