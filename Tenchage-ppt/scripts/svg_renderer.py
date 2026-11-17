"""
Tenchage-ppt v3.3 · SVG 渲染器
================================
将 SVG 字符串/文件渲染为高 DPI PNG，供 add_svg() 嵌入 PPTX 使用。

后端策略（自动 fallback）：
  1. Playwright (headless Chromium) — 首选，SVG 标准支持最完整，字体/滤镜/渐变全保留
  2. svglib + reportlab + Pillow — 备用，纯 Python 但渲染精度略弱

依赖：playwright（已装）、Pillow
"""
import io
import os
import tempfile
import hashlib
from pathlib import Path

# ============================================================
# 缓存目录
# ============================================================
CACHE_DIR = Path(tempfile.gettempdir()) / "tenchage_svg_cache"
CACHE_DIR.mkdir(exist_ok=True)


def _wrap_svg_html(svg_str, width, height, bg_color):
    """把 SVG 字符串包成完整 HTML，供 headless 浏览器渲染"""
    bg = bg_color if bg_color else "transparent"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  *,*::before,*::after {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width: {width}px; height: {height}px;
    background: {bg};
    overflow: hidden;
  }}
  body > svg {{
    width: 100%;
    height: 100%;
    display: block;
  }}
</style>
</head><body>{svg_str}</body></html>"""
    return html


def _render_with_playwright(svg_str, out_path, width, height, bg_color):
    """用 Playwright + Chromium 渲染 SVG"""
    from playwright.sync_api import sync_playwright

    html = _wrap_svg_html(svg_str, width, height, bg_color)
    tmp_html = Path(tempfile.mktemp(suffix=".html"))
    tmp_html.write_text(html, encoding="utf-8")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": int(width), "height": int(height)},
                device_scale_factor=2.0,  # 2x 高清
            )
            page = context.new_page()
            page.goto(f"file:///{tmp_html.as_posix()}")
            page.wait_for_load_state("networkidle")
            page.screenshot(
                path=out_path,
                omit_background=(bg_color is None),
                clip={"x": 0, "y": 0, "width": int(width), "height": int(height)},
            )
            browser.close()
    finally:
        try:
            tmp_html.unlink()
        except Exception:
            pass


def _render_with_svglib(svg_str_or_path, out_path, width, height, bg_color):
    """用 svglib+reportlab 渲染 SVG（备用，可能因 cairo 缺失失败）"""
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM

    if "<svg" in str(svg_str_or_path):
        tmp_svg = Path(tempfile.mktemp(suffix=".svg"))
        tmp_svg.write_text(svg_str_or_path, encoding="utf-8")
        svg_path = str(tmp_svg)
    else:
        svg_path = str(svg_str_or_path)

    drawing = svg2rlg(svg_path)
    if drawing is None:
        raise RuntimeError(f"svglib 解析失败：{svg_path}")

    if width or height:
        scale = (width / drawing.width) if width else (height / drawing.height)
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)

    renderPM.drawToFile(drawing, out_path, fmt="PNG")


def svg_to_png(
    svg,
    out_path=None,
    width=800,
    height=600,
    bg_color=None,
    use_cache=True,
    backend="auto",
):
    """
    将 SVG 渲染成 PNG。

    参数：
        svg       : SVG 字符串 或 SVG 文件路径
        out_path  : 输出 PNG 路径；不传则自动生成临时文件（缓存可复用）
        width     : 输出宽度（像素），默认 800
        height    : 输出高度（像素），默认 600
        bg_color  : 背景色 CSS 字符串（如 "#FFFFFF"），不传则透明
        use_cache : 是否启用缓存（同一 SVG 多次调用直接复用 PNG）
        backend   : "auto" / "playwright" / "svglib"

    返回：
        out_path（PNG 文件绝对路径）
    """
    # 标准化：拿到 SVG 字符串
    if isinstance(svg, (str, bytes)) and ("<svg" in str(svg) or "<?xml" in str(svg)):
        svg_str = svg if isinstance(svg, str) else svg.decode("utf-8")
    else:
        # 当作文件路径
        svg_path = Path(str(svg))
        if not svg_path.exists():
            raise FileNotFoundError(f"SVG 文件不存在：{svg_path}")
        svg_str = svg_path.read_text(encoding="utf-8")

    # 缓存命中检查
    if use_cache and out_path is None:
        cache_key = hashlib.md5(
            f"{svg_str}|{width}|{height}|{bg_color}|{backend}".encode("utf-8")
        ).hexdigest()[:16]
        out_path = str(CACHE_DIR / f"png_{cache_key}.png")
        if os.path.exists(out_path):
            return out_path

    if out_path is None:
        out_path = tempfile.mktemp(suffix=".png")

    # 选择 backend
    last_err = None
    backends = [backend] if backend != "auto" else ["playwright", "svglib"]

    for be in backends:
        try:
            if be == "playwright":
                _render_with_playwright(svg_str, out_path, width, height, bg_color)
            elif be == "svglib":
                _render_with_svglib(svg_str, out_path, width, height, bg_color)
            else:
                raise ValueError(f"未知 backend：{be}")
            return out_path
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"所有 backend 渲染失败，最后错误：{last_err}")


def clear_cache():
    """清空 SVG 渲染缓存"""
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(exist_ok=True)


if __name__ == "__main__":
    test_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1A73E8"/>
      <stop offset="100%" stop-color="#0F4C9A"/>
    </linearGradient>
  </defs>
  <rect x="50" y="50" width="300" height="200" fill="url(#g)" rx="20"/>
  <text x="200" y="160" font-size="28" fill="white" text-anchor="middle"
        font-family="Microsoft YaHei, Arial" font-weight="bold">Tenchage v3.3</text>
  <text x="200" y="195" font-size="16" fill="#B0D0FF" text-anchor="middle"
        font-family="Microsoft YaHei, Arial">SVG → PNG 混合渲染</text>
</svg>"""
    out = svg_to_png(test_svg, "test_out.png", width=800, height=600)
    print(f"✓ 渲染成功：{out}")
    print(f"  文件大小：{os.path.getsize(out)} bytes")
