# Prompt Compilation

Bounded Prompt Kit subsystem for compiling semantic prompt policy into effective instructions without owning lifecycle events.

- Architecture: [`PROMPT_COMPILATION_ARCHITECTURE.md`](./PROMPT_COMPILATION_ARCHITECTURE.md)
- Sprint map: [`PROMPT_COMPILATION_SPRINT_MAP.md`](./PROMPT_COMPILATION_SPRINT_MAP.md)
- Language Engine: `scripts/prompt_language_compiler.py`
- Context Engine adapters: `scripts/prompt_context_engine.py`
- Improvement Compiler: `scripts/prompt_improvement_compiler.py`
- Compute Mode runtime: `docs/prompt-kit-compute-mode.js`
- Builder wiring: `scripts/build_prompt_kit_registry.py` attaches `compiledEffectivePrompts`
- Focused tests: `tests/test_prompt_compilation.py`, `tests/test_prompt_context_engine.py`, `tests/test_prompt_improvement_compiler.py`, `tests/test_prompt_kit_compute_mode.py`

```bash
python -m unittest tests.test_prompt_compilation tests.test_prompt_context_engine tests.test_prompt_improvement_compiler tests.test_prompt_kit_compute_mode -v
python scripts/prompt_language_compiler.py validate-fixtures --summary
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```
