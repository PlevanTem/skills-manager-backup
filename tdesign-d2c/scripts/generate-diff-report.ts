import * as fs from "node:fs";
import * as path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

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

/** 区块清单：驱动摘要结论与「顺利达成 / 待改进」统计 */
interface Region {
  /** 唯一标识 */
  id?: string;
  /** 区块名（如 "顶部导航 + 左侧菜单"） */
  name: string;
  /** 处理策略：决定摘要分类（顺利达成 / 待改进） */
  strategy:
    | "component-rewrite"     // 组件化重写（success / 绿）
    | "image-restore"         // 图片还原（合理路径）（info / 蓝）
    | "image-restore-warn"    // 图片还原 + 强制告知（warning / 橙）
    | "issue";                // 还原失败问题（error / 红）
  /** Figma 资源路径（如 "2ff61b43...png"） */
  resource?: string;
  /** 该区块覆盖的内容描述（出现在摘要清单中） */
  msg: string;
  /** 改进建议（出现在摘要清单中） */
  suggestion?: string;
  /** （可选）扩展的详细 KV 表 */
  details?: Array<{ key: string; value: string }>;
}

/** 评分相关（机器自动算 + 用户可覆写） */
interface ScoreData {
  pixelSim?: number;
  ssimSim?: number;
  diffPixels?: number;
  totalPixels?: number;
}

/** TL;DR 双栏 */
type ColRow = string;
interface AdviceCol {
  title?: string;
  rows: ColRow[];
}

/** 给设计师的建议 */
interface DesignAdvice {
  toneTag?: string;          // 标签文字（如 "提升组件化率 14% → 95%+"）
  summary?: string;          // 一段简介
  problems?: ColRow[];       // ❌ 当前稿件的问题
  solutions?: ColRow[];      // ✅ 改造建议
}

interface ReportInput {
  base: string;
  render: string;
  diff?: string;
  out?: string;
  title?: string;
  sourceUrl?: string;
  leftLabel?: string;
  rightLabel?: string;

  // —— 评分（也可由工具自动计算）
  pixelSim?: number;
  ssimSim?: number;
  diffPixels?: number;
  totalPixels?: number;

  // —— 诊断数据（v2 新增）
  summary?: string;          // 一句话结论 HTML
  summaryFile?: string;      // 或读 HTML 文件
  wins?: ColRow[];           // ✅ 顺利达成（默认从 regions 自动推断）
  issuesBrief?: ColRow[];    // ⚠️ 待改进（默认从 regions 自动推断）
  regions?: Region[];        // 区块清单（驱动热区 + 问题清单）
  regionsFile?: string;      // 或从文件读
  designAdvice?: DesignAdvice;
  designAdviceFile?: string;
  hotspotDesc?: string;      // 区块策略热区的副标题
  hotspotBgImg?: "render" | "base"; // 热区底图用渲染图还是原稿（默认 render）

  // —— 差异点（自动检测：还原存在差异的点是哪些）
  diffRegions?: any[];        // 自动检测到的差异区域列表
  diffRegionsFile?: string;   // 或从文件读（detect-diff-regions.ts 产物）
  noDiffPoints?: boolean;     // 跳过自动差异点检测

  // —— 兼容旧用法
  extraHtml?: string;
}

/* ============== CLI 解析 ============== */

function parseCli(argv: string[]): ReportInput {
  const args: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = "true";
    } else {
      args[key] = next;
      i++;
    }
  }
  if (args.config) {
    const cfg = JSON.parse(fs.readFileSync(args.config, "utf8"));
    return cfg as ReportInput;
  }
  if (!args.base || !args.render) {
    throw new Error(
      "缺少必填参数 --base / --render（或 --config xxx.json）。\n" +
        "示例：npx tsx generate-diff-report.ts --base figma.png --render render.png --diff diff.png"
    );
  }
  const readJsonIfExists = (p?: string) => (p ? JSON.parse(fs.readFileSync(p, "utf8")) : undefined);

  return {
    base: args.base,
    render: args.render,
    diff: args.diff,
    out: args.out,
    title: args.title,
    sourceUrl: args["source-url"],
    leftLabel: args["left-label"],
    rightLabel: args["right-label"],
    pixelSim: args["pixel-sim"] ? Number(args["pixel-sim"]) : undefined,
    ssimSim: args["ssim-sim"] ? Number(args["ssim-sim"]) : undefined,
    diffPixels: args["diff-pixels"] ? Number(args["diff-pixels"]) : undefined,
    totalPixels: args["total-pixels"] ? Number(args["total-pixels"]) : undefined,
    summary: args.summary,
    summaryFile: args["summary-file"],
    wins: readJsonIfExists(args.wins),
    issuesBrief: readJsonIfExists(args["issues-brief"]),
    regions: readJsonIfExists(args.regions ?? args["regions-file"]),
    designAdvice: readJsonIfExists(args["design-advice"] ?? args["design-advice-file"]),
    hotspotDesc: args["hotspot-desc"],
    hotspotBgImg: args["hotspot-bg"] as any,
    diffRegions: readJsonIfExists(args["diff-regions"] ?? args["diff-regions-file"]),
    noDiffPoints: args["no-diff-points"] === "true",
    extraHtml: args["extra-html-file"]
      ? fs.readFileSync(args["extra-html-file"], "utf8")
      : undefined,
  };
}

/* ============== 计算相似度（如果用户没传） ============== */

async function computeSimIfNeeded(
  baseFile: string,
  renderFile: string,
  input: ReportInput
): Promise<ReportInput> {
  if (
    input.pixelSim != null &&
    input.ssimSim != null &&
    input.diffPixels != null &&
    input.totalPixels != null
  ) {
    return input;
  }

  // 优先复用 compare-images.ts 的实现，保证报告数值与对比脚本 console 输出一致：
  // - 像素相似度：pixelmatch（含 autoTrim + letterbox 归一化）
  // - SSIM：内置零依赖实现（无需安装 ssim.js）
  try {
    const cmpMod = await import(
      pathToFileURL(path.resolve(__dirname, "compare-images.ts")).href
    );
    const { compareImages, compareImagesSSIM } = cmpMod;
    if (typeof compareImages === "function" && typeof compareImagesSSIM === "function") {
      const pixel = await compareImages(baseFile, renderFile);
      const ssimSim = await compareImagesSSIM(baseFile, renderFile);
      return {
        ...input,
        pixelSim: input.pixelSim ?? pixel.similarity,
        ssimSim: input.ssimSim ?? ssimSim,
        diffPixels: input.diffPixels ?? pixel.differencePixels,
        totalPixels: input.totalPixels ?? pixel.width * pixel.height,
      };
    }
  } catch (e) {
    console.warn(
      "[warn] 复用 compare-images 计算相似度失败，回退到内置逻辑：",
      (e as Error).message
    );
  }

  // —— 回退逻辑：直接用 jimp + pixelmatch + 内置 SSIM（仍不依赖 ssim.js）
  const jimpMod = safeRequire("jimp");
  if (!jimpMod) {
    console.warn("[warn] 未安装 jimp，跳过自动相似度计算（可手动通过 --pixel-sim 等参数传入）");
    return input;
  }
  const Jimp = jimpMod.Jimp ?? jimpMod.default ?? jimpMod;

  let pixelmatch: any;
  const pmMod = safeRequire("pixelmatch");
  if (pmMod) pixelmatch = pmMod.default ?? pmMod;
  else console.warn("[warn] 未安装 pixelmatch，跳过自动像素相似度计算");

  const a = await Jimp.read(baseFile);
  const b = await Jimp.read(renderFile);
  const w = Math.min(a.bitmap.width, b.bitmap.width);
  const h = Math.min(a.bitmap.height, b.bitmap.height);
  const resize = (im: any, ww: number, hh: number) => {
    if (im.bitmap.width === ww && im.bitmap.height === hh) return;
    if (typeof im.resize === "function") {
      try { im.resize({ w: ww, h: hh }); return; } catch {}
      try { im.resize(ww, hh); return; } catch {}
    }
  };
  resize(a, w, h);
  resize(b, w, h);

  const total = w * h;
  let pixelSim = input.pixelSim;
  let diffMatch = input.diffPixels;
  if (pixelmatch && (pixelSim == null || diffMatch == null)) {
    diffMatch = pixelmatch(a.bitmap.data, b.bitmap.data, null, w, h, { threshold: 0.1 });
    pixelSim = ((total - diffMatch!) / total) * 100;
  }

  // 内置 SSIM（8×8 分块，灰度），无需外部依赖
  let ssimSim = input.ssimSim;
  if (ssimSim == null) {
    ssimSim = computeSsimBuiltin(a.bitmap.data, b.bitmap.data, w, h);
  }

  return {
    ...input,
    pixelSim: pixelSim != null ? Number(pixelSim.toFixed(2)) : undefined,
    ssimSim: ssimSim != null ? Number(ssimSim.toFixed(2)) : undefined,
    diffPixels: diffMatch ?? input.diffPixels,
    totalPixels: input.totalPixels ?? total,
  };
}

/** 内置 SSIM（灰度、8×8 分块），与 compare-images.ts 保持一致，无需依赖 ssim.js */
function computeSsimBuiltin(
  d1: Buffer | Uint8Array,
  d2: Buffer | Uint8Array,
  width: number,
  height: number
): number {
  const BLOCK = 8;
  const C1 = 6.5025;
  const C2 = 58.5225;
  const blocksX = Math.floor(width / BLOCK);
  const blocksY = Math.floor(height / BLOCK);
  let totalSsim = 0;
  let blockCount = 0;

  for (let by = 0; by < blocksY; by++) {
    for (let bx = 0; bx < blocksX; bx++) {
      let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
      const pixels = BLOCK * BLOCK;
      for (let y = 0; y < BLOCK; y++) {
        for (let x = 0; x < BLOCK; x++) {
          const px = bx * BLOCK + x;
          const py = by * BLOCK + y;
          const idx = (py * width + px) * 4;
          const gx = d1[idx] * 0.299 + d1[idx + 1] * 0.587 + d1[idx + 2] * 0.114;
          const gy = d2[idx] * 0.299 + d2[idx + 1] * 0.587 + d2[idx + 2] * 0.114;
          sumX += gx; sumY += gy; sumXY += gx * gy;
          sumX2 += gx * gx; sumY2 += gy * gy;
        }
      }
      const meanX = sumX / pixels;
      const meanY = sumY / pixels;
      const varX = sumX2 / pixels - meanX * meanX;
      const varY = sumY2 / pixels - meanY * meanY;
      const covXY = sumXY / pixels - meanX * meanY;
      const ssim =
        ((2 * meanX * meanY + C1) * (2 * covXY + C2)) /
        ((meanX * meanX + meanY * meanY + C1) * (varX + varY + C2));
      totalSsim += ssim;
      blockCount++;
    }
  }
  const avg = blockCount > 0 ? totalSsim / blockCount : 0;
  return parseFloat((avg * 100).toFixed(2));
}

/* ============== 工具函数 ============== */

function toDataUrl(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase().replace(".", "");
  const mime = ext === "jpg" ? "jpeg" : ext;
  const buf = fs.readFileSync(filePath);
  return `data:image/${mime};base64,${buf.toString("base64")}`;
}

function renderTemplate(tpl: string, vars: Record<string, string>): string {
  return tpl.replace(/\{\{([A-Z_]+)\}\}/g, (_, k) => (vars[k] ?? ""));
}

function getTone(score?: number): "ok" | "warn" | "bad" {
  if (score == null) return "bad";
  if (score >= 95) return "ok";
  if (score >= 85) return "warn";
  return "bad";
}
function getVerdict(score?: number): string {
  if (score == null) return "未评估";
  if (score >= 95) return "合格";
  if (score >= 85) return "需改进";
  return "不合格";
}

function fmtPct(v?: number): string { return v == null ? "—" : `${v.toFixed(2)}%`; }
function fmtInt(v?: number): string { return v == null ? "—" : v.toLocaleString(); }
function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* ============== 渲染诊断 section ============== */

/**
 * 从自动检测的差异点里聚合出「待改进」条目（区块清单未标 issue 时的兜底来源）。
 * 只纳入 fixable 的问题类差异点：位置偏移（offset）、颜色 / 背景差异（color）。
 * 按类型 + 区块归并，避免逐点罗列。
 */
function aggregateFixableIssues(diffRegions?: any[]): ColRow[] {
  if (!diffRegions || diffRegions.length === 0) return [];
  const items: ColRow[] = [];

  const offsets = diffRegions.filter((r) => r.kind === "offset");
  const median = (arr: number[]) =>
    arr.length ? arr.slice().sort((a, b) => a - b)[Math.floor(arr.length / 2)] : 0;
  const uniqNames = (list: any[]) =>
    Array.from(new Set(list.map((r) => r.regionName).filter(Boolean)));

  // —— 横向位置偏移：优先呈现（多为左侧栏 / 容器宽度不符导致右侧整体横移）
  const horiz = offsets.filter((r) => Math.abs(Number(r.offsetX) || 0) >= 3);
  if (horiz.length > 0) {
    const absDxs = horiz.map((r) => Math.abs(Number(r.offsetX) || 0));
    const dirs = horiz.map((r) => (Number(r.offsetX) > 0 ? "左" : "右"));
    const sameDir = new Set(dirs).size === 1;
    const names = uniqNames(horiz);
    const scope = names.length
      ? `集中于 ${names.map((n) => escapeHtml(String(n))).join("、")}`
      : `共 ${horiz.length} 处结构块`;
    items.push(
      `<strong>横向位置偏移</strong>：检测到 ${horiz.length} 处区域内容一致但横向错位` +
        `（典型约 ${median(absDxs)}px，最大约 ${Math.max(...absDxs)}px，${scope}）` +
        `${sameDir ? `，且方向一致（整体偏${dirs[0]}）` : ""}，` +
        `多为<strong>左侧栏 / 上游容器宽度与设计稿不符</strong>导致右侧内容整体横移，` +
        `建议优先核对列宽 / 容器宽度（如侧边栏宽度）后重排。`
    );
  }

  // —— 纵向位置偏移：汇总为一条，列出涉及区块与最大偏移量
  const vert = offsets.filter(
    (r) => Math.abs(Number(r.offsetY) || 0) >= 3 && Math.abs(Number(r.offsetX) || 0) < 3
  );
  if (vert.length > 0) {
    const absDys = vert.map((r) => Math.abs(Number(r.offsetY) || 0));
    const names = uniqNames(vert);
    const scope = names.length
      ? `集中于 ${names.map((n) => escapeHtml(String(n))).join("、")}`
      : `共 ${vert.length} 处文本 / 结构块`;
    items.push(
      `<strong>纵向位置偏移</strong>：检测到 ${vert.length} 处区域内容一致但纵向错位` +
        `（典型约 ${median(absDys)}px，最大约 ${Math.max(...absDys)}px，${scope}），呈自上而下累计特征，` +
        `建议核对上游区块的高度 / 内外边距，改用相对布局消除累计误差。`
    );
  }

  // —— 颜色 / 背景差异：按区块归并
  const colors = diffRegions.filter((r) => r.kind === "color");
  if (colors.length > 0) {
    const names = Array.from(
      new Set(colors.map((r) => r.regionName).filter(Boolean))
    );
    const scope = names.length
      ? names.map((n) => escapeHtml(String(n))).join("、")
      : `${colors.length} 处区域`;
    items.push(
      `<strong>颜色 / 背景差异</strong>：${scope} 的整体色值与设计稿存在偏差，建议核对背景色 / 填充色 token。`
    );
  }

  return items;
}

/** § 一句话结论 */
function renderSummarySection(input: ReportInput, scoreTotal?: number, diffRegions?: any[]): {
  summaryHtml: string;
  winsHtml: string;
  issuesBriefHtml: string;
} {
  // ① summary
  let summaryHtml = "";
  if (input.summaryFile && fs.existsSync(input.summaryFile)) {
    summaryHtml = fs.readFileSync(input.summaryFile, "utf8");
  } else if (input.summary) {
    summaryHtml = input.summary;
  } else {
    // 自动生成：根据相似度 + region 数量
    const tone = getTone(scoreTotal);
    const score = scoreTotal != null ? `${scoreTotal.toFixed(2)}%` : "未评估";
    const regions = input.regions ?? [];
    const compRewrite = regions.filter(r => r.strategy === "component-rewrite").length;
    const imgWarn = regions.filter(r => r.strategy === "image-restore-warn").length;
    const issues = regions.filter(r => r.strategy === "issue").length;
    const total = regions.length;

    const regionStat = total > 0
      ? `共识别 ${total} 个区块：${compRewrite} 个组件化重写${imgWarn ? ` / ${imgWarn} 个图片还原 + 强制告知` : ""}${issues ? ` / ${issues} 处需修复问题` : ""}`
      : "（未提供区块清单数据）";

    // 自动检测差异点的关键结论（偏移 / 颜色），并入一句话总结
    const offsetPts = (diffRegions ?? []).filter((r) => r.kind === "offset");
    const colorPts = (diffRegions ?? []).filter((r) => r.kind === "color");
    const median = (arr: number[]) =>
      arr.length ? arr.slice().sort((a, b) => a - b)[Math.floor(arr.length / 2)] : 0;
    const detectHints: string[] = [];
    // 横向偏移优先（多指向左侧栏 / 容器宽度问题，是最需要关注的结构性偏差）
    const horizPts = offsetPts.filter((r) => Math.abs(Number(r.offsetX) || 0) >= 3);
    if (horizPts.length > 0) {
      const m = median(horizPts.map((r) => Math.abs(Number(r.offsetX) || 0)));
      detectHints.push(
        `<strong>${horizPts.length} 处横向位置偏移</strong>（典型约 ${m}px，疑似左侧栏 / 容器宽度不符）`
      );
    }
    const vertPts = offsetPts.filter(
      (r) => Math.abs(Number(r.offsetY) || 0) >= 3 && Math.abs(Number(r.offsetX) || 0) < 3
    );
    if (vertPts.length > 0) {
      const m = median(vertPts.map((r) => Math.abs(Number(r.offsetY) || 0)));
      detectHints.push(`<strong>${vertPts.length} 处纵向位置偏移</strong>（典型约 ${m}px，呈累计特征）`);
    }
    if (colorPts.length > 0) detectHints.push(`${colorPts.length} 处颜色 / 背景差异`);
    const detectStat = detectHints.length ? `自动检测发现 ${detectHints.join("、")}` : "";

    const verdict =
      tone === "ok"   ? `本次还原达到 <strong>${score}</strong> 加权相似度，结果优秀，可直接交付。` :
      tone === "warn" ? `本次还原 <strong>${score}</strong>，结果合格但需关注偏差区域。` :
                        `本次还原 <strong>${score}</strong>，未达交付标准，建议根据下方"待改进"项继续优化。`;

    summaryHtml = `${verdict} ${regionStat}${detectStat ? `；${detectStat}` : ""}。详见下方 <strong>差异点分布（自动检测）</strong>。`;
  }

  // ② wins / issuesBrief（默认从 regions 推断）
  const regions = input.regions ?? [];
  const autoWins: ColRow[] = [];
  const autoIssues: ColRow[] = [];
  for (const r of regions) {
    if (r.strategy === "component-rewrite") {
      autoWins.push(`<strong>${escapeHtml(r.name)}</strong>：${escapeHtml(r.msg)}`);
    } else if (r.strategy === "image-restore-warn" || r.strategy === "issue") {
      autoIssues.push(`<strong>${escapeHtml(r.name)}</strong>：${escapeHtml(r.msg)}`);
    }
  }
  // 兜底：区块清单未标记 issue 时，从自动检测的差异点聚合可修复问题（偏移 / 颜色）
  for (const it of aggregateFixableIssues(diffRegions)) autoIssues.push(it);

  if (autoWins.length === 0 && (input.pixelSim ?? 0) >= 95) {
    autoWins.push(`视觉还原度 <strong>${fmtPct(scoreTotal)}</strong>（像素 ${fmtPct(input.pixelSim)} / SSIM ${fmtPct(input.ssimSim)}）`);
  }
  if (autoWins.length === 0) autoWins.push("（暂无亮点数据）");
  if (autoIssues.length === 0) autoIssues.push("（无明显待改进项）");

  const wins = input.wins ?? autoWins;
  const issuesBrief = input.issuesBrief ?? autoIssues;

  return {
    summaryHtml,
    winsHtml: wins.map(s => `<li>${s}</li>`).join("\n"),
    issuesBriefHtml: issuesBrief.map(s => `<li>${s}</li>`).join("\n"),
  };
}

/** § 给设计师的画稿建议 */
function renderDesignAdviceSection(input: ReportInput): {
  toneTag: string;
  summary: string;
  problemsHtml: string;
  solutionsHtml: string;
} {
  const advice =
    input.designAdvice ??
    (input.designAdviceFile && fs.existsSync(input.designAdviceFile)
      ? JSON.parse(fs.readFileSync(input.designAdviceFile, "utf8"))
      : undefined);

  const regions = input.regions ?? [];
  const warnRegions = regions.filter(r =>
    r.strategy === "image-restore-warn" || r.strategy === "issue"
  );

  // 自动推断：当有 warn / issue 区块且用户没传 designAdvice 时
  const toneTag = advice?.toneTag ?? (warnRegions.length > 0 ? "请反馈给设计同学" : "已达组件化最佳实践");
  const summary =
    advice?.summary ??
    (warnRegions.length > 0
      ? `下面给出当前稿件的具体问题和修改后的收益预期，建议以这份对比作为反馈给设计师的依据。`
      : `本次设计稿质量良好，所有可识别区块都成功走了组件化重写分支。`);

  const autoProblems: ColRow[] = warnRegions.map(r =>
    `<strong>${escapeHtml(r.name)}</strong>：${escapeHtml(r.msg)}`
  );
  const autoSolutions: ColRow[] = warnRegions.length > 0
    ? [
        "在 Figma 中将各功能区都用<strong>独立的 Frame 或 Component</strong> 搭建，而不是整体导出为 PNG",
        "给每个组件节点添加 <span class=\"code\">data-name</span> 或 <span class=\"code\">data-component-name</span>（如 <span class=\"code\">data-name=\"Card/卡片名\"</span>）",
        "字段/文案/状态/按钮等都保持为<strong>独立矢量文本节点 + Auto Layout</strong>，避免合并为图片",
        "调整设计稿后重新运行 D2C，可获得 95%+ 视觉还原度的同时保留完整的组件化结构",
      ]
    : ["（无需修改）"];

  const problems = advice?.problems ?? (autoProblems.length > 0 ? autoProblems : ["（无明显问题）"]);
  const solutions = advice?.solutions ?? autoSolutions;

  return {
    toneTag,
    summary,
    problemsHtml: problems.map(s => `<li>${s}</li>`).join("\n"),
    solutionsHtml: solutions.map(s => `<li>${s}</li>`).join("\n"),
  };
}

/** § 差异点分布（自动检测） */
function renderDiffPointsSection(diffRegions: any[] | undefined, renderImgUrl: string): string {
  if (!diffRegions || diffRegions.length === 0) return "";

  // 差异类型 → 配色 / 兜底标签（无 kind 时按严重度回退）
  const KIND_META: Record<string, { label: string; cls: string }> = {
    text:   { label: "字体渲染差异", cls: "info" },
    image:  { label: "配图差异",     cls: "warning" },
    color:  { label: "颜色 / 背景差异", cls: "error" },
    edge:   { label: "抗锯齿边缘",   cls: "muted" },
    offset: { label: "位置偏移",     cls: "error" },
  };
  const SEV_FALLBACK: Record<string, { label: string; cls: string }> = {
    high:   { label: "明显差异", cls: "error" },
    medium: { label: "部分差异", cls: "warning" },
    low:    { label: "细微差异", cls: "muted" },
  };
  const metaOf = (r: any) => {
    const base =
      (r.kind && KIND_META[r.kind]) ||
      { label: SEV_FALLBACK[r.severity]?.label || "差异", cls: SEV_FALLBACK[r.severity]?.cls || "info" };
    // 具体标签（如「横向位置偏移」/「纵向位置偏移」）优先于 kind 的默认标签，配色仍按 kind
    return { label: r.kindLabel || base.label, cls: base.cls };
  };

  const hotspots = diffRegions.map((r, i) => {
    const meta = metaOf(r);
    const style = `left: ${r.bbox.left}; top: ${r.bbox.top}; width: ${r.bbox.width}; height: ${r.bbox.height};`;
    const tip =
      `#${i + 1} ${r.regionName ? r.regionName + " · " : ""}${meta.label}\n` +
      `${r.reason || ""}\n` +
      `位置 左${r.bbox.left} / 上${r.bbox.top} · 差异占比 ${(Number(r.ratio) * 100).toFixed(1)}%`;
    return `        <div class="diff-point ${meta.cls}" data-idx="${i + 1}" style="${style}" title="${escapeHtml(tip)}"></div>`;
  }).join("\n");

  const rows = diffRegions.map((r, i) => {
    const meta = metaOf(r);
    const region = r.regionName ? escapeHtml(r.regionName) : '<span class="dp-muted-text">全局 / 未归类</span>';
    const reason = escapeHtml(r.reason || "—");
    return `      <tr class="dp-row" data-idx="${i + 1}">
        <td>${i + 1}</td>
        <td><span class="issue-rule-tag ${meta.cls}">${escapeHtml(meta.label)}</span></td>
        <td class="dp-region">${region}</td>
        <td class="dp-reason">${reason}</td>
        <td class="dp-bbox">左 ${r.bbox.left} · 上 ${r.bbox.top}</td>
        <td>${(Number(r.ratio) * 100).toFixed(1)}%</td>
      </tr>`;
  }).join("\n");

  return `
      <!-- ④-bis 差异点分布（自动检测） -->
      <div class="snapshot-section">
        <div class="section-header">
          <div>
            <h2 class="section-title">差异点分布（自动检测）</h2>
            <div class="section-desc">基于像素对比自动识别的还原差异区域，共 ${diffRegions.length} 处，并已按「所在区块 + 像素特征」推断差异类型与原因。鼠标悬停查看详情，点击可联动高亮。</div>
          </div>
        </div>
        <div class="snapshot-wrap">
          <div class="snapshot-inner" id="dpInner">
            <img src="${renderImgUrl}" alt="渲染结果" />
${hotspots}
          </div>
        </div>
        <div class="legend">
          <span><span class="legend-dot" style="background: var(--brand)"></span>字体渲染差异（系统字体回退）</span>
          <span><span class="legend-dot" style="background: var(--warning)"></span>配图差异（位图缩放采样）</span>
          <span><span class="legend-dot" style="background: var(--error)"></span>颜色 / 背景差异 · 位置偏移（结构错位，需修复）</span>
          <span><span class="legend-dot" style="background: var(--text-3)"></span>抗锯齿边缘（肉眼几乎不可见）</span>
        </div>
        <div class="issues-card" style="margin-top: 16px;">
          <h2 class="section-title" style="margin-bottom: 12px;">差异点清单</h2>
          <table class="dp-table">
            <thead><tr><th>#</th><th>差异类型</th><th>所在区块</th><th>可能原因</th><th>位置</th><th>占比</th></tr></thead>
            <tbody>
${rows}
            </tbody>
          </table>
        </div>
      </div>
      <script>
      (function () {
        var inner = document.getElementById("dpInner");
        if (!inner) return;
        var points = inner.querySelectorAll(".diff-point");
        var rows = document.querySelectorAll(".dp-row");
        var current = null;
        function highlight(idx, opts) {
          opts = opts || {};
          // 再次点击同一项则取消选中
          if (current === idx) idx = null;
          current = idx;
          inner.classList.toggle("dp-focused", idx != null);
          points.forEach(function (p) {
            p.classList.toggle("is-hit", idx != null && p.getAttribute("data-idx") === idx);
          });
          rows.forEach(function (r) {
            r.classList.toggle("dp-active", idx != null && r.getAttribute("data-idx") === idx);
          });
          if (idx == null) return;
          if (opts.scrollRow) {
            var row = document.querySelector('.dp-row[data-idx="' + idx + '"]');
            if (row) row.scrollIntoView({ behavior: "smooth", block: "center" });
          }
          if (opts.scrollPoint) {
            var pt = inner.querySelector('.diff-point[data-idx="' + idx + '"]');
            if (pt) pt.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        }
        // 点击图上差异框 → 高亮并把对应清单行滚动到可视区
        points.forEach(function (p) {
          p.addEventListener("click", function () {
            highlight(p.getAttribute("data-idx"), { scrollRow: true });
          });
        });
        // 点击清单行 → 高亮并把对应差异框滚动到可视区
        rows.forEach(function (r) {
          r.addEventListener("click", function () {
            highlight(r.getAttribute("data-idx"), { scrollPoint: true });
          });
        });
      })();
      </script>`;
}

/* ============== 主流程 ============== */

async function main() {
  const argv = process.argv.slice(2);
  let input: ReportInput;
  try { input = parseCli(argv); }
  catch (e) { console.error((e as Error).message); process.exit(1); return; }

  const base = path.resolve(input.base);
  const render = path.resolve(input.render);
  const diff = input.diff ? path.resolve(input.diff) : undefined;
  if (!fs.existsSync(base)) throw new Error(`base 不存在：${base}`);
  if (!fs.existsSync(render)) throw new Error(`render 不存在：${render}`);
  if (diff && !fs.existsSync(diff)) {
    console.warn(`[warn] diff 不存在：${diff}，将跳过 diff 模式`);
  }

  input = await computeSimIfNeeded(base, render, input);

  // —— 自动检测差异点（还原存在差异的点是哪些）
  let diffRegions = input.diffRegions;
  if (!diffRegions && !input.noDiffPoints && fs.existsSync(base) && fs.existsSync(render)) {
    try {
      const detMod = await import(pathToFileURL(path.resolve(__dirname, "detect-diff-regions.ts")).href);
      diffRegions = await detMod.detectDiffRegions(base, render, {
        maxRegions: 40,
        colorThreshold: 40,
        regions: input.regions,
      });
    } catch (e) {
      console.warn("[warn] 自动差异点检测跳过：", (e as Error).message);
    }
  }

  const out = path.resolve(
    input.out ?? path.join(path.dirname(base), "visual-diff-report.html")
  );

  const tplCandidates = [
    path.resolve(__dirname, "../template/visual-diff-viewer.html"),
    path.resolve(__dirname, "./visual-diff-viewer.html"),
    path.resolve(process.cwd(), "template/visual-diff-viewer.html"),
  ];
  const tplPath = tplCandidates.find(fs.existsSync);
  if (!tplPath) {
    throw new Error(
      "找不到 visual-diff-viewer.html 模板。请放在以下任一路径：\n  " +
        tplCandidates.join("\n  ")
    );
  }
  const tpl = fs.readFileSync(tplPath, "utf8");

  const baseUrl = toDataUrl(base);
  const renderUrl = toDataUrl(render);
  const diffUrl = diff && fs.existsSync(diff) ? toDataUrl(diff) : renderUrl;

  let imgSize = "—";
  try {
    const m = safeRequire("jimp");
    if (m) {
      const Jimp = m.Jimp ?? m.default ?? m;
      const im = await Jimp.read(base);
      imgSize = `${im.bitmap.width}×${im.bitmap.height}`;
    }
  } catch {}

  const score =
    input.pixelSim != null && input.ssimSim != null
      ? input.pixelSim * 0.7 + input.ssimSim * 0.3
      : input.pixelSim;

  const meta: string[] = [];
  if (input.sourceUrl) {
    meta.push(`来源：<a href="${input.sourceUrl}" target="_blank">${input.sourceUrl}</a>`);
  }
  meta.push(`生成于 ${new Date().toLocaleString("zh-CN")}`);

  // —— 渲染 4 个诊断 section
  const summary = renderSummarySection(input, score, diffRegions);
  const advice = renderDesignAdviceSection(input);
  const diffPointsHtml = renderDiffPointsSection(diffRegions, renderUrl);

  const html = renderTemplate(tpl, {
    TITLE: input.title ?? "视觉还原度报告",
    META_HTML: meta.join("&nbsp;·&nbsp;"),
    VERDICT: getVerdict(score),
    SCORE_TOTAL: score == null ? "—" : score.toFixed(2),
    SCORE_TONE: getTone(score),
    PIXEL_SIM: fmtPct(input.pixelSim),
    SSIM_SIM: fmtPct(input.ssimSim),
    DIFF_PIXELS: fmtInt(input.diffPixels),
    TOTAL_PIXELS: fmtInt(input.totalPixels),
    IMG_SIZE: imgSize,
    LEFT_LABEL: input.leftLabel ?? "DESIGN",
    RIGHT_LABEL: input.rightLabel ?? "RENDER",
    BASE_IMG: baseUrl,
    RENDER_IMG: renderUrl,
    DIFF_IMG: diffUrl,

    // 诊断 sections
    SUMMARY_HTML: summary.summaryHtml,
    WINS_HTML: summary.winsHtml,
    ISSUES_BRIEF_HTML: summary.issuesBriefHtml,
    ADVICE_TONE_TAG: advice.toneTag,
    ADVICE_SUMMARY_HTML: advice.summary,
    ADVICE_PROBLEMS_HTML: advice.problemsHtml,
    ADVICE_SOLUTIONS_HTML: advice.solutionsHtml,
    DIFF_POINTS_HTML: diffPointsHtml,

    EXTRA_HTML: input.extraHtml ?? "",
    GENERATED_AT: new Date().toLocaleString("zh-CN"),
    SOURCE_PATH: path.relative(process.cwd(), base),
  });

  fs.writeFileSync(out, html, "utf8");
  console.log("✓ 报告已生成：", out);
  console.log("  尺寸：", imgSize);
  if (score != null) console.log("  加权相似度：", score.toFixed(2) + "%");
  if (input.pixelSim != null) console.log("  像素相似度：", input.pixelSim.toFixed(2) + "%");
  if (input.ssimSim != null) console.log("  SSIM：", input.ssimSim.toFixed(2) + "%");
  console.log("  区块清单：", (input.regions ?? []).length, "个");
  console.log("  差异点（自动检测）：", (diffRegions ?? []).length, "处");
}

main().catch((e) => {
  console.error("✗ 报告生成失败：", e);
  process.exit(1);
});
