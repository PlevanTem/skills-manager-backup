#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPTX -> Markdown 解析器（Tenchage-ppt v3.0 能力 1）
用法：python ppt_to_md.py <input.pptx> [output.md]

依赖：python-pptx
"""
import sys
from pathlib import Path


def ppt_to_md(input_path: str, output_path: str = None) -> str:
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"PPTX not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(".md")
    output_path = Path(output_path).resolve()

    try:
        from pptx import Presentation
    except ImportError:
        print("ERROR: pip install python-pptx", file=sys.stderr)
        sys.exit(1)

    prs = Presentation(str(input_path))
    md_lines = [f"# {input_path.stem}\n", f"> Source: `{input_path.name}`\n"]

    for i, slide in enumerate(prs.slides, 1):
        md_lines.append(f"\n## Slide {i}\n")
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        md_lines.append(text)
        # 备注
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                md_lines.append(f"\n> **演讲备注**：{notes}")

    output_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ PPTX -> MD: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ppt_to_md.py <input.pptx> [output.md]")
        sys.exit(1)
    ppt_to_md(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
