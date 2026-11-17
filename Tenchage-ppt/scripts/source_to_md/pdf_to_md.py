#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF -> Markdown 解析器（Tenchage-ppt v3.0 能力 1）
用法：python pdf_to_md.py <input.pdf> [output.md]

依赖（按优先级回退）：
  1. pdfplumber（推荐，结构化好）
  2. PyMuPDF / fitz（速度快）
  3. pdftotext CLI（兜底）
"""
import sys
import os
from pathlib import Path


def pdf_to_md(input_path: str, output_path: str = None) -> str:
    """将 PDF 转为 Markdown，按页分隔。"""
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"PDF not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(".md")
    output_path = Path(output_path).resolve()

    md_lines = [f"# {input_path.stem}\n", f"> Source: `{input_path.name}`\n"]

    # 优先用 pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(input_path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                md_lines.append(f"\n## Page {i}\n")
                text = page.extract_text() or ""
                md_lines.append(text.strip() + "\n")
    except ImportError:
        # 回退到 PyMuPDF
        try:
            import fitz
            doc = fitz.open(str(input_path))
            for i, page in enumerate(doc, 1):
                md_lines.append(f"\n## Page {i}\n")
                md_lines.append(page.get_text().strip() + "\n")
            doc.close()
        except ImportError:
            print("ERROR: 请先安装 pdfplumber 或 PyMuPDF：", file=sys.stderr)
            print("  pip install pdfplumber  # 推荐", file=sys.stderr)
            sys.exit(1)

    md_content = "\n".join(md_lines)
    output_path.write_text(md_content, encoding="utf-8")
    print(f"✅ PDF -> MD: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_md.py <input.pdf> [output.md]")
        sys.exit(1)
    pdf_to_md(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
