from pathlib import Path
import subprocess

# Synchronize after the default-branch executor switched to this bounded retry.
path = Path('.prompt-contrib/favorite_gameplay_repair.py')
text = path.read_text(encoding='utf-8')
old = '''runtime_section = """
RUNTIME ACCEPTANCE WHEN THE USER ASKED FOR BEHAVIOR
- Treat an observable product request as an implementation obligation, not merely a prompt or contract contribution.
- Follow the real terminal path through the canonical runtime owner: configured favorite shortcut -> canonical prompt copy -> successful clipboard write -> existing success toast -> exactly one semantic usage event -> live dashboard refresh.
- Do not count focus, hover, panel-open, detail-open, or failed copy attempts as usage.
- The preference dashboard must be derived from successful semantic actions and remain local/privacy-bounded unless the operator explicitly authorizes a shared telemetry backend.
- Make accumulating use legible and rewarding through progress/levels, most-used prompts, preference signals, and a favorite loadout; badges are a separate future capability unless requested now.
- Before declaring completion, prove the generated/deployed surface contains the runtime change and add a regression that would fail if the shortcut regresses to detail-open, the toast disappears, usage double-counts, or the dashboard stops reflecting successful copies.
""".strip()'''
new = '''runtime_section = """
RUNTIME ACCEPTANCE WHEN THE USER ASKED FOR BEHAVIOR
- Runtime requests are incomplete as prompt/contract-only work.
- Prove favorite shortcut -> copy -> successful clipboard write -> normal success toast -> exactly one semantic usage event -> live dashboard refresh.
- Count successful actions only; keep telemetry local/private unless sharing is authorized.
- Dashboard shows levels, most-used prompts, preferences, and favorite loadout; badges are a separate future capability.
""".strip()'''
if old not in text:
    raise SystemExit('long P99 runtime section anchor missing')
text = text.replace(old, new, 1)
text = text.replace(
    'SELF = Path(__file__)\n',
    'SELF = Path(__file__)\nRETRY = ROOT / ".prompt-contrib" / "favorite_gameplay_retry.py"\n',
    1,
)
text = text.replace(
    'if TEMP_WORKFLOW.exists():\n    TEMP_WORKFLOW.unlink()\n',
    'subprocess.run(["git", "checkout", "--", ".github/workflows/prompt-kit-web.yml"], cwd=ROOT, check=True)\n',
    1,
)
text = text.replace(
    'if SELF.exists():\n    SELF.unlink()\n',
    'if RETRY.exists():\n    RETRY.unlink()\nif SELF.exists():\n    SELF.unlink()\n',
    1,
)
text = text.replace(
    '    ".github/workflows/prompt-kit-web.yml",\n',
    '',
    1,
)
text = text.replace(
    '    ".github/workflows/tmp-prompt-kit-favorite-gameplay-20260822.yml",\n',
    '',
    1,
)
text = text.replace(
    '    ".prompt-contrib/favorite_gameplay_repair.py",\n',
    '    ".prompt-contrib/favorite_gameplay_repair.py",\n    ".prompt-contrib/favorite_gameplay_retry.py",\n',
    1,
)
path.write_text(text, encoding='utf-8')
subprocess.run(['python', str(path)], check=True)
