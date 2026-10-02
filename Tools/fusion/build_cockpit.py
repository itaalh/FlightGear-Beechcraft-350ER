"""Builds the King Air 350 Pro Line Fusion flight deck in Blender and exports it for FlightGear.

blender -b --factory-startup --python Tools/fusion/build_cockpit.py -- [--preview] [--no-export] [--ref]

Outputs: Models/Fusion/fusion-cockpit.ac (+ Models/Fusion/Sources/fusion-cockpit.blend).
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy

import ac3d
import bl_common as C
import shell as S
from layout import Y0, Frame, add, mul, rounded_rect
from shapes import MeshBuilder, frame_ring, fr_point, lathe, material, prism, rrect_prism

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = os.path.join(C.REPO, "Models", "Fusion")


def collection(name, parent=None):
    coll = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(coll)
    return coll


# ----------------------------------------------------------------------------------------------------------------
def build_glareshield(coll):
    mb = MeshBuilder()
    stations = [-s for s in reversed(S.GS_STATIONS[1:])] + S.GS_STATIONS
    secs = []
    for s in stations:
        secs.append([(x, Y0 + s, z) for (x, z) in S.gs_section(s)])
    for a, b in zip(secs, secs[1:]):
        mb.quad_strip(a, b, "shell", closed=False, smooth=True, flip=True)
    # end caps (closed section outline)
    mb.face(list(secs[0]), "shell")
    mb.face(list(reversed(secs[-1])), "shell")
    ob = mb.build("GS.shell", coll, {"ac_crease": 50.0})
    return ob


def build_main_panel(coll):
    mb = MeshBuilder()
    cy = (S.MP_V[0] + S.MP_V[1]) / 2
    w = S.MP_U[1] - S.MP_U[0]
    h = S.MP_V[1] - S.MP_V[0]
    rrect_prism(mb, S.MP, 0.0, cy, w, h, 0.004, -0.025, 0.0, "shell")
    mb.build("MP.shell", coll)
    lb = MeshBuilder()
    rrect_prism(lb, S.LP, 0.0, 0.0, S.LP_U[1] - S.LP_U[0], S.LP_H, 0.004, -0.025, 0.0, "shell")
    lb.build("LP.shell", coll)


def build_displays(coll):
    for i, cx in enumerate(S.DISPLAY_X):
        n = i + 1
        mb = MeshBuilder()
        frame_ring(mb, S.MP, cx, 0.0, S.DISPLAY_W, S.DISPLAY_H, 0.010, S.SCREEN_W + 0.002, S.SCREEN_H + 0.002, 0.003,
                   -0.002, S.DISPLAY_Z, "bezel", inner_depth=S.DISPLAY_Z - S.SCREEN_Z)
        # black glass left and right of the 4:3 canvas
        band = (S.SCREEN_W - S.CANVAS_W) / 2
        for side in (-1, 1):
            x0 = cx + side * (S.CANVAS_W / 2)
            x1 = cx + side * (S.SCREEN_W / 2 + 0.001)
            xa, xb = min(x0, x1), max(x0, x1)
            pts = [(xa, -S.SCREEN_H / 2 - 0.001), (xb, -S.SCREEN_H / 2 - 0.001), (xb, S.SCREEN_H / 2 + 0.001),
                   (xa, S.SCREEN_H / 2 + 0.001)]
            mb.face([fr_point(S.MP, p, S.SCREEN_Z) for p in pts], "screen_off")
        mb.build("Display%d.bezel" % n, coll)
        # canvas target: the FG1000 display n, UV (0,0)-(1,1)
        sb = MeshBuilder()
        pts = [(cx - S.CANVAS_W / 2, -S.SCREEN_H / 2), (cx + S.CANVAS_W / 2, -S.SCREEN_H / 2),
               (cx + S.CANVAS_W / 2, S.SCREEN_H / 2), (cx - S.CANVAS_W / 2, S.SCREEN_H / 2)]
        sb.face([fr_point(S.MP, p, S.SCREEN_Z) for p in pts], "screen", [(0, 0), (1, 0), (1, 1), (0, 1)])
        sb.build("Fusion.Screen%d" % n, coll, {"ac_texture": "screen.png"})
        # touch softkeys: the 12 FG1000 softkey labels along the bottom of the canvas (768 px: labels in the
        # lowest ~26 px)
        kw = S.CANVAS_W / 12.0
        for k in range(12):
            hb = MeshBuilder()
            x0 = cx - S.CANVAS_W / 2 + k * kw
            y0 = -S.SCREEN_H / 2
            prism(hb, S.MP, lambda i, x0=x0, y0=y0: [(x0 + 0.0005, y0), (x0 + kw - 0.0005, y0),
                                                   (x0 + kw - 0.0005, y0 + 0.0085), (x0 + 0.0005, y0 + 0.0085)],
                  S.SCREEN_Z + 0.0003, S.SCREEN_Z + 0.004, "hotspot")
            ob = hb.build("Display%d.sk%d" % (n, k + 1), coll, {"ac_twosided": True})
            ob.hide_render = True


# ----------------------------------------------------------------------------------------------------------------
def reference(coll):
    c2, objs = ac3d.import_ac(os.path.join(C.REPO, "Models", "KingAir.ac"), "ref_fuselage")
    keep = {"Fuselage", "interior", "Windows.001", "Circle.005", "Cube.002"}
    for ob in objs:
        if ob.name not in keep:
            bpy.data.objects.remove(ob)
        elif ob.name.startswith("Windows"):
            ob.hide_render = True
    return c2


def texture_name(page):
    if page is None:
        return None
    if page == "screen":
        return "screen.png"
    return "fusion-panel-%d.png" % page


def build_spec(coll):
    import json
    import importlib
    import controls3d
    import cockpit_spec
    importlib.reload(cockpit_spec)
    with open(os.path.join(HERE, "_build", "atlas.json")) as fh:
        regions = json.load(fh)["regions"]

    def build_obj(name, mb, page, props):
        if not mb.faces:
            return None
        pr = dict(props)
        tex = texture_name(page)
        if tex:
            pr["ac_texture"] = tex
        ob = mb.build(name, coll, pr)
        if tex:
            from shapes import textured_variant
            for slot in ob.material_slots:
                slot.material = textured_variant(slot.material, os.path.join(OUT_DIR, tex))
        if ".hs" in name or name.endswith(".push"):
            ob.hide_render = True
        return ob

    ctx = controls3d.Ctx(regions, coll, build_obj)
    for p in cockpit_spec.PANELS:
        controls3d.build_panel(ctx, p)
    controls3d.build_yokes(ctx)
    import pedestal3d
    pedestal3d.build_pedestal(ctx)
    import misc3d
    misc3d.build_misc(ctx)
    anim = {k: {kk: list(vv) if isinstance(vv, (tuple, list)) else vv for kk, vv in v.items()}
            for k, v in ctx.anim.items()}
    with open(os.path.join(HERE, "_build", "pivots.json"), "w") as fh:
        json.dump(anim, fh, indent=0)


def export(coll):
    os.makedirs(OUT_DIR, exist_ok=True)
    objs = [o for o in coll.all_objects if o.type == "MESH"]
    n = ac3d.export_ac(os.path.join(OUT_DIR, "fusion-cockpit.ac"), objs, texture_of=lambda o: o.get("ac_texture"),
                       crease=40.0)
    import json
    with open(os.path.join(HERE, "_build", "objects.json"), "w") as fh:
        json.dump({o.name: o.get("ac_texture") for o in objs}, fh, indent=0)
    print("exported %d objects" % n)
    src = os.path.join(OUT_DIR, "Sources")
    os.makedirs(src, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(src, "fusion-cockpit.blend"), compress=True)


VIEWS = {
    "pilot": ((-4.00, -0.34, 0.58), 0, -14, 70, (1600, 900)),
    "photo": ((-3.62, Y0, 0.50), 0, -10, 74, (2000, 775)),
    "side": ((-4.25, -0.55, 0.45), -40, -18, 65, (1600, 900)),
    "fgp": ((-4.25, Y0, 0.48), 0, -14, 45, (1600, 900)),
    "lower": ((-4.10, -0.20, 0.35), 8, -38, 60, (1600, 900)),
    "right": ((-4.10, 0.25, 0.35), -12, -32, 60, (1600, 900)),
    "yoke": ((-3.90, -0.30, 0.30), 4, -12, 45, (1600, 900)),
    "pedestal": ((-3.92, Y0 + 0.22, 0.12), 32, -32, 62, (1600, 900)),
    "quad": ((-3.95, Y0 - 0.30, 0.20), -32, -30, 55, (1600, 900)),
    "aft": ((-3.70, Y0, 0.20), 0, -62, 60, (1600, 900)),
    "ovh": ((-3.95, Y0 - 0.20, 0.55), -25, 45, 70, (1600, 900)),
    "leftwall": ((-3.95, Y0 - 0.10, 0.35), 70, -30, 70, (1600, 900)),
    "rightwall": ((-3.95, Y0 + 0.10, 0.35), -70, -30, 70, (1600, 900)),
    "cabin": ((-3.20, Y0, 0.45), 0, -18, 80, (1600, 900)),
    "ccp": ((-4.00, -0.34, 0.58), -28, -58, 70, (1600, 900)),
}


def preview():
    shots = os.environ.get("FUSION_SHOTS", os.path.join(HERE, "_shots"))
    os.makedirs(shots, exist_ok=True)
    scn = bpy.context.scene
    world = bpy.data.worlds.new("preview")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.58, 0.62, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    scn.world = world
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 2.5
    so = bpy.data.objects.new("sun", sun)
    scn.collection.objects.link(so)
    so.rotation_euler = (math.radians(40), math.radians(-25), math.radians(60))
    engine = "BLENDER_EEVEE"
    try:
        scn.render.engine = engine
    except TypeError:
        engine = "BLENDER_EEVEE_NEXT"
    views = [a for a in ARGS if a in VIEWS] or ["pilot", "photo"]
    for k in views:
        eye, hdg, pitch, fov, res = VIEWS[k]
        cam = C.look_camera("cam_" + k, eye, hdg, pitch, fov)
        C.render(os.path.join(shots, "prev_%s.png" % k), cam, res=res, engine=engine, samples=16)


def main():
    C.clear_scene()
    cockpit = collection("cockpit")
    build_glareshield(cockpit)
    build_main_panel(cockpit)
    build_displays(cockpit)
    build_spec(cockpit)

    if "--ref" in ARGS or "--preview" in ARGS:
        reference(None)
    if "--preview" in ARGS:
        preview()
    if "--no-export" not in ARGS:
        for ob in list(bpy.data.objects):
            if ob.users_collection and ob.users_collection[0].name.startswith("ref_"):
                bpy.data.objects.remove(ob)
        export(cockpit)


main()
