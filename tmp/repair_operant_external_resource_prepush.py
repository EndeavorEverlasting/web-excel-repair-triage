#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / ".githooks" / "pre-push"
text = path.read_text(encoding="utf-8")
anchor = "python -m unittest tests.test_operant_product_identity -v\n"
addition = anchor + "python scripts/validate_operant_external_resources.py --summary\npython -m unittest tests.test_operant_external_resources -v\n"
if "validate_operant_external_resources.py --summary" not in text:
    if anchor not in text:
        raise SystemExit("pre-push operant identity anchor missing")
    text = text.replace(anchor, addition, 1)
path.write_text(text, encoding="utf-8")
print("OPERANT_EXTERNAL_RESOURCE_PREPUSH_REPAIRED=1")
