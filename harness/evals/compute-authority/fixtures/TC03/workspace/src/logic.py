import json
from pathlib import Path

def load_config():
    return json.loads(Path("config.json").read_text(encoding="utf-8"))

def compute(value: int) -> int:
    cfg = load_config()
    return value * int(cfg["multiplier"])
