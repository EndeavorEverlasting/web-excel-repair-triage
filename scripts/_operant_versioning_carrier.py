#!/usr/bin/env python3
"""Temporary exact-string carrier for the Operant versioning cutover.

This file is removed before integration. It exists only because the active execution
environment cannot mount the GitHub checkout locally; GitHub Actions supplies the
isolated checkout needed to patch the existing large renderer safely.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(relative: str, old: str, new: str, expected: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(
            f"{relative}: expected {expected} exact occurrence(s), found {count}: {old!r}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    replace_exact(
        "build_prompt_kit.py",
        "import os\nimport sys\n",
        "import os\nimport re\nimport sys\n",
    )
    replace_exact(
        "build_prompt_kit.py",
        'REPO_ROOT = os.path.dirname(os.path.abspath(__file__))\nDATA_DIR = os.path.join(REPO_ROOT, "docs")\n',
        'REPO_ROOT = os.path.dirname(os.path.abspath(__file__))\nOPERANT_VERSION_PATH = os.path.join(REPO_ROOT, "OPERANT_VERSION")\nDATA_DIR = os.path.join(REPO_ROOT, "docs")\n',
    )
    replace_exact(
        "build_prompt_kit.py",
        "\ndef load_json(path):\n",
        "\ndef load_operant_version():\n"
        "    with open(OPERANT_VERSION_PATH, 'r', encoding='utf-8') as f:\n"
        "        value = f.read().strip()\n"
        "    if not re.fullmatch(r'(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)', value):\n"
        "        raise ValueError(f'Invalid Operant version authority: {value!r}')\n"
        "    return value\n\n\n"
        "def load_json(path):\n",
    )
    replace_exact(
        "build_prompt_kit.py",
        "def build_html(prompts, ref):\n    doctrine = build_doctrine()\n    prompt_json = json.dumps(prompts, ensure_ascii=False)\n    ref_json = json.dumps(ref, ensure_ascii=False)\n",
        "def build_html(prompts, ref):\n    doctrine = build_doctrine()\n    prompt_json = json.dumps(prompts, ensure_ascii=False)\n    ref_json = json.dumps(ref, ensure_ascii=False)\n    operant_version = load_operant_version()\n",
    )
    replace_exact(
        "build_prompt_kit.py",
        "    html.append('<title>Operant 0.1</title>')\n",
        "    html.append(f'<title>Operant {operant_version}</title>')\n",
    )
    replace_exact(
        "build_prompt_kit.py",
        "    html.append('      <div><h1>Operant <span>0.1</span></h1>'\n",
        "    html.append(f'      <div><h1>Operant <span>{operant_version}</span></h1>'\n",
    )
    replace_exact(
        "build_prompt_kit.py",
        "    html.append('<div class=\"version-badge\" id=\"versionBadge\">0.1</div>')\n",
        "    html.append(f'<div class=\"version-badge\" id=\"versionBadge\">{operant_version}</div>')\n",
    )

    target = "tests/test_prompt_kit_order_navigation_product.py"
    replace_exact(
        target,
        "    def test_visible_product_identity_is_operant(self) -> None:\n        html = build_prompt_kit_registry.render()\n",
        "    def test_visible_product_identity_is_operant(self) -> None:\n        html = build_prompt_kit_registry.render()\n        version = build_prompt_kit_registry.build_prompt_kit.load_operant_version()\n",
    )
    replace_exact(
        target,
        "        self.assertIn('<title>Operant 0.1</title>', html)\n",
        "        self.assertIn(f'<title>Operant {version}</title>', html)\n",
    )
    replace_exact(
        target,
        "        self.assertIn('Operant <span>0.1</span>', html)\n",
        "        self.assertIn(f'Operant <span>{version}</span>', html)\n",
    )
    replace_exact(
        target,
        "        self.assertIn('id=\\\"versionBadge\\\">0.1</div>', html)\n",
        "        self.assertIn(f'id=\\\"versionBadge\\\">{version}</div>', html)\n",
    )

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
