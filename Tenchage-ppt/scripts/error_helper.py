#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误诊断辅助器（Tenchage-ppt v3.1 P1 能力）

参考 ppt-master 的 error_helper.py 思路，做 JSON Schema 校验 + 友好错误提示。
不是替代 build_ppt.js 的运行时错误，而是 **在生成前** 把 JSON 问题暴露出来，避免到 PPTX 阶段才发现。

用法：
  python error_helper.py validate <ppt_data.json>      # 校验，返回 0=OK, 1=有错
  python error_helper.py explain <error_message>        # 解释 build_ppt.js 的报错（待续）

校验规则（按页粒度）：
  1. 必填字段：layout, mainTitle
  2. 布局-字段一致性（如 layout=cards 必须有非空 cards 数组）
  3. 数量约束（如 cards 4 张、quad_loop 4 个、three_pillars 3 个）
  4. 字数约束（窄卡描述 40-55 字、不得含全角括号「（）」）
  5. 文件存在性（image / backgroundImage / logo 引用的本地图必须存在）
"""
import sys
import json
import re
from pathlib import Path


# ============== 布局定义 ==============

LAYOUT_RULES = {
    "cards":              {"required": ["cards"], "card_count": 4, "narrow": True},
    "summary":            {"required": [], "narrow": False},
    "table":              {"required": ["headers", "rows"], "narrow": False},
    "comparison":         {"required": ["leftTitle", "rightTitle", "leftItems", "rightItems"], "narrow": False},
    "process":            {"required": ["steps"], "narrow": False},
    "kpi":                {"required": ["kpis"], "narrow": False},
    "architecture":       {"required": ["layers"], "narrow": False},
    "circle_loop":        {"required": ["nodes"], "node_count": 4, "narrow": False},
    "quad_loop":          {"required": ["quadrants"], "quad_count": 4, "narrow": False},
    "three_pillars":      {"required": ["pillars"], "pillar_count": 3, "narrow": True},
    "break_three_columns":{"required": ["columns"], "col_count": 3, "narrow": True},
    "hub_dual_card":      {"required": ["hub", "leftCard", "rightCard"], "narrow": False},
    "radial":             {"required": ["center", "branches"], "narrow": False},
    "three_generations":  {"required": ["generations"], "gen_count": 3, "narrow": True},
    "one_plus_n":         {"required": ["main", "subs"], "narrow": False},
    "three_schools_debate":{"required": ["schools", "matrix", "verdict"], "school_count": 3, "narrow": True},
    "cards_with_image":   {"required": ["cards", "image"], "card_count": 4, "narrow": True},
}

NARROW_DESC_MIN = 40
NARROW_DESC_MAX = 55
FORBIDDEN_PUNCT = ["（", "）", "「", "」"]  # 窄卡铁律：禁全角括号


# ============== 校验入口 ==============

class ValidationReport:
    def __init__(self):
        self.errors = []   # 必须修复
        self.warnings = [] # 建议修复

    def err(self, page: int, code: str, msg: str, fix: str = ""):
        self.errors.append({"page": page, "code": code, "msg": msg, "fix": fix})

    def warn(self, page: int, code: str, msg: str, fix: str = ""):
        self.warnings.append({"page": page, "code": code, "msg": msg, "fix": fix})

    def is_ok(self) -> bool:
        return len(self.errors) == 0

    def render(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"\n❌ 发现 {len(self.errors)} 个错误（必须修复）：\n")
            for e in self.errors:
                lines.append(f"  [P{e['page']}] [{e['code']}] {e['msg']}")
                if e["fix"]:
                    lines.append(f"         💡 修复建议：{e['fix']}")
        if self.warnings:
            lines.append(f"\n⚠️  发现 {len(self.warnings)} 个警告（建议修复）：\n")
            for w in self.warnings:
                lines.append(f"  [P{w['page']}] [{w['code']}] {w['msg']}")
                if w["fix"]:
                    lines.append(f"         💡 建议：{w['fix']}")
        if not self.errors and not self.warnings:
            lines.append("\n✅ JSON 校验通过，无错误无警告。")
        elif not self.errors:
            lines.append(f"\n✅ 无致命错误，{len(self.warnings)} 个警告可酌情修复。")
        return "\n".join(lines)


def validate(json_path: str) -> ValidationReport:
    json_path = Path(json_path).resolve()
    rpt = ValidationReport()

    if not json_path.exists():
        rpt.err(0, "FILE_NOT_FOUND", f"JSON 文件不存在：{json_path}",
                "请检查路径是否正确")
        return rpt

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rpt.err(0, "JSON_PARSE_ERROR",
                f"JSON 语法错误：第 {e.lineno} 行 第 {e.colno} 列 - {e.msg}",
                "用 VS Code 打开 JSON 文件，按 F8 跳到错误位置；常见原因：尾随逗号、缺少引号")
        return rpt

    slides = data.get("slides", [])
    if not slides:
        rpt.err(0, "NO_SLIDES", "JSON 中 slides 数组为空",
                "至少需要 1 页幻灯片，结构为 {\"slides\": [{\"layout\": \"cards\", ...}]}")
        return rpt

    base_dir = json_path.parent
    for i, slide in enumerate(slides, 1):
        _validate_slide(slide, i, rpt, base_dir)

    return rpt


def _validate_slide(slide: dict, page: int, rpt: ValidationReport, base_dir: Path):
    # 1. 必填字段
    layout = slide.get("layout")
    if not layout:
        rpt.err(page, "MISSING_LAYOUT", "缺少 layout 字段",
                f'添加 "layout": "cards"（或其他 17 种之一）')
        return

    if layout not in LAYOUT_RULES:
        rpt.err(page, "UNKNOWN_LAYOUT", f"未知 layout：{layout}",
                f"支持的 layout 列表：{', '.join(LAYOUT_RULES.keys())}")
        return

    if not slide.get("mainTitle"):
        rpt.err(page, "MISSING_TITLE", "缺少 mainTitle 字段",
                '添加结论性标题，如 "mainTitle": "AI 让一线员工也能用上专家智能"')

    # 2. 布局必填字段
    rule = LAYOUT_RULES[layout]
    for field in rule["required"]:
        val = slide.get(field)
        if val is None or (isinstance(val, list) and len(val) == 0):
            rpt.err(page, "LAYOUT_FIELD_MISSING",
                    f"layout={layout} 必须包含非空字段 {field}",
                    f"参考 SKILL.md「七、各布局数据格式」中 {layout} 章节")

    # 3. 数量约束
    for count_key, field_name in [("card_count", "cards"), ("node_count", "nodes"),
                                   ("quad_count", "quadrants"), ("pillar_count", "pillars"),
                                   ("col_count", "columns"), ("gen_count", "generations"),
                                   ("school_count", "schools")]:
        if count_key in rule:
            expected = rule[count_key]
            actual = len(slide.get(field_name, []) or [])
            if actual != expected:
                rpt.err(page, "WRONG_COUNT",
                        f"layout={layout} 要求 {field_name} 数量为 {expected}，实际 {actual}",
                        f"调整 {field_name} 数组长度为 {expected}")

    # 4. 窄卡铁律
    if rule.get("narrow"):
        for j, card in enumerate(slide.get("cards", []) or [], 1):
            desc = card.get("desc", "") or card.get("description", "")
            if not desc:
                continue
            n = len(desc)
            if n < NARROW_DESC_MIN:
                rpt.warn(page, "DESC_TOO_SHORT",
                         f"卡片#{j} 描述只有 {n} 字（建议 {NARROW_DESC_MIN}-{NARROW_DESC_MAX}）",
                         "扩充描述或精简标题以平衡视觉")
            elif n > NARROW_DESC_MAX:
                rpt.err(page, "DESC_TOO_LONG",
                        f"卡片#{j} 描述 {n} 字超过 {NARROW_DESC_MAX} 字铁律",
                        "压缩到 40-55 字，避免竖排断字")
            for ch in FORBIDDEN_PUNCT:
                if ch in desc:
                    rpt.err(page, "FORBIDDEN_PUNCT",
                            f"卡片#{j} 描述含全角括号「{ch}」（窄卡铁律禁用）",
                            f'改用半角括号 "(" ")" 或破折号 "——"')
                    break

    # 5. 文件存在性
    for img_field in ["backgroundImage", "logo", "image"]:
        val = slide.get(img_field)
        if isinstance(val, str) and not val.startswith(("http://", "https://")):
            img_path = (base_dir / val).resolve() if not Path(val).is_absolute() else Path(val)
            if not img_path.exists():
                rpt.warn(page, "IMAGE_MISSING",
                         f"{img_field} 引用的图片不存在：{val}",
                         f"运行 asset_acquire.py 自动获取，或手工放置图片到 {img_path}")

    for j, card in enumerate(slide.get("cards", []) or [], 1):
        img = card.get("image")
        if isinstance(img, str) and not img.startswith(("http://", "https://")):
            img_path = (base_dir / img).resolve() if not Path(img).is_absolute() else Path(img)
            if not img_path.exists():
                rpt.warn(page, "IMAGE_MISSING",
                         f"卡片#{j} image 引用的图片不存在：{img}",
                         "运行 asset_acquire.py --batch 自动获取")


# ============== 错误信息翻译器（彩蛋） ==============

ERROR_TRANSLATIONS = {
    "Cannot read properties of undefined": "通常是 JSON 结构和 layout 不匹配，运行 validate 看缺哪个字段",
    "ENOENT": "文件路径不存在，检查 image/backgroundImage 是否拼对",
    "Invalid font": "字体名拼写错误，必须是「腾讯体 W3」或「腾讯体 W7」（中文名+空格+英文）",
    "addText": "通常是 mainTitle 为空或 layout 字段未定义",
}


def explain(error_msg: str) -> str:
    for key, hint in ERROR_TRANSLATIONS.items():
        if key in error_msg:
            return f"💡 已识别错误模式「{key}」：\n   {hint}"
    return "❓ 未识别的错误模式，请运行 validate 检查 JSON 结构"


# ============== CLI ==============

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "validate":
        if len(sys.argv) < 3:
            print("Usage: python error_helper.py validate <ppt_data.json>")
            sys.exit(1)
        rpt = validate(sys.argv[2])
        print(rpt.render())
        sys.exit(0 if rpt.is_ok() else 1)
    elif cmd == "explain":
        if len(sys.argv) < 3:
            print("Usage: python error_helper.py explain <error_message>")
            sys.exit(1)
        print(explain(" ".join(sys.argv[2:])))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
