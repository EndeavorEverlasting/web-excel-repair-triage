from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_BUILDER = ROOT / "scripts" / "serve_prompt_kit_portable.py"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
RUNTIME = ROOT / "docs" / "prompt-kit-favorites-portability.js"
EXPECTED_ORIGIN = "http://127.0.0.1:8765/"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptKitPortableResourceCollisionTests(unittest.TestCase):
    def test_output_cannot_collide_with_resource_sidecar(self) -> None:
        portable = load_module("prompt_kit_portable_resource_collision", PORTABLE_BUILDER)
        outputs = ROOT / "Outputs"
        outputs.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=outputs) as temporary:
            temporary_path = Path(temporary)
            output = temporary_path / portable.RESOURCE_INDEX_NAME
            manifest = temporary_path / "manifest.json"
            with self.assertRaisesRegex(
                ValueError,
                "portable artifact path must not be resources.v1.json",
            ):
                portable.build_portable_artifact(
                    repo_root=ROOT,
                    source_path=SITE,
                    runtime_path=RUNTIME,
                    output_path=output,
                    manifest_path=manifest,
                    origin=EXPECTED_ORIGIN,
                )
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())


if __name__ == "__main__":
    unittest.main()
