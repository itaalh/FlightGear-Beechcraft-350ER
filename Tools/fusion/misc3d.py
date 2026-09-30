"""Blender geometry of the overhead console body, the standby magnetic compass and the crew seats."""

import math

import cockpit_spec as SPEC
from layout import Y0, Frame, add, mul
from shapes import MeshBuilder, fr_point, lathe, rrect_prism, tube
from pedestal3d import wbox


def ceiling_z(x):
    """Inner ceiling of the fuselage (Models/KingAir.ac) on the centre line."""
    pts = [(-4.30, 0.803), (-4.15, 0.879), (-4.00, 0.907), (-3.85, 0.916)]
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def build_overhead_body(ctx):
    """Console between the ceiling and the overhead panels (beige trim)."""
    g = SPEC.OVH_G_FRAME
    s = SPEC.OVH_SW_FRAME
    hw = 0.205
    # side profile (x, z) from the front lower edge of the gauge panel, along both faces, up to the ceiling
    g0 = fr_point(g, (0.0, -0.034), -0.001)
    g1 = fr_point(g, (0.0, 0.034), -0.001)
    s0 = fr_point(s, (0.0, -0.128), -0.001)
    s1 = fr_point(s, (0.0, 0.128), -0.001)
    prof = [(g0[0], g0[2]), (g1[0], g1[2]), (s0[0], s0[2]), (s1[0], s1[2]),
            (s1[0], ceiling_z(s1[0]) + 0.012), (g0[0], ceiling_z(g0[0]) + 0.004)]
    mb = MeshBuilder()
    a = [(x, Y0 - hw, z) for x, z in prof]
    b = [(x, Y0 + hw, z) for x, z in prof]
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        mb.face([a[j], a[i], b[i], b[j]], "beige")
    mb.face(a, "beige")
    mb.face(list(reversed(b)), "beige")
    ctx.build_obj("F.OVH.body", mb, None, {})


def build_compass(ctx):
    """Standby magnetic compass hanging below the windshield top frame, on the centre post."""
    y = 0.033
    cx, cz = -4.335, 0.715
    st = MeshBuilder()
    # bracket to the top frame
    wbox(st, cx - 0.006, cx + 0.006, y - 0.008, y + 0.008, cz + 0.022, 0.795, "shell")
    # housing: black box with a window on the aft face
    wbox(st, cx - 0.030, cx + 0.018, y - 0.030, y + 0.030, cz - 0.022, cz + 0.024, "shell")
    fr = Frame((cx + 0.0185, y, cz), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    st.face([fr_point(fr, p, 0.0) for p in ((-0.024, -0.016), (0.024, -0.016), (0.024, 0.016), (-0.024, 0.016))],
            "screen_off")
    ctx.build_obj("F.COMPASS", st, None, {})
    # card: drum about a vertical axis behind the window, the heading strip wrapped round it
    reg = ctx.region("compass")
    r, h = 0.019, 0.013
    ccx = cx - 0.004
    mb = MeshBuilder()
    n = 48
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        # the heading under the lubber line (aft side of the drum, towards the crew) is the reading
        pts = [(ccx + r * math.cos(a0), y + r * math.sin(a0), cz - h / 2),
               (ccx + r * math.cos(a1), y + r * math.sin(a1), cz - h / 2),
               (ccx + r * math.cos(a1), y + r * math.sin(a1), cz + h / 2),
               (ccx + r * math.cos(a0), y + r * math.sin(a0), cz + h / 2)]
        uvs = None
        if reg:
            _, u0, v0, u1, v1 = reg
            f0, f1 = 1.0 - i / n, 1.0 - (i + 1) / n        # headings increase to the left, as on a real card
            uvs = [(u0 + f0 * (u1 - u0), v0), (u0 + f1 * (u1 - u0), v0), (u0 + f1 * (u1 - u0), v1),
                   (u0 + f0 * (u1 - u0), v1)]
        mb.face(pts, "plate" if reg else "white", uvs, smooth=True)
    ctx.build_obj("F.COMPASS.card", mb, reg[0] if reg else None, {})
    ctx.anim["COMPASS"] = {"pivot": (ccx, y, cz), "axis": (0.0, 0.0, 1.0)}
    lb = MeshBuilder()
    wbox(lb, cx + 0.0186, cx + 0.0190, y - 0.0006, y + 0.0006, cz - 0.014, cz + 0.014, "white")
    ctx.build_obj("F.COMPASS.lubber", lb, None, {})


def seat(ctx, side):
    """Crew seat (tan leather): base on rails, cushion with bolsters, reclined back, headrest, armrests."""
    y = Y0 + side * 0.355
    mb = MeshBuilder()
    x0, x1 = -4.33, -3.86                  # cushion front / rear
    zc = -0.19                             # cushion top
    # base and rails
    for dy in (-0.16, 0.16):
        wbox(mb, -4.36, -3.80, y + dy - 0.012, y + dy + 0.012, -0.558, -0.540, "metal")
    wbox(mb, -4.26, -3.90, y - 0.17, y + 0.17, -0.540, -0.300, "shell")
    # cushion (horizontal frame, normal up)
    cf = Frame(((x0 + x1) / 2, y, zc - 0.07), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0))
    rrect_prism(mb, cf, 0.0, 0.0, 0.46, x1 - x0, 0.06, 0.0, 0.075, "leather", bevel=0.03, bevel_steps=4,
                side_smooth=True)
    for dy in (-0.205, 0.205):
        rrect_prism(mb, cf, dy, 0.0, 0.07, x1 - x0 - 0.02, 0.03, 0.0, 0.095, "leather", bevel=0.03, bevel_steps=4,
                    side_smooth=True)
    # back, reclined 14 deg
    t = math.radians(14.0)
    bb = (x1 - 0.02, y, zc)
    bf = Frame(add(bb, (math.sin(t) * 0.32, 0.0, math.cos(t) * 0.32)), (0.0, -1.0, 0.0), (math.sin(t), 0.0, math.cos(t)))
    rrect_prism(mb, bf, 0.0, 0.0, 0.46, 0.62, 0.07, 0.0, 0.10, "leather", bevel=0.035, bevel_steps=4, side_smooth=True)
    for dy in (-0.21, 0.21):
        rrect_prism(mb, bf, dy, -0.03, 0.06, 0.52, 0.03, 0.0, 0.125, "leather", bevel=0.03, bevel_steps=4,
                    side_smooth=True)
    # headrest
    hf = Frame(add(bb, (math.sin(t) * 0.72, 0.0, math.cos(t) * 0.72)), (0.0, -1.0, 0.0), (math.sin(t), 0.0, math.cos(t)))
    rrect_prism(mb, hf, 0.0, 0.0, 0.26, 0.17, 0.06, 0.02, 0.10, "leather", bevel=0.03, bevel_steps=4, side_smooth=True)
    # armrests (inboard and outboard) on posts
    for dy in (-0.25, 0.25):
        wbox(mb, x1 - 0.30, x1 - 0.02, y + dy - 0.03, y + dy + 0.03, zc + 0.17, zc + 0.22, "leather", smooth=False)
        wbox(mb, x1 - 0.05, x1 - 0.02, y + dy - 0.01, y + dy + 0.01, zc, zc + 0.17, "shell")
    ctx.build_obj("F.SEAT%s" % ("L" if side < 0 else "R"), mb, None, {"ac_crease": 60.0})


def build_misc(ctx):
    build_overhead_body(ctx)
    build_compass(ctx)
    seat(ctx, -1)
    seat(ctx, 1)
