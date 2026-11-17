"""
Tenchage-ppt v3.3 · SVG 模板库
================================
内置 5 个高频 SVG 模板，专为腾讯智慧零售风格的售前/咨询 PPT 而设计。

每个模板接受 data dict，返回 SVG 字符串。配合 svg_renderer.svg_to_png 使用。

字体规范（与 Tenchage 主体保持一致）：
  - 标题/关键词：腾讯体 W7（Web fallback: Microsoft YaHei Bold）
  - 正文：腾讯体 W3（Web fallback: Microsoft YaHei Light）

配色规范（腾讯智慧零售蓝系）：
  - 主蓝 #1A73E8 / 深蓝 #0F4C9A
  - 浅蓝 #E8F0FE / 极浅 #F4F8FF
  - 黑 #1A1A1A / 灰 #5A6168 / 浅灰 #B5BAC2
  - 强调橙 #FF6A00（仅末级高亮）
"""

# ============================================================
# 通用配色
# ============================================================
C_PRIMARY = "#1A73E8"
C_PRIMARY_DARK = "#0F4C9A"
C_PRIMARY_LITE = "#E8F0FE"
C_PRIMARY_FAINT = "#F4F8FF"
C_INK = "#1A1A1A"
C_GRAY = "#5A6168"
C_GRAY_LITE = "#B5BAC2"
C_ACCENT = "#FF6A00"

# 渐变色板（5 阶梯/漏斗用）
GRADIENT_BLUE_5 = [
    "#B7D4FB",   # 极浅
    "#7FB1F7",   # 浅
    "#3D8DEF",   # 中
    "#1A73E8",   # 主蓝
    "#0F4C9A",   # 深蓝
]

# 字体
FONT_BOLD = "腾讯体 W7, 'Tencent Sans W7', 'Microsoft YaHei', sans-serif"
FONT_REG = "腾讯体 W3, 'Tencent Sans W3', 'Microsoft YaHei Light', 'Microsoft YaHei', sans-serif"


def _wrap(svg_inner, width, height):
    """SVG 外壳"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" font-family="{FONT_REG}">
{svg_inner}
</svg>"""


# ============================================================
# 模板 1：funnel - 漏斗图（5/4/3 阶段）
# ============================================================
def funnel(data, width=800, height=600):
    """
    漏斗图：上宽下窄，每层一个阶段

    data 格式：
      {
        "title": "用户运营漏斗",
        "stages": [
          {"label": "公域触达", "value": "5000万", "desc": "视频号+广告"},
          {"label": "流量承接", "value": "800万", "desc": "小程序进店"},
          ...
        ]
      }
    """
    stages = data.get("stages", [])
    n = len(stages)
    if n == 0:
        return _wrap("", width, height)

    title = data.get("title", "")
    title_h = 60 if title else 0
    avail_h = height - title_h - 40
    layer_h = avail_h / n
    max_w = width * 0.85
    min_w = width * 0.30

    parts = []

    # 标题
    if title:
        parts.append(
            f'<text x="{width/2}" y="40" font-size="32" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="{C_INK}" text-anchor="middle">{title}</text>'
        )

    # 漏斗梯形
    for i, s in enumerate(stages):
        ratio_top = 1 - (i / n) * 0.7      # 顶宽比例
        ratio_bot = 1 - ((i + 1) / n) * 0.7  # 底宽比例
        w_top = min_w + (max_w - min_w) * ratio_top
        w_bot = min_w + (max_w - min_w) * ratio_bot

        cx = width / 2
        y_top = title_h + 20 + i * layer_h
        y_bot = y_top + layer_h - 4  # 留 4px 间隙

        x_tl = cx - w_top / 2
        x_tr = cx + w_top / 2
        x_bl = cx - w_bot / 2
        x_br = cx + w_bot / 2

        color = GRADIENT_BLUE_5[min(i, 4)]

        # 梯形
        parts.append(
            f'<polygon points="{x_tl},{y_top} {x_tr},{y_top} {x_br},{y_bot} {x_bl},{y_bot}" '
            f'fill="{color}"/>'
        )

        # 阶段文字（label 居中）
        label = s.get("label", "")
        value = s.get("value", "")
        desc = s.get("desc", "")

        text_y = y_top + layer_h / 2 - 8
        parts.append(
            f'<text x="{cx}" y="{text_y}" font-size="28" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="white" text-anchor="middle">{label}</text>'
        )
        if value:
            parts.append(
                f'<text x="{cx}" y="{text_y + 36}" font-size="32" font-family="{FONT_BOLD}" '
                f'font-weight="700" fill="white" text-anchor="middle">{value}</text>'
            )

        # 右侧描述
        if desc:
            parts.append(
                f'<text x="{x_br + 16}" y="{(y_top + y_bot)/2 + 4}" font-size="18" '
                f'font-family="{FONT_REG}" fill="{C_GRAY}">{desc}</text>'
            )

    return _wrap("\n".join(parts), width, height)


# ============================================================
# 模板 2：radar - 雷达图
# ============================================================
def radar(data, width=600, height=600):
    """
    雷达图

    data 格式：
      {
        "title": "AI能力评估",
        "axes": ["内容", "数据", "运营", "技术", "组织"],
        "series": [
          {"name": "当前", "values": [3, 4, 2, 3, 2], "color": "#1A73E8"},
          {"name": "目标", "values": [5, 5, 4, 4, 4], "color": "#FF6A00"}
        ],
        "max": 5
      }
    """
    import math

    axes = data.get("axes", [])
    series = data.get("series", [])
    max_val = data.get("max", 5)
    title = data.get("title", "")

    n = len(axes)
    if n < 3:
        return _wrap("", width, height)

    cx = width / 2
    cy = height / 2 + (20 if title else 0)
    radius = min(width, height) * 0.36

    parts = []
    if title:
        parts.append(
            f'<text x="{cx}" y="36" font-size="28" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="{C_INK}" text-anchor="middle">{title}</text>'
        )

    # 网格圈（4 层）
    for level in range(1, 5):
        r = radius * level / 4
        points = []
        for i in range(n):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")
        parts.append(
            f'<polygon points="{" ".join(points)}" fill="none" '
            f'stroke="{C_GRAY_LITE}" stroke-width="1" stroke-dasharray="3 3"/>'
        )

    # 轴线 + 标签
    for i, ax in enumerate(axes):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        x_end = cx + radius * math.cos(angle)
        y_end = cy + radius * math.sin(angle)
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x_end:.1f}" y2="{y_end:.1f}" '
            f'stroke="{C_GRAY_LITE}" stroke-width="1"/>'
        )
        # 标签
        label_x = cx + (radius + 30) * math.cos(angle)
        label_y = cy + (radius + 30) * math.sin(angle) + 8
        anchor = "middle"
        if math.cos(angle) > 0.3:
            anchor = "start"
        elif math.cos(angle) < -0.3:
            anchor = "end"
        parts.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" font-size="20" '
            f'font-family="{FONT_BOLD}" font-weight="700" fill="{C_INK}" '
            f'text-anchor="{anchor}">{ax}</text>'
        )

    # 数据多边形
    for s in series:
        vals = s.get("values", [])
        color = s.get("color", C_PRIMARY)
        points = []
        for i, v in enumerate(vals[:n]):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            r = radius * (v / max_val)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")
        parts.append(
            f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="0.25" '
            f'stroke="{color}" stroke-width="2.5"/>'
        )
        # 顶点圆
        for p in points:
            x, y = p.split(",")
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>'
            )

    # 图例
    if len(series) > 1:
        ly = height - 30
        lx = 30
        for s in series:
            color = s.get("color", C_PRIMARY)
            name = s.get("name", "")
            parts.append(
                f'<rect x="{lx}" y="{ly-16}" width="20" height="20" fill="{color}" rx="3"/>'
            )
            parts.append(
                f'<text x="{lx+28}" y="{ly}" font-size="18" font-family="{FONT_REG}" '
                f'fill="{C_INK}">{name}</text>'
            )
            lx += 130

    return _wrap("\n".join(parts), width, height)


# ============================================================
# 模板 3：stairs - 阶梯递进图
# ============================================================
def stairs(data, width=900, height=500):
    """
    阶梯递进：N 级阶梯，从浅蓝到深蓝渐变

    data 格式：
      {
        "title": "AI 使用水平五级模型",
        "levels": [
          {"label": "L1", "name": "尝试", "desc": "..."},
          {"label": "L2", "name": "使用", "desc": "..."},
          ...
        ]
      }
    """
    levels = data.get("levels", [])
    n = len(levels)
    title = data.get("title", "")
    title_h = 50 if title else 0

    if n == 0:
        return _wrap("", width, height)

    parts = []
    if title:
        parts.append(
            f'<text x="{width/2}" y="34" font-size="28" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="{C_INK}" text-anchor="middle">{title}</text>'
        )

    # 计算每级高度（递增）
    avail_w = width - 80
    avail_h = height - title_h - 60
    step_w = avail_w / n
    base_y = height - 30

    for i, lvl in enumerate(levels):
        # 高度递增（30% → 100%）
        h_ratio = 0.3 + 0.7 * (i / max(n - 1, 1))
        bar_h = avail_h * h_ratio
        x = 40 + i * step_w
        y = base_y - bar_h
        # 颜色：除最后一级用橙色高亮
        if i == n - 1:
            color = C_ACCENT
        else:
            color = GRADIENT_BLUE_5[min(int(i * 4 / max(n - 1, 1)), 4)]

        # 阶梯柱
        parts.append(
            f'<rect x="{x+4}" y="{y}" width="{step_w-8}" height="{bar_h}" '
            f'fill="{color}" rx="8"/>'
        )

        # Label
        label = lvl.get("label", "")
        name = lvl.get("name", "")
        desc = lvl.get("desc", "")

        cx = x + step_w / 2
        parts.append(
            f'<text x="{cx}" y="{y+34}" font-size="20" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="white" text-anchor="middle" opacity="0.9">{label}</text>'
        )
        parts.append(
            f'<text x="{cx}" y="{y+68}" font-size="28" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="white" text-anchor="middle">{name}</text>'
        )

        # desc 在底下
        if desc:
            parts.append(
                f'<text x="{cx}" y="{base_y+22}" font-size="16" font-family="{FONT_REG}" '
                f'fill="{C_GRAY}" text-anchor="middle">{desc}</text>'
            )

    return _wrap("\n".join(parts), width, height)


# ============================================================
# 模板 4：ring_progress - 环形进度
# ============================================================
def ring_progress(data, width=600, height=600):
    """
    环形进度图（多个环并列）

    data 格式：
      {
        "title": "Q1 关键指标",
        "rings": [
          {"label": "GMV 完成率", "value": 78, "max": 100, "color": "#1A73E8"},
          {"label": "新客占比", "value": 45, "max": 100, "color": "#FF6A00"},
          {"label": "复购率", "value": 62, "max": 100, "color": "#0F4C9A"}
        ]
      }
    """
    import math

    rings = data.get("rings", [])
    title = data.get("title", "")
    n = len(rings)
    if n == 0:
        return _wrap("", width, height)

    parts = []
    if title:
        parts.append(
            f'<text x="{width/2}" y="36" font-size="28" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="{C_INK}" text-anchor="middle">{title}</text>'
        )

    title_h = 60 if title else 0
    cell_w = width / n
    radius = min(cell_w, height - title_h - 80) * 0.32
    cy = title_h + (height - title_h) / 2 - 20

    for i, r in enumerate(rings):
        cx = cell_w * (i + 0.5)
        val = r.get("value", 0)
        mx = r.get("max", 100)
        pct = max(0, min(1, val / mx))
        color = r.get("color", C_PRIMARY)
        label = r.get("label", "")

        # 背景圈
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" '
            f'stroke="{C_PRIMARY_LITE}" stroke-width="20"/>'
        )
        # 进度圈（从顶端开始顺时针）
        circ = 2 * math.pi * radius
        dash = circ * pct
        gap = circ - dash
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" '
            f'stroke="{color}" stroke-width="20" stroke-linecap="round" '
            f'stroke-dasharray="{dash:.1f} {gap:.1f}" '
            f'transform="rotate(-90 {cx} {cy})"/>'
        )
        # 中心数值
        parts.append(
            f'<text x="{cx}" y="{cy+12}" font-size="48" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="{color}" text-anchor="middle">{val}%</text>'
        )
        # 底部标签
        parts.append(
            f'<text x="{cx}" y="{cy+radius+52}" font-size="20" font-family="{FONT_BOLD}" '
            f'font-weight="700" fill="{C_INK}" text-anchor="middle">{label}</text>'
        )

    return _wrap("\n".join(parts), width, height)


# ============================================================
# 模板 5：decor_bg - 装饰背景（蓝色不规则几何）
# ============================================================
def decor_bg(data=None, width=1280, height=720):
    """
    腾讯智慧零售风格的装饰背景：蓝色不规则几何 + 网格 + 渐变光
    
    data 格式（可选）：
      {
        "intensity": 0.6  # 装饰强度 0~1，默认 0.6
      }
    """
    data = data or {}
    intensity = data.get("intensity", 0.6)

    parts = []
    parts.append(f"""<defs>
  <linearGradient id="bg_grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#F4F8FF"/>
    <stop offset="50%" stop-color="#E8F0FE"/>
    <stop offset="100%" stop-color="#D4E4FC"/>
  </linearGradient>
  <radialGradient id="light" cx="20%" cy="20%" r="60%">
    <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.8"/>
    <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
  </radialGradient>
</defs>""")

    # 底色
    parts.append(f'<rect width="{width}" height="{height}" fill="url(#bg_grad)"/>')

    # 顶部装饰横条
    parts.append(
        f'<rect x="0" y="0" width="{width}" height="6" fill="{C_PRIMARY}"/>'
    )
    parts.append(
        f'<rect x="0" y="6" width="{width*0.3}" height="2" fill="{C_ACCENT}"/>'
    )

    # 几何装饰（圆/三角/方块）
    decorations = [
        ("circle", width * 0.08, height * 0.85, 80, C_PRIMARY, 0.08),
        ("circle", width * 0.92, height * 0.15, 120, C_PRIMARY, 0.06),
        ("circle", width * 0.78, height * 0.78, 50, C_ACCENT, 0.1),
        ("rect", width * 0.06, height * 0.12, 60, C_PRIMARY_DARK, 0.08),
    ]
    for tp, x, y, sz, c, op in decorations:
        op_real = op * intensity
        if tp == "circle":
            parts.append(f'<circle cx="{x}" cy="{y}" r="{sz}" fill="{c}" fill-opacity="{op_real}"/>')
        elif tp == "rect":
            parts.append(
                f'<rect x="{x-sz/2}" y="{y-sz/2}" width="{sz}" height="{sz}" '
                f'fill="{c}" fill-opacity="{op_real}" transform="rotate(15 {x} {y})"/>'
            )

    # 高光层
    parts.append(f'<rect width="{width}" height="{height}" fill="url(#light)"/>')

    return _wrap("\n".join(parts), width, height)


# ============================================================
# 注册表
# ============================================================
TEMPLATES = {
    "funnel": funnel,
    "radar": radar,
    "stairs": stairs,
    "ring_progress": ring_progress,
    "decor_bg": decor_bg,
}


def render(name, data, **size):
    """统一入口：render('funnel', {...}, width=800, height=600)"""
    if name not in TEMPLATES:
        raise ValueError(f"未知模板：{name}，可用：{list(TEMPLATES.keys())}")
    return TEMPLATES[name](data, **size)


if __name__ == "__main__":
    # 自测：每个模板出一张 demo
    import os
    from svg_renderer import svg_to_png

    out_dir = "C:/Users/marvinmin/.workbuddy/skills/Tenchage-ppt/scripts/_svg_test"
    os.makedirs(out_dir, exist_ok=True)

    # 1. funnel - 伊利场景
    yili_funnel = {
        "title": "伊利全域消费者运营漏斗",
        "stages": [
            {"label": "公域触达", "value": "5000万", "desc": "8 大触点"},
            {"label": "流量承接", "value": "1200万", "desc": "小程序/视频号进店"},
            {"label": "数据沉淀", "value": "600万", "desc": "会员注册"},
            {"label": "转化变现", "value": "180万", "desc": "首单成交"},
            {"label": "口碑传播", "value": "45万", "desc": "复购+裂变"},
        ],
    }
    svg = funnel(yili_funnel, width=900, height=620)
    out = svg_to_png(svg, f"{out_dir}/test_funnel.png", width=900, height=620)
    print(f"✓ funnel: {out}")

    # 2. radar
    svg = radar({
        "title": "AI 成熟度雷达",
        "axes": ["内容", "数据", "运营", "技术", "组织"],
        "series": [
            {"name": "当前", "values": [3, 4, 2, 3, 2], "color": C_PRIMARY},
            {"name": "目标", "values": [5, 5, 4, 4, 4], "color": C_ACCENT},
        ],
        "max": 5,
    }, width=600, height=620)
    out = svg_to_png(svg, f"{out_dir}/test_radar.png", width=600, height=620)
    print(f"✓ radar: {out}")

    # 3. stairs
    svg = stairs({
        "title": "AI 使用水平五级模型",
        "levels": [
            {"label": "L1", "name": "尝试", "desc": "偶尔使用"},
            {"label": "L2", "name": "使用", "desc": "高频依赖"},
            {"label": "L3", "name": "整合", "desc": "嵌入工作流"},
            {"label": "L4", "name": "驾驭", "desc": "组合多模型"},
            {"label": "L5", "name": "创造", "desc": "自构 Agent"},
        ],
    })
    out = svg_to_png(svg, f"{out_dir}/test_stairs.png", width=900, height=500)
    print(f"✓ stairs: {out}")

    # 4. ring_progress
    svg = ring_progress({
        "title": "伊利 Q1 关键指标",
        "rings": [
            {"label": "GMV 完成率", "value": 78, "color": C_PRIMARY},
            {"label": "新客占比", "value": 45, "color": C_ACCENT},
            {"label": "复购率", "value": 62, "color": C_PRIMARY_DARK},
        ],
    })
    out = svg_to_png(svg, f"{out_dir}/test_ring.png", width=600, height=600)
    print(f"✓ ring_progress: {out}")

    # 5. decor_bg
    svg = decor_bg()
    out = svg_to_png(svg, f"{out_dir}/test_decor.png", width=1280, height=720, bg_color="#FFFFFF")
    print(f"✓ decor_bg: {out}")

    print(f"\n所有测试图输出到：{out_dir}")
