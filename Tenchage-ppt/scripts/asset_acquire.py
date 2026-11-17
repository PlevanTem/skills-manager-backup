#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化资产获取（Tenchage-ppt v3.1 P0 能力）

用法：
  # 单条获取
  python asset_acquire.py --type logo --query "腾讯云" --output images/logo_tencent.png
  python asset_acquire.py --type screenshot --query "WorkBuddy 专家中心" --output images/screenshot_workbuddy_p3.png
  python asset_acquire.py --type bg --prompt "深蓝色科技感渐变背景" --output images/bg_p1_tech.png

  # 从 JSON 批量获取（扫描 ppt_data.json 中的 image / backgroundImage / logo 字段）
  python asset_acquire.py --batch ppt_data.json [--dir images/]

资产类型与策略：
  logo       优先 baoyu-imagine，失败回退到生成 SVG 占位
  screenshot 提示用户手动提供（不自动生成，避免误导）
  bg         调用 baoyu-imagine 文生图
  icon       调用 baoyu-imagine 文生图

命名规范（写入 JSON 时采用相对路径）：
  images/logo_<name>.<ext>
  images/screenshot_<product>_p<N>.<ext>
  images/bg_p<N>_<desc>.<ext>
  images/icon_<keyword>.<ext>
"""
import sys
import os
import json
import shutil
import subprocess
import argparse
from pathlib import Path


# ============== 后端 1：baoyu-imagine ==============

def gen_with_baoyu_imagine(prompt: str, output_path: Path, aspect: str = "16:9") -> bool:
    """调用 baoyu-imagine CLI 生成图片。返回 True 表示成功。"""
    cli_candidates = ["baoyu-imagine", "imagine", "baoyu-image-gen"]
    for cli in cli_candidates:
        if shutil.which(cli):
            try:
                cmd = [cli, "--prompt", prompt, "--output", str(output_path), "--aspect", aspect]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0 and output_path.exists():
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    return False


# ============== 后端 2：SVG 占位图 ==============

def gen_svg_placeholder(label: str, output_path: Path, width: int = 800, height: int = 450,
                       color: str = "#1A50D6") -> bool:
    """生成腾讯蓝绿风格 SVG 占位图，作为兜底。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#00A45D" stop-opacity="0.04"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#g)" stroke="{color}" stroke-width="2" stroke-dasharray="8,6"/>
  <g transform="translate({width//2},{height//2})">
    <text text-anchor="middle" y="-12" font-family="Microsoft YaHei,PingFang SC" font-size="22" font-weight="bold" fill="{color}">[占位图]</text>
    <text text-anchor="middle" y="22" font-family="Microsoft YaHei,PingFang SC" font-size="16" fill="#4E5969">{label}</text>
    <text text-anchor="middle" y="48" font-family="Microsoft YaHei,PingFang SC" font-size="11" fill="#86909C">请用 baoyu-imagine 替换</text>
  </g>
</svg>'''
    # 强制保存为 .svg；若用户传 .png 后缀，警告但保存为 svg
    if output_path.suffix.lower() != ".svg":
        new_path = output_path.with_suffix(".svg")
        print(f"⚠️  baoyu-imagine 不可用，已生成 SVG 占位：{new_path}（原请求 {output_path.name}）", file=sys.stderr)
        output_path = new_path
    output_path.write_text(svg, encoding="utf-8")
    return True


# ============== 主获取逻辑 ==============

def acquire_one(asset_type: str, query: str = "", prompt: str = "", output_path: str = "") -> str:
    """单条资产获取主入口。返回最终落盘路径。"""
    output_path = Path(output_path).resolve() if output_path else None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if asset_type == "screenshot":
        # 截图必须人工提供，自动生成会误导
        print(f"❌ screenshot 类型不支持自动生成。", file=sys.stderr)
        print(f"   请手动截图后保存到：{output_path}", file=sys.stderr)
        print(f"   建议来源：Snipaste / Windows+Shift+S / 产品官网", file=sys.stderr)
        return ""

    full_prompt = prompt or _build_prompt(asset_type, query)
    aspect = {"logo": "1:1", "icon": "1:1", "bg": "16:9"}.get(asset_type, "16:9")

    # Step 1: 尝试 baoyu-imagine
    if gen_with_baoyu_imagine(full_prompt, output_path, aspect=aspect):
        print(f"✅ 已生成（baoyu-imagine）：{output_path}")
        return str(output_path)

    # Step 2: 回退到 SVG 占位
    label = query or prompt[:20]
    gen_svg_placeholder(label, output_path)
    return str(output_path.with_suffix(".svg"))


def _build_prompt(asset_type: str, query: str) -> str:
    """根据资产类型构建生图 prompt。"""
    templates = {
        "logo": f"{query} 公司 logo，简洁，扁平化，白底，矢量风格，居中",
        "bg": f"{query}，腾讯科技蓝（#1A50D6）渐变背景，极简，无文字，宽屏 16:9，适合 PPT 背景",
        "icon": f"{query} 图标，扁平化，腾讯蓝绿色调，简洁，白底，居中",
    }
    return templates.get(asset_type, query)


# ============== 批量模式 ==============

def acquire_batch(json_path: str, dir_root: str = None) -> dict:
    """扫描 JSON 中所有 image/backgroundImage/logo 字段，逐一获取并就地写入相对路径。"""
    json_path = Path(json_path).resolve()
    data = json.loads(json_path.read_text(encoding="utf-8"))

    dir_root = Path(dir_root).resolve() if dir_root else json_path.parent / "images"
    dir_root.mkdir(parents=True, exist_ok=True)

    report = {"total": 0, "success": 0, "skipped": 0, "failed": 0, "items": []}

    slides = data.get("slides", [])
    for i, slide in enumerate(slides, 1):
        # 背景图
        bg_query = slide.get("backgroundImage")
        if isinstance(bg_query, str) and not bg_query.startswith(("images/", "http", "/")):
            target = dir_root / f"bg_p{i}_{_slug(bg_query)}.png"
            result = acquire_one("bg", query=bg_query, output_path=str(target))
            slide["backgroundImage"] = f"images/{Path(result).name}" if result else bg_query
            report["items"].append({"page": i, "type": "bg", "query": bg_query, "result": result})
            report["total"] += 1
            report["success" if result else "failed"] += 1

        # Logo
        logo_query = slide.get("logo")
        if isinstance(logo_query, str) and not logo_query.startswith(("images/", "http", "/")):
            target = dir_root / f"logo_{_slug(logo_query)}.png"
            result = acquire_one("logo", query=logo_query, output_path=str(target))
            slide["logo"] = f"images/{Path(result).name}" if result else logo_query
            report["items"].append({"page": i, "type": "logo", "query": logo_query, "result": result})
            report["total"] += 1
            report["success" if result else "failed"] += 1

        # 卡片配图
        for j, card in enumerate(slide.get("cards", []) or []):
            img_query = card.get("image")
            if isinstance(img_query, str) and not img_query.startswith(("images/", "http", "/")):
                target = dir_root / f"icon_p{i}_c{j+1}_{_slug(img_query)}.png"
                result = acquire_one("icon", query=img_query, output_path=str(target))
                card["image"] = f"images/{Path(result).name}" if result else img_query
                report["items"].append({"page": i, "card": j+1, "type": "icon", "query": img_query, "result": result})
                report["total"] += 1
                report["success" if result else "failed"] += 1

    # 写回 JSON（备份原文件）
    backup = json_path.with_suffix(json_path.suffix + ".bak")
    shutil.copy(str(json_path), str(backup))
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n📊 批量资产获取完成：")
    print(f"   总计：{report['total']} | 成功：{report['success']} | 失败：{report['failed']}")
    print(f"   原 JSON 已备份至：{backup}")
    print(f"   新 JSON 路径已更新为相对路径")
    return report


def _slug(s: str, max_len: int = 20) -> str:
    """生成文件名安全的简短 slug。"""
    import re
    s = re.sub(r"[^\w\u4e00-\u9fa5]+", "_", s).strip("_")
    return s[:max_len] or "asset"


# ============== CLI ==============

def main():
    parser = argparse.ArgumentParser(description="Tenchage-ppt v3.1 自动化资产获取")
    parser.add_argument("--type", choices=["logo", "screenshot", "bg", "icon"], help="单条模式：资产类型")
    parser.add_argument("--query", default="", help="单条模式：搜索关键词")
    parser.add_argument("--prompt", default="", help="单条模式：自定义 prompt（覆盖默认模板）")
    parser.add_argument("--output", default="", help="单条模式：输出路径")
    parser.add_argument("--batch", help="批量模式：JSON 文件路径")
    parser.add_argument("--dir", help="批量模式：图片输出目录（默认 <json同级>/images）")
    args = parser.parse_args()

    if args.batch:
        acquire_batch(args.batch, args.dir)
    elif args.type and args.output:
        acquire_one(args.type, query=args.query, prompt=args.prompt, output_path=args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
