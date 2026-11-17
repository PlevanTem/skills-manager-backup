#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量验证 / 版本 diff 工具（Tenchage-ppt v3.1 P2 能力）

用途：在 PPT 多次迭代中，快速看清「这一稿和上一稿差在哪几页」，避免回归走样。

用法：
  # 单一 PPTX 全页截图（与 qa_screenshot.py 等价，但带索引页）
  python batch_diff.py snapshot <input.pptx> [--out out_dir/]

  # 双 PPTX 版本 diff（生成对比报告）
  python batch_diff.py diff <old.pptx> <new.pptx> [--out diff_report/]

  # 双截图目录 diff（如已有截图，跳过 LibreOffice 渲染）
  python batch_diff.py diff-imgs <old_dir/> <new_dir/> [--out diff_report/]

输出：
  diff_report/
    ├── index.html              ← 总览页（点击进入每页对比）
    ├── page_001.png            ← 旧 | 新 | diff 三联图
    └── summary.json            ← 结构化报告

依赖：Pillow（pip install Pillow）+ LibreOffice（snapshot/diff 模式需要）
"""
import sys
import os
import json
import shutil
import subprocess
import argparse
from pathlib import Path


# ============== Step 1: PPTX -> PNG ==============

def pptx_to_pngs(pptx_path: Path, out_dir: Path) -> list:
    """用 LibreOffice 把 PPTX 转 PDF，再用 pdftoppm 拆成每页 PNG。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / (pptx_path.stem + ".pdf")

    # 1. PPTX -> PDF
    soffice = _find_soffice()
    if not soffice:
        raise RuntimeError("找不到 LibreOffice (soffice)，请先安装 LibreOffice")
    subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                    "--outdir", str(out_dir), str(pptx_path)],
                   check=True, capture_output=True, timeout=120)

    # 2. PDF -> PNG（一页一张）
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", "120",
                        str(pdf_path), str(out_dir / "page")],
                       check=True, capture_output=True)
        return sorted(out_dir.glob("page-*.png"))
    else:
        # 回退：用 pypdfium2 或 PyMuPDF
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            pngs = []
            for i, page in enumerate(doc, 1):
                pix = page.get_pixmap(dpi=120)
                p = out_dir / f"page-{i:03d}.png"
                pix.save(str(p))
                pngs.append(p)
            doc.close()
            return pngs
        except ImportError:
            raise RuntimeError("找不到 pdftoppm，请安装 poppler 或 pip install PyMuPDF")


def _find_soffice() -> str:
    candidates = [
        "soffice", "libreoffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    for c in candidates:
        if shutil.which(c) or Path(c).exists():
            return c
    return ""


# ============== Step 2: 像素 diff ==============

def diff_two_images(img_a: Path, img_b: Path, out_path: Path) -> dict:
    """对比两张 PNG，输出三联图 (旧|新|diff)。返回相似度统计。"""
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError("pip install Pillow")

    a = Image.open(img_a).convert("RGB")
    b = Image.open(img_b).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)

    # 计算 diff
    d = ImageChops.difference(a, b)
    bbox = d.getbbox()
    pixels_diff = sum(1 for px in d.getdata() if any(c > 10 for c in px))
    total_pixels = a.size[0] * a.size[1]
    diff_ratio = pixels_diff / total_pixels if total_pixels else 0

    # 在 diff 图上画红框标出变化区域
    diff_vis = b.copy()
    if bbox:
        draw = ImageDraw.Draw(diff_vis)
        draw.rectangle(bbox, outline="red", width=4)

    # 拼三联图
    w, h = a.size
    canvas = Image.new("RGB", (w * 3 + 20, h + 40), "white")
    canvas.paste(a, (0, 30))
    canvas.paste(b, (w + 10, 30))
    canvas.paste(diff_vis, (w * 2 + 20, 30))

    # 加标签
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 5), "OLD", fill="black")
    draw.text((w + 20, 5), "NEW", fill="black")
    draw.text((w * 2 + 30, 5), f"DIFF ({diff_ratio:.2%})", fill="red")

    canvas.save(out_path)
    return {"diff_ratio": diff_ratio, "bbox": bbox, "changed": diff_ratio > 0.001}


# ============== Step 3: 对比报告 ==============

def diff_dirs(old_dir: Path, new_dir: Path, out_dir: Path) -> dict:
    """对两个截图目录做逐页 diff，生成 HTML 报告。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    old_pngs = sorted(old_dir.glob("page-*.png"))
    new_pngs = sorted(new_dir.glob("page-*.png"))

    n = max(len(old_pngs), len(new_pngs))
    summary = {"total_pages": n, "changed_pages": [], "added": [], "removed": [], "items": []}

    for i in range(n):
        page_no = i + 1
        old_p = old_pngs[i] if i < len(old_pngs) else None
        new_p = new_pngs[i] if i < len(new_pngs) else None

        if old_p is None:
            summary["added"].append(page_no)
            shutil.copy(str(new_p), str(out_dir / f"page_{page_no:03d}_NEW_ONLY.png"))
            summary["items"].append({"page": page_no, "status": "added"})
        elif new_p is None:
            summary["removed"].append(page_no)
            shutil.copy(str(old_p), str(out_dir / f"page_{page_no:03d}_OLD_ONLY.png"))
            summary["items"].append({"page": page_no, "status": "removed"})
        else:
            out_png = out_dir / f"page_{page_no:03d}.png"
            stat = diff_two_images(old_p, new_p, out_png)
            if stat["changed"]:
                summary["changed_pages"].append(page_no)
            summary["items"].append({"page": page_no, "status": "changed" if stat["changed"] else "same",
                                     "diff_ratio": stat["diff_ratio"]})

    # 写报告
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _render_html(out_dir, summary)

    print(f"\n📊 Diff 完成：")
    print(f"   总页数：{summary['total_pages']}")
    print(f"   变化页：{len(summary['changed_pages'])}（{summary['changed_pages']}）")
    print(f"   新增页：{len(summary['added'])}")
    print(f"   删除页：{len(summary['removed'])}")
    print(f"   报告路径：{out_dir / 'index.html'}")
    return summary


def _render_html(out_dir: Path, summary: dict):
    rows = []
    for item in summary["items"]:
        page = item["page"]
        status = item["status"]
        if status == "added":
            img = f"page_{page:03d}_NEW_ONLY.png"
            badge = '<span style="background:#00A45D;color:white;padding:2px 8px;border-radius:4px">新增</span>'
        elif status == "removed":
            img = f"page_{page:03d}_OLD_ONLY.png"
            badge = '<span style="background:#86909C;color:white;padding:2px 8px;border-radius:4px">删除</span>'
        elif status == "changed":
            img = f"page_{page:03d}.png"
            ratio = item.get("diff_ratio", 0)
            badge = f'<span style="background:#1A50D6;color:white;padding:2px 8px;border-radius:4px">变化 {ratio:.1%}</span>'
        else:
            img = f"page_{page:03d}.png"
            badge = '<span style="background:#E5EBF5;color:#86909C;padding:2px 8px;border-radius:4px">未变</span>'
        rows.append(f"""
        <div class="row">
          <h3>第 {page} 页 {badge}</h3>
          <img src="{img}" alt="page {page}" loading="lazy">
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>Tenchage-ppt Diff Report</title>
<style>
body {{ font-family: "Microsoft YaHei",sans-serif; background:#F4F5F7; margin:0; padding:24px; }}
h1 {{ color:#1A50D6; }}
.summary {{ background:white; padding:16px 20px; border-radius:8px; margin-bottom:24px;
            border-left:4px solid #1A50D6; }}
.row {{ background:white; padding:16px; margin-bottom:16px; border-radius:8px;
        box-shadow:0 2px 6px rgba(0,0,0,.05); }}
.row img {{ max-width:100%; border:1px solid #E5EBF5; border-radius:4px; }}
h3 {{ margin:0 0 12px; color:#1D2129; }}
</style></head><body>
<h1>📊 Tenchage-ppt Diff Report</h1>
<div class="summary">
  <p>总页数：<b>{summary['total_pages']}</b> | 变化页：<b style="color:#1A50D6">{len(summary['changed_pages'])}</b>
  | 新增：<b style="color:#00A45D">{len(summary['added'])}</b>
  | 删除：<b style="color:#86909C">{len(summary['removed'])}</b></p>
  <p>变化页码：{summary['changed_pages'] or '无'}</p>
</div>
{"".join(rows)}
</body></html>"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")


# ============== CLI ==============

def main():
    parser = argparse.ArgumentParser(description="Tenchage-ppt v3.1 批量验证 / Diff 工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_snap = sub.add_parser("snapshot", help="单 PPTX 全页截图")
    p_snap.add_argument("pptx")
    p_snap.add_argument("--out", default="snapshot")

    p_diff = sub.add_parser("diff", help="双 PPTX 版本对比")
    p_diff.add_argument("old_pptx")
    p_diff.add_argument("new_pptx")
    p_diff.add_argument("--out", default="diff_report")

    p_diff_imgs = sub.add_parser("diff-imgs", help="双截图目录对比")
    p_diff_imgs.add_argument("old_dir")
    p_diff_imgs.add_argument("new_dir")
    p_diff_imgs.add_argument("--out", default="diff_report")

    args = parser.parse_args()

    if args.cmd == "snapshot":
        out = Path(args.out).resolve()
        pngs = pptx_to_pngs(Path(args.pptx).resolve(), out)
        print(f"✅ 已生成 {len(pngs)} 张截图于 {out}")
    elif args.cmd == "diff":
        out = Path(args.out).resolve()
        old_dir = out / "_old"
        new_dir = out / "_new"
        pptx_to_pngs(Path(args.old_pptx).resolve(), old_dir)
        pptx_to_pngs(Path(args.new_pptx).resolve(), new_dir)
        diff_dirs(old_dir, new_dir, out)
    elif args.cmd == "diff-imgs":
        diff_dirs(Path(args.old_dir).resolve(), Path(args.new_dir).resolve(),
                  Path(args.out).resolve())


if __name__ == "__main__":
    main()
