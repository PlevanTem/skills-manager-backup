/* ===== context-visualizer interactive.js =====
   轻量交互组件 — Tab / 折叠 / 表格排序
   仅在页面包含对应组件时自动激活，无外部依赖
   ================================================= */
(function () {
  'use strict';

  // ══════════════════════════════════════════════════
  // Tab 切换组件
  // HTML 结构:
  //   <div class="cv-tabs">
  //     <div class="cv-tab-nav">
  //       <button class="cv-tab-btn cv-tab-btn-active" data-tab="tab1">标签1</button>
  //       <button class="cv-tab-btn" data-tab="tab2">标签2</button>
  //     </div>
  //     <div class="cv-tab-panel cv-tab-panel-active" data-tab-id="tab1" data-tab-label="标签1">内容1</div>
  //     <div class="cv-tab-panel" data-tab-id="tab2" data-tab-label="标签2">内容2</div>
  //   </div>
  // ══════════════════════════════════════════════════
  function initTabs() {
    var tabContainers = document.querySelectorAll('.cv-tabs');
    tabContainers.forEach(function (container) {
      var buttons = container.querySelectorAll('.cv-tab-btn');
      var panels = container.querySelectorAll('.cv-tab-panel');

      buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          var targetId = btn.getAttribute('data-tab');

          // 切换按钮激活状态
          buttons.forEach(function (b) { b.classList.remove('cv-tab-btn-active'); });
          btn.classList.add('cv-tab-btn-active');

          // 切换面板显示
          panels.forEach(function (p) {
            if (p.getAttribute('data-tab-id') === targetId) {
              p.classList.add('cv-tab-panel-active');
            } else {
              p.classList.remove('cv-tab-panel-active');
            }
          });
        });
      });
    });
  }

  // ══════════════════════════════════════════════════
  // 折叠面板组件
  // HTML 结构:
  //   <div class="cv-collapse">
  //     <div class="cv-collapse-trigger">
  //       <span class="cv-collapse-title">标题</span>
  //       <span class="cv-collapse-icon">▸</span>
  //     </div>
  //     <div class="cv-collapse-body">折叠内容</div>
  //   </div>
  // ══════════════════════════════════════════════════
  function initCollapse() {
    var triggers = document.querySelectorAll('.cv-collapse-trigger');
    triggers.forEach(function (trigger) {
      trigger.addEventListener('click', function () {
        var collapse = trigger.closest('.cv-collapse');
        if (collapse) {
          collapse.classList.toggle('cv-collapse-open');
          var body = collapse.querySelector('.cv-collapse-body');
          if (body) {
            if (collapse.classList.contains('cv-collapse-open')) {
              body.style.maxHeight = body.scrollHeight + 'px';
            } else {
              body.style.maxHeight = '0';
            }
          }
        }
      });
    });

    // 默认展开带 .cv-collapse-open 的
    document.querySelectorAll('.cv-collapse.cv-collapse-open').forEach(function (c) {
      var body = c.querySelector('.cv-collapse-body');
      if (body) body.style.maxHeight = body.scrollHeight + 'px';
    });
  }

  // ══════════════════════════════════════════════════
  // 表格排序组件
  // 在 <th> 上添加 class="cv-table-sortable" 即可启用
  // HTML 结构:
  //   <table class="cv-table">
  //     <thead>
  //       <tr>
  //         <th class="cv-table-sortable">名称</th>
  //         <th class="cv-table-sortable" data-sort-type="number">数值</th>
  //       </tr>
  //     </thead>
  //     ...
  //   </table>
  // ══════════════════════════════════════════════════
  function initTableSort() {
    var sortableHeaders = document.querySelectorAll('.cv-table-sortable');
    sortableHeaders.forEach(function (th) {
      // 添加排序图标
      if (!th.querySelector('.cv-sort-icon')) {
        var icon = document.createElement('span');
        icon.className = 'cv-sort-icon';
        icon.textContent = ' ↕';
        th.appendChild(icon);
      }
      th.style.cursor = 'pointer';
      th.style.userSelect = 'none';

      th.addEventListener('click', function () {
        var table = th.closest('table');
        if (!table) return;
        var tbody = table.querySelector('tbody');
        if (!tbody) return;

        var colIndex = Array.from(th.parentNode.children).indexOf(th);
        var sortType = th.getAttribute('data-sort-type') || 'string';
        var currentDir = th.getAttribute('data-sort-dir') || 'none';
        var newDir = currentDir === 'asc' ? 'desc' : 'asc';

        // 清除其他列的排序状态
        var allHeaders = table.querySelectorAll('.cv-table-sortable');
        allHeaders.forEach(function (h) {
          h.setAttribute('data-sort-dir', 'none');
          h.classList.remove('cv-sort-asc', 'cv-sort-desc');
          var ic = h.querySelector('.cv-sort-icon');
          if (ic) ic.textContent = ' ↕';
        });

        // 设置当前列排序
        th.setAttribute('data-sort-dir', newDir);
        th.classList.add(newDir === 'asc' ? 'cv-sort-asc' : 'cv-sort-desc');
        var sortIcon = th.querySelector('.cv-sort-icon');
        if (sortIcon) sortIcon.textContent = newDir === 'asc' ? ' ↑' : ' ↓';

        // 排序行
        var rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort(function (a, b) {
          var aCell = a.children[colIndex];
          var bCell = b.children[colIndex];
          if (!aCell || !bCell) return 0;
          var aText = aCell.textContent.trim();
          var bText = bCell.textContent.trim();

          if (sortType === 'number') {
            var aNum = parseFloat(aText.replace(/[^0-9.\-]/g, '')) || 0;
            var bNum = parseFloat(bText.replace(/[^0-9.\-]/g, '')) || 0;
            return newDir === 'asc' ? aNum - bNum : bNum - aNum;
          } else {
            var cmp = aText.localeCompare(bText, 'zh-CN');
            return newDir === 'asc' ? cmp : -cmp;
          }
        });

        // 重新插入
        rows.forEach(function (row) { tbody.appendChild(row); });
      });
    });
  }

  // ══════════════════════════════════════════════════
  // 手风琴组件（互斥折叠）
  // HTML: <div class="cv-accordion">
  //         <div class="cv-collapse">...</div>
  //         <div class="cv-collapse">...</div>
  //       </div>
  // ══════════════════════════════════════════════════
  function initAccordion() {
    var accordions = document.querySelectorAll('.cv-accordion');
    accordions.forEach(function (accordion) {
      accordion.addEventListener('click', function (e) {
        var trigger = e.target.closest('.cv-collapse-trigger');
        if (!trigger) return;
        var currentCollapse = trigger.closest('.cv-collapse');
        var collapses = accordion.querySelectorAll('.cv-collapse');
        collapses.forEach(function (c) {
          if (c !== currentCollapse && c.classList.contains('cv-collapse-open')) {
            c.classList.remove('cv-collapse-open');
            var body = c.querySelector('.cv-collapse-body');
            if (body) body.style.maxHeight = '0';
          }
        });
      });
    });
  }

  // ══════════════════════════════════════════════════
  // 左侧导航栏组件 (Side TOC)
  // 自动从页面 section 的 h2/h3 标题生成目录
  // 默认收起，点击汉堡按钮展开
  // ══════════════════════════════════════════════════
  function initSideToc() {
    // PPT 模式不启用导航栏
    if (document.body.classList.contains('presentation-ppt')) return;
    // 如果页面已有手动创建的 TOC，不重复创建
    if (document.querySelector('.cv-toc-panel')) return;

    // 收集所有 section 的标题
    var sections = document.querySelectorAll('.cv-section[id], .cv-hero-card[id], .cv-hero[id]');
    var headings = [];

    // 优先从带 id 的 section 里找 h2/h3
    sections.forEach(function (sec) {
      var h = sec.querySelector('h2, h3, .cv-section-head h2, .cv-section-head h3');
      if (h) {
        headings.push({
          id: sec.id,
          text: h.textContent.trim(),
          level: h.tagName === 'H3' ? 3 : 2,
          el: sec
        });
      }
    });

    // 如果 section 不够，尝试直接找 .cv-page 下的 h2/h3
    if (headings.length < 2) {
      headings = [];
      var page = document.querySelector('.cv-page');
      if (!page) return;
      var allHeadings = page.querySelectorAll('h2, h3');
      allHeadings.forEach(function (h, i) {
        var section = h.closest('.cv-section') || h.closest('section');
        var targetId = '';
        if (section && section.id) {
          targetId = section.id;
        } else if (h.id) {
          targetId = h.id;
        } else {
          targetId = 'cv-toc-heading-' + i;
          h.id = targetId;
        }
        headings.push({
          id: targetId,
          text: h.textContent.trim(),
          level: h.tagName === 'H3' ? 3 : 2,
          el: section || h
        });
      });
    }

    // 少于 2 个标题时不显示导航
    if (headings.length < 2) return;

    // 创建汉堡按钮
    var toggleBtn = document.createElement('button');
    toggleBtn.className = 'cv-toc-toggle';
    toggleBtn.setAttribute('aria-label', '目录导航');
    toggleBtn.setAttribute('title', '目录导航');
    toggleBtn.innerHTML = '<svg viewBox="0 0 24 24"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    document.body.appendChild(toggleBtn);

    // 创建遮罩
    var overlay = document.createElement('div');
    overlay.className = 'cv-toc-overlay';
    document.body.appendChild(overlay);

    // 创建面板
    var panel = document.createElement('div');
    panel.className = 'cv-toc-panel';

    // 头部
    var header = document.createElement('div');
    header.className = 'cv-toc-header';
    header.innerHTML = '<span class="cv-toc-header-title">📑 目录</span>';
    var closeBtn = document.createElement('button');
    closeBtn.className = 'cv-toc-close';
    closeBtn.setAttribute('aria-label', '关闭目录');
    closeBtn.innerHTML = '<svg viewBox="0 0 24 24"><line x1="6" y1="6" x2="18" y2="18"/><line x1="6" y1="18" x2="18" y2="6"/></svg>';
    header.appendChild(closeBtn);
    panel.appendChild(header);

    // 列表
    var list = document.createElement('div');
    list.className = 'cv-toc-list';
    headings.forEach(function (h) {
      var item = document.createElement('a');
      item.className = 'cv-toc-item';
      item.href = '#' + h.id;
      item.textContent = h.text;
      item.setAttribute('data-toc-level', h.level);
      item.setAttribute('data-toc-target', h.id);
      list.appendChild(item);
    });
    panel.appendChild(list);
    document.body.appendChild(panel);

    // 开/关函数
    function openToc() {
      panel.classList.add('cv-toc-open');
      overlay.classList.add('cv-toc-overlay-show');
    }
    function closeToc() {
      panel.classList.remove('cv-toc-open');
      overlay.classList.remove('cv-toc-overlay-show');
    }

    // 事件绑定
    toggleBtn.addEventListener('click', function () {
      if (panel.classList.contains('cv-toc-open')) {
        closeToc();
      } else {
        openToc();
      }
    });
    closeBtn.addEventListener('click', closeToc);
    overlay.addEventListener('click', closeToc);

    // 点击条目：跳转 + 关闭导航栏
    list.addEventListener('click', function (e) {
      var item = e.target.closest('.cv-toc-item');
      if (!item) return;
      e.preventDefault();
      var targetId = item.getAttribute('data-toc-target');
      var target = document.getElementById(targetId);
      if (target) {
        closeToc();
        // 延迟滚动让面板先收起
        setTimeout(function () {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    });

    // ESC 关闭
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && panel.classList.contains('cv-toc-open')) {
        closeToc();
      }
    });

    // 滚动高亮当前章节
    var tocItems = list.querySelectorAll('.cv-toc-item');
    var scrollTimer = null;
    function updateActiveItem() {
      var scrollTop = window.scrollY || document.documentElement.scrollTop;
      var current = null;
      headings.forEach(function (h) {
        var el = document.getElementById(h.id);
        if (el) {
          var rect = el.getBoundingClientRect();
          if (rect.top <= 120) {
            current = h.id;
          }
        }
      });
      tocItems.forEach(function (item) {
        if (item.getAttribute('data-toc-target') === current) {
          item.classList.add('cv-toc-active');
        } else {
          item.classList.remove('cv-toc-active');
        }
      });
    }
    window.addEventListener('scroll', function () {
      if (scrollTimer) clearTimeout(scrollTimer);
      scrollTimer = setTimeout(updateActiveItem, 60);
    }, { passive: true });
    // 初始化一次
    updateActiveItem();
  }

  // ══════════════════════════════════════════════════
  // 初始化所有组件
  // ══════════════════════════════════════════════════
  function init() {
    initTabs();
    initCollapse();
    initTableSort();
    initAccordion();
    initSideToc();
  }

  // DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
