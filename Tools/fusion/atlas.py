"""Draws the panel faces, button caps, lamp legends and gauge dials of cockpit_spec.py into texture pages.

python atlas.py            -> Models/Fusion/fusion-panel-<n>.png (colour) and fusion-panel-<n>-lm.png (lightmap:
                              back-lit markings in white), Tools/fusion/_build/atlas.json (UV rectangles)

UV rectangles: [page, u0, v0, u1, v1], v up (OpenGL / AC3D convention). The top right 16 x 16 px of every page is
white (plain faces of textured objects).
"""

import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cockpit_spec as SPEC                    # noqa: E402
from spec_base import (AMBER, BLACK, CYAN, FONT, FONT_BOLD, GREEN, RED, WHITE, Button, Gauge, Knob,  # noqa: E402
                       Lamp, PushLight, Toggle)

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Models", "Fusion")
BUILD = os.path.join(HERE, "_build")
PAGE = 4096
PAD = 6
FONT_FILE = "C:/Windows/Fonts/bahnschrift.ttf"
CAP_RATIO = 0.70          # cap height / font size (Bahnschrift)

_fonts = {}


def font(px, style=FONT):
    key = (int(round(px)), style)
    if key not in _fonts:
        f = ImageFont.truetype(FONT_FILE, max(4, key[0]))
        f.set_variation_by_name(style)
        _fonts[key] = f
    return _fonts[key]


def rgb255(c, a=255):
    return (int(round(c[0] * 255)), int(round(c[1] * 255)), int(round(c[2] * 255)), a)


class Canvas:
    """Drawing surface in millimetres (origin at the centre, y up) for the colour and lightmap images."""

    def __init__(self, w_mm, h_mm, ppm, bg, lm_bg=(0, 0, 0)):
        self.w, self.h, self.ppm = w_mm, h_mm, ppm
        self.W = max(4, int(round(w_mm * ppm)))
        self.H = max(4, int(round(h_mm * ppm)))
        self.img = Image.new("RGBA", (self.W, self.H), rgb255(bg))
        self.lm = Image.new("RGBA", (self.W, self.H), rgb255(lm_bg))
        self.d = ImageDraw.Draw(self.img)
        self.dl = ImageDraw.Draw(self.lm)

    def P(self, x, y):
        return ((x + self.w / 2) * self.ppm, (self.h / 2 - y) * self.ppm)

    def text(self, s, x, y, size, align="c", style=FONT, color=WHITE, lit=True, lm_color=(1, 1, 1)):
        f = font(size * self.ppm / CAP_RATIO, style)
        anchor = {"c": "ms", "l": "ls", "r": "rs"}[align]
        px, py = self.P(x, y - size / 2)
        self.d.text((px, py), s, font=f, fill=rgb255(color), anchor=anchor)
        if lit:
            self.dl.text((px, py), s, font=f, fill=rgb255(lm_color), anchor=anchor)

    def text_width(self, s, size, style=FONT):
        f = font(size * self.ppm / CAP_RATIO, style)
        return f.getlength(s) / self.ppm

    def line(self, pts, width, color=WHITE, lit=True):
        px = [self.P(*p) for p in pts]
        w = max(1, int(round(width * self.ppm)))
        self.d.line(px, fill=rgb255(color), width=w, joint="curve")
        if lit:
            self.dl.line(px, fill=(255, 255, 255, 255), width=w, joint="curve")

    def rect(self, x0, y0, x1, y1, width, radius=0.0, color=WHITE, lit=True, fill=None):
        a = self.P(x0, y1)
        b = self.P(x1, y0)
        w = max(1, int(round(width * self.ppm)))
        self.d.rounded_rectangle([a, b], radius=radius * self.ppm, outline=rgb255(color), width=w,
                                 fill=rgb255(fill) if fill else None)
        if lit:
            self.dl.rounded_rectangle([a, b], radius=radius * self.ppm, outline=(255, 255, 255, 255), width=w)

    def disc(self, x, y, r, color, lit=False):
        a = self.P(x - r, y + r)
        b = self.P(x + r, y - r)
        self.d.ellipse([a, b], fill=rgb255(color))
        if lit:
            self.dl.ellipse([a, b], fill=(255, 255, 255, 255))

    def arc(self, x, y, r, a0, a1, width, color=WHITE, lit=True):
        """Arc from a0 to a1 (degrees clockwise from 12 o'clock)."""
        a = self.P(x - r, y + r)
        b = self.P(x + r, y - r)
        w = max(1, int(round(width * self.ppm)))
        # PIL angles: degrees clockwise from 3 o'clock
        self.d.arc([a, b], a0 - 90, a1 - 90, fill=rgb255(color), width=w)
        if lit:
            self.dl.arc([a, b], a0 - 90, a1 - 90, fill=(255, 255, 255, 255), width=w)

    def tick(self, x, y, r0, r1, ang, width, color=WHITE, lit=True):
        a = math.radians(ang)
        self.line([(x + r0 * math.sin(a), y + r0 * math.cos(a)), (x + r1 * math.sin(a), y + r1 * math.cos(a))], width,
                  color, lit)

    def polygon(self, pts, color, lit=False):
        px = [self.P(*p) for p in pts]
        self.d.polygon(px, fill=rgb255(color))
        if lit:
            self.dl.polygon(px, fill=(255, 255, 255, 255))


# -----------------------------------------------------------------------------------------------------------------
# panel faces

def draw_panel(p):
    ppm = min(p.ppm, 4000.0 / p.w, 4000.0 / p.h)
    c = Canvas(p.w, p.h, ppm, p.color)
    for m in p.marks:
        if m.kind == "text":
            c.text(m.s, m.x, m.y, m.size, m.align, m.font, m.color, m.lit)
        elif m.kind == "line":
            c.line(m.pts, m.width, m.color, m.lit)
        elif m.kind == "rect":
            c.rect(m.x0, m.y0, m.x1, m.y1, m.width, m.radius, m.color, m.lit, m.fill)
        elif m.kind == "group":
            draw_group(c, m)
        elif m.kind == "bracket":
            draw_bracket(c, m)
    return c


def draw_group(c, m):
    w = 0.35
    x0, y0, x1, y1 = m.x0, m.y0, m.x1, m.y1
    top = [(x0, y1), (x1, y1)]
    if m.title:
        lines = m.title.split("\n")
        tw = max(c.text_width(t, m.size) for t in lines)
        cx = (x0 + x1) / 2
        for k, t in enumerate(lines):
            c.text(t, cx, y1 - (k - (len(lines) - 1)) * m.size * 1.15 - 0.0, m.size)
        c.line([(x0, y1), (cx - tw / 2 - m.gap, y1)], w)
        c.line([(cx + tw / 2 + m.gap, y1), (x1, y1)], w)
    else:
        c.line(top, w)
    c.line([(x0, y1), (x0, y0)], w)
    c.line([(x1, y1), (x1, y0)], w)
    if m.bottom:
        tw = c.text_width(m.bottom, m.size * 0.9)
        cx = (x0 + x1) / 2
        c.text(m.bottom, cx, y0, m.size * 0.9)
        c.line([(x0, y0), (cx - tw / 2 - m.gap, y0)], w)
        c.line([(cx + tw / 2 + m.gap, y0), (x1, y0)], w)
    else:
        c.line([(x0, y0), (x1, y0)], w)


def draw_bracket(c, m):
    w = 0.35
    t = m.tick if m.down else -m.tick
    cx = (m.x0 + m.x1) / 2
    if m.title:
        tw = c.text_width(m.title, m.size)
        c.text(m.title, cx, m.y, m.size)
        c.line([(m.x0, m.y - t), (m.x0, m.y), (cx - tw / 2 - 1.2, m.y)], w)
        c.line([(cx + tw / 2 + 1.2, m.y), (m.x1, m.y), (m.x1, m.y - t)], w)
    else:
        c.line([(m.x0, m.y - t), (m.x0, m.y), (m.x1, m.y), (m.x1, m.y - t)], w)


# -----------------------------------------------------------------------------------------------------------------
# control decals

CAP_COLORS = {
    "cap": (0.63, 0.64, 0.66), "cap_dark": (0.13, 0.13, 0.14), "bezel_key": (0.10, 0.10, 0.11),
    "red_round": (0.70, 0.06, 0.05), "cap_dark_round": (0.14, 0.14, 0.15), "lens": (0.09, 0.09, 0.09),
}


def draw_legend(c, legend, color, size, lit_color=None):
    if not legend:
        return
    if legend in ("<", ">"):
        s = -1 if legend == "<" else 1
        c.polygon([(-s * 1.2, -1.5), (-s * 1.2, 1.5), (s * 1.4, 0.0)], color, lit=True)
        return
    lines = legend.split("\n")
    n = len(lines)
    for k, t in enumerate(lines):
        if not t:
            continue
        y = (n - 1) / 2.0 * size * 1.3 - k * size * 1.3
        c.text(t, 0.0, y, size, "c", FONT_BOLD, color, lit=True, lm_color=lit_color or (1, 1, 1))


def decal_button(b):
    ppm = 10
    if isinstance(b, PushLight):
        c = Canvas(b.w, b.h, ppm, CAP_COLORS["lens"])
        # unlit: legend in a dark tint of its colour; lit via emission
        dim = tuple(0.25 + 0.35 * v for v in b.lamp_color)
        draw_legend(c, b.legend, dim, b.legend_size)
        c.rect(-b.w / 2 + 0.4, -b.h / 2 + 0.4, b.w / 2 - 0.4, b.h / 2 - 0.4, 0.5, 0.8, (0.3, 0.3, 0.3), lit=False)
        return c
    c = Canvas(b.w, b.h, ppm, CAP_COLORS.get(b.cap, CAP_COLORS["cap"]))
    draw_legend(c, b.legend, b.legend_color, b.legend_size)
    return c


def decal_lamp(l):
    ppm = 10
    c = Canvas(l.w, l.h, ppm, (0.08, 0.08, 0.08))
    dim = tuple(0.18 + 0.3 * v for v in l.color)
    if l.legend:
        draw_legend(c, l.legend, dim, l.legend_size)
    else:
        c.disc(0, 0, min(l.w, l.h) / 2 - 0.3, dim)
    return c


def decal_knob(style):
    """Top of a knob, 20 x 20 mm, drawn for the unit circle (the cap is mapped on its diameter)."""
    ppm = 12
    bg = {"fgp": (0.60, 0.61, 0.63), "cb": (0.05, 0.05, 0.05)}.get(style, (0.04, 0.04, 0.042))
    c = Canvas(20, 20, ppm, bg)
    if style in ("rheostat", "receiver", "bar", "selector", "trim"):
        c.line([(0, 3.0), (0, 9.0)], 1.4, WHITE, lit=True)
    elif style == "fgp":
        c.text("PUSH", 0, 1.6, 2.6, color=(0.15, 0.15, 0.15), lit=False)
    elif style == "cb":
        c.text("5", 0, 0, 7.0, color=WHITE, lit=True)
    return c


def gauge_scale(c, cx, cy, r, marks, major_len=3.0, minor_len=1.8, width=0.6, label_r=None, size=3.0):
    for ang, major, label in marks:
        c.tick(cx, cy, r - (major_len if major else minor_len), r, ang, width * (1.3 if major else 1.0))
        if label is not None:
            lr = label_r or (r - major_len - 3.2)
            a = math.radians(ang)
            c.text(label, cx + lr * math.sin(a), cy + lr * math.cos(a), size)


def lin(v0, a0, v1, a1):
    return lambda v: a0 + (a1 - a0) * (v - v0) / (v1 - v0)


def decal_dial(g):
    ppm = 12
    d = g.d
    c = Canvas(d, d, ppm, (0.03, 0.03, 0.03))
    r = d / 2 - 0.8
    kind = g.dial
    if kind == "flap":
        c.text("FLAP", 0, -6.0, 3.4)
        c.arc(0, 0, r - 1.0, -60, 60, 0.6)
        for ang, lab in ((-60, "UP"), (0, "APPR"), (60, "DN")):
            c.tick(0, 0, r - 5.0, r - 0.5, ang, 1.2)
            a = math.radians(ang)
            c.text(lab, (r - 9.5) * math.sin(a), (r - 9.5) * math.cos(a), 2.8)
        for ang in (-30, 30):
            c.tick(0, 0, r - 3.0, r - 0.5, ang, 0.7)
    elif kind == "cabin_climb":
        f = lin(0, 0, 3000, 150)
        marks = []
        for v in range(-3000, 3001, 500):
            major = v % 1000 == 0
            marks.append((f(v), major, str(abs(v) // 1000) if major else None))
        gauge_scale(c, 0, 0, r, marks, size=3.2)
        c.text("CABIN", 0, 6.5, 2.4)
        c.text("CLIMB", 0, 3.5, 2.4)
        c.text("UP", -9.0, 2.0, 2.2)
        c.text("DN", -9.0, -4.0, 2.2)
        c.text("1000 FT", 0, -8.0, 2.0)
        c.text("PER MIN", 0, -10.6, 2.0)
    elif kind == "cabin_alt":
        f = lin(0, -150, 20000, 120)
        marks = [(f(v * 1000), v % 5 == 0, str(v) if v % 5 == 0 else None) for v in range(0, 36) if f(v * 1000) <= 150]
        gauge_scale(c, 0, 0, r, marks, size=2.8)
        fd = lin(0, -160, 7, -20)
        c.arc(0, 0, r - 11.5, -160, -20, 0.5, AMBER)
        for v in range(0, 8):
            c.tick(0, 0, r - 13.5, r - 11.5, fd(v), 0.6, AMBER)
            a = math.radians(fd(v))
            c.text(str(v), (r - 16.0) * math.sin(a), (r - 16.0) * math.cos(a), 2.0, color=AMBER)
        c.text("CABIN ALT", 0, -6.5, 2.2)
        c.text("1000 FT", 0, -9.2, 1.9)
        c.text("DIFF PSI", 0, 7.0, 1.9, color=AMBER)
    elif kind == "cabin_temp":
        f = lin(0, -60, 30, 60)
        marks = [(f(v), v % 10 == 0, str(v) if v % 10 == 0 else None) for v in range(0, 31, 2)]
        c.arc(0, 0, r - 0.5, -60, 60, 0.5)
        gauge_scale(c, 0, 0, r - 0.5, marks, size=3.0)
        c.text("CABIN TEMP", 0, -5.0, 2.6)
        c.text("\u00b0C", 0, -9.0, 2.6)
    elif kind == "oxygen":
        f = lin(0, -135, 2000, 135)
        marks = [(f(v), v % 500 == 0, str(v // 100) if v % 500 == 0 else None) for v in range(0, 2001, 100)]
        gauge_scale(c, 0, 0, r, marks, size=2.8)
        c.arc(0, 0, r - 0.6, f(1550), f(1850), 1.2, GREEN)
        c.text("OXYGEN", 0, -6.0, 2.6)
        c.text("PSI x 100", 0, -9.2, 2.0)
    elif kind in ("dcload_l", "dcload_r"):
        f = lin(0, -135, 100, 135)
        gauge_scale(c, 0, 0, r, [(f(v), v % 20 == 0, str(v) if v % 20 == 0 else None) for v in range(0, 101, 10)],
                    size=2.6)
        c.text("DC", 0, 6.0, 2.4)
        c.text("% LOAD", 0, -5.0, 2.3)
        c.text("LEFT" if kind.endswith("_l") else "RIGHT", 0, -9.5, 2.0)
    elif kind == "battamps":
        f = lin(-100, -120, 100, 120)
        gauge_scale(c, 0, 0, r, [(f(v), v % 50 == 0, str(v) if v % 50 == 0 else None) for v in range(-100, 101, 25)],
                    size=2.4)
        c.text("BATT", 0, 6.0, 2.4)
        c.text("AMPS", 0, -5.0, 2.3)
        c.text("-  DISCH   CHG  +", 0, -9.5, 1.7)
    elif kind == "volts":
        f = lin(0, -135, 30, 135)
        gauge_scale(c, 0, 0, r, [(f(v), v % 10 == 0, str(v) if v % 10 == 0 else None) for v in range(0, 31, 2)],
                    size=2.6)
        c.arc(0, 0, r - 0.8, f(24), f(29), 1.2, GREEN)
        c.text("DC", 0, 6.0, 2.4)
        c.text("VOLTS", 0, -5.0, 2.3)
    elif kind == "propamps":
        f = lin(0, -135, 40, 135)
        gauge_scale(c, 0, 0, r, [(f(v), v % 10 == 0, str(v) if v % 10 == 0 else None) for v in range(0, 41, 5)],
                    size=2.6)
        c.arc(0, 0, r - 0.8, f(26), f(32), 1.2, GREEN)
        c.text("PROP", 0, 6.0, 2.4)
        c.text("AMPS", 0, -5.0, 2.3)
    elif kind == "oat":
        f = lin(-50, -135, 50, 135)
        gauge_scale(c, 0, 0, r, [(f(v), v % 20 == 0 or abs(v) == 50, str(v) if v % 20 == 0 else None)
                                 for v in range(-50, 51, 10)], size=2.4)
        c.text("OAT", 0, 6.0, 2.4)
        c.text("\u00b0C", 0, -5.0, 2.3)
    elif kind == "fuelqty":
        f = lin(0, -120, 2000, 120)
        gauge_scale(c, 0, 0, r, [(f(v), v % 400 == 0, str(v // 100) if v % 400 == 0 else None)
                                 for v in range(0, 2001, 200)], size=3.4)
        c.arc(0, 0, r - 1.0, f(0), f(265), 1.6, AMBER)
        c.text("FUEL", 0, 8.0, 3.0)
        c.text("QTY", 0, -8.0, 2.8)
        c.text("LBS x 100", 0, -12.5, 2.0)
    elif kind == "hobbs":
        c.text("QUARTZ", 0, 8.5, 2.8)
        c.text("FLIGHT HOURS", 0, -9.0, 2.6)
        c.rect(-12.5, -3.2, 12.5, 3.2, 0.5, 0.6, (0.6, 0.6, 0.6), lit=False, fill=(0.0, 0.0, 0.0))
    return c


def decal_emblem():
    """Hub of the control wheels: 'Beechcraft' and 'KING AIR' on the black hub, 128 x 76 mm."""
    ppm = 8
    c = Canvas(128, 76, ppm, (0.03, 0.03, 0.035))
    f = ImageFont.truetype("C:/Windows/Fonts/timesbi.ttf", int(9.0 * ppm / 0.66))
    px, py = c.P(0, 4.5)
    c.d.text((px, py), "Beechcraft", font=f, fill=rgb255((0.80, 0.08, 0.06)), anchor="ms")
    c.text("K I N G   A I R", 0, -8.5, 3.6, style=FONT, color=(0.72, 0.72, 0.74), lit=False)
    return c


def decal_compass():
    """Compass card strip: 0-360 deg over 120 mm (wrapped round the drum), N E S W and every 30 deg."""
    ppm = 12
    c = Canvas(120.0, 12.0, ppm, (0.05, 0.05, 0.05))
    for d in range(0, 360, 5):
        x = -60.0 + d / 360.0 * 120.0
        big = d % 30 == 0
        c.line([(x, 6.0), (x, 6.0 - (2.4 if big else 1.2))], 0.3)
        if big:
            lab = {0: "N", 90: "E", 180: "S", 270: "W"}.get(d, str(d // 10))
            c.text(lab, x, 0.0, 3.2 if d % 90 == 0 else 2.6)
    return c


def decal_digits():
    """Counter drum: digits 0-9 stacked (0 at the top), 6 x 60 mm."""
    ppm = 16
    c = Canvas(6.0, 60.0, ppm, (0.02, 0.02, 0.02))
    for k in range(10):
        c.text(str(k), 0, 30.0 - 3.0 - 6.0 * k, 3.6, color=WHITE)
    return c


# -----------------------------------------------------------------------------------------------------------------
# packing

def collect():
    groups = []            # [(group name, [(key, Canvas)])]
    styles = set()
    for p in SPEC.PANELS:
        items = [("panel:" + p.name, draw_panel(p))]
        for ctl in p.controls:
            if isinstance(ctl, Button):
                items.append(("btn:" + ctl.name, decal_button(ctl)))
            elif isinstance(ctl, Lamp):
                items.append(("lamp:" + ctl.name, decal_lamp(ctl)))
            elif isinstance(ctl, Gauge):
                items.append(("dial:" + ctl.name, decal_dial(ctl)))
            elif isinstance(ctl, Knob):
                styles.add(ctl.style)
        groups.append((p.name, items))
    common = [("knob:" + s, decal_knob(s)) for s in sorted(styles | {"rheostat", "fgp", "selector", "bar", "receiver", "cb",
                                                                     "trim"})]
    common.append(("digits", decal_digits()))
    common.append(("yoke:emblem", decal_emblem()))
    common.append(("compass", decal_compass()))
    return groups, common


def pack(groups, common):
    pages = []            # [{"img", "lm", "shelves": [(y, h, x)]}]

    def new_page():
        pg = {"img": Image.new("RGBA", (PAGE, PAGE), (128, 128, 128, 255)),
              "lm": Image.new("RGBA", (PAGE, PAGE), (0, 0, 0, 255)), "y": 0, "shelves": []}
        # white block (plain faces)
        pg["img"].paste((255, 255, 255, 255), (PAGE - 20, 0, PAGE, 20))
        pg["shelves"].append([0, 24, PAGE - 24])       # the first shelf ends before the white block
        pages.append(pg)
        return pg

    def try_place(pg, W, H, commit):
        for sh in pg["shelves"]:
            y, h, x = sh
            limit = PAGE - 24 if y == 0 else PAGE
            if H <= h and x + W <= (PAGE - 24 if y < 24 else PAGE):
                if commit:
                    sh[2] = x + W + PAD
                return (x, y)
        if pg["y"] + H <= PAGE:
            if commit:
                y = pg["y"]
                pg["shelves"].append([y, H, W + PAD])
                pg["y"] = y + H + PAD
                return (0, y)
            return (0, pg["y"])
        return None

    regions = {}

    def place_group(items):
        items = sorted(items, key=lambda kv: -kv[1].H)
        for pg_index, pg in enumerate(pages + [None]):
            if pg is None:
                pg = new_page()
                pg_index = len(pages) - 1
            # dry run on a copy of the shelves
            saved = ([list(s) for s in pg["shelves"]], pg["y"])
            ok = True
            spots = []
            for key, cv in items:
                spot = try_place(pg, cv.W, cv.H, commit=True)
                if spot is None:
                    ok = False
                    break
                spots.append(spot)
            if not ok:
                pg["shelves"], pg["y"] = saved
                continue
            for (key, cv), (x, y) in zip(items, spots):
                pg["img"].paste(cv.img, (x, y))
                pg["lm"].paste(cv.lm, (x, y))
                regions[key] = [pg_index, x / PAGE, 1.0 - (y + cv.H) / PAGE, (x + cv.W) / PAGE, 1.0 - y / PAGE]
            return

    # large groups first
    order = sorted(groups, key=lambda g: -sum(cv.W * cv.H for _, cv in g[1]))
    for name, items in order:
        place_group(items)
    place_group(common)
    return pages, regions


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    groups, common = collect()
    pages, regions = pack(groups, common)
    for k, pg in enumerate(pages):
        used = pg["y"]
        pg["img"].convert("RGB").save(os.path.join(OUT, "fusion-panel-%d.png" % k), optimize=True)
        # the lightmap only needs half the resolution (same UV layout)
        pg["lm"].convert("RGB").resize((PAGE // 2, PAGE // 2), Image.LANCZOS).save(
            os.path.join(OUT, "fusion-panel-%d-lm.png" % k), optimize=True)
        print("page %d: used height %d px" % (k, used))
    with open(os.path.join(BUILD, "atlas.json"), "w") as fh:
        json.dump({"pages": len(pages), "regions": regions}, fh, indent=0)
    print("%d regions on %d page(s)" % (len(regions), len(pages)))


if __name__ == "__main__":
    main()
