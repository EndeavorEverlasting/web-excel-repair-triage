from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))
import validate_prompt_kit_ui_format_alignment as alignment  # noqa: E402


class PromptKitUiFormatAlignmentTests(unittest.TestCase):
    def test_current_repository_passes_alignment_gate(self) -> None:
        result = alignment.validate(require_implementation=True)
        self.assertTrue(result["ok"], result["errors"])
        self.assertGreaterEqual(result["aligned_count"], 5)
        self.assertEqual(result["deferred_count"], 0)

    def test_forbidden_btn_without_deferred_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            contract = json.loads((ROOT / "harness/contracts/prompt-kit-ui-format-alignment.v1.json").read_text(encoding="utf-8"))
            ledger = {
                "schema_version": "prompt-kit-ui-format-alignment-ledger/v1",
                "contract_id": "prompt-kit-ui-format-alignment",
                "aligned": [
                    {
                        "id": "header-storage-utility",
                        "control_id": "promptStorageLifecycleBtn",
                        "source": "docs/prompt-kit-storage-lifecycle.js",
                        "classes": ["operant-resource-button"],
                        "status": "aligned",
                    },
                    {
                        "id": "header-resources-utility",
                        "control_id": "externalResourcesButton",
                        "source": "docs/prompt-kit-external-resources.js",
                        "classes": ["operant-resource-button"],
                        "status": "aligned",
                    },
                    {
                        "id": "storage-modal-surface",
                        "control_id": "promptStorageLifecycleDialog",
                        "source": "docs/prompt-kit-storage-lifecycle.js",
                        "classes": ["prompt-storage-backdrop"],
                        "status": "aligned",
                    },
                ],
                "deferred": [],
            }
            scan = tmp_path / "bad.js"
            scan.write_text(
                "var button=doc.createElement('button');\n"
                "button.id='promptStorageLifecycleBtn';\n"
                "button.className='btn';\n",
                encoding="utf-8",
            )
            contract["scan_paths"] = [scan.name]
            contract_path = tmp_path / "contract.json"
            ledger_path = tmp_path / "ledger.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            with mock.patch.object(alignment, "CONTRACT", contract_path), mock.patch.object(
                alignment, "LEDGER", ledger_path
            ), mock.patch.object(alignment, "ROOT", tmp_path):
                result = alignment.validate(require_implementation=True)
            self.assertFalse(result["ok"])
            self.assertTrue(any("forbidden class" in err or "formatting sequence" in err for err in result["errors"]))

    def test_deferred_marker_coerces_lazy_control_into_ledger_fodder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            contract = json.loads((ROOT / "harness/contracts/prompt-kit-ui-format-alignment.v1.json").read_text(encoding="utf-8"))
            ledger = {
                "schema_version": "prompt-kit-ui-format-alignment-ledger/v1",
                "contract_id": "prompt-kit-ui-format-alignment",
                "aligned": [
                    {
                        "id": "header-storage-utility",
                        "control_id": "promptStorageLifecycleBtn",
                        "source": "docs/x.js",
                        "classes": ["operant-resource-button"],
                        "status": "aligned",
                    },
                    {
                        "id": "header-resources-utility",
                        "control_id": "externalResourcesButton",
                        "source": "docs/y.js",
                        "classes": ["operant-resource-button"],
                        "status": "aligned",
                    },
                    {
                        "id": "storage-modal-surface",
                        "control_id": "promptStorageLifecycleDialog",
                        "source": "docs/x.js",
                        "classes": ["prompt-storage-backdrop"],
                        "status": "aligned",
                    },
                ],
                "deferred": [
                    {
                        "id": "TRQ-UI-LAZY-1",
                        "source": "lazy.js",
                        "reason": "Prototype control landed without catalog classes",
                        "owner": "ui-format-alignment-tests",
                        "next_action": "Replace className='btn' with operant-resource-button",
                        "status": "deferred",
                    }
                ],
            }
            scan = tmp_path / "lazy.js"
            scan.write_text(
                "var button=doc.createElement('button');\n"
                "button.className='btn';\n"
                "button.setAttribute('data-ui-format-deferred','TRQ-UI-LAZY-1');\n",
                encoding="utf-8",
            )
            # Keep required header ids out of this scan file so only deferred path is exercised.
            contract["scan_paths"] = [scan.name]
            contract["header_utility_control_ids"] = []
            contract_path = tmp_path / "contract.json"
            ledger_path = tmp_path / "ledger.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            # Stub storage source required by require_implementation check.
            docs = tmp_path / "docs"
            docs.mkdir()
            (docs / "prompt-kit-storage-lifecycle.js").write_text(
                "button.className='operant-resource-button'\n", encoding="utf-8"
            )
            with mock.patch.object(alignment, "CONTRACT", contract_path), mock.patch.object(
                alignment, "LEDGER", ledger_path
            ), mock.patch.object(alignment, "ROOT", tmp_path):
                result = alignment.validate(require_implementation=True)
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["deferred_count"], 1)
            self.assertTrue(any("deferred as TRQ-UI-LAZY-1" in warn for warn in result["warnings"]))

    def test_storage_runtime_uses_header_utility_class(self) -> None:
        source = (ROOT / "docs/prompt-kit-storage-lifecycle.js").read_text(encoding="utf-8")
        self.assertIn("button.className='operant-resource-button'", source)
        self.assertNotIn("button.className='btn'", source)
        self.assertIn("prompt-storage-backdrop", source)


if __name__ == "__main__":
    unittest.main()
