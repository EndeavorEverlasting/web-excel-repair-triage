from pathlib import Path

path = Path("scripts/tmp_converge_natural_hotkeys.py")
text = path.read_text(encoding="utf-8")
open_token = 'p126_probe = press_anchor + """'
close_token = '            })\n"""\n    text = replace_once(text, press_anchor, p126_probe, "identity press helper")'
if open_token not in text or close_token not in text:
    raise SystemExit("converger quote anchors missing")
text = text.replace(open_token, "p126_probe = press_anchor + '''", 1)
text = text.replace(
    close_token,
    "            })\n'''\n    text = replace_once(text, press_anchor, p126_probe, \"identity press helper\")",
    1,
)
path.write_text(text, encoding="utf-8")
