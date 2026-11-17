#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讲稿文档导出器（Tenchage-ppt v3.0 能力 5）
用法：python export_notes.py <ppt_data.json> [output.md|output.docx]

将 JSON 中每页的 speakerNotes 字段提取整理为讲稿文档。
"""
import sys
import json
from pathlib import Path


def export_notes(json_path: str, output_path: str = None) -> str:
    json_path = Path(json_path).resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if output_path is None:
        output_path = json_path.with_name(json_path.stem + "_notes.md")
    output_path = Path(output_path).resolve()

    slides = data.get("slides", [])
    start_page = data.get("startPage", 1)

    if output_path.suffix.lower() == ".docx":
        _export_docx(slides, start_page, output_path)
    else:
        _export_md(slides, start_page, output_path)

    print(f"✅ 讲稿已导出：{output_path}")
    return str(output_path)


def _export_md(slides, start_page, output_path: Path):
    lines = ["# 演讲讲稿\n", f"> 共 {len(slides)} 页\n"]
    for i, s in enumerate(slides):
        page_no = start_page + i
        title = s.get("mainTitle", "(未命名)")
        notes = s.get("speakerNotes", "").strip()
        lines.append(f"\n## 第 {page_no} 页 · {title}\n")
        if notes:
            lines.append(notes)
        else:
            lines.append("_（本页无讲稿）_")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _export_docx(slides, start_page, output_path: Path):
    try:
        from docx import Document
        from docx.shared import Pt
    except ImportError:
        print("ERROR: pip install python-docx", file=sys.stderr)
        sys.exit(1)

    doc = Document()
    doc.add_heading("演讲讲稿", level=0)
    doc.add_paragraph(f"共 {len(slides)} 页")

    for i, s in enumerate(slides):
        page_no = start_page + i
        title = s.get("mainTitle", "(未命名)")
        notes = s.get("speakerNotes", "").strip()
        doc.add_heading(f"第 {page_no} 页 · {title}", level=1)
        if notes:
            for para in notes.split("\n"):
                if para.strip():
                    doc.add_paragraph(para)
        else:
            p = doc.add_paragraph("（本页无讲稿）")
            p.runs[0].italic = True

    doc.save(str(output_path))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_notes.py <ppt_data.json> [output.md|output.docx]")
        sys.exit(1)
    export_notes(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
