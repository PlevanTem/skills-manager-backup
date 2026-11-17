/* ===== context-visualizer presentation.js =====
   PPT 演示模式控制器 — 键盘/触摸/鼠标翻页 + 进度条 + 缩略图
   仅在 body 包含 presentation-ppt class 时激活
   ================================================= */
(function () {
  'use strict';
  if (!document.body.classList.contains('presentation-ppt')) return;

  // ── 初始化 ──
  const slides = Array.from(document.querySelectorAll('.cv-slide'));
  if (slides.length === 0) return;

  let current = 0;
  const total = slides.length;

  // ── 创建导航 UI ──
  function createNavUI() {
    // 进度条
    const progress = document.createElement('div');
    progress.className = 'cv-ppt-progress';
    progress.innerHTML = '<div class="cv-ppt-progress-fill" id="cvPptProgressFill"></div>';
    document.body.appendChild(progress);

    // 底部导航栏
    const nav = document.createElement('div');
    nav.className = 'cv-ppt-nav';
    nav.id = 'cvPptNav';
    nav.innerHTML = `
      <div class="cv-ppt-nav-left">
        <button class="cv-ppt-nav-btn" id="cvPptPrev" title="上一页 (←)">◀</button>
        <div class="cv-ppt-page-info">
          <span class="cv-ppt-current" id="cvPptCurrent">1</span>
          <span> / ${total}</span>
        </div>
        <button class="cv-ppt-nav-btn" id="cvPptNext" title="下一页 (→)">▶</button>
      </div>
      <div class="cv-ppt-nav-right">
        <button class="cv-ppt-nav-btn" id="cvPptOverviewBtn" title="幻灯片总览 (G)">▦</button>
        <button class="cv-ppt-fullscreen-btn" id="cvPptFullscreen" title="全屏 (F)">⛶</button>
      </div>
    `;
    document.body.appendChild(nav);

    // 缩略图总览面板
    const overview = document.createElement('div');
    overview.className = 'cv-ppt-overview';
    overview.id = 'cvPptOverview';
    let gridHTML = '<div class="cv-ppt-overview-grid">';
    slides.forEach(function (slide, i) {
      const title = getSlideTitle(slide);
      const isCurrent = i === current ? ' cv-ppt-overview-current' : '';
      gridHTML += `
        <div class="cv-ppt-overview-item${isCurrent}" data-slide="${i}">
          <span class="cv-ppt-overview-label">${i + 1}</span>
          <div class="cv-ppt-overview-title">${title}</div>
        </div>`;
    });
    gridHTML += '</div>';
    overview.innerHTML = gridHTML;
    document.body.appendChild(overview);

    // 自动隐藏导航栏（3s 无操作后半透明）
    let hideTimer;
    function resetHideTimer() {
      nav.style.opacity = '1';
      clearTimeout(hideTimer);
      hideTimer = setTimeout(function () {
        nav.style.opacity = '0.3';
      }, 3000);
    }
    document.addEventListener('mousemove', resetHideTimer);
    document.addEventListener('touchstart', resetHideTimer);
    resetHideTimer();
  }

  function getSlideTitle(slide) {
    var el = slide.querySelector('.cv-slide-title, .cv-slide-header h2, h2, h1');
    return el ? el.textContent.trim() : '幻灯片';
  }

  // ── 切换幻灯片 ──
  function goToSlide(index) {
    if (index < 0 || index >= total) return;
    var prev = current;
    current = index;

    slides.forEach(function (slide, i) {
      slide.classList.remove('cv-slide-active', 'cv-slide-prev');
      if (i === current) {
        slide.classList.add('cv-slide-active');
      } else if (i < current) {
        slide.classList.add('cv-slide-prev');
      }
    });

    // 更新进度条
    var fill = document.getElementById('cvPptProgressFill');
    if (fill) {
      fill.style.width = ((current + 1) / total * 100) + '%';
    }

    // 更新页码
    var pageNum = document.getElementById('cvPptCurrent');
    if (pageNum) {
      pageNum.textContent = current + 1;
    }

    // 更新按钮禁用状态
    var prevBtn = document.getElementById('cvPptPrev');
    var nextBtn = document.getElementById('cvPptNext');
    if (prevBtn) prevBtn.disabled = current === 0;
    if (nextBtn) nextBtn.disabled = current === total - 1;

    // 更新缩略图总览中的当前标记
    var overviewItems = document.querySelectorAll('.cv-ppt-overview-item');
    overviewItems.forEach(function (item, i) {
      item.classList.toggle('cv-ppt-overview-current', i === current);
    });

    // 滚回顶部（幻灯片内的滚动）
    slides[current].scrollTop = 0;
  }

  function nextSlide() { goToSlide(current + 1); }
  function prevSlide() { goToSlide(current - 1); }
  function firstSlide() { goToSlide(0); }
  function lastSlide() { goToSlide(total - 1); }

  // ── 缩略图总览 ──
  function toggleOverview() {
    var panel = document.getElementById('cvPptOverview');
    if (panel) {
      panel.classList.toggle('cv-ppt-overview-open');
    }
  }
  function closeOverview() {
    var panel = document.getElementById('cvPptOverview');
    if (panel) {
      panel.classList.remove('cv-ppt-overview-open');
    }
  }

  // ── 全屏 ──
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(function () {});
    } else {
      document.exitFullscreen();
    }
  }

  // ── 键盘事件 ──
  document.addEventListener('keydown', function (e) {
    // 如果缩略图面板打开
    var overviewOpen = document.querySelector('.cv-ppt-overview-open');
    if (overviewOpen) {
      if (e.key === 'Escape' || e.key === 'g' || e.key === 'G') {
        closeOverview();
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
      case ' ':
      case 'PageDown':
        e.preventDefault();
        nextSlide();
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
      case 'PageUp':
        e.preventDefault();
        prevSlide();
        break;
      case 'Home':
        e.preventDefault();
        firstSlide();
        break;
      case 'End':
        e.preventDefault();
        lastSlide();
        break;
      case 'f':
      case 'F':
        e.preventDefault();
        toggleFullscreen();
        break;
      case 'g':
      case 'G':
        e.preventDefault();
        toggleOverview();
        break;
      case 'Escape':
        e.preventDefault();
        if (document.fullscreenElement) {
          document.exitFullscreen();
        }
        break;
    }
  });

  // ── 触摸滑动 ──
  var touchStartX = 0;
  var touchStartY = 0;
  document.addEventListener('touchstart', function (e) {
    touchStartX = e.changedTouches[0].clientX;
    touchStartY = e.changedTouches[0].clientY;
  }, { passive: true });

  document.addEventListener('touchend', function (e) {
    var dx = e.changedTouches[0].clientX - touchStartX;
    var dy = e.changedTouches[0].clientY - touchStartY;
    // 水平滑动距离大于 50px 且大于垂直距离
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
      if (dx < 0) nextSlide();
      else prevSlide();
    }
  }, { passive: true });

  // ── 鼠标滚轮（可选，仅在非内容溢出时翻页）──
  var wheelTimer;
  document.addEventListener('wheel', function (e) {
    // 如果当前幻灯片内容可滚动，不拦截
    var activeSlide = slides[current];
    if (activeSlide && activeSlide.scrollHeight > activeSlide.clientHeight + 10) {
      return;
    }
    clearTimeout(wheelTimer);
    wheelTimer = setTimeout(function () {
      if (e.deltaY > 0) nextSlide();
      else if (e.deltaY < 0) prevSlide();
    }, 80);
  }, { passive: true });

  // ── 点击事件 ──
  document.addEventListener('click', function (e) {
    // 导航按钮
    var target = e.target.closest('[id]');
    if (!target) return;
    switch (target.id) {
      case 'cvPptPrev': prevSlide(); break;
      case 'cvPptNext': nextSlide(); break;
      case 'cvPptOverviewBtn': toggleOverview(); break;
      case 'cvPptFullscreen': toggleFullscreen(); break;
    }

    // 缩略图总览点击
    var overviewItem = e.target.closest('.cv-ppt-overview-item');
    if (overviewItem) {
      var slideIndex = parseInt(overviewItem.dataset.slide, 10);
      goToSlide(slideIndex);
      closeOverview();
    }
  });

  // ── 初始化 ──
  createNavUI();
  goToSlide(0);
})();
