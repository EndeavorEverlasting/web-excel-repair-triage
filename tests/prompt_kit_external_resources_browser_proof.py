#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "web" / "prompt-kit" / "index.html"
RESOURCE_INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def observe(port: int, screenshot: Path) -> list[dict]:
    expected = json.loads(RESOURCE_INDEX.read_text(encoding="utf-8"))
    expected_count = int(expected["summary"]["resource_count"])
    expected_page = min(40, expected_count)
    source_shas = {row["id"]: row["resolved_sha"] for row in expected["source_floor"]}
    portable_root = ROOT / "Outputs" / "observed-proof" / "external-resource-portable"
    portable_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "serve_prompt_kit_portable.py"),
            "--build-only",
            "--output",
            str(portable_root / "index.html"),
            "--manifest",
            str(portable_root / "manifest.json"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    resource_requests: list[str] = []
    original_cwd = Path.cwd()
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on(
                "request",
                lambda request: resource_requests.append(request.url)
                if request.url.endswith("/resources.v1.json")
                else None,
            )
            page.goto(
                f"http://127.0.0.1:{port}/web/prompt-kit/index.html",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(150)
            initial_requests = len(resource_requests)
            button_present = page.locator("#externalResourcesButton").count() == 1
            panel_hidden = page.locator("#operantExternalResources").evaluate("el => el.hidden")
            initial_rows = page.locator(".operant-resource-row").count()

            page.locator("#externalResourcesButton").click()
            page.wait_for_function(
                """expected => {
                  const count=document.querySelector('.operant-resource-count');
                  return !!(count && count.textContent.includes(expected+' indexed'));
                }""",
                arg=expected_count,
                timeout=5000,
            )
            loaded_requests = len(resource_requests)
            rendered_rows = page.locator(".operant-resource-row").count()
            loaded_panel_visible = not page.locator("#operantExternalResources").evaluate("el => el.hidden")

            search = page.locator(".operant-resource-search")
            search.fill("code review")
            page.wait_for_timeout(100)
            search_rows = page.locator(".operant-resource-row").count()
            source_link = page.locator(".operant-resource-row a", has_text="Open source").first
            source_href = source_link.get_attribute("href") if search_rows else ""
            pinned_href = bool(source_href and any(f"/blob/{sha}/" in source_href for sha in source_shas.values()))

            search.fill("")
            page.evaluate("""() => {
              const base=window.externalResourceIndex.resources.slice();
              const expanded=[];
              for(let i=0;i<85;i++){const source=base[i%base.length];expanded.push(Object.assign({},source,{id:source.id+'-proof-'+i,title:source.title+' proof '+i}))}
              window.externalResourceIndex=Object.assign({},window.externalResourceIndex,{summary:Object.assign({},window.externalResourceIndex.summary,{resource_count:85}),resources:expanded});
              window.externalResourcePage=0;
              window.OperantExternalResources.render();
            }""")
            first_page_rows = page.locator(".operant-resource-row").count()
            page.locator(".operant-resource-next").click()
            second_page_rows = page.locator(".operant-resource-row").count()
            page.locator(".operant-resource-next").click()
            third_page_rows = page.locator(".operant-resource-row").count()
            page.locator(".operant-resource-prev").click()
            previous_page_rows = page.locator(".operant-resource-row").count()

            page.keyboard.press("Escape")
            closed_by_escape = page.locator("#operantExternalResources").evaluate("el => el.hidden")

            portable_request_floor = len(resource_requests)
            page.goto(f"http://127.0.0.1:{port}/Outputs/observed-proof/external-resource-portable/index.html",wait_until="domcontentloaded")
            page.wait_for_timeout(100)
            portable_initial_requests = len(resource_requests)-portable_request_floor
            page.locator("#externalResourcesButton").click()
            page.wait_for_function(
                """expected => {const count=document.querySelector('.operant-resource-count');return !!(count && count.textContent.includes(expected+' indexed'));}""",
                arg=expected_count,
                timeout=5000,
            )
            portable_loaded_requests = len(resource_requests)-portable_request_floor
            portable_rows = page.locator(".operant-resource-row").count()

            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=False)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        os.chdir(original_cwd)

    return [
        {
            "id": "default_load_is_catalog_free",
            "event": "initial Operant page load performs no external resource index request",
            "occurred": True,
            "passed": initial_requests == 0 and button_present and panel_hidden and initial_rows == 0,
            "resource_requests": initial_requests,
            "button_present": button_present,
            "panel_hidden": panel_hidden,
            "rows": initial_rows,
        },
        {
            "id": "explicit_open_fetches_once",
            "event": "opening Resources performs one metadata-sidecar fetch and reveals the panel",
            "occurred": True,
            "passed": loaded_requests == 1 and loaded_panel_visible,
            "resource_requests": loaded_requests,
            "panel_visible": loaded_panel_visible,
        },
        {
            "id": "render_is_bounded",
            "event": "resource rendering is capped to the configured first page",
            "occurred": True,
            "passed": rendered_rows == expected_page and rendered_rows <= 40,
            "rendered_rows": rendered_rows,
            "expected_page_rows": expected_page,
            "catalog_count": expected_count,
        },
        {
            "id": "search_preserves_pinned_source_navigation",
            "event": "resource search returns bounded results whose upstream link remains commit-pinned",
            "occurred": True,
            "passed": search_rows > 0 and search_rows <= 40 and pinned_href,
            "search_rows": search_rows,
            "source_href": source_href,
            "pinned": pinned_href,
        },
        {
            "id": "pagination_remains_bounded",
            "event": "next/previous pagination never renders more than one configured resource page",
            "occurred": True,
            "passed": first_page_rows == 40 and second_page_rows == 40 and third_page_rows == 5 and previous_page_rows == 40,
            "first_page_rows": first_page_rows,
            "second_page_rows": second_page_rows,
            "third_page_rows": third_page_rows,
            "previous_page_rows": previous_page_rows,
            "synthetic_catalog_count": 85,
        },
        {
            "id": "portable_package_serves_sidecar",
            "event": "portable packaging includes the canonical resource sidecar and keeps lazy loading",
            "occurred": True,
            "passed": portable_initial_requests == 0 and portable_loaded_requests == 1 and portable_rows == expected_page,
            "initial_resource_requests": portable_initial_requests,
            "loaded_resource_requests": portable_loaded_requests,
            "rendered_rows": portable_rows,
        },
        {
            "id": "escape_closes_resources",
            "event": "Escape closes the progressive-disclosure resource panel",
            "occurred": True,
            "passed": bool(closed_by_escape),
        },
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--screenshot", required=True)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args(argv)
    observations = observe(args.port, Path(args.screenshot))
    by_id = {item["id"]: item for item in observations}
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    claims = [
        {
            "id": "lazy_catalog_loading",
            "statement": "Operant does not fetch the external resource catalog until Resources is explicitly opened",
            "status": "PASS" if by_id["default_load_is_catalog_free"]["passed"] and by_id["explicit_open_fetches_once"]["passed"] else "FAIL",
            "required_evidence_class": "browser_runtime_observed",
            "observation_ids": ["default_load_is_catalog_free", "explicit_open_fetches_once"],
        },
        {
            "id": "bounded_resource_rendering",
            "statement": "Operant renders at most one bounded resource page at a time",
            "status": "PASS" if by_id["render_is_bounded"]["passed"] and by_id["pagination_remains_bounded"]["passed"] else "FAIL",
            "required_evidence_class": "browser_runtime_observed",
            "observation_ids": ["render_is_bounded", "pagination_remains_bounded"],
        },
        {
            "id": "resource_navigation",
            "statement": "Resource search exposes commit-pinned upstream navigation without embedding donor bodies",
            "status": "PASS" if by_id["search_preserves_pinned_source_navigation"]["passed"] and by_id["portable_package_serves_sidecar"]["passed"] and by_id["escape_closes_resources"]["passed"] else "FAIL",
            "required_evidence_class": "browser_runtime_observed",
            "observation_ids": ["search_preserves_pinned_source_navigation", "portable_package_serves_sidecar", "escape_closes_resources"],
        },
    ]
    verdict = "PASS" if all(item["passed"] for item in observations) else "FAIL"
    receipt = {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": verdict,
        "evidence_class": "browser_runtime_observed",
        "subject": {
            "commit_sha": sha,
            "artifact": {
                "path": "web/prompt-kit/index.html",
                "sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
            },
        },
        "environment": {
            "kind": "github_actions_headless_browser" if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" else "local_headless_browser",
            "engine": "chromium",
            "scenario": "operant-lazy-external-resource-catalog",
        },
        "claims": claims,
        "observations": observations,
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "receipt": str(receipt_path), "observations": observations}))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
