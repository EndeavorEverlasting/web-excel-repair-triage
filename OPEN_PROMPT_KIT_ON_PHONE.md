# Open the AI Harness Prompt Kit on Android

## One tap — no download required

**[Open the phone launcher](https://endeavoreverlasting.github.io/web-excel-repair-triage/)**

GitHub does not need to download `index.html` to your phone. The public GitHub Pages launcher opens the same responsive Prompt Kit published from the repository's canonical `main` release.

### From the GitHub Android app

1. Tap **Open the phone launcher** above.
2. When GitHub uses its in-app browser, open the browser menu and choose **Open in browser** so the page opens in Chrome.
3. Tap **Open Prompt Kit** for immediate use.
4. Tap **Install on this Android phone** to place **AI Prompt Kit** on the home screen. When Chrome does not display the native prompt, use Chrome's menu and choose **Install app** or **Add to Home screen**.

The installed home-screen app starts at:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

It is the same Prompt Kit used on desktop, not a separate Android copy or prompt database.

## Moving from a computer to the phone

Open the launcher on the computer and scan its QR code with the Android camera:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/
```

## Source and publishing contract

- Canonical generated/deployed website artifact: `web/prompt-kit/index.html`
- Implementation source: `docs/prompt-kit.js`
- Android/mobile launcher source: `web/prompt-kit-mobile/`
- Pages deployment: `.github/workflows/prompt-kit-pages.yml`
- Stable Prompt Kit URL: `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`
- Launcher URL: `https://endeavoreverlasting.github.io/web-excel-repair-triage/`

The launcher adds install, share, copy-link, QR, and offline-fallback surfaces without changing prompt content or creating a parallel mobile application.


## Quick Controls on touch devices

On a phone or tablet, the floating **Quick Controls** handle is the touch counterpart to desktop Hotkeys. The old floating Reference button is folded into this control on narrow layouts so there is one obvious mobile command surface.

- **Tap Quick Controls** — open labeled touch commands for Find Prompt, Search, previous/next profile, Favorites, Filters, Reference, Top, and Bottom.
- **Swipe up from Quick Controls** — open **Find Prompt**.
- **Swipe left from Quick Controls** — move to the previous A-E profile slot.
- **Swipe right from Quick Controls** — move to the next A-E profile slot.
- **Swipe down from Quick Controls** — show/hide filters.

The gestures are optional accelerators. Every gesture also has a labeled button in the Quick Controls sheet; normal vertical page scrolling and browser-edge gestures are not captured because gesture recognition begins only on the handle. Desktop keyboard users keep the existing Hotkeys panel and shortcuts.
