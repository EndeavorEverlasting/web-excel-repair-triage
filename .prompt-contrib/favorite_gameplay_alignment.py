from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'docs' / 'PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md'
PROTOTYPE = ROOT / 'docs' / 'prompt-kit-hotkey-prototype.js'
TEST = ROOT / 'tests' / 'test_prompt_kit_hotkey_completion.py'
SELF = Path(__file__)

# Re-run after the default-branch bridge points at this semantic-alignment executor.
# Favorite prompt shortcuts perform the terminal COPY action, not detail-open.
design = DESIGN.read_text(encoding='utf-8')
design = design.replace('OPEN_PROMPT', 'COPY_PROMPT')
design = design.replace('PromptNavigator', 'PromptAction')
design = design.replace('`openPrompt(promptId)`', '`copyPrompt(promptId)`')
design = design.replace(
    'It owns translation from PromptTarget to current Prompt Kit card/render behavior. The dispatcher supplies `P95`; the navigator decides how to reveal, focus, scroll, or open it through existing product functions.',
    'It owns translation from PromptTarget to the canonical Prompt Kit terminal action. The dispatcher supplies `P95`; the action owner copies canonical prompt content through the existing copy/success-feedback path without requiring an intermediate detail panel.',
)
design = design.replace(
    "`5` → exact binding resolves → `PromptAction.openPrompt('P95')` → buffer clears → result/trace returns.",
    "`5` → exact binding resolves → `PromptAction.copyPrompt('P95')` → buffer clears → result/trace returns.",
)
design = design.replace(
    '- a completed prompt-ID shortcut opens canonical prompt detail immediately through `showPromptDetail`.',
    '- a completed prompt-ID shortcut copies canonical prompt content immediately through `copyPrompt`, reusing the standard clipboard-success feedback path.',
)
design = design.replace(
    'target validation, and canonical prompt-detail dispatch.',
    'target validation, canonical prompt-copy dispatch, and clipboard-success feedback.',
)
DESIGN.write_text(design, encoding='utf-8')

prototype = PROTOTYPE.read_text(encoding='utf-8')
prototype = prototype.replace('OPEN_PROMPT', 'COPY_PROMPT')
prototype = prototype.replace('PromptNavigatorFake', 'PromptActionFake')
prototype = prototype.replace('promptNavigator', 'promptAction')
prototype = prototype.replace('openPrompt', 'copyPrompt')
prototype = prototype.replace('opened', 'copied')
prototype = prototype.replace('prompt_opened', 'prompt_copied')
PROTOTYPE.write_text(prototype, encoding='utf-8')

test = TEST.read_text(encoding='utf-8').replace('OPEN_PROMPT(P95)', 'COPY_PROMPT(P95)').replace('OPEN_PROMPT(P14)', 'COPY_PROMPT(P14)')
TEST.write_text(test, encoding='utf-8')

subprocess.run(['node', '--check', str(PROTOTYPE)], cwd=ROOT, check=True)
subprocess.run(['node', str(PROTOTYPE)], cwd=ROOT, check=True)
subprocess.run(['python', '-m', 'unittest', 'tests.test_prompt_kit_hotkey_completion', 'tests.test_prompt_kit_favorite_gameplay', '-v'], cwd=ROOT, check=True)
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)

if SELF.exists():
    SELF.unlink()
subprocess.run(['git', 'add', str(DESIGN.relative_to(ROOT)), str(PROTOTYPE.relative_to(ROOT)), str(TEST.relative_to(ROOT)), str(SELF.relative_to(ROOT))], cwd=ROOT, check=True)
subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
subprocess.run(['git', 'commit', '-m', 'docs(prompt-kit): align hotkey prototype with copy action'], cwd=ROOT, check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:feat/prompt-kit-favorite-gameplay-20260822'], cwd=ROOT, check=True)
