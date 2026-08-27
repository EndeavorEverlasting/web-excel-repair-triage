from pathlib import Path

path = Path("scripts/tmp_apply_p92_dev_prod_path_safety.py")
text = path.read_text(encoding="utf-8")

repairs = (
    (
        "remote merge is never local deployment ",
        "remote merged SHA is never treated as local deployment ",
        "P92 remote/local proof wording",
    ),
    (
        "cloud roots/redirection when relevant; terminal host",
        "OneDrive/cloud roots and redirection when relevant; terminal host",
        "P92 OneDrive/cloud roots wording",
    ),
)
for old, new, label in repairs:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one repair anchor, found {count}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
