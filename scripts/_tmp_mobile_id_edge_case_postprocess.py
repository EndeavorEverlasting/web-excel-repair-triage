from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_prompt_kit_mobile_quick_controls.py"
text = path.read_text(encoding="utf-8")
old = '            "press **Enter**",\n'
new = '            "Press **Enter**",\n'
if text.count(old) != 1:
    raise SystemExit(f"expected one assertion anchor, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("corrected phone-guide Enter assertion")
