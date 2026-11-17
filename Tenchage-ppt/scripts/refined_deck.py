# -*- coding: utf-8 -*-
"""Refined C-path layout helpers for Tenchage-ppt.

Imported by deck generator scripts to produce the v2-style refined visual:
icon-chip cards, brand-hue color rotation, designed cover/closing shells,
background decoration, and page-number chip. All output is native-editable
SVG for the svg_to_pptx converter.

Visual standard (default for C path since 2026-07-15):
  - every content card carries an icon chip + a brand-hue accent
  - card accents rotate through HUBS (blue family + green) for variety
  - cover & closing use layered gradient + decorative circles
  - pages feel full: background deco + header hairline + page chip
Respects skill 铁律: only brand palette, no English decorative words.
"""

import html
from svg_icons import render_icon

# ---- brand palette (Tencent visual genes) ----
WHITE = "#FFFFFF"
DEEP = "#0E2F7E"; BRIGHT = "#2E6CFF"; MAIN = "#1A50D6"; MID = "#4E82C5"; LIGHT = "#7CB3E0"
TXT = "#1D2129"; GRAY = "#4E5969"; LGRAY = "#86909C"
SHADOW = "#E0E6F1"; GREEN = "#00A45D"; BORDER = "#EAEDF5"; CHIP = "#EAF0FF"
FT = "腾讯体 W7"; FB = "腾讯体 W3"

# brand-hue rotation for cards (no forbidden colors)
HUBS = [MAIN, BRIGHT, GREEN, DEEP, MID, LIGHT]

# minimum SVG font size -> 16pt floor (user rule). 22px * 0.75 = 16.5pt
MIN_SVG = 22


def esc(s):
    return html.escape(str(s), quote=True)


def T(x, y, s, size, font=FB, fill=GRAY, anchor="start", weight=None):
    w = f' font-weight="{weight}"' if weight else ''
    return f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}"{w} fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>'


def bg_white():
    return f'<rect x="0" y="0" width="1280" height="720" fill="{WHITE}"/>'


def bg_grad():
    return ('<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0%" stop-color="{DEEP}"/><stop offset="55%" stop-color="{MAIN}"/><stop offset="100%" stop-color="{BRIGHT}"/></linearGradient>'
            f'<radialGradient id="glow" cx="80%" cy="20%" r="60%">'
            f'<stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.18"/><stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient></defs>'
            f'<rect x="0" y="0" width="1280" height="720" fill="url(#bg)"/>'
            f'<rect x="0" y="0" width="1280" height="720" fill="url(#glow)"/>')


def spine_def():
    return ('<defs><linearGradient id="spine" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="{DEEP}"/><stop offset="100%" stop-color="{BRIGHT}"/></linearGradient></defs>')


def deco():
    return (f'<circle cx="1200" cy="70" r="180" fill="{MAIN}" opacity="0.05"/>'
            f'<circle cx="1200" cy="70" r="120" fill="{MAIN}" opacity="0.04"/>')


def page_chip(n):
    return (f'<rect x="1158" y="670" width="62" height="28" rx="14" fill="#F2F5FC"/>'
            + T(1189, 689, f"{n:02d}/13", MIN_SVG, FT, MAIN, anchor="middle"))


def header(title, n):
    bar = f'<rect x="60" y="44" width="7" height="40" rx="3.5" fill="url(#spine)"/>'
    t = T(84, 76, title, 32, FT, TXT)
    hair = f'<line x1="60" y1="100" x2="1220" y2="100" stroke="{BORDER}" stroke-width="2"/>'
    return spine_def() + bar + t + hair + deco() + page_chip(n)


def wrap(text, width_px, font_px):
    cpl = max(6, int(width_px / (font_px * 0.52)))
    words = text.split(); lines = []; cur = ""
    for wd in words:
        if not cur:
            cur = wd
        elif len(cur) + 1 + len(wd) <= cpl:
            cur += " " + wd
        else:
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines


def icon_chip(x, y, accent, icon_name, chip=48):
    """Rounded tinted chip + centered icon. (x,y) = top-left of chip."""
    s = f'<rect x="{x}" y="{y}" width="{chip}" height="{chip}" rx="12" fill="{CHIP}"/>'
    s += render_icon(icon_name, x + chip/2, y + chip/2, accent, k=1.05)
    return s


def card(x, y, w, h, title, body, accent, icon_name):
    sh = f'<rect x="{x}" y="{y+7}" width="{w}" height="{h}" rx="16" fill="{SHADOW}" opacity="0.85"/>'
    body_r = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{WHITE}" stroke="{BORDER}" stroke-width="1"/>'
    top = f'<rect x="{x}" y="{y}" width="{w}" height="7" rx="3.5" fill="{accent}"/>'
    chip = icon_chip(x+22, y+24, accent, icon_name)
    tt = T(x+82, y+56, title, 24, FT, TXT)
    blines = wrap(body, w-44, 24)
    maxlines = (h - 110) // 32
    ly = y + 96
    ls = ""
    for ln in blines[:maxlines]:
        ls += T(x+24, ly, ln, 24, FB, GRAY); ly += 32
    return sh + body_r + top + chip + tt + ls


def row4(y, h, items):
    x0 = 60; w = 270; gap = 20; s = ""
    for i, it in enumerate(items):
        x = x0 + i * (w + gap)
        s += card(x, y, w, h, it[0], it[1], HUBS[i % len(HUBS)], it[2])
    return s


def row2(y, h, items):
    x0 = 60; w = 560; gap = 40; s = ""
    for i, it in enumerate(items):
        x = x0 + i * (w + gap)
        s += card(x, y, w, h, it[0], it[1], HUBS[i % len(HUBS)], it[2])
    return s


def grid6(y, items):
    x0 = 60; cw = 360; ch = 200; gap = 20; s = ""
    for i, it in enumerate(items):
        r = i // 3; c = i % 3
        x = x0 + c * (cw + gap); yy = y + r * (ch + gap)
        s += card(x, yy, cw, ch, it[0], it[1], HUBS[i % len(HUBS)], it[2])
    return s


def grid22(y, items):
    x0 = 60; w = 560; ch = 200; gap = 40; s = ""
    for i, it in enumerate(items):
        r = i // 2; c = i % 2
        x = x0 + c * (w + gap); yy = y + r * (ch + gap)
        s += card(x, yy, w, ch, it[0], it[1], HUBS[i % len(HUBS)], it[2])
    return s


def note(y, text):
    return T(60, y, text, MIN_SVG, FB, LGRAY)


def cover_bg():
    s = bg_grad()
    s += f'<circle cx="1080" cy="640" r="220" fill="#FFFFFF" opacity="0.06"/>'
    s += f'<circle cx="180" cy="120" r="150" fill="#FFFFFF" opacity="0.05"/>'
    return s


def closing_bg():
    s = bg_grad()
    s += f'<circle cx="200" cy="640" r="200" fill="#FFFFFF" opacity="0.06"/>'
    s += f'<circle cx="1100" cy="120" r="160" fill="#FFFFFF" opacity="0.05"/>'
    return s


def svg_page(inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            f'width="1280" height="720">{inner}</svg>')
