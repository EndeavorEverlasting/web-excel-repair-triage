from pathlib import Path

path = Path('docs/prompt-kit-polish.js')
text = path.read_text(encoding='utf-8')
replacements = {
    "action.setAttribute('aria-label','Browse all prompts and choose Favorites');": "action.setAttribute('aria-label','Browse all prompts');",
    "action.setAttribute('aria-label','Clear Favorites search and prompt filters');": "action.setAttribute('aria-label','Clear Favorites filters');",
}
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit(f'Expected one accessible-name anchor: {old!r}')
    text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('FAVORITES_EMPTY_ACCESSIBLE_NAMES_REPAIRED=PASS')
