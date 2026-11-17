#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOCX -> Markdown 解析器（Tenchage-ppt v3.0 能力 1）
用法：python doc_to_md.py <input.docx> [output.md]

依赖：python-docx（pip install python-docx）
"""
import sys
from pathlib import Path


def doc_to_md(input_path: str, output_path: str = None) -> str:
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"DOCX not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(".md")
    output_path = Path(output_path).resolve()

    try:
        from docx import Document
    except ImportError:
        print("ERROR: pip install python-docx", file=sys.stderr)
        sys.exit(1)

    doc = Document(str(input_path))
    md_lines = [f"# {input_path.stem}\n", f"> Source: `{input_path.name}`\n"]

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            md_lines.append("")
            continue
        style = (para.style.name or "").lower()
        if "heading 1" in style:
            md_lines.append(f"\n## {text}\n")
        elif "heading 2" in style:
            md_lines.append(f"\n### {text}\n")
        elif "heading 3" in style:
            md_lines.append(f"\n#### {text}\n")
        else:
            md_lines.append(text)

    # 处理表格
    for i, table in enumerate(doc.tables, 1):
        md_lines.append(f"\n### Table {i}\n")
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        if rows:
            md_lines.append("| " + " | ".join(rows[0]) + " |")
            md_lines.append("|" + "|".join(["---"] * len(rows[0])) + "|")
            for row in rows[1:]:
                md_lines.append("| " + " | ".join(row) + " |")

    output_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ DOCX -> MD: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python doc_to_md.py <input.docx> [output.md]")
        sys.exit(1)
    doc_to_md(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
