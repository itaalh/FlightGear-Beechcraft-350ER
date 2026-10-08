"""AC3D (.ac) reader and writer for the King Air 350 cockpit tools.

Frames: the FlightGear model frame (x aft, y right, z up, metres) is used everywhere in these tools and in
Blender. An AC3D file stores (x, y, z)_ac = (x, z, -y)_model, as FlightGear loads .ac files "Y up".

read_ac() works without Blender (plain Python). The bpy helpers import_ac() / export_ac() are used from the
Blender scripts of this folder.
"""

import math
import os
import re


# ---------------------------------------------------------------------------------------------------------------
# reading

class AcObject:
    __slots__ = ("kind", "name", "texture", "texrep", "texoff", "loc", "rot", "crease", "verts", "surfs", "kids",
                 "data")

    def __init__(self, kind):
        self.kind = kind
        self.name = ""
        self.texture = None
        self.texrep = (1.0, 1.0)
        self.texoff = (0.0, 0.0)
        self.loc = (0.0, 0.0, 0.0)
        self.rot = None
        self.crease = None
        self.verts = []
        self.surfs = []      # (flags, mat, [(vidx, u, v), ...])
        self.kids = []
        self.data = None


class AcFile:
    def __init__(self):
        self.materials = []  # dicts: name, rgb, amb, emis, spec, shi, trans
        self.world = None


_MAT_RE = re.compile(r'MATERIAL\s+"([^"]*)"\s+rgb\s+(\S+)\s+(\S+)\s+(\S+)\s+amb\s+(\S+)\s+(\S+)\s+(\S+)\s+'
                     r'emis\s+(\S+)\s+(\S+)\s+(\S+)\s+spec\s+(\S+)\s+(\S+)\s+(\S+)\s+shi\s+(\S+)\s+trans\s+(\S+)')


def read_ac(path):
    with open(path, encoding="latin-1") as fh:
        lines = fh.read().splitlines()
    ac = AcFile()
    pos = 1

    def parse_object():
        nonlocal pos
        kind = lines[pos].split()[1]
        pos += 1
        obj = AcObject(kind)
        while pos < len(lines):
            line = lines[pos].strip()
            pos += 1
            if not line:
                continue
            tok = line.split(None, 1)
            key = tok[0]
            if key == "name":
                obj.name = tok[1].strip().strip('"')
            elif key == "data":
                n = int(tok[1])
                text = ""
                while len(text) < n and pos < len(lines):
                    text += lines[pos] + "\n"
                    pos += 1
                obj.data = text[:n]
            elif key == "texture":
                obj.texture = tok[1].strip().strip('"')
            elif key == "texrep":
                obj.texrep = tuple(float(v) for v in tok[1].split())
            elif key == "texoff":
                obj.texoff = tuple(float(v) for v in tok[1].split())
            elif key == "loc":
                obj.loc = tuple(float(v) for v in tok[1].split())
            elif key == "rot":
                obj.rot = tuple(float(v) for v in tok[1].split())
            elif key == "crease":
                obj.crease = float(tok[1])
            elif key == "numvert":
                n = int(tok[1])
                obj.verts = [tuple(float(v) for v in lines[pos + i].split()[:3]) for i in range(n)]
                pos += n
            elif key == "numsurf":
                n = int(tok[1])
                for _ in range(n):
                    while not lines[pos].startswith("SURF"):
                        pos += 1
                    flags = int(lines[pos].split()[1], 16)
                    pos += 1
                    mat = 0
                    refs = []
                    while True:
                        l2 = lines[pos].split()
                        pos += 1
                        if l2[0] == "mat":
                            mat = int(l2[1])
                        elif l2[0] == "refs":
                            k = int(l2[1])
                            for i in range(k):
                                p = lines[pos + i].split()
                                refs.append((int(p[0]), float(p[1]), float(p[2])))
                            pos += k
                            break
                    obj.surfs.append((flags, mat, refs))
            elif key == "kids":
                for _ in range(int(tok[1])):
                    obj.kids.append(parse_object())
                return obj
        return obj

    while pos < len(lines):
        line = lines[pos]
        if line.startswith("MATERIAL"):
            m = _MAT_RE.match(line)
            v = [float(x) for x in m.groups()[1:]]
            ac.materials.append(dict(name=m.group(1), rgb=v[0:3], amb=v[3:6], emis=v[6:9], spec=v[9:12], shi=v[12],
                                     trans=v[13]))
            pos += 1
        elif line.startswith("OBJECT"):
            ac.world = parse_object()
        else:
            pos += 1
    return ac


def ac_to_model(v):
    return (v[0], -v[2], v[1])


def model_to_ac(v):
    return (v[0], v[2], -v[1])


def walk(obj, parent_loc=(0.0, 0.0, 0.0)):
    """Yield (object, world offset in the AC frame) for every object (rot is not used by our files)."""
    loc = tuple(a + b for a, b in zip(parent_loc, obj.loc))
    yield obj, loc
    for k in obj.kids:
        yield from walk(k, loc)


# ---------------------------------------------------------------------------------------------------------------
# Blender import (reference geometry)

def import_ac(path, collection_name=None, with_textures=True):
    import bpy

    ac = read_ac(path)
    base = os.path.dirname(path)
    coll = bpy.data.collections.new(collection_name or os.path.basename(path))
    bpy.context.scene.collection.children.link(coll)

    mats = []
    for m in ac.materials:
        mat = bpy.data.materials.new(m["name"])
        mat.diffuse_color = (*m["rgb"], 1.0 - m["trans"])
        mats.append(mat)

    textured = {}

    def textured_mat(mat_index, tex):
        key = (mat_index, tex)
        if key in textured:
            return textured[key]
        src = mats[mat_index]
        mat = bpy.data.materials.new(src.name + "|" + os.path.basename(tex))
        mat.diffuse_color = src.diffuse_color
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        img_path = os.path.join(base, os.path.basename(tex))
        if os.path.exists(img_path):
            img = bpy.data.images.load(img_path, check_existing=True)
            node = nt.nodes.new("ShaderNodeTexImage")
            node.image = img
            nt.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
            if src.diffuse_color[3] < 1.0:
                nt.links.new(node.outputs["Alpha"], bsdf.inputs["Alpha"])
        textured[key] = mat
        return mat

    created = []
    for obj, loc in walk(ac.world):
        if obj.kind != "poly" or not obj.verts:
            continue
        verts = [ac_to_model((v[0] + loc[0], v[1] + loc[1], v[2] + loc[2])) for v in obj.verts]
        faces, uvs, fmats, smooth = [], [], [], []
        for flags, mat, refs in obj.surfs:
            if flags & 0xF != 0 or len(refs) < 3:
                continue
            idx = [r[0] for r in refs]
            if len(set(idx)) < 3:
                continue
            faces.append(idx)
            uvs.append([(obj.texoff[0] + r[1] * obj.texrep[0], obj.texoff[1] + r[2] * obj.texrep[1]) for r in refs])
            fmats.append(mat)
            smooth.append(bool(flags & 0x10))
        if not faces:
            continue
        me = bpy.data.meshes.new(obj.name or "ac")
        try:
            me.from_pydata(verts, [], faces)
        except Exception:
            continue
        me.validate(clean_customdata=False)
        uvl = me.uv_layers.new(name="UVMap")
        slot_of = {}
        for fi, poly in enumerate(me.polygons):
            if fi >= len(fmats):
                break
            m = fmats[fi]
            key = m
            if key not in slot_of:
                slot_of[key] = len(me.materials)
                if with_textures and obj.texture:
                    me.materials.append(textured_mat(m, obj.texture))
                else:
                    me.materials.append(mats[m] if m < len(mats) else None)
            poly.material_index = slot_of[key]
            poly.use_smooth = smooth[fi]
            for k, li in enumerate(poly.loop_indices):
                if k < len(uvs[fi]):
                    uvl.data[li].uv = uvs[fi][k]
        ob = bpy.data.objects.new(obj.name or "ac", me)
        coll.objects.link(ob)
        created.append(ob)
    return coll, created


# ---------------------------------------------------------------------------------------------------------------
# Blender export

def _fmt(x):
    s = "%.5f" % x
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def export_ac(path, objects, texture_of=None, crease=45.0, material_filter=None):
    """Write the given Blender objects (modifiers applied, world coordinates) as one flat AC3D file.

    texture_of(obj) returns the texture path written in the file (relative to the .ac) or None.
    Materials are exported from each Blender material's viewport colour (diffuse_color), plus the custom
    properties ac_emis (rgb), ac_spec (rgb), ac_shi (int) and ac_trans (float) when present.
    """
    import bpy
    import bmesh

    depsgraph = bpy.context.evaluated_depsgraph_get()
    mat_index = {}
    mat_lines = []

    def mat_id(mat):
        key = mat.name if mat else "__none__"
        if key in mat_index:
            return mat_index[key]
        if mat is None:
            rgb, emis, spec, shi, trans = (0.8, 0.8, 0.8), (0, 0, 0), (0.2, 0.2, 0.2), 16, 0.0
            name = "none"
        else:
            rgb = tuple(mat.diffuse_color[:3])
            emis = tuple(mat.get("ac_emis", (0.0, 0.0, 0.0)))
            spec = tuple(mat.get("ac_spec", (0.25, 0.25, 0.25)))
            shi = int(mat.get("ac_shi", 24))
            trans = float(mat.get("ac_trans", 1.0 - mat.diffuse_color[3]))
            name = mat.name
        mat_index[key] = len(mat_lines)
        mat_lines.append('MATERIAL "%s" rgb %s %s %s  amb %s %s %s  emis %s %s %s  spec %s %s %s  shi %d  trans %s' % (
            name, *(_fmt(c) for c in rgb), *(_fmt(c) for c in rgb), *(_fmt(c) for c in emis),
            *(_fmt(c) for c in spec), shi, _fmt(trans)))
        return mat_index[key]

    blocks = []
    for ob in objects:
        if ob.type != "MESH":
            continue
        ev = ob.evaluated_get(depsgraph)
        me = ev.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(ob.matrix_world)
        # AC3D surfaces are drawn as polygons: keep quads/n-gons only when planar and convex, else triangulate
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4 or not _planar_convex(f)])
        uv_layer = bm.loops.layers.uv.active
        tex = texture_of(ob) if texture_of else None
        out = ['OBJECT poly', 'name "%s"' % ob.name]
        if tex:
            out.append('texture "%s"' % tex)
        out.append("crease %s" % _fmt(ob.get("ac_crease", crease)))
        verts = list(bm.verts)
        vi = {v: i for i, v in enumerate(verts)}
        out.append("numvert %d" % len(verts))
        for v in verts:
            a = model_to_ac(v.co)
            out.append("%s %s %s" % (_fmt(a[0]), _fmt(a[1]), _fmt(a[2])))
        faces = list(bm.faces)
        out.append("numsurf %d" % len(faces))
        two_sided = bool(ob.get("ac_twosided", False))
        for f in faces:
            mat = me.materials[f.material_index] if f.material_index < len(me.materials) else None
            flags = (0x10 if f.smooth else 0) | (0x20 if two_sided else 0)
            out.append("SURF 0x%X" % flags)
            out.append("mat %d" % mat_id(mat))
            out.append("refs %d" % len(f.loops))
            for loop in f.loops:
                u, v = (loop[uv_layer].uv if uv_layer else (0.0, 0.0))
                out.append("%d %s %s" % (vi[loop.vert], _fmt(u), _fmt(v)))
        out.append("kids 0")
        blocks.append("\n".join(out))
        bm.free()
        ev.to_mesh_clear()

    with open(path, "w", encoding="latin-1", newline="\n") as fh:
        fh.write("AC3Db\n")
        fh.write("\n".join(mat_lines) + "\n")
        fh.write("OBJECT world\nkids %d\n" % len(blocks))
        fh.write("\n".join(blocks) + "\n")
    return len(blocks)


def _planar_convex(f, tol=1e-4):
    if len(f.verts) == 3:
        return True
    n = f.normal
    if n.length < 1e-9:
        return False
    p0 = f.verts[0].co
    for v in f.verts[1:]:
        if abs((v.co - p0).dot(n)) > tol:
            return False
    # convexity: all consecutive cross products point along the normal
    pts = [v.co for v in f.verts]
    k = len(pts)
    for i in range(k):
        a, b, c = pts[i], pts[(i + 1) % k], pts[(i + 2) % k]
        if (b - a).cross(c - b).dot(n) < -1e-9:
            return False
    return True


if __name__ == "__main__":
    import sys
    ac = read_ac(sys.argv[1])
    for o, loc in walk(ac.world):
        if o.verts:
            xs = [ac_to_model((v[0] + loc[0], v[1] + loc[1], v[2] + loc[2])) for v in o.verts]
            lo = [min(p[i] for p in xs) for i in range(3)]
            hi = [max(p[i] for p in xs) for i in range(3)]
            print("%-28s %6d v %6d f  x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f  %s" % (
                o.name, len(o.verts), len(o.surfs), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
                os.path.basename(o.texture or "")))
