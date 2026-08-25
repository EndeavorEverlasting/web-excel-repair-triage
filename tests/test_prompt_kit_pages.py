from pathlib import Path
import json
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"
ACCESS_GUIDE = ROOT / "PROMPT_KIT_ACCESS.md"
PHONE_GUIDE = ROOT / "OPEN_PROMPT_KIT_ON_PHONE.md"
MOBILE_ROOT = ROOT / "web" / "prompt-kit-mobile"
PUBLIC_LAUNCHER_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/"
PUBLIC_PROMPT_URL = PUBLIC_LAUNCHER_URL + "prompt-kit/"

def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"not a PNG file: {path}")
    return struct.unpack(">II", data[16:24])

class PromptKitPagesContractTests(unittest.TestCase):
    def test_pages_workflow_is_exact_candidate_validation_then_promotion(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        required = (
            "name: Prompt Kit GitHub Pages",
            "branches: [main]",
            "workflow_dispatch:",
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            "persist-credentials: false",
            "git merge-base --is-ancestor origin/main HEAD",
            "name: Harness E2E gate",
            "python scripts/validate_harness.py --report Outputs/harness-completeness-report.json",
            "name: Explicit feedback contract gate",
            "name: Application browser E2E gate",
            "bash scripts/run_prompt_kit_browser_e2e.sh",
            "name: Release identity gate",
            "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check",
            'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"',
            'cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html',
            "write_prompt_kit_promotion_receipt.py",
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main'",
            "name: Prove deployed canonical bytes",
            "cmp deployed-prompt-kit.html web/prompt-kit/index.html",
        )
        for marker in required:
            with self.subTest(marker=marker): self.assertIn(marker, text)
        self.assertNotIn("continue-on-error", text)
        self.assertNotIn("contents: write", text)
    def test_pages_workflow_uses_least_privilege_deploy_permissions(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for marker in ("contents: read","pages: write","id-token: write","name: github-pages","actions/configure-pages@v5","actions/upload-pages-artifact@v4","actions/deploy-pages@v4"):
            with self.subTest(marker=marker): self.assertIn(marker,text)
        self.assertIn("needs: [validate, package]",text)
    def test_existing_access_guide_retains_public_prompt_surface(self):
        text=ACCESS_GUIDE.read_text(encoding="utf-8"); self.assertIn(PUBLIC_PROMPT_URL,text); self.assertIn("## Phone, tablet, or any browser",text); self.assertIn("Add to Home Screen",text); self.assertIn("GitHub Actions",text)
    def test_android_quick_open_guide_requires_no_download(self):
        text=PHONE_GUIDE.read_text(encoding="utf-8"); self.assertIn(PUBLIC_LAUNCHER_URL,text); self.assertIn(PUBLIC_PROMPT_URL,text); self.assertIn("no download required",text.lower()); self.assertIn("Open in browser",text); self.assertIn("Install on this Android phone",text); self.assertIn("same Prompt Kit used on desktop",text); self.assertIn("Canonical generated/deployed website artifact",text); self.assertIn("Implementation source: `docs/prompt-kit.js`",text)
    def test_mobile_launcher_exposes_open_install_share_and_copy(self):
        html=(MOBILE_ROOT/"index.html").read_text(encoding="utf-8")
        for marker in ('href="./manifest.webmanifest"','id="openPromptKit"','href="./prompt-kit/"','id="installButton"','id="shareButton"','id="copyButton"',"beforeinstallprompt","navigator.share","navigator.clipboard.writeText",'navigator.serviceWorker.register("./service-worker.js")',"Open in browser"):
            with self.subTest(marker=marker): self.assertIn(marker,html)
    def test_manifest_launches_canonical_prompt_kit_as_standalone_app(self):
        payload=json.loads((MOBILE_ROOT/"manifest.webmanifest").read_text(encoding="utf-8")); self.assertEqual(payload["id"],"./prompt-kit/"); self.assertEqual(payload["start_url"],"./prompt-kit/"); self.assertEqual(payload["scope"],"./"); self.assertEqual(payload["display"],"standalone"); self.assertEqual({icon["sizes"] for icon in payload["icons"]},{"192x192","512x512"}); self.assertTrue(all("maskable" in icon["purpose"] for icon in payload["icons"]))
    def test_service_worker_is_same_origin_network_first_with_offline_fallback(self):
        text=(MOBILE_ROOT/"service-worker.js").read_text(encoding="utf-8")
        for marker in ('"./prompt-kit/"','requestUrl.origin !== self.location.origin',"fetch(event.request)","cache.put(event.request, copy)",'caches.match("./prompt-kit/")',"self.skipWaiting()","self.clients.claim()"):
            with self.subTest(marker=marker): self.assertIn(marker,text)
        self.assertNotIn('fetch("http',text); self.assertNotIn("importScripts(",text)
    def test_service_worker_only_cleans_prompt_kit_caches_and_waits_for_runtime_writes(self):
        text=(MOBILE_ROOT/"service-worker.js").read_text(encoding="utf-8"); self.assertIn('const CACHE_PREFIX = "ai-prompt-kit-mobile-";',text); self.assertIn("key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME",text); self.assertNotIn("keys.filter(key => key !== CACHE_NAME)",text); self.assertIn("event.waitUntil(\n            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy))",text)
    def test_mobile_icons_and_qr_are_tracked_sized_pngs(self):
        self.assertEqual(png_size(MOBILE_ROOT/"icon-192.png"),(192,192)); self.assertEqual(png_size(MOBILE_ROOT/"icon-512.png"),(512,512)); w,h=png_size(MOBILE_ROOT/"qr-prompt-kit.png"); self.assertEqual(w,h); self.assertGreaterEqual(w,256)

if __name__ == "__main__": unittest.main()
