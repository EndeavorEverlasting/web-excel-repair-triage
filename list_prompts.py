import json
from pathlib import Path

ROOT = Path('.').resolve()
registries = [
    ROOT / 'docs' / 'prompts.json',
    ROOT / 'registry' / 'prompts' / 'skill-development-prompts.v1.json',
    ROOT / 'registry' / 'prompts' / 'tutorial-discovery-prompts.v1.json',
    ROOT / 'registry' / 'prompts' / 'ai-engineering-level-up-prompts.v1.json',
    ROOT / 'registry' / 'prompts' / 'repository-work-ledger-prompts.v1.json',
    ROOT / 'registry' / 'prompts' / 'management-operations-prompts.v1.json',
    ROOT / 'registry' / 'prompts' / 'spec-architecture-prompts.v1.json',
    ROOT / 'registry' / 'prompts' / 'correspondence-prompts.v1.json',
]

all_prompts = []
for r in registries:
    if r.exists():
        data = json.loads(r.read_text())
        if isinstance(data, list):
            all_prompts.extend(data)
        elif isinstance(data, dict) and 'prompts' in data:
            all_prompts.extend(data['prompts'])

print(f'Total prompts: {len(all_prompts)}')
for p in sorted(all_prompts, key=lambda x: int(x.get('seq', '999'))):
    t = p.get('type', 'N/A')
    c = p.get('class', 'N/A')
    n = p['name'][:60]
    print(f"{p['id']}: {n} | type={t} | class={c}")
