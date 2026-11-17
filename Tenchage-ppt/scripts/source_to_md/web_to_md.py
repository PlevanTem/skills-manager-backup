#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL -> Markdown 解析器（Tenchage-ppt v3.0 能力 1）
用法：python web_to_md.py <url> [output.md]

优先调用 baoyu-fetch CLI（如已安装），否则回退到 requests + BeautifulSoup。
"""
import sys
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def web_to_md(url: str, output_path: str = None) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url}")

    if output_path is None:
        host = urlparse(url).hostname or "page"
        output_path = Path.cwd() / f"{host}.md"
    output_path = Path(output_path).resolve()

    # 优先尝试 baoyu-fetch
    try:
        result = subprocess.run(
            ["baoyu-fetch", url, "--output", str(output_path), "--format", "markdown"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and output_path.exists():
            print(f"✅ URL -> MD (baoyu-fetch): {output_path}")
            return str(output_path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 回退到 requests + BeautifulSoup
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("ERROR: pip install requests beautifulsoup4", file=sys.stderr)
        sys.exit(1)

    headers = {"User-Agent": "Mozilla/5.0 Tenchage-ppt/3.0"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title = (soup.title.string if soup.title else url).strip()
    md_lines = [f"# {title}\n", f"> Source: <{url}>\n"]

    # 移除 nav/script/style/footer 等噪音
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    main = soup.find("article") or soup.find("main") or soup.body
    if main:
        for tag in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = tag.get_text(strip=True)
            if not text:
                continue
            if tag.name == "h1":
                md_lines.append(f"\n## {text}\n")
            elif tag.name == "h2":
                md_lines.append(f"\n### {text}\n")
            elif tag.name == "h3":
                md_lines.append(f"\n#### {text}\n")
            elif tag.name == "h4":
                md_lines.append(f"\n##### {text}\n")
            elif tag.name == "li":
                md_lines.append(f"- {text}")
            else:
                md_lines.append(text)

    output_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ URL -> MD: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python web_to_md.py <url> [output.md]")
        sys.exit(1)
    web_to_md(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
