# -*- coding: utf-8 -*-
"""Reusable line-icon library for Tenchage-ppt (C-path SVG).

Each icon is drawn with basic SVG shapes (circle/rect/line/polyline/polygon)
using stroke only, centered at (cx, cy) and scaled by k. The svg_to_pptx
converter turns these into native editable DrawingML shapes.

This is an *expanding* library -- add new names to ICON_NAMES and a matching
branch in render_icon whenever a deck needs a fresh glyph. Keep icons to
basic shapes only (no <path> arcs) so the converter stays happy.

Palette note: icons use the caller-supplied color (normally a brand hue from
refined_deck.HUBS). No forbidden colors are introduced here.
"""

import math

ICON_NAMES = [
    # --- original 24 ---
    "task", "check", "search", "doc", "gear", "person", "people", "book",
    "link", "layers", "bolt", "blocks", "disk", "key", "list", "tag",
    "shield", "chart", "folder", "chat", "calendar", "mega", "grid", "target",
    # --- expanded set: business / status / data / tech / ui ---
    "rocket", "star", "heart", "trophy", "flag", "bulb", "gift", "coin",
    "pie", "trend", "globe", "mail", "phone", "bell", "clock", "cloud",
    "lock", "pin", "compass", "eye", "filter", "sync", "pencil", "plus",
    "arrow", "crown", "briefcase", "scale", "database", "server", "code",
    "cpu", "terminal", "sliders", "play", "pause", "stop", "minus", "close",
    "sun", "wifi", "map",
]

_STROKE_W = 3


def _S(c):
    return (f'fill="none" stroke="{c}" stroke-width="{_STROKE_W}" '
            f'stroke-linecap="round" stroke-linejoin="round"')


def _star_points(cx, cy, R, r, n, rot=-90.0):
    pts = []
    for i in range(n * 2):
        ang = math.radians(rot + i * 180.0 / n)
        rad = R if i % 2 == 0 else r
        pts.append(f"{round(cx + rad*math.cos(ang),1)},{round(cy + rad*math.sin(ang),1)}")
    return " ".join(pts)


def _ellipse_points(cx, cy, rx, ry, n=18):
    pts = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        pts.append(f"{round(cx + rx*math.cos(ang),1)},{round(cy + ry*math.sin(ang),1)}")
    return " ".join(pts)


def render_icon(name, cx, cy, color, k=1.0):
    """Return an SVG fragment string for the named icon centered at (cx, cy)."""
    g = []
    A = lambda x, y: (round(cx + x * k, 1), round(cy + y * k, 1))
    st = _S(color)

    if name in ("task", "check"):
        x1, y1 = A(-8, 0); x2, y2 = A(-2, 7); x3, y3 = A(9, -8)
        g.append(f'<polyline points="{x1},{y1} {x2},{y2} {x3},{y3}" {st}/>')
    elif name == "search":
        hx, hy = A(-3, -3); ex, ey = A(5, 5)
        g.append(f'<circle cx="{hx}" cy="{hy}" r="{round(9*k,1)}" {st}/>')
        g.append(f'<line x1="{hx+6*k}" y1="{hy+6*k}" x2="{ex}" y2="{ey}" {st}/>')
    elif name == "doc":
        x, y = A(-11, -13)
        g.append(f'<rect x="{x}" y="{y}" width="{round(22*k,1)}" height="{round(26*k,1)}" rx="3" {st}/>')
        a, b = A(-5, -4); c, d = A(5, -4); e, f = A(-5, 3); h, i = A(5, 3)
        g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
        g.append(f'<line x1="{e}" y1="{f}" x2="{h}" y2="{i}" {st}/>')
    elif name == "gear":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(10*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(3.5*k,1)}" fill="{color}"/>')
        for ang in (0, 90, 180, 270):
            rad = math.radians(ang)
            x1, y1 = A(round(11*math.cos(rad),1), round(11*math.sin(rad),1))
            x2, y2 = A(round(15*math.cos(rad),1), round(15*math.sin(rad),1))
            g.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {st}/>')
    elif name == "person":
        hx, hy = A(0, -7)
        g.append(f'<circle cx="{hx}" cy="{hy}" r="{round(6*k,1)}" {st}/>')
        g.append(f'<polyline points="{A(-10,12)[0]},{A(-10,12)[1]} {A(-10,2)[0]},{A(-10,2)[1]} '
                 f'{A(10,2)[0]},{A(10,2)[1]} {A(10,12)[0]},{A(10,12)[1]}" {st}/>')
    elif name == "people":
        g.append(f'<circle cx="{cx-7*k}" cy="{cy-6*k}" r="{round(5*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx+7*k}" cy="{cy-6*k}" r="{round(5*k,1)}" {st}/>')
        g.append(f'<polyline points="{A(-15,12)[0]},{A(-15,12)[1]} {A(-13,0)[0]},{A(-13,0)[1]} '
                 f'{A(0,4)[0]},{A(0,4)[1]} {A(13,0)[0]},{A(13,0)[1]} {A(15,12)[0]},{A(15,12)[1]}" {st}/>')
    elif name == "book":
        x, y = A(-12, -13)
        g.append(f'<rect x="{x}" y="{y}" width="{round(24*k,1)}" height="{round(26*k,1)}" rx="3" {st}/>')
        a, b = A(-4, -13); c, d = A(-4, 13)
        g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
    elif name == "link":
        g.append(f'<circle cx="{cx-8*k}" cy="{cy}" r="{round(6*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx+8*k}" cy="{cy}" r="{round(6*k,1)}" {st}/>')
        g.append(f'<line x1="{cx-2*k}" y1="{cy}" x2="{cx+2*k}" y2="{cy}" {st}/>')
    elif name == "layers":
        for yy in (-10, 0, 10):
            a, b = A(-12, yy-4); c, d = A(12, yy-4); e, f = A(0, yy+4)
            g.append(f'<polygon points="{a},{b} {c},{d} {e},{f}" {st}/>')
    elif name == "bolt":
        g.append(f'<polygon points="{A(-3,-13)[0]},{A(-3,-13)[1]} {A(8,-13)[0]},{A(8,-13)[1]} '
                 f'{A(1,-1)[0]},{A(1,-1)[1]} {A(9,-1)[0]},{A(9,-1)[1]} {A(-6,13)[0]},{A(-6,13)[1]} '
                 f'{A(-1,-1)[0]},{A(-1,-1)[1]} {A(-9,-1)[0]},{A(-9,-1)[1]}" fill="{color}"/>')
    elif name == "blocks":
        for r in (-1, 1):
            for col in (-1, 1):
                x, y = A(col*7-5, r*7-5)
                g.append(f'<rect x="{x}" y="{y}" width="{round(10*k,1)}" height="{round(10*k,1)}" rx="2" {st}/>')
    elif name == "disk":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(12*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(3.5*k,1)}" fill="{color}"/>')
    elif name == "key":
        g.append(f'<circle cx="{cx-4*k}" cy="{cy-4*k}" r="{round(7*k,1)}" {st}/>')
        g.append(f'<line x1="{cx+1*k}" y1="{cy+1*k}" x2="{cx+10*k}" y2="{cy+10*k}" {st}/>')
        g.append(f'<line x1="{cx+5*k}" y1="{cy+5*k}" x2="{cx+10*k}" y2="{cy}" {st}/>')
    elif name == "list":
        for yy in (-7, 0, 7):
            a, b = A(-10, yy); c, d = A(10, yy)
            g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
            g.append(f'<circle cx="{cx-13*k}" cy="{cy+yy*k}" r="{round(2*k,1)}" fill="{color}"/>')
    elif name == "tag":
        a, b = A(-11, -7); c, d = A(6, -11); e, f = A(11, -4); h, i = A(11, 9); j, l = A(-11, 9)
        g.append(f'<polygon points="{a},{b} {c},{d} {e},{f} {h},{i} {j},{l}" {st}/>')
        g.append(f'<circle cx="{cx+4*k}" cy="{cy-2*k}" r="{round(3*k,1)}" fill="{color}"/>')
    elif name == "shield":
        g.append(f'<polygon points="{A(0,-13)[0]},{A(0,-13)[1]} {A(11,-7)[0]},{A(11,-7)[1]} '
                 f'{A(11,4)[0]},{A(11,4)[1]} {A(0,13)[0]},{A(0,13)[1]} {A(-11,4)[0]},{A(-11,4)[1]} '
                 f'{A(-11,-7)[0]},{A(-11,-7)[1]}" {st}/>')
        g.append(f'<polyline points="{A(-4,0)[0]},{A(-4,0)[1]} {A(0,5)[0]},{A(0,5)[1]} {A(5,-5)[0]},{A(5,-5)[1]}" {st}/>')
    elif name == "chart":
        g.append(f'<rect x="{A(-10,-2)[0]}" y="{A(-10,-2)[1]}" width="{round(6*k,1)}" height="{round(10*k,1)}" rx="1" fill="{color}"/>')
        g.append(f'<rect x="{A(-1,-9)[0]}" y="{A(-1,-9)[1]}" width="{round(6*k,1)}" height="{round(17*k,1)}" rx="1" fill="{color}"/>')
        g.append(f'<rect x="{A(8,1)[0]}" y="{A(8,1)[1]}" width="{round(6*k,1)}" height="{round(7*k,1)}" rx="1" fill="{color}"/>')
    elif name == "folder":
        a, b = A(-12, -7)
        g.append(f'<rect x="{a}" y="{b}" width="{round(24*k,1)}" height="{round(17*k,1)}" rx="2" {st}/>')
        g.append(f'<polyline points="{A(-12,-7)[0]},{A(-12,-7)[1]} {A(-7,-12)[0]},{A(-7,-12)[1]} '
                 f'{A(2,-12)[0]},{A(2,-12)[1]} {A(2,-7)[0]},{A(2,-7)[1]}" {st}/>')
    elif name == "chat":
        x, y = A(-11, -11)
        g.append(f'<rect x="{x}" y="{y}" width="{round(22*k,1)}" height="{round(19*k,1)}" rx="4" {st}/>')
        g.append(f'<polyline points="{A(-4,8)[0]},{A(-4,8)[1]} {A(-4,14)[0]},{A(-4,14)[1]} {A(3,8)[0]},{A(3,8)[1]}" {st}/>')
    elif name == "calendar":
        x, y = A(-11, -9)
        g.append(f'<rect x="{x}" y="{y}" width="{round(22*k,1)}" height="{round(20*k,1)}" rx="3" {st}/>')
        a, b = A(-11, -3); c, d = A(11, -3)
        g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
        g.append(f'<line x1="{A(-7,-13)[0]}" y1="{A(-7,-13)[1]}" x2="{A(-7,-9)[0]}" y2="{A(-7,-9)[1]}" {st}/>')
        g.append(f'<line x1="{A(7,-13)[0]}" y1="{A(7,-13)[1]}" x2="{A(7,-9)[0]}" y2="{A(7,-9)[1]}" {st}/>')
    elif name == "mega":
        g.append(f'<polygon points="{A(-11,-5)[0]},{A(-11,-5)[1]} {A(2,-10)[0]},{A(2,-10)[1]} '
                 f'{A(2,10)[0]},{A(2,10)[1]} {A(-11,5)[0]},{A(-11,5)[1]}" fill="{color}"/>')
        g.append(f'<line x1="{A(2,0)[0]}" y1="{A(2,0)[1]}" x2="{A(12,0)[0]}" y2="{A(12,0)[1]}" {st}/>')
        g.append(f'<line x1="{A(6,-6)[0]}" y1="{A(6,-6)[1]}" x2="{A(11,-9)[0]}" y2="{A(11,-9)[1]}" {st}/>')
        g.append(f'<line x1="{A(6,6)[0]}" y1="{A(6,6)[1]}" x2="{A(11,9)[0]}" y2="{A(11,9)[1]}" {st}/>')
    elif name == "grid":
        for r in (-1, 1):
            for col in (-1, 1):
                x, y = A(col*7-5, r*7-5)
                g.append(f'<rect x="{x}" y="{y}" width="{round(10*k,1)}" height="{round(10*k,1)}" rx="2" {st}/>')
    elif name == "target":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(12*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(3.5*k,1)}" fill="{color}"/>')
        g.append(f'<line x1="{cx}" y1="{cy-12*k}" x2="{cx}" y2="{cy-16*k}" {st}/>')
        g.append(f'<line x1="{cx}" y1="{cy+12*k}" x2="{cx}" y2="{cy+16*k}" {st}/>')
        g.append(f'<line x1="{cx-12*k}" y1="{cy}" x2="{cx-16*k}" y2="{cy}" {st}/>')
        g.append(f'<line x1="{cx+12*k}" y1="{cy}" x2="{cx+16*k}" y2="{cy}" {st}/>')
    # ---------------- expanded set ----------------
    elif name == "rocket":
        g.append(f'<polygon points="{A(0,-16)[0]},{A(0,-16)[1]} {A(-6,-6)[0]},{A(-6,-6)[1]} {A(6,-6)[0]},{A(6,-6)[1]}" {st}/>')
        g.append(f'<rect x="{A(-6,-6)[0]}" y="{A(-6,-6)[1]}" width="{round(12*k,1)}" height="{round(18*k,1)}" rx="6" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy-2*k}" r="{round(3*k,1)}" {st}/>')
        g.append(f'<polygon points="{A(-6,2)[0]},{A(-6,2)[1]} {A(-12,11)[0]},{A(-12,11)[1]} {A(-6,9)[0]},{A(-6,9)[1]}" {st}/>')
        g.append(f'<polygon points="{A(6,2)[0]},{A(6,2)[1]} {A(12,11)[0]},{A(12,11)[1]} {A(6,9)[0]},{A(6,9)[1]}" {st}/>')
        g.append(f'<polygon points="{A(0,14)[0]},{A(0,14)[1]} {A(-4,12)[0]},{A(-4,12)[1]} {A(4,12)[0]},{A(4,12)[1]}" fill="{color}"/>')
    elif name == "star":
        g.append(f'<polygon points="{_star_points(cx, cy, 13*k, 5.5*k, 5, -90)}" {st}/>')
    elif name == "heart":
        g.append(f'<circle cx="{cx-5*k}" cy="{cy-3*k}" r="{round(5*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx+5*k}" cy="{cy-3*k}" r="{round(5*k,1)}" {st}/>')
        g.append(f'<polygon points="{A(-10,1)[0]},{A(-10,1)[1]} {A(10,1)[0]},{A(10,1)[1]} {A(0,12)[0]},{A(0,12)[1]}" {st}/>')
    elif name == "trophy":
        g.append(f'<polygon points="{A(-7,-12)[0]},{A(-7,-12)[1]} {A(7,-12)[0]},{A(7,-12)[1]} {A(5,2)[0]},{A(5,2)[1]} {A(-5,2)[0]},{A(-5,2)[1]}" {st}/>')
        g.append(f'<circle cx="{cx-9*k}" cy="{cy-6*k}" r="{round(4*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx+9*k}" cy="{cy-6*k}" r="{round(4*k,1)}" {st}/>')
        g.append(f'<rect x="{A(-2,2)[0]}" y="{A(-2,2)[1]}" width="{round(4*k,1)}" height="{round(5*k,1)}" {st}/>')
        g.append(f'<rect x="{A(-8,7)[0]}" y="{A(-8,7)[1]}" width="{round(16*k,1)}" height="{round(3*k,1)}" rx="1" {st}/>')
    elif name == "flag":
        g.append(f'<line x1="{A(0,-14)[0]}" y1="{A(0,-14)[1]}" x2="{A(0,14)[0]}" y2="{A(0,14)[1]}" {st}/>')
        g.append(f'<polygon points="{A(0,-14)[0]},{A(0,-14)[1]} {A(12,-9)[0]},{A(12,-9)[1]} {A(0,-4)[0]},{A(0,-4)[1]}" {st}/>')
    elif name == "bulb":
        g.append(f'<circle cx="{cx}" cy="{cy-4*k}" r="{round(8*k,1)}" {st}/>')
        g.append(f'<line x1="{A(-4,4)[0]}" y1="{A(-4,4)[1]}" x2="{A(4,4)[0]}" y2="{A(4,4)[1]}" {st}/>')
        g.append(f'<line x1="{A(-3,8)[0]}" y1="{A(-3,8)[1]}" x2="{A(3,8)[0]}" y2="{A(3,8)[1]}" {st}/>')
        g.append(f'<line x1="{A(0,-15)[0]}" y1="{A(0,-15)[1]}" x2="{A(0,-13)[0]}" y2="{A(0,-13)[1]}" {st}/>')
        g.append(f'<line x1="{A(-12,-10)[0]}" y1="{A(-12,-10)[1]}" x2="{A(-10,-8)[0]}" y2="{A(-10,-8)[1]}" {st}/>')
        g.append(f'<line x1="{A(12,-10)[0]}" y1="{A(12,-10)[1]}" x2="{A(10,-8)[0]}" y2="{A(10,-8)[1]}" {st}/>')
    elif name == "gift":
        g.append(f'<rect x="{A(-10,-2)[0]}" y="{A(-10,-2)[1]}" width="{round(20*k,1)}" height="{round(14*k,1)}" rx="2" {st}/>')
        g.append(f'<rect x="{A(-12,-6)[0]}" y="{A(-12,-6)[1]}" width="{round(24*k,1)}" height="{round(5*k,1)}" rx="1" {st}/>')
        g.append(f'<line x1="{A(0,-6)[0]}" y1="{A(0,-6)[1]}" x2="{A(0,8)[0]}" y2="{A(0,8)[1]}" {st}/>')
        g.append(f'<polyline points="{A(0,-6)[0]},{A(0,-6)[1]} {A(-6,-11)[0]},{A(-6,-11)[1]} {A(-2,-6)[0]},{A(-2,-6)[1]}" {st}/>')
        g.append(f'<polyline points="{A(0,-6)[0]},{A(0,-6)[1]} {A(6,-11)[0]},{A(6,-11)[1]} {A(2,-6)[0]},{A(2,-6)[1]}" {st}/>')
    elif name == "coin":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(12*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(8*k,1)}" {st}/>')
        g.append(f'<line x1="{A(0,-6)[0]}" y1="{A(0,-6)[1]}" x2="{A(0,6)[0]}" y2="{A(0,6)[1]}" {st}/>')
        g.append(f'<line x1="{A(-4,-2)[0]}" y1="{A(-4,-2)[1]}" x2="{A(4,-2)[0]}" y2="{A(4,-2)[1]}" {st}/>')
        g.append(f'<line x1="{A(-4,2)[0]}" y1="{A(4,2)[1]}" x2="{A(4,2)[0]}" y2="{A(4,2)[1]}" {st}/>')
    elif name == "pie":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(12*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(6*k,1)}" {st}/>')
    elif name == "trend":
        g.append(f'<polyline points="{A(-11,8)[0]},{A(-11,8)[1]} {A(-3,2)[0]},{A(-3,2)[1]} {A(3,-3)[0]},{A(3,-3)[1]} {A(11,-10)[0]},{A(11,-10)[1]}" {st}/>')
        g.append(f'<polygon points="{A(11,-10)[0]},{A(11,-10)[1]} {A(3,-10)[0]},{A(3,-10)[1]} {A(11,-3)[0]},{A(11,-3)[1]}" fill="{color}"/>')
    elif name == "globe":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(12*k,1)}" {st}/>')
        g.append(f'<line x1="{A(-12,0)[0]}" y1="{A(-12,0)[1]}" x2="{A(12,0)[0]}" y2="{A(12,0)[1]}" {st}/>')
        g.append(f'<line x1="{A(0,-12)[0]}" y1="{A(0,-12)[1]}" x2="{A(0,12)[0]}" y2="{A(0,12)[1]}" {st}/>')
        g.append(f'<line x1="{A(-8,-9)[0]}" y1="{A(-8,-9)[1]}" x2="{A(8,9)[0]}" y2="{A(8,9)[1]}" {st}/>')
        g.append(f'<line x1="{A(8,-9)[0]}" y1="{A(8,-9)[1]}" x2="{A(-8,9)[0]}" y2="{A(-8,9)[1]}" {st}/>')
    elif name == "mail":
        g.append(f'<rect x="{A(-12,-8)[0]}" y="{A(-12,-8)[1]}" width="{round(24*k,1)}" height="{round(16*k,1)}" rx="2" {st}/>')
        g.append(f'<polyline points="{A(-12,-8)[0]},{A(-12,-8)[1]} {A(0,0)[0]},{A(0,0)[1]} {A(12,-8)[0]},{A(12,-8)[1]}" {st}/>')
    elif name == "phone":
        g.append(f'<rect x="{A(-6,-12)[0]}" y="{A(-6,-12)[1]}" width="{round(12*k,1)}" height="{round(24*k,1)}" rx="3" {st}/>')
        g.append(f'<line x1="{A(-2,-9)[0]}" y1="{A(-2,-9)[1]}" x2="{A(2,-9)[0]}" y2="{A(2,-9)[1]}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy+8*k}" r="{round(1.6*k,1)}" fill="{color}"/>')
    elif name == "bell":
        g.append(f'<polygon points="{A(0,-12)[0]},{A(0,-12)[1]} {A(-9,-2)[0]},{A(-9,-2)[1]} {A(-6,6)[0]},{A(-6,6)[1]} {A(6,6)[0]},{A(6,6)[1]} {A(9,-2)[0]},{A(9,-2)[1]}" {st}/>')
        g.append(f'<rect x="{A(-4,6)[0]}" y="{A(-4,6)[1]}" width="{round(8*k,1)}" height="{round(3*k,1)}" rx="1" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy+10*k}" r="{round(2.5*k,1)}" fill="{color}"/>')
    elif name == "clock":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(12*k,1)}" {st}/>')
        g.append(f'<line x1="{A(0,0)[0]}" y1="{A(0,0)[1]}" x2="{A(0,-7)[0]}" y2="{A(0,-7)[1]}" {st}/>')
        g.append(f'<line x1="{A(0,0)[0]}" y1="{A(0,0)[1]}" x2="{A(5,3)[0]}" y2="{A(5,3)[1]}" {st}/>')
    elif name == "cloud":
        g.append(f'<circle cx="{cx-6*k}" cy="{cy-2*k}" r="{round(6*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx+5*k}" cy="{cy-3*k}" r="{round(7*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy+1*k}" r="{round(5*k,1)}" {st}/>')
        g.append(f'<line x1="{A(-11,2)[0]}" y1="{A(-11,2)[1]}" x2="{A(11,2)[0]}" y2="{A(11,2)[1]}" {st}/>')
    elif name == "lock":
        g.append(f'<circle cx="{cx}" cy="{cy-3*k}" r="{round(7*k,1)}" {st}/>')
        g.append(f'<rect x="{A(-8,-1)[0]}" y="{A(-8,-1)[1]}" width="{round(16*k,1)}" height="{round(14*k,1)}" rx="2" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy+5*k}" r="{round(2.5*k,1)}" fill="{color}"/>')
        g.append(f'<line x1="{A(0,4)[0]}" y1="{A(0,4)[1]}" x2="{A(0,8)[0]}" y2="{A(0,8)[1]}" {st}/>')
    elif name == "pin":
        g.append(f'<polygon points="{A(0,12)[0]},{A(0,12)[1]} {A(-7,0)[0]},{A(-7,0)[1]} {A(7,0)[0]},{A(7,0)[1]}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy-3*k}" r="{round(6*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy-3*k}" r="{round(2.5*k,1)}" fill="{color}"/>')
    elif name == "compass":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(12*k,1)}" {st}/>')
        g.append(f'<polygon points="{A(0,-9)[0]},{A(0,-9)[1]} {A(3,0)[0]},{A(3,0)[1]} {A(0,9)[0]},{A(0,9)[1]} {A(-3,0)[0]},{A(-3,0)[1]}" fill="{color}"/>')
    elif name == "eye":
        g.append(f'<polygon points="{A(-12,-2)[0]},{A(-12,-2)[1]} {A(0,-9)[0]},{A(0,-9)[1]} {A(12,-2)[0]},{A(12,-2)[1]} {A(0,5)[0]},{A(0,5)[1]}" {st}/>')
        g.append(f'<circle cx="{cx}" cy="{cy-2*k}" r="{round(4*k,1)}" {st}/>')
    elif name == "filter":
        g.append(f'<polygon points="{A(-10,-10)[0]},{A(-10,-10)[1]} {A(10,-10)[0]},{A(10,-10)[1]} {A(3,2)[0]},{A(3,2)[1]} {A(3,10)[0]},{A(3,10)[1]} {A(-3,10)[0]},{A(-3,10)[1]} {A(-3,2)[0]},{A(-3,2)[1]}" {st}/>')
    elif name == "sync":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(9*k,1)}" {st}/>')
        g.append(f'<polygon points="{A(9,-3)[0]},{A(9,-3)[1]} {A(9,-9)[0]},{A(9,-9)[1]} {A(3,-9)[0]},{A(3,-9)[1]}" fill="{color}"/>')
        g.append(f'<polygon points="{A(-9,3)[0]},{A(-9,3)[1]} {A(-9,9)[0]},{A(-9,9)[1]} {A(-3,9)[0]},{A(-3,9)[1]}" fill="{color}"/>')
    elif name == "pencil":
        g.append(f'<polygon points="{A(-9,5)[0]},{A(-9,5)[1]} {A(-5,9)[0]},{A(-5,9)[1]} {A(9,-5)[0]},{A(9,-5)[1]} {A(5,-9)[0]},{A(5,-9)[1]}" {st}/>')
        g.append(f'<polygon points="{A(-9,5)[0]},{A(-9,5)[1]} {A(-5,9)[0]},{A(-5,9)[1]} {A(-12,12)[0]},{A(-12,12)[1]}" fill="{color}"/>')
        g.append(f'<polygon points="{A(5,-9)[0]},{A(5,-9)[1]} {A(9,-5)[0]},{A(9,-5)[1]} {A(7,-12)[0]},{A(7,-12)[1]} {A(3,-8)[0]},{A(3,-8)[1]}" {st}/>')
    elif name == "plus":
        g.append(f'<line x1="{A(0,-11)[0]}" y1="{A(0,-11)[1]}" x2="{A(0,11)[0]}" y2="{A(0,11)[1]}" {st}/>')
        g.append(f'<line x1="{A(-11,0)[0]}" y1="{A(-11,0)[1]}" x2="{A(11,0)[0]}" y2="{A(11,0)[1]}" {st}/>')
    elif name == "arrow":
        g.append(f'<line x1="{A(-9,0)[0]}" y1="{A(-9,0)[1]}" x2="{A(7,0)[0]}" y2="{A(7,0)[1]}" {st}/>')
        g.append(f'<polygon points="{A(7,0)[0]},{A(7,0)[1]} {A(0,-7)[0]},{A(0,-7)[1]} {A(0,7)[0]},{A(0,7)[1]}" fill="{color}"/>')
    elif name == "crown":
        g.append(f'<polygon points="{A(-11,-4)[0]},{A(-11,-4)[1]} {A(-5,-9)[0]},{A(-5,-9)[1]} {A(0,-3)[0]},{A(0,-3)[1]} {A(5,-9)[0]},{A(5,-9)[1]} {A(11,-4)[0]},{A(11,-4)[1]} {A(11,8)[0]},{A(11,8)[1]} {A(-11,8)[0]},{A(-11,8)[1]}" {st}/>')
        g.append(f'<circle cx="{cx-6*k}" cy="{cy+4*k}" r="{round(2*k,1)}" fill="{color}"/>')
        g.append(f'<circle cx="{cx}" cy="{cy+4*k}" r="{round(2*k,1)}" fill="{color}"/>')
        g.append(f'<circle cx="{cx+6*k}" cy="{cy+4*k}" r="{round(2*k,1)}" fill="{color}"/>')
    elif name == "briefcase":
        g.append(f'<rect x="{A(-11,-4)[0]}" y="{A(-11,-4)[1]}" width="{round(22*k,1)}" height="{round(14*k,1)}" rx="2" {st}/>')
        g.append(f'<rect x="{A(-7,-8)[0]}" y="{A(-7,-8)[1]}" width="{round(14*k,1)}" height="{round(5*k,1)}" rx="1" {st}/>')
        g.append(f'<line x1="{A(-3,-8)[0]}" y1="{A(-3,-8)[1]}" x2="{A(-3,-11)[0]}" y2="{A(-3,-11)[1]}" {st}/>')
        g.append(f'<line x1="{A(3,-8)[0]}" y1="{A(3,-8)[1]}" x2="{A(3,-11)[0]}" y2="{A(3,-11)[1]}" {st}/>')
        g.append(f'<line x1="{A(-3,-11)[0]}" y1="{A(-3,-11)[1]}" x2="{A(3,-11)[0]}" y2="{A(3,-11)[1]}" {st}/>')
    elif name == "scale":
        g.append(f'<line x1="{A(-11,-4)[0]}" y1="{A(-11,-4)[1]}" x2="{A(11,-4)[0]}" y2="{A(11,-4)[1]}" {st}/>')
        g.append(f'<line x1="{A(0,-4)[0]}" y1="{A(0,-4)[1]}" x2="{A(0,10)[0]}" y2="{A(0,10)[1]}" {st}/>')
        g.append(f'<line x1="{A(-7,10)[0]}" y1="{A(-7,10)[1]}" x2="{A(7,10)[0]}" y2="{A(7,10)[1]}" {st}/>')
        g.append(f'<circle cx="{cx-11*k}" cy="{cy-4*k}" r="{round(4*k,1)}" {st}/>')
        g.append(f'<circle cx="{cx+11*k}" cy="{cy-4*k}" r="{round(4*k,1)}" {st}/>')
    elif name == "database":
        top = _ellipse_points(cx, cy-9*k, 9*k, 3.5*k, 16)
        bot = _ellipse_points(cx, cy+9*k, 9*k, 3.5*k, 16)
        mid = _ellipse_points(cx, cy, 9*k, 3.5*k, 16)
        g.append(f'<polygon points="{top}" {st}/>')
        g.append(f'<polygon points="{bot}" {st}/>')
        g.append(f'<line x1="{A(-9,-9)[0]}" y1="{A(-9,-9)[1]}" x2="{A(-9,9)[0]}" y2="{A(-9,9)[1]}" {st}/>')
        g.append(f'<line x1="{A(9,-9)[0]}" y1="{A(9,-9)[1]}" x2="{A(9,9)[0]}" y2="{A(9,9)[1]}" {st}/>')
        g.append(f'<polyline points="{mid}" {st}/>')
    elif name == "server":
        g.append(f'<rect x="{A(-10,-11)[0]}" y="{A(-10,-11)[1]}" width="{round(20*k,1)}" height="{round(9*k,1)}" rx="2" {st}/>')
        g.append(f'<rect x="{A(-10,0)[0]}" y="{A(-10,0)[1]}" width="{round(20*k,1)}" height="{round(9*k,1)}" rx="2" {st}/>')
        g.append(f'<circle cx="{cx-6*k}" cy="{cy-6.5*k}" r="{round(2*k,1)}" fill="{color}"/>')
        g.append(f'<circle cx="{cx-6*k}" cy="{cy+4.5*k}" r="{round(2*k,1)}" fill="{color}"/>')
    elif name == "code":
        g.append(f'<polyline points="{A(3,-9)[0]},{A(3,-9)[1]} {A(-5,0)[0]},{A(-5,0)[1]} {A(3,9)[0]},{A(3,9)[1]}" {st}/>')
        g.append(f'<polyline points="{A(-3,-9)[0]},{A(-3,-9)[1]} {A(5,0)[0]},{A(5,0)[1]} {A(-3,9)[0]},{A(-3,9)[1]}" {st}/>')
        g.append(f'<line x1="{A(-1,4)[0]}" y1="{A(-1,4)[1]}" x2="{A(1,-4)[0]}" y2="{A(1,-4)[1]}" {st}/>')
    elif name == "cpu":
        g.append(f'<rect x="{A(-8,-8)[0]}" y="{A(-8,-8)[1]}" width="{round(16*k,1)}" height="{round(16*k,1)}" rx="2" {st}/>')
        g.append(f'<rect x="{A(-4,-4)[0]}" y="{A(-4,-4)[1]}" width="{round(8*k,1)}" height="{round(8*k,1)}" rx="1" {st}/>')
        for px in (-4, 0, 4):
            a, b = A(px, -12); c, d = A(px, -8)
            g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
            a, b = A(px, 8); c, d = A(px, 12)
            g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
        for py in (-4, 0, 4):
            a, b = A(-12, py); c, d = A(-8, py)
            g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
            a, b = A(8, py); c, d = A(12, py)
            g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
    elif name == "terminal":
        g.append(f'<rect x="{A(-11,-9)[0]}" y="{A(-11,-9)[1]}" width="{round(22*k,1)}" height="{round(18*k,1)}" rx="3" {st}/>')
        g.append(f'<polyline points="{A(-7,1)[0]},{A(-7,1)[1]} {A(-3,-3)[0]},{A(-3,-3)[1]} {A(-7,-7)[0]},{A(-7,-7)[1]}" {st}/>')
        g.append(f'<line x1="{A(-1,-3)[0]}" y1="{A(-1,-3)[1]}" x2="{A(3,-3)[0]}" y2="{A(3,-3)[1]}" {st}/>')
    elif name == "sliders":
        g.append(f'<line x1="{A(-9,-6)[0]}" y1="{A(-9,-6)[1]}" x2="{A(9,-6)[0]}" y2="{A(9,-6)[1]}" {st}/>')
        g.append(f'<circle cx="{cx+3*k}" cy="{cy-6*k}" r="{round(3*k,1)}" fill="{color}"/>')
        g.append(f'<line x1="{A(-9,0)[0]}" y1="{A(-9,0)[1]}" x2="{A(9,0)[0]}" y2="{A(9,0)[1]}" {st}/>')
        g.append(f'<circle cx="{cx-3*k}" cy="{cy}" r="{round(3*k,1)}" fill="{color}"/>')
        g.append(f'<line x1="{A(-9,6)[0]}" y1="{A(-9,6)[1]}" x2="{A(9,6)[0]}" y2="{A(9,6)[1]}" {st}/>')
        g.append(f'<circle cx="{cx+4*k}" cy="{cy+6*k}" r="{round(3*k,1)}" fill="{color}"/>')
    elif name == "play":
        g.append(f'<polygon points="{A(-6,-9)[0]},{A(-6,-9)[1]} {A(-6,9)[0]},{A(-6,9)[1]} {A(9,0)[0]},{A(9,0)[1]}" fill="{color}"/>')
    elif name == "pause":
        g.append(f'<rect x="{A(-9,-9)[0]}" y="{A(-9,-9)[1]}" width="{round(6*k,1)}" height="{round(18*k,1)}" rx="1" fill="{color}"/>')
        g.append(f'<rect x="{A(3,-9)[0]}" y="{A(3,-9)[1]}" width="{round(6*k,1)}" height="{round(18*k,1)}" rx="1" fill="{color}"/>')
    elif name == "stop":
        g.append(f'<rect x="{A(-9,-9)[0]}" y="{A(-9,-9)[1]}" width="{round(18*k,1)}" height="{round(18*k,1)}" rx="2" fill="{color}"/>')
    elif name == "minus":
        g.append(f'<line x1="{A(-11,0)[0]}" y1="{A(-11,0)[1]}" x2="{A(11,0)[0]}" y2="{A(11,0)[1]}" {st}/>')
    elif name == "close":
        g.append(f'<line x1="{A(-8,-8)[0]}" y1="{A(-8,-8)[1]}" x2="{A(8,8)[0]}" y2="{A(8,8)[1]}" {st}/>')
        g.append(f'<line x1="{A(-8,8)[0]}" y1="{A(-8,8)[1]}" x2="{A(8,-8)[0]}" y2="{A(8,-8)[1]}" {st}/>')
    elif name == "sun":
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(6*k,1)}" {st}/>')
        for ang in (0, 45, 90, 135, 180, 225, 270, 315):
            rad = math.radians(ang)
            a, b = A(round(9*math.cos(rad),1), round(9*math.sin(rad),1))
            c, d = A(round(13*math.cos(rad),1), round(13*math.sin(rad),1))
            g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {st}/>')
    elif name == "wifi":
        g.append(f'<circle cx="{cx}" cy="{cy+8*k}" r="{round(2*k,1)}" fill="{color}"/>')
        g.append(f'<polyline points="{A(-4,4)[0]},{A(-4,4)[1]} {A(0,0)[0]},{A(0,0)[1]} {A(4,4)[0]},{A(4,4)[1]}" {st}/>')
        g.append(f'<polyline points="{A(-8,0)[0]},{A(-8,0)[1]} {A(0,-6)[0]},{A(0,-6)[1]} {A(8,0)[0]},{A(8,0)[1]}" {st}/>')
        g.append(f'<polyline points="{A(-12,-4)[0]},{A(-12,-4)[1]} {A(0,-12)[0]},{A(0,-12)[1]} {A(12,-4)[0]},{A(12,-4)[1]}" {st}/>')
    elif name == "map":
        g.append(f'<polygon points="{A(-12,-8)[0]},{A(-12,-8)[1]} {A(-4,-11)[0]},{A(-4,-11)[1]} {A(4,-7)[0]},{A(4,-7)[1]} {A(12,-10)[0]},{A(12,-10)[1]} {A(12,8)[0]},{A(12,8)[1]} {A(4,5)[0]},{A(4,5)[1]} {A(-4,9)[0]},{A(-4,9)[1]} {A(-12,6)[0]},{A(-12,6)[1]}" {st}/>')
    else:
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{round(10*k,1)}" {st}/>')
    return "".join(g)
