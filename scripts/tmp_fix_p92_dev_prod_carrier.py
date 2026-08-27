from pathlib import Path

path = Path("scripts/tmp_apply_p92_dev_prod_path_safety.py")
text = path.read_text(encoding="utf-8")
old = "remote merge is never local deployment "
new = "remote merged SHA is never treated as local deployment "
if text.count(old) != 1:
    raise SystemExit(f"expected one P92 proofGate phrase to repair, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
