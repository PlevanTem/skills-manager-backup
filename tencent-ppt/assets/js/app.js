/**
 * Tencent PPT Slideshow Engine v3.5
 *
 * Static asset — hard-linked into every presentation project.
 * DO NOT edit per-presentation. All customization lives in index.html + styles.css.
 *
 * v3.5 changelog
 *   - EDITABLE_SELECTORS extended to cover common layout-card text classes
 *     (paradigm-*, stage-*, ability-*, cant-do-*, layer-*, criteria-*, case-*,
 *     timeline-*, ind-*, etc.) so <div class="X">text</div> wrappers used
 *     across non-template layouts are now clickable in edit mode.
 *
 * Features:
 *   - Viewport scaling (transform: scale) for 1920×1080 canvas
 *   - Keyboard & button navigation (←→↑↓ Space Home End)
 *   - Fullscreen toggle (F)
 *   - Gallery / overview mode (G) — thumbnail grid for quick navigation
 *   - Progress bar & slide counter
 *   - PDF export via html2canvas + jsPDF (P key or button) — HTTP mode only
 *   - Auto-hide control bar
 *   - **Visual editor (E key)** — inline text editing, image replacement,
 *     formatting toolbar, slide duplicate/delete, save edited HTML (Ctrl+S)
 */

(function () {
  'use strict';

  // ── Protocol detection ─────────────────────────────────────────
  var isFileProtocol = location.protocol === 'file:';

  // ── Slide discovery ──────────────────────────────────────────────
  var slides = document.querySelectorAll('.slide');
  var total  = slides.length;
  if (!total) return;

  var current = 0;
  var galleryOpen = false;

  // ── Inject navigation UI ────────────────────────────────────────
  // Hide export button under file:// protocol
  var exportBtn = isFileProtocol ? '' :
    '<button id="pptExport" title="Export PDF (P)">📄</button>';

  var controlsHTML =
    '<div class="ppt-progress"><div class="ppt-progress-fill" id="pptProgress"></div></div>' +
    '<div class="ppt-controls" id="pptControls">' +
      '<button id="pptPrev" title="Previous (←)">◀</button>' +
      '<span class="ppt-counter" id="pptCounter">1 / ' + total + '</span>' +
      '<button id="pptNext" title="Next (→)">▶</button>' +
      '<button id="pptGallery" title="Gallery (G)">▦</button>' +
      '<button id="pptFS" title="Fullscreen (F)">⛶</button>' +
      '<button id="pptEdit" title="Edit (E)">✏️</button>' +
      exportBtn +
    '</div>' +
    '<div class="ppt-export-overlay" id="pptExportOverlay">' +
      '<h2>Exporting PDF…</h2>' +
      '<div class="ppt-export-progress" id="pptExportProgress">Preparing…</div>' +
      '<div class="ppt-export-bar-bg"><div class="ppt-export-bar-fill" id="pptExportBar"></div></div>' +
    '</div>';

  // Gallery overlay
  var galleryHTML = '<div class="ppt-gallery" id="pptGalleryOverlay">' +
    '<div class="ppt-gallery-header">' +
      '<h2 class="ppt-gallery-title">Slide Overview</h2>' +
      '<button class="ppt-gallery-close" id="pptGalleryClose">✕</button>' +
    '</div>' +
    '<div class="ppt-gallery-grid" id="pptGalleryGrid"></div>' +
  '</div>';

  // file:// tip overlay
  var tipHTML = '<div class="ppt-tip-overlay" id="pptTipOverlay">' +
    '<div class="ppt-tip-box">' +
      '<h2>导出 PDF 需要启动预览服务</h2>' +
      '<p>当前以本地文件方式打开，无法导出 PDF。</p>' +
      '<p>请在 CodeBuddy / AI 助手中输入：</p>' +
      '<div class="ppt-tip-cmd">"帮我启动 PPT 预览"</div>' +
      '<p class="ppt-tip-sub">启动后即可正常导出 PDF、并获得更好的预览体验。</p>' +
      '<button class="ppt-tip-close" id="pptTipClose">我知道了</button>' +
    '</div>' +
  '</div>';

  var wrapper = document.createElement('div');
  wrapper.innerHTML = controlsHTML + galleryHTML + tipHTML;
  while (wrapper.firstChild) document.body.appendChild(wrapper.firstChild);

  // Inject styles (self-contained)
  var style = document.createElement('style');
  style.textContent =
    /* Progress bar */
    '.ppt-progress{position:fixed;top:0;left:0;right:0;height:4px;background:rgba(255,255,255,.1);z-index:9000}' +
    '.ppt-progress-fill{height:100%;background:#0052D9;transition:width .3s}' +
    /* Control bar */
    '.ppt-controls{position:fixed;bottom:0;left:0;right:0;height:56px;' +
      'background:linear-gradient(transparent,rgba(0,0,0,.6));display:flex;align-items:center;' +
      'justify-content:center;gap:20px;z-index:9000;opacity:0;transition:opacity .3s}' +
    'body:hover .ppt-controls,.ppt-controls:hover{opacity:1}' +
    '.ppt-controls button{background:rgba(255,255,255,.15);border:none;color:#fff;' +
      'width:40px;height:40px;border-radius:50%;cursor:pointer;font-size:18px;' +
      'display:flex;align-items:center;justify-content:center;transition:background .2s}' +
    '.ppt-controls button:hover{background:rgba(255,255,255,.3)}' +
    '.ppt-counter{color:rgba(255,255,255,.8);font-size:14px;min-width:60px;text-align:center}' +
    /* Export overlay */
    '.ppt-export-overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.85);' +
      'display:none;flex-direction:column;align-items:center;justify-content:center;gap:20px}' +
    '.ppt-export-overlay.active{display:flex}' +
    '.ppt-export-overlay h2{color:#fff;font-size:24px;font-family:inherit}' +
    '.ppt-export-progress{color:rgba(255,255,255,.7);font-size:16px}' +
    '.ppt-export-bar-bg{width:320px;height:6px;background:rgba(255,255,255,.15);border-radius:3px;overflow:hidden}' +
    '.ppt-export-bar-fill{height:100%;background:#0052D9;border-radius:3px;transition:width .3s;width:0}' +
    /* Tip overlay (file:// PDF hint) */
    '.ppt-tip-overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.75);' +
      'display:none;align-items:center;justify-content:center}' +
    '.ppt-tip-overlay.active{display:flex}' +
    '.ppt-tip-box{background:#fff;border-radius:12px;padding:40px 48px;max-width:480px;text-align:center;' +
      'font-family:inherit;box-shadow:0 20px 60px rgba(0,0,0,.3)}' +
    '.ppt-tip-box h2{font-size:22px;color:#1a1a2e;margin:0 0 16px;font-weight:700}' +
    '.ppt-tip-box p{font-size:15px;color:#555;line-height:1.6;margin:0 0 12px}' +
    '.ppt-tip-cmd{background:#F0F4FF;border:1px solid #D0DFFF;border-radius:8px;padding:12px 20px;' +
      'font-size:16px;color:#0052D9;font-weight:700;margin:16px 0;user-select:all}' +
    '.ppt-tip-sub{font-size:13px;color:#999;margin:12px 0 20px}' +
    '.ppt-tip-close{background:#0052D9;color:#fff;border:none;border-radius:8px;' +
      'padding:10px 32px;font-size:15px;cursor:pointer;transition:background .2s}' +
    '.ppt-tip-close:hover{background:#0040B0}' +
    /* Gallery overlay */
    '.ppt-gallery{position:fixed;inset:0;z-index:9500;background:rgba(10,10,30,.95);' +
      'display:none;flex-direction:column;overflow:hidden}' +
    '.ppt-gallery.active{display:flex}' +
    '.ppt-gallery-header{display:flex;align-items:center;justify-content:space-between;' +
      'padding:20px 32px;flex-shrink:0}' +
    '.ppt-gallery-title{color:#fff;font-size:20px;font-weight:700;font-family:inherit;margin:0}' +
    '.ppt-gallery-close{background:rgba(255,255,255,.15);border:none;color:#fff;' +
      'width:36px;height:36px;border-radius:50%;cursor:pointer;font-size:18px;' +
      'display:flex;align-items:center;justify-content:center;transition:background .2s}' +
    '.ppt-gallery-close:hover{background:rgba(255,255,255,.3)}' +
    '.ppt-gallery-grid{flex:1;overflow-y:auto;padding:0 32px 32px;' +
      'display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;' +
      'align-content:start}' +
    '.ppt-gallery-item{position:relative;cursor:pointer;border-radius:6px;overflow:hidden;' +
      'border:3px solid transparent;transition:border-color .2s,transform .2s;aspect-ratio:16/9;background:#222}' +
    '.ppt-gallery-item:hover{border-color:rgba(255,255,255,.4);transform:scale(1.03)}' +
    '.ppt-gallery-item.current{border-color:#0052D9}' +
    '.ppt-gallery-thumb{width:1920px;height:1080px;transform-origin:0 0;pointer-events:none;' +
      'position:absolute;top:0;left:0;overflow:hidden}' +
    '.ppt-gallery-label{position:absolute;bottom:0;left:0;right:0;padding:6px 10px;' +
      'background:linear-gradient(transparent,rgba(0,0,0,.7));color:rgba(255,255,255,.9);' +
      'font-size:13px;font-family:inherit;text-align:center;z-index:2}';
  document.head.appendChild(style);

  // ── DOM refs ─────────────────────────────────────────────────────
  var progressBar = document.getElementById('pptProgress');
  var counter     = document.getElementById('pptCounter');

  // ── Viewport scaling ─────────────────────────────────────────────
  function fitSlide() {
    var vw = window.innerWidth  || document.documentElement.clientWidth;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var scale = Math.min(vw / 1920, vh / 1080);
    var left  = (vw - 1920 * scale) / 2;
    var top   = (vh - 1080 * scale) / 2;
    for (var i = 0; i < total; i++) {
      slides[i].style.left      = left + 'px';
      slides[i].style.top       = top  + 'px';
      slides[i].style.transform = 'scale(' + scale + ')';
    }
  }

  window.addEventListener('resize', fitSlide);
  window.addEventListener('DOMContentLoaded', fitSlide);
  document.addEventListener('fullscreenchange', function () {
    setTimeout(fitSlide, 100); setTimeout(fitSlide, 300);
  });
  document.addEventListener('webkitfullscreenchange', function () {
    setTimeout(fitSlide, 100); setTimeout(fitSlide, 300);
  });
  // Polling fallback (catches edge cases like devtools open/close)
  (function () {
    var lastW = 0, lastH = 0;
    setInterval(function () {
      var w = window.innerWidth  || document.documentElement.clientWidth;
      var h = window.innerHeight || document.documentElement.clientHeight;
      if (w !== lastW || h !== lastH) { lastW = w; lastH = h; fitSlide(); }
    }, 300);
  })();
  fitSlide();

  // ── Navigation ───────────────────────────────────────────────────
  function updateUI() {
    counter.textContent  = (current + 1) + ' / ' + total;
    progressBar.style.width = ((current + 1) / total * 100) + '%';
  }

  function goTo(idx) {
    if (idx < 0 || idx >= total) return;
    slides[current].classList.remove('active');
    current = idx;
    slides[current].classList.add('active');
    updateUI();
    if (typeof editMode !== 'undefined' && editMode &&
        typeof refreshEditableForCurrent === 'function') {
      refreshEditableForCurrent();
    }
  }
  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  function toggleFullscreen() {
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
      var el = document.documentElement;
      (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
    } else {
      (document.exitFullscreen || document.webkitExitFullscreen).call(document);
    }
  }

  // ── Gallery / Overview ──────────────────────────────────────────
  var galleryOverlay = document.getElementById('pptGalleryOverlay');
  var galleryGrid    = document.getElementById('pptGalleryGrid');

  function openGallery() {
    if (galleryOpen) return;
    galleryOpen = true;

    // Build thumbnails
    galleryGrid.innerHTML = '';
    for (var i = 0; i < total; i++) {
      var item = document.createElement('div');
      item.className = 'ppt-gallery-item' + (i === current ? ' current' : '');
      item.setAttribute('data-index', i);

      // Clone slide content for thumbnail — preserve ALL original classes
      var inner = slides[i].cloneNode(true);
      inner.classList.add('ppt-gallery-thumb');
      // Force visible (original .slide has display:none unless .active)
      inner.style.display = 'block';
      inner.style.position = 'absolute';
      inner.style.left = '0';
      inner.style.top = '0';
      inner.style.transform = '';
      inner.style.transformOrigin = '0 0';

      var label = document.createElement('div');
      label.className = 'ppt-gallery-label';
      // Extract slide title from heading elements
      var titleEl = slides[i].querySelector('.cover-title, .content-heading, .section-title, .center-title, .thanks-text');
      var slideTitle = titleEl ? titleEl.textContent.trim() : '';
      label.textContent = (i + 1) + (slideTitle ? ' · ' + slideTitle.substring(0, 40) : '');

      item.appendChild(inner);
      item.appendChild(label);
      galleryGrid.appendChild(item);

      // Scale the cloned slide to fit the thumbnail container
      (function (el, itemEl) {
        requestAnimationFrame(function () {
          var w = itemEl.offsetWidth;
          if (w > 0) {
            el.style.transform = 'scale(' + (w / 1920) + ')';
          }
        });
      })(inner, item);
    }

    galleryOverlay.classList.add('active');

    // Scroll current slide into view
    var currentItem = galleryGrid.querySelector('.current');
    if (currentItem) {
      currentItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function closeGallery() {
    if (!galleryOpen) return;
    galleryOpen = false;
    galleryOverlay.classList.remove('active');
    galleryGrid.innerHTML = ''; // free cloned DOM
  }

  function toggleGallery() {
    if (galleryOpen) closeGallery(); else openGallery();
  }

  // Gallery click handler (event delegation)
  galleryGrid.addEventListener('click', function (e) {
    var item = e.target.closest('.ppt-gallery-item');
    if (!item) return;
    var idx = parseInt(item.getAttribute('data-index'), 10);
    if (!isNaN(idx)) {
      goTo(idx);
      closeGallery();
    }
  });

  document.getElementById('pptGalleryClose').addEventListener('click', function () { closeGallery(); this.blur(); });

  // Resize gallery thumbnails on window resize
  window.addEventListener('resize', function () {
    if (!galleryOpen) return;
    var items = galleryGrid.querySelectorAll('.ppt-gallery-item');
    for (var i = 0; i < items.length; i++) {
      var inner = items[i].querySelector('.ppt-gallery-thumb');
      if (inner) {
        var w = items[i].offsetWidth;
        if (w > 0) inner.style.transform = 'scale(' + (w / 1920) + ')';
      }
    }
  });

  // ── file:// PDF tip ────────────────────────────────────────────
  var tipOverlay = document.getElementById('pptTipOverlay');
  document.getElementById('pptTipClose').addEventListener('click', function () {
    tipOverlay.classList.remove('active');
  });

  function showFileTip() {
    tipOverlay.classList.add('active');
  }

  // Button bindings
  document.getElementById('pptPrev').addEventListener('click', function () { prev(); this.blur(); });
  document.getElementById('pptNext').addEventListener('click', function () { next(); this.blur(); });
  document.getElementById('pptGallery').addEventListener('click', function () { toggleGallery(); this.blur(); });
  document.getElementById('pptFS').addEventListener('click', function () { toggleFullscreen(); this.blur(); });
  if (!isFileProtocol) {
    document.getElementById('pptExport').addEventListener('click', function () { exportPDF(); this.blur(); });
  }

  // Keyboard
  document.addEventListener('keydown', function (e) {
    // When gallery is open, only handle gallery-specific keys
    if (galleryOpen) {
      if (e.key === 'Escape' || e.key === 'g' || e.key === 'G') {
        e.preventDefault(); closeGallery();
      }
      return;
    }

    // When tip overlay is open
    if (tipOverlay.classList.contains('active')) {
      if (e.key === 'Escape' || e.key === 'Enter') {
        e.preventDefault(); tipOverlay.classList.remove('active');
      }
      return;
    }

    // Save shortcut works in any mode
    if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
      e.preventDefault();
      if (typeof saveEditedHTML === 'function') saveEditedHTML();
      return;
    }

    // Coarse-grained undo (snapshot stack) — Ctrl/Cmd+Shift+Z
    if (typeof editMode !== 'undefined' && editMode &&
        (e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'z' || e.key === 'Z')) {
      e.preventDefault();
      if (typeof undo === 'function') undo();
      return;
    }

    // When edit mode is on: only Esc/Ctrl+S/E exit; other keys go to the editor
    if (typeof editMode !== 'undefined' && editMode) {
      if (e.key === 'Escape') { e.preventDefault(); toggleEdit(); }
      // Allow typing inside contenteditable regions; don't capture nav keys
      return;
    }

    switch (e.key) {
      case 'ArrowRight': case 'ArrowDown': case ' ':
        e.preventDefault(); next(); break;
      case 'ArrowLeft': case 'ArrowUp':
        e.preventDefault(); prev(); break;
      case 'Home': e.preventDefault(); goTo(0); break;
      case 'End':  e.preventDefault(); goTo(total - 1); break;
      case 'f': case 'F': e.preventDefault(); toggleFullscreen(); break;
      case 'g': case 'G': e.preventDefault(); openGallery(); break;
      case 'e': case 'E':
        e.preventDefault();
        if (typeof toggleEdit === 'function') toggleEdit();
        break;
      case 'p': case 'P':
        e.preventDefault();
        if (isFileProtocol) showFileTip(); else exportPDF();
        break;
      case 'Escape':
        if (document.fullscreenElement) document.exitFullscreen();
        break;
    }
  });

  // Ensure first slide is active on load
  goTo(0);

  // ── PDF Export (HTTP mode only) ────────────────────────────────
  var exportBusy = false;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (document.querySelector('script[src="' + src + '"]')) { resolve(); return; }
      var s = document.createElement('script');
      s.src = src; s.onload = resolve; s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function exportPDF() {
    if (exportBusy || isFileProtocol) return;
    exportBusy = true;

    var overlay  = document.getElementById('pptExportOverlay');
    var progress = document.getElementById('pptExportProgress');
    var bar      = document.getElementById('pptExportBar');
    overlay.classList.add('active');
    progress.textContent = 'Loading libraries…';
    bar.style.width = '0%';

    (async function () {
      try {
        await loadScript('https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js');
        await loadScript('https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js');

        var jsPDF = window.jspdf.jsPDF;
        var pdf = new jsPDF({ orientation: 'landscape', unit: 'px', format: [1920, 1080], compress: true });
        var savedCurrent = current;

        for (var i = 0; i < total; i++) {
          progress.textContent = 'Slide ' + (i + 1) + ' / ' + total;
          bar.style.width = ((i / total) * 100) + '%';

          slides[i].classList.add('active');
          slides[i].style.display = 'block';
          var origT = slides[i].style.transform;
          var origL = slides[i].style.left;
          var origTop = slides[i].style.top;
          slides[i].style.transform = 'none';
          slides[i].style.left = '0px';
          slides[i].style.top  = '0px';

          await new Promise(function (r) { setTimeout(r, 100); });
          var canvas = await html2canvas(slides[i], {
            scale: 2, useCORS: true,
            width: 1920, height: 1080
          });

          slides[i].style.transform = origT;
          slides[i].style.left = origL;
          slides[i].style.top  = origTop;
          if (i !== savedCurrent) {
            slides[i].classList.remove('active');
            slides[i].style.display = '';
          }

          var imgData = canvas.toDataURL('image/jpeg', 0.92);
          if (i > 0) pdf.addPage([1920, 1080], 'landscape');
          pdf.addImage(imgData, 'JPEG', 0, 0, 1920, 1080);
        }

        bar.style.width = '100%';
        progress.textContent = 'Saving…';
        goTo(savedCurrent);

        var title = (document.title || 'slides').replace(/[\\/:*?"<>|]/g, '');
        pdf.save(title + '.pdf');
      } catch (e) {
        alert('PDF export failed: ' + e.message);
        console.error(e);
      } finally {
        overlay.classList.remove('active');
        exportBusy = false;
      }
    })();
  }

  // ── Visual Editor (E key) ──────────────────────────────────────
  // In-browser WYSIWYG editing. Toggle with E or the ✏️ button.
  // - Text nodes inside slides become contenteditable (plaintext-only)
  // - Floating toolbar appears on text selection: B / I / U / size ± / color
  // - Double-click <img> to replace with a local file (DataURL embedded)
  // - Add/duplicate/delete current slide
  // - Ctrl/Cmd+S downloads a clean snapshot of the edited HTML
  // - Esc exits edit mode

  var editMode = false;
  var editToolbar = null;
  var editSidebar = null;
  var editStyleEl = null;
  // Selectors for editable text containers — only leaf-ish text holders.
  // v3.5: extended with common layout-card classes (cant-do-*, ability-*,
  // criteria-*, layer-*, paradigm-*, stage-*, timeline-*, case-*, etc.)
  // so authors who use <div class="card-num">…</div> still get clickable
  // editing without having to wrap text in <p>/<span> manually.
  var EDITABLE_SELECTORS = [
    // Existing core
    '.cover-title','.cover-subtitle','.cover-tag','.cover-meta','.cover-meta-item',
    '.content-heading','.content-subheading','.section-title','.section-subtitle',
    '.section-label','.section-number','.center-title','.center-subtitle',
    'h1','h2','h3','h4','h5','h6','p','li','span','blockquote','figcaption',
    '.badge','.card-title','.card-text','.stat-number','.stat-label',
    '.timeline-title','.timeline-text','.quote-text','.quote-author',
    '.toc-item','.toc-title','.column-title','.column-text',
    '.thanks-text','.page-number','.footer-text',
    '.label','.caption','.meta','.tag',
    // v3.5 extension — common layout-card text containers
    '.callout','.callout-bottom','.chart-caption','.thumb-caption',
    '.stat-baseline','.toc-number','.toc-desc',
    '.compare-tag','.compare-name',
    '.cant-do-num','.cant-do-title','.cant-do-desc',
    '.ability-icon','.ability-title','.ability-via','.ability-desc',
    '.rot-icon','.rot-title','.rot-desc','.rot-quote',
    '.layer-tag','.layer-name','.layer-q','.layer-a',
    '.criteria-num','.criteria-title','.criteria-desc',
    '.paradigm-tag','.paradigm-name','.paradigm-q','.paradigm-a','.paradigm-trait','.paradigm-arrow',
    '.stage-num','.stage-name','.stage-desc','.stage-arrow','.stage-icon',
    '.timeline-date','.timeline-content','.timeline-dot',
    '.case-headline','.case-takeaway',
    '.note-tag','.note-text',
    '.eq-left','.eq-op','.eq-model','.eq-harness',
    '.def-intro','.def-source',
    '.intro-name','intro-title','.book-caption',
    '.fl-big','.fl-small','.thanks-sub',
    '.ct-line1','.ct-line2','.oq-intro','.oq-list',
    '.ind-tier-tag','.ind-name','.ind-evidence',
    '.fs-row','.react-step','.react-arrow'
  ].join(',');

  function injectEditStyles() {
    if (editStyleEl) return;
    editStyleEl = document.createElement('style');
    editStyleEl.id = 'pptEditStyles';
    editStyleEl.textContent =
      /* Edit mode body indicator */
      'body.ppt-editing .slide.active{outline:2px dashed rgba(0,82,217,.35);outline-offset:-2px}' +
      /* Editable hover/focus */
      'body.ppt-editing [contenteditable="true"]{cursor:text;border-radius:4px;' +
        'transition:box-shadow .15s,background .15s}' +
      'body.ppt-editing [contenteditable="true"]:hover{background:rgba(0,82,217,.06);' +
        'box-shadow:0 0 0 2px rgba(0,82,217,.25)}' +
      'body.ppt-editing [contenteditable="true"]:focus{outline:none;background:rgba(0,82,217,.08);' +
        'box-shadow:0 0 0 2px #0052D9}' +
      /* Image hover */
      'body.ppt-editing .slide img:not(.cover-logo):not(.pattern-img){cursor:pointer;' +
        'transition:filter .15s,outline .15s}' +
      'body.ppt-editing .slide img:not(.cover-logo):not(.pattern-img):hover{' +
        'filter:brightness(.92);outline:3px dashed #0052D9;outline-offset:2px}' +
      /* Floating toolbar */
      '.ppt-edit-toolbar{position:fixed;display:none;background:#1a1a2e;color:#fff;' +
        'border-radius:8px;padding:6px;z-index:9800;box-shadow:0 8px 24px rgba(0,0,0,.4);' +
        'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:13px;' +
        'gap:2px;align-items:center}' +
      '.ppt-edit-toolbar.active{display:inline-flex}' +
      '.ppt-edit-toolbar button{background:transparent;border:none;color:#fff;cursor:pointer;' +
        'padding:6px 10px;border-radius:4px;font-size:13px;min-width:30px;font-family:inherit;' +
        'display:inline-flex;align-items:center;justify-content:center;transition:background .15s}' +
      '.ppt-edit-toolbar button:hover{background:rgba(255,255,255,.15)}' +
      '.ppt-edit-toolbar button.active{background:#0052D9}' +
      '.ppt-edit-toolbar .sep{width:1px;height:20px;background:rgba(255,255,255,.2);margin:0 4px}' +
      '.ppt-edit-toolbar input[type="color"]{width:28px;height:28px;border:none;' +
        'background:transparent;cursor:pointer;padding:0}' +
      /* Sidebar — compact, draggable icon dock */
      '.ppt-edit-sidebar{position:fixed;bottom:80px;right:16px;' +
        'background:rgba(26,26,46,.92);color:#fff;border-radius:10px;padding:6px;z-index:9700;display:none;' +
        'flex-direction:column;gap:2px;font-family:-apple-system,sans-serif;' +
        'box-shadow:0 8px 24px rgba(0,0,0,.4);backdrop-filter:blur(8px)}' +
      '.ppt-edit-sidebar.active{display:flex}' +
      '.ppt-edit-sidebar.collapsed .ppt-edit-row{display:none}' +
      '.ppt-edit-sidebar.collapsed{padding:4px}' +
      '.ppt-edit-drag{cursor:move;height:14px;display:flex;align-items:center;justify-content:center;' +
        'opacity:.4;user-select:none;font-size:10px;letter-spacing:2px;color:#fff}' +
      '.ppt-edit-drag:hover{opacity:.8}' +
      '.ppt-edit-row{display:flex;gap:2px;align-items:center}' +
      '.ppt-edit-sidebar button{background:transparent;border:none;color:#fff;' +
        'width:34px;height:34px;border-radius:6px;cursor:pointer;font-size:16px;' +
        'font-family:inherit;transition:background .15s;display:inline-flex;' +
        'align-items:center;justify-content:center;padding:0}' +
      '.ppt-edit-sidebar button:hover{background:rgba(255,255,255,.18)}' +
      '.ppt-edit-sidebar button.primary{color:#5b9eff}' +
      '.ppt-edit-sidebar button.primary:hover{background:rgba(91,158,255,.2)}' +
      '.ppt-edit-sidebar button.danger:hover{background:rgba(220,68,68,.4)}' +
      '.ppt-edit-sidebar .sep-h{height:1px;background:rgba(255,255,255,.12);margin:2px 4px}' +
      '.ppt-edit-sidebar .toggle-btn{font-size:12px;opacity:.6}' +
      /* Edit-mode badge (top-left) */
      '.ppt-edit-badge{position:fixed;top:14px;left:14px;background:#0052D9;color:#fff;' +
        'padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600;z-index:9700;' +
        'font-family:-apple-system,sans-serif;display:none;box-shadow:0 4px 12px rgba(0,82,217,.4)}' +
      '.ppt-edit-badge.active{display:block}' +
      /* Toast */
      '.ppt-toast{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);' +
        'background:rgba(20,20,40,.95);color:#fff;padding:10px 22px;border-radius:8px;' +
        'font-family:-apple-system,sans-serif;font-size:14px;z-index:9900;opacity:0;' +
        'pointer-events:none;transition:opacity .25s}' +
      '.ppt-toast.active{opacity:1}';
    document.head.appendChild(editStyleEl);
  }

  function buildEditUI() {
    if (editToolbar && editSidebar) return;
    injectEditStyles();

    // Floating toolbar
    editToolbar = document.createElement('div');
    editToolbar.className = 'ppt-edit-toolbar';
    editToolbar.id = 'pptEditToolbar';
    editToolbar.innerHTML =
      '<button data-cmd="bold" title="Bold (Ctrl+B)"><b>B</b></button>' +
      '<button data-cmd="italic" title="Italic (Ctrl+I)"><i>I</i></button>' +
      '<button data-cmd="underline" title="Underline (Ctrl+U)"><u>U</u></button>' +
      '<span class="sep"></span>' +
      '<button data-cmd="fontSizeDelta" data-arg="2" title="Larger">A+</button>' +
      '<button data-cmd="fontSizeDelta" data-arg="-2" title="Smaller">A−</button>' +
      '<span class="sep"></span>' +
      '<input type="color" id="pptEditColor" title="Text color" value="#1a1a2e">' +
      '<button data-cmd="removeFormat" title="Clear formatting">⌫</button>';
    document.body.appendChild(editToolbar);

    // Sidebar — compact draggable dock with icon-only buttons + tooltips
    editSidebar = document.createElement('div');
    editSidebar.className = 'ppt-edit-sidebar';
    editSidebar.id = 'pptEditSidebar';
    editSidebar.innerHTML =
      '<div class="ppt-edit-drag" id="pptEditDrag" title="Drag to move · click to collapse">⋮⋮</div>' +
      '<div class="ppt-edit-row">' +
        '<button data-action="undo" title="撤销 (Ctrl+Shift+Z)">↶</button>' +
        '<button data-action="duplicate" title="复制当前页">⧉</button>' +
        '<button data-action="addBlank" title="新增空白页">＋</button>' +
        '<button data-action="delete" class="danger" title="删除当前页">🗑</button>' +
      '</div>' +
      '<div class="sep-h"></div>' +
      '<div class="ppt-edit-row">' +
        '<button data-action="replaceImg" title="替换选中图片">🖼</button>' +
        '<button data-action="save" class="primary" title="保存（覆盖原文件 + 备份） (Ctrl+S)">💾</button>' +
        '<button data-action="exit" title="退出编辑 (Esc)">✕</button>' +
      '</div>';
    document.body.appendChild(editSidebar);

    // Drag-to-move + click-to-collapse on the handle
    (function () {
      var handle = document.getElementById('pptEditDrag');
      var startX, startY, startLeft, startTop, dragging = false, moved = false;

      handle.addEventListener('mousedown', function (e) {
        e.preventDefault();
        dragging = true; moved = false;
        var rect = editSidebar.getBoundingClientRect();
        startX = e.clientX; startY = e.clientY;
        startLeft = rect.left; startTop = rect.top;
        // Switch to top/left positioning so we can move freely
        editSidebar.style.right = 'auto';
        editSidebar.style.bottom = 'auto';
        editSidebar.style.left = startLeft + 'px';
        editSidebar.style.top = startTop + 'px';
      });
      document.addEventListener('mousemove', function (e) {
        if (!dragging) return;
        var dx = e.clientX - startX, dy = e.clientY - startY;
        if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
        var nl = Math.max(0, Math.min(window.innerWidth  - editSidebar.offsetWidth,  startLeft + dx));
        var nt = Math.max(0, Math.min(window.innerHeight - editSidebar.offsetHeight, startTop  + dy));
        editSidebar.style.left = nl + 'px';
        editSidebar.style.top  = nt + 'px';
      });
      document.addEventListener('mouseup', function () {
        if (!dragging) return;
        dragging = false;
        // Click (no drag) → toggle collapse
        if (!moved) editSidebar.classList.toggle('collapsed');
      });
    })();

    // Edit-mode badge
    var badge = document.createElement('div');
    badge.className = 'ppt-edit-badge';
    badge.id = 'pptEditBadge';
    badge.textContent = '✏️ Editing';
    document.body.appendChild(badge);

    // Toolbar bindings
    editToolbar.addEventListener('mousedown', function (e) {
      // Prevent stealing selection
      e.preventDefault();
    });
    editToolbar.addEventListener('click', function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;
      var cmd = btn.getAttribute('data-cmd');
      var arg = btn.getAttribute('data-arg');
      applyFormat(cmd, arg);
    });
    document.getElementById('pptEditColor').addEventListener('input', function (e) {
      applyFormat('foreColor', e.target.value);
    });

    // Sidebar bindings
    editSidebar.addEventListener('click', function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;
      var action = btn.getAttribute('data-action');
      switch (action) {
        case 'undo':        undo(); break;
        case 'duplicate':   duplicateSlide(); break;
        case 'addBlank':    addBlankSlide(); break;
        case 'delete':      deleteSlide(); break;
        case 'replaceImg':  replaceSelectedImage(); break;
        case 'save':        saveEditedHTML(); break;
        case 'exit':        toggleEdit(); break;
      }
    });
  }

  function showToast(msg, ms) {
    var t = document.getElementById('pptToast');
    if (!t) {
      t = document.createElement('div');
      t.className = 'ppt-toast';
      t.id = 'pptToast';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('active');
    clearTimeout(t._timer);
    t._timer = setTimeout(function () { t.classList.remove('active'); }, ms || 1800);
  }

  // Find text-bearing nodes in a slide; mark each as contenteditable.
  function makeSlideEditable(slide, on) {
    var nodes = slide.querySelectorAll(EDITABLE_SELECTORS);
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      // Skip if a parent is already editable (avoid nested editors)
      if (n.closest('[contenteditable="true"]') && n.closest('[contenteditable="true"]') !== n) continue;
      // Skip empty wrappers (no direct text)
      if (on) {
        n.setAttribute('contenteditable', 'plaintext-only');
        // Some browsers don't support plaintext-only — fallback to true
        if (n.contentEditable !== 'plaintext-only') n.setAttribute('contenteditable', 'true');
      } else {
        n.removeAttribute('contenteditable');
      }
    }
  }

  function refreshEditableForCurrent() {
    if (!editMode) return;
    // Only the active slide is editable to avoid surprises
    for (var i = 0; i < total; i++) makeSlideEditable(slides[i], false);
    if (slides[current]) makeSlideEditable(slides[current], true);
  }

  function toggleEdit() {
    if (!editMode) {
      buildEditUI();
      editMode = true;
      document.body.classList.add('ppt-editing');
      document.getElementById('pptEditSidebar').classList.add('active');
      document.getElementById('pptEditBadge').classList.add('active');
      refreshEditableForCurrent();
      // Capture pre-edit baseline so user can fully revert
      historyStack = [];
      pushHistory();
      showToast('编辑模式已开启 · 点击文字编辑 · Ctrl+S 保存');
    } else {
      // Exit
      editMode = false;
      hideToolbar();
      for (var i = 0; i < total; i++) makeSlideEditable(slides[i], false);
      document.body.classList.remove('ppt-editing');
      document.getElementById('pptEditSidebar').classList.remove('active');
      document.getElementById('pptEditBadge').classList.remove('active');
      showToast('已退出编辑模式');
    }
  }

  // ── Selection & toolbar ─────────────────────────────────────
  function hideToolbar() {
    if (editToolbar) editToolbar.classList.remove('active');
  }

  function showToolbarAtSelection() {
    var sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) { hideToolbar(); return; }
    // Only show if the selection is inside an editable
    var node = sel.anchorNode;
    if (!node) { hideToolbar(); return; }
    var el = node.nodeType === 1 ? node : node.parentElement;
    if (!el || !el.closest('[contenteditable="true"], [contenteditable="plaintext-only"]')) {
      hideToolbar();
      return;
    }
    var rect = sel.getRangeAt(0).getBoundingClientRect();
    if (!rect || (rect.width === 0 && rect.height === 0)) { hideToolbar(); return; }
    editToolbar.classList.add('active');
    var tw = editToolbar.offsetWidth;
    var th = editToolbar.offsetHeight;
    var top = rect.top - th - 10;
    if (top < 8) top = rect.bottom + 10;
    var left = rect.left + (rect.width / 2) - (tw / 2);
    left = Math.max(8, Math.min(window.innerWidth - tw - 8, left));
    editToolbar.style.top = top + 'px';
    editToolbar.style.left = left + 'px';
  }

  document.addEventListener('selectionchange', function () {
    if (!editMode) return;
    showToolbarAtSelection();
  });
  window.addEventListener('scroll', hideToolbar, true);
  window.addEventListener('resize', hideToolbar);

  // Apply formatting using execCommand (well-supported for inline styles).
  // Stored as inline styles on a <span>, which serializes cleanly into the saved HTML.
  function applyFormat(cmd, arg) {
    if (!cmd) return;
    var sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return;
    if (cmd === 'fontSizeDelta') {
      adjustFontSize(parseInt(arg, 10) || 2);
      return;
    }
    try {
      // Use styleWithCSS so colors/sizes serialize as inline style (cleaner)
      document.execCommand('styleWithCSS', false, true);
      document.execCommand(cmd, false, arg || null);
    } catch (e) { console.warn('execCommand failed', cmd, e); }
    showToolbarAtSelection();
  }

  // Adjust font-size of the selected text by N px. Uses computed style from the
  // anchor element, wraps the selection in a <span style="font-size:Xpx">.
  function adjustFontSize(deltaPx) {
    var sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
    var range = sel.getRangeAt(0);
    var anchorEl = sel.anchorNode && sel.anchorNode.nodeType === 1
      ? sel.anchorNode : (sel.anchorNode && sel.anchorNode.parentElement);
    if (!anchorEl) return;
    var current = parseFloat(window.getComputedStyle(anchorEl).fontSize) || 32;
    var next = Math.max(12, Math.min(200, current + deltaPx));
    var span = document.createElement('span');
    span.style.fontSize = next + 'px';
    try {
      span.appendChild(range.extractContents());
      range.insertNode(span);
      // Restore selection to the inserted span
      sel.removeAllRanges();
      var nr = document.createRange();
      nr.selectNodeContents(span);
      sel.addRange(nr);
    } catch (e) { console.warn('font-size delta failed', e); }
  }

  // ── Image replacement ───────────────────────────────────────
  var lastClickedImg = null;
  document.addEventListener('click', function (e) {
    if (!editMode) return;
    var img = e.target.closest('.slide img');
    if (img && !img.classList.contains('cover-logo') && !img.classList.contains('pattern-img')) {
      lastClickedImg = img;
    }
  });
  document.addEventListener('dblclick', function (e) {
    if (!editMode) return;
    var img = e.target.closest('.slide img');
    if (!img) return;
    if (img.classList.contains('cover-logo') || img.classList.contains('pattern-img')) {
      showToast('logo / pattern 图为模板资源，不建议替换');
      return;
    }
    e.preventDefault();
    pickImageFor(img);
  });

  function pickImageFor(img) {
    var input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = function () {
      var f = input.files && input.files[0];
      if (!f) return;
      pushHistory();
      var reader = new FileReader();
      reader.onload = function () {
        img.src = reader.result; // DataURL — embeds into saved HTML
        showToast('图片已替换');
      };
      reader.readAsDataURL(f);
    };
    input.click();
  }

  function replaceSelectedImage() {
    if (lastClickedImg) {
      pickImageFor(lastClickedImg);
      return;
    }
    // Otherwise pick the first replaceable image on current slide
    var img = slides[current].querySelector('img:not(.cover-logo):not(.pattern-img)');
    if (!img) { showToast('当前页没有可替换的图片'); return; }
    pickImageFor(img);
  }

  // ── Slide operations ────────────────────────────────────────
  function getViewportContainer() {
    return document.querySelector('.slide-viewport') || slides[0].parentNode;
  }

  function refreshSlideRegistry() {
    // Re-query slides; renumber data-slide; rebuild local list
    var container = getViewportContainer();
    var fresh = container.querySelectorAll('.slide');
    // Renumber
    for (var i = 0; i < fresh.length; i++) {
      fresh[i].setAttribute('data-slide', String(i + 1));
      // Update page-number text if present
      var pn = fresh[i].querySelector('.page-number');
      if (pn && /^\s*\d+/.test(pn.textContent)) {
        // Replace leading number while preserving any suffix
        pn.textContent = pn.textContent.replace(/^\s*\d+/, String(i + 1));
      }
    }
    // Mutate the closure-scoped slides list
    slides = fresh;
    total = slides.length;
    // Update counter UI
    if (counter) counter.textContent = (current + 1) + ' / ' + total;
  }

  function duplicateSlide() {
    if (!total) return;
    pushHistory();
    var src = slides[current];
    var clone = src.cloneNode(true);
    clone.classList.remove('active');
    // Remove contenteditable from clone
    var eds = clone.querySelectorAll('[contenteditable]');
    for (var i = 0; i < eds.length; i++) eds[i].removeAttribute('contenteditable');
    src.parentNode.insertBefore(clone, src.nextSibling);
    refreshSlideRegistry();
    goTo(current + 1);
    refreshEditableForCurrent();
    showToast('已复制当前页');
  }

  function addBlankSlide() {
    pushHistory();
    var src = slides[current];
    var blank = document.createElement('div');
    blank.className = 'slide';
    blank.setAttribute('data-slide', '0');
    // Minimal scaffold matching the template
    blank.innerHTML =
      '<div class="slide-header"></div>' +
      '<div class="slide-body" style="padding:160px 120px;display:flex;flex-direction:column;gap:32px;height:100%;box-sizing:border-box">' +
        '<h2 class="content-heading" style="font-size:48px;font-weight:700">New slide</h2>' +
        '<p style="font-size:32px;line-height:1.6;color:#333">Click here to edit body text…</p>' +
      '</div>' +
      '<div class="slide-footer"><span class="page-number">0</span></div>';
    src.parentNode.insertBefore(blank, src.nextSibling);
    refreshSlideRegistry();
    goTo(current + 1);
    refreshEditableForCurrent();
    showToast('已新增空白页');
  }

  function deleteSlide() {
    if (total <= 1) { showToast('至少保留 1 页'); return; }
    if (!confirm('确认删除第 ' + (current + 1) + ' 页？')) return;
    pushHistory();
    var idx = current;
    slides[idx].parentNode.removeChild(slides[idx]);
    refreshSlideRegistry();
    var newIdx = Math.min(idx, total - 1);
    // Force re-activation
    current = -1;
    goTo(newIdx);
    refreshEditableForCurrent();
    showToast('已删除');
  }

  // ── Save edited HTML ────────────────────────────────────────
  // Strategy:
  //   1. Under HTTP (served by tencent-ppt skill's serve.py), POST the cleaned
  //      HTML back via PUT to location.pathname. The Python server handles
  //      atomic write + auto-backup (<name>.YYYYMMDD-HHMMSS.bak.html).
  //      Zero permission prompts — the OS-level server has the FS rights.
  //   2. Anything else (file:// or third-party HTTP server without PUT
  //      support) falls back to download as before.

  var historyStack = [];        // Array<string> — clean HTML snapshots
  var HISTORY_LIMIT = 30;

  // Build a clean HTML snapshot string (no editor UI / contenteditable / state).
  function buildCleanHTML() {
    var cloneDoc = document.documentElement.cloneNode(true);

    var injectIds = [
      'pptControls','pptProgress','pptCounter','pptGalleryOverlay','pptTipOverlay',
      'pptExportOverlay','pptEditToolbar','pptEditSidebar','pptEditBadge','pptToast',
      'pptEditStyles'
    ];
    for (var i = 0; i < injectIds.length; i++) {
      var el = cloneDoc.querySelector('#' + injectIds[i]);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    }
    var styles = cloneDoc.querySelectorAll('style');
    for (var j = 0; j < styles.length; j++) {
      var txt = styles[j].textContent || '';
      if (txt.indexOf('.ppt-progress') !== -1 || txt.indexOf('.ppt-edit-toolbar') !== -1) {
        styles[j].parentNode.removeChild(styles[j]);
      }
    }
    var pb = cloneDoc.querySelector('.ppt-progress');
    if (pb) pb.parentNode.removeChild(pb);

    var clonedSlides = cloneDoc.querySelectorAll('.slide');
    for (var k = 0; k < clonedSlides.length; k++) {
      var s = clonedSlides[k];
      s.style.removeProperty('transform');
      s.style.removeProperty('left');
      s.style.removeProperty('top');
      var eds = s.querySelectorAll('[contenteditable]');
      for (var m = 0; m < eds.length; m++) eds[m].removeAttribute('contenteditable');
      s.classList.remove('active');
    }
    if (clonedSlides[0]) clonedSlides[0].classList.add('active');

    var clonedBody = cloneDoc.querySelector('body');
    if (clonedBody) clonedBody.classList.remove('ppt-editing');

    return '<!DOCTYPE html>\n' + cloneDoc.outerHTML;
  }

  // History snapshot management — capture before each destructive change & save.
  function pushHistory() {
    try {
      var snap = buildCleanHTML();
      if (historyStack.length && historyStack[historyStack.length - 1] === snap) return;
      historyStack.push(snap);
      if (historyStack.length > HISTORY_LIMIT) historyStack.shift();
      updateUndoBtn();
    } catch (e) { console.warn('pushHistory failed', e); }
  }

  function updateUndoBtn() {
    var btn = document.querySelector('#pptEditSidebar [data-action="undo"]');
    if (!btn) return;
    btn.style.opacity = historyStack.length ? '1' : '0.3';
    btn.title = '撤销到上一快照 (' + historyStack.length + ' 步)';
  }

  // Restore the most recent snapshot.
  function undo() {
    if (!historyStack.length) { showToast('没有可撤销的快照'); return; }
    var snap = historyStack.pop();
    try {
      var parser = new DOMParser();
      var snapDoc = parser.parseFromString(snap, 'text/html');
      var newBody = snapDoc.querySelector('body');
      if (!newBody) throw new Error('snapshot missing <body>');

      var keep = [];
      var keepIds = ['pptControls','pptProgress','pptGalleryOverlay','pptTipOverlay',
                     'pptExportOverlay','pptEditToolbar','pptEditSidebar','pptEditBadge',
                     'pptToast'];
      for (var i = 0; i < keepIds.length; i++) {
        var el = document.getElementById(keepIds[i]);
        if (el) keep.push(el);
      }

      document.body.innerHTML = newBody.innerHTML;
      document.body.className = newBody.className + ' ppt-editing';
      for (var k = 0; k < keep.length; k++) document.body.appendChild(keep[k]);

      slides = document.querySelectorAll('.slide');
      total = slides.length;
      current = 0;
      if (slides[0]) {
        for (var s = 0; s < total; s++) slides[s].classList.remove('active');
        slides[0].classList.add('active');
      }
      if (counter) counter.textContent = '1 / ' + total;
      if (progressBar) progressBar.style.width = (1 / total * 100) + '%';
      fitSlide();
      refreshEditableForCurrent();
      updateUndoBtn();
      showToast('已撤销 · 剩 ' + historyStack.length + ' 步');
    } catch (e) {
      console.error('undo failed', e);
      alert('撤销失败：' + e.message);
    }
  }

  function saveDownload(html) {
    var blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    var base = (document.title || 'slides').replace(/[\\/:*?"<>|]/g, '').trim() || 'slides';
    a.href = url;
    a.download = base + '-edited.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    return a.download;
  }

  // PUT to the same path the page was served from. Works against the skill's
  // `serve.py` (or any HTTP server that accepts PUT and writes to disk).
  function savePUT(html) {
    // Resolve the actual file path. If served as /, treat as /index.html.
    var path = location.pathname;
    if (path.endsWith('/')) path += 'index.html';
    return fetch(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
      body: html
    }).then(function (resp) {
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      return path;
    });
  }

  function saveEditedHTML() {
    var html;
    try { html = buildCleanHTML(); }
    catch (err) { console.error('buildCleanHTML failed', err); alert('生成 HTML 失败：' + err.message); return; }

    pushHistory();

    // file:// — browsers can't write back; download.
    if (location.protocol === 'file:') {
      var dl = saveDownload(html);
      showToast('已下载 ' + dl + '（file:// 模式无法原地保存，请改用 serve.py 启动预览）', 4000);
      return;
    }

    // HTTP — try PUT first; fall back to download if server doesn't support it.
    savePUT(html).then(function (path) {
      showToast('已原地保存到 ' + path);
    }).catch(function (err) {
      console.warn('PUT save failed, falling back to download:', err);
      var dl = saveDownload(html);
      showToast('当前 server 不支持原地写入，已下载 ' + dl + '（建议改用 serve.py）', 4000);
    });
  }

  // Wire up the edit button
  var editBtn = document.getElementById('pptEdit');
  if (editBtn) editBtn.addEventListener('click', function () { toggleEdit(); this.blur(); });
})();
