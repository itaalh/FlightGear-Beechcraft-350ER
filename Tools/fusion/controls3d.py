"""Blender geometry of the panels and controls of cockpit_spec.py.

Every panel gives one static object "F.<panel>" (plate, screws, switch nuts, button housings, gauge bezels and
dials) textured with its atlas page, plus one object per moving or clickable part:
  toggle   F.<n>.lever, F.<n>.hs.up / .hs.dn (invisible pick boxes), F.<n>.guard (+ .hs.guard)
  knob     F.<n>.knob (+ F.<n>.push: invisible cap for the push action)
  dualknob F.<n>.outer, F.<n>.inner, F.<n>.push
  button   F.<n>.cap (+ F.<n>.lamp: lit bar)       pushlight F.<n>.cap (lit lens)
  lamp     F.<n>.lamp                               gauge     F.<n>.needle<k> (+ F.<n>.d<k> counter drums)
  hotspot  F.<n>.hs
Pivot points and axes needed by the animations are stored in the returned `anim` dictionary (model frame, m),
read by gen_xml.py from Tools/fusion/_build/pivots.json.
"""

import math

from layout import Frame, add, mul, sub, cross, norm, rounded_rect, circle
from shapes import MeshBuilder, fr_point, frame_ring, lathe, prism, rrect_prism, box, tube
from spec_base import Button, DualKnob, Gauge, Hotspot, Knob, Lamp, PushLight, Toggle, Decor
from layout import Y0 as S_Y0

MM = 0.001


class Ctx:
    """Build context: atlas regions, the per-panel static mesh and the animation data."""

    def __init__(self, regions, coll, build_obj):
        self.regions = regions
        self.coll = coll
        self.build_obj = build_obj          # (name, MeshBuilder, texture page or None, props) -> object
        self.anim = {}

    def region(self, key):
        return self.regions.get(key)

    def uv_rect(self, key, w, h, cx=0.0, cy=0.0):
        """UV function of a w x h (m) rectangle centred on (cx, cy) mapped on the atlas region `key`."""
        r = self.regions[key]
        _, u0, v0, u1, v1 = r

        def f(p):
            return (u0 + (p[0] - cx + w / 2) / w * (u1 - u0), v0 + (p[1] - cy + h / 2) / h * (v1 - v0))
        return f

    def page(self, key):
        r = self.regions.get(key)
        return None if r is None else r[0]


def P(fr, x_mm, y_mm):
    return (x_mm * MM, y_mm * MM)


# -----------------------------------------------------------------------------------------------------------------
def build_panel(ctx, p):
    fr = p.frame
    st = MeshBuilder()
    key = "panel:" + p.name
    w, h = p.w * MM, p.h * MM
    z0, z1 = p.elev * MM, p.face_z * MM
    uv = ctx.uv_rect(key, w, h)
    if not p.custom:
        # edges in the panel paint, the face textured with the panel drawing
        rrect_prism(st, fr, 0.0, 0.0, w, h, p.radius * MM, z0 - 0.002, z1, "panel",
                    bevel=min(0.0008, p.thick * MM * 0.4), front_mat=p.material, front_uv=uv)
    if p.screws and not p.custom:
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx = sx * (p.w / 2 - 3.2)
                cy = sy * (p.h / 2 - 3.2)
                lathe(st, fr, [(1.5 * MM, z1), (1.45 * MM, z1 + 0.35 * MM), (0.9 * MM, z1 + 0.7 * MM)], "nut", n=8,
                      cx=cx * MM, cy=cy * MM)
    for c in p.controls:
        BUILDERS[c.kind](ctx, p, c, st)
    ctx.build_obj("F." + p.name, st, ctx.page(key), {})


# -----------------------------------------------------------------------------------------------------------------
# toggle switch

LEVER_PROFILE = [(0.0, -0.5), (1.9, 0.0), (1.85, 2.5), (1.35, 13.2), (1.55, 14.0), (1.95, 15.0), (1.75, 16.2),
                 (1.1, 16.9), (0.0, 17.2)]


def build_toggle(ctx, p, t, st):
    fr = p.frame
    z = p.face_z * MM
    x, y = t.x * MM, t.y * MM
    # static: hex nut and threaded bushing
    lathe(st, fr, [(5.0 * MM, z), (5.0 * MM, z + 2.0 * MM), (4.4 * MM, z + 2.5 * MM)], "nut", n=6, cx=x, cy=y,
          smooth=False, a0=math.radians(30))
    lathe(st, fr, [(3.1 * MM, z + 2.4 * MM), (3.1 * MM, z + 5.6 * MM), (2.5 * MM, z + 6.2 * MM)], "nut", n=14, cx=x,
          cy=y)
    pivot = fr_point(fr, (x, y), z + 5.2 * MM)
    # lever, modelled straight out along the panel normal
    lf = Frame(pivot, fr.u, fr.v)
    lb = MeshBuilder()
    scale = t.lever / 17.2
    lathe(lb, lf, [(r * MM, zz * scale * MM) for r, zz in LEVER_PROFILE], "chrome", n=12, cap_top=False)
    ctx.build_obj(t.obj("lever"), lb, None, {})
    axis = fr.u if not t.horizontal else fr.v
    ctx.anim[t.name] = {"pivot": pivot, "axis": axis, "normal": fr.n, "u": fr.u, "v": fr.v}
    # pick boxes: upper / lower half (or right / left for horizontal switches)
    for part, sgn in (("up", 1), ("dn", -1)):
        hb = MeshBuilder()
        if t.horizontal:
            cx, cy, bw, bh = x + sgn * 5.5 * MM, y, 11.0 * MM, 14.0 * MM
        else:
            cx, cy, bw, bh = x, y + sgn * 5.5 * MM, 11.0 * MM, 11.0 * MM
        box(hb, fr, cx, cy, bw, bh, z + 0.5 * MM, z + 19.0 * MM, "hotspot")
        ctx.build_obj(t.obj("hs." + part), hb, None, {"ac_twosided": True})
    if t.guard:
        g = MeshBuilder()
        # red cover hinged at its top edge, closed over the switch in the NORM (up) position
        gw, gh, gd = 13.0 * MM, 22.0 * MM, 20.0 * MM
        top = y + 12.0 * MM
        for dx in (-gw / 2, gw / 2 - 1.2 * MM):
            box(g, fr, x + dx + 0.6 * MM, top - gh / 2, 1.2 * MM, gh, z, z + gd, "red")
        box(g, fr, x, top - 0.6 * MM, gw, 1.2 * MM, z, z + gd, "red")
        box(g, fr, x, top - gh / 2, gw, gh, z + gd - 1.2 * MM, z + gd, "red")
        ctx.build_obj(t.obj("guard"), g, None, {})
        ctx.anim[t.name]["hinge"] = fr_point(fr, (x, top), z)
        hs = MeshBuilder()
        box(hs, fr, x, top - gh / 2, gw + 2 * MM, gh, z + gd, z + gd + 1.5 * MM, "hotspot")
        ctx.build_obj(t.obj("hs.guard"), hs, None, {"ac_twosided": True})


# -----------------------------------------------------------------------------------------------------------------
# knobs

def knob_mesh(ctx, fr, style, d, h, z, x, y, color):
    kb = MeshBuilder()
    r = d / 2 * MM
    hh = h * MM
    key = "knob:" + style
    top_uv = None
    if ctx.region(key):
        _, u0, v0, u1, v1 = ctx.region(key)
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
        hu, hv = (u1 - u0) / 2, (v1 - v0) / 2
        top_uv = lambda c: (cu + c[0] * hu * 0.95, cv + c[1] * hv * 0.95)
    mat = color
    if style == "selector":
        # round base and a pointer bar ("chicken head")
        lathe(kb, fr, [(r * 0.78, z), (r * 0.78, z + hh * 0.45), (r * 0.70, z + hh * 0.5)], mat, n=20, cx=x, cy=y)
        bw, bl = d * 0.34 * MM, d * 1.02 * MM
        rrect_prism(kb, fr, x, y, bw, bl, bw / 2, z, z + hh, mat, bevel=0.6 * MM,
                    front_uv=(lambda p: top_uv(((p[0] - x) / (bl / 2), (p[1] - y) / (bl / 2)))) if top_uv else None)
    elif style == "cb":
        lathe(kb, fr, [(r, z), (r, z + hh * 0.9), (r * 0.9, z + hh)], "knob", n=16, cx=x, cy=y, top_uv=top_uv)
        lathe(kb, fr, [(r * 1.02, z - 4.0 * MM), (r * 1.02, z - 0.2 * MM)], "white", n=16, cx=x, cy=y, cap_top=False)
    else:
        flutes = {"fgp": 28, "rheostat": 20, "receiver": 18, "bar": 20, "trim": 30}.get(style, 20)
        n = flutes * 2
        rings = []
        prof = [(1.0, 0.0), (1.0, 0.72), (0.96, 0.9), (0.86, 1.0)]
        for rr, zz in prof:
            ring = []
            for i in range(n):
                a = 2 * math.pi * i / n
                rad = r * rr * (1.0 if (i % 2 == 0 or zz > 0.8) else 0.93)
                ring.append(fr_point(fr, (x + rad * math.cos(a), y + rad * math.sin(a)), z + hh * zz))
            rings.append(ring)
        for k in range(len(rings) - 1):
            kb.quad_strip(rings[k], rings[k + 1], mat, closed=True, smooth=True)
        top = [fr_point(fr, (x + r * 0.86 * math.cos(2 * math.pi * i / n), y + r * 0.86 * math.sin(2 * math.pi * i / n)),
                        z + hh) for i in range(n)]
        uvs = [top_uv((math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))) for i in range(n)] if top_uv else None
        kb.face(top, mat, uvs)
    return kb, (ctx.page(key) if top_uv else None)


def build_knob(ctx, p, k, st):
    fr = p.frame
    z = p.face_z * MM
    x, y = k.x * MM, k.y * MM
    if k.style != "cb":
        # shaft collar
        lathe(st, fr, [(k.d * 0.30 * MM, z), (k.d * 0.30 * MM, z + 1.2 * MM)], "nut", n=12, cx=x, cy=y)
    kz = z + (1.0 * MM if k.style != "cb" else 0.0)
    kb, page = knob_mesh(ctx, fr, k.style, k.d, k.h, kz, x, y, k.color)
    ctx.build_obj(k.obj("knob"), kb, page, {})
    ctx.anim[k.name] = {"pivot": fr_point(fr, (x, y), z), "axis": mul(fr.n, -1.0), "normal": fr.n, "u": fr.u,
                        "v": fr.v}
    if k.push:
        pb = MeshBuilder()
        lathe(pb, fr, [(k.d * 0.30 * MM, kz + k.h * MM + 0.3 * MM), (k.d * 0.30 * MM, kz + k.h * MM + 1.0 * MM)],
              "hotspot", n=12, cx=x, cy=y)
        ctx.build_obj(k.obj("push"), pb, None, {"ac_twosided": True})


def build_dualknob(ctx, p, k, st):
    fr = p.frame
    z = p.face_z * MM
    x, y = k.x * MM, k.y * MM
    ob, pg = knob_mesh(ctx, fr, "fgp", k.d_outer, 6.0, z + 0.8 * MM, x, y, "knob")
    ctx.build_obj(k.obj("outer"), ob, None, {})
    ib, pg2 = knob_mesh(ctx, fr, "rheostat", k.d_inner, 6.0, z + 6.8 * MM, x, y, "knob")
    ctx.build_obj(k.obj("inner"), ib, pg2, {})
    ctx.anim[k.name] = {"pivot": fr_point(fr, (x, y), z), "axis": mul(fr.n, -1.0), "normal": fr.n, "u": fr.u, "v": fr.v}
    if k.push:
        pb = MeshBuilder()
        lathe(pb, fr, [(k.d_inner * 0.32 * MM, z + 13.2 * MM), (k.d_inner * 0.32 * MM, z + 13.8 * MM)], "hotspot",
              n=12, cx=x, cy=y)
        ctx.build_obj(k.obj("push"), pb, None, {"ac_twosided": True})


# -----------------------------------------------------------------------------------------------------------------
# buttons, push-lights, lamps

def build_button(ctx, p, b, st):
    fr = p.frame
    z = p.face_z * MM
    x, y = b.x * MM, b.y * MM
    w, h = b.w * MM, b.h * MM
    round_cap = b.cap.endswith("_round")
    # housing ring
    if round_cap:
        lathe(st, fr, [(w / 2 + 1.6 * MM, z), (w / 2 + 1.6 * MM, z + 2.0 * MM), (w / 2 + 0.4 * MM, z + 2.4 * MM),
                       (w / 2 + 0.3 * MM, z + 0.5 * MM)], "bezel", n=20, cx=x, cy=y, cap_top=False)
    else:
        frame_ring(st, fr, x, y, w + 3.0 * MM, h + 3.0 * MM, 1.4 * MM, w + 0.5 * MM, h + 0.5 * MM, 0.8 * MM, z,
                   z + 2.2 * MM, "bezel", inner_depth=2.0 * MM)
    cb = MeshBuilder()
    key = "btn:" + b.name
    cap_mat = {"cap": "cap", "cap_dark": "bezel", "bezel_key": "bezel", "red_round": "red", "cap_dark_round": "bezel",
               "lens": "lens"}.get(b.cap, "cap")
    top = z + b.depth * MM
    if round_cap:
        lathe(cb, fr, [(w / 2, z + 0.2 * MM), (w / 2, top - 0.8 * MM), (w / 2 - 0.8 * MM, top)], cap_mat, n=20, cx=x,
              cy=y)
        page = None
    else:
        uv = ctx.uv_rect(key, w, h, x, y) if ctx.region(key) else None
        rrect_prism(cb, fr, x, y, w, h, 0.8 * MM, z + 0.2 * MM, top, cap_mat, bevel=0.5 * MM, front_mat="plate" if uv else None,
                    front_uv=uv)
        page = ctx.page(key) if uv else None
    ctx.build_obj(b.obj("cap"), cb, page, {})
    ctx.anim[b.name] = {"normal": fr.n, "pivot": fr_point(fr, (x, y), z)}
    if b.lamp and b.lamp_style == "bar":
        lb = MeshBuilder()
        box(lb, fr, x, y + h / 2 - 1.6 * MM, w * 0.55, 1.1 * MM, top, top + 0.25 * MM, "white")
        ctx.build_obj(b.obj("lamp"), lb, None, {})


def build_lamp(ctx, p, l, st):
    fr = p.frame
    z = p.face_z * MM
    x, y = l.x * MM, l.y * MM
    w, h = l.w * MM, l.h * MM
    key = "lamp:" + l.name
    lb = MeshBuilder()
    if l.shape == "round":
        lathe(st, fr, [(w / 2 + 1.0 * MM, z), (w / 2 + 1.0 * MM, z + 1.5 * MM), (w / 2 + 0.2 * MM, z + 1.8 * MM)],
              "bezel", n=16, cx=x, cy=y, cap_top=False)
        lathe(lb, fr, [(w / 2, z), (w / 2, z + 1.4 * MM), (w / 2 * 0.7, z + 2.0 * MM)], "lens", n=16, cx=x, cy=y)
        page = None
    else:
        frame_ring(st, fr, x, y, w + 2.0 * MM, h + 2.0 * MM, 0.8 * MM, w, h, 0.4 * MM, z, z + l.depth * MM, "bezel",
                   inner_depth=0.4 * MM)
        uv = ctx.uv_rect(key, w, h, x, y)
        rrect_prism(lb, fr, x, y, w, h, 0.3 * MM, z, z + (l.depth - 0.4) * MM, "lens", front_mat="plate", front_uv=uv)
        page = ctx.page(key)
    ctx.build_obj(l.obj("lamp"), lb, page, {})


# -----------------------------------------------------------------------------------------------------------------
# gauges

def build_gauge(ctx, p, g, st):
    fr = p.frame
    z = p.face_z * MM
    x, y = g.x * MM, g.y * MM
    r = g.d / 2 * MM
    rb = r + g.bezel * MM
    # bezel: square flange with a round ring
    rrect_prism(st, fr, x, y, 2 * rb + 2 * MM, 2 * rb + 2 * MM, 3.0 * MM, z, z + 1.2 * MM, "bezel")
    lathe(st, fr, [(rb, z + 1.2 * MM), (rb, z + g.depth * MM - 1.0 * MM), (rb - 1.0 * MM, z + g.depth * MM),
                   (r + 0.3 * MM, z + g.depth * MM - 0.3 * MM), (r, z + 2.0 * MM)], "bezel", n=36, cx=x, cy=y,
          cap_top=False)
    key = "dial:" + g.name
    uv = ctx.uv_rect(key, 2 * r, 2 * r, x, y)
    dial = [(x + r * math.cos(2 * math.pi * i / 36), y + r * math.sin(2 * math.pi * i / 36)) for i in range(36)]
    st.face([fr_point(fr, q, z + 2.0 * MM) for q in dial], "plate", [uv(q) for q in dial])
    centre = fr_point(fr, (x, y), z + 2.0 * MM)
    ctx.anim[g.name] = {"pivot": centre, "axis": mul(fr.n, -1.0), "normal": fr.n}
    for k, (prop, table, style) in enumerate(g.needles):
        nb = MeshBuilder()
        col = "white" if style == "white" else "red"
        zz = z + (2.6 + 0.4 * k) * MM
        L = r * (0.86 if k == 0 else 0.62)
        pts = [(x - 0.9 * MM, y - 0.18 * r), (x + 0.9 * MM, y - 0.18 * r), (x + 0.35 * MM, y + L), (x - 0.35 * MM, y + L)]
        nb.face([fr_point(fr, q, zz) for q in pts], col)
        lathe(nb, fr, [(2.2 * MM, zz - 0.2 * MM), (2.2 * MM, zz + 0.3 * MM), (1.2 * MM, zz + 0.7 * MM)], "knob", n=12,
              cx=x, cy=y)
        ctx.build_obj(g.obj("needle%d" % k), nb, None, {})
    if g.dial == "hobbs":
        # counter drums: 5 digits in the window of the dial (tenths last)
        reg = ctx.region("digits")
        if reg:
            _, u0, v0, u1, v1 = reg
            dh = (v1 - v0) / 10.0
            for k in range(5):
                db = MeshBuilder()
                cx = x + (-9.6 + 4.8 * k) * MM
                pts = [(cx - 2.1 * MM, y - 2.8 * MM), (cx + 2.1 * MM, y - 2.8 * MM), (cx + 2.1 * MM, y + 2.8 * MM),
                       (cx - 2.1 * MM, y + 2.8 * MM)]
                # the window shows digit 0 (top cell of the strip); textranslate moves down the strip
                uvs = [(u0, v1 - dh), (u1, v1 - dh), (u1, v1), (u0, v1)]
                db.face([fr_point(fr, q, z + 2.4 * MM) for q in pts], "plate", uvs)
                ctx.build_obj(g.obj("d%d" % k), db, reg[0], {})
            ctx.anim[g.name]["digit_step"] = dh


def build_hotspot(ctx, p, hs, st):
    fr = p.frame
    z = p.face_z * MM
    hb = MeshBuilder()
    box(hb, fr, hs.x * MM, hs.y * MM, hs.w * MM, hs.h * MM, z + 0.3 * MM, z + hs.z * MM, "hotspot")
    ctx.build_obj(hs.obj("hs"), hb, None, {"ac_twosided": True})


# -----------------------------------------------------------------------------------------------------------------
# decorations

def build_decor(ctx, p, d, st):
    fr = p.frame
    z = p.face_z * MM
    x, y = d.x * MM, d.y * MM
    r = d.recipe
    if r == "screen":
        w, h = d.params["w"] * MM, d.params["h"] * MM
        # raised frame on the face, the glass just above the face inside it
        frame_ring(st, fr, x, y, w + 5 * MM, h + 5 * MM, 1.5 * MM, w, h, 0.5 * MM, z - 0.2 * MM, z + 2.5 * MM, "bezel",
                   inner_depth=2.1 * MM)
        sb = MeshBuilder()
        pts = [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)]
        sb.face([fr_point(fr, q, z + 0.4 * MM) for q in pts], "screen", [(0, 0), (1, 0), (1, 1), (0, 1)])
        ctx.build_obj(d.params["object"], sb, "screen", {})
    elif r == "pitch_wheel":
        rrect_prism(st, fr, x, y, 9 * MM, 30 * MM, 2 * MM, z - 3 * MM, z + 0.2 * MM, "shell")
        wb = MeshBuilder()
        # drum with ribs, axis along the panel u
        n = 28
        R = 11.0 * MM
        ax = fr.u
        cz = z - R + 3.2 * MM
        rings = []
        for xs in (-3.2 * MM, 3.2 * MM):
            ring = []
            for i in range(n):
                a = 2 * math.pi * i / n
                rad = R * (1.0 if i % 2 == 0 else 0.93)
                ring.append(fr_point(fr, (x + xs, y + rad * math.sin(a)), cz + rad * math.cos(a)))
            rings.append(ring)
        wb.quad_strip(rings[1], rings[0], "knob", closed=True, smooth=True)
        ctx.build_obj("F.FGP.WHEEL.wheel", wb, None, {})
        ctx.anim["FGP.WHEEL"] = {"pivot": fr_point(fr, (x, y), cz), "axis": ax}
    elif r == "column_boot":
        lathe(st, fr, [(24 * MM, z), (24 * MM, z + 1.5 * MM), (21 * MM, z + 2.5 * MM), (15 * MM, z + 1.0 * MM),
                       (15 * MM, z - 6 * MM)], "bezel", n=32, cx=x, cy=y, cap_top=False)
        lathe(st, fr, [(15 * MM, z - 6 * MM), (1 * MM, z - 6 * MM)], "shell", n=32, cx=x, cy=y, cap_top=False)
    elif r == "gear_slot":
        rrect_prism(st, fr, x, y, 13 * MM, 58 * MM, 3 * MM, z, z + 1.5 * MM, "bezel")
        rrect_prism(st, fr, x, y, 7 * MM, 50 * MM, 2 * MM, z + 1.5 * MM, z + 1.55 * MM, "shell")
        # gear handle: arm from a pivot behind the panel through the slot, white wheel knob
        pivot = fr_point(fr, (x, y), z - 40 * MM)
        gb = MeshBuilder()
        a = fr_point(fr, (x, y), z - 38 * MM)
        b_ = fr_point(fr, (x, y), z + 26 * MM)
        tube(gb, [a, b_], 3.2 * MM, "chrome", n=12)
        knob_c = fr_point(fr, (x, y), z + 32 * MM)
        # the wheel: disc of radius 9 mm, thickness 11 mm, axis along the panel u
        rings = []
        for xs, rr in ((-5.5 * MM, 7.5 * MM), (-4.5 * MM, 9.0 * MM), (4.5 * MM, 9.0 * MM), (5.5 * MM, 7.5 * MM)):
            ring = []
            for i in range(24):
                ang = 2 * math.pi * i / 24
                ring.append(add(add(knob_c, mul(fr.u, xs)), add(mul(fr.v, rr * math.sin(ang)), mul(fr.n, rr * math.cos(ang)))))
            rings.append(ring)
        for k in range(3):
            gb.quad_strip(rings[k + 1], rings[k], "white", closed=True, smooth=True)
        gb.face(list(reversed(rings[-1])), "white")
        gb.face(rings[0], "white")
        ctx.build_obj("F.GEAR.handle", gb, None, {})
        lb = MeshBuilder()
        rl = [add(add(knob_c, mul(fr.u, 5.6 * MM)), add(mul(fr.v, 3.5 * MM * math.sin(2 * math.pi * i / 16)),
                                                         mul(fr.n, 3.5 * MM * math.cos(2 * math.pi * i / 16))))
              for i in range(16)]
        lb.face(list(reversed(rl)), "red")
        ctx.build_obj("F.GEAR.handle.lamp", lb, None, {})
        ctx.anim["GEAR"] = {"pivot": pivot, "axis": fr.u, "normal": fr.n, "v": fr.v}
        hb = MeshBuilder()
        box(hb, fr, x, y, 22 * MM, 60 * MM, z + 1 * MM, z + 44 * MM, "hotspot")
        ctx.build_obj("F.GEAR.hs", hb, None, {"ac_twosided": True})
    elif r == "jack":
        lathe(st, fr, [(4.5 * MM, z), (4.5 * MM, z + 1.5 * MM), (3.2 * MM, z + 1.8 * MM), (3.0 * MM, z + 0.3 * MM),
                       (2.0 * MM, z - 3.0 * MM)], "chrome", n=16, cx=x, cy=y, cap_top=False)
        lathe(st, fr, [(2.0 * MM, z - 3.0 * MM), (0.1 * MM, z - 3.0 * MM)], "shell", n=16, cx=x, cy=y, cap_top=False)
    elif r == "pbrake_handle":
        lathe(st, fr, [(5.5 * MM, z), (5.5 * MM, z + 2.5 * MM), (3.8 * MM, z + 3.2 * MM)], "nut", n=16, cx=x, cy=y)
        hb = MeshBuilder()
        tube(hb, [fr_point(fr, (x, y), z - 20 * MM), fr_point(fr, (x, y), z + 16 * MM)], 2.8 * MM, "chrome", n=12)
        tee = [fr_point(fr, (x - 11 * MM, y), z + 17 * MM), fr_point(fr, (x + 11 * MM, y), z + 17 * MM)]
        tube(hb, tee, 4.2 * MM, "knob", n=14)
        ctx.build_obj("F.PBRAKE.handle", hb, None, {})
        ctx.anim["PBRAKE"] = {"normal": fr.n}


BUILDERS = {"toggle": build_toggle, "knob": build_knob, "dualknob": build_dualknob, "button": build_button,
            "pushlight": build_button, "lamp": build_lamp, "gauge": build_gauge, "hotspot": build_hotspot,
            "decor": build_decor}


# -----------------------------------------------------------------------------------------------------------------
# control wheels (yokes)

YOKE_S = 0.355                      # lateral offset of the columns (pilot -, copilot +)
YOKE_TILT = 12.0                    # column rises towards the crew
YOKE_ENTRY_X = -4.618               # column leaves the lower panel (boot on the subpanels)
YOKE_ENTRY_Z = 0.022
YOKE_HUB_X = -4.330

# grip / bar centre line in the yoke plane (u right, v up), metres, left half from the horn tip to the centre
YOKE_PATH = [(-0.108, 0.094), (-0.124, 0.097), (-0.138, 0.088), (-0.145, 0.066), (-0.146, 0.040), (-0.144, 0.012),
             (-0.138, -0.016), (-0.126, -0.040), (-0.104, -0.056), (-0.070, -0.064), (-0.035, -0.066), (0.0, -0.066)]
YOKE_RADII = [0.012, 0.017, 0.019, 0.019, 0.018, 0.018, 0.017, 0.016, 0.015, 0.014, 0.0135, 0.013]


def yoke_frame(side):
    import math as m
    t = m.radians(YOKE_TILT)
    a = (m.cos(t), 0.0, m.sin(t))
    y = S_Y0 + side * YOKE_S
    hub = (YOKE_HUB_X, y, YOKE_ENTRY_Z + (YOKE_HUB_X - YOKE_ENTRY_X) * m.tan(t))
    return Frame(hub, (0.0, 1.0, 0.0), (-m.sin(t), 0.0, m.cos(t))), a, hub


def build_yokes(ctx):
    import math as m
    for side, k in ((-1, "L"), (1, "R")):
        fr, a, hub = yoke_frame(side)
        # column (moves fore and aft with the elevator)
        cb = MeshBuilder()
        entry = (YOKE_ENTRY_X - 0.06, hub[1], YOKE_ENTRY_Z - 0.06 * m.tan(m.radians(YOKE_TILT)))
        back = add(hub, mul(a, -0.022))
        tube(cb, [entry, back], 0.0175, "metal", n=18)
        ctx.build_obj("F.YOKE%s.column" % k, cb, None, {})
        # wheel: grips and lower bar swept along the path, hub with the emblem
        wb = MeshBuilder()
        path = YOKE_PATH + [(-p[0], p[1]) for p in reversed(YOKE_PATH[:-1])]
        radii = YOKE_RADII + list(reversed(YOKE_RADII[:-1]))
        pts = [fr_point(fr, p, 0.0) for p in path]
        tube(wb, pts, 0.017, "yoke", n=14, radii=radii)
        # horn tips: rounded caps
        for p in (path[0], path[-1]):
            lathe(wb, Frame(fr_point(fr, p, 0.0), fr.u, fr.v), [(0.012, -0.004), (0.010, 0.004), (0.0, 0.008)], "yoke",
                  n=12, cap_top=False)
        hw, hh = 0.128, 0.076
        key = "yoke:emblem"
        uv = ctx.uv_rect(key, hw, hh, 0.0, -0.004) if ctx.region(key) else None
        rrect_prism(wb, fr, 0.0, -0.004, hw, hh, 0.034, -0.026, 0.022, "yoke", bevel=0.010, bevel_steps=3,
                    front_mat="plate" if uv else None, front_uv=uv, seg=8)
        page = ctx.page(key) if uv else None
        ctx.build_obj("F.YOKE%s.wheel" % k, wb, page, {})
        # switches on the outer grip: AP/YD DISC (red, aft face of the horn), pitch trim rocker (top), PTT (front)
        o = -1 if k == "L" else 1                       # outer grip on the left for the pilot, right for the copilot
        horn = (o * 0.128, 0.094)
        db = MeshBuilder()
        lathe(db, fr, [(0.0055, 0.012), (0.0055, 0.019), (0.004, 0.0215)], "red", n=14, cx=horn[0] - o * 0.002,
              cy=horn[1] - 0.004)
        ctx.build_obj("F.YOKE%s.apdisc" % k, db, None, {})
        top = fr_point(fr, (o * 0.140, 0.103), 0.0)
        tf = Frame(top, fr.u, fr.n)                      # rocker frame: its normal points up (yoke v)
        for part, dz in (("trimdn", -0.0055), ("trimup", 0.0055)):
            rb = MeshBuilder()
            rrect_prism(rb, Frame(fr_point(fr, (o * 0.140, 0.101), dz), fr.u, mul(fr.n, -1.0)), 0.0, 0.0, 0.009,
                        0.009, 0.002, 0.0, 0.006, "knob", bevel=0.0015)
            ctx.build_obj("F.YOKE%s.%s" % (k, part), rb, None, {})
        pb = MeshBuilder()
        rrect_prism(pb, Frame(fr_point(fr, (o * 0.146, 0.028), -0.017), fr.u, fr.v), 0.0, 0.0, 0.010, 0.026, 0.004,
                    -0.006, 0.0, "knob", bevel=0.002)
        ctx.build_obj("F.YOKE%s.ptt" % k, pb, None, {})
        ctx.anim["YOKE" + k] = {"hub": hub, "axis": a, "normal": fr.n, "v": fr.v, "outer": o}
