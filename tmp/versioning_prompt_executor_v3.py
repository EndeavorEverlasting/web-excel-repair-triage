from pathlib import Path

source_path = Path("tmp/versioning_prompt_executor.py")
source = source_path.read_text(encoding="utf-8")

old_temp = '''TEMP_FILES = [
    ".github/workflows/tmp-versioning-owner-discovery.yml",
    "tmp/versioning_prompt_executor.py",
]
'''
new_temp = '''TEMP_FILES = [
    ".github/workflows/tmp-versioning-owner-discovery.yml",
    "tmp/versioning_prompt_executor.py",
    "tmp/versioning_prompt_executor_v2.py",
    "tmp/versioning_prompt_executor_v3.py",
]
'''

old_floor = '''carrier_head = git_output("rev-parse", "origin/main")
semantic_base = git_output("rev-parse", f"{carrier_head}^")
carrier_blob = git_output("rev-parse", f"{semantic_base}:{CARRIER}")
changed = [line for line in git_output("diff", "--name-only", semantic_base, carrier_head).splitlines() if line]
print(json.dumps({"carrier_head": carrier_head, "semantic_base": semantic_base, "carrier_blob": carrier_blob, "carrier_changed_files": changed}, indent=2))
if carrier_blob != CANONICAL_CARRIER_BLOB:
    raise SystemExit(f"semantic base does not contain canonical carrier: {carrier_blob}")
if changed != [CARRIER]:
    raise SystemExit(f"temporary carrier head contains unexpected files: {changed}")
'''
new_floor = '''carrier_head = git_output("rev-parse", "origin/main")
semantic_base = carrier_head
transport_hops = []
for _ in range(8):
    carrier_blob = git_output("rev-parse", f"{semantic_base}:{CARRIER}")
    if carrier_blob == CANONICAL_CARRIER_BLOB:
        break
    parent = git_output("rev-parse", f"{semantic_base}^")
    changed = [line for line in git_output("diff", "--name-only", parent, semantic_base).splitlines() if line]
    if changed != [CARRIER]:
        raise SystemExit(f"temporary carrier chain contains unexpected files at {semantic_base}: {changed}")
    transport_hops.append({"commit": semantic_base, "carrier_blob": carrier_blob})
    semantic_base = parent
else:
    raise SystemExit("canonical carrier not found within bounded temporary transport chain")
print(json.dumps({"carrier_head": carrier_head, "semantic_base": semantic_base, "canonical_carrier_blob": carrier_blob, "transport_hops": transport_hops}, indent=2))
'''

if old_temp not in source or old_floor not in source:
    raise SystemExit("temporary executor patch anchor missing")
patched = source.replace(old_temp, new_temp, 1).replace(old_floor, new_floor, 1)
exec(compile(patched, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
