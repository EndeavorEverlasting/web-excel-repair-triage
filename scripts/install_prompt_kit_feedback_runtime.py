#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BUILDER=ROOT/'scripts/build_prompt_kit_registry.py'
RUNTIME='docs/prompt-kit-feedback-production.js'

def replace_once(text:str, old:str, new:str)->str:
    if new in text: return text
    if old not in text: raise SystemExit(f'installer marker missing: {old[:80]}')
    return text.replace(old,new,1)

def main()->int:
    text=BUILDER.read_text(encoding='utf-8')
    text=replace_once(text,
        'SPEC_ARCHITECTURE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-spec-architecture.js"\n',
        'SPEC_ARCHITECTURE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-spec-architecture.js"\nFEEDBACK_PRODUCTION_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-feedback-production.js"\n')
    text=replace_once(text,
        '    spec_architecture_script = _read_runtime(\n        SPEC_ARCHITECTURE_RUNTIME, "Prompt Kit spec architecture profile behavior"\n    )\n',
        '    spec_architecture_script = _read_runtime(\n        SPEC_ARCHITECTURE_RUNTIME, "Prompt Kit spec architecture profile behavior"\n    )\n    feedback_production_script = _read_runtime(\n        FEEDBACK_PRODUCTION_RUNTIME, "Prompt Kit production feedback behavior"\n    )\n')
    text=replace_once(text,
        '        f"<script>\\n{spec_architecture_script}\\n</script>\\n"\n',
        '        f"<script>\\n{spec_architecture_script}\\n</script>\\n"\n        f"<script>\\n{feedback_production_script}\\n</script>\\n"\n')
    BUILDER.write_text(text,encoding='utf-8')
    print(f'installed {RUNTIME} into canonical builder')
    return 0
if __name__=='__main__': raise SystemExit(main())
