from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__)

commands = [
    ['node', '--check', 'docs/prompt-kit-polish.js'],
    ['node', '--check', 'docs/prompt-kit-preference-gameplay.js'],
    ['node', '--check', 'docs/prompt-kit-hotkey-prototype.js'],
    ['node', 'docs/prompt-kit-hotkey-prototype.js'],
    ['python', 'scripts/build_prompt_kit_registry.py', '--output', 'web/prompt-kit/index.html'],
    ['python', '-m', 'unittest', 'tests.test_prompt_kit_hotkey_completion', 'tests.test_prompt_kit_favorite_gameplay', 'tests.test_spec_architecture_prompt_registry', 'tests.test_remote_freshness_p13_iteration', '-v'],
    ['python', 'scripts/prompt_registry_ops.py', 'validate'],
    ['python', 'scripts/validate_prompt_kit_discovery.py', '--summary'],
    ['python', 'scripts/build_prompt_kit_registry.py', '--output', 'web/prompt-kit/index.html', '--check'],
    ['git', 'diff', '--check'],
]
for command in commands:
    subprocess.run(command, cwd=ROOT, check=True)

if SELF.exists():
    SELF.unlink()
subprocess.run(['git', 'add', 'web/prompt-kit/index.html', str(SELF.relative_to(ROOT))], cwd=ROOT, check=True)
subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
subprocess.run(['git', 'status', '--short'], cwd=ROOT, check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], cwd=ROOT, check=True)
subprocess.run(['git', 'commit', '-m', 'build(prompt-kit): refresh favorite gameplay on main floor'], cwd=ROOT, check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:feat/prompt-kit-favorite-gameplay-20260822'], cwd=ROOT, check=True)
