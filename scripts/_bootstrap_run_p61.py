#!/usr/bin/env python3
from pathlib import Path
import runpy

script = Path(__file__).with_name("_bootstrap_add_p63.py")
text = script.read_text(encoding="utf-8")
text = text.replace("P63", "P61").replace("p63", "p61")
text = text.replace('Expected P62 as registry tail', 'Expected P60 as registry tail')
text = text.replace('ids[-1] != "P62"', 'ids[-1] != "P60"')
script.write_text(text, encoding="utf-8")
runpy.run_path(str(script), run_name="__main__")
