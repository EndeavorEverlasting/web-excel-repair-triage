from pathlib import Path

path = Path("scripts/tmp_converge_natural_hotkeys.py")
text = path.read_text(encoding="utf-8")

extra_anchor = '    if anchor not in text:\n        raise SystemExit("hotkey completion grammar insertion anchor missing")\n'
extra_replacement = '    extra = textwrap.indent(extra, "    ")\n' + extra_anchor
if extra_anchor not in text:
    raise SystemExit("grammar indentation anchor missing")
text = text.replace(extra_anchor, extra_replacement, 1)

negative_anchor = '    if human_anchor not in text:\n        raise SystemExit("hotkey completion design guard anchor missing")\n'
negative_replacement = '    negative = textwrap.indent(negative, "        ")\n' + negative_anchor
if negative_anchor not in text:
    raise SystemExit("design-guard indentation anchor missing")
text = text.replace(negative_anchor, negative_replacement, 1)

path.write_text(text, encoding="utf-8")
