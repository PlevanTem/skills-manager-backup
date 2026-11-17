---
name: context-visualizer
description: "在用户需要把项目汇报、问题定位、调试过程、会议纪要、周报月报、方案评审、dashboard 看板、流程图、架构图、技术文档插图或技术文章配图转成可视化页面时触发。支持生成单文件 HTML、内嵌 CSS 设计系统、dark/PPT/文章插图模式、mermaid/图表/时间线/看板等组件，并可在用户明确要求分享、部署、发给团队时联动 OA Pages 生成内网链接。触发关键词：可视化、HTML、dashboard、看板、流程图、架构图、PPT 风格、技术文章插图、分享、部署、OA 链接。不适用于：纯文本总结、普通问答、代码调试或修复、无需页面化/可视化、明确要求 Markdown/纯文本/ASCII 且不要 HTML 的场景。"
triggers:
  - 可视化
  - 生成 HTML 页面
  - dashboard
  - 看板
  - 流程图
  - 架构图
  - PPT 风格
  - 技术文档插图
  - 技术文章配图
  - 分享页面
  - 部署到 OA
  - 生成内网链接
phases: 3
---

# context-visualizer — 设计系统模式 v4

## 核心理念

**AI 直接输出 HTML，skill 只管"风格一致性"。**

- 风格一致性 → CSS 变量 + 组件 class
- 内容增强 → AI 理解内容后自由决定用什么组件
- 场景模板 → 每个场景有推荐的组件组合和页面结构

## 触发方式

- 可视化项目汇报 / 问题定位 / 调试过程 / 当前总结
- 可视化为周报 / 月报 / 会议纪要 / 方案评审
- 可视化项目仪表盘 / dashboard / 看板
- 换成 dark 风格 / PPT 风格
- 帮我画个流程图说明一下
- 把这个分析做成可视化页面
- 可视化为技术文档插图
- 生成一个用于技术文章的 HTML 插图

**组合触发（生成 + 部署分享）**：

- 可视化 xxx 并分享 / 并发给团队 / 部署到 OA
- 做成页面部署给大家看 / 生成链接分享
- xxx 可视化一下然后给我个内网链接
- 把刚才的可视化页面分享出去

→ 见本文「一键分享到 OA Pages」章节。

## 负向触发规则

以下场景不要触发完整 `context-visualizer` 流程：

- 用户只要求纯文本总结、普通问答、代码解释、代码修改或问题修复，没有要求可视化/页面化。
- 用户明确要求 Markdown、纯文本、ASCII 图，或明确表示不要 HTML。
- 用户只要求部署已有文件，不要求生成可视化内容时，优先使用 `oa-pages-deploy`。
- 页面包含密钥、token、cookie、个人信息、内部敏感链接或未脱敏业务数据且用户要求分享/部署时，先提醒脱敏并确认授权。

## 工作流程

### 1. 识别场景

读取 `config/scene_routes.json`，根据 `aliases` 关键词匹配场景类型。

### 2. 查阅场景模板

识别场景后，从 `config/scene_routes.json` 读取该场景的 `template` 字段：
- `recommended_components`: 推荐使用的组件列表
- `page_structure`: 推荐的页面章节结构

**AI 应参考但不需完全照搬模板**——根据实际内容自由调整。

### 3. 直接输出 HTML

**如果是技术文档插图场景（文章插图模式）：**

1. 使用精简骨架（参见 4.2 节的 HTML 模板），无需读取完整 `base.css` / `components.css`
2. 仅内嵌实际用到的组件样式
3. 不引入任何 CDN / JS / 外部资源
4. 输出单文件 HTML

**其他场景（完整页面模式）：**

1. 读取 `assets/base.css` + `assets/components.css`，内嵌到 `<style>` 中
2. 如需打印/导出：内嵌 `assets/print.css`
3. 根据主题在 `:root` 中设置 CSS 变量
4. 如有品牌定制需求，覆盖 `--accent` 等品牌变量
5. **参考场景模板**组织页面结构
6. **自由决定**用什么组件来表达内容
7. 如使用交互组件（Tab/折叠/表格排序）：在 `</body>` 前内嵌 `assets/interactive.js`
8. 如使用 Chart.js 图表：引入 CDN
9. 输出单文件 HTML

### 4. AI 的自由裁量权

AI 可以自由决定：
- 用 **mermaid 流程图** 还是 **时间线** 还是 **对比表格**
- 哪些数据用 **指标卡片**，哪些用 **数据表格**
- 哪些代码/配置需要 **代码块**
- 哪些结论需要 **callout 强调框**
- 任务状态用 **看板** 还是 **表格**
- 进度用 **甘特图** 还是 **进度条** 还是 **水平柱状图**
- 比例数据用 **饼图** 还是 **柱状图**
- 风险用 **风险矩阵** 还是 **风险列表**
- 长内容用 **Tab 切换** 还是 **折叠面板** 还是全部展开

### 4.1 技术文档插图：可视化优先规则

**⚠️ 重要**：当场景识别为"技术文档插图"时，**默认使用 CSS 可视化方式**生成架构图、流程图、数据结构图等，而非 ASCII 文本方式。

**默认行为（可视化方式）：**
- **架构图** → 使用 `.cv-arch-visual`（CSS 彩色块 + 箭头 + Grid 布局）
- **流程图** → 使用 `.cv-flow-visual`（CSS 节点 + 连接线）或 Mermaid
- **数据结构图** → 使用 `.cv-struct-visual`（CSS 内存布局 + 域段标注）
- **层次关系** → 使用 `.cv-layer-stack`（CSS 层叠卡片）
- **状态机** → 使用 Mermaid stateDiagram 或 CSS 节点图

**仅当用户明确要求时，才使用 ASCII 方式：**
- 触发词："保持 ASCII" / "ASCII 风格" / "文本方式显示" / "纯文本图" / "monospace 风格"
- 使用 `.arch-diagram` class（等宽字体 + `white-space: pre`）

**可视化方式的优势：**
- 彩色编码更直观，读者一眼能区分不同模块
- 支持主题切换（light/dark 自动适配）
- 打印时保持高质量渲染
- 支持 hover 高亮等交互提示

### 4.2 文章插图模式（截图友好）

**⚠️ 重要**：当场景识别为"技术文档插图"时，默认启用**文章插图模式**——生成的 HTML 专门用于浏览器截图后插入文章，必须遵循以下规则：

**触发词**（与技术文档插图场景合并识别）：
- "技术文章插图" / "文章插图" / "用于截图" / "插入文章" / "截图用"
- "画个流程图" / "画个架构图" / "帮我画个图" / "生成一个插图"

**文章插图模式规则：**

1. **纯白背景**：`body` 追加 class `cv-article-illustration`，覆盖变量为纯白 `--bg: #ffffff`，去掉默认的渐变背景和 topbar/footer 等页面骨架
2. **紧凑尺寸**：整体宽度 600-700px（内容少可缩至 500px，多可放至 800px，不超过 800px），通过 `--max` 变量控制
3. **字号规范**：标题 18-20px，主文字 14-15px，辅助文字/标签不小于 12px，确保截图缩放后仍清晰可读
4. **无外部依赖**：纯 HTML + CSS + 内联 SVG，**不引用任何 CDN**（mermaid、Chart.js 均不使用），不引用外部字体或图标库
5. **静态展示**：不需要交互效果、不需要动画、不需要 JS，**不内嵌** `interactive.js`
6. **无页面骨架**：不需要 `.cv-topbar` / `.cv-footer` / `.cv-nav` / 左侧导航栏
7. **配色柔和专业**：使用设计系统的 CSS 变量色彩区分类别/层级/状态，但不花哨
8. **圆角统一**：`--radius: 8px`（覆盖默认的 20px，更紧凑）

**输出 HTML 骨架（文章插图模式）：**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ illustration_title }}</title>
  <style>
    /* 文章插图模式变量覆盖 */
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
      --shadow: none;
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
    /* 内嵌必要的组件样式（仅使用到的组件，精简版） */
  </style>
</head>
<body>
  <!-- 直接放置插图内容，无 topbar/footer -->
</body>
</html>
```

**与完整页面模式的区别：**

| 对比项 | 完整页面模式（默认） | 文章插图模式 |
|--------|---------------------|-------------|
| 背景 | 渐变灰蓝 `#f6f8fb` | 纯白 `#ffffff` |
| 宽度 | 1180px | 600-700px |
| 圆角 | 20px | 8px |
| 阴影 | 有 | 无 |
| 页面骨架 | topbar + footer + nav | 无 |
| JS 交互 | 支持 | 无 |
| 外部 CDN | mermaid / Chart.js | 无 |
| 用途 | 独立浏览的完整页面 | 截图后插入文章 |

### 5. 图片处理规则

**默认行为：Base64 内嵌（保持单文件自包含）**
- 读取图片文件，转为 base64 编码，内嵌到 `<img src="data:image/png;base64,...">`
- 支持格式：PNG、JPG/JPEG、GIF、WebP、SVG
- 使用 `.cv-figure` 组件包裹（详见 `references/component_catalog.md`）

**切换为引用模式的触发词**：
- "用引用方式" / "用链接方式" / "图片用 src 引用" / "不要内嵌图片"

### 6. PPT 演示模式

触发词："PPT 风格" / "PPT 模式" / "幻灯片" / "翻页" / "演示文稿"

PPT 模式输出规则：
1. **额外内嵌** `assets/presentation.css` 到 `<style>` 中
2. **body class** 追加 `presentation-ppt`
3. **内容结构**：用 `<div class="cv-slide cv-slide-xxx">` 包裹每页
4. **在 `</body>` 前**内嵌 `assets/presentation.js`
5. 第一个幻灯片加 `.cv-slide-active`

幻灯片类型：`cv-slide-cover`（封面）/ `cv-slide-divider`（章节）/ `cv-slide-content`（内容）/ `cv-slide-split`（两栏）/ `cv-slide-ending`（结尾）

### 7. 品牌定制

当用户需要团队辨识度时，覆盖 `:root` 中的 `--accent`、`--accent-soft` 等变量，body 追加 `cv-brand-custom` class。
详见 `references/component_catalog.md` 品牌定制章节。

### 8. 打印 / 导出

内嵌 `assets/print.css` 即可获得打印优化（自动隐藏导航、展开折叠/Tab、避免跨页断裂）。
水印：`<body class="cv-watermark" data-watermark="INTERNAL">`

### 10. 左侧导航栏（Side TOC）— 唯一导航方式

非 PPT 场景下，**左侧导航栏是唯一的章节导航方式**（由 `interactive.js` 自动创建，无需手写 HTML）。
**不要在 topbar 中放置 `<nav class="cv-nav">` 导航链接**——横向导航在章节较多时排列困难，所有章节导航统一由左侧面板承担。

**AI 只需确保**：
- 每个 `.cv-section` 带有唯一的 `id` 属性
- section 内有 `h2` 或 `h3` 标题
- 已内嵌 `interactive.js`
- section 少于 2 个时不显示导航栏
- **topbar 只放品牌标识（`.cv-brand`），不放章节导航链接**

详见 `references/component_catalog.md` 左侧导航栏章节。

- ✅ 使用 CSS 变量（`var(--accent)` 等）而非硬编码颜色
- ✅ 使用组件 class（`.cv-card`、`.cv-section` 等）
- ✅ mermaid 通过 CDN 引入
- ✅ **mermaid 初始化必须含 `securityLevel: 'sandbox'` 与 `htmlLabels: false`**（XSS 安全基线，详见 `references/component_catalog.md` 页面骨架段）
- ✅ Chart.js（如需）通过 CDN 引入
- ✅ 代码高亮通过 `<pre><code>` + CSS class 实现
- ✅ 图片默认 base64 内嵌
- ✅ 生成前参考 `config/scene_routes.json` 中的场景模板
- ✅ 如使用交互组件，内嵌 `interactive.js`
- ✅ 如需打印友好，内嵌 `print.css`
- ✅ PPT 模式时额外内嵌 `presentation.css` + `presentation.js`
- ✅ 每个 `.cv-section` 必须带唯一 `id` 属性（供导航栏跳转使用）
- ✅ 技术文档插图场景默认启用文章插图模式（`cv-article-illustration`）
- ✅ topbar 只放品牌标识，章节导航统一由左侧导航栏承担
- ❌ 不要硬编码 font-family / 颜色 / 圆角
- ❌ 不要写 inline style（除非 conic-gradient / 进度条 / 甘特图定位必需）
- ❌ 不要在未经用户指定时使用外部图片引用
- ❌ PPT 模式不要在单页放超过 7 个要点
- ❌ 文章插图模式不要引用外部 CDN（mermaid / Chart.js / 字体）
- ❌ 文章插图模式不要添加 JS 交互、动画、topbar / footer
- ❌ **不要在 topbar 中放置 `<nav class="cv-nav">` 章节链接**（横向导航在章节多时排列困难）
- ❌ **严禁将 mermaid `securityLevel` 设为 `'loose'` 或 `'antiscript'`**，也不得省略该字段
- ❌ **严禁将未经 DOMPurify 清洗的用户输入直接作为 `.mermaid` 容器内容**

## 一键分享到 OA Pages（融合子技能）

`context-visualizer` 内嵌了 `oa-pages-deploy` 作为**子技能**，位于 `./oa-pages-deploy/`。当用户同时表达"生成可视化"和"分享/发给团队/部署"时，**串行执行**两步：先生成 HTML，再调用子技能部署到 OA Pages，返回内网链接。

### 触发判定

识别到以下任一"分享意图"关键词时，进入组合模式：
- 分享 / 部署 / 上传到 OA / 发给团队 / 给大家看
- 生成链接 / 内网链接 / 预览链接 / OA 链接
- 部署到 pages.woa.com / 部署预览

### 工作流

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: 正常走 context-visualizer 工作流生成 HTML       │
│  Step 2: 将 HTML 写入 /tmp/cv-<slug>-<timestamp>.html    │
│  Step 3: 检查子技能配置：                                │
│    <SKILL_DIR>/oa-pages-deploy/config.sh                 │
│    - 若 PREVIEW_REPO 或 PREVIEW_DOMAIN 为空 → 进入        │
│      oa-pages-deploy 的对话式配置引导                    │
│  Step 4: 调用部署脚本（自动选 temp/ 目录）               │
│  Step 5: 把脚本返回的链接清晰告知用户                     │
└─────────────────────────────────────────────────────────┘
```

### 文件命名与目录选择

按用户语义自动选择 OA Pages 侧目标目录（对应 `oa-pages-deploy` 的目录约定）：

| 用户语义 | 目标路径 | 适用场景 |
|----------|----------|----------|
| "临时"/"一次性"/"随便发发" | `temp/<slug>.html` | 默认，一次性分享 |
| "保留"/"长期"/"归档" | `docs/<slug>.html` | 报告、建议书 |
| "交互预览"/"给 PM 看" | `preview/<slug>.html` | 交互 demo |
| 明确指定了目录 | 用用户指定的 | — |

`<slug>` 生成规则：
- 取可视化页面的标题 → 转小写 → 非字母数字替换为 `-` → 截断至 40 字符
- 追加日期后缀 `-YYYYMMDD`，避免重复（同名会被覆盖，但用户通常希望保留历史）
- 示例：`"2026 Q2 MEP 微码周报"` → `2026-q2-mep-weekly-20260423.html`

### 部署调用模板（AI 需要执行的命令）

```bash
# 定位子技能脚本（相对 context-visualizer 根目录）
CV_DIR="/Users/houxiangcai/workspace/tnic_docs/context-visualizer"
DEPLOY="${CV_DIR}/oa-pages-deploy/scripts/deploy.sh"

# 1. 把生成的 HTML 写到临时文件
HTML_TMP="/tmp/cv-${SLUG}-$(date +%Y%m%d%H%M%S).html"
# ... (AI 用 write_to_file 把 HTML 写到 $HTML_TMP)

# 2. 调用部署脚本（以临时分享为例）
bash "$DEPLOY" "$HTML_TMP" "temp/${SLUG}.html" "share: ${TITLE}"
```

脚本输出示例（AI 需要把这段转述给用户）：

```
✅ 部署成功！
   🔗 访问链接: https://xxx-preview.pages.woa.com/temp/xxx.html
   ⏳ OA Pages 自动部署通常 1-2 分钟生效
```

### 首次未配置时的处理

`oa-pages-deploy` 的 `config.sh` 为空（`PREVIEW_REPO=""` 或 `PREVIEW_DOMAIN=""`）时：

1. **先完成 HTML 生成并落到本地**（不要丢失用户成果）
2. 告知用户："HTML 已生成在 `<path>`，要部署到 OA Pages 还需配置一次仓库信息"
3. 按 `oa-pages-deploy/SKILL.md` 的"首次配置（对话引导）"流程收集 `PREVIEW_REPO` + `PREVIEW_DOMAIN`，写入 `<CV_DIR>/oa-pages-deploy/config.sh`
4. 配置完成后**自动**再次调用 `deploy.sh` 完成部署

### 多页一次分享

若用户一次需要生成多个页面（例如一组插图），建议：

1. 生成到同一个临时目录 `/tmp/cv-batch-<timestamp>/`
2. 用目录部署模式：`bash "$DEPLOY" --dir /tmp/cv-batch-<ts> "preview/<slug>" "share: ..."`
3. 返回目录索引链接 `https://<domain>/preview/<slug>/`

### 注意事项

- 仅在用户明确表达"分享/部署/发给团队"意图时才自动部署，避免打扰
- 文章插图模式（`cv-article-illustration`）生成的 HTML 仍可部署，但提醒用户这类页面是"为截图设计"的紧凑尺寸，直接在浏览器打开可能显示偏窄
- PPT 模式生成的 HTML 适合直接部署分享（可在内网用浏览器演示）
- 部署完成后同时把**本地 HTML 路径**和**OA Pages 链接**都给用户，方便后续修改重发

## 工程结构

```
context-visualizer/
├── SKILL.md                    # 本文件：AI 指令
├── assets/
│   ├── base.css                # 基础布局 + 排版
│   ├── components.css          # 组件样式库（含甘特图/看板/饼图/风险矩阵/Tab/折叠等）
│   ├── presentation.css        # PPT 演示模式样式
│   ├── presentation.js         # PPT 翻页/导航控制器
│   ├── print.css               # 打印 + 导出模式样式
│   └── interactive.js          # 轻量交互（Tab/折叠/表格排序）
├── config/
│   └── scene_routes.json       # 场景识别 + 别名路由 + 场景模板
├── references/
│   └── component_catalog.md    # 组件参考手册（AI 查阅用）
├── oa-pages-deploy/            # 🚀 子技能：一键部署到 OA Pages
│   ├── SKILL.md                # 独立 skill 文档（可单独加载）
│   ├── config.sh               # 仓库路径 + 域名配置
│   └── scripts/
│       ├── deploy.sh           # 部署脚本（支持单文件/目录/删除）
│       └── list.sh             # 列出已部署文件
└── demo/
    ├── v3-design-system-showcase.html   # v3 设计系统 demo
    ├── v4-weekly-report-demo.html       # v4 周报场景 demo
    ├── v4-meeting-notes-demo.html       # v4 会议纪要 demo
    ├── v4-design-review-demo.html       # v4 方案评审 demo
    ├── v4-project-dashboard-demo.html   # v4 项目仪表盘 demo
    └── v4-tech-doc-illustration-demo.html  # v4 技术文档插图 demo（可视化版）
```

## 主题

通过 `:root` CSS 变量控制（定义在 `assets/base.css`）：

- **白底通用**（默认）：`theme-default-light`
- **深色投屏**：body 添加 `theme-dark-screen` class，CSS 变量自动切换

## 组件速查

> 完整参考：`references/component_catalog.md`

**v3 基础组件**：`.cv-topbar` `.cv-page` `.cv-footer` · `.cv-hero` `.cv-hero-card` · `.cv-section` · `.cv-code-block` · `.cv-table` · `.cv-timeline` · `.cv-mermaid` · `.cv-metric-row` · `.cv-comparison` · `.cv-steps` · `.cv-callout` · `.cv-badge` `.cv-chip` `.cv-tag` · `.cv-progress-bar` · `.cv-grid-2/3/4` · `.cv-figure` · `.cv-slide`

**v4 新增组件**：`.cv-gantt` · `.cv-kanban` · `.cv-pie-chart` · `.cv-bar-chart` · `.cv-hbar-chart` · `.cv-risk-matrix` `.cv-risk-list` · `.cv-tabs` · `.cv-collapse` · `.cv-accordion` · `.cv-chart-container` · `.cv-export-ready` · `.cv-watermark` · `.cv-arch-visual` · `.cv-flow-visual` · `.cv-struct-visual` · `.cv-layer-stack` · `.cv-legend` · `.cv-toc-panel`
| **文章插图模式** | `.cv-article-illustration` | 截图友好：纯白背景、紧凑 600-700px、无骨架/JS/CDN | **v4** |
