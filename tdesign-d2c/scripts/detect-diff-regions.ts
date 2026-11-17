import * as fs from "node:fs";
import * as path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

// ESM 下 __dirname 默认未定义；这里兜底为脚本所在目录
const __filename =
  typeof (globalThis as any).__filename === "string"
    ? (globalThis as any).__filename
    : fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const cwdRequire = createRequire(path.join(process.cwd(), "package.json"));
function safeRequire(id: string): any {
  try { return cwdRequire(id); } catch {}
  try { return require(id); } catch {}
  return null;
}

/* ============== 类型定义 ============== */

export type DiffSeverity = "high" | "medium" | "low";

/** 自动检测到的还原差异区域 */
export interface DetectedDiffRegion {
  /** 名称（差异点 N） */
  name: string;
  /** 相对整图的百分比位置（与 generate-diff-report 的 hotspot 对齐） */
  bbox: { left: string; top: string; width: string; height: string };
  /** 该 bbox 内差异像素数 */
  diffPixels: number;
  /** 该 bbox 的像素面积 */
  bboxPixels: number;
  /** 差异像素占比 0~1（diffPixels / bboxPixels） */
  ratio: number;
  /** 严重度（保留字段，供内部排序/兼容，不再直接展示） */
  severity: DiffSeverity;
  /** 差异类型 */
  kind?: "text" | "image" | "color" | "edge" | "offset";
  /** 差异类型标签（中文） */
  kindLabel?: string;
  /** 差异原因说明（中文） */
  reason?: string;
  /** 归属区块名（与区块清单重叠匹配得到） */
  regionName?: string;
  /** 检测到的纵向偏移量（px，正=渲染结果整体偏下）；仅 kind==="offset" 时有意义 */
  offsetY?: number;
  /** 检测到的横向偏移量（px，正=渲染结果整体偏左）；仅 kind==="offset" 时有意义 */
  offsetX?: number;
  /** 偏移主方向（用于报告聚合归类）；仅 kind==="offset" 时有意义 */
  offsetAxis?: "x" | "y" | "xy";
  /** 是否属于「待改进」的可修复问题（供报告聚合"待改进"清单） */
  fixable?: boolean;
}

/** 区块清单引用（用于归属匹配 + 原因推断） */
export interface RefRegion {
  name: string;
  strategy?: string;
  bbox: { left: string; top: string; width: string; height: string };
}

export interface DetectDiffOptions {
  /** 网格单元尺寸（px），默认按图片尺寸自适应 */
  cellSize?: number;
  /** 单元内差异像素占比阈值（超过才标记），默认 0.04 */
  density?: number;
  /** 最小 bbox 面积占整图比例（低于则丢弃），默认 0.0008 */
  minBboxAreaRatio?: number;
  /** 最多返回区域数（按差异像素降序），默认 40 */
  maxRegions?: number;
  /** 单像素颜色距离阈值（超过记为差异），默认 40 */
  colorThreshold?: number;
  /** 探测模式：base 与 render 尺寸不一致时是否对齐到小图，默认 true */
  align?: boolean;
  /** 区块清单（用于给每个差异点归属区块 + 推断差异原因） */
  regions?: RefRegion[];
}

/* ============== 差异类型 / 原因推断 ============== */

const pctNum = (s: string) => parseFloat(String(s)) || 0;


function estimateVerticalShift(
  d1: Buffer,
  d2: Buffer,
  w: number,
  h: number,
  bx: number,
  by: number,
  bw: number,
  bh: number,
  maxShift: number
): { bestDy: number; baseDiff: number; bestDiff: number } {
  const stepX = Math.max(1, Math.floor(bw / 30));
  const stepY = Math.max(1, Math.floor(bh / 30));
  const meanDiffAt = (dy: number): number => {
    let sum = 0;
    let cnt = 0;
    for (let y = by; y < by + bh && y < h; y += stepY) {
      const ry = y + dy;
      if (ry < 0 || ry >= h) continue;
      for (let x = bx; x < bx + bw && x < w; x += stepX) {
        const i1 = (y * w + x) * 4;
        const i2 = (ry * w + x) * 4;
        const dr = d1[i1] - d2[i2];
        const dg = d1[i1 + 1] - d2[i2 + 1];
        const db = d1[i1 + 2] - d2[i2 + 2];
        sum += Math.sqrt(dr * dr + dg * dg + db * db);
        cnt++;
      }
    }
    return cnt ? sum / cnt : Infinity;
  };
  const baseDiff = meanDiffAt(0);
  // 扫描所有候选位移的差异
  const scores: Array<{ dy: number; m: number }> = [];
  let globalMin = baseDiff;
  for (let dy = -maxShift; dy <= maxShift; dy++) {
    if (dy === 0) continue;
    const m = meanDiffAt(dy);
    scores.push({ dy, m });
    if (m < globalMin) globalMin = m;
  }
  // 在「接近全局最小」的容差内，选绝对值最小的位移，避免文本行周期性把匹配拉到相邻行导致虚高
  const tol = globalMin * 1.15 + 1;
  let bestDy = 0;
  let bestDiff = baseDiff;
  scores
    .filter((s) => s.m <= tol)
    .sort((a, b) => Math.abs(a.dy) - Math.abs(b.dy))
    .some((s) => {
      bestDy = s.dy;
      bestDiff = s.m;
      return true; // 取第一个（|dy| 最小）
    });
  return { bestDy, baseDiff, bestDiff };
}


function estimateHorizontalShift(
  d1: Buffer,
  d2: Buffer,
  w: number,
  h: number,
  bx: number,
  by: number,
  bw: number,
  bh: number,
  maxShift: number
): { bestDx: number; baseDiff: number; bestDiff: number } {
  const stepX = Math.max(1, Math.floor(bw / 30));
  const stepY = Math.max(1, Math.floor(bh / 30));
  const meanDiffAt = (dx: number): number => {
    let sum = 0;
    let cnt = 0;
    for (let y = by; y < by + bh && y < h; y += stepY) {
      for (let x = bx; x < bx + bw && x < w; x += stepX) {
        const rx = x + dx;
        if (rx < 0 || rx >= w) continue;
        const i1 = (y * w + x) * 4;
        const i2 = (y * w + rx) * 4;
        const dr = d1[i1] - d2[i2];
        const dg = d1[i1 + 1] - d2[i2 + 1];
        const db = d1[i1 + 2] - d2[i2 + 2];
        sum += Math.sqrt(dr * dr + dg * dg + db * db);
        cnt++;
      }
    }
    return cnt ? sum / cnt : Infinity;
  };
  const baseDiff = meanDiffAt(0);
  const scores: Array<{ dx: number; m: number }> = [];
  let globalMin = baseDiff;
  for (let dx = -maxShift; dx <= maxShift; dx++) {
    if (dx === 0) continue;
    const m = meanDiffAt(dx);
    scores.push({ dx, m });
    if (m < globalMin) globalMin = m;
  }
  // 在「接近全局最小」的容差内，选绝对值最小的位移，避免竖直笔画 / 网格周期性把匹配拉到相邻列导致虚高
  const tol = globalMin * 1.15 + 1;
  let bestDx = 0;
  let bestDiff = baseDiff;
  scores
    .filter((s) => s.m <= tol)
    .sort((a, b) => Math.abs(a.dx) - Math.abs(b.dx))
    .some((s) => {
      bestDx = s.dx;
      bestDiff = s.m;
      return true;
    });
  return { bestDx, baseDiff, bestDiff };
}


function classifyRegions(
  list: DetectedDiffRegion[],
  base: any,
  render: any,
  w: number,
  h: number,
  refs: RefRegion[]
): void {
  const d1 = base.bitmap.data as Buffer;
  const d2 = render.bitmap.data as Buffer;

  for (const r of list) {
    const rl = pctNum(r.bbox.left);
    const rt = pctNum(r.bbox.top);
    const rw = pctNum(r.bbox.width);
    const rh = pctNum(r.bbox.height);

    let owner: RefRegion | undefined;
    let ownerArea = 0;
    for (const g of refs) {
      const gl = pctNum(g.bbox.left);
      const gt = pctNum(g.bbox.top);
      const gw = pctNum(g.bbox.width);
      const gh = pctNum(g.bbox.height);
      const ox = Math.max(0, Math.min(rl + rw, gl + gw) - Math.max(rl, gl));
      const oy = Math.max(0, Math.min(rt + rh, gt + gh) - Math.max(rt, gt));
      const oa = ox * oy;
      if (oa > ownerArea) {
        ownerArea = oa;
        owner = g;
      }
    }

    const bx = Math.round((rl / 100) * w);
    const by = Math.round((rt / 100) * h);
    const bw = Math.max(1, Math.round((rw / 100) * w));
    const bh = Math.max(1, Math.round((rh / 100) * h));
    const stepX = Math.max(1, Math.floor(bw / 40));
    const stepY = Math.max(1, Math.floor(bh / 40));
    let dark = 0;
    let cnt = 0;
    let sumDiff = 0;
    for (let y = by; y < by + bh && y < h; y += stepY) {
      for (let x = bx; x < bx + bw && x < w; x += stepX) {
        const i = (y * w + x) * 4;
        const lum = 0.299 * d1[i] + 0.587 * d1[i + 1] + 0.114 * d1[i + 2];
        if (lum < 140) dark++;
        const dr = d1[i] - d2[i];
        const dg = d1[i + 1] - d2[i + 1];
        const db = d1[i + 2] - d2[i + 2];
        sumDiff += Math.sqrt(dr * dr + dg * dg + db * db);
        cnt++;
      }
    }
    const darkRatio = cnt ? dark / cnt : 0;
    const meanDiff = cnt ? sumDiff / cnt : 0;
    const strat = owner?.strategy ?? "";

   
    let bestDy = 0;
    let baseDiffY = 0;
    let bestDiffY = 0;
    let bestDx = 0;
    let baseDiffX = 0;
    let bestDiffX = 0;
    const isImage = strat.indexOf("image-restore") === 0;
    if (!isImage) {
      const maxShiftY = Math.max(4, Math.min(64, Math.round(h * 0.02), bh));
      const sy = estimateVerticalShift(d1, d2, w, h, bx, by, bw, bh, maxShiftY);
      bestDy = sy.bestDy;
      baseDiffY = sy.baseDiff;
      bestDiffY = sy.bestDiff;

      const maxShiftX = Math.max(4, Math.min(80, Math.round(w * 0.03), bw));
      const sx = estimateHorizontalShift(d1, d2, w, h, bx, by, bw, bh, maxShiftX);
      bestDx = sx.bestDx;
      baseDiffX = sx.baseDiff;
      bestDiffX = sx.bestDiff;
    }
    // 单方向偏移判定：>=3px 的最优位移，且平移对齐后差异较对齐前显著下降（说明内容本身一致）
    const isOffsetY =
      !isImage && Math.abs(bestDy) >= 3 && baseDiffY > 12 && bestDiffY < baseDiffY * 0.7;
    const isOffsetX =
      !isImage && Math.abs(bestDx) >= 3 && baseDiffX > 12 && bestDiffX < baseDiffX * 0.7;
    // 对齐增益：平移后差异下降幅度（越大说明该方向偏移越显著）
    const gainY = isOffsetY ? 1 - bestDiffY / baseDiffY : 0;
    const gainX = isOffsetX ? 1 - bestDiffX / baseDiffX : 0;
    const isOffset = isOffsetX || isOffsetY;

    let kind: DetectedDiffRegion["kind"];
    let kindLabel: string;
    let reason: string;
    let fixable = false;
    let offsetY: number | undefined;
    let offsetX: number | undefined;
    let offsetAxis: DetectedDiffRegion["offsetAxis"];
    if (isImage) {
      kind = "image";
      kindLabel = "配图差异";
      reason =
        "装饰位图按原图还原，浏览器缩放采样与设计稿导出的位图之间存在细微像素差异，非结构问题";
    } else if (isOffset) {
      kind = "offset";
      // 主方向：取对齐增益更大者；两方向增益接近（差值<10%）视为斜向偏移
      const bothClose = isOffsetX && isOffsetY && Math.abs(gainX - gainY) < 0.1;
      offsetAxis = bothClose ? "xy" : gainX >= gainY ? "x" : "y";
      const parts: string[] = [];
      if (offsetAxis === "x" || offsetAxis === "xy") {
        offsetX = bestDx;
        const dirX = bestDx > 0 ? "偏左" : "偏右";
        parts.push(
          `横向${dirX}约 ${Math.abs(bestDx)}px（对齐后差异下降 ${Math.round(gainX * 100)}%）`
        );
      }
      if (offsetAxis === "y" || offsetAxis === "xy") {
        offsetY = bestDy;
        const dirY = bestDy > 0 ? "偏下" : "偏上";
        parts.push(
          `纵向${dirY}约 ${Math.abs(bestDy)}px（对齐后差异下降 ${Math.round(gainY * 100)}%）`
        );
      }
      const isX = offsetAxis === "x" || offsetAxis === "xy";
      kindLabel =
        offsetAxis === "x" ? "横向位置偏移" : offsetAxis === "y" ? "纵向位置偏移" : "位置偏移";
      const cause = isX
        ? "疑似左侧栏 / 上游容器宽度与设计稿不符，导致内容整体横移，建议核对列宽 / 容器宽度后重排"
        : "疑似上游区块高度 / 间距累计误差，建议核对间距后重排";
      reason = `该区域内容与设计稿一致，但${parts.join("、")}，${cause}`;
      fixable = true;
    } else if (r.ratio < 0.03) {
      kind = "edge";
      kindLabel = "抗锯齿边缘";
      reason = "元素边界的次像素抗锯齿渲染不同，肉眼几乎不可见";
    } else if (darkRatio > 0.55 && meanDiff > 60) {
      kind = "color";
      kindLabel = "颜色 / 背景差异";
      reason =
        "该区域整体色值与设计稿存在偏差（背景色 / 填充色不一致），建议核对色值 token";
      fixable = true;
    } else {
      kind = "text";
      kindLabel = "字体渲染差异";
      reason =
        "文字内容与排版位置一致，因页面回退到系统字体（与设计稿指定字体的字形 / 字重 / 抗锯齿不同）而产生像素级差异";
    }
    r.kind = kind;
    r.kindLabel = kindLabel;
    r.reason = reason;
    r.regionName = owner?.name ?? "";
    r.fixable = fixable;
    if (offsetY !== undefined) r.offsetY = offsetY;
    if (offsetX !== undefined) r.offsetX = offsetX;
    if (offsetAxis !== undefined) r.offsetAxis = offsetAxis;
  }
}

/* ============== 核心检测 ============== */

async function loadJimp(): Promise<any> {
  const mod = safeRequire("jimp");
  if (!mod) throw new Error("未安装 jimp，无法自动检测差异点（请 npm i -D jimp）");
  return mod.Jimp ?? mod.default ?? mod;
}

/** 计算 base / render 逐像素差异掩码 */
function buildMask(base: any, render: any, threshold: number) {
  const w = base.bitmap.width;
  const h = base.bitmap.height;
  const d1 = base.bitmap.data as Buffer;
  const d2 = render.bitmap.data as Buffer;
  const mask = new Uint8Array(w * h);
  let total = 0;
  for (let i = 0, p = 0; i < d1.length; i += 4, p++) {
    const dr = d1[i] - d2[i];
    const dg = d1[i + 1] - d2[i + 1];
    const db = d1[i + 2] - d2[i + 2];
    const da = d1[i + 3] - d2[i + 3];
    const dist = Math.sqrt(dr * dr + dg * dg + db * db + da * da);
    if (dist > threshold) {
      mask[p] = 1;
      total++;
    }
  }
  return { mask, w, h, total };
}

export async function detectDiffRegions(
  basePath: string,
  renderPath: string,
  opts: DetectDiffOptions = {}
): Promise<DetectedDiffRegion[]> {
  const Jimp = await loadJimp();

  const base = await Jimp.read(basePath);
  const render = await Jimp.read(renderPath);

  let aligned = false;
  if (base.bitmap.width !== render.bitmap.width || base.bitmap.height !== render.bitmap.height) {
    if (opts.align === false) {
      throw new Error(
        `原稿与渲染图尺寸不一致（${base.bitmap.width}x${base.bitmap.height} vs ${render.bitmap.width}x${render.bitmap.height}），且已禁用对齐。`
      );
    }
    aligned = true;
    const w = Math.min(base.bitmap.width, render.bitmap.width);
    const h = Math.min(base.bitmap.height, render.bitmap.height);
    if (typeof base.resize === "function") {
      try { base.resize({ w, h }); } catch { base.resize(w, h); }
      try { render.resize({ w, h }); } catch { render.resize(w, h); }
    }
  }

  const cellSize =
    opts.cellSize ?? Math.max(8, Math.round(Math.min(base.bitmap.width, base.bitmap.height) / 60));
  const density = opts.density ?? 0.04;
  const minBboxAreaRatio = opts.minBboxAreaRatio ?? 0.0008;
  const maxRegions = opts.maxRegions ?? 40;
  const colorThreshold = opts.colorThreshold ?? 40;

  const { mask, w, h, total } = buildMask(base, render, colorThreshold);
  const totalArea = w * h;

  if (total === 0) return [];

  const cols = Math.ceil(w / cellSize);
  const rows = Math.ceil(h / cellSize);
  const cellDiff = new Float64Array(cols * rows);
  const cellArea = new Float64Array(cols * rows);
  for (let y = 0; y < h; y++) {
    const row = (y / cellSize) | 0;
    for (let x = 0; x < w; x++) {
      const col = (x / cellSize) | 0;
      const idx = row * cols + col;
      cellArea[idx]++;
      cellDiff[idx] += mask[y * w + x];
    }
  }

  const hot = new Uint8Array(cols * rows);
  for (let i = 0; i < hot.length; i++) {
    if (cellArea[i] > 0 && cellDiff[i] / cellArea[i] >= density) hot[i] = 1;
  }

  // 连通分量（4 邻接）合并热单元
  const label = new Int32Array(cols * rows).fill(-1);
  const boxes: Array<{ minC: number; minR: number; maxC: number; maxR: number }> = [];
  const stack: number[] = [];
  for (let i = 0; i < hot.length; i++) {
    if (!hot[i] || label[i] !== -1) continue;
    const cur = boxes.length;
    label[i] = cur;
    stack.length = 0;
    stack.push(i);
    let minC = cols, minR = rows, maxC = -1, maxR = -1;
    while (stack.length) {
      const c = stack.pop()!;
      const cc = c % cols;
      const cr = (c / cols) | 0;
      if (cc < minC) minC = cc;
      if (cc > maxC) maxC = cc;
      if (cr < minR) minR = cr;
      if (cr > maxR) maxR = cr;
      const neigh = [c - 1, c + 1, c - cols, c + cols];
      for (const n of neigh) {
        if (n < 0 || n >= hot.length) continue;
        if (n % cols === 0 && cc === cols - 1) continue; // 跨行
        if (n % cols === cols - 1 && cc === 0) continue;
        if (hot[n] && label[n] === -1) {
          label[n] = cur;
          stack.push(n);
        }
      }
    }
    boxes[cur] = { minC, minR, maxC, maxR };
  }
  const regions: DetectedDiffRegion[] = [];
  for (let l = 0; l < (boxes?.length ?? 0); l++) {
    const b = boxes[l];
    if (!b) continue;
    const bx = b.minC * cellSize;
    const by = b.minR * cellSize;
    const bw = Math.min((b.maxC + 1) * cellSize - bx, w - bx);
    const bh = Math.min((b.maxR + 1) * cellSize - by, h - by);
    if (bw <= 0 || bh <= 0) continue;

    let diffPixels = 0;
    for (let y = by; y < by + bh; y++) {
      const off = y * w + bx;
      for (let x = bx; x < bx + bw; x++) diffPixels += mask[off + x];
    }
    const bboxPixels = bw * bh;
    if (bboxPixels / totalArea < minBboxAreaRatio) continue;
    if (diffPixels < 8) continue;

    const ratio = diffPixels / bboxPixels;
    const severity: DiffSeverity = ratio >= 0.12 ? "high" : ratio >= 0.04 ? "medium" : "low";
    regions.push({
      name: "",
      bbox: {
        left: `${((bx / w) * 100).toFixed(2)}%`,
        top: `${((by / h) * 100).toFixed(2)}%`,
        width: `${((bw / w) * 100).toFixed(2)}%`,
        height: `${((bh / h) * 100).toFixed(2)}%`,
      },
      diffPixels,
      bboxPixels,
      ratio: Number(ratio.toFixed(4)),
      severity,
    });
  }

  regions.sort((a, b) => b.diffPixels - a.diffPixels);
  const top = regions.slice(0, maxRegions);
  top.forEach((r, i) => (r.name = `差异点 ${i + 1}`));

  // 推断差异类型 / 原因 / 所在区块
  classifyRegions(top, base, render, w, h, opts.regions ?? []);

  if (aligned) {
    console.warn(
      "[warn] 原稿与渲染图尺寸不一致，已对齐到小图后再检测；若热区位置偏差，请保证两者尺寸一致。"
    );
  }
  return top;
}

/* ============== CLI ============== */

function parseCli(argv: string[]): { base: string; render: string; out: string; opts: DetectDiffOptions; quiet?: boolean } {
  const args: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) args[key] = "true";
    else { args[key] = next; i++; }
  }
  if (!args.base || !args.render) {
    throw new Error(
      "缺少必填参数 --base / --render。\n" +
        "示例：npx tsx detect-diff-regions.ts --base figma.png --render render.png --out diff-regions.json"
    );
  }
  const num = (k: string) => (args[k] ? Number(args[k]) : undefined);
  const readJson = (p?: string) =>
    p && fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : undefined;
  return {
    base: args.base,
    render: args.render,
    out: args.out ?? path.join(path.dirname(args.base), "diff-regions.json"),
    quiet: args.quiet === "true",
    opts: {
      cellSize: num("cell-size"),
      density: num("density"),
      minBboxAreaRatio: num("min-bbox-area-ratio"),
      maxRegions: num("max-regions"),
      colorThreshold: num("color-threshold"),
      align: args.align === "false" ? false : true,
      // 传入区块清单后，会为每个差异点自动匹配归属区块（regionName），
      // 否则 CLI 下 regionName 恒为空，差异点无法归属到任何区块。
      regions: readJson(args.regions ?? args["regions-file"]),
    },
  };
}

async function main() {
  const parsed = parseCli(process.argv.slice(2));
  if (!fs.existsSync(parsed.base)) throw new Error(`base 不存在：${parsed.base}`);
  if (!fs.existsSync(parsed.render)) throw new Error(`render 不存在：${parsed.render}`);

  const regions = await detectDiffRegions(parsed.base, parsed.render, parsed.opts);

  fs.writeFileSync(parsed.out, JSON.stringify(regions, null, 2), "utf8");
  console.log(`✓ 检测完成，共 ${regions.length} 处差异区域，已写入：${parsed.out}`);
  for (const r of regions.slice(0, 10)) {
    console.log(
      `  - ${r.name} [${r.severity}] 位置 左${r.bbox.left} 上${r.bbox.top} 宽${r.bbox.width} 高${r.bbox.height} · 差异像素 ${r.diffPixels} (${(r.ratio * 100).toFixed(1)}%)`
    );
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error("✗ 差异点检测失败：", e.message);
    process.exit(1);
  });
}
