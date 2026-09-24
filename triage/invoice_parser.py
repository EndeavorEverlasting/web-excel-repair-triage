"""
triage/invoice_parser.py
------------------------
Parse vendor .docx invoices and extract structured line-item data.

Supported vendors: AAA Disposal, NYM Courier, AGL, Cybernet, and generic.

Returns a dict with keys:
    invoice_number, po_number, vendor, service_date, service_window,
    prepared_for, prepared_by, currency, line_items, subtotal, total,
    cost_category   (trucking | labor | courier | other)

Raises InvoiceParseError on unrecognized structure.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class InvoiceParseError(Exception):
    pass


# ── Cost category keyword rules ──────────────────────────────────────────────

CATEGORY_RULES: List[tuple[str, List[str]]] = [
    ("courier", [
        "courier", "messenger", "new york minute", "nym courier", "pickup",
    ]),
    ("trucking", [
        "truck", "logistics", "transport", "hauling", "disposal", "delivery",
        "pallet", "freight",
    ]),
    ("labor", [
        "labor", "labour", "crew", "crew-hour", "technician", "tech", "staff",
        "worker", "installation", "staging", "support",
    ]),
]

# Explicit prefix patterns: if the description STARTS WITH one of these words
# (before a colon, dash, or space), that category wins regardless of what
# other keywords appear in the rest of the text.  This prevents "Labor: 3-person
# logistics team" from being classified as trucking because "logistics" appears.
_PREFIX_CATEGORY: List[tuple[str, List[str]]] = [
    ("labor",    ["labor", "labour", "crew", "tech", "technician", "worker", "staff"]),
    ("courier",  ["courier", "messenger", "nym"]),
    ("trucking", ["truck", "hauling", "disposal", "freight", "pallet"]),
]


def _classify_line(description: str) -> str:
    """Classify a single invoice line-item description.

    Two-pass strategy:
    1. Explicit-prefix pass — if the description starts with a known category
       word (before the first colon/dash/space), use that category.  This
       ensures "Labor: 3-person logistics team …" → labor even though
       "logistics" would normally match trucking.
    2. Keyword-scan pass — standard first-match scan through CATEGORY_RULES.
    """
    import re
    desc_lower = description.lower().strip()

    # Pass 1 — extract the leading label (everything before first colon or
    # separator punctuation) and check against explicit prefixes.
    prefix_match = re.match(r"^([a-z][a-z\-' ]{0,19}?)(?:\s*[:\-–—]|\s{2,}|$)", desc_lower)
    if prefix_match:
        prefix = prefix_match.group(1).strip()
        # Score each category by how many of its prefix keywords appear
        # in the extracted prefix token.
        for category, prefix_kws in _PREFIX_CATEGORY:
            if any(kw in prefix for kw in prefix_kws):
                return category

    # Pass 2 — general keyword scan (first-category-wins).
    for category, keywords in CATEGORY_RULES:
        if any(kw in desc_lower for kw in keywords):
            return category

    return "other"


def _classify_invoice(line_items: List[Dict[str, Any]], vendor_hint: str = "") -> str:
    """Pick the dominant cost category for the invoice as a whole.

    Uses the sum of line-item amounts per category; falls back to first-keyword
    scan on the combined text when no line-item amounts are available.
    """
    if line_items:
        totals: dict = {}
        for item in line_items:
            cat = item.get("category") or _classify_line(item.get("description", ""))
            amt = item.get("amount") or 0.0
            totals[cat] = totals.get(cat, 0.0) + amt
        if totals:
            return max(totals, key=lambda c: totals[c])

    all_text = vendor_hint.lower() + " ".join(
        item.get("description", "") for item in line_items
    ).lower()
    for category, keywords in CATEGORY_RULES:
        if any(kw in all_text for kw in keywords):
            return category
    return "other"


# ── Text extraction helpers ───────────────────────────────────────────────────

def _extract_docx_text(path: str) -> str:
    """
    Return the full plain text of a .docx file by iterating all XML <w:p>
    elements recursively (handles nested tables / frames common in invoice layouts).
    """
    try:
        from docx import Document
    except ImportError:
        raise InvoiceParseError("python-docx is required: pip install python-docx")

    doc = Document(path)
    paragraphs: List[str] = []

    for elem in doc.element.body.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "p":
            texts = []
            for t_elem in elem.iter():
                t_tag = t_elem.tag.split("}")[-1] if "}" in t_elem.tag else t_elem.tag
                if t_tag == "t" and t_elem.text:
                    texts.append(t_elem.text)
            text = "".join(texts).strip()
            if text:
                paragraphs.append(text)

    return "\n".join(paragraphs)


def _find_value(text: str, *patterns: str) -> Optional[str]:
    """Search text for a regex pattern and return the first capture group."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    return None


def _parse_amount(s: str) -> Optional[float]:
    if not s:
        return None
    cleaned = re.sub(r"[^\d.]", "", s.strip())
    try:
        return float(cleaned)
    except ValueError:
        return None


# ── Line-item parsing ─────────────────────────────────────────────────────────

def _is_amount(s: str) -> bool:
    """True if the string looks like a money amount (e.g. '300.00', '1,234.56')."""
    return bool(re.match(r"^\d[\d,]*\.\d{2}$", s.strip()))


def _is_qty(s: str) -> bool:
    """True if the string looks like a quantity (pure integer or small decimal)."""
    return bool(re.match(r"^\d+(\.\d+)?$", s.strip())) and len(s.strip()) <= 10


def _is_unit(s: str) -> bool:
    """True if the string looks like a unit label (day, hours, service, …)."""
    units = {"day", "days", "hour", "hours", "crew-hours", "service", "each", "ea",
             "trip", "trips", "lump", "ls", "job"}
    return s.strip().lower() in units


def _parse_line_items(text: str) -> List[Dict[str, Any]]:
    """
    Extract billing line items from invoice text.

    Handles two layouts:
    1. Sequential paragraphs: description / qty / unit / rate / amount each on own line
    2. Tab-separated single-line rows
    """
    items: List[Dict[str, Any]] = []

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ── Locate billing section ────────────────────────────────────────────────
    start_idx = None
    end_idx   = len(lines)
    for i, line in enumerate(lines):
        if re.search(r"billing summary|item[/ ]*description|description.*qty", line, re.IGNORECASE):
            start_idx = i + 1
        if start_idx is not None and re.search(r"^(subtotal|total due|sub-total)\s*$", line, re.IGNORECASE):
            end_idx = i
            break

    if start_idx is None:
        # Fall back: scan the whole document
        start_idx = 0

    section = lines[start_idx:end_idx]

    # ── Skip column header row (Qty / Unit / Rate / Amount) ──────────────────
    header_consumed = False
    filtered: List[str] = []
    for line in section:
        if not header_consumed and re.match(
            r"^(qty|unit|rate|amount|item|description)\s*$", line, re.IGNORECASE
        ):
            continue
        filtered.append(line)

    # ── Strategy 1: sequential 5-line groups (desc / qty / unit / rate / amt) ─
    i = 0
    while i < len(filtered):
        line = filtered[i]
        # Look-ahead: if next 4 lines match qty / unit / rate / amount pattern
        if (
            i + 4 < len(filtered)
            and _is_qty(filtered[i + 1])
            and _is_unit(filtered[i + 2])
            and _is_amount(filtered[i + 3])
            and _is_amount(filtered[i + 4])
        ):
            desc = line
            qty  = _parse_amount(filtered[i + 1])
            unit = filtered[i + 2]
            rate = _parse_amount(filtered[i + 3])
            amt  = _parse_amount(filtered[i + 4])
            items.append({
                "description": desc,
                "qty":         qty,
                "unit":        unit,
                "rate":        rate,
                "amount":      amt,
                "category":    _classify_line(desc),
            })
            i += 5
            continue

        # Strategy 2: tab-separated row (desc\tqty\tunit\trate\tamt)
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) >= 4:
            try:
                amount = _parse_amount(parts[-1])
                if amount is not None:
                    rate   = _parse_amount(parts[-2]) if len(parts) >= 5 else None
                    unit   = parts[-3] if len(parts) >= 5 else (parts[-2] if len(parts) == 4 else "")
                    qty_s  = parts[-4] if len(parts) >= 5 else (parts[-3] if len(parts) == 4 else "")
                    desc   = " ".join(parts[:max(1, len(parts) - 4)]) or parts[0]
                    items.append({
                        "description": desc,
                        "qty":         _parse_amount(qty_s),
                        "unit":        unit,
                        "rate":        rate,
                        "amount":      amount,
                        "category":    _classify_line(desc),
                    })
                    i += 1
                    continue
            except Exception:
                pass

        # Strategy 3: single line ending in an amount.
        # Lines that are invoice-level summary labels (Total, Subtotal, etc.)
        # are excluded — those are not billable line items.  If a document
        # produces only such lines the weak/partial-structure guard in
        # parse_invoice() raises InvoiceParseError.
        amt_match = re.search(r"\b(\d[\d,]*\.\d{2})\s*$", line)
        if amt_match and not _SUMMARY_LINE_RE.match(line.strip()):
            amount = _parse_amount(amt_match.group(1))
            desc   = line[:amt_match.start()].strip()
            if desc and amount is not None:
                items.append({
                    "description": desc,
                    "qty":         None,
                    "unit":        "",
                    "rate":        None,
                    "amount":      amount,
                    "category":    _classify_line(desc),
                })

        i += 1

    return items


# ── Vendor hints ──────────────────────────────────────────────────────────────

# Lines matching this pattern are invoice-level summary labels, not line items.
# Strategy 3 in _parse_line_items skips these so the weak/partial-structure
# guard in parse_invoice() can fire correctly.
_SUMMARY_LINE_RE = re.compile(
    r"^(total|subtotal|sub-total|amount\s+due|balance\s+due|"
    r"grand\s+total|invoice\s+total|tax|gst|hst|vat)\b",
    re.IGNORECASE,
)

_VENDOR_PATTERNS: List[tuple[str, str]] = [
    (r"AAA\s*Disposal",                     "AAA Disposal"),
    (r"Disposal\s*[&+]\s*Logistics",        "AAA Disposal"),
    (r"NYM\s*Courier|New\s+York\s+Minute",  "NYM Courier"),
    (r"Courier\s*[&+]\s*Logistics",         "NYM Courier"),
    (r"AGL",                                "AGL"),
    (r"Cybernet",                           "Cybernet"),
]


def _detect_vendor(text: str) -> str:
    """
    Detect vendor from the first 5 lines (title/header area) before
    falling back to full-text search. This prevents body text like
    'Cybernet deployment' from hijacking the vendor name.
    """
    header = "\n".join(text.splitlines()[:5])
    for pat, name in _VENDOR_PATTERNS:
        if re.search(pat, header, re.IGNORECASE):
            return name
    for pat, name in _VENDOR_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return name
    return "Unknown Vendor"


# ── Public API ────────────────────────────────────────────────────────────────

def parse_invoice(path: str) -> Dict[str, Any]:
    """
    Parse a vendor .docx invoice and return a structured dict.

    Raises InvoiceParseError if the file cannot be read or has unrecognized structure.
    """
    p = Path(path)
    if not p.exists():
        raise InvoiceParseError(f"Invoice file not found: {path}")
    if p.suffix.lower() != ".docx":
        raise InvoiceParseError(f"Expected a .docx file, got: {p.suffix}")

    try:
        text = _extract_docx_text(str(p))
    except InvoiceParseError:
        raise
    except Exception as exc:
        raise InvoiceParseError(f"Cannot read '{path}': {exc}")

    if not text.strip():
        raise InvoiceParseError(f"Invoice file is empty or has no readable text: {path}")

    vendor = _detect_vendor(text)

    invoice_number = _find_value(
        text,
        r"Invoice\s+No[:\s]+([A-Z0-9\-]+)",
        r"Invoice\s*#\s*([A-Z0-9\-]+)",
        r"INV[:\-]([A-Z0-9\-]+)",
    )
    po_number = _find_value(
        text,
        r"PO\s+No[:\s]+(\d+)",
        r"PO\s*#\s*(\d+)",
        r"Purchase\s+Order[:\s]+(\d+)",
        r"PO\s*:\s*(\d+)",
        r"PO(\d{6,})",
    )
    service_date = _find_value(
        text,
        r"Service\s+Date[:\s]+([^\n|]+)",
        r"Date[:\s]+([A-Za-z]+ \d+,? \d{4})",
    )
    service_window = _find_value(
        text,
        r"Service\s+Window[:\s]+([^\n|]+)",
        r"Service\s+Period[:\s]+([^\n|]+)",
        r"Coverage\s+Period[:\s]+([^\n|]+)",
    )
    prepared_for = _find_value(text, r"Prepared\s+for[:\s]+([^\n|]+)")
    prepared_by  = _find_value(text, r"Prepared\s+by[:\s]+([^\n|]+)")
    currency     = _find_value(text, r"\b(USD|GBP|EUR|CAD)\b") or "USD"

    subtotal_str = _find_value(text, r"Subtotal\s+([\d,]+\.\d{2})")
    total_str    = _find_value(text, r"Total\s+Due\s+([\d,]+\.\d{2})", r"Total\s+([\d,]+\.\d{2})")

    subtotal = _parse_amount(subtotal_str) if subtotal_str else None
    total    = _parse_amount(total_str)    if total_str    else None

    line_items = _parse_line_items(text)

    if total is None and not line_items:
        raise InvoiceParseError(
            f"Could not extract any amounts from '{path}'. "
            "Verify the file matches expected invoice format."
        )

    # Raise on weak/partial structures: total found but no line items could be
    # parsed means the document layout is unrecognized — do not silently classify
    # it as "other" with empty line_items.
    if total is not None and not line_items:
        raise InvoiceParseError(
            f"Invoice total found (${total}) but no line items could be parsed "
            f"from '{path}'. Document layout may not match any supported format. "
            "Expected: sequential paragraph groups (desc/qty/unit/rate/amount) "
            "or tab-separated rows."
        )

    cost_category = _classify_invoice(line_items, vendor)

    # Build totals from line items if not found directly
    if subtotal is None and line_items:
        subtotal = round(sum(item.get("amount") or 0 for item in line_items), 2)
    if total is None:
        total = subtotal

    return {
        "source_file":     str(p),
        "vendor":          vendor,
        "invoice_number":  invoice_number,
        "po_number":       po_number,
        "service_date":    service_date.strip("|").strip()    if service_date    else None,
        "service_window":  service_window.strip("|").strip()  if service_window  else None,
        "prepared_for":    prepared_for.strip("|").strip()    if prepared_for    else None,
        "prepared_by":     prepared_by.strip("|").strip()     if prepared_by     else None,
        "currency":        currency,
        "line_items":      line_items,
        "subtotal":        subtotal,
        "total":           total,
        "cost_category":   cost_category,
    }


def parse_invoices(paths: List[str]) -> List[Dict[str, Any]]:
    """Parse multiple invoice files, raising InvoiceParseError on any failure."""
    return [parse_invoice(p) for p in paths]
