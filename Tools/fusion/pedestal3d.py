"""Blender geometry of the pedestal: body, curved power quadrant (textured with the PED.QUAD drawing), levers,
flap lever, elevator trim wheel and its indicator, grab rails. The flat panels of the pedestal (trim knobs, cursor
control panels, keyboard, pressurization, CVR) are ordinary spec panels built by controls3d.build_panel.
"""

import math

import pedestal as PD
from layout import Y0, Frame, add, mul
from shapes import MeshBuilder, fr_point, lathe, rrect_prism, tube, box
from controls3d import MM


def wbox(mb, x0, x1, y0, y1, z0, z1, mat, smooth=False):
    """Axis-aligned box in the model frame (outward faces)."""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
        mb.face([v[i] for i in f], mat, smooth=smooth)


def build_pedestal(ctx):
    body = MeshBuilder()
    # front tower under the lower panel
    wbox(body, PD.TOWER_X[0], PD.TOWER_X[1], Y0 - PD.BODY_HW, Y0 + PD.BODY_HW, PD.FLOOR_Z, PD.TOWER_TOP, "shell")
    # trim face body and aft pedestal
    (tx0, tz0), (tx1, tz1) = PD.TRIM_FACE
    prof = [(tx1, PD.FLOOR_Z), (tx1, tz1), (tx0, tz0), (tx0, PD.FLOOR_Z)]
    ring_a = [(x, Y0 - PD.BODY_HW, z) for x, z in prof]
    ring_b = [(x, Y0 + PD.BODY_HW, z) for x, z in prof]
    for i in range(4):
        j = (i + 1) % 4
        body.face([ring_a[j], ring_a[i], ring_b[i], ring_b[j]], "shell")
    body.face(ring_a, "shell")
    body.face(list(reversed(ring_b)), "shell")
    wbox(body, PD.AFT_X[0], PD.AFT_X[1], Y0 - PD.AFT_HW, Y0 + PD.AFT_HW, PD.FLOOR_Z, PD.AFT_Z - 0.001, "shell")
    ctx.build_obj("F.PED.body", body, None, {})

    # quadrant: curved top (textured), sides and front
    q = MeshBuilder()
    reg = ctx.region("panel:PED.QUAD")
    a_front, a_aft = PD.QUAD_A
    steps = 36
    angles = [a_front + (a_aft - a_front) * i / steps for i in range(steps + 1)]
    L = PD.arc_len_mm() / 1000.0
    for k in range(steps):
        a0, a1 = angles[k], angles[k + 1]
        p0, p1 = PD.arc_point(a0), PD.arc_point(a1)
        quad = [(p0[0], Y0 + PD.QUAD_HW, p0[1]), (p0[0], Y0 - PD.QUAD_HW, p0[1]),
                (p1[0], Y0 - PD.QUAD_HW, p1[1]), (p1[0], Y0 + PD.QUAD_HW, p1[1])]
        uvs = None
        if reg:
            _, u0, v0, u1, v1 = reg
            f0 = (PD.quad_y_mm(a0) / 1000.0 + L / 2) / L
            f1 = (PD.quad_y_mm(a1) / 1000.0 + L / 2) / L
            uvs = [(u1, v0 + f0 * (v1 - v0)), (u0, v0 + f0 * (v1 - v0)), (u0, v0 + f1 * (v1 - v0)),
                   (u1, v0 + f1 * (v1 - v0))]
        q.face(quad, "plate" if reg else "shell", uvs, smooth=True)
    for side in (-1, 1):
        y = Y0 + side * PD.QUAD_HW
        pts = [(PD.arc_point(a)[0], y, PD.arc_point(a)[1]) for a in angles]
        pts += [(PD.arc_point(a_aft)[0], y, PD.FLOOR_Z), (PD.arc_point(a_front)[0], y, PD.FLOOR_Z)]
        q.face(pts if side > 0 else list(reversed(pts)), "shell")
    pf = PD.arc_point(a_front)
    q.face([(pf[0], Y0 - PD.QUAD_HW, PD.FLOOR_Z), (pf[0], Y0 - PD.QUAD_HW, pf[1]), (pf[0], Y0 + PD.QUAD_HW, pf[1]),
            (pf[0], Y0 + PD.QUAD_HW, PD.FLOOR_Z)], "shell")
    ctx.build_obj("F.PED.quadrant", q, reg[0] if reg else None, {"ac_crease": 30.0})

    # levers (modelled upright, animated about the pivot axis)
    for nm, off, prop, table, style, length in PD.LEVERS:
        lb = MeshBuilder()
        piv = (PD.PIVOT[0], Y0 + off, PD.PIVOT[1])
        fr = Frame(piv, (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))        # u = y, v = up, n = +x (aft)
        # stem: flat bar from inside the quadrant to the knob
        r0, r1 = PD.QUAD_R - 0.02, length - 0.012
        wbox(lb, piv[0] - 0.004, piv[0] + 0.004, piv[1] - 0.0025, piv[1] + 0.0025, piv[2] + r0, piv[2] + r1, "metal")
        top = piv[2] + length
        if style == "power":
            rrect_prism(lb, Frame((piv[0] - 0.014, piv[1], top - 0.017), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), 0.0, 0.0,
                        0.0205, 0.036, 0.006, 0.0, 0.028, "knob", bevel=0.003, bevel_steps=3)
        elif style == "prop":
            rings = []
            for yy, rr in ((-0.0095, 0.011), (-0.0080, 0.0135), (0.0080, 0.0135), (0.0095, 0.011)):
                ring = []
                for i in range(24):
                    ang = 2 * math.pi * i / 24
                    rad = rr * (1.0 if i % 2 == 0 else 0.9)
                    ring.append((piv[0] + rad * math.sin(ang), piv[1] + yy, top - 0.014 + rad * math.cos(ang)))
                rings.append(ring)
            for k in range(3):
                lb.quad_strip(rings[k], rings[k + 1], "knob", closed=True, smooth=True)
            lb.face(list(reversed(rings[0])), "knob")
            lb.face(rings[-1], "knob")
        else:
            wbox(lb, piv[0] - 0.006, piv[0] + 0.006, piv[1] - 0.0095, piv[1] + 0.0095, top - 0.030, top, "knob")
        ctx.build_obj("F.%s.lever" % nm, lb, None, {})
        ctx.anim[nm] = {"pivot": piv, "axis": (0.0, -1.0, 0.0)}
        if nm == "PWR0":
            # GO AROUND (left face of the knob) and GEAR HORN SILENCE (aft face) buttons
            gb = MeshBuilder()
            lathe(gb, Frame((piv[0], piv[1] - 0.0103, top - 0.010), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                  [(0.0045, 0.0), (0.0045, 0.0025), (0.0035, 0.0035)], "white", n=14)
            ctx.build_obj("F.PWR0.ga", gb, None, {})
            hb = MeshBuilder()
            rrect_prism(hb, Frame((piv[0] + 0.0145, piv[1], top - 0.026), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), 0.0, 0.0,
                        0.016, 0.007, 0.002, 0.0, 0.002, "red")
            ctx.build_obj("F.PWR0.ghs", hb, None, {})
            ctx.anim["PWR0"]["ga_normal"] = (0.0, -1.0, 0.0)

    # flap lever: tab in a vertical slot of the right side of the quadrant (UP / APPROACH / DOWN)
    fx, fz, fy = PD.FLAP_SLOT["x"], PD.FLAP_SLOT["z"], Y0 + PD.FLAP_SLOT["y"]
    sl = MeshBuilder()
    wbox(sl, fx - 0.006, fx + 0.006, fy - 0.001, fy + 0.0005, fz - 0.040, fz + 0.040, "bezel")
    ctx.build_obj("F.FLAP.slot", sl, None, {})
    fb = MeshBuilder()
    wbox(fb, fx - 0.004, fx + 0.004, fy - 0.004, fy + 0.012, fz - 0.003, fz + 0.003, "metal")
    wbox(fb, fx - 0.011, fx + 0.011, fy + 0.012, fy + 0.034, fz - 0.009, fz + 0.009, "white")
    ctx.build_obj("F.FLAP.handle", fb, None, {})
    ctx.anim["FLAP"] = {"normal": (0.0, 1.0, 0.0)}

    # elevator trim wheel (left side of the quadrant) and its indicator
    t = PD.TRIM_WHEEL
    wb = MeshBuilder()
    rings = []
    for yy, rr in ((-t["w"] / 2, t["r"] - 0.004), (-t["w"] / 2 + 0.002, t["r"]), (t["w"] / 2 - 0.002, t["r"]),
                   (t["w"] / 2, t["r"] - 0.004)):
        ring = []
        for i in range(72):
            ang = 2 * math.pi * i / 72
            rad = rr * (1.0 if (i % 2 == 0 or rr < t["r"]) else 0.975)
            ring.append((t["x"] + rad * math.sin(ang), Y0 + t["y"] + yy, t["z"] + rad * math.cos(ang)))
        rings.append(ring)
    for k in range(3):
        wb.quad_strip(rings[k], rings[k + 1], "knob", closed=True, smooth=True)
    wb.face(list(reversed(rings[0])), "knob")
    wb.face(rings[-1], "knob")
    # white index marks on the rim
    for i in range(0, 72, 12):
        ang = 2 * math.pi * i / 72
        c = (t["x"] + (t["r"] + 0.0005) * math.sin(ang), Y0 + t["y"], t["z"] + (t["r"] + 0.0005) * math.cos(ang))
        wbox(wb, c[0] - 0.0015, c[0] + 0.0015, c[1] - 0.006, c[1] + 0.006, c[2] - 0.0015, c[2] + 0.0015, "white")
    ctx.build_obj("F.TRIMWHEEL", wb, None, {})
    ctx.anim["TRIMWHEEL"] = {"pivot": (t["x"], Y0 + t["y"], t["z"]), "axis": (0.0, -1.0, 0.0)}
    pb = MeshBuilder()
    # indicator pointer on the left side face (PED.ETRIM), moves along the scale
    px, pz = -4.418, -0.335
    wbox(pb, px - 0.0035, px + 0.0035, Y0 - PD.QUAD_HW - 0.0028, Y0 - PD.QUAD_HW - 0.0008, pz - 0.0010, pz + 0.0010, "white")
    ctx.build_obj("F.ETRIM.pointer", pb, None, {})

    # grab rails across the aft pedestal
    rb = MeshBuilder()
    for xr in (-4.045, -3.868):
        pts = [(xr, Y0 - PD.AFT_HW + 0.012, PD.AFT_Z), (xr, Y0 - PD.AFT_HW + 0.012, PD.AFT_Z + 0.025),
               (xr, Y0 + PD.AFT_HW - 0.012, PD.AFT_Z + 0.025), (xr, Y0 + PD.AFT_HW - 0.012, PD.AFT_Z)]
        tube(rb, pts, 0.0045, "chrome", n=10)
    ctx.build_obj("F.PED.rails", rb, None, {})
