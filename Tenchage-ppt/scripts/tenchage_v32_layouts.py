"""
Tenchage-ppt v3.2 — 7 个新版式生成器
作者：哈小助
适用：腾讯智慧零售售前/咨询场景
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ========== 色彩系统（与 ppt-master 对齐 + Tenchage 主蓝） ==========
C_PRIMARY = RGBColor(0x1A, 0x50, 0xD6)     # Tenchage 主蓝
C_PRIMARY_DEEP = RGBColor(0x0E, 0x2F, 0x7E) # 深蓝
C_ORANGE = RGBColor(0xF3, 0x9C, 0x2A)       # 橙
C_GREEN = RGBColor(0x00, 0xA4, 0x5D)        # 绿
C_RED = RGBColor(0xE0, 0x3E, 0x36)          # 高亮红
C_YELLOW = RGBColor(0xFF, 0xC9, 0x39)       # 分享方黄
C_INK = RGBColor(0x1F, 0x29, 0x37)          # 主文字
C_GRAY = RGBColor(0x6B, 0x72, 0x80)         # 副文字
C_LIGHT = RGBColor(0xF5, 0xF7, 0xFB)        # 卡背景
C_LIGHT_BLUE = RGBColor(0xCC, 0xDD, 0xFF)   # Agenda 装饰浅蓝
C_BRIGHT_BLUE = RGBColor(0x2E, 0x6CFF & 0xFF, 0xFF)  # 不用
C_BRIGHT_BLUE = RGBColor(0x2E, 0x6C, 0xFF)
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
C_SHADOW = RGBColor(0xE0, 0xE6, 0xF1)        # 卡片阴影色（v3.9.6，与 A 路径 CLR.shadow 对齐）

# 16:9 尺寸（英寸）
SLIDE_W, SLIDE_H = 13.333, 7.5

# ========== 字体系统 ==========
# 标题/关键词/PART编号/卡片标题/金句条 → 腾讯体 W7
# 正文/说明/副标题/页码 → 腾讯体 W3
# Emoji 图标 → Segoe UI Emoji（emoji 字体保持原样，否则不显示）
FONT_BOLD = '腾讯体 W7'
FONT_REG  = '腾讯体 W3'
FONT_EMOJI = 'Segoe UI Emoji'

# ========== 字号铁律（v3.9.2 哈哥拍板）==========
# 正文最小字号 12pt。低于此值的文字投屏看不清。
# add_text 内部强制兜底：任何 < MIN_FONT_SIZE 的字号自动抬到 12。
# 仅页码 / 角标 / 装饰小字可显式传 allow_small=True 破例。
MIN_FONT_SIZE = 12

# ========== 工具函数 ==========
def set_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()

def set_outline(shape, color, width=0.75):
    shape.line.color.rgb = color
    shape.line.width = Pt(width)


# ========== v3.9 填充增强：半透明 + 渐变（学自 ppt-master 文本框底色）==========

def _hex(color):
    """RGBColor / 'RRGGBB' / '#RRGGBB' / (r,g,b) -> 'RRGGBB' 大写无井号"""
    if isinstance(color, RGBColor):
        return str(color)
    if isinstance(color, (tuple, list)) and len(color) == 3:
        return '%02X%02X%02X' % tuple(color)
    s = str(color).lstrip('#').upper()
    return s


def set_fill_alpha(shape, color, alpha=1.0, line=False):
    """
    纯色填充 + 透明度（半透明底色）。

    参数：
        shape : 形状对象
        color : 颜色（RGBColor / 'RRGGBB' / '#RRGGBB' / (r,g,b)）
        alpha : 不透明度 0.0(全透明)-1.0(不透明)，如 0.85 = 15% 透明
        line  : 是否同时去掉描边（默认 True 去边）

    原理：python-pptx 没有 alpha API，直接操作 solidFill 的 srgbClr 子元素，
          插入 <a:alpha val="xxxxx"/>（val 是千分比 * 100，范围 0-100000）。
    """
    shape.fill.solid()
    shape.fill.fore_color.rgb = (color if isinstance(color, RGBColor)
                                  else RGBColor.from_string(_hex(color)))
    if not line:
        shape.line.fill.background()

    # 取到 solidFill -> srgbClr，注入 alpha
    sp = shape.fill._xPr  # spPr 元素
    nsmap = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    # 找到 solidFill/srgbClr
    srgb = sp.find(qn('a:solidFill') + '/' + qn('a:srgbClr'))
    if srgb is None:
        # 兼容不同 python-pptx 路径
        sf = sp.find(qn('a:solidFill'))
        if sf is not None:
            srgb = sf.find(qn('a:srgbClr'))
    if srgb is not None:
        # 删旧 alpha
        for old in srgb.findall(qn('a:alpha')):
            srgb.remove(old)
        a = etree.SubElement(srgb, qn('a:alpha'))
        a.set('val', str(int(max(0.0, min(1.0, alpha)) * 100000)))
    return shape


def set_fill_gradient(shape, color1, color2, color3=None,
                      angle=90, alpha=1.0, line=False):
    """
    线性渐变填充（双色或三色）。

    参数：
        shape  : 形状对象
        color1 : 起始色（0%）
        color2 : 结束色（100%，双色时）/ 中间色（50%，三色时）
        color3 : 三色渐变的结束色（100%），为 None 则双色
        angle  : 渐变角度（度），0=从左到右，90=从上到下（默认），45=左上→右下
        alpha  : 整体不透明度 0.0-1.0（应用到每个 stop）
        line   : 是否保留描边（默认 True 去边）

    原理：直接写 <a:gradFill> XML，python-pptx 无原生渐变 API。
    """
    sp = shape.fill._xPr  # spPr

    # 删掉现有 fill 节点
    for tag in ('a:noFill', 'a:solidFill', 'a:gradFill', 'a:blipFill',
                'a:pattFill', 'a:grpFill'):
        for el in sp.findall(qn(tag)):
            sp.remove(el)

    # 构建 stops
    if color3 is not None:
        stops = [(0, color1), (50, color2), (100, color3)]
    else:
        stops = [(0, color1), (100, color2)]

    alpha_val = str(int(max(0.0, min(1.0, alpha)) * 100000))

    # gradFill
    grad = etree.SubElement(sp, qn('a:gradFill'))
    grad.set('flip', 'none')
    grad.set('rotWithShape', '1')
    gsLst = etree.SubElement(grad, qn('a:gsLst'))
    for pos, col in stops:
        gs = etree.SubElement(gsLst, qn('a:gs'))
        gs.set('pos', str(int(pos * 1000)))  # 千分比
        srgb = etree.SubElement(gs, qn('a:srgbClr'))
        srgb.set('val', _hex(col))
        if alpha < 1.0:
            a = etree.SubElement(srgb, qn('a:alpha'))
            a.set('val', alpha_val)
    # 线性方向：PPT 角度单位 1/60000 度
    lin = etree.SubElement(grad, qn('a:lin'))
    lin.set('ang', str(int(angle * 60000) % 21600000))
    lin.set('scaled', '1')

    # gradFill 必须在 spPr 中位于 ln 之前——重新排序：把 grad 移到正确位置
    # 简化：直接保证 grad 在 prstGeom/custGeom 之后即可，python-pptx 通常已处理
    if not line:
        shape.line.fill.background()
    return shape

def set_shadow(shape, blur=10, offset=3, angle=90, color='000000', opacity=0.5):
    """
    弥散投影（外阴影）。v3.9.6 新增，补齐 B 路径阴影能力缺口
    （A 路径 pptxgenjs 早有 shadow 参数，B 路径 python-pptx 一直没有对应函数）。

    参数：
        shape   : 形状对象
        blur    : 模糊半径，单位 pt（对应 A 路径的 blur，默认 10）
        offset  : 投影偏移距离，单位 pt（对应 A 路径的 offset，默认 3）
        angle   : 投影方向角度（度），0=右, 90=下（默认，即向下投影）, 180=左, 270=上
        color   : 阴影颜色（RGBColor / 'RRGGBB' / '#RRGGBB' / (r,g,b)），
                  默认纯黑，卡片阴影建议传色板里的 E0E6F1（浅蓝灰卡片阴影色）
        opacity : 阴影不透明度 0.0(全透明)-1.0(不透明)，默认 0.5

    原理：python-pptx 无原生阴影 API，直接写 <a:effectLst><a:outerShdw>，
          单位换算：pt → EMU（1pt = 12700 EMU），PPT 角度单位 1/60000 度。

    用法：
        set_shadow(shape, blur=10, offset=3, angle=90, color=C_LIGHT_BLUE_SHADOW, opacity=0.5)
    """
    sp = shape.fill._xPr  # spPr
    # 删掉已有 effectLst（避免重复叠加）
    for el in sp.findall(qn('a:effectLst')):
        sp.remove(el)

    effect_lst = etree.SubElement(sp, qn('a:effectLst'))
    outer_shdw = etree.SubElement(effect_lst, qn('a:outerShdw'))
    outer_shdw.set('blurRad', str(int(blur * 12700)))
    outer_shdw.set('dist', str(int(offset * 12700)))
    outer_shdw.set('dir', str(int(angle * 60000) % 21600000))
    outer_shdw.set('rotWithShape', '0')
    srgb = etree.SubElement(outer_shdw, qn('a:srgbClr'))
    srgb.set('val', _hex(color))
    if opacity < 1.0:
        a = etree.SubElement(srgb, qn('a:alpha'))
        a.set('val', str(int(max(0.0, min(1.0, opacity)) * 100000)))
    return shape


def _enforce_min(sz, allow_small):
    """字号铁律兜底：低于 MIN_FONT_SIZE(12) 自动抬到 12，除非 allow_small=True"""
    if allow_small:
        return sz
    try:
        return max(float(sz), float(MIN_FONT_SIZE))
    except (TypeError, ValueError):
        return sz


def add_text(slide, x, y, w, h, text, size=14, bold=False, color=C_INK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=None,
             italic=False, allow_small=False):
    """
    字体策略：
      - 调用方未显式传 font 时，bold=True → 腾讯体 W7，bold=False → 腾讯体 W3
      - 调用方显式传 font（如 Segoe UI Emoji / Arial 数字编号）则保留

    字号铁律（v3.9.2）：
      - 正文最小字号 12pt，任何 size < 12 自动抬到 12
      - 仅页码/角标/装饰小字传 allow_small=True 才允许更小
      - 多 run 列表里每个 run 的 size 同样受此约束
    """
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    # 默认字体根据 bold 自动选
    default_font = font if font else (FONT_BOLD if bold else FONT_REG)
    if isinstance(text, list):
        # 多 run 列表 [{text, size, bold, color, italic, font}]
        for i, run_cfg in enumerate(text):
            r = p.add_run() if i > 0 else p.add_run()
            r.text = run_cfg.get('text', '')
            r.font.size = Pt(_enforce_min(run_cfg.get('size', size), allow_small))
            run_bold = run_cfg.get('bold', bold)
            r.font.bold = run_bold
            r.font.italic = run_cfg.get('italic', italic)
            # run 级字体：显式传则用，否则按 bold 自动选
            run_font = run_cfg.get('font', None)
            if run_font is None:
                run_font = FONT_BOLD if run_bold else FONT_REG
            r.font.name = run_font
            c = run_cfg.get('color', color)
            r.font.color.rgb = c
    else:
        r = p.add_run()
        r.text = text
        r.font.size = Pt(_enforce_min(size, allow_small))
        r.font.bold = bold
        r.font.italic = italic
        r.font.name = default_font
        r.font.color.rgb = color
    return tb

def add_rect(slide, x, y, w, h, color, line_color=None, rounded=False, radius=0.08):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    if rounded:
        # 设置圆角度
        try:
            shape.adjustments[0] = radius
        except:
            pass
    set_fill(shape, color)
    if line_color is None:
        shape.line.fill.background()
    else:
        set_outline(shape, line_color)
    return shape

def add_circle(slide, x, y, d, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    set_fill(shape, color)
    return shape

def page_bg(slide, color=C_WHITE):
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, color)

def add_logo_block(slide, brand_logo_text='腾讯智慧零售  Tencent Smart Retail'):
    """右上角 Logo 区（文字版 Logo，适配可变品牌）"""
    add_text(slide, SLIDE_W-3.5, 0.25, 3.3, 0.45, brand_logo_text,
             size=10, bold=True, color=C_INK, align=PP_ALIGN.RIGHT, allow_small=True)

def add_page_num(slide, num):
    add_text(slide, SLIDE_W/2-0.5, SLIDE_H-0.4, 1, 0.3, f'- {num} -',
             size=9, color=C_GRAY, align=PP_ALIGN.CENTER, allow_small=True)

# ========== Layout 1: agenda_premium ==========
def layout_agenda_premium(slide, title_en='Agenda', title_cn='本次研讨议程',
                          parts=None, logo_text='腾讯智慧零售  Tencent Smart Retail',
                          page_num=2):
    page_bg(slide, C_WHITE)
    parts = parts or []
    n = len(parts)

    # 右上+右下蓝色错位矩形装饰
    add_rect(slide, SLIDE_W-2.0, 0, 2.0, 0.6, C_BRIGHT_BLUE)
    add_rect(slide, SLIDE_W-3.5, 0.6, 1.5, 0.4, C_LIGHT_BLUE)
    add_rect(slide, SLIDE_W-1.2, SLIDE_H-0.7, 1.2, 0.7, C_BRIGHT_BLUE)
    add_rect(slide, SLIDE_W-2.5, SLIDE_H-0.4, 1.3, 0.4, C_LIGHT_BLUE)

    # 顶部 Logo
    add_logo_block(slide, logo_text)

    # 左上标题：Agenda（斜体大字）+ 本次研讨议程
    add_text(slide, 0.7, 0.85, 4.0, 1.2, 'Agenda',
             size=54, bold=True, italic=True, color=C_PRIMARY, font=FONT_BOLD)
    add_text(slide, 0.7, 1.85, 4.0, 0.5, title_cn,
             size=18, bold=True, color=C_INK)
    # 橙色短分隔线
    add_rect(slide, 0.75, 2.35, 0.6, 0.06, C_ORANGE)

    # Part 大白卡（4-8 动态适配）
    card_top = 2.7
    card_bottom = SLIDE_H - 0.6
    card_h_total = card_bottom - card_top
    if n <= 4:
        rows = n
        cols = 1
        row_h = card_h_total / max(rows, 1)
        for i, part in enumerate(parts):
            y = card_top + i * row_h
            card_x, card_w = 0.7, SLIDE_W - 1.4
            # 白卡 + 浅边框
            add_rect(slide, card_x, y+0.05, card_w, row_h-0.15, C_LIGHT, line_color=None, rounded=True, radius=0.05)
            # Part 编号
            add_text(slide, card_x+0.3, y+0.15, 1.5, 0.5,
                     f'Part {i+1:02d}', size=22, bold=True, italic=True, color=C_PRIMARY, font=FONT_BOLD)
            # 主标题
            add_text(slide, card_x+1.9, y+0.1, card_w-2.2, 0.55,
                     part.get('title', ''), size=17, bold=True, color=C_INK)
            # 副标题
            add_text(slide, card_x+1.9, y+0.55, card_w-2.2, 0.4,
                     '▸  ' + part.get('subtitle', ''), size=11, color=C_GRAY)
    else:
        # 5-8 Part：双栏布局
        cols = 2
        rows = (n + 1) // 2
        row_h = card_h_total / max(rows, 1)
        col_w = (SLIDE_W - 1.4 - 0.3) / 2
        for i, part in enumerate(parts):
            r, c = divmod(i, 2)
            y = card_top + r * row_h
            x = 0.7 + c * (col_w + 0.3)
            add_rect(slide, x, y+0.05, col_w, row_h-0.15, C_LIGHT, rounded=True, radius=0.05)
            add_text(slide, x+0.2, y+0.15, 1.2, 0.4,
                     f'Part {i+1:02d}', size=16, bold=True, italic=True, color=C_PRIMARY, font=FONT_BOLD)
            add_text(slide, x+1.4, y+0.1, col_w-1.5, 0.45,
                     part.get('title', ''), size=13, bold=True, color=C_INK)
            add_text(slide, x+1.4, y+0.5, col_w-1.5, 0.4,
                     '▸  ' + part.get('subtitle', ''), size=9, color=C_GRAY)

    add_page_num(slide, page_num)


# ========== Layout 2: chapter_premium ==========
def layout_chapter_premium(slide, part_no='01', chapter_name='前置洞察',
                           subtitle='打破关于消费者运营的 2 个反常识',
                           logo_text='腾讯智慧零售  Tencent Smart Retail',
                           page_num=3):
    page_bg(slide, C_PRIMARY)
    # 右侧装饰矩形
    add_rect(slide, SLIDE_W-3.5, 0, 3.5, 1.2, C_BRIGHT_BLUE)
    add_rect(slide, SLIDE_W-2.0, 1.2, 2.0, 0.5, C_LIGHT_BLUE)
    add_rect(slide, SLIDE_W-1.5, SLIDE_H-1.2, 1.5, 1.2, C_PRIMARY_DEEP)
    add_rect(slide, SLIDE_W-3.0, SLIDE_H-0.6, 1.5, 0.6, C_BRIGHT_BLUE)

    # Logo（白色版）
    add_text(slide, SLIDE_W-3.5, 0.25, 3.3, 0.45, logo_text,
             size=10, bold=True, color=C_WHITE, align=PP_ALIGN.RIGHT, allow_small=True)

    # 橙色 PART 胶囊
    cap = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(0.9), Inches(2.4), Inches(2.6), Inches(0.7))
    try:
        cap.adjustments[0] = 0.5
    except:
        pass
    set_fill(cap, C_ORANGE)
    cap.line.fill.background()
    add_text(slide, 0.9, 2.4, 2.6, 0.7, f'PART {part_no}',
             size=22, bold=True, italic=True, color=C_WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_BOLD)

    # 章名大字
    add_text(slide, 0.9, 3.3, 10, 1.4, chapter_name,
             size=64, bold=True, color=C_WHITE)

    # 橙色短分隔线
    add_rect(slide, 0.95, 4.85, 0.8, 0.08, C_ORANGE)

    # 副标题
    add_text(slide, 0.9, 5.05, 10, 0.6, subtitle,
             size=18, color=C_WHITE)

    # 页码（白色）
    add_text(slide, SLIDE_W/2-0.5, SLIDE_H-0.4, 1, 0.3, f'- {page_num} -',
             size=9, color=C_LIGHT_BLUE, align=PP_ALIGN.CENTER)


# ========== Layout 3: closing_premium（4 变量） ==========
def layout_closing_premium(slide, brand='伊利', scenario='集团消费者运营',
                           date='2026.05', subtitle='第二部分：微信生态全域运营新洞察与实战框架',
                           logo_text='腾讯智慧零售  Tencent Smart Retail',
                           page_num=14):
    page_bg(slide, C_PRIMARY)
    # 装饰
    add_rect(slide, SLIDE_W-3.5, 0, 3.5, 1.0, C_BRIGHT_BLUE)
    add_rect(slide, 0, SLIDE_H-1.5, 1.5, 1.5, C_PRIMARY_DEEP)
    add_rect(slide, SLIDE_W-1.5, SLIDE_H-0.8, 1.5, 0.8, C_BRIGHT_BLUE)

    # Logo
    add_text(slide, SLIDE_W-3.5, 0.25, 3.3, 0.45, logo_text,
             size=10, bold=True, color=C_WHITE, align=PP_ALIGN.RIGHT, allow_small=True)

    # Thanks! 大斜体
    add_text(slide, 0.9, 1.6, 12, 2.2, 'Thanks!',
             size=110, bold=True, italic=True, color=C_WHITE, font=FONT_BOLD)

    # 中文副标
    add_text(slide, 0.9, 3.7, 12, 0.6,
             f'期待与{brand}共建全域消费者经营',
             size=22, bold=True, color=C_WHITE)

    # 橙色短分隔线
    add_rect(slide, 0.95, 4.5, 0.6, 0.06, C_ORANGE)

    # 黄色"分享方"标签
    tag = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(0.9), Inches(4.85), Inches(1.0), Inches(0.4))
    try:
        tag.adjustments[0] = 0.5
    except:
        pass
    set_fill(tag, C_YELLOW)
    tag.line.fill.background()
    add_text(slide, 0.9, 4.85, 1.0, 0.4, '分享方',
             size=11, bold=True, color=C_INK,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # 分享方文字
    add_text(slide, 2.0, 4.85, 10, 0.4,
             f'腾讯智慧零售 · {brand}{scenario} Workshop',
             size=14, color=C_WHITE, anchor=MSO_ANCHOR.MIDDLE)

    # 底部署名
    add_text(slide, 0.9, 5.5, 12, 0.4,
             f'{date} · {subtitle}',
             size=12, color=C_LIGHT_BLUE)


# ========== Layout 4: trend_3card_premium ==========
def layout_trend_3card_premium(slide, title='3 大趋势：消费者运营进入新阶段',
                               cards=None, logo_text='腾讯智慧零售  Tencent Smart Retail',
                               page_num=6):
    page_bg(slide, C_WHITE)
    add_logo_block(slide, logo_text)

    # 标题
    add_text(slide, 0.7, 0.5, 12, 0.7, title, size=24, bold=True, color=C_INK)
    add_rect(slide, 0.75, 1.2, 0.6, 0.08, C_ORANGE)

    cards = cards or []
    colors = [C_ORANGE, C_PRIMARY, C_GREEN]
    icons = ['🔥', '🎯', '⚡']
    card_w = (SLIDE_W - 0.7*2 - 0.4*2) / 3
    card_top = 1.6
    card_h = SLIDE_H - card_top - 0.6
    for i, c in enumerate(cards[:3]):
        x = 0.7 + i * (card_w + 0.4)
        color = colors[i]
        # 顶部彩色胶囊卡头（圆角矩形）
        cap = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                      Inches(x), Inches(card_top),
                                      Inches(card_w), Inches(0.85))
        try: cap.adjustments[0] = 0.2
        except: pass
        set_fill(cap, color)
        cap.line.fill.background()
        add_text(slide, x+0.2, card_top+0.1, card_w-0.4, 0.7,
                 c.get('tag', f'趋势 {i+1:02d}'),
                 size=14, bold=True, color=C_WHITE, anchor=MSO_ANCHOR.MIDDLE)
        # 圆形大图标
        ico_d = 0.9
        add_circle(slide, x + card_w/2 - ico_d/2, card_top + 1.0, ico_d, C_LIGHT)
        add_text(slide, x + card_w/2 - ico_d/2, card_top + 1.0, ico_d, ico_d,
                 icons[i], size=32, color=color,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                 font='Segoe UI Emoji')
        # 主标题
        add_text(slide, x+0.2, card_top+2.05, card_w-0.4, 0.55,
                 c.get('title', ''), size=15, bold=True, color=C_INK,
                 align=PP_ALIGN.CENTER)
        # 副标题（灰色）
        add_text(slide, x+0.2, card_top+2.6, card_w-0.4, 0.5,
                 c.get('subtitle', ''), size=10, color=C_GRAY,
                 align=PP_ALIGN.CENTER)
        # 火苗"真相洞察"
        add_text(slide, x+0.25, card_top+3.2, card_w-0.5, 0.3,
                 [{'text': '🔍 ', 'size': 11, 'color': color, 'font': 'Segoe UI Emoji'},
                  {'text': '真相洞察', 'size': 11, 'bold': True, 'color': color}])
        add_text(slide, x+0.25, card_top+3.5, card_w-0.5, 0.7,
                 c.get('insight', ''), size=10, color=C_INK)
        # 勾选"最佳实践"
        add_text(slide, x+0.25, card_top+4.3, card_w-0.5, 0.3,
                 [{'text': '✓ ', 'size': 11, 'color': color, 'bold': True, 'font': FONT_BOLD},
                  {'text': '最佳实践', 'size': 11, 'bold': True, 'color': color}])
        add_text(slide, x+0.25, card_top+4.6, card_w-0.5, 0.7,
                 c.get('practice', ''), size=10, color=C_INK)

    add_page_num(slide, page_num)


# ========== Layout 5: framework_table_color ==========
def layout_framework_table_color(slide, title='消费者运营五层框架',
                                  headers=None, rows=None,
                                  logo_text='腾讯智慧零售  Tencent Smart Retail',
                                  page_num=9):
    page_bg(slide, C_WHITE)
    add_logo_block(slide, logo_text)
    add_text(slide, 0.7, 0.5, 12, 0.7, title, size=24, bold=True, color=C_INK)
    add_rect(slide, 0.75, 1.2, 0.6, 0.08, C_ORANGE)

    headers = headers or ['维度', '触达', '留存', '转化', '复购']
    rows = rows or []
    row_colors = [C_ORANGE, C_PRIMARY, C_GREEN, C_PRIMARY_DEEP]

    table_top = 1.7
    table_left = 0.7
    table_w = SLIDE_W - 1.4
    n_cols = len(headers)
    col_w_first = 1.8
    col_w = (table_w - col_w_first) / (n_cols - 1)
    header_h = 0.55
    row_h = (SLIDE_H - table_top - 0.7 - header_h) / max(len(rows), 1)

    # 表头
    for i, h in enumerate(headers):
        x = table_left + (col_w_first if i > 0 else 0) + (i-1) * col_w if i > 0 else table_left
        w = col_w_first if i == 0 else col_w
        bg = C_INK if i == 0 else C_PRIMARY
        add_rect(slide, x, table_top, w, header_h, bg)
        add_text(slide, x, table_top, w, header_h, h,
                 size=13, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # 行
    for ri, row in enumerate(rows):
        y = table_top + header_h + ri * row_h
        row_color = row_colors[ri % len(row_colors)]
        # 行头（彩色）
        add_rect(slide, table_left, y, col_w_first, row_h, row_color)
        add_text(slide, table_left+0.1, y, col_w_first-0.2, row_h, row.get('label', ''),
                 size=13, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        # 数据列
        cells = row.get('cells', [])
        for ci in range(n_cols-1):
            x = table_left + col_w_first + ci * col_w
            bg = C_LIGHT if ri % 2 == 0 else C_WHITE
            add_rect(slide, x, y, col_w, row_h, bg, line_color=RGBColor(0xE5,0xE7,0xEB))
            txt = cells[ci] if ci < len(cells) else ''
            add_text(slide, x+0.1, y+0.1, col_w-0.2, row_h-0.2, txt,
                     size=10, color=C_INK, anchor=MSO_ANCHOR.MIDDLE)

    add_page_num(slide, page_num)


# ========== Layout 6: four_layer_pillar ==========
def layout_four_layer_pillar(slide, title='全域运营 4 大支柱',
                             pillars=None, quote='让每一次触达都成为品牌资产',
                             logo_text='腾讯智慧零售  Tencent Smart Retail',
                             page_num=11):
    page_bg(slide, C_WHITE)
    add_logo_block(slide, logo_text)
    add_text(slide, 0.7, 0.5, 12, 0.7, title, size=24, bold=True, color=C_INK)
    add_rect(slide, 0.75, 1.2, 0.6, 0.08, C_ORANGE)

    pillars = pillars or []
    colors = [C_ORANGE, C_PRIMARY, C_GREEN, C_PRIMARY_DEEP]
    n = len(pillars)
    pillar_top = 1.7
    pillar_h = 4.4
    col_w = (SLIDE_W - 1.4 - 0.3*(n-1)) / n
    for i, p in enumerate(pillars):
        x = 0.7 + i * (col_w + 0.3)
        color = colors[i % 4]
        # 头部色块
        add_rect(slide, x, pillar_top, col_w, 0.7, color)
        add_text(slide, x, pillar_top, col_w, 0.7, p.get('tag', f'支柱 0{i+1}'),
                 size=15, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        # 浅色卡身
        add_rect(slide, x, pillar_top+0.7, col_w, pillar_h-0.7, C_LIGHT)
        # 标题
        add_text(slide, x+0.2, pillar_top+0.9, col_w-0.4, 0.5,
                 p.get('title', ''), size=14, bold=True, color=C_INK,
                 align=PP_ALIGN.CENTER)
        # 要点列表
        bullets = p.get('bullets', [])
        for bi, b in enumerate(bullets):
            add_text(slide, x+0.25, pillar_top+1.5+bi*0.55, col_w-0.5, 0.5,
                     [{'text': '● ', 'size': 11, 'color': color, 'bold': True},
                      {'text': b, 'size': 10.5, 'color': C_INK}])

    # 底部蓝色金句条（带左右双引号）
    quote_y = pillar_top + pillar_h + 0.25
    add_rect(slide, 0.7, quote_y, SLIDE_W-1.4, 0.7, C_PRIMARY)
    add_text(slide, 0.85, quote_y, 0.5, 0.7, '"', size=32, bold=True,
             color=C_ORANGE, anchor=MSO_ANCHOR.MIDDLE, font=FONT_BOLD)
    add_text(slide, 1.2, quote_y, SLIDE_W-2.8, 0.7, quote,
             size=15, bold=True, color=C_WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, SLIDE_W-1.35, quote_y, 0.5, 0.7, '"', size=32, bold=True,
             color=C_ORANGE, anchor=MSO_ANCHOR.MIDDLE, font=FONT_BOLD)

    add_page_num(slide, page_num)


# ========== Layout 7: four_module_2x2_breakthrough ==========
def layout_four_module_2x2_breakthrough(slide, title='四模块落地执行框架',
                                         modules=None, quote='打破点位思维，构建闭环资产',
                                         logo_text='腾讯智慧零售  Tencent Smart Retail',
                                         page_num=13):
    page_bg(slide, C_WHITE)
    add_logo_block(slide, logo_text)
    add_text(slide, 0.7, 0.5, 12, 0.7, title, size=24, bold=True, color=C_INK)
    add_rect(slide, 0.75, 1.2, 0.6, 0.08, C_ORANGE)

    modules = modules or []
    colors = [C_ORANGE, C_PRIMARY, C_GREEN, C_PRIMARY_DEEP]
    icons = ['📍', '👥', '🛒', '📊']
    grid_top = 1.7
    grid_h = 4.7
    grid_w = SLIDE_W - 1.4
    cell_w = (grid_w - 0.25) / 2
    cell_h = (grid_h - 0.25) / 2
    left_w = 1.8  # 左侧彩色卡宽度

    for i, m in enumerate(modules[:4]):
        r, c = divmod(i, 2)
        cx = 0.7 + c * (cell_w + 0.25)
        cy = grid_top + r * (cell_h + 0.25)
        color = colors[i]

        # 左侧彩色卡（图标 + 模块名）
        add_rect(slide, cx, cy, left_w, cell_h, color)
        # 大图标
        add_text(slide, cx, cy+0.2, left_w, 0.9, icons[i],
                 size=40, color=C_WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                 font='Segoe UI Emoji')
        # 模块名（大字）
        add_text(slide, cx+0.1, cy+1.3, left_w-0.2, 0.6,
                 m.get('name', ''), size=18, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER)
        # 模块副标题（小字）
        add_text(slide, cx+0.1, cy+1.95, left_w-0.2, 0.4,
                 m.get('subname', ''), size=10, color=C_WHITE,
                 align=PP_ALIGN.CENTER)

        # 右侧浅色卡（突破点 ①②）
        rx = cx + left_w
        rw = cell_w - left_w
        add_rect(slide, rx, cy, rw, cell_h, C_LIGHT)
        breakthroughs = m.get('breakthroughs', [])
        for bi, b in enumerate(breakthroughs[:2]):
            by = cy + 0.15 + bi * (cell_h-0.3)/2
            # 突破点①标签（彩色）
            add_text(slide, rx+0.15, by, rw-0.3, 0.3,
                     f'突破点 {"①" if bi==0 else "②"}',
                     size=11, bold=True, color=color)
            # 关键词（粗体）
            add_text(slide, rx+0.15, by+0.3, rw-0.3, 0.4,
                     b.get('keyword', ''), size=12, bold=True, color=C_INK)
            # 描述
            add_text(slide, rx+0.15, by+0.7, rw-0.3, 0.5,
                     b.get('desc', ''), size=9.5, color=C_GRAY)

    # 底部蓝色金句条
    quote_y = grid_top + grid_h + 0.05
    add_rect(slide, 0.7, quote_y, SLIDE_W-1.4, 0.55, C_PRIMARY)
    add_text(slide, 0.85, quote_y, 0.4, 0.55, '"', size=24, bold=True,
             color=C_ORANGE, anchor=MSO_ANCHOR.MIDDLE, font=FONT_BOLD)
    add_text(slide, 1.2, quote_y, SLIDE_W-2.8, 0.55, quote,
             size=14, bold=True, color=C_WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, SLIDE_W-1.25, quote_y, 0.4, 0.55, '"', size=24, bold=True,
             color=C_ORANGE, anchor=MSO_ANCHOR.MIDDLE, font=FONT_BOLD)

    add_page_num(slide, page_num)


# ========== Layout 8: cards_3col_section（章节内页·N列彩卡+底部金句） ==========
# 用于：分节展示 2 / 3 张并列彩色卡片（橙/蓝/绿），每卡支持 双段（真相洞察 + 最佳实践）
# 或自定义段（关键点①/关键点②）。底部带蓝色金句横条（含黄色高亮 + 角点装饰）。
# 适用：渠道融合趋势页、公私域联动页、AI 突破点页、蒙牛/光明同结构内容页。
def layout_cards_3col_section(slide,
        title='', title_accent='',
        subtitle='',
        cards=None,
        quote='', quote_highlights=None,
        logo_text='腾讯智慧零售  Tencent Smart Retail',
        page_num=6):
    """
    cards: list[dict]，2 或 3 张卡。每张卡支持以下字段：
        - color: 'orange' / 'blue' / 'green'（决定 badge / icon / 标签 / 高亮色）
        - badge: 顶部胶囊标签文字，如 '趋势 ①' 或 '趋势 ④ · P2P'
        - icon: emoji，如 '📍' '🔄' '🛵' '🤝' '🤖'
        - title: 卡主标题（黑色大字）
        - subtitle: 卡副标题（灰色小字）
        - sections: list[dict]，每段一个 dict：
              {'label': '真相洞察' / '关键点 ①', 'icon': '⚡' / '✓',
               'text': 正文（可含 \\n 换行）,
               'highlights': ['关键词1', '关键词2']  # 这些词会被加粗变色
              }
        - footer: 卡底彩色一句话（可选，仅当只有 2 段时建议用）
    quote: 底部金句横条文字
    quote_highlights: list[str]，金句中要变黄的关键词
    """
    page_bg(slide, C_WHITE)

    # ===== 顶部装饰：蓝绿短横条 =====
    add_rect(slide, 0.6, 0.28, 0.85, 0.06, C_PRIMARY)
    add_rect(slide, 1.5, 0.28, 0.5, 0.06, C_GREEN)

    # ===== 右上 logo 区 =====
    add_text(slide, SLIDE_W-3.7, 0.22, 3.4, 0.3, logo_text,
             size=10, color=C_GRAY, align=PP_ALIGN.RIGHT)

    # ===== 主标题（左侧 4px 蓝竖条 + 黑字 + 蓝色 accent） =====
    add_rect(slide, 0.6, 0.7, 0.06, 0.5, C_PRIMARY)
    if title_accent:
        add_text(slide, 0.78, 0.65, 12, 0.6,
                 [{'text': title, 'size': 24, 'bold': True, 'color': C_INK, 'font': FONT_BOLD},
                  {'text': title_accent, 'size': 24, 'bold': True, 'color': C_PRIMARY, 'font': FONT_BOLD}],
                 anchor=MSO_ANCHOR.MIDDLE)
    else:
        add_text(slide, 0.78, 0.65, 12, 0.6, title,
                 size=24, bold=True, color=C_INK, anchor=MSO_ANCHOR.MIDDLE)

    # ===== 副标题（灰色一行） =====
    if subtitle:
        add_text(slide, 0.78, 1.22, 12, 0.3, subtitle,
                 size=12, color=C_GRAY)

    # ===== 卡片区 =====
    color_map = {
        'orange': C_ORANGE,
        'blue': C_PRIMARY,
        'green': C_GREEN,
    }
    cards = cards or []
    n = len(cards)
    if n not in (2, 3):
        n = min(max(n, 2), 3)
        cards = cards[:n]

    margin_x = 0.6
    gap = 0.3
    card_top = 1.65
    card_h = 4.65
    card_w = (SLIDE_W - margin_x*2 - gap*(n-1)) / n

    for i, c in enumerate(cards):
        color = color_map.get(c.get('color', 'blue'), C_PRIMARY)
        x = margin_x + i * (card_w + gap)

        # 卡片底（白色 + 彩色细边）
        card_shape = add_rect(slide, x, card_top, card_w, card_h,
                              C_WHITE, line_color=color, rounded=True, radius=0.05)
        try:
            card_shape.line.width = Pt(1.25)
        except:
            pass

        # 顶部彩色细横条
        add_rect(slide, x, card_top, card_w, 0.08, color)

        # 顶部胶囊 badge
        badge_w = 1.6 if len(c.get('badge', '')) > 6 else 1.1
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                        Inches(x+0.25), Inches(card_top+0.22),
                                        Inches(badge_w), Inches(0.34))
        try: badge.adjustments[0] = 0.5
        except: pass
        set_fill(badge, color)
        badge.line.fill.background()
        add_text(slide, x+0.25, card_top+0.22, badge_w, 0.34,
                 c.get('badge', ''), size=10, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

        # 大 emoji 图标（右上角）
        add_text(slide, x+card_w-0.85, card_top+0.18, 0.7, 0.55,
                 c.get('icon', ''), size=28, color=color,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                 font='Segoe UI Emoji')

        # 卡主标题
        add_text(slide, x+0.25, card_top+0.7, card_w-0.5, 0.45,
                 c.get('title', ''), size=15, bold=True, color=C_INK)

        # 卡副标题（灰）
        add_text(slide, x+0.25, card_top+1.15, card_w-0.5, 0.32,
                 c.get('subtitle', ''), size=10, color=C_GRAY)

        # 分隔细线
        add_rect(slide, x+0.25, card_top+1.55, card_w-0.5, 0.015, RGBColor(0xE5,0xE6,0xEB))

        # 内容段（动态 N 段，每段：标签 + 正文）
        sections = c.get('sections', [])
        sec_y = card_top + 1.7
        # 控制段间距（2 段时大间距，3 段及以上时压缩）
        max_sec_h = (card_h - 1.7 - 0.5) / max(len(sections), 1)
        for s_idx, sec in enumerate(sections):
            label_icon = sec.get('icon', '⚡')
            label_text = sec.get('label', '')
            # 标签：emoji + 加粗彩字
            add_text(slide, x+0.25, sec_y, card_w-0.5, 0.3,
                     [{'text': label_icon + ' ', 'size': 10, 'color': color,
                       'font': 'Segoe UI Emoji'},
                      {'text': label_text, 'size': 10, 'bold': True, 'color': color,
                       'font': FONT_BOLD}])
            sec_y += 0.32

            # 正文（支持高亮关键词 + 换行 \n）
            text = sec.get('text', '')
            highlights = sec.get('highlights', [])
            text_h = max_sec_h - 0.42
            _add_multiline_text(slide, x+0.25, sec_y, card_w-0.5, text_h,
                                text, size=10.5, color=C_INK,
                                highlights=highlights, hl_color=color)
            sec_y += text_h + 0.05

        # 卡底脚注（彩色一句话，可选）
        footer = c.get('footer', '')
        if footer:
            add_text(slide, x+0.25, card_top+card_h-0.45, card_w-0.5, 0.3,
                     footer, size=11, bold=True, color=color)

    # ===== 底部金句横条（蓝底白字 + 黄色高亮 + 角点装饰） =====
    if quote:
        quote_top = SLIDE_H - 0.95
        quote_h = 0.55
        bar = add_rect(slide, margin_x, quote_top, SLIDE_W-margin_x*2, quote_h,
                       C_PRIMARY, rounded=True, radius=0.15)
        # 角点装饰：左上 + 右下
        deco_color = RGBColor(0xFF, 0xFF, 0xFF)
        d1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                    Inches(margin_x+0.12), Inches(quote_top+0.12),
                                    Inches(0.13), Inches(0.13))
        set_fill(d1, deco_color)
        try: d1.fill.transparency = 0.6
        except: pass
        d1.line.fill.background()
        d2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                    Inches(SLIDE_W-margin_x-0.25), Inches(quote_top+quote_h-0.25),
                                    Inches(0.13), Inches(0.13))
        set_fill(d2, deco_color)
        d2.line.fill.background()

        # 金句文字（带黄色高亮，单行）
        _add_multiline_text(slide, margin_x+0.5, quote_top, SLIDE_W-margin_x*2-1, quote_h,
                            quote, size=14, color=C_WHITE, base_bold=True,
                            highlights=quote_highlights or [], hl_color=C_YELLOW,
                            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # 页码
    add_page_num(slide, page_num)


def _add_multiline_text(slide, x, y, w, h, text,
                         size=10.5, color=C_INK, base_bold=False,
                         highlights=None, hl_color=None,
                         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """
    支持 \\n 换行 + 关键词高亮（加粗变色）。
    一段文本 → 一个 textbox，多个 paragraph，每段多个 run。
    """
    highlights = highlights or []
    if hl_color is None:
        hl_color = C_PRIMARY

    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor

    lines = text.split('\n')
    for li, line in enumerate(lines):
        p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
        p.alignment = align
        # 切 highlight 子段
        if highlights:
            SEP = '\u0001'
            sentinel = line
            sorted_hls = sorted(set(highlights), key=lambda s: -len(s))
            for hl in sorted_hls:
                if hl in sentinel:
                    sentinel = sentinel.replace(hl, SEP + hl + SEP)
            parts = [pp for pp in sentinel.split(SEP) if pp]
        else:
            parts = [line] if line else ['']

        if not parts:
            parts = ['']

        for part in parts:
            r = p.add_run()
            r.text = part
            r.font.size = Pt(size)
            if part in highlights:
                r.font.bold = True
                r.font.color.rgb = hl_color
                r.font.name = FONT_BOLD
            else:
                r.font.bold = base_bold
                r.font.color.rgb = color
                r.font.name = FONT_BOLD if base_bold else FONT_REG
    return tb


def _split_with_highlights(text, highlights, hl_color,
                            base_color=C_INK, base_bold=False):
    """
    把一段含换行的文字切成多个 run。highlight 词加粗变色。
    返回 add_text 可用的 runs 列表。
    """
    if not highlights:
        return [{'text': text, 'color': base_color, 'bold': base_bold}]
    # 用占位符分隔
    SEP = '\u0001'
    sentinel = text
    # 先把所有 highlight 用同一占位符替换为 SEP+词+SEP
    # 长词优先匹配，避免短词把长词切碎
    sorted_hls = sorted(set(highlights), key=lambda s: -len(s))
    for hl in sorted_hls:
        sentinel = sentinel.replace(hl, SEP + hl + SEP)
    parts = sentinel.split(SEP)
    runs = []
    for p in parts:
        if not p:
            continue
        if p in highlights:
            runs.append({'text': p, 'color': hl_color, 'bold': True,
                         'font': FONT_BOLD})
        else:
            runs.append({'text': p, 'color': base_color, 'bold': base_bold})
    return runs


# ========== Layout: case_left_text_right_image_grid ==========
def layout_case_left_text_right_image_grid(slide,
    title_prefix='会员转化策略：',
    title_main='可以利用线上线下',
    title_highlights=None,           # list: [{text, color}] 高亮词组（按顺序）
    title_tail='，实现会员流量的全域转化',
    sections=None,                   # list of {label, text, highlights}
    images=None,                     # list of dict: {path, caption} 1-6 张
    image_cols=3,
    image_rows=None,                 # None=自动按数量
    bottom_caption='',
    logo_text='腾讯智慧零售  Tencent Smart Retail',
    page_num=32):
    """
    左文 + 右图网格 案例展示页（基于伊利乌苏卡券案例参考样式）。

    特征：
      - 顶部：左侧绿+蓝细色条 / 右上 logo
      - 主标题（黑色 28pt）：title_prefix + title_main + 多个蓝色/红色高亮词 + tail
      - 左侧 3-4 段说明：每段 「label：」(粗黑) + 正文(黑常规) + 关键词蓝色加粗
      - 右侧 N 张图片网格（默认 3 列 × 2 行）
      - 底部蓝色加粗小字图示说明（可选）

    适用场景：案例图证、产品截图墙、效果验证页
    """
    page_bg(slide, C_WHITE)

    # 顶部双色细条（绿 + 蓝），位置左上
    add_rect(slide, 0.55, 0.30, 0.55, 0.06, C_GREEN)
    add_rect(slide, 1.18, 0.30, 1.65, 0.06, C_PRIMARY)

    # 右上 Logo
    add_logo_block(slide, logo_text)

    # ---- 主标题 ----
    # 多 run 标题：title_prefix(黑加粗) + title_main(黑加粗) + highlights(逐段彩色) + tail(黑)
    title_runs = []
    title_runs.append({'text': title_prefix, 'size': 26, 'bold': True, 'color': C_INK, 'font': FONT_BOLD})
    title_runs.append({'text': title_main, 'size': 26, 'bold': True, 'color': C_INK, 'font': FONT_BOLD})
    for hl in (title_highlights or []):
        title_runs.append({
            'text': hl.get('text', ''),
            'size': 26,
            'bold': True,
            'color': hl.get('color', C_PRIMARY),
            'font': FONT_BOLD,
        })
    title_runs.append({'text': title_tail, 'size': 26, 'bold': True, 'color': C_INK, 'font': FONT_BOLD})

    add_text(slide, 0.55, 0.50, 12.3, 0.95, title_runs,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)

    # ---- 左侧文字区 ----
    text_x = 0.55
    text_y = 1.85
    text_w = 6.6
    section_h = 1.55  # 每段高度

    sections = sections or []
    for i, sec in enumerate(sections):
        label = sec.get('label', '')
        body = sec.get('text', '')
        hls = sec.get('highlights', [])

        sec_top = text_y + i * section_h

        # 段落 label：「策略设计：线上线下」 黑色加粗 16pt
        add_text(slide, text_x, sec_top, text_w, 0.4, label,
                 size=16, bold=True, color=C_INK, align=PP_ALIGN.LEFT)

        # 段落正文（多条要点，每条以 ■ 起头）
        # body 形如 [{'k':'场景化捆绑', 'v':'根据用户消费路径..., 触发跨品类消费。'}, ...]
        bullet_top = sec_top + 0.45
        if isinstance(body, list):
            for j, pt in enumerate(body):
                k = pt.get('k', '')
                v = pt.get('v', '')
                pt_hls = pt.get('highlights', [])
                # bullet ■  + key:  + value(含高亮词)
                runs = [
                    {'text': '■ ', 'size': 12, 'bold': True, 'color': C_INK, 'font': FONT_BOLD},
                    {'text': k + '：', 'size': 12, 'bold': True, 'color': C_INK, 'font': FONT_BOLD},
                ]
                # 拆分 value 中的高亮词
                value_runs = _split_with_highlights(v, pt_hls, C_PRIMARY,
                                                    base_color=C_INK, base_bold=False)
                for vr in value_runs:
                    runs.append({
                        'text': vr['text'],
                        'size': 12,
                        'bold': vr.get('bold', False),
                        'color': vr.get('color', C_INK),
                        'font': vr.get('font', FONT_REG if not vr.get('bold') else FONT_BOLD),
                    })
                add_text(slide, text_x + 0.05, bullet_top + j * 0.42, text_w - 0.1, 0.85, runs,
                         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
        else:
            # 简单字符串
            add_text(slide, text_x + 0.05, bullet_top, text_w - 0.1, 0.85, body,
                     size=12, color=C_INK, align=PP_ALIGN.LEFT)

    # ---- 右侧图片网格 ----
    images = images or []
    n = len(images)
    if n == 0:
        pass
    else:
        # 计算行列
        cols = image_cols
        rows = image_rows if image_rows else (n + cols - 1) // cols

        grid_x = 7.55
        grid_y = 1.55
        grid_w = 5.25
        grid_h = 5.30
        gap_x = 0.12
        gap_y = 0.18

        cell_w = (grid_w - gap_x * (cols - 1)) / cols
        cell_h = (grid_h - gap_y * (rows - 1)) / rows

        for idx, img in enumerate(images):
            r = idx // cols
            c = idx % cols
            cx = grid_x + c * (cell_w + gap_x)
            cy = grid_y + r * (cell_h + gap_y)
            try:
                slide.shapes.add_picture(
                    img['path'],
                    Inches(cx), Inches(cy),
                    width=Inches(cell_w), height=Inches(cell_h),
                )
            except Exception as e:
                # 占位
                add_rect(slide, cx, cy, cell_w, cell_h, C_LIGHT, line_color=C_GRAY)
                add_text(slide, cx, cy + cell_h/2 - 0.15, cell_w, 0.3,
                         f'图片缺失: {img.get("path", "")[:20]}',
                         size=8, color=C_GRAY, align=PP_ALIGN.CENTER)
            # caption
            cap = img.get('caption', '')
            if cap:
                add_text(slide, cx, cy + cell_h - 0.28, cell_w, 0.25, cap,
                         size=8, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

    # ---- 底部图示说明（蓝色加粗小字，居于图片区下方） ----
    if bottom_caption:
        add_text(slide, 7.55, 6.95, 5.25, 0.30, bottom_caption,
                 size=12, bold=True, color=C_INK, align=PP_ALIGN.CENTER)

    # 页码
    add_text(slide, SLIDE_W - 0.9, SLIDE_H - 0.35, 0.7, 0.25, f'-{page_num}-',
             size=9, color=C_GRAY, align=PP_ALIGN.RIGHT, allow_small=True)


# ========== v3.3 SVG 混合渲染能力 ==========
# 通过 svg_renderer + svg_templates 把复杂图表渲染成 PNG 嵌入 PPTX，
# 文字仍由 python-pptx 直出（保持可编辑性 + W7/W3 字体规范）。

def add_svg(slide, svg_str=None, template=None, data=None,
            x=0, y=0, w=4.0, h=3.0, render_w=1200, render_h=900,
            bg_color=None):
    """
    把 SVG 渲染成 PNG 嵌入到 slide。

    用法 1（直接传 SVG 字符串）：
        add_svg(slide, svg_str='<svg ...>...</svg>',
                x=7, y=1.5, w=5, h=5)

    用法 2（用内置模板）：
        add_svg(slide, template='funnel', data={'stages':[...]},
                x=7, y=1.5, w=5, h=5)

    参数：
        slide      : python-pptx slide 对象
        svg_str    : SVG 字符串（与 template 二选一）
        template   : SVG 模板名（funnel / radar / stairs / ring_progress / decor_bg）
        data       : 模板数据
        x, y       : PPT 坐标（英寸）
        w, h       : PPT 显示尺寸（英寸）
        render_w   : SVG 渲染宽度（像素，越大越清晰，默认 1200）
        render_h   : SVG 渲染高度（像素，默认 900）
        bg_color   : 背景色（None=透明）

    返回：
        picture shape 对象
    """
    # 延迟 import，让没装 playwright 的环境也能 import 本模块
    import sys, os
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from svg_renderer import svg_to_png
    from svg_templates import render as render_template

    # 拿到 SVG 字符串
    if svg_str is None:
        if template is None:
            raise ValueError('add_svg 必须传 svg_str 或 template')
        svg_str = render_template(template, data or {},
                                   width=render_w, height=render_h)

    # 渲染 PNG
    png_path = svg_to_png(svg_str, width=render_w, height=render_h,
                          bg_color=bg_color, use_cache=True)

    # 嵌入到 slide
    pic = slide.shapes.add_picture(png_path,
                                    Inches(x), Inches(y),
                                    Inches(w), Inches(h))
    return pic


# ========== v3.4 图标库能力（tabler-outline + tabler-filled）==========
import pathlib as _pathlib
_ICONS_ROOT = _pathlib.Path(__file__).parent.parent / 'templates' / 'icons'

def add_icon(slide, icon_name, style='outline',
              x=0, y=0, w=0.3, h=0.3,
              color='#1A50D6', alpha=1.0, render_size=256):
    """
    从图标库插入 SVG 图标，渲染成 PNG 嵌入到 slide。

    参数：
        icon_name   : 图标名（如 'chart-bar', 'arrow-right', 'check', 'flame'）
        style       : 'outline'（线框，默认）或 'filled'（填充）
        x, y, w, h  : PPT 坐标和尺寸（英寸），默认 0.3×0.3" 约 22pt 见方
        color       : 图标颜色（HEX 字符串，默认腾讯蓝 #1A50D6）
        alpha       : 透明度 0.0-1.0
        render_size : 渲染像素尺寸（默认 256，高清 2x 缩放到 PPT 显示）

    返回：
        picture shape 对象，失败返回 None

    用法示例：
        add_icon(slide, 'chart-bar', style='outline', x=0.5, y=0.5, color='#1A50D6')
        add_icon(slide, 'flame', style='filled', x=6.5, y=2.0, color='#FF6A00')
    """
    # 确定图标路径
    dir_name = f'tabler-{style}'
    icon_dir = _ICONS_ROOT / dir_name
    if not icon_dir.exists():
        return None

    # 尝试多种文件名格式
    candidates = [
        icon_dir / f'{icon_name}.svg',
        icon_dir / f'{icon_name.replace("-", "")}.svg',
    ]
    icon_path = None
    for c in candidates:
        if c.exists():
            icon_path = c
            break

    if icon_path is None:
        # 模糊搜索：按前缀匹配
        matches = list(icon_dir.glob(f'{icon_name}*.svg'))
        if matches:
            icon_path = matches[0]
        else:
            return None

    # 读取 SVG 并注入颜色
    svg_raw = icon_path.read_text(encoding='utf-8')
    # 替换 stroke 和 fill 颜色（保持原图标的 stroke-width）
    # 简单替换：把所有 stroke="currentColor" 或 stroke="#XXXXXX" 替换为指定颜色
    import re
    svg_colored = re.sub(r'stroke="[^"]+"', f'stroke="{color}"', svg_raw)
    svg_colored = re.sub(r'fill="[^"]+"', f'fill="{color}"', svg_colored)

    # 如果没有 viewBox，加一个
    if 'viewBox' not in svg_colored:
        w_attr = re.search(r'width="(\d+)"', svg_colored)
        h_attr = re.search(r'height="(\d+)"', svg_colored)
        if w_attr and h_attr:
            vb = f'viewBox="0 0 {w_attr.group(1)} {h_attr.group(1)}"'
            svg_colored = svg_colored.replace('>', f' {vb}>', 1)

    # 延迟 import，避免循环依赖
    import sys, os
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from svg_renderer import svg_to_png

    png_path = svg_to_png(svg_colored, width=render_size, height=render_size,
                          bg_color=None, use_cache=True)

    pic = slide.shapes.add_picture(png_path,
                                    Inches(x), Inches(y),
                                    Inches(w), Inches(h))
    return pic


def list_icons(query=None, style='outline', max_results=20):
    """
    搜索图标库，返回匹配图标名列表。

    参数：
        query       : 搜索关键词（如 'chart', 'arrow', 'check'）
        style       : 'outline' 或 'filled'
        max_results : 最大返回数量

    返回：
        图标名列表（去后缀 .svg）
    """
    dir_name = f'tabler-{style}'
    icon_dir = _ICONS_ROOT / dir_name
    if not icon_dir.exists():
        return []

    icons = sorted([p.stem for p in icon_dir.glob('*.svg')])
    if query:
        icons = [i for i in icons if query.lower() in i.lower()]
    return icons[:max_results]


# ========== v3.3 新版式：layout_data_chart_premium ==========
def layout_data_chart_premium(slide,
                               title='伊利全域消费者运营漏斗',
                               subtitle='5 阶段链路：从公域触达到口碑传播',
                               left_sections=None,
                               chart_template='funnel',
                               chart_data=None,
                               chart_render_size=(1200, 1000),
                               quote=None,
                               logo_text='腾讯智慧零售  Tencent Smart Retail',
                               page_num=1):
    """
    左文 + 右 SVG 数据图。文字 python-pptx 直出（可编辑），图表 SVG 渲染嵌入。

    适用场景：漏斗图/雷达图/阶梯图/环形进度等数据可视化页

    参数：
        title             : 主标题
        subtitle          : 副标题
        left_sections     : 左侧文字段落列表，每个 {label, text, highlight}
        chart_template    : SVG 模板名
        chart_data        : 模板数据
        chart_render_size : (render_w, render_h) SVG 渲染像素尺寸
        quote             : 底部金句条（可选）
    """
    # 顶部装饰条
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  Inches(0), Inches(0),
                                  Inches(SLIDE_W), Inches(0.08))
    set_fill(bar, C_PRIMARY)

    # 主标题
    add_text(slide, 0.5, 0.30, SLIDE_W - 1, 0.50, title,
             size=24, bold=True, color=C_INK)
    # 副标题
    if subtitle:
        add_text(slide, 0.5, 0.85, SLIDE_W - 1, 0.35, subtitle,
                 size=14, color=C_GRAY)

    # 左侧文字区（约占 5.5 英寸宽）
    LEFT_X = 0.5
    LEFT_W = 5.3
    LEFT_Y = 1.45

    if left_sections:
        cur_y = LEFT_Y
        for sec in left_sections:
            label = sec.get('label', '')
            text = sec.get('text', '')
            highlight = sec.get('highlight', '')

            # 左侧蓝色竖条 + label
            if label:
                bar2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                               Inches(LEFT_X), Inches(cur_y),
                                               Inches(0.10), Inches(0.32))
                set_fill(bar2, C_PRIMARY)
                add_text(slide, LEFT_X + 0.20, cur_y - 0.02,
                         LEFT_W - 0.2, 0.36, label,
                         size=15, bold=True, color=C_INK)
                cur_y += 0.42

            # 描述文字
            if text:
                # 多行 run：把 highlight 关键词加蓝加粗
                if highlight and highlight in text:
                    parts = text.split(highlight, 1)
                    runs = [
                        {'text': parts[0], 'bold': False, 'color': C_GRAY},
                        {'text': highlight, 'bold': True, 'color': C_PRIMARY},
                        {'text': parts[1], 'bold': False, 'color': C_GRAY},
                    ]
                    add_text(slide, LEFT_X + 0.20, cur_y, LEFT_W - 0.2, 1.2,
                             runs, size=12)
                else:
                    add_text(slide, LEFT_X + 0.20, cur_y, LEFT_W - 0.2, 1.2,
                             text, size=12, color=C_GRAY)
                cur_y += 0.95
            cur_y += 0.15

    # 右侧 SVG 图表
    rw, rh = chart_render_size
    add_svg(slide,
            template=chart_template,
            data=chart_data or {},
            x=6.0, y=1.30,
            w=7.0, h=5.30,
            render_w=rw, render_h=rh,
            bg_color=None)

    # 底部金句条
    if quote:
        bar3 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(0.5), Inches(6.85),
                                       Inches(SLIDE_W - 1.0), Inches(0.40))
        set_fill(bar3, C_PRIMARY)
        add_text(slide, 0.5, 6.85, SLIDE_W - 1.0, 0.40, quote,
                 size=13, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # logo + 页码
    add_text(slide, 0.5, SLIDE_H - 0.35, 6, 0.25, logo_text,
             size=9, color=C_GRAY, allow_small=True)
    add_text(slide, SLIDE_W - 0.9, SLIDE_H - 0.35, 0.7, 0.25,
             f'-{page_num}-', size=9, color=C_GRAY, align=PP_ALIGN.RIGHT, allow_small=True)


# ========== 主函数：生成伊利演示 PPT ==========
def build_demo(output_path, brand='伊利'):
    pres = Presentation()
    pres.slide_width = Inches(SLIDE_W)
    pres.slide_height = Inches(SLIDE_H)
    blank = pres.slide_layouts[6]

    LOGO = '腾讯智慧零售  Tencent Smart Retail'

    # ---- Slide 1: Agenda ----
    s = pres.slides.add_slide(blank)
    layout_agenda_premium(s,
        title_cn=f'{brand}全域消费者运营研讨议程',
        parts=[
            {'title': '前置洞察：打破 2 个反常识', 'subtitle': '消费者运营的本质是经营关系，而非投放'},
            {'title': '微信生态全域运营新洞察', 'subtitle': '3 个 O2O + 1 个 P2P + 1 个 AI 趋势'},
            {'title': '消费者运营五层框架', 'subtitle': '触达 / 留存 / 转化 / 复购 / 资产化'},
            {'title': '四模块落地执行框架', 'subtitle': '触点 / 留存 / 转化 / 数据 的突破路径'},
        ],
        logo_text=LOGO, page_num=2)

    # ---- Slide 2: Chapter (PART 01) ----
    s = pres.slides.add_slide(blank)
    layout_chapter_premium(s, part_no='01',
        chapter_name='前置洞察',
        subtitle='打破关于消费者运营的 2 个反常识',
        logo_text=LOGO, page_num=3)

    # ---- Slide 3: trend_3card_premium ----
    s = pres.slides.add_slide(blank)
    layout_trend_3card_premium(s,
        title='3 大趋势：消费者运营进入新阶段',
        cards=[
            {'tag': '趋势 01', 'title': '从流量思维到关系经营',
             'subtitle': '人货场全面重构',
             'insight': '流量见顶，企微+视频号成为留存关键',
             'practice': f'{brand}通过企微 1V1 触达，复购率提升 38%'},
            {'tag': '趋势 02', 'title': '从单点投放到全链路',
             'subtitle': '触点 + 链路双驱动',
             'insight': '8 大公域触点联动私域形成闭环资产',
             'practice': '可口可乐"码上有礼"打通 8 触点 → 单 SKU 拉新 230 万'},
            {'tag': '趋势 03', 'title': 'AI 重塑运营效率',
             'subtitle': '人效 × 智能化',
             'insight': '生成式 AI 让千人千面从口号变为可落地',
             'practice': f'{brand}AI 文案生成日产 5000+，节省人力 60%'},
        ],
        logo_text=LOGO, page_num=4)

    # ---- Slide 4: Chapter (PART 02) ----
    s = pres.slides.add_slide(blank)
    layout_chapter_premium(s, part_no='02',
        chapter_name='五层框架',
        subtitle='消费者运营的系统化方法论',
        logo_text=LOGO, page_num=5)

    # ---- Slide 5: framework_table_color ----
    s = pres.slides.add_slide(blank)
    layout_framework_table_color(s,
        title='消费者运营五层框架 · 全场景对照',
        headers=['场景', '触达手段', '留存触点', '转化路径', '资产沉淀'],
        rows=[
            {'label': '公域种草', 'cells': ['朋友圈广告 / 视频号信息流', '关注公众号 / 加企微', '小程序商城下单', '会员标签 + 行为数据']},
            {'label': '私域复购', 'cells': ['企微 1V1 / 社群', '订阅号软文 / 服务号通知', '小程序回购 / 直播秒杀', 'CDP 用户旅程']},
            {'label': '门店导流', 'cells': ['LBS 广告 / 一物一码', '门店企微社群', 'O2O 同城配送', '门店人群资产']},
            {'label': '会员经营', 'cells': ['会员日 EDM', '专属客服 / VIP 群', '积分兑换 / 升级特权', '会员生命周期模型']},
        ],
        logo_text=LOGO, page_num=6)

    # ---- Slide 6: Chapter (PART 03) ----
    s = pres.slides.add_slide(blank)
    layout_chapter_premium(s, part_no='03',
        chapter_name='4 大支柱',
        subtitle='全域运营的核心能力底座',
        logo_text=LOGO, page_num=7)

    # ---- Slide 7: four_layer_pillar ----
    s = pres.slides.add_slide(blank)
    layout_four_layer_pillar(s,
        title='全域运营 4 大支柱：从触达到资产',
        pillars=[
            {'tag': '支柱 01', 'title': '全触点矩阵',
             'bullets': ['8 大公域触点联动', '朋友圈+视频号+搜一搜', '一物一码+LBS', '门店导购企微']},
            {'tag': '支柱 02', 'title': '私域留存池',
             'bullets': ['公众号 + 企微 + 社群', '订阅号内容种草', '服务号交易触达', '会员体系沉淀']},
            {'tag': '支柱 03', 'title': '智能转化链路',
             'bullets': ['小程序商城闭环', '直播+短视频带货', 'AI 千人千面推送', 'CDP 旅程编排']},
            {'tag': '支柱 04', 'title': '数据资产化',
             'bullets': ['统一 ID 体系', '人群标签库', '行为数据沉淀', '全域归因模型']},
        ],
        quote=f'让{brand}每一次触达都成为可复用的品牌资产',
        logo_text=LOGO, page_num=8)

    # ---- Slide 8: Chapter (PART 04) ----
    s = pres.slides.add_slide(blank)
    layout_chapter_premium(s, part_no='04',
        chapter_name='落地执行',
        subtitle='四模块突破点 + 实战路径',
        logo_text=LOGO, page_num=9)

    # ---- Slide 9: four_module_2x2_breakthrough ----
    s = pres.slides.add_slide(blank)
    layout_four_module_2x2_breakthrough(s,
        title='四模块落地执行框架 · 8 大突破点',
        modules=[
            {'name': '触点', 'subname': 'Touchpoint',
             'breakthroughs': [
                {'keyword': '一物一码 + LBS 技术', 'desc': '商品瓶身扫码即触达，结合门店 LBS 实现"千店千面"'},
                {'keyword': '8 触点公域矩阵', 'desc': '朋友圈/视频号/搜一搜/小程序/服务号/订阅号/企微/社群联动'}]},
            {'name': '留存', 'subname': 'Retention',
             'breakthroughs': [
                {'keyword': '企微 1V1 高频触达', 'desc': '导购企微沉淀私域用户，平均触达频次提升 5 倍'},
                {'keyword': '社群运营 SOP', 'desc': '日历化内容 + 周期性活动，社群活跃度稳定 40%+'}]},
            {'name': '转化', 'subname': 'Conversion',
             'breakthroughs': [
                {'keyword': '小程序闭环交易', 'desc': '从种草到下单 3 步完成，转化漏斗缩短 60%'},
                {'keyword': '直播 + 短视频带货', 'desc': '视频号直播+短视频组合拳，单场 GMV 破百万'}]},
            {'name': '数据', 'subname': 'Data',
             'breakthroughs': [
                {'keyword': '腾讯 CDP 统一 ID', 'desc': '打通公私域全链路用户数据，构建 360° 用户画像'},
                {'keyword': '全域归因模型', 'desc': 'MTA 多触点归因，量化每一次投放的真实贡献'}]},
        ],
        quote=f'打破点位思维，让{brand}全域数据成为可复用资产',
        logo_text=LOGO, page_num=10)

    # ---- Slide 10: Closing ----
    s = pres.slides.add_slide(blank)
    layout_closing_premium(s,
        brand=brand,
        scenario='集团消费者运营',
        date='2026.05',
        subtitle='第二部分：微信生态全域运营新洞察与实战框架',
        logo_text=LOGO, page_num=11)

    pres.save(output_path)
    return output_path


if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else 'tenchage_v32_demo.pptx'
    brand = sys.argv[2] if len(sys.argv) > 2 else '伊利'
    p = build_demo(out, brand=brand)
    print(f'✅ {p}')
