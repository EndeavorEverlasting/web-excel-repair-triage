from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))
source_path = Path("tmp/versioning_prompt_executor_v3.py")
source = source_path.read_text(encoding="utf-8")
old = '''    "tmp/versioning_prompt_executor_v3.py",
]'''
new = '''    "tmp/versioning_prompt_executor_v3.py",
    "tmp/versioning_prompt_executor_v4.py",
]'''
if old not in source:
    raise SystemExit("temporary executor cleanup extension anchor missing")
patched = source.replace(old, new, 1)
exec(compile(patched, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
