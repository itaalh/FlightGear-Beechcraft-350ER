"""Mesh building blocks for the cockpit (Blender side).

MeshBuilder collects polygons (world coordinates, model frame) with a material name, UVs and a smooth flag, then
creates one Blender object. Materials are created once by name from MATERIALS (viewport colour = AC3D colour).
Faces without UVs get the UV of the white texel block of the atlas (WHITE_UV), so that one textured object can mix
labelled and plain faces.
"""

import math
import os

import bpy

from layout import Frame, add, cross, dot, mul, norm, sub, rounded_rect, circle

WHITE_UV = (0.9990, 0.9990)     # atlas.py keeps the top right corner of every page white

# name: (rgb, spec, shininess, emission, transparency)
MATERIALS = {
    "shell":      ((0.105, 0.105, 0.112), 0.14, 14, 0.0, 0.0),    # glareshield / panel structure, matt black
    "panel":      ((0.090, 0.090, 0.095), 0.20, 20, 0.0, 0.0),    # instrument panel plates (dark grey paint)
    "plate":      ((1.000, 1.000, 1.000), 0.15, 20, 0.0, 0.0),    # textured plates (colour from the atlas)
    "bezel":      ((0.105, 0.105, 0.110), 0.30, 40, 0.0, 0.0),    # display bezels, avionics boxes
    "screen_off": ((0.010, 0.012, 0.015), 0.90, 90, 0.0, 0.0),    # glass of the displays (unlit parts)
    "screen":     ((1.000, 1.000, 1.000), 0.50, 60, 0.0, 0.0),    # canvas placement target
    "knob":       ((0.035, 0.035, 0.037), 0.35, 40, 0.0, 0.0),    # black knobs
    "knob_grey":  ((0.55, 0.56, 0.58), 0.60, 60, 0.0, 0.0),       # FGP knobs (satin aluminium)
    "chrome":     ((0.78, 0.78, 0.80), 0.95, 110, 0.0, 0.0),      # toggle levers
    "nut":        ((0.30, 0.30, 0.31), 0.70, 70, 0.0, 0.0),       # switch nuts, screws
    "cap":        ((0.62, 0.63, 0.65), 0.35, 30, 0.0, 0.0),       # light grey push button caps
    "lens":       ((0.20, 0.20, 0.20), 0.90, 100, 0.0, 0.0),      # annunciator lens (unlit)
    "red":        ((0.72, 0.05, 0.04), 0.40, 40, 0.0, 0.0),
    "white":      ((0.90, 0.90, 0.88), 0.30, 30, 0.0, 0.0),
    "beige":      ((0.66, 0.60, 0.50), 0.12, 12, 0.0, 0.0),       # interior trim
    "leather":    ((0.60, 0.53, 0.43), 0.25, 20, 0.0, 0.0),       # seats
    "carpet":     ((0.23, 0.21, 0.19), 0.02, 4, 0.0, 0.0),
    "yoke":       ((0.030, 0.030, 0.032), 0.55, 60, 0.0, 0.0),    # glossy black yokes
    "metal":      ((0.45, 0.46, 0.48), 0.70, 70, 0.0, 0.0),
    "hotspot":    ((1.0, 0.0, 1.0), 0.0, 1, 0.0, 1.0),            # invisible pick areas
}


def material(name):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    rgb, spec, shi, emis, trans = MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1.0 - trans if trans < 1.0 else 0.25)
    mat["ac_spec"] = (spec, spec, spec)
    mat["ac_shi"] = shi
    mat["ac_emis"] = (emis, emis, emis)
    mat["ac_trans"] = trans
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = max(0.05, 1.0 - spec)
        if trans >= 1.0:
            bsdf.inputs["Alpha"].default_value = 0.0
    return mat


def textured_variant(mat, image_path):
    """Copy of a material whose colour is multiplied by an image (preview renders); exported as its own AC3D
    material with the same colours."""
    name = "%s|%s" % (mat.name, os.path.basename(image_path))
    v = bpy.data.materials.get(name)
    if v is not None:
        return v
    v = mat.copy()
    v.name = name
    nt = v.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    img = bpy.data.images.load(image_path, check_existing=True)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs[6].default_value = (*mat.diffuse_color[:3], 1.0)
    nt.links.new(tex.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return v


class MeshBuilder:
    def __init__(self):
        self.verts = []
        self.faces = []      # (vertex indices, material name, uvs, smooth)

    def face(self, pts, mat, uvs=None, smooth=False):
        base = len(self.verts)
        self.verts.extend(tuple(p) for p in pts)
        self.faces.append((list(range(base, base + len(pts))), mat, uvs, smooth))

    def quad_strip(self, a, b, mat, closed=False, smooth=True, uv_a=None, uv_b=None, flip=False):
        """Faces between two point rows of equal length (a then b)."""
        n = len(a)
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            j = (i + 1) % n
            pts = [a[i], a[j], b[j], b[i]]
            uvs = None
            if uv_a is not None:
                uvs = [uv_a[i], uv_a[j], uv_b[j], uv_b[i]]
            if flip:
                pts.reverse()
                if uvs:
                    uvs.reverse()
            self.face(pts, mat, uvs, smooth)

    def loft(self, rings, mat, closed=True, smooth=True, cap_start=False, cap_end=False, cap_mat=None,
             cap_uv_start=None, cap_uv_end=None):
        for k in range(len(rings) - 1):
            self.quad_strip(rings[k], rings[k + 1], mat, closed=closed, smooth=smooth)
        if cap_start:
            self.face(list(reversed(rings[0])), cap_mat or mat,
                      list(reversed(cap_uv_start)) if cap_uv_start else None)
        if cap_end:
            self.face(list(rings[-1]), cap_mat or mat, cap_uv_end)

    def extend(self, other):
        base = len(self.verts)
        self.verts.extend(other.verts)
        for idx, mat, uvs, smooth in other.faces:
            self.faces.append(([i + base for i in idx], mat, uvs, smooth))

    def build(self, name, collection, props=None, weld=1e-6):
        me = bpy.data.meshes.new(name)
        mats = []
        for _, m, _, _ in self.faces:
            if m not in mats:
                mats.append(m)
        me.from_pydata(self.verts, [], [f[0] for f in self.faces])
        for m in mats:
            me.materials.append(material(m))
        uvl = me.uv_layers.new(name="UVMap")
        for poly, (idx, m, uvs, smooth) in zip(me.polygons, self.faces):
            poly.material_index = mats.index(m)
            poly.use_smooth = smooth
            for k, li in enumerate(poly.loop_indices):
                uvl.data[li].uv = uvs[k] if uvs else WHITE_UV
        if weld:
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
            bm.to_mesh(me)
            bm.free()
        me.validate()
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        for k, v in (props or {}).items():
            ob[k] = v
        return ob


# -----------------------------------------------------------------------------------------------------------------
# primitives in a panel frame (dimensions in metres, 2D outlines in the frame's u/v plane)

def prism(mb, fr, outline_of_inset, z_back, z_front, mat, bevel=0.0, bevel_steps=2, front_mat=None, front_uv=None,
          back=True, side_smooth=False):
    """Extrusion along the frame normal from z_back to z_front of outline_of_inset(inset) (list of 2D points).
    The front edge is rounded with radius bevel (outline inset by bevel on the front face).
    front_uv(point2d) gives the UV of a front face point (for labelled faces)."""
    layers = [(0.0, z_back)]
    if bevel > 0:
        for s in range(bevel_steps + 1):
            a = (math.pi / 2) * s / bevel_steps
            layers.append((bevel * (1 - math.cos(a)), z_front - bevel + bevel * math.sin(a)))
    else:
        layers.append((0.0, z_front))
    rings2d = [outline_of_inset(i) for i, _ in layers]
    rings = [[fr_point(fr, p, z) for p in ring] for ring, (_, z) in zip(rings2d, layers)]
    for k in range(len(rings) - 1):
        mb.quad_strip(rings[k], rings[k + 1], mat, closed=True, smooth=side_smooth or bevel > 0)
    front = rings[-1]
    mb.face(front, front_mat or mat, [front_uv(p) for p in rings2d[-1]] if front_uv else None)
    if back:
        mb.face(list(reversed(rings[0])), mat)
    return rings2d[-1]


def fr_point(fr, p2, z):
    return add(fr.o, add(mul(fr.u, p2[0]), add(mul(fr.v, p2[1]), mul(fr.n, z))))


def rrect_prism(mb, fr, cx, cy, w, h, r, z_back, z_front, mat, bevel=0.0, seg=5, **kw):
    return prism(mb, fr, lambda i: rounded_rect(w - 2 * i, h - 2 * i, max(0.0, r - i), seg, cx, cy),
                 z_back, z_front, mat, bevel=bevel, **kw)


def frame_ring(mb, fr, cx, cy, w_out, h_out, r_out, w_in, h_in, r_in, z_back, z_front, mat, seg=5, inner_depth=0.0,
               inner_mat=None, front_uv=None):
    """Rectangular frame (bezel) between an outer and an inner rounded rectangle. The inner edge returns
    towards the back by inner_depth."""
    o_f = rounded_rect(w_out, h_out, r_out, seg, cx, cy)
    i_f = rounded_rect(w_in, h_in, r_in, seg, cx, cy)
    o_front = [fr_point(fr, p, z_front) for p in o_f]
    i_front = [fr_point(fr, p, z_front) for p in i_f]
    o_back = [fr_point(fr, p, z_back) for p in o_f]
    i_back = [fr_point(fr, p, z_front - inner_depth) for p in i_f]
    uv_o = [front_uv(p) for p in o_f] if front_uv else None
    uv_i = [front_uv(p) for p in i_f] if front_uv else None
    mb.quad_strip(o_front, i_front, mat, closed=True, smooth=False, uv_a=uv_o, uv_b=uv_i)   # front face
    mb.quad_strip(o_back, o_front, mat, closed=True, smooth=False)                         # outer side
    if inner_depth > 0:
        mb.quad_strip(i_front, i_back, inner_mat or mat, closed=True, smooth=False)        # inner side


def lathe(mb, fr, profile, mat, n=24, smooth=True, cx=0.0, cy=0.0, cap_top=True, cap_bottom=False, a0=0.0,
          top_mat=None, top_uv=None):
    """Surface of revolution about the frame normal through (cx, cy): profile = [(radius, z), ...] from the
    back to the front."""
    rings = []
    for r, z in profile:
        rings.append([fr_point(fr, (cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)), z)
                      for i in range(n)])
    for k in range(len(rings) - 1):
        mb.quad_strip(rings[k], rings[k + 1], mat, closed=True, smooth=smooth)
    if cap_top and profile[-1][0] > 1e-6:
        uvs = None
        if top_uv:
            r = profile[-1][0]
            uvs = [top_uv((math.cos(a0 + 2 * math.pi * i / n), math.sin(a0 + 2 * math.pi * i / n))) for i in range(n)]
        mb.face(rings[-1], top_mat or mat, uvs)
    if cap_bottom and profile[0][0] > 1e-6:
        mb.face(list(reversed(rings[0])), mat)
    return rings


def box(mb, fr, cx, cy, w, h, z0, z1, mat, front_uv=None):
    return rrect_prism(mb, fr, cx, cy, w, h, 0.0, z0, z1, mat, seg=0, front_uv=front_uv)


def tube(mb, path, radius, mat, n=12, smooth=True, cap=True, radii=None):
    """Circular section swept along a 3D polyline (parallel transport of the section)."""
    rings = []
    prev_x = None
    for k, p in enumerate(path):
        if k == 0:
            t = norm(sub(path[1], path[0]))
        elif k == len(path) - 1:
            t = norm(sub(path[-1], path[-2]))
        else:
            t = norm(add(norm(sub(path[k], path[k - 1])), norm(sub(path[k + 1], path[k]))))
        if prev_x is None:
            ref = (0, 0, 1) if abs(t[2]) < 0.9 else (1, 0, 0)
            x = norm(cross(t, ref))
        else:
            x = norm(sub(prev_x, mul(t, dot(prev_x, t))))
        y = cross(t, x)
        prev_x = x
        r = radii[k] if radii else radius
        rings.append([add(p, add(mul(x, r * math.cos(2 * math.pi * i / n)), mul(y, r * math.sin(2 * math.pi * i / n))))
                      for i in range(n)])
    for k in range(len(rings) - 1):
        mb.quad_strip(rings[k], rings[k + 1], mat, closed=True, smooth=smooth)
    if cap:
        mb.face(list(reversed(rings[0])), mat)
        mb.face(rings[-1], mat)
    return rings
