# Authoring Details — `tencent-ppt`

This file gathers the **on-demand details** of the skill: full font-size table,
Visual Editor capabilities, Media Handling rules, PDF export internals, and
the slideshow engine's runtime feature list. SKILL.md only carries the
generation-time workflow — read this file when you need any of the below.

---

## Font Size Rules

`references/design-spec.md` is the single source of truth. Quick reference:

| Element | Recommended | Minimum |
|---------|-------------|---------|
| Cover title | 72px | 64px |
| Cover subtitle | 48px | 44px |
| Section title | 60px | 52px |
| Slide heading | 48px | 44px |
| Card/column title | 38px | 34px |
| Body text | 32px | 28px |
| Statistics number | 96px | 80px |
| Section label | 26px | 24px |
| Captions / badges | 24px | 22px |
| Page number | 14px | 14px |

**Absolute floor**: No visible text below **22px**, except page numbers (14px).

**Rationale**: On MacBook (scale ~0.75×), 32px body text renders as ~24px — still readable at 3–5m distance.

### Font Family Rule

ALL text uses `'TencentSans'` as primary font, set on `.slide` and inherited by all children. Never override `font-family` on inner elements.

### Post-Generation Audit

1. **Font size audit**: Every `font-size` below 22px (except `.page-number` 14px) is a violation
2. **Consistency audit**: All section dividers use identical styles
3. **Space audit**: Lowest content within 120px of footer on every slide

---

## Slideshow Engine (`app.js`) — Runtime Features

`app.js` is a static skill asset. It auto-discovers all `.slide` elements and provides:

- **Keyboard navigation**: ← → ↑ ↓ Space Home End
- **Fullscreen**: F key
- **Gallery / overview**: G key or ▦ button — thumbnail grid for quick slide navigation
- **Visual editor**: E key or ✏️ button — in-browser WYSIWYG editing (see below)
- **PDF export**: P key or 📄 button (**HTTP mode only** — under `file://` the button is hidden, P key shows a friendly tip)
- **Progress bar** at top
- **Slide counter** (e.g., "3 / 15")
- **Auto-hide control bar** (appears on hover)
- **Viewport scaling**: `transform: scale()` with 300ms polling fallback

Navigation, fullscreen, gallery, and visual editing work under both `file://` and HTTP. PDF export requires HTTP mode.

---

## PDF Export

Built into `app.js`. Uses html2canvas + jsPDF loaded from CDN on first use. **Requires HTTP mode** (local server).

- Under `file://`: export button is hidden; pressing P shows a friendly tip directing the user to start preview via the dev server
- Under HTTP (`localhost`): P key or 📄 button triggers export
- Internet required on first export (CDN libraries cached after)
- Progress overlay shows capture status
- Temporarily resets `transform: scale()` to capture at full 1920×1080
- PDF filename defaults to `<title>` of `index.html`

---

## Visual Editor (v3.4+)

Built into `app.js`. Toggle with **E** key or the **✏️** button in the control bar. Works under both `file://` and HTTP — no server required.

### Capabilities

| Operation | How |
|-----------|-----|
| Edit text | Click any text on the active slide → type. Browser-native undo/redo (Ctrl/Cmd+Z / Y) works inside fields. |
| Format selection | Select text → floating toolbar appears with **B / I / U / A+ / A− / color / clear**. |
| Replace image | Double-click any image (skip Tencent logo / pattern overlays) → file picker → image is embedded as DataURL. |
| Duplicate slide | Floating dock → ⧉. Renumbers `data-slide` and `.page-number` automatically. |
| Add blank slide | Floating dock → ＋. Inserts a minimal `content-heading` + body scaffold after the current slide. |
| Delete slide | Floating dock → 🗑 (confirms). At least 1 slide always retained. |
| **Save (in place)** | Ctrl/Cmd+S or floating dock → 💾. Sends a `PUT` to the current path. The skill's `serve.py` writes the file to disk and creates a `<name>.YYYYMMDD-HHMMSS.bak.html` backup automatically. No permission prompt, no FSA, just a silent write. If the server doesn't accept PUT (e.g. user ran `python3 -m http.server` or opened via `file://`), Ctrl+S falls back to downloading `<title>-edited.html`. |
| **Undo** | Floating dock → ↶ or Ctrl/Cmd+Shift+Z. Coarse-grained snapshot stack — captures state before each save / slide-op / image-replace (up to 30 steps). For fine-grained text undo, use browser-native Ctrl/Cmd+Z while typing. |
| Exit | Esc, E key, or floating dock → ✕. |
| Move dock | Drag the `⋮⋮` handle. Click (no drag) the handle to collapse/expand into a tiny grip. |

### Behavior Notes

- Only the **active slide** is editable at a time. Switching slides via ← → keeps edit mode on and hands editability to the new active slide.
- Text containers are marked `contenteditable="plaintext-only"` (falls back to `true` on browsers without plaintext support). Existing inline structure is preserved on save.
- The downloaded HTML strips all editor-injected UI and the `contenteditable` attributes, then re-asserts `active` on slide #1. The output is a clean static `index.html`.
- Replaced images are inlined as DataURL — they ride inside the saved HTML and survive moving the file. Beware: large images bloat file size; consider hard-linking into `assets/media/` for production decks.
- The editor is **opt-in** at the user level. The PDF export, gallery, and navigation all continue to work alongside it.

### Limitations

- Layout (positioning, sizes set in `styles.css`) is NOT editable in-browser. For structural changes, edit `index.html` / `styles.css` and re-open.
- Custom diagrams (SVGs with `<path>` connectors) keep their geometry; only text labels inside them edit cleanly.
- Text formatting from the toolbar serializes as inline `<span style="...">`, which deviates from the "no inline styles" rule — that's intentional for the user-edit path; LLM-authored slides should still keep styles in `styles.css`.

### Editable Selectors (v3.5+)

The editor only marks an element editable if it matches its selector list (text-bearing tags `h1-h6`, `p`, `li`, `span`, `blockquote` plus a curated set of layout classes — see `EDITABLE_SELECTORS` in `app.js`).

v3.5 expanded the class list to cover most card-style layouts (`.paradigm-*`, `.stage-*`, `.ability-*`, `.layer-*`, `.cant-do-*`, `.criteria-*`, `.case-*`, `.timeline-*`, `.ind-*`, etc.). When you author new layouts, prefer `<p>` / `<h3>` / `<span>` over `<div>` for any container holding plain text — they are always editable and styling is identical (just remember `margin: 0` if you don't want default `<p>` spacing).

---

## Media Handling

1. **Local files**: Hard-link into `assets/media/` and use relative path — `<img src="assets/media/photo.jpg">`. **Never use absolute paths** — they break PDF export under `file://` (cross-origin canvas tainting) and make slides non-portable.
2. **URLs**: Use directly — `<img src="https://example.com/img.jpg">`. Note: remote images may fail PDF export under `file://` due to CORS.
3. **Formats**: PNG, JPG, SVG, WebP, GIF (animated), MP4, WebM.
4. **Video**: `<video controls autoplay muted loop>` with `<source>`.
5. **Sizing**: `object-fit: cover` or `contain` to preserve aspect ratio.
6. **File naming**: Preserve original filename. If conflicts arise, prefix with a short identifier (e.g., `user-photo.jpg`).

### Inline text-heavy SVG (PDF-export pitfall)

`html2canvas` cannot rescale text inside externally referenced SVG files: it rasterizes them at viewBox size and CSS-scales the result, clipping text. The on-screen preview looks fine, but the exported PDF page shows a single huge glyph instead of the diagram.

If a diagram contains substantive `<text>` (timeline labels, comparison-card text, anything with more than a couple of words), **paste the `<svg>...</svg>` directly into `index.html`**:

```html
<!-- Bad — exports as a single oversized glyph -->
<img src="assets/media/my-diagram.svg" class="diagram">

<!-- Good — html2canvas walks the SVG DOM and renders every node -->
<svg class="diagram" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 760">
  <text x="60" y="60" font-size="32" font-weight="700" fill="#0A1F44">Diagram title</text>
  <!-- ...full SVG markup... -->
</svg>
```

```css
.diagram { width: 100%; height: auto; max-height: 100%; display: block; }
```

Image-only SVGs (icons, single-glyph logos with no text) can stay as `<img>` — the bug only affects text rendering.
