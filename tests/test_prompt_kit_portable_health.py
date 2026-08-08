from __future__ import annotations

import hashlib
import importlib.util
import json
import threading
import unittest
import urllib.request
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "scripts" / "serve_prompt_kit_portable.py"
LAUNCHER_PATH = ROOT / "scripts" / "Open-LatestPromptKitPortable.ps1"
POLICY_PATH = ROOT / "harness" / "contracts" / "prompt-kit-portability.v1.json"


def load_server_module():
    spec = importlib.util.spec_from_file_location("prompt_kit_portable_server", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SERVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptKitPortableHealthTests(unittest.TestCase):
    def test_health_reports_exact_current_artifact_hash(self) -> None:
        portable = load_server_module()
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "index.html"
            artifact.write_text("version-one", encoding="utf-8")
            handler = partial(portable.PortablePromptKitHandler, directory=str(root))
            server = portable.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/healthz", timeout=3
                ) as response:
                    health_one = json.load(response)
                self.assertEqual(health_one["status"], "ok")
                self.assertEqual(
                    health_one["artifact_sha256"],
                    hashlib.sha256(b"version-one").hexdigest(),
                )
                self.assertEqual(health_one["artifact_bytes"], len(b"version-one"))

                artifact.write_text("version-two", encoding="utf-8")
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/healthz", timeout=3
                ) as response:
                    health_two = json.load(response)
                self.assertEqual(
                    health_two["artifact_sha256"],
                    hashlib.sha256(b"version-two").hexdigest(),
                )
                self.assertNotEqual(
                    health_one["artifact_sha256"], health_two["artifact_sha256"]
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_launcher_requires_expected_artifact_hash(self) -> None:
        launcher = LAUNCHER_PATH.read_text(encoding="utf-8")
        for marker in (
            "ExpectedArtifactSha256",
            "artifact_sha256",
            "Stable Prompt Kit origin is already occupied by a different artifact",
            "PROMPT_KIT_PORTABLE_SHA256=",
        ):
            self.assertIn(marker, launcher)

    def test_policy_requires_health_hash_guardrail(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        artifact = policy["artifact_rules"]["portable_runtime_artifact"]
        self.assertEqual(artifact["path"], "Outputs/prompt-kit-portable/index.html")
        self.assertIn(
            "never_modify_canonical_site_during_runtime_generation",
            policy["favorites_portability"]["security"],
        )


if __name__ == "__main__":
    unittest.main()
