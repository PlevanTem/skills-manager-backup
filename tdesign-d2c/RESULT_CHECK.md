# 1. 检查渲染结果

## 1.1 启动开发服务器

- 如果开发服务器尚未运行，请先启动（根据项目使用的包管理器自动选择 `npm run dev` / `pnpm dev` / `yarn dev`）：
  ```bash
  # AI 应根据项目中的 lock 文件自动判断包管理器
  npm run dev   # 或 pnpm dev / yarn dev
  ```
- 如果已经在运行，请继续下一步。

## 1.2 截取渲染页面截图

- 如果项目中未安装 playwright，请先安装：

```bash
npm i -D playwright
npx playwright install chromium
```

- 只截取目标组件所在的 DOM 节点，而非整页
- 使用 `deviceScaleFactor: 1`（关键）
- 视口宽度与 Figma 设计稿一致（通常 1440）
- 使用 `Math.round(box.x/y)` + Figma 原图 `width/height` 作为 `clip` 参数显式传入 `page.screenshot`，不要直接使用 `el.screenshot()`。

**统一用脚本截图（跨平台，macOS / Linux / Windows PowerShell 都适用）**：

```bash
npx tsx scripts/take-screenshot.ts \
  --url       <page-url> \
  --selector  '[data-screenshot-root]' \
  --out       _design-context/${figma-id}/render-result.png \
  --width     <figma-width> \
  --height    <figma-height>
```

> 若项目中未安装 `playwright`，请先安装：`npm i -D playwright && npx playwright install chromium`（或对应包管理器的等效命令，如 `pnpm add -D playwright`）。

### 最低要求

- 截图保存路径：`_design-context/${figma-id}/render-result.png`
- 截图尺寸必须与 `_design-context/${figma-id}/screenShot.png`（Figma 原图）**完全一致**（宽/高都相同）。

## 1.3 对比渲染结果与 Figma 设计稿

> [用法] `npx tsx scripts/compare-images.ts <imagePath1> <imagePath2> <figma-link> <model>`

> 差异图会输出到 `imagePath1` 所在目录下的 `diff.png`。

如果脚本提示 "尺寸不一致" 或 "宽高比差异较大"，请回到 1.2 重新截图。

> ⚠️ **强制要求**：无论 §1.3 输出的相似度是否达标（哪怕明显很低），都**必须**立即进入 §1.4 生成报告，**不允许**在看到低分后跳过 §1.4、直接返回 1.2/1.3 或直接开始修改代码。报告是本流程的交付物，低分同样需要被记录和展示；是否继续修改是 §1.4 生成完报告之后、§2 才需要决策的事情。

## 1.3.1 自动检测"还原存在差异的点是哪些"

- 默认在 §1.4 调用 `generate-diff-report.ts` 时**自动执行**，无需额外操作。
- 也可显式预生成，再传入报告：

```bash
npx tsx scripts/detect-diff-regions.ts \
  --base    _design-context/${figma-id}/screenShot.png \
  --render  _design-context/${figma-id}/render-result.png \
  --regions _design-context/${figma-id}/regions.json \
  --out     _design-context/${figma-id}/diff-regions.json
```

可选参数：`--cell-size`（网格单元 px，默认自适应）、`--density`（单元差异占比阈值，默认 0.04）、`--max-regions`（最多返回数，默认 40）、`--color-threshold`（单像素色差阈值，默认 40）。

- **务必传入 `--regions`**：传入 §1.4.1 的区块清单后，脚本会按重叠面积为每个差异点自动匹配归属区块（`regionName`）；若省略，则 CLI 下 `regionName` 恒为空，差异点清单无法归属到任何区块。（注：`generate-diff-report.ts` 内部自动检测时已复用 `--regions`，无需重复传。）
- 报告生成时可显式注入：`--diff-regions _design-context/${figma-id}/diff-regions.json`；或 `--no-diff-points` 关闭自动检测。
- 严重度分级：`明显差异`（高占比 / 大块）→ 🔴、`部分差异` → 🟠、`细微差异`（多为边缘抗锯齿）→ 🔵。

### 1.3.2 补充跨区块的"系统性差异"条目（重要）

当从 `diff.png` 观察到跨区块的系统性差异（如「纵向累计偏移」）时，**必须手动在 `diff-regions.json` 中补充一条独立条目**，使其进入报告的「差异点清单」。示例条目：

```json
{
  "name": "纵向累计偏移（系统性）",
  "bbox": { "left": "6.67%", "top": "27%", "width": "86.67%", "height": "73%" },
  "diffPixels": null,
  "ratio": 0.31,
  "severity": "high",
  "kindLabel": "纵向累计偏移",
  "reason": "文本行高 / 卡片高度与 figma.html 存在细微差异，自上而下逐区块累加，页脚处最明显（diff 呈成对红蓝双影），属跨区块系统性问题。",
  "regionName": "实验室工具 → 实践案例 → 页脚"
}
```

补充后再通过 `--diff-regions` 注入 `generate-diff-report.ts` 重新生成报告。

## 1.4 生成可视化还原报告

> 在 §1.3 完成 `compare-images.ts` 终端对比之后，**必须继续**生成一份单文件 HTML 还原报告，方便交付给设计师 / 产品经理 / Code Review。**这一步不可省略，也不可因为相似度低而跳过。**

### 1.4.1 准备 regions.json（区块清单）

根据本次 D2C 转换的实际结果，生成 `_design-context/${figma-id}/regions.json`：

```json
[
  {
    "name": "区块名（人类可读）",
    "strategy": "component-rewrite | image-restore | image-restore-warn | issue",
    "bbox": {
      "left": "12.5%",
      "top": "18.9%",
      "width": "22.5%",
      "height": "58.1%"
    },
    "msg": "一句话说明 Figma 节点形态 + 实际处理方式",
    "suggestion": "若 strategy = image-restore-warn / issue，给出修复建议；否则填 — "
  }
]
```

`strategy` 4 个值：

| 值                   | hotspot 颜色   | 触发场景                                                        |
| -------------------- | -------------- | --------------------------------------------------------------- |
| `component-rewrite`  | 🟢 绿（PASS）  | 节点是真矢量结构，按 §3.2 映射规则替换为业务组件 / TDesign 组件 |
| `image-restore`      | 🔵 蓝（INFO）  | 小图标 / 装饰画 / Logo / 真实位图（合理路径）                   |
| `image-restore-warn` | 🟠 橙（WARN）  | 设计稿质量不达标（结构被烘焙），需反馈给设计师                  |
| `issue`              | 🔴 红（ERROR） | 还原失败 / 明显视觉偏差                                         |

`bbox` 用百分比，相对画布的 left/top/width/height（不是相对父节点）。

### 1.4.2 调用脚本生成报告

```bash
# 在用户项目目录跑（让脚本能从 cwd 解析 jimp 等可选依赖）
npx tsx scripts/generate-diff-report.ts \
  --base    _design-context/${figma-id}/screenShot.png \
  --render  _design-context/${figma-id}/render-result.png \
  --diff    _design-context/${figma-id}/diff.png \
  --regions _design-context/${figma-id}/regions.json \
  --out     _design-context/${figma-id}/visual-diff-report.html \
  --title   "TDesign D2C 还原度报告 — <页面名>" \
  --source-url "<Figma URL>"
```

### 1.4.3 强制告知用户（还原度声明）

报告生成后，必须在对话中显式告知：

- ✅ **报告绝对路径**
- 📊 **加权相似度**（脚本 stdout 已打印）
- ⚠️ **是否触发了"图片还原 + 强制告知"**（即 regions 中是否存在 `image-restore-warn`）：若触发，需在对话中明确提示用户"当前设计稿存在结构被烘焙的区块，建议反馈给设计师按 §1.4.1 表格中的建议重新组织 Figma 节点"

### 1.4.4 还原度参考基线

基线说明：

- 加权相似度 ≥ 95%：优秀（视觉接近完美还原）
- 加权相似度 ≥ 85%：合格（结构与样式正确，存在抗锯齿/细微间距差异）
- 加权相似度 < 85%：不合格，报告生成后触发 §2 询问用户是否继续修改

## 2. §1.4 报告生成完毕后，如果加权相似度 < 85%，询问用户是否根据差异继续修改实现，还是停止流程。

**问题 2 — 是否继续？**（标题："是否继续？"）
是否根据差异继续修改实现？选项：是 / 否

如果用户选择"是"，则继续下一步。

**修复时的约束**：

- 不通过新增 `position: absolute` + 硬编码 `top/left` 的方式来修复偏移问题。
- 应回到 SKILL.md §6.3，将受影响区块改为 flex/gap/margin 的相对布局，通过调整 `margin` / `gap` / `padding` / `line-height` 来对齐。
- 仅当该元素本来就是角标、蒙版、浮层时，才允许保留或新增 `absolute`。

根据 `diff.png` 的差异形态判断修复方向：

- 若下半部分出现整体性红蓝"双影"沿 Y 轴成对分布，说明存在累计纵向偏移，需按 `SKILL.md` §6.3 的要求核对每个节点的 `line-height`、`font-size`、`margin`/`gap` 与 `figma.html` 是否一致，逐段消除多出的间距。
- 若差异仅集中在文字/图标边缘的细红边，属于字体抗锯齿差异，无需修改实现。
- 若存在大块色差，检查对应节点的 `background` / `src` 是否正确。

尝试查询组件文档，获取影响差异的组件文档。

> [用法] `npx tsx scripts/query-docs.ts <框架> <组件>`
> 例如：`npx tsx scripts/query-docs.ts react button,link`
