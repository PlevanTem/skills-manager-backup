#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel -> Markdown 解析器（Tenchage-ppt v3.0 能力 1）
用法：python excel_to_md.py <input.xlsx> [output.md]

依赖：openpyxl 或 pandas
"""
import sys
from pathlib import Path


def excel_to_md(input_path: str, output_path: str = None) -> str:
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Excel not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(".md")
    output_path = Path(output_path).resolve()

    md_lines = [f"# {input_path.stem}\n", f"> Source: `{input_path.name}`\n"]

    try:
        from openpyxl import load_workbook
        wb = load_workbook(str(input_path), data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            md_lines.append(f"\n## Sheet: {sheet_name}\n")
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                md_lines.append("_（空表）_\n")
                continue
            header = rows[0]
            md_lines.append("| " + " | ".join(str(c or "") for c in header) + " |")
            md_lines.append("|" + "|".join(["---"] * len(header)) + "|")
            for row in rows[1:]:
                md_lines.append("| " + " | ".join(str(c or "") for c in row) + " |")
    except ImportError:
        print("ERROR: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    output_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ XLSX -> MD: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python excel_to_md.py <input.xlsx> [output.md]")
        sys.exit(1)
    excel_to_md(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
