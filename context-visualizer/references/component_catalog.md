# Context Visualizer — 组件参考手册

> AI 在生成 HTML 页面时查阅此手册，选择合适的组件来表达内容。
> 所有组件使用 CSS 变量，支持 light/dark 主题自动切换。

---

## 页面骨架

完整单文件 HTML 骨架：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ page_title }}</title>
  <style>
    /* 1. 主题 CSS 变量 */
    :root { --bg: #f6f8fb; --panel: #ffffff; --text: #1a1a2e; ... }
    /* 2. 品牌定制变量（可选） */
    /* :root { --brand-name: "TNIC"; --brand-color: #2563eb; } */
    /* 3. 内嵌 assets/base.css 内容 */
    /* 4. 内嵌 assets/components.css 内容 */
    /* 5. 如需打印支持：内嵌 assets/print.css */
  </style>
</head>
<body class="{{ body_class }}">
  <header class="cv-topbar">
    <div class="cv-topbar-inner">
      <div class="cv-brand">Context Visualizer</div>
      <!-- ⚠️ 不放 <nav class="cv-nav"> — 章节导航由左侧导航栏(Side TOC)自动生成 -->
    </div>
  </header>
  <div class="cv-page">
    <!-- AI 自由构建内容 -->
  </div>
  <footer class="cv-footer">
    <div class="cv-footer-card">Generated from source data.</div>
  </footer>
  <!-- 如果使用 mermaid -->
  <!-- ⚠️ 安全基线：securityLevel 必须为 'sandbox'，htmlLabels 必须为 false，严禁下调为 'loose' 或 'antiscript' -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({
      startOnLoad: true,
      theme: 'neutral',
      securityLevel: 'sandbox',
      htmlLabels: false,
      flowchart: { htmlLabels: false },
      sequence: { htmlLabels: false },
      class: { htmlLabels: false }
    });
  </script>
  <!-- 如果使用 Tab/折叠/表格排序等交互组件（也负责自动生成左侧导航栏） -->
  <script>/* 内嵌 assets/interactive.js */</script>
  <!-- 如果使用 Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
</body>
</html>
```

**body_class 规则**：
- 白底主题: `theme-default-light`
- 深色主题: `theme-dark-screen`
- PPT 模式追加: `presentation-ppt`
- 品牌定制追加: `cv-brand-custom`
- 示例: `class="theme-dark-screen presentation-ppt cv-brand-custom"`

---

## Hero 区

页面顶部的大标题区域。

```html
<!-- 带侧边栏的 Hero -->
<section class="cv-hero">
  <article class="cv-hero-card">
    <span class="cv-badge">内部汇报 · 结论型</span>
    <div class="cv-kicker">面向技术负责人的项目进展同步</div>
    <h1 class="cv-title">MEP SDK 重构阶段总结</h1>
    <p class="cv-subtitle">2026 Q1 第二轮重构完成度 85%</p>
    <div class="cv-summary-box">
      <ul>
        <li>核心 API 已完成迁移</li>
        <li>性能测试通过率 98%</li>
      </ul>
    </div>
    <div class="cv-meta-row">
      <span class="cv-chip">houxiangcai</span>
      <span class="cv-chip">2026-03-27</span>
      <span class="cv-chip">#MEP</span>
    </div>
  </article>
  <div class="cv-side-stack">
    <!-- 侧边卡片放这里 -->
  </div>
</section>
```

---

## 内容卡片 (Section)

主要内容分区，每个 `##` 章节一个卡片。

```html
<main class="cv-content">
  <section id="background" class="cv-section">
    <div class="cv-section-head">
      <h2>背景与问题</h2>
      <p>为什么需要这次重构</p>
    </div>
    <div class="cv-section-body">
      <p>原有 SDK 存在以下问题：</p>
      <ul>
        <li>API 不一致，新人上手成本高</li>
      </ul>
    </div>
  </section>
</main>
```

---

## 代码块

展示代码、配置、命令行输出。支持语言标签和文件名。

```html
<div class="cv-code-block">
  <div class="cv-code-header">
    <span class="cv-code-lang">C</span>
    <span class="cv-code-filename">mep_sdk/session.c</span>
  </div>
  <pre><code>int jnet_session_tbl_add(struct session_entry *entry) {
    if (!entry) return JNET_ERR_PARAM;
    return do_session_add(entry);
}</code></pre>
</div>
```

---

## 数据表格

结构化数据展示。支持紧凑模式、条纹模式和排序。

```html
<!-- 标准表格 -->
<div class="cv-table-wrap">
  <table class="cv-table">
    <thead>
      <tr>
        <th class="cv-table-sortable">表项类型</th>
        <th class="cv-table-sortable" data-sort-type="number">容量</th>
        <th>API</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Session 表</td>
        <td>可配</td>
        <td><code>jnet_session_tbl_add</code></td>
      </tr>
    </tbody>
  </table>
</div>
```

**排序功能**：在 `<th>` 上加 `class="cv-table-sortable"` 即可，数字列加 `data-sort-type="number"`。需要内嵌 `interactive.js`。

---

## 时间线

按时间顺序展示事件、调试步骤、项目里程碑。

```html
<div class="cv-timeline">
  <div class="cv-timeline-item">
    <div class="cv-timeline-dot"></div>
    <div class="cv-timeline-time">2026-03-20 14:00</div>
    <div class="cv-timeline-title">发现丢包现象</div>
    <div class="cv-timeline-desc">RX 方向 cathaya 诊断显示 drop 不为零</div>
  </div>
  <div class="cv-timeline-item">
    <div class="cv-timeline-dot cv-timeline-dot-success"></div>
    <div class="cv-timeline-time">2026-03-20 17:00</div>
    <div class="cv-timeline-title">问题修复</div>
    <div class="cv-timeline-desc">调整配置后恢复</div>
  </div>
</div>
```

**Dot 颜色变体**: `.cv-timeline-dot-success` / `-warning` / `-danger` / `-muted`

---

## Mermaid 图表

```html
<div class="cv-mermaid">
  <div class="cv-mermaid-title">报文转发路径</div>
  <div class="mermaid">
graph LR
    A[MACIF RX] --> B[PAE 解析]
    B --> C[PIPE 查表]
    C --> D{命中?}
    D -->|Yes| E[PKE 编辑]
    D -->|No| F[送 MEP]
  </div>
</div>
```

### ⚠️ 安全配置要求（必读）

Mermaid 存在 XSS 风险，AI 生成的所有含 Mermaid 的页面必须满足：

1. **`securityLevel: 'sandbox'`**（最低 `'strict'`）— 严禁使用 `'loose'` 或 `'antiscript'`。sandbox 模式会把 Mermaid 渲染结果放入 iframe，阻断脚本执行。
2. **`htmlLabels: false`** — 全局和各子图（flowchart/sequence/class）均需关闭 HTML 标签，防止通过 label 注入 `<img onerror>` 等向量。
3. **禁止将用户自由输入直接拼接到 `.mermaid` 容器**。若确有需要，先用 DOMPurify 清洗。静态模板写死的 Mermaid 源码不受此限。

正确初始化代码已包含在上方的"页面骨架"示例中，请勿随意修改。

---

## 可视化架构图 (Architecture Visual) 🆕

**⚠️ 技术文档插图场景的默认方式**。使用 CSS 彩色块 + 箭头 + Grid 布局绘制，替代 ASCII 文本图。
仅当用户明确要求"保持 ASCII"时，才回退到 `.arch-diagram` 等宽字体方式。

```html
<div class="cv-arch-visual">
  <div class="cv-arch-visual-title">CME Thread Buffer Layout</div>
  <div class="cv-arch-container">
    <!-- 输入数据源 -->
    <div class="cv-arch-group">
      <span class="cv-arch-group-label">PIPE → MEP 送入数据</span>
      <div class="cv-arch-group-content">
        <div class="cv-arch-box cv-arch-box-primary">
          <div class="cv-arch-box-title">Packet Header</div>
          <div class="cv-arch-box-desc">256 Byte · 报文头 cell</div>
        </div>
        <div class="cv-arch-box cv-arch-box-success">
          <div class="cv-arch-box-title">pipe_mep_meta</div>
          <div class="cv-arch-box-desc">64 Byte · PAE 解析结果</div>
        </div>
        <div class="cv-arch-box cv-arch-box-warning">
          <div class="cv-arch-box-title">pipe_mep_result</div>
          <div class="cv-arch-box-desc">32 Byte · PIPE 查表结果</div>
          <span class="cv-arch-box-badge">256bit</span>
        </div>
      </div>
    </div>

    <!-- 箭头 -->
    <div class="cv-arch-arrow cv-arch-arrow-down">
      <span class="cv-arch-arrow-label">填入 Input Buffers</span>
    </div>

    <!-- Input Buffers -->
    <div class="cv-arch-row">
      <div class="cv-arch-box cv-arch-box-primary">
        <div class="cv-arch-box-title">PB (256B)</div>
        <div class="cv-arch-box-desc">Packet Buffer · 只读</div>
      </div>
      <div class="cv-arch-box cv-arch-box-success">
        <div class="cv-arch-box-title">MB (96B)</div>
        <div class="cv-arch-box-desc">Meta Buffer · 只读</div>
      </div>
    </div>

    <!-- 箭头 -->
    <div class="cv-arch-arrow cv-arch-arrow-down">
      <span class="cv-arch-arrow-label">CME 微码处理</span>
    </div>

    <!-- Output Buffers -->
    <div class="cv-arch-row">
      <div class="cv-arch-box cv-arch-box-danger">
        <div class="cv-arch-box-title">NHB (384B)</div>
        <div class="cv-arch-box-desc">New Head · 可写</div>
      </div>
      <div class="cv-arch-box cv-arch-box-danger">
        <div class="cv-arch-box-title">NMB (96B)</div>
        <div class="cv-arch-box-desc">New Meta · 可写</div>
      </div>
      <div class="cv-arch-box cv-arch-box-muted">
        <div class="cv-arch-box-title">KB</div>
        <div class="cv-arch-box-desc">Key Buffer · 查表用</div>
      </div>
    </div>
  </div>
</div>
```

**块颜色变体**：
- 默认 `.cv-arch-box-primary`（蓝色）
- `.cv-arch-box-success`（绿色）/ `-warning`（黄色）/ `-danger`（红色）
- `.cv-arch-box-muted`（灰色虚线）/ `.cv-arch-box-dark`（深色实底）

**箭头变体**：`.cv-arch-arrow-down` / `-right` / `-left` / `-bidir`

---

## 可视化流程图 (Flow Visual) 🆕

使用 CSS 节点 + 连接线绘制流程图。适合简单的线性流程。复杂分支建议用 Mermaid。

```html
<div class="cv-flow-visual">
  <div class="cv-flow-visual-title">报文处理流程</div>
  <div class="cv-flow-container">
    <div class="cv-flow-node cv-flow-node-start">RX 接收</div>
    <div class="cv-flow-connector"></div>
    <div class="cv-flow-node cv-flow-node-process">PAE 解析</div>
    <div class="cv-flow-connector"></div>
    <div class="cv-flow-node cv-flow-node-process">PIPE 查表</div>
    <div class="cv-flow-connector"></div>
    <div class="cv-flow-node" style="border-color:var(--warning);background:rgba(183,121,31,.08)">MEP 处理</div>
    <div class="cv-flow-connector"></div>
    <div class="cv-flow-node cv-flow-node-end">TX 发送</div>
  </div>
</div>

<!-- 垂直流程 -->
<div class="cv-flow-visual">
  <div class="cv-flow-container cv-flow-container-vertical">
    <div class="cv-flow-node cv-flow-node-start">开始</div>
    <div class="cv-flow-connector"></div>
    <div class="cv-flow-node cv-flow-node-process">步骤 1</div>
    <div class="cv-flow-connector"></div>
    <div class="cv-flow-node cv-flow-node-process">步骤 2</div>
    <div class="cv-flow-connector"></div>
    <div class="cv-flow-node cv-flow-node-end">结束</div>
  </div>
</div>
```

---

## 数据结构可视化 (Struct Visual) 🆕

展示内存布局、寄存器域段、数据包结构等。

### 内存条形式

```html
<div class="cv-struct-visual">
  <div class="cv-struct-visual-title">Meta Buffer 96 Byte 内存映射</div>
  <div class="cv-struct-bar">
    <div class="cv-struct-field cv-struct-field-primary" style="flex:64">
      <span class="cv-struct-field-name">pipe_mep_meta</span>
      <span class="cv-struct-field-bits">64 Byte / 512 bit</span>
      <span class="cv-struct-field-offset">offset 0</span>
    </div>
    <div class="cv-struct-field cv-struct-field-warning" style="flex:32">
      <span class="cv-struct-field-name">pipe_mep_result</span>
      <span class="cv-struct-field-bits">32 Byte / 256 bit</span>
      <span class="cv-struct-field-offset">offset 512</span>
    </div>
  </div>
</div>
```

### 结构体卡片形式

```html
<div class="cv-struct-visual">
  <div class="cv-struct-visual-title">pipe_mep_meta 关键域段</div>
  <div class="cv-struct-card">
    <div class="cv-struct-card-header">
      <code>struct pipe_mep_meta</code> · 64 Byte
    </div>
    <div class="cv-struct-card-body">
      <div class="cv-struct-card-row">
        <span class="cv-struct-card-field">src_type</span>
        <span class="cv-struct-card-type">2 bit</span>
        <span class="cv-struct-card-desc">TX: 0=VPE, 1=RPE, 2=Loopback</span>
      </div>
      <div class="cv-struct-card-row">
        <span class="cv-struct-card-field">src_vif</span>
        <span class="cv-struct-card-type">14 bit</span>
        <span class="cv-struct-card-desc">源 VIF，全局编址</span>
      </div>
      <div class="cv-struct-card-row">
        <span class="cv-struct-card-field">pkt_len</span>
        <span class="cv-struct-card-type">14 bit</span>
        <span class="cv-struct-card-desc">报文长度</span>
      </div>
    </div>
  </div>
</div>
```

**域段颜色**：`.cv-struct-field-primary` / `-success` / `-warning` / `-danger` / `-muted`

---

## 层叠展示 (Layer Stack) 🆕

展示协议层次、软件栈、架构分层等。

```html
<div class="cv-layer-stack">
  <div class="cv-layer-item cv-layer-item-l1">
    应用层 (Application)
    <div class="cv-layer-item-desc">TCP/UDP 报文收发</div>
  </div>
  <div class="cv-layer-item cv-layer-item-l2">
    MEP 处理层 (Microcode Engine)
    <div class="cv-layer-item-desc">CME 微码运行，查表 + 编辑</div>
  </div>
  <div class="cv-layer-item cv-layer-item-l3">
    PIPE 查表层 (Pipeline)
    <div class="cv-layer-item-desc">4 级子 PIPE，classify → profile → EM → WC</div>
  </div>
  <div class="cv-layer-item cv-layer-item-l4">
    PAE 解析层 (Parser Engine)
    <div class="cv-layer-item-desc">P4-like 报文解析，提取 256 byte 报文头</div>
  </div>
  <div class="cv-layer-item cv-layer-item-l5">
    MAC 接口层 (MACIF)
    <div class="cv-layer-item-desc">RX 方向报文接收，PB 写入和优先级调度</div>
  </div>
</div>
```

**层颜色**：`.cv-layer-item-l1` ~ `.cv-layer-item-l6`（蓝/绿/黄/红/紫/灰）

---

## 图例 (Legend) 🆕

配合可视化图表使用，解释颜色含义。

```html
<div class="cv-legend">
  <div class="cv-legend-item">
    <span class="cv-legend-dot" style="background:var(--accent)"></span>
    Input Buffer（只读）
  </div>
  <div class="cv-legend-item">
    <span class="cv-legend-dot" style="background:var(--danger)"></span>
    Output Buffer（可写）
  </div>
  <div class="cv-legend-item">
    <span class="cv-legend-dot" style="background:var(--muted)"></span>
    辅助 Buffer
  </div>
</div>
```

---

## 指标行 / 数据卡片

```html
<div class="cv-metric-row">
  <div class="cv-metric-card">
    <div class="cv-metric-value">98%</div>
    <div class="cv-metric-label">测试通过率</div>
    <div class="cv-metric-sub">共 1,234 个用例</div>
  </div>
  <div class="cv-metric-card">
    <div class="cv-metric-value cv-metric-value-success">0</div>
    <div class="cv-metric-label">丢包数</div>
  </div>
</div>
```

---

## 对比表格

```html
<div class="cv-comparison">
  <div class="cv-comparison-col cv-comparison-before">
    <div class="cv-comparison-header">改造前</div>
    <ul>
      <li>旧方案描述</li>
    </ul>
  </div>
  <div class="cv-comparison-col cv-comparison-after">
    <div class="cv-comparison-header">改造后</div>
    <ul>
      <li>新方案描述</li>
    </ul>
  </div>
</div>
```

---

## 步骤列表

```html
<div class="cv-steps">
  <div class="cv-step">
    <div class="cv-step-num cv-step-num-done">1</div>
    <div class="cv-step-content">
      <div class="cv-step-title">准备环境</div>
      <div class="cv-step-desc">确认 Docker 容器运行正常</div>
    </div>
  </div>
</div>
```

**编号变体**: `.cv-step-num`(蓝) / `.cv-step-num-done`(绿) / `.cv-step-num-pending`(灰)

---

## Callout 强调框

```html
<div class="cv-callout cv-callout-info">
  <div class="cv-callout-title">💡 提示</div>
  提示内容
</div>
<div class="cv-callout cv-callout-success">...</div>
<div class="cv-callout cv-callout-warning">...</div>
<div class="cv-callout cv-callout-danger">...</div>
```

---

## 甘特图 🆕

展示项目里程碑、任务排期。通过 CSS Grid + 绝对定位实现，不依赖外部库。

```html
<div class="cv-gantt">
  <div class="cv-gantt-title">Q1 里程碑排期</div>
  <!-- 头部时间轴 -->
  <div class="cv-gantt-header" style="grid-template-columns: 120px repeat(12, 1fr);">
    <span></span>
    <span>W1</span><span>W2</span><span>W3</span><span>W4</span>
    <span>W5</span><span>W6</span><span>W7</span><span>W8</span>
    <span>W9</span><span>W10</span><span>W11</span><span>W12</span>
  </div>
  <!-- 数据行 -->
  <div class="cv-gantt-row" style="grid-template-columns: 120px 1fr;">
    <div class="cv-gantt-label">需求分析</div>
    <div class="cv-gantt-track">
      <div class="cv-gantt-bar cv-gantt-bar-success" style="left: 0%; width: 25%;">W1-W3</div>
    </div>
  </div>
  <div class="cv-gantt-row" style="grid-template-columns: 120px 1fr;">
    <div class="cv-gantt-label">开发实现</div>
    <div class="cv-gantt-track">
      <div class="cv-gantt-bar" style="left: 20%; width: 50%;">W3-W9</div>
    </div>
  </div>
  <div class="cv-gantt-row" style="grid-template-columns: 120px 1fr;">
    <div class="cv-gantt-label">测试验证</div>
    <div class="cv-gantt-track">
      <div class="cv-gantt-bar cv-gantt-bar-warning" style="left: 65%; width: 25%;">W8-W11</div>
    </div>
  </div>
</div>
```

**Bar 颜色变体**: 默认蓝 / `.cv-gantt-bar-success`(绿) / `-warning`(黄) / `-danger`(红) / `-muted`(灰)

---

## 看板 (Kanban Board) 🆕

任务看板，按状态分列展示卡片。

```html
<div class="cv-kanban">
  <!-- Todo 列 -->
  <div class="cv-kanban-column cv-kanban-column-todo">
    <div class="cv-kanban-header">
      <span class="cv-kanban-header-title">待办</span>
      <span class="cv-kanban-header-count">3</span>
    </div>
    <div class="cv-kanban-card">
      <div class="cv-kanban-card-title">实现会话管理模块</div>
      <div class="cv-kanban-card-desc">包含 session 的增删查改 API</div>
      <div class="cv-kanban-card-meta">
        <span class="cv-kanban-card-tag cv-kanban-card-tag-p1">P1</span>
        <span class="cv-kanban-card-tag cv-kanban-card-tag-owner">@张三</span>
      </div>
    </div>
  </div>
  <!-- Doing 列 -->
  <div class="cv-kanban-column cv-kanban-column-doing">
    <div class="cv-kanban-header">
      <span class="cv-kanban-header-title">进行中</span>
      <span class="cv-kanban-header-count">2</span>
    </div>
    <div class="cv-kanban-card">
      <div class="cv-kanban-card-title">重构 TSE 查表逻辑</div>
      <div class="cv-kanban-card-meta">
        <span class="cv-kanban-card-tag cv-kanban-card-tag-p0">P0</span>
      </div>
    </div>
  </div>
  <!-- Done 列 -->
  <div class="cv-kanban-column cv-kanban-column-done">
    <div class="cv-kanban-header">
      <span class="cv-kanban-header-title">已完成</span>
      <span class="cv-kanban-header-count">5</span>
    </div>
    <div class="cv-kanban-card">
      <div class="cv-kanban-card-title">API 统一命名</div>
    </div>
  </div>
</div>
```

**列变体**: `.cv-kanban-column-todo` / `-doing` / `-done` / `-blocked`

---

## 饼图 / 环形图（纯 CSS）🆕

使用 `conic-gradient` 实现，不依赖外部图表库。

```html
<div class="cv-pie-chart">
  <div class="cv-pie-visual cv-pie-visual-donut"
       data-center="85%"
       style="background: conic-gradient(
         var(--success) 0deg 198deg,
         var(--warning) 198deg 270deg,
         var(--danger) 270deg 306deg,
         var(--muted) 306deg 360deg
       );">
  </div>
  <div class="cv-pie-legend">
    <div class="cv-pie-legend-item">
      <span class="cv-pie-legend-dot" style="background:var(--success)"></span>
      已完成
      <span class="cv-pie-legend-value">55%</span>
    </div>
    <div class="cv-pie-legend-item">
      <span class="cv-pie-legend-dot" style="background:var(--warning)"></span>
      进行中
      <span class="cv-pie-legend-value">20%</span>
    </div>
    <div class="cv-pie-legend-item">
      <span class="cv-pie-legend-dot" style="background:var(--danger)"></span>
      阻塞
      <span class="cv-pie-legend-value">10%</span>
    </div>
    <div class="cv-pie-legend-item">
      <span class="cv-pie-legend-dot" style="background:var(--muted)"></span>
      待启动
      <span class="cv-pie-legend-value">15%</span>
    </div>
  </div>
</div>
```

---

## 柱状图（纯 CSS）🆕

垂直柱状图，通过 CSS Flexbox + 百分比高度实现。

```html
<div class="cv-bar-chart">
  <div class="cv-bar-chart-title">月度 Bug 修复趋势</div>
  <div class="cv-bar-chart-body">
    <div class="cv-bar-group">
      <div class="cv-bar cv-bar-danger" style="height: 80%;">
        <span class="cv-bar-value">24</span>
      </div>
      <div class="cv-bar-label">1月</div>
    </div>
    <div class="cv-bar-group">
      <div class="cv-bar cv-bar-warning" style="height: 50%;">
        <span class="cv-bar-value">15</span>
      </div>
      <div class="cv-bar-label">2月</div>
    </div>
    <div class="cv-bar-group">
      <div class="cv-bar cv-bar-success" style="height: 20%;">
        <span class="cv-bar-value">6</span>
      </div>
      <div class="cv-bar-label">3月</div>
    </div>
  </div>
</div>
```

**水平柱状图**（适合更多数据项）：

```html
<div class="cv-hbar-chart">
  <div class="cv-hbar-row">
    <div class="cv-hbar-label">模块 A</div>
    <div class="cv-hbar-track">
      <div class="cv-hbar-fill cv-hbar-fill-success" style="width: 90%"></div>
    </div>
    <div class="cv-hbar-value">90%</div>
  </div>
  <div class="cv-hbar-row">
    <div class="cv-hbar-label">模块 B</div>
    <div class="cv-hbar-track">
      <div class="cv-hbar-fill" style="width: 65%"></div>
    </div>
    <div class="cv-hbar-value">65%</div>
  </div>
</div>
```

---

## 风险矩阵 🆕

以影响×概率展示风险等级，用于方案评审和项目管理。

**简化列表版（推荐，更灵活）：**

```html
<div class="cv-risk-list">
  <div class="cv-risk-list-item">
    <div class="cv-risk-level cv-risk-level-high">H</div>
    <div class="cv-risk-content">
      <div class="cv-risk-title">TSE 查表性能不达标</div>
      <div class="cv-risk-desc">大流量场景下 miss 率超过 5%，需要优化 hash 算法</div>
    </div>
  </div>
  <div class="cv-risk-list-item">
    <div class="cv-risk-level cv-risk-level-medium">M</div>
    <div class="cv-risk-content">
      <div class="cv-risk-title">热升级兼容性</div>
      <div class="cv-risk-desc">新旧版本 IMEM 格式不兼容，需要双镜像方案</div>
    </div>
  </div>
  <div class="cv-risk-list-item">
    <div class="cv-risk-level cv-risk-level-low">L</div>
    <div class="cv-risk-content">
      <div class="cv-risk-title">文档延迟</div>
      <div class="cv-risk-desc">API 文档更新滞后一周</div>
    </div>
  </div>
</div>
```

---

## Tab 切换 🆕

在同一区域切换不同面板内容，减少页面长度。

```html
<div class="cv-tabs">
  <div class="cv-tab-nav">
    <button class="cv-tab-btn cv-tab-btn-active" data-tab="overview">概览</button>
    <button class="cv-tab-btn" data-tab="detail">详情</button>
    <button class="cv-tab-btn" data-tab="log">日志</button>
  </div>
  <div class="cv-tab-panel cv-tab-panel-active" data-tab-id="overview" data-tab-label="概览">
    <p>概览内容...</p>
  </div>
  <div class="cv-tab-panel" data-tab-id="detail" data-tab-label="详情">
    <p>详情内容...</p>
  </div>
  <div class="cv-tab-panel" data-tab-id="log" data-tab-label="日志">
    <div class="cv-code-block">
      <pre><code>log output...</code></pre>
    </div>
  </div>
</div>
```

**注意**：Tab 交互需要内嵌 `interactive.js`。打印时所有 Tab 内容自动展开。

---

## 折叠面板 🆕

适用于长文档中的辅助信息，默认收起以减少阅读干扰。

```html
<!-- 单个折叠 -->
<div class="cv-collapse">
  <div class="cv-collapse-trigger">
    <span class="cv-collapse-title">查看详细日志</span>
    <span class="cv-collapse-icon">▸</span>
  </div>
  <div class="cv-collapse-body">
    <div class="cv-collapse-body-inner">
      <div class="cv-code-block">
        <pre><code>... detailed log ...</code></pre>
      </div>
    </div>
  </div>
</div>

<!-- 手风琴（互斥折叠） -->
<div class="cv-accordion">
  <div class="cv-collapse">
    <div class="cv-collapse-trigger">
      <span class="cv-collapse-title">方案 A</span>
      <span class="cv-collapse-icon">▸</span>
    </div>
    <div class="cv-collapse-body">
      <div class="cv-collapse-body-inner">方案 A 详情</div>
    </div>
  </div>
  <div class="cv-collapse">
    <div class="cv-collapse-trigger">
      <span class="cv-collapse-title">方案 B</span>
      <span class="cv-collapse-icon">▸</span>
    </div>
    <div class="cv-collapse-body">
      <div class="cv-collapse-body-inner">方案 B 详情</div>
    </div>
  </div>
</div>
```

**注意**：折叠交互需要内嵌 `interactive.js`。打印时所有折叠自动展开。

---

## Chart.js 集成（P2）🆕

当纯 CSS 图表无法满足需求时（如折线图、雷达图、混合图表），引入 Chart.js 精简版。

```html
<!-- 在 body 末尾引入 Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>

<!-- 图表容器 -->
<div class="cv-chart-container">
  <div class="cv-chart-title">缺陷趋势（近6个月）</div>
  <canvas id="defectTrend" width="600" height="300"></canvas>
</div>

<script>
new Chart(document.getElementById('defectTrend'), {
  type: 'line',
  data: {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    datasets: [{
      label: '新增缺陷',
      data: [24, 18, 15, 12, 8, 6],
      borderColor: getComputedStyle(document.documentElement).getPropertyValue('--danger').trim(),
      tension: 0.3,
      fill: false
    }, {
      label: '修复缺陷',
      data: [20, 22, 18, 14, 10, 8],
      borderColor: getComputedStyle(document.documentElement).getPropertyValue('--success').trim(),
      tension: 0.3,
      fill: false
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { position: 'top' } },
    scales: { y: { beginAtZero: true } }
  }
});
</script>
```

**Chart.js 容器样式**：

```html
<style>
.cv-chart-container {
  margin: 20px 0;
  padding: 20px;
  border-radius: var(--radius);
  background: var(--panel);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}
.cv-chart-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--accent);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 16px;
}
</style>
```

---

## 左侧导航栏 (Side TOC) 🆕

**唯一的章节导航方式**。自动生成的左侧可折叠章节导航，默认收起。由 `interactive.js` 自动创建，无需手动添加 HTML。

> ⚠️ **不再使用顶部 `<nav class="cv-nav">`**：横向导航在章节较多时排列困难，已废弃。所有章节导航统一由左侧面板承担。

### 自动生成条件

- 页面包含 2 个以上带 `id` 的 `.cv-section`（内含 h2/h3）
- 非 PPT 演示模式
- 已内嵌 `interactive.js`

### AI 只需确保 section 有 id

```html
<section id="background" class="cv-section">
  <div class="cv-section-head">
    <h2>背景与问题</h2>
  </div>
  <div class="cv-section-body">...</div>
</section>

<section id="solution" class="cv-section">
  <div class="cv-section-head">
    <h2>解决方案</h2>
  </div>
  <div class="cv-section-body">...</div>
</section>
```

### 功能特性

- ☰ 汉堡按钮固定在页面左上角（topbar 下方）
- 点击展开左侧滑出面板，显示所有章节标题
- 支持 h2（一级）和 h3（二级缩进）
- 点击条目平滑滚动到对应章节，同时关闭面板
- 滚动页面时自动高亮当前章节
- 点击遮罩、关闭按钮或 ESC 键关闭面板
- 打印模式自动隐藏

### 相关 CSS class

| Class | 作用 |
|-------|------|
| `.cv-toc-toggle` | 汉堡按钮 |
| `.cv-toc-panel` | 导航面板 |
| `.cv-toc-item` | 目录条目 |
| `.cv-toc-active` | 当前章节高亮 |
| `.cv-toc-overlay` | 遮罩层 |

---

## 品牌定制 🆕

通过 CSS 变量覆盖实现团队品牌定制。

```html
<style>
:root {
  /* 覆盖品牌色 */
  --accent: #6366f1;        /* 主色调改为紫色 */
  --accent-soft: #eef2ff;
  /* 品牌信息 */
  --brand-color: #6366f1;
}
</style>
<body class="theme-default-light cv-brand-custom">
  <header class="cv-topbar">
    <div class="cv-topbar-inner">
      <!-- 自定义品牌名 -->
      <div class="cv-brand">TNIC · XLine Team</div>
    </div>
  </header>
  ...
  <footer class="cv-footer">
    <div class="cv-footer-card">TNIC / XLine Team · Powered by Context Visualizer</div>
  </footer>
</body>
```

---

## 打印 / 导出模式 🆕

### 自动打印适配

只需内嵌 `print.css` 即可获得打印优化：
- 自动隐藏导航栏、交互按钮
- 展开所有折叠和 Tab 内容
- 去除阴影、保留色彩
- 避免元素跨页断裂

### 截图友好容器

用 `.cv-export-ready` 包裹内容获得固定宽度白底容器：

```html
<div class="cv-export-ready">
  <!-- 截图友好的内容区域 -->
</div>
```

### 水印

```html
<body class="theme-default-light cv-watermark" data-watermark="INTERNAL">
```

---

## 文章插图模式 🆕

专为"截图后插入技术文章"设计的轻量模式。纯白背景、紧凑布局、无外部依赖。

### 完整 HTML 骨架

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>插图标题</title>
  <style>
    :root {
      --bg: #ffffff;
      --panel: #ffffff;
      --text: #1a1a2e;
      --muted: #6b7280;
      --accent: #3b82f6;
      --accent-soft: #eff6ff;
      --success: #10b981;
      --success-soft: #ecfdf5;
      --warning: #f59e0b;
      --warning-soft: #fffbeb;
      --danger: #ef4444;
      --danger-soft: #fef2f2;
      --purple: #8b5cf6;
      --purple-soft: #f5f3ff;
      --border: #e5e7eb;
      --code-bg: #f3f4f6;
      --max: 680px;
      --radius: 8px;
      --font: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 24px;
      max-width: var(--max);
      margin: 0 auto;
      -webkit-font-smoothing: antialiased;
    }
    /* ↓ 仅内嵌实际用到的组件样式，保持精简 ↓ */
  </style>
</head>
<body>
  <!-- 直接放置内容，无 topbar / footer -->
</body>
</html>
```

### 核心规则

| 规则 | 说明 |
|------|------|
| 背景 | 纯白 `#ffffff`，无渐变 |
| 宽度 | 600-700px（推荐 680px），内容少可缩至 500px，多可放至 800px |
| 标题字号 | 18-20px |
| 主文字字号 | 14-15px |
| 辅助文字 | ≥12px（标签、注释、说明） |
| 圆角 | 统一 8px |
| 阴影 | 无 |
| 外部依赖 | 无（不引用 CDN、外部字体、JS 框架） |
| 交互 | 无（不使用 JS、不加动画） |
| 页面骨架 | 无（不需要 topbar / footer / nav / 导航栏） |

### 配色速查

| 颜色 | 前景色 | 背景色 |
|------|--------|--------|
| 蓝色 | `#3B82F6` | `#EFF6FF` |
| 绿色 | `#10B981` | `#ECFDF5` |
| 橙色 | `#F59E0B` | `#FFFBEB` |
| 紫色 | `#8B5CF6` | `#F5F3FF` |
| 红色 | `#EF4444` | `#FEF2F2` |
| 灰色 | `#6B7280` | `#F9FAFB` |

### 适用图表类型

所有 `cv-arch-visual`、`cv-flow-visual`、`cv-struct-visual`、`cv-layer-stack` 等可视化组件均可在文章插图模式下使用，只需内嵌对应的 CSS 样式即可。

---

## 进度条

```html
<div class="cv-progress-bar">
  <div class="cv-progress-fill" style="width: 85%"></div>
</div>
```

---

## 标签组

```html
<div class="cv-tag-group">
  <span class="cv-tag cv-tag-accent">核心功能</span>
  <span class="cv-tag cv-tag-success">已完成</span>
  <span class="cv-tag cv-tag-warning">进行中</span>
  <span class="cv-tag cv-tag-danger">阻塞</span>
</div>
```

---

## Grid 布局辅助

```html
<div class="cv-grid-2">两列</div>
<div class="cv-grid-3">三列</div>
<div class="cv-grid-4">四列</div>
```

---

## 图片 / Figure 组件

参见 SKILL.md 中的详细图片处理规则。默认 base64 内嵌。

```html
<figure class="cv-figure">
  <img src="data:image/png;base64,..." alt="描述">
  <figcaption>图片说明</figcaption>
</figure>
```

---

## PPT 演示模式

参见 SKILL.md 中的完整 PPT 模式说明。

---

## 场景组合模板

各场景的推荐组件组合和页面结构，请参考 `config/scene_routes.json` 中对应场景的 `template.page_structure` 字段。
