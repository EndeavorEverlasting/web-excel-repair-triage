"""Excel column letter helpers."""
from __future__ import annotations

import re


def col_index_to_letter(col: int) -> str:
    """1-based column index to letter(s), e.g. 1 -> A, 28 -> AB."""
    if col < 1:
        raise ValueError(f"Column index must be >= 1, got {col}")
    letters = ""
    n = col
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def col_letter_to_index(col: str) -> int:
    """Column letter(s) to 1-based index."""
    n = 0
    for ch in col.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def substitute_column_refs(
    text: str,
    ref_in: str,
    ref_out: str,
    new_in: str,
    new_out: str,
) -> str:
    """Replace Excel column references for clock in/out columns in CF XML."""
    ref_in = ref_in.upper()
    ref_out = ref_out.upper()
    new_in = new_in.upper()
    new_out = new_out.upper()

    def _repl(text_in: str, old: str, new: str) -> str:
        pattern = rf"(\$?)({re.escape(old)})(\d+)"
        return re.sub(pattern, rf"\1{new}\3", text_in, flags=re.IGNORECASE)

    out = _repl(text, ref_in, new_in)
    out = _repl(out, ref_out, new_out)
    return out


def rewrite_priorities(xml: str, start: int) -> tuple[str, int]:
    """Rewrite cfRule priority attributes sequentially from *start*."""
    counter = start

    def _repl(m: re.Match) -> str:
        nonlocal counter
        frag = m.group(0)
        new_frag = re.sub(r'priority="\d+"', f'priority="{counter}"', frag, count=1)
        counter += 1
        return new_frag

    out = re.sub(r"<cfRule\b[^>]*(?:>.*?</cfRule>|/>)", _repl, xml, flags=re.DOTALL)
    return out, counter - 1
