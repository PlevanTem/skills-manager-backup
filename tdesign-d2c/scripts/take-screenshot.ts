import { createRequire } from "node:module";
import * as path from "node:path";
import * as fs from "node:fs";

interface Args {
  url: string;
  selector: string;
  out: string;
  width?: number;
  height?: number;
  viewportWidth: number;
  viewportHeight: number;
  deviceScaleFactor: number;
  waitUntil: "load" | "domcontentloaded" | "networkidle";
  waitMs: number;
}

function parseCli(argv: string[]): Args {
  const dict: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const k = a.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      dict[k] = "true";
    } else {
      dict[k] = next;
      i++;
    }
  }
  if (!dict.url) throw new Error("缺少 --url");
  if (!dict.selector) throw new Error("缺少 --selector（要截图的 DOM 节点选择器）");
  if (!dict.out) throw new Error("缺少 --out（输出 PNG 路径）");
  return {
    url: dict.url,
    selector: dict.selector,
    out: dict.out,
    width: dict.width ? Number(dict.width) : undefined,
    height: dict.height ? Number(dict.height) : undefined,
    viewportWidth: dict["viewport-width"] ? Number(dict["viewport-width"]) : 1440,
    viewportHeight: dict["viewport-height"] ? Number(dict["viewport-height"]) : 900,
    deviceScaleFactor: dict["device-scale-factor"] ? Number(dict["device-scale-factor"]) : 1,
    waitUntil: (dict["wait-until"] as Args["waitUntil"]) || "networkidle",
    waitMs: dict["wait-ms"] ? Number(dict["wait-ms"]) : 0,
  };
}

/** 同 generate-diff-report.ts，优先从用户项目 cwd 解析 playwright */
function loadPlaywright(): any {
  const tryPaths: Array<() => any> = [
    () => createRequire(path.join(process.cwd(), "package.json"))("playwright"),
    () => require("playwright"),
  ];
  for (const t of tryPaths) {
    try {
      return t();
    } catch {
      /* fallthrough */
    }
  }
  throw new Error(
    "未能加载 playwright。请在用户项目目录执行：\n  npm i -D playwright\n  npx playwright install chromium"
  );
}

async function main() {
  const args = parseCli(process.argv.slice(2));
  const { chromium } = loadPlaywright();

  const outDir = path.dirname(path.resolve(args.out));
  fs.mkdirSync(outDir, { recursive: true });

  console.log(`▶ 启动 chromium ...`);
  const browser = await chromium.launch();
  try {
   
    const viewportWidth = args.width ?? args.viewportWidth;
    // 视口高度撑到至少覆盖目标 clip 高度，配合 fullPage 截图，避免长图只截首屏
    const viewportHeight = Math.max(args.viewportHeight, args.height ?? 0);
    const context = await browser.newContext({
      viewport: { width: viewportWidth, height: viewportHeight },
      deviceScaleFactor: args.deviceScaleFactor,
    });
    const page = await context.newPage();
    console.log(`▶ goto ${args.url}`);
    await page.goto(args.url, { waitUntil: args.waitUntil });
    if (args.waitMs > 0) await page.waitForTimeout(args.waitMs);

    const el = await page.$(args.selector);
    if (!el) {
      throw new Error(
        `找不到节点 selector=${args.selector}。请确认选择器是否正确，或在被截元素加上 data-screenshot-root 标记。`
      );
    }
    const box = await el.boundingBox();
    if (!box) throw new Error("无法获取目标节点的 boundingBox（节点可能不可见）。");

    const clip = {
      x: Math.round(box.x),
      y: Math.round(box.y),
      width: args.width ?? Math.round(box.width),
      height: args.height ?? Math.round(box.height),
    };
    // fullPage: true 让 Playwright 渲染整个可滚动页面后再按 clip 裁剪，
    console.log(`▶ screenshot fullPage clip=${JSON.stringify(clip)}`);
    await page.screenshot({ path: args.out, clip, fullPage: true });
    console.log(`✓ 已保存：${args.out}`);
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error("✗ 截图失败：", e instanceof Error ? e.message : e);
  process.exit(1);
});
