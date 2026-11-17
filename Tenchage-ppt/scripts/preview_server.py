#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时 Web 预览服务（Tenchage-ppt v3.0 能力 4）
用法：python preview_server.py <ppt_data.json> [port=6060]

工作原理：
  1. 启动 HTTP 服务器（默认端口 6060）
  2. 监听 JSON 文件变化
  3. 用 HTML/CSS 渲染每页缩略图
  4. 浏览器打开 http://localhost:6060 查看
"""
import sys
import json
import os
import threading
import time
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"


class PreviewState:
    """全局状态：JSON 路径、最后修改时间、缓存内容。"""
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.last_mtime = 0
        self.cached_data = None
        self.refresh()

    def refresh(self):
        try:
            mtime = self.json_path.stat().st_mtime
            if mtime != self.last_mtime:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self.cached_data = json.load(f)
                self.last_mtime = mtime
        except Exception as e:
            self.cached_data = {"error": str(e)}


def make_handler(state: PreviewState):
    class PreviewHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            state.refresh()
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(self._render_index().encode("utf-8"))
            elif self.path == "/data.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(state.cached_data, ensure_ascii=False).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, fmt, *args):
            pass  # 静默日志

        def _render_index(self) -> str:
            tpl = TEMPLATE_DIR / "preview.html"
            if tpl.exists():
                return tpl.read_text(encoding="utf-8")
            # 内置默认模板
            return DEFAULT_HTML

    return PreviewHandler


DEFAULT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Tenchage-ppt 实时预览</title>
<style>
body { font-family: "Microsoft YaHei", sans-serif; background: #F4F5F7; margin: 0; padding: 20px; }
h1 { color: #1A50D6; }
.slide { background: white; border: 1px solid #E5EBF5; border-radius: 8px; padding: 20px;
         margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
.slide-no { color: #86909C; font-size: 12px; }
.slide-title { color: #1D2129; font-size: 20px; font-weight: bold; margin: 8px 0; }
.slide-layout { display: inline-block; background: #1A50D6; color: white; padding: 2px 8px;
                border-radius: 4px; font-size: 11px; margin-left: 8px; }
.deco { display: flex; gap: 4px; margin-bottom: 12px; }
.deco-blue { width: 60px; height: 5px; background: #1A50D6; }
.deco-green { width: 48px; height: 5px; background: #00A45D; }
pre { background: #F4F5F7; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 12px; }
</style>
</head>
<body>
<h1>📊 Tenchage-ppt 实时预览</h1>
<div id="content">加载中...</div>
<script>
async function refresh() {
  try {
    const res = await fetch("/data.json?_=" + Date.now());
    const data = await res.json();
    const slides = data.slides || [];
    const html = slides.map((s, i) => `
      <div class="slide">
        <div class="deco"><div class="deco-blue"></div><div class="deco-green"></div></div>
        <div class="slide-no">Page ${i + 1}<span class="slide-layout">${s.layout || "cards"}</span></div>
        <div class="slide-title">${s.mainTitle || "(未命名)"}</div>
        ${s.subTitle ? `<div style="color:#4E5969">${s.subTitle}</div>` : ""}
        <pre>${JSON.stringify(s, null, 2)}</pre>
      </div>
    `).join("");
    document.getElementById("content").innerHTML = html || "<p>无幻灯片数据</p>";
  } catch (e) {
    document.getElementById("content").innerHTML = "<p style='color:red'>加载失败：" + e.message + "</p>";
  }
}
refresh();
setInterval(refresh, 1500);  // 1.5 秒轮询一次
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python preview_server.py <ppt_data.json> [port=6060]")
        sys.exit(1)

    json_path = Path(sys.argv[1]).resolve()
    if not json_path.exists():
        print(f"ERROR: JSON not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    port = int(sys.argv[2]) if len(sys.argv) > 2 else 6060
    state = PreviewState(json_path)

    server = HTTPServer(("127.0.0.1", port), make_handler(state))
    url = f"http://localhost:{port}"
    print(f"🚀 预览服务启动：{url}")
    print(f"   监听文件：{json_path}")
    print(f"   按 Ctrl+C 退出")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 预览服务已停止")


if __name__ == "__main__":
    main()
