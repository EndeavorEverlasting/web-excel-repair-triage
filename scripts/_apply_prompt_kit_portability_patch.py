#!/usr/bin/env python3
"""One-time branch patcher for Prompt Kit portability integration.

This file and its triggering workflow remove themselves before the resulting commit.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one marker in {path}: found {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all(path: Path, old: str, new: str, expected: int) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(
            f"expected {expected} markers in {path}: found {count}: {old!r}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


builder = ROOT / "build_prompt_kit.py"
replace_once(
    builder,
    'JS_PATH = os.path.join(DATA_DIR, "prompt-kit.js")\n',
    'JS_PATH = os.path.join(DATA_DIR, "prompt-kit.js")\n'
    'PORTABILITY_JS_PATH = os.path.join(DATA_DIR, "prompt-kit-favorites-portability.js")\n',
)
replace_once(
    builder,
    '    with open(JS_PATH, "r", encoding="utf-8") as f:\n'
    '        js_text = f.read()\n'
    '    html.append(js_text)\n',
    '    for script_path in (JS_PATH, PORTABILITY_JS_PATH):\n'
    '        with open(script_path, "r", encoding="utf-8") as f:\n'
    '            html.append(f.read())\n',
)

workflow = ROOT / ".github" / "workflows" / "prompt-kit-web.yml"
replace_all(
    workflow,
    '      - docs/prompt-kit.js\n',
    '      - docs/prompt-kit.js\n'
    '      - docs/prompt-kit-favorites-portability.js\n'
    '      - docs/PROMPT_KIT_PORTABILITY.md\n'
    '      - harness/contracts/prompt-kit-portability.v1.json\n'
    '      - scripts/validate_prompt_kit_portability.py\n'
    '      - tests/test_prompt_kit_portability.py\n',
    2,
)
replace_once(
    workflow,
    '            scripts/validate_prompt_kit_discovery.py \\\n',
    '            scripts/validate_prompt_kit_discovery.py \\\n'
    '            scripts/validate_prompt_kit_portability.py \\\n',
)
replace_once(
    workflow,
    '            tests/test_prompt_kit_discovery.py \\\n',
    '            tests/test_prompt_kit_discovery.py \\\n'
    '            tests/test_prompt_kit_portability.py \\\n',
)
replace_once(
    workflow,
    '      - name: Validate Prompt Kit JavaScript syntax\n'
    '        run: node --check docs/prompt-kit.js\n',
    '      - name: Validate Prompt Kit JavaScript syntax\n'
    '        run: |\n'
    '          node --check docs/prompt-kit.js\n'
    '          node --check docs/prompt-kit-favorites-portability.js\n',
)
replace_once(
    workflow,
    '      - name: Validate Prompt Kit product interactions\n',
    '      - name: Validate portable Favorites and harness discipline\n'
    '        run: |\n'
    '          python scripts/validate_prompt_kit_portability.py --summary\n'
    '          python -m unittest tests.test_prompt_kit_portability -v\n'
    '      - name: Validate Prompt Kit product interactions\n',
)

manifest_path = ROOT / "harness" / "manifest.v1.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
components = manifest.setdefault("components", {})
components["prompt_kit_portability_contract"] = (
    "harness/contracts/prompt-kit-portability.v1.json"
)
validation = manifest.setdefault("validation_order", [])
command = "python scripts/validate_prompt_kit_portability.py --summary"
if command not in validation:
    insertion = next(
        (
            index + 1
            for index, value in enumerate(validation)
            if "validate_prompt_kit_discovery.py" in str(value)
        ),
        len(validation),
    )
    validation.insert(insertion, command)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

readme_path = ROOT / "web" / "README.md"
readme = readme_path.read_text(encoding="utf-8")
section = """

## Portable Favorites

The standalone Prompt Kit stores the active browser's Favorites under
`promptKit.favoritePromptIds.v1` and exposes **Export Favorites** and
**Import Favorites** controls beside the Prompt Kit header actions.

The export is a portable JSON document using schema
`prompt-kit-favorites/v1`. Import validates, normalizes, deduplicates, and
merges IDs without deleting current Favorites. Legacy array backups remain
accepted. Unknown prompt IDs stay preserved for later Prompt Kit versions.

The editable runtime is `docs/prompt-kit-favorites-portability.js`; the
canonical builder embeds it into `web/prompt-kit/index.html`. Validate with:

```powershell
python scripts\\validate_prompt_kit_portability.py --summary
python -m unittest tests.test_prompt_kit_portability -v
python scripts\\build_prompt_kit_registry.py --output web\\prompt-kit\\index.html --check
```

See `docs/PROMPT_KIT_PORTABILITY.md` for the complete portability and proof
contract.
"""
if "## Portable Favorites" not in readme:
    readme_path.write_text(readme.rstrip() + section + "\n", encoding="utf-8")

validator = ROOT / "scripts" / "validate_prompt_kit_portability.py"
validator_text = validator.read_text(encoding="utf-8")
validator_text = validator_text.replace('            "never",\n', "")
validator.write_text(validator_text, encoding="utf-8")

subprocess.run(
    [
        "python",
        "scripts/build_prompt_kit_registry.py",
        "--output",
        "web/prompt-kit/index.html",
    ],
    cwd=ROOT,
    check=True,
)

(ROOT / ".github" / "workflows" / "apply-prompt-kit-portability.yml").unlink()
Path(__file__).unlink()

# This no-op marker exists only to trigger the already-registered workflow.
