---
name: tencent-ppt
description: Generates web-based presentation slides (HTML/CSS) following the Tencent PPT design system, with TencentSans font, brand colors, in-browser visual editing, and PDF export.
version: 3.6.0
author: shiyicao
allowed-tools: 
disable: false
---

# Tencent PPT Slide Generator

Generates `index.html` + `styles.css` + a static `assets/` folder (fonts, media, slideshow engine). Open in a browser via the bundled local server for full features (navigation, gallery, in-place editing, PDF export), or double-click `index.html` for a quick preview.

## Workflow

### 1. Gather Requirements

- **Topic & audience**: What and for whom?
- **Slide count & outline**: How many slides? Key sections?
- **Media**: Any local images / videos / GIFs, or URLs?
- **Color theme**: Blue monochrome (default) or multicolor?

### 2. Plan Slides

Present a structured plan before generating. One core topic per slide — prefer focused over cramped. For each slide, pick a layout type:

- **Cover**: `cover-grid` / `cover-blocks` / `cover-stripes` / `cover-light` / `cover-blue-solid` / `cover-photo`
- **Content**: `title-only` / `content-text` / `content-image-right` / `content-image-left` / `content-full-image` / `content-3-images` / `content-2-column` / `content-cards` / `content-chart` / `content-video` / `content-quote` / `content-comparison` / `content-timeline` / `content-stats`
- **Structural**: `toc` / `section-divider` / `ending-thanks`

Layout HTML/CSS templates: see `references/layout-patterns.md`.

### 3. Set Up Project — hard-link skill assets

Hard links share the inode; both `file://` and HTTP paths work. Symlinks break under `file://`; `cp` wastes ~17MB on fonts.

```bash
mkdir -p slides-output/{assets/{js,fonts,media},scripts}
ln -f SKILL_DIR/assets/js/app.js slides-output/assets/js/app.js
ln -f SKILL_DIR/scripts/serve.py slides-output/scripts/serve.py
ln -f SKILL_DIR/assets/fonts/TencentSans-W3.ttf slides-output/assets/fonts/TencentSans-W3.ttf
ln -f SKILL_DIR/assets/fonts/TencentSans-W7.ttf slides-output/assets/fonts/TencentSans-W7.ttf
for f in SKILL_DIR/assets/media/*; do ln -f "$f" slides-output/assets/media/; done
```

Hard-link **user-provided local media** the same way and reference with relative paths — `<img src="assets/media/photo.jpg">`. **Never use absolute paths**: they taint the PDF-export canvas under `file://` and make decks non-portable.

### 4. Generate Files

Generate exactly two files:

| File | Content |
|------|---------|
| `index.html` | All slides as `<div class="slide" data-slide="N">`, linked to `styles.css` and `assets/js/app.js` |
| `styles.css` | `@font-face` declarations + shared styles + per-slide `[data-slide="N"]` scoped rules |

**Never modify `assets/`** — those are static skill assets.

#### Critical Rules

- **Canvas**: Fixed 1920×1080px. `app.js` handles `transform: scale()` to fit any screen — never resize the `.slide` div.
- **Fonts**: `@font-face` loads TencentSans-W3/W7. Set `font-family` on `.slide` only — children inherit. Never override on inner elements.
- **No inline styles/scripts**: All CSS in `styles.css`, all JS in `app.js`. `index.html` has zero `<style>` or `<script>` blocks.
- **One active slide**: Exactly one `<div class="slide">` has class `active` (usually the first).
- **Font-size floor**: 22px minimum for visible text (page numbers exempt at 14px). Full table in `references/authoring-details.md`.
- **Inline text-heavy SVG**: Diagrams with substantive `<text>` content **must** be pasted directly as `<svg>...</svg>` into `index.html`, NOT loaded as `<img src="x.svg">`. Externally referenced SVGs render as a single oversized glyph in the exported PDF (html2canvas viewBox bug). Image-only SVGs are unaffected. Example in `references/authoring-details.md`.

#### Layout Integrity Audit (after each slide)

1. **Boundary**: All elements within 0–1920 (x) and 0–1080 (y)
2. **Overlap**: Non-nested siblings have ≥8px clearance
3. **Overflow**: Text doesn't overflow containers
4. **Space utilization**: Content area (top ~180 → bottom ~1030) fills ≥80%; lowest content within 120px of footer; near-footer elements need `z-index: 2` (footer-bar is `z-index: 1`)

#### Slide Add/Remove/Reorder Checklist

1. Renumber all `data-slide` attributes sequentially (1, 2, 3, ...)
2. Update `.page-number` text in each slide's footer
3. Update section numbers if sections reordered

### 5. Start Preview Server

```bash
cd slides-output && python3 scripts/serve.py 8080
```

`serve.py` is a tiny stdlib-only dev server that adds **`PUT` on `*.html`** for the editor's silent in-place save with auto-backup, plus path-traversal protection and CORS scoped to `localhost`. Hard-link it from the skill (Step 3).

Then open `http://localhost:8080` and tell the user:

> "已启动 PPT 预览，请在浏览器中打开 http://localhost:8080 查看。
> 按 **P** 导出 PDF，按 **E** 进入可视化编辑（点击文字直接改、双击图片替换、**Ctrl+S 直接覆盖原文件并自动备份**）。"

If the user runs `python3 -m http.server` or opens via `file://` instead, the editor still works but Ctrl+S falls back to downloading `<title>-edited.html`; PDF export needs HTTP mode.

## Project Structure

```
slides-output/
├── index.html          # All slides (LLM-generated)
├── styles.css          # All styles (LLM-generated)
├── assets/             # Hard-linked from skill assets + user media
│   ├── js/app.js       # Slideshow engine + visual editor (static)
│   ├── fonts/          # TencentSans-W3.ttf, TencentSans-W7.ttf
│   └── media/          # Logos, patterns, footer-bar + user images/videos
└── scripts/
    └── serve.py        # Dev server: GET + PUT (in-place save) (static)
```

## Reference Files (read on demand)

- **`references/layout-patterns.md`** — HTML/CSS templates for every layout type, the `index.html` and `styles.css` boilerplate
- **`references/design-spec.md`** — Brand colors, full typography scale, spacing tokens, layout integrity rules
- **`references/authoring-details.md`** — Font-size table, Visual Editor full capability matrix, Media Handling rules, PDF Export internals, slideshow engine runtime features, EDITABLE_SELECTORS guidance, inline-SVG example
