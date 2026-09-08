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

## Fastest path to a known prompt ID

If you already know the prompt ID, do **not** open More and do **not** use a swipe gesture. Use the dedicated thumb-zone jump:

1. Tap **Go to P#**.
2. For `P111`, type **111**. The `P` is already supplied by the control.
3. When the ID is exact and unambiguous, **P111 opens automatically**. There is no search-results tap. The main prompt library also reveals and centers P111 behind the detail panel, so closing the panel leaves you at the prompt you requested.
4. Use the **☆ Favorite** control directly in the open prompt panel when you want to keep it. A Favorite automatically becomes its lower-case P-ID hotkey (for example, `p111`); there is no second shortcut-save step.

You do not open **More** first. **Swiping is not required.** This path also avoids opening Chrome's **Find in page**, typing the `P`, and stepping through text matches that do not understand Prompt Kit IDs.

If a shorter ID is also the start of a longer ID (for example `P11` and `P111`), the shorter one waits instead of stealing the route. For **P11**, type `11`; the button changes to **Open P11** and the status tells you the ID is exact. Press **Enter** (including the phone keyboard's Go/Enter key) or tap **Open P11** to open it, or keep typing `1` to continue to P111. There is no timing race.

For the zero-padded IDs `P00` through `P09`, keep the **leading zero**: type `00` for P00, `01` for P01, and so on. A prefix such as `1` that is not itself a canonical prompt stays in **Keep typing** state and cannot submit a fake exact target. A nonexistent number stays closed with a clear no-match message. Pasting `P111` is also safe: the control strips the `P` and resolves the same canonical ID.

## More controls on touch devices

The second floating control is **More**. Open it only when you need a secondary action: **Find Prompt, Previous profile, Next profile, Search, Favorites, Filters, Reference, Top, or Bottom**. These are ordinary labeled buttons; there is no hidden swipe vocabulary to memorize.

Desktop keyboard users keep the existing Hotkeys panel and prompt-ID sequences. The phone controls call the same underlying Prompt Kit actions (`toggleRef`, Favorites activation, filter toggle, scroll, finder/search, profile slots) and do not create a second prompt database or parallel state. Known-ID phone jumps open detail for reading; desktop configured `p##` sequences remain the power-user copy+reveal path, with phone Copy available after open.
