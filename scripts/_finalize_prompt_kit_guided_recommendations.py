#!/usr/bin/env python3
"""One-time branch finalizer for the Prompt Kit tutorial/polish sprint.

The branch-only workflow runs this file after durable sources are committed. It
adds the repository quick-access front door, validates supplemental JavaScript,
regenerates the canonical website, then removes this helper and its temporary
write-enabled workflow before the generated-artifact commit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ACCESS = ROOT / "PROMPT_KIT_ACCESS.md"
TEMP_WORKFLOW = ROOT / ".github" / "workflows" / "apply-prompt-kit-portability.yml"

README_START = "<!-- PROMPT_KIT_QUICK_ACCESS_START -->"
README_END = "<!-- PROMPT_KIT_QUICK_ACCESS_END -->"
ACCESS_START = "<!-- PROMPT_KIT_FAST_PATH_START -->"
ACCESS_END = "<!-- PROMPT_KIT_FAST_PATH_END -->"

README_BLOCK = f"""{README_START}
## 🤖 AI Harness Prompt Kit — open it like an app

The Prompt Kit is a separate, self-contained operator surface in this repository. You do **not** need to install the workbook-repair application just to use the prompts.

| What you want | Fastest path |
|---|---|
| **Use the Prompt Kit now** on any browser | **[Open the Prompt Kit](https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/)** |
| **Phone / tablet / install / QR** | **[Open the device launcher](https://endeavoreverlasting.github.io/web-excel-repair-triage/)** |
| **Windows one-click local copy** | **[Download `Open-Latest-PromptKit.cmd`](https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/Open-Latest-PromptKit.cmd)**, save it, and double-click it. It safely resolves or clones canonical `main`, fast-forwards only, validates the generated site, and opens it. |
| **Download without Git** | **[Download the latest `main` ZIP](https://github.com/EndeavorEverlasting/web-excel-repair-triage/archive/refs/heads/main.zip)**, extract it, then open `web/prompt-kit/index.html`. |
| **Clone once** | `git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git` |

Inside the Prompt Kit, use the glowing **Tutorial · Find My Prompt** button when you are unsure which prompt to choose. Full acquisition details: [`PROMPT_KIT_ACCESS.md`](PROMPT_KIT_ACCESS.md). Phone-specific help: [`OPEN_PROMPT_KIT_ON_PHONE.md`](OPEN_PROMPT_KIT_ON_PHONE.md).
{README_END}
"""

ACCESS_BLOCK = f"""{ACCESS_START}
## Choose the easiest path

| Device / need | Do this |
|---|---|
| Browser on any computer | Open **https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/** |
| Phone / tablet / install / QR | Open **https://endeavoreverlasting.github.io/web-excel-repair-triage/** |
| Windows local/offline copy | Download **https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/Open-Latest-PromptKit.cmd** and double-click it |
| No Git client | Download **https://github.com/EndeavorEverlasting/web-excel-repair-triage/archive/refs/heads/main.zip** and open `web/prompt-kit/index.html` after extraction |
| Git user | `git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git` |

Normal users should prefer the public browser URL. The CMD path exists for a validated local Windows copy; the ZIP and clone paths are fallbacks, not prerequisites for using the web app.
{ACCESS_END}
"""


def replace_or_insert(text: str, start: str, end: str, block: str, insertion: int) -> str:
    if start in text and end in text:
        before, remainder = text.split(start, 1)
        _, after = remainder.split(end, 1)
        return before.rstrip() + "\n\n" + block.strip() + "\n" + after.lstrip("\n")
    return text[:insertion].rstrip() + "\n\n" + block.strip() + "\n\n" + text[insertion:].lstrip()


def patch_readme() -> None:
    text = README.read_text(encoding="utf-8")
    divider = text.find("\n---\n")
    insertion = divider + len("\n---\n") if divider >= 0 else text.find("\n") + 1
    README.write_text(
        replace_or_insert(text, README_START, README_END, README_BLOCK, insertion),
        encoding="utf-8",
    )


def patch_access_guide() -> None:
    text = ACCESS.read_text(encoding="utf-8")
    first_line = text.find("\n") + 1
    ACCESS.write_text(
        replace_or_insert(text, ACCESS_START, ACCESS_END, ACCESS_BLOCK, first_line),
        encoding="utf-8",
    )


patch_readme()
patch_access_guide()

for script in (
    "docs/prompt-kit-guided-recommendations.js",
    "docs/prompt-kit-polish.js",
):
    subprocess.run(["node", "--check", script], cwd=ROOT, check=True)

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

TEMP_WORKFLOW.unlink()
Path(__file__).unlink()
