"""Blender script: rebuilds the PT6A-60A engine air inlets, exhaust stacks and lower-cowl vents of the King Air 350
nacelles, closes the missing leading edge of the inboard wing and completes the black de-icing boots.

    blender --background --python Tools/nacelle/nacelle_details.py -- --out /tmp/nacelle.ac
    python Tools/pod/splice_ac.py /tmp/nacelle.ac --set-mat Exhaust=2 --remove DeicebootsInner --remove PropCone
    # merges Exhaust (white material instead of the original very dark one), EngineInlets, DeicebootsWings,
    # FrontCowls, FrontEngineCowls, Wings, PropConeLeft, PropConeRight (DeicebootsInner: object of an earlier
    # version of this script;
    # PropCone: stray disc of the original model, hidden until now by the old exhaust stack)

Can also be pasted in Blender's text editor or sent through Blender's MCP server (globals PARAMS / OUT as in
Tools/pod/alsr_pod.py). Models/KingAir.ac is imported first if the scene has no "Fuselage" object; the objects the
script edits are taken from original_objects.ac (their geometry before the script) on every run, so that the result
does not depend on what the model already contains.

References: photographs of F-WTAO, F-RACH and F-RACG, three-view drawing of the Super King Air 350, Twin & Turbine /
King Air Magazine descriptions (inlet lip heated by exhaust gas).
- Inlet: below the ring band round the spinner, the front of each original cowl (FrontCowls) was a rounded frame
  around a D-shaped opening (0.54 x 0.25 m) with a tunnel behind it: the inside of the nacelle showed through. The
  frame and the tunnel are removed and replaced, in FrontCowls, by a chin carrying the real inlet (EngineInlets): a
  stadium shaped mouth 0.34 x 0.10 m with a polished metal lip (outer 0.43 x 0.19 m) standing forward like a snout,
  and a short dark duct. The chin is made of curves from the outer edge of the lip (leaving it aft) to the rear edge
  of the band, and to the front edge of FrontEngineCowls, where they arrive along the cowl (no crease). Beside the
  band, the narrow parts between it and the cowl edge are filled flat, like the flange above them.
- Exhaust (Exhaust, replaced): one short elbow each side of each nacelle, at the height of the spinner axis (front,
  rear and three-quarter photos): it rises from the side of the cowl just behind the front ring through a fillet
  collar (tangent to the cowl and to the tube), outwards and 10 deg up, bends by 64 deg and ends with a short
  straight part whose axis points aft, 25 deg outwards and 6 deg up; the outlet stands 0.23 m beyond the cowl. Round section of 0.14 m
  flaring to 0.18 x 0.17 m at the outlet, cut obliquely so that it faces mostly aft. A dark recess under the stack.
  The raised socket of the original stacks is removed from FrontEngineCowls and the hole is filled in the same
  object (fine constrained Delaunay mesh, every vertex on the cowl surface, UVs of the surrounding cowl). Stacks and lip are mapped on a mid grey of the spinner area, the same in every livery.
- Lower vents (in EngineInlets): two dark openings under each nacelle behind the front ring.
- Spinners (PropConeLeft, PropConeRight): the original spinners had three blade openings for four blades; they are
  rebuilt closed (surface of revolution about the spin axis, profile of the original), mapped on a clean sector of
  their front-projected texture so that the painted openings do not show.
- Wings: between the fuselage and the nacelles (|y| 0.83-1.88) the original wing has no leading-edge faces (open
  nose, the leading edge seemed set back by 11 cm). The six missing faces of each side are rebuilt between the two
  existing stations (straight leading edge, as on the three-view), with the UVs of their neighbours.
- De-icing boots (DeicebootsWings, rebuilt): black strips wrapping the leading edge from the fuselage to the nacelle
  and from the nacelle to the wing tip, mapped on the black boot texels of the body texture. From the end of the
  nacelle fillet to the tip the wing has no nose (its skins stop about 15 cm behind the leading edge): there the
  strip has a D section, along both skins and round the nose through the leading-edge line of the original boot. The original
  boots had two short white pieces inboard, nothing between the nacelle and |y| 3.97 and, outboard, a coarse shell
  of long triangles that did not follow the curved leading edge near the nacelle (a piece hung below the wing).
"""
import bpy, bmesh, math, os, sys, tempfile
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
from mathutils.geometry import delaunay_2d_cdt

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MODELS = os.path.join(ROOT, 'Models')
if not os.path.exists(os.path.join(MODELS, 'KingAir.ac')):
    for p in (os.getcwd(), os.path.dirname(bpy.data.filepath or '')):
        if os.path.exists(os.path.join(p, 'Models', 'KingAir.ac')):
            ROOT = p; MODELS = os.path.join(ROOT, 'Models'); break

P = dict(
    engines_y=(-2.749, 2.796),           # nacelle axes = propeller spin centres of Models/KingAir.xml (FG y, right positive)
    axis_z=-0.35,                        # nacelle axis height
    wall_y=0.376,                        # half-width of the nacelle at the wing
    # inlet: plane of the lip, mouth centre height, half axes, exponent, lip tube radius, duct depth
    inlet_x=-5.26, inlet_z=-0.624, inlet_a=0.17, inlet_b=0.05, inlet_exp=3.2, lip_r=0.022, duct_len=0.12,
    # chin (FrontCowls): the faces below the spinner ring band and below chin_split are replaced; ring stations from
    # the lip (0) to the boundary (1); handle length of the profile curves (fraction of the lip-boundary distance)
    chin_split=-0.25, chin_rings=(0.0, 0.05, 0.12, 0.21, 0.32, 0.45, 0.6, 0.78, 1.0), chin_handle=0.38,
    # beside the ring band, from chin_split down to chin_horn, the hole is filled flat like the flange above it; the
    # chin starts at the lower edge of these parts (divided in chin_horn_div)
    chin_horn=-0.43, chin_horn_div=4,
    # exhaust stacks: root station and height on the side wall, root radius, outlet half axes (vertical, lateral),
    # flattening of the cowl side at the outlet, width of the fillet collar round the root on the cowl, elevation of
    # the exit out of the cowl, straight part before the bend (height of the collar), bend radius, direction of the
    # outlet axis (degrees outwards and upwards from straight aft), straight part after the bend, oblique cut angle
    # (front, rear and three-quarter photos: short elbow out of the side of the cowl at the height of the spinner
    # axis, outwards and slightly up, outlet facing aft and outwards, about 0.23 m beyond the cowl)
    stack_x=-5.02, stack_z=-0.16, stack_r0=0.070, stack_end=(0.088, 0.084), stack_flat=1.0, stack_collar=0.025,
    stack_elev_deg=10.0, stack_out=0.035, bend_r=0.10, stack_dir=(25.0, 6.0), stack_run=0.065, cut_deg=20.0,
    stack_segments=24, bracket_dx=(0.06, 0.24), bracket_dz=(-0.17, -0.095),
    patch_x=(-5.14, -4.50), patch_z=(-0.365, -0.005),
    cowl_hole=((-5.13, -4.75), (-0.355, -0.012), (0.25, 0.45)),   # FrontEngineCowls faces removed (x, z, |dy|)
    lift=0.004, decal_lift=0.0015, fill_step=0.025,
    vents=((-4.97, -4.72), (0.045, 0.16)),         # x range, |dy| range of each lower vent (two per nacelle)
    # wing nose rebuilt between these stations; boots: inboard span, outboard overlap with the original boots,
    # fan centre behind the leading edge, number of fan rays, lift off the skin, station spacing
    wing_gap=(0.80, 1.95), boots_inner=(0.80, 2.33),
    boot_depth=0.16, boot_rays=15, boot_lift=0.012, boot_dy=0.04, boot_dy_outer=(0.03, 0.6, 0.10),
    # outer wing (from the end of the nacelle fillet to the tip): the wing has no nose, the original boot shell formed
    # it; leading-edge line of that shell per side: (|y|, x, z) at its inboard end and at the tip
    outer_le={-1: ((3.966, -2.779, -0.331), (8.588, -2.609, 0.149)), 1: ((3.987, -2.747, -0.331), (8.608, -2.541, 0.149))},
    outer_extra=0.02,                    # how far the boot runs onto the skins behind their front edge
    outer_tip=8.76,                      # the strip continues past the original boot end while the skins are found
    # UVs: mid grey of the spinner area (127 in every livery) for the lip and the stacks; dark grey of the boot strip
    # for gaps, duct and vents (dark in every livery but LN-LTI); boot black
    uv_metal=(0.6699, 0.2402), uv_dark=(0.16, 0.033), uv_boot=((0.556, 0.600), (0.0225, 0.0255)),
    # spinners: spin centres (y, z) of Models/KingAir.xml, segments round, profile step, half width of the clean
    # sector of the spinner texture the closed spinner is mapped on
    spinners={'PropConeLeft': (-2.7494, -0.1808), 'PropConeRight': (2.7957, -0.1808)},
    spinner_segments=48, spinner_step=0.012, spinner_sector_deg=12.0,
)
if 'PARAMS' in globals():
    P.update(globals()['PARAMS'])
OUT = globals().get('OUT') or os.path.join(tempfile.gettempdir(), 'nacelle.ac')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--out' in argv:
    OUT = argv[argv.index('--out') + 1]

AC = os.path.join(MODELS, 'KingAir.ac')
# the objects this script edits are always taken from their original geometry (original_objects.ac, extracted from
# Models/KingAir.ac before the script was first applied): every run starts from the same geometry, also on a model
# that already went through it
ORIG = os.path.join(HERE, 'original_objects.ac')
EDITED = ('FrontCowls', 'FrontEngineCowls', 'DeicebootsWings', 'Wings', 'PropConeLeft', 'PropConeRight')
if 'Fuselage' not in bpy.data.objects:
    bpy.ops.import_scene.import_ac3d(filepath=AC, axis_forward='-Z', axis_up='Y', collection_name='KingAir')
before = set(bpy.data.objects)
bpy.ops.import_scene.import_ac3d(filepath=ORIG, axis_forward='-Z', axis_up='Y', collection_name='tmp_reload')
target = bpy.data.objects['Fuselage'].users_collection[0]
for o in [o for o in bpy.data.objects if o not in before]:
    base = o.name[:-4] if o.name[-4:-3] == '.' and o.name[-3:].isdigit() else o.name
    if base in EDITED:
        old = bpy.data.objects.get(base)
        if old and old is not o:
            me = old.data; bpy.data.objects.remove(old, do_unlink=True); bpy.data.meshes.remove(me)
        o.name = base; o.data.name = base
        for c in list(o.users_collection): c.objects.unlink(o)
        target.objects.link(o)
    else:
        me = o.data; bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0: bpy.data.meshes.remove(me)
tmp = bpy.data.collections.get('tmp_reload')
if tmp: bpy.data.collections.remove(tmp)
col = bpy.data.collections.get('ALSR') or bpy.data.collections.new('ALSR')
if col.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(col)
mat = bpy.data.materials.get('Material6.001') or bpy.data.objects['Fuselage'].data.materials[0]


def world_bmesh(names):
    bmx = bmesh.new()
    for nm in names:
        o = bpy.data.objects[nm]; tmp = bmesh.new(); tmp.from_mesh(o.data); tmp.transform(o.matrix_world)
        me = bpy.data.meshes.new('tmp_bvh'); tmp.to_mesh(me); bmx.from_mesh(me); bpy.data.meshes.remove(me); tmp.free()
    bmx.faces.ensure_lookup_table()
    return bmx


def bvh_of(names):
    return BVHTree.FromBMesh(world_bmesh(names))


def uv_sampler(names):
    """Function giving the UV of the nearest point of the named objects (to borrow the livery colour there)."""
    bmx = world_bmesh(names); uvl = bmx.loops.layers.uv.active; tree = BVHTree.FromBMesh(bmx)

    def f(p):
        loc, nrm, idx, dist = tree.find_nearest(Vector(p))
        face = bmx.faces[idx]; w = poly_3d_calc([v.co for v in face.verts], loc)
        u = sum(wi * l[uvl].uv.x for wi, l in zip(w, face.loops)); v = sum(wi * l[uvl].uv.y for wi, l in zip(w, face.loops))
        return (u, v)
    return f


def cast(bvh, origin, direction, maxd=3.0):
    hit = bvh.ray_cast(Vector(origin), Vector(direction).normalized(), maxd)
    return (hit[0], hit[1]) if hit[0] is not None else (None, None)


def remove_obj(nm):
    o = bpy.data.objects.get(nm)
    if o:
        me = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me)


def finish(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    remove_obj(name)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.data.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    bmx = bmesh.new(); bmx.from_mesh(me)
    for e in bmx.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(50):
            e.smooth = False
    bmx.to_mesh(me); bmx.free(); me.update()
    return o


def superellipse(a, b, th, e):
    c, s = math.cos(th), math.sin(th)
    return a * math.copysign(abs(c) ** (2 / e), c), b * math.copysign(abs(s) ** (2 / e), s)


class SideSurface:
    """Height field y(x, z) of one side of a nacelle over the patch area, sampled by rays cast towards the nacelle
    axis; where the rays go through the removed socket, filled by interpolation from the hits around it."""
    NX, NZ = 33, 25

    def __init__(self, tree, ye, out):
        (x0, x1), (z0, z1) = P['patch_x'], P['patch_z']
        self.ye, self.out = ye, out
        self.xs = [x0 + (x1 - x0) * i / (self.NX - 1) for i in range(self.NX)]
        self.zs = [z0 + (z1 - z0) * j / (self.NZ - 1) for j in range(self.NZ)]
        Y = [[None] * self.NX for _ in self.zs]
        for j, z in enumerate(self.zs):
            for i, x in enumerate(self.xs):
                q, _ = cast(tree, (x, ye + out * 1.2, z), (0, -out, 0), 1.2)
                if q is not None and out * (q.y - ye) > 0.2:
                    Y[j][i] = q.y
        for j in range(self.NZ):                         # fill along x, then along z
            hits = [i for i in range(self.NX) if Y[j][i] is not None]
            for i in range(self.NX):
                if Y[j][i] is None and len(hits) >= 2 and hits[0] < i < hits[-1]:
                    a = max(h for h in hits if h < i); b = min(h for h in hits if h > i)
                    Y[j][i] = Y[j][a] + (Y[j][b] - Y[j][a]) * (i - a) / (b - a)
        for i in range(self.NX):
            hits = [j for j in range(self.NZ) if Y[j][i] is not None]
            for j in range(self.NZ):
                if Y[j][i] is None and hits:
                    lo = [h for h in hits if h < j]; hi = [h for h in hits if h > j]
                    if lo and hi:
                        a, b = lo[-1], hi[0]; Y[j][i] = Y[a][i] + (Y[b][i] - Y[a][i]) * (j - a) / (b - a)
                    else:
                        Y[j][i] = Y[(lo or hi)[-1 if lo else 0]][i]
        self.Y = Y

    def y(self, x, z):
        fx = (x - self.xs[0]) / (self.xs[-1] - self.xs[0]) * (self.NX - 1)
        fz = (z - self.zs[0]) / (self.zs[-1] - self.zs[0]) * (self.NZ - 1)
        i = min(max(int(fx), 0), self.NX - 2); j = min(max(int(fz), 0), self.NZ - 2); u = fx - i; v = fz - j
        Y = self.Y
        return ((1 - u) * (1 - v) * Y[j][i] + u * (1 - v) * Y[j][i + 1] + (1 - u) * v * Y[j + 1][i] + u * v * Y[j + 1][i + 1])

    def point(self, x, z, lift=0.0):
        h = 0.005
        yx = (self.y(x + h, z) - self.y(x - h, z)) / (2 * h); yz = (self.y(x, z + h) - self.y(x, z - h)) / (2 * h)
        n = Vector((-self.out * yx, self.out, -self.out * yz)).normalized()
        return Vector((x, self.y(x, z), z)) + n * lift, n


# ================================================================ wings: rebuild the missing leading edge
ow = bpy.data.objects['Wings']; mww = ow.matrix_world
bmw = bmesh.new(); bmw.from_mesh(ow.data); uvw = bmw.loops.layers.uv.active
Wp = lambda v: mww @ v.co
g0, g1 = P['wing_gap']
added = 0
for side in (-1, 1):
    cand = [v for v in bmw.verts if g0 < side * Wp(v).y < g1 and Wp(v).x < -2.79
            and any(len(e.link_faces) == 1 for e in v.link_edges)]
    groups = {}
    for v in cand:
        groups.setdefault(round(abs(Wp(v).y) * 20) / 20, []).append(v)
    st = [groups[k] for k in sorted(groups)]
    if len(st) != 2 or len(st[0]) != len(st[1]):
        print('wing nose: unexpected boundary on side %+d: %s' % (side, [len(s) for s in st])); continue
    loops = []
    for vs in st:
        c = Vector((min(Wp(v).x for v in vs) + 0.25, Wp(vs[0]).y, sum(Wp(v).z for v in vs) / len(vs)))
        vs.sort(key=lambda v: math.atan2(Wp(v).z - c.z, -(Wp(v).x - c.x)))   # lower aft -> nose -> upper aft
        loops.append((vs, c))
    (a, ca), (b, cb) = loops
    n = len(a)
    nose_k = min(range(n), key=lambda k: Wp(a[k]).x)     # foremost vertex: lower faces before it, boot faces after
    for k in range(n - 1):
        try:
            f = bmw.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
        except ValueError:
            continue
        lower = k < nose_k
        for l in f.loops:
            uvs = [ll[uvw].uv.copy() for ll in l.vert.link_loops if ll.face is not f]
            pick = [uv for uv in uvs if (uv.y > 0.3) == lower] or uvs
            l[uvw].uv = pick[0]
        cen = (Wp(a[k]) + Wp(b[k + 1])) / 2; inside = (ca + cb) / 2
        nrm = (mww.to_3x3() @ f.normal)
        if nrm.dot(cen - inside) < 0:
            f.normal_flip()
        f.smooth = True
        added += 1
bmw.to_mesh(ow.data); bmw.free(); ow.data.update()
print('Wings: %d leading-edge faces rebuilt' % added)

skin = bvh_of(('FrontCowls', 'FrontEngineCowls', 'MidEngineCowls', 'TopEngineCowl', 'LowerEngCowls', 'EngCowlStrips'))
wing_only = bvh_of(('Wings',))
wing_root = bvh_of(('Wings', 'WngCowl'))
front_uv = uv_sampler(('FrontCowls',))

# ================================================================ exhaust stacks
(hx0, hx1), (hz0, hz1), (hd0, hd1) = P['cowl_hole']
ofc = bpy.data.objects['FrontEngineCowls']; mwc = ofc.matrix_world
bmc = bmesh.new(); bmc.from_mesh(ofc.data)
hole = [f for f in bmc.faces
        if hx0 <= (mwc @ f.calc_center_median()).x <= hx1 and hz0 <= (mwc @ f.calc_center_median()).z <= hz1
        and any(hd0 < abs((mwc @ f.calc_center_median()).y - ye) < hd1 for ye in P['engines_y'])]
bmesh.ops.delete(bmc, geom=hole, context='FACES'); bmc.to_mesh(ofc.data); bmc.free(); ofc.data.update()
print('FrontEngineCowls: %d socket faces removed' % len(hole))
cowl_uv = uv_sampler(('FrontEngineCowls', 'MidEngineCowls'))
side_tree = bvh_of(('FrontCowls', 'FrontEngineCowls', 'MidEngineCowls', 'TopEngineCowl', 'EngCowlStrips'))
surfs = {(ye, out): SideSurface(side_tree, ye, out) for ye in P['engines_y'] for out in (-1, 1)}

# fill the socket holes of FrontEngineCowls in the object itself. Each hole is open on its front side (it reaches
# the front edge of the object, against the FrontCowls ring): walk the boundary chain of the hole, close it along the
# front edge with vertices on the cowl surface, then mesh the hole finely (constrained Delaunay triangulation, seen
# from the side, of its outline and of a grid of points fill_step apart) with every new vertex on the cowl surface;
# UVs of the surrounding cowl
bmc = bmesh.new(); bmc.from_mesh(ofc.data); uvc = bmc.loops.layers.uv.active
W = lambda v: mwc @ v.co
inv = mwc.inverted()
filled = 0
for (ye, out), surf in surfs.items():
    def in_box(q):
        return (hx0 - 0.10 <= q.x <= hx1 + 0.05 and hz0 - 0.10 <= q.z <= hz1 + 0.10
                and hd0 - 0.05 < out * (q.y - ye) < hd1)
    sel = [e for e in bmc.edges if len(e.link_faces) == 1 and all(in_box(W(v)) for v in e.verts)]
    if len(sel) < 3:
        continue
    front_x = min(W(v).x for e in sel for v in e.verts)
    sel = [e for e in sel if not all(W(v).x < front_x + 0.0015 for v in e.verts)]   # drop the object's front edge
    adj = {}
    for e in sel:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    ends = [v for v, nb in adj.items() if len(nb) == 1]
    start = ends[0] if ends else next(iter(adj))
    chain = [start]; prev = None
    while True:
        nxt = [v for v in adj[chain[-1]] if v is not prev and v is not chain[0]]
        if not nxt:
            break
        prev = chain[-1]; chain.append(nxt[0])
        if len(chain) > len(adj):
            break
    if ends:   # close along the front edge with vertices on the cowl surface
        pa, pb = W(chain[-1]), W(chain[0])
        k = max(2, int((pa - pb).length / 0.04))
        for i in range(1, k):
            q = pa.lerp(pb, i / k); q2, _ = surf.point(q.x, q.z)
            chain.append(bmc.verts.new(inv @ Vector((q.x, q2.y, q.z))))
    outline = [(W(v).x, W(v).z) for v in chain]; n = len(outline)

    def inside(px, pz):
        c = False
        for i in range(n):
            (x1, z1), (x2, z2) = outline[i], outline[(i + 1) % n]
            if (z1 > pz) != (z2 > pz) and px < x1 + (pz - z1) * (x2 - x1) / (z2 - z1):
                c = not c
        return c

    def dist_outline(px, pz):
        best = 1e9
        for i in range(n):
            (x1, z1), (x2, z2) = outline[i], outline[(i + 1) % n]
            dx, dz = x2 - x1, z2 - z1; L2 = dx * dx + dz * dz or 1e-12
            t = min(max(((px - x1) * dx + (pz - z1) * dz) / L2, 0.0), 1.0)
            best = min(best, math.hypot(px - x1 - t * dx, pz - z1 - t * dz))
        return best
    st = P['fill_step']; xs_o = [q[0] for q in outline]; zs_o = [q[1] for q in outline]
    pts2 = list(outline)
    for i in range(int((max(xs_o) - min(xs_o)) / st) + 1):
        for j in range(int((max(zs_o) - min(zs_o)) / st) + 1):
            px, pz = min(xs_o) + st * (i + 0.5), min(zs_o) + st * (j + 0.5)
            if inside(px, pz) and dist_outline(px, pz) > 0.6 * st:
                pts2.append((px, pz))
    co_out, _, faces_out, orig_v, _, _ = delaunay_2d_cdt([Vector(q) for q in pts2], [], [list(range(n))], 1, 1e-6)
    vmap = []
    for k, c in enumerate(co_out):
        src = [i for i in orig_v[k] if i < n]
        if src:
            vmap.append(chain[src[0]])
        else:
            q2, _ = surf.point(c.x, c.y)
            vmap.append(bmc.verts.new(inv @ q2))
    for fo in faces_out:
        try:
            f = bmc.faces.new([vmap[i] for i in fo])
        except ValueError:
            continue
        f.normal_update()
        if (mwc.to_3x3() @ f.normal).y * out < 0:
            f.normal_flip()
        for l in f.loops:
            l[uvc].uv = cowl_uv(W(l.vert))
        f.smooth = True
        filled += 1
bmc.normal_update(); bmc.to_mesh(ofc.data); bmc.free(); ofc.data.update()
print('FrontEngineCowls: %d faces fill the socket holes' % filled)

bm = bmesh.new(); uv_lay = bm.loops.layers.uv.new('UVMap')
N = P['stack_segments']


def set_uv(f, uv):
    for l in f.loops:
        l[uv_lay].uv = uv


def stack(points, sizes, foot):
    """Sweep a section along points; sizes[i] = (vertical half axis, lateral half axis, lateral half axis on the cowl
    side). The section frame is carried along the path without twist, starting from the forward direction; nn ends
    pointing away from the cowl after the bend. foot(x, z) -> (point, normal) of the cowl: a fillet collar joins the
    first section to the cowl surface, tangent to both."""
    n_pts = len(points); rings = []; frames = []
    nn = None; sgn = 1.0
    for i, c in enumerate(points):
        t = (points[min(i + 1, n_pts - 1)] - points[max(i - 1, 0)]).normalized()
        if nn is None:
            nn = Vector((-1.0, 0.0, 0.0)); nn = (nn - nn.dot(t) * t).normalized()
            sgn = 1.0 if t.cross(nn).z >= 0 else -1.0
        else:
            nn = (nn - nn.dot(t) * t).normalized()
        bb = t.cross(nn) * sgn
        frames.append((t, nn, bb))
        av, al, alc = sizes[i]
        ring = []
        for k in range(N):
            th = 2 * math.pi * k / N
            cn = math.cos(th) * (alc if math.cos(th) < 0 else al)
            p = c + nn * cn + bb * (av * math.sin(th))
            if i == n_pts - 1:   # oblique outlet: the outer / upper side reaches further aft
                p = p + t * ((math.cos(th) * 0.6 + math.sin(th) * 0.8) * av * math.tan(math.radians(P['cut_deg'])))
            ring.append(bm.verts.new(p))
        rings.append(ring)
    # collar: for each vertex of the first section, a curve from the cowl (a little outside the section, leaving the
    # cowl along its surface) up to the vertex (arriving along the tube)
    t0 = frames[0][0]; c0 = points[0]; wcol = P['stack_collar']; collar = []
    for fr in (0.0, 0.12, 0.3, 0.55, 0.8):
        collar.append([])
    for k, v in enumerate(rings[0]):
        pk = v.co.copy(); radial = pk - c0; radial = (radial - radial.dot(t0) * t0).normalized()
        q = pk + radial * wcol; F, Fn = foot(q.x, q.z); F = F + Fn * 0.0015
        h = max((pk - F).dot(t0), 0.01)
        tang = -radial; tang = (tang - tang.dot(Fn) * Fn).normalized()
        q1 = F + tang * (wcol * 0.6); q2 = pk - t0 * (h * 0.6)
        for j, u in enumerate((0.0, 0.12, 0.3, 0.55, 0.8)):
            w1 = 1 - u
            collar[j].append(bm.verts.new(F * w1 ** 3 + q1 * (3 * w1 * w1 * u) + q2 * (3 * w1 * u * u) + pk * u ** 3))
    rings = collar + rings
    for i in range(len(rings) - 1):
        for k in range(N):
            set_uv(bm.faces.new((rings[i][k], rings[i][(k + 1) % N], rings[i + 1][(k + 1) % N], rings[i + 1][k])), P['uv_metal'])
    last = rings[-1]; cen = sum((v.co for v in last), Vector()) / N; tdir = (points[-1] - points[-2]).normalized()
    inner = [bm.verts.new(cen + (v.co - cen) * 0.84 - tdir * 0.035) for v in last]
    for k in range(N):
        set_uv(bm.faces.new((last[k], inner[k], inner[(k + 1) % N], last[(k + 1) % N])), P['uv_dark'])
    set_uv(bm.faces.new(list(reversed(inner))), P['uv_dark'])


def stack_size(g):
    """Section at growth g (0 at the root, 1 at the outlet)."""
    (ev, el), r0 = P['stack_end'], P['stack_r0']
    av = r0 + (ev - r0) * g; al = r0 + (el - r0) * g
    return av, al, al * (1 - (1 - P['stack_flat']) * g)


def wall_grid(surf, xs, zs, lift, uv):
    """Quad grid on the nacelle side over xs x zs; uv: fixed (u, v) or a function of the point."""
    rows = []
    for z in zs:
        rows.append([bm.verts.new(surf.point(x, z, lift)[0]) for x in xs])
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            for l in f.loops:
                l[uv_lay].uv = uv(l.vert.co) if callable(uv) else uv


for ye in P['engines_y']:
    for out in (-1, 1):
        surf = surfs[(ye, out)]
        # stack: out of the side of the cowl (d: outwards, slightly up), circular bend of radius R from d to the outlet
        # axis f (aft, turned outwards and up), short straight part along f
        el = math.radians(P['stack_elev_deg']); ao, au = (math.radians(v) for v in P['stack_dir'])
        d = Vector((0.0, out * math.cos(el), math.sin(el)))
        f = Vector((math.cos(au) * math.cos(ao), out * math.cos(au) * math.sin(ao), math.sin(au))).normalized()
        R = P['bend_r']; phi = math.acos(max(-1.0, min(1.0, d.dot(f)))); nb = (f - d * d.dot(f)).normalized()
        S, wn = surf.point(P['stack_x'], P['stack_z'])
        s_out = P['stack_out']; B0 = S + d * s_out        # first section; the collar joins it to the cowl
        pts = [B0]
        for i in range(1, 9):                            # circular bend from d to f
            th = phi * i / 8
            pts.append(B0 + d * (R * math.sin(th)) + nb * (R * (1 - math.cos(th))))
        E = pts[-1]; L = P['stack_run']
        pts += [E + f * L * k for k in (0.5, 1.0)]
        # sizes: growth from the root to the outlet
        cum = [0.0]
        for i in range(1, len(pts)):
            cum.append(cum[-1] + (pts[i] - pts[i - 1]).length)
        sizes = [stack_size((c_ / cum[-1]) ** 1.8) for c_ in cum]
        stack(pts, sizes, lambda x, z, surf=surf: surf.point(x, z))
        # dark recess under the stack
        bx0, bx1 = P['bracket_dx']; bz0, bz1 = P['bracket_dz']
        wall_grid(surf, [P['stack_x'] + bx0, P['stack_x'] + bx1],
                  [P['stack_z'] + bz0 + (bz1 - bz0) * j / 3 for j in range(4)], P['decal_lift'], P['uv_dark'])
        O = pts[-1]
        print('stack %+.3f %+d: bend %.0f deg, outlet x %.3f, %.3f m beyond the cowl, %.3f m higher than the root'
              % (ye, out, math.degrees(phi), O.x, out * (O.y - S.y) + P['stack_end'][1], O.z - S.z))
exh = finish(bm, 'Exhaust')

# ================================================================ inlets: chin, lip, duct; lower vents
# Below its spinner ring band, the front of each original cowl (FrontCowls) was a rounded frame around a D-shaped
# opening with a tunnel behind it (the inside of the nacelle showed through). Those faces are removed and the hole is
# filled, in FrontCowls itself, by a chin that carries the inlet: profile curves from the outer edge of the lip (leaving
# it aft, along the lip) to the hole boundary: the rear edge of the ring band above the lip, the cut of the side flanges
# and the front edge of FrontEngineCowls, where they arrive along the cowl (no crease). The lip and the duct are in
# EngineInlets.
bm = bmesh.new(); uv_lay = bm.loops.layers.uv.new('UVMap')
a0, b0, e0, lr = P['inlet_a'], P['inlet_b'], P['inlet_exp'], P['lip_r']; x0 = P['inlet_x']
ofr = bpy.data.objects['FrontCowls']; mwf = ofr.matrix_world
bmf = bmesh.new(); bmf.from_mesh(ofr.data); bmf.transform(mwf); uvf = bmf.loops.layers.uv.active
fec = world_bmesh(('FrontEngineCowls',))
zs = P['chin_split']; X = Vector((1.0, 0.0, 0.0))
chin_faces = 0


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * (u ** 3) + p1 * (3 * u * u * t) + p2 * (3 * u * t * t) + p3 * (t ** 3)


def lip_point(th, a, b):
    y, z = superellipse(a, b, th, e0)
    return y, z


for ye in P['engines_y']:
    zc = P['inlet_z']
    # remove the frame and the tunnel: faces of this side that do not touch the front circle of the ring band,
    # below chin_split (the side flanges are cut there)
    side = [f for f in bmf.faces if abs(f.calc_center_median().y - ye) < 0.6]
    sv = set(v for f in side for v in f.verts)
    xmin = min(v.co.x for v in sv)
    ring_front = set(v for v in sv if v.co.x < xmin + 0.004 and any(len(e.link_faces) == 1 for e in v.link_edges))
    other = [f for f in side if not any(v in ring_front for v in f.verts)]
    geom = list(set(other) | set(e for f in other for e in f.edges) | set(v for f in other for v in f.verts))
    bmesh.ops.bisect_plane(bmf, geom=geom, plane_co=(0.0, 0.0, zs), plane_no=(0.0, 0.0, 1.0), dist=1e-6)
    gone = [f for f in bmf.faces if abs(f.calc_center_median().y - ye) < 0.6
            and not any(v in ring_front for v in f.verts) and f.calc_center_median().z < zs]
    bmesh.ops.delete(bmf, geom=gone, context='FACES')
    # hole boundary, counter-clockwise seen from the front: right flange cut, rear edge of the band, left flange cut
    # (FrontCowls vertices), then the front edge of FrontEngineCowls from left to right under the nacelle
    hole = [e for e in bmf.edges if len(e.link_faces) == 1 and abs(e.verts[0].co.y - ye) < 0.6
            and all(v.co.z < zs + 1e-5 for v in e.verts) and not all(v in ring_front for v in e.verts)]
    adj = {}
    for e in hole:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    ends = [v for v, nb in adj.items() if len(nb) == 1]
    if len(ends) != 2:
        print('chin: unexpected hole boundary on engine %+.3f (%d ends)' % (ye, len(ends))); continue
    chain = [max(ends, key=lambda v: v.co.y)]; prev = None
    while True:
        nxt = [v for v in adj[chain[-1]] if v is not prev]
        if not nxt:
            break
        prev = chain[-1]; chain.append(nxt[0])
    fb_all = [v for v in fec.verts if abs(v.co.y - ye) < 0.6 and v.co.x < -5.05
              and any(len(e.link_faces) == 1 for e in v.link_edges)]

    def cowl_dir(v):           # along the cowl, towards its front edge (into the hole)
        d = sum(((v.co - e.other_vert(v).co).normalized() for e in v.link_edges if len(e.link_faces) == 2), Vector())
        return d.normalized() if d.length > 1e-6 else -X

    def ang(q):
        return math.atan2(q.z - zc, q.y - ye) % (2 * math.pi)
    a_l = ang(chain[-1].co)
    arc = [v for v in fb_all if v.co.z < zs - 1e-4]
    arc.sort(key=lambda v: ang(v.co) if ang(v.co) > a_l else ang(v.co) + 2 * math.pi)
    # beside the ring band, between its rear edge and the cowl, under the cut of the flange and down to chin_horn:
    # flat fill (one polygon, triangulated), like the flange above
    top = [k for k, v in enumerate(chain) if abs(v.co.z - zs) < 1e-5]
    k_pr = max(k for k in top if k < len(chain) // 2); k_pl = min(k for k in top if k > len(chain) // 2)
    bandc = chain[k_pr:k_pl + 1]                              # rear edge of the band, right to left
    zh = P['chin_horn']
    k_er = min(range(len(bandc) // 2), key=lambda k: abs(bandc[k].co.z - zh))
    k_el = min(range(len(bandc) // 2, len(bandc)), key=lambda k: abs(bandc[k].co.z - zh))
    arcv = [bmf.verts.new(v.co) for v in arc]                 # front edge of FrontEngineCowls (same positions)
    arcT = [cowl_dir(v) for v in arc]
    half = len(arc) // 2
    k_fl = min(range(half), key=lambda k: abs(arc[k].co.z - bandc[k_el].co.z))
    k_fr = min(range(half, len(arc)), key=lambda k: abs(arc[k].co.z - bandc[k_er].co.z))
    nd = P['chin_horn_div']
    ef_r = [bmf.verts.new(bandc[k_er].co.lerp(arcv[k_fr].co, i / nd)) for i in range(1, nd)]
    ef_l = [bmf.verts.new(bandc[k_el].co.lerp(arcv[k_fl].co, i / nd)) for i in range(1, nd)]
    # each flat part: strip of triangles between the band edge and the cowl edge, top to bottom; its first and last
    # triangles are fanned over the flange cut and over the divided lower edge
    horns = ((chain[:k_pr + 1][::-1], bandc[:k_er + 1], [chain[0]] + arcv[k_fr:][::-1], [bandc[k_er]] + ef_r + [arcv[k_fr]]),
             (chain[k_pl:], bandc[k_el:][::-1], [chain[-1]] + arcv[:k_fl + 1], [bandc[k_el]] + ef_l + [arcv[k_fl]]))
    ref_h = Vector((-4.9, ye, -0.30))
    for cut, inner, outer, low in horns:
        tris = []; i = j = 0
        while i < len(inner) - 1 or j < len(outer) - 1:
            if j == len(outer) - 1 or (i < len(inner) - 1 and inner[i + 1].co.z >= outer[j + 1].co.z):
                tris.append([inner[i], outer[j], inner[i + 1]]); i += 1
            else:
                tris.append([inner[i], outer[j], outer[j + 1]]); j += 1
        first, last = tris[0], tris[-1]
        apex_t = [v for v in first if v is not inner[0] and v is not outer[0]][0]
        apex_b = [v for v in last if v is not inner[-1] and v is not outer[-1]][0]
        tris = tris[1:-1] + [[apex_t, cut[k], cut[k + 1]] for k in range(len(cut) - 1)] \
            + [[apex_b, low[k], low[k + 1]] for k in range(len(low) - 1)]
        for vs in tris:
            f = bmf.faces.new(vs)
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - ref_h) < 0:
                f.normal_flip()
            for l in f.loops:
                l[uvf].uv = front_uv(l.vert.co + Vector((0.03, 0, 0)))
            f.smooth = True
            chin_faces += 1
    # chin boundary, counter-clockwise seen from the front: band edge from the right flat part to the left one, lower
    # edge of the left flat part, front edge of FrontEngineCowls under the nacelle, lower edge of the right flat part
    # (vertex position, kind, vertex, direction into the hole). Along the lower edge of the flat parts the curves
    # arrive along them: downwards along the band edge at one end, along the cowl at the other
    def band_down(kb, step):
        return (bandc[kb + step].co - bandc[kb].co).normalized() if 0 <= kb + step < len(bandc) else Vector((0, 0, -1))
    tb_l, tb_r = band_down(k_el, -1), band_down(k_er, 1)
    B = [(v.co.copy(), 'band', v, None) for v in bandc[k_er:k_el + 1]]
    B[0] = (B[0][0], 'edge', B[0][2], tb_r); B[-1] = (B[-1][0], 'edge', B[-1][2], tb_l)
    B += [(v.co.copy(), 'edge', v, tb_l.lerp(arcT[k_fl], (i + 1) / nd).normalized()) for i, v in enumerate(ef_l)]
    B += [(arcv[k].co.copy(), 'cowl', arcv[k], arcT[k]) for k in range(k_fl, k_fr + 1)]
    B += [(v.co.copy(), 'edge', v, tb_r.lerp(arcT[k_fr], (nd - 1 - i) / nd).normalized()) for i, v in enumerate(ef_r[::-1])]
    n = len(B)
    # lip angle of each boundary point: arc length of the boundary (front view) mapped on arc length of the lip
    # between four anchors (sides at the lip centre height, top of the band edge, bottom of the cowl)
    cow = [j for j in range(n) if B[j][1] == 'cowl']
    j_r = min((j for j in cow if B[j][0].y > ye), key=lambda j: abs(B[j][0].z - zc))
    B = B[j_r:] + B[:j_r]
    cow = [j for j in range(n) if B[j][1] == 'cowl']
    j_t = min((j for j in range(n) if B[j][1] == 'band'), key=lambda j: abs(B[j][0].y - ye))
    j_l = min((j for j in cow if B[j][0].y < ye), key=lambda j: abs(B[j][0].z - zc))
    j_b = min((j for j in cow if B[j][0].z < zc - 0.05), key=lambda j: abs(B[j][0].y - ye))
    assert 0 < j_t < j_l < j_b < n, (j_t, j_l, j_b, n)
    lb = [0.0]
    for j in range(1, n + 1):
        d = B[j % n][0] - B[j - 1][0]
        lb.append(lb[-1] + math.hypot(d.y, d.z))
    S = 4000; ls = [0.0]; prevp = lip_point(0.0, a0 + 2 * lr, b0 + 2 * lr)
    for i in range(1, S + 1):
        q = lip_point(2 * math.pi * i / S, a0 + 2 * lr, b0 + 2 * lr)
        ls.append(ls[-1] + math.hypot(q[0] - prevp[0], q[1] - prevp[1])); prevp = q

    def theta_at(sv_):         # inverse of the lip arc length
        lo, hi = 0, S
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if ls[mid] < sv_:
                lo = mid
            else:
                hi = mid
        f = (sv_ - ls[lo]) / max(ls[hi] - ls[lo], 1e-12)
        return 2 * math.pi * (lo + f) / S
    th_anchor = {0: 0.0, j_t: math.pi / 2, j_l: math.pi, j_b: 1.5 * math.pi, n: 2 * math.pi}
    keys = [0, j_t, j_l, j_b, n]
    ths = []
    for ka, kb in zip(keys[:-1], keys[1:]):
        sa = ls[int(round(th_anchor[ka] / (2 * math.pi) * S))]; sb = ls[int(round(th_anchor[kb] / (2 * math.pi) * S))]
        for j in range(ka, kb):
            f = (lb[j] - lb[ka]) / (lb[kb] - lb[ka])
            ths.append(theta_at(sa + (sb - sa) * f))
    M = len(ths)
    # chin rows (FrontCowls), from the lip outline to the hole boundary
    Lp = []
    for th in ths:
        y, z = lip_point(th, a0 + 2 * lr, b0 + 2 * lr)
        Lp.append(Vector((x0, ye + y, zc + z)))
    rows = []
    for t in P['chin_rings']:
        row = []
        for j in range(M):
            L = Lp[j]; Bp, kind, bv, T = B[j]
            h = P['chin_handle'] * (Bp - L).length
            p1 = L + X * h
            if kind == 'band':                       # concave corner under the band: straight towards the lip
                T = (p1 - Bp).normalized()
            row.append(bv if t >= 1.0 else bmf.verts.new(bezier(L, p1, Bp + T * h, Bp, t)))
        rows.append(row)
    ref = Vector((x0 + 0.12, ye, zc))
    for i in range(len(rows) - 1):
        for j in range(M):
            f = bmf.faces.new((rows[i][j], rows[i][(j + 1) % M], rows[i + 1][(j + 1) % M], rows[i + 1][j]))
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - ref) < 0:
                f.normal_flip()
            for l in f.loops:
                l[uvf].uv = front_uv(l.vert.co + Vector((0.03, 0, 0)))
            f.smooth = True
            chin_faces += 1
    # lip (metal) and duct (dark), on the same angles as the chin

    def ring_at(x, a, b):
        r = []
        for th in ths:
            y, z = superellipse(a, b, th, e0)
            r.append(bm.verts.new(Vector((x, ye + y, zc + z))))
        return r
    lip_outer = ring_at(x0, a0 + 2 * lr, b0 + 2 * lr)
    lip = [lip_outer,
           ring_at(x0 - lr * 0.75, a0 + lr * 1.7, b0 + lr * 1.7), ring_at(x0 - lr, a0 + lr, b0 + lr),
           ring_at(x0 - lr * 0.75, a0 + lr * 0.3, b0 + lr * 0.3), ring_at(x0, a0, b0)]
    duct = [lip[-1], ring_at(x0 + 0.02, a0, b0), ring_at(x0 + P['duct_len'], a0 - 0.012, b0 - 0.012)]
    for seqr, uv in ((lip, P['uv_metal']), (duct, P['uv_dark'])):
        for i in range(len(seqr) - 1):
            for k in range(M):
                set_uv(bm.faces.new((seqr[i][k], seqr[i][(k + 1) % M], seqr[i + 1][(k + 1) % M], seqr[i + 1][k])), uv)
    set_uv(bm.faces.new(list(reversed(duct[-1]))), P['uv_dark'])
bmf.transform(mwf.inverted()); bmf.normal_update(); bmf.to_mesh(ofr.data); bmf.free(); ofr.data.update()
print('FrontCowls: chin %d faces' % chin_faces)
skin = bvh_of(('FrontCowls', 'FrontEngineCowls', 'MidEngineCowls', 'TopEngineCowl', 'LowerEngCowls', 'EngCowlStrips'))
for ye in P['engines_y']:
    # lower vents
    (vx0, vx1), (vy0, vy1) = P['vents']
    for side in (-1, 1):
        grid = []
        for x in (vx0, (vx0 + vx1) / 2, vx1):
            row = []
            for dy in (vy0, (vy0 + vy1) / 2, vy1):
                q, qn = cast(skin, (x, ye + side * dy, P['axis_z']), (0, 0, -1))
                if q is None:
                    q, qn = Vector((x, ye + side * dy, -0.83)), Vector((0, 0, -1))
                row.append(bm.verts.new(q + qn * P['lift']))
            grid.append(row)
        for i in range(2):
            for j in range(2):
                set_uv(bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])), P['uv_dark'])
inl = finish(bm, 'EngineInlets')

# ================================================================ de-icing boots
bm = bmesh.new(); uv_lay = bm.loops.layers.uv.new('UVMap')
(bu0, bu1), (bv0, bv1) = P['uv_boot']
wing = wing_root


def leading_edge(y, tree=None):
    best = None
    for z in [-0.9 + 0.01 * i for i in range(130)]:
        q, qn = cast(tree or wing, (-7.0, y, z), (1, 0, 0), 10.0)
        if q is not None and (best is None or q.x < best.x):
            best = q
    return best


def leading_edge_x(y):
    q = leading_edge(y)
    return q.x if q is not None else None


nacelle_skin = bvh_of(('WngCowl', 'FrontEngineCowls', 'MidEngineCowls', 'LowerEngCowls', 'TopEngineCowl'))


def nacelle_side(ye, toward, y_from, tree):
    """|y| of the nacelle skin met by a ray cast spanwise towards the nacelle (toward = +1 / -1 in y), at the height
    of the wing leading edge, 3 cm behind it."""
    q = leading_edge(y_from, tree)
    h, _ = cast(nacelle_skin, (q.x + 0.03, ye + (y_from - ye), q.z), (0, toward, 0), 2.0)
    return abs(h.y) if h is not None else None


def boot_ring(y, le_x):
    """P['boot_rays'] points wrapping the leading edge at span station y (lower surface, nose, upper surface): rays
    cast inwards in a fan centred boot_depth behind the leading edge, from -90 deg (below) to +90 deg (above)."""
    dep = P['boot_depth']
    U, _ = cast(wing, (le_x + dep, y, 3.0), (0, 0, -1), 6.0); L, _ = cast(wing, (le_x + dep, y, -3.0), (0, 0, 1), 6.0)
    if U is None or L is None:
        return None
    zc = (U.z + L.z) / 2; O = Vector((le_x + dep, y, zc)); a = dep + 0.012; bu = U.z - zc; bl = zc - L.z
    pts = []
    n = P['boot_rays']
    for k in range(n):
        th = math.radians(-90 + 180 * k / (n - 1))
        b = bu if th > 0 else bl
        A = O + Vector((-a * math.cos(th), 0.0, b * math.sin(th)))
        an = Vector((-math.cos(th) / a, 0.0, math.sin(th) / b)).normalized()
        d = (A - O).normalized()
        q, qn = cast(wing, O + d * 1.0, -d, 1.0)
        if q is None or (q - O).length < (A - O).length - 0.04:
            q, qn = A, an
        elif qn.dot(d) < 0:                              # faces of the original wing are not consistently oriented
            qn = -qn
        pts.append((q, qn))
    return pts


def open_ring(y, le):
    """Ring of P['boot_rays'] points for the open-nose outer wing: lower skin (aft to front), nose arc through the
    leading-edge line le, upper skin (front to aft)."""
    (y0, x0, z0), (y1, x1, z1) = le
    t = (abs(y) - y0) / (y1 - y0); x_le = x0 + (x1 - x0) * t; z_le = z0 + (z1 - z0) * t
    s_edge = None
    for i in range(1, 100):                              # front edge of the skins behind the leading edge
        sx = 0.005 * i
        U, _ = cast(wing, (x_le + sx, y, 3.0), (0, 0, -1), 6.0); L, _ = cast(wing, (x_le + sx, y, -3.0), (0, 0, 1), 6.0)
        if U is not None and L is not None and U.z - L.z > 0.02:
            s_edge = sx + 0.005; break
    if s_edge is None:
        return None
    m = (P['boot_rays'] - 5) // 2
    xs = [x_le + s_edge + P['outer_extra'] * (1 - i / (m - 1)) for i in range(m)]      # aft -> front
    low, up = [], []
    for x in xs:
        L, _ = cast(wing, (x, y, -3.0), (0, 0, 1), 6.0); U, _ = cast(wing, (x, y, 3.0), (0, 0, -1), 6.0)
        if L is None or U is None:
            return None
        low.append((L, Vector((0, 0, -1)))); up.append((U, Vector((0, 0, 1))))
    zl, zu = low[-1][0].z, up[-1][0].z
    zc = min(max(z_le, zl + 0.01), zu - 0.01); xe = x_le + s_edge; a = s_edge
    arc = []
    for k in range(5):
        ph = math.radians(-60 + 30 * k); b = (zu - zc) if ph > 0 else (zc - zl)
        q = Vector((xe - a * math.cos(ph), y, zc + b * math.sin(ph)))
        arc.append((q, Vector((-math.cos(ph) / a, 0.0, math.sin(ph) / max(b, 1e-3))).normalized()))
    return low + arc + list(reversed(up))


def strip(ys, tree, le=None):
    global wing
    wing = tree
    les = [leading_edge_x(y) for y in ys]
    smooth = []                                          # running median of 5: the ray-found edge wanders by ~1 cm
    for i in range(len(ys)):
        win = sorted(v for v in les[max(0, i - 2):i + 3] if v is not None)
        smooth.append(win[len(win) // 2] if win else None)
    if le is not None:
        stations = [(y, open_ring(y, le)) for y in ys]
    else:
        stations = [(y, boot_ring(y, lx)) for y, lx in zip(ys, smooth) if lx is not None]
    stations = [s_ for s_ in stations if s_[1]]          # stations without skin (past the wing tip) are skipped
    verts = [[bm.verts.new(q + qn * P['boot_lift']) for (q, qn) in ring] for (_, ring) in stations]
    for i in range(len(verts) - 1):
        for k in range(len(verts[i]) - 1):
            f = bm.faces.new((verts[i][k], verts[i + 1][k], verts[i + 1][k + 1], verts[i][k + 1]))
            for l, kk in zip(f.loops, (k, k, k + 1, k + 1)):
                l[uv_lay].uv = (bu0 + (bu1 - bu0) * kk / max(1, len(verts[i]) - 1), (bv0 + bv1) / 2)
    for ring_v in (verts[:1] + verts[-1:]) if len(verts) > 1 else []:   # end caps
        try:
            f = bm.faces.new(ring_v)
        except ValueError:
            continue
        for l in f.loops:
            l[uv_lay].uv = (bu0, (bv0 + bv1) / 2)
    return len(stations), len(ys)


for sign, ye in ((-1, P['engines_y'][0]), (1, P['engines_y'][1])):
    ya, yb = P['boots_inner']
    y_in = nacelle_side(ye, sign, sign * (abs(ye) - 0.6), wing_only)          # nacelle skin, inboard side
    if y_in: yb = y_in + 0.012
    y_out = nacelle_side(ye, -sign, sign * (abs(ye) + 0.9), wing_only)       # nacelle skin, outboard side
    n_st = int(round((yb - ya) / P['boot_dy'])) + 1
    r1 = strip([sign * (ya + (yb - ya) * i / (n_st - 1)) for i in range(n_st)], wing_only)
    le = P['outer_le'][sign]; y_open, y_tip = le[0][0], P['outer_tip'] + (le[1][0] - P['outer_le'][-1][1][0])
    oa = (y_out - 0.012) if y_out else abs(ye) + P['wall_y'] - 0.03; fine, fine_len, coarse = P['boot_dy_outer']
    n_g = max(3, int(round((y_open + 0.01 - oa) / fine)) + 1)          # nacelle fillet: closed nose, fan
    r2 = strip([sign * (oa + (y_open + 0.01 - oa) * i / (n_g - 1)) for i in range(n_g)], wing_only)
    ys = [y_open + fine * i for i in range(int(fine_len / fine) + 1)]   # outer wing: open nose, D section
    while ys[-1] + coarse < y_tip:
        ys.append(ys[-1] + coarse)
    ys.append(y_tip)
    r3 = strip([sign * y for y in ys], wing_only, le)
    print('boots side %+d: inner %.3f..%.3f %d/%d, fillet %.3f..%.2f %d/%d, outer %.2f..%.2f %d/%d stations'
          % (sign, ya, yb, r1[0], r1[1], oa, y_open, r2[0], r2[1], y_open, y_tip, r3[0], r3[1]))
# the strips replace the geometry of DeicebootsWings (same object, material and lists in Models/KingAir.xml)
remove_obj('DeicebootsInner')
# PropCone: stray closed disc (dia. 0.21 m) on the outboard side of the right cowl, under the root of the old
# exhaust stack; not animated, it showed under the new, slimmer stack
remove_obj('PropCone')
ob = bpy.data.objects['DeicebootsWings']; me = ob.data; inv_b = ob.matrix_world.inverted()
for v in bm.verts:
    v.co = inv_b @ v.co
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    f.smooth = True
bm.to_mesh(me); bm.free(); me.update()
boots = ob

# ================================================================ spinners: closed
# The original spinners have three blade openings (120 deg apart) while the propellers have four blades: only one
# blade went through an opening. Each spinner is rebuilt closed, as a surface of revolution about the spin axis of
# Models/KingAir.xml, with the profile of the original (outer radius of its rings, interpolated). Its texture is a
# projection of the spinner seen from the front, with the three openings painted in: the closed spinner is mapped on
# a narrow clean sector of it, half way between two painted openings, at the same radius (shading of the polished
# metal kept, no livery retouched).
for sname, (sy, sz) in P['spinners'].items():
    ob_s = bpy.data.objects[sname]; mw_s = ob_s.matrix_world
    src = bmesh.new(); src.from_mesh(ob_s.data); src.transform(mw_s); uvs = src.loops.layers.uv.active
    # planar texture projection of the original: uv = A (y, z) + b, least squares over its loops
    rows = [(l.vert.co.y, l.vert.co.z, l[uvs].uv.x, l[uvs].uv.y) for f in src.faces for l in f.loops]
    def solve(col):
        n = len(rows); sy_ = sum(r[0] for r in rows); sz_ = sum(r[1] for r in rows)
        syy = sum(r[0] * r[0] for r in rows); szz = sum(r[1] * r[1] for r in rows); syz = sum(r[0] * r[1] for r in rows)
        sc = sum(r[col] for r in rows); syc = sum(r[0] * r[col] for r in rows); szc = sum(r[1] * r[col] for r in rows)
        import mathutils
        M = mathutils.Matrix(((syy, syz, sy_), (syz, szz, sz_), (sy_, sz_, n)))
        return M.inverted() @ Vector((syc, szc, sc))
    cu, cv = solve(2), solve(3)
    proj = lambda y, z: (cu[0] * y + cu[1] * z + cu[2], cv[0] * y + cv[1] * z + cv[2])
    # clean direction of the texture: the painted openings stand out from the polished metal; for each direction,
    # departure of the texture along the radius from the median over all directions, summed over the sector width;
    # the direction with the smallest sum is used (texture of Models/prototype.png, same spinner in every livery)
    import numpy as np
    img = bpy.data.images.load(os.path.join(MODELS, 'prototype.png'), check_existing=True)
    W_i, H_i = img.size; px = np.empty(W_i * H_i * 4, dtype=np.float32); img.pixels.foreach_get(px)
    px = px.reshape(H_i, W_i, 4)[:, :, :3].mean(axis=2)
    r_base = max(math.hypot(v.co.y - sy, v.co.z - sz) for v in src.verts)
    radii = [r_base * f for f in np.linspace(0.25, 0.97, 30)]
    lum = np.zeros((360, len(radii)))
    for deg in range(360):
        th = math.radians(deg)
        for j, r in enumerate(radii):
            u, v = proj(sy + r * math.cos(th), sz + r * math.sin(th))
            lum[deg, j] = px[min(max(int(v * H_i), 0), H_i - 1), min(max(int(u * W_i), 0), W_i - 1)]
    dev = np.abs(lum - np.median(lum, axis=0)).mean(axis=1)
    half = int(round(P['spinner_sector_deg'])) + 4
    score = [sum(dev[(d + k) % 360] for k in range(-half, half + 1)) for d in range(360)]
    deg_c = int(np.argmin(score)); th_c = math.radians(deg_c)
    centres = [d for d in range(360) if dev[d] == max(dev[(d + k) % 360] for k in range(-20, 21)) and dev[d] > 2 * np.median(dev)]
    # profile: outer radius of the rings of the original (x clusters of at least 10 vertices), from the tip to the base
    xs = sorted(v.co.x for v in src.verts); clusters = []
    for x in xs:
        if clusters and x - clusters[-1][-1] < 0.004:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    prof = []
    for c in clusters:
        if len(c) < 10 and c is not clusters[0] and c is not clusters[-1]:
            continue
        x0, x1 = c[0] - 1e-6, c[-1] + 1e-6
        rs = sorted(math.hypot(v.co.y - sy, v.co.z - sz) for v in src.verts if x0 <= v.co.x <= x1)
        prof.append((sum(c) / len(c), rs[len(rs) * 3 // 4]))
    prof.sort()
    x_tip, x_base = prof[0][0], prof[-1][0]
    def r_at(x):                                         # Catmull-Rom through the profile points
        if x <= prof[0][0]: return prof[0][1]
        if x >= prof[-1][0]: return prof[-1][1]
        i = max(k for k in range(len(prof) - 1) if prof[k][0] <= x)
        p0 = prof[max(i - 1, 0)]; p1 = prof[i]; p2 = prof[i + 1]; p3 = prof[min(i + 2, len(prof) - 1)]
        t = (x - p1[0]) / (p2[0] - p1[0])
        m1 = (p2[1] - p0[1]) / max(p2[0] - p0[0], 1e-6) * (p2[0] - p1[0])
        m2 = (p3[1] - p1[1]) / max(p3[0] - p1[0], 1e-6) * (p2[0] - p1[0])
        h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t; h01 = -2 * t ** 3 + 3 * t ** 2; h11 = t ** 3 - t ** 2
        return h00 * p1[1] + h10 * m1 + h01 * p2[1] + h11 * m2
    n_st = max(8, int((x_base - x_tip) / P['spinner_step']))
    stations = [x_tip + (x_base - x_tip) * (i / n_st) ** 1.0 for i in range(n_st + 1)]
    src.free()
    # mesh: rings round the axis, closed at the tip, open at the base (as the original, against PropConeDisks)
    Ns = P['spinner_segments']; inv_s = mw_s.inverted(); bm = bmesh.new(); uv_s = bm.loops.layers.uv.new('UVMap')
    tip = bm.verts.new(inv_s @ Vector((x_tip - 0.002, sy, sz)))
    ringsv = []
    for x in stations:
        r = r_at(x)
        ringsv.append([bm.verts.new(inv_s @ Vector((x, sy + r * math.cos(2 * math.pi * k / Ns), sz + r * math.sin(2 * math.pi * k / Ns))))
                       for k in range(Ns)])
    sector = math.radians(P['spinner_sector_deg'])

    def uv_of(x, k_ang):                                # angle k_ang in [0, 2 pi] (unwrapped per face)
        r = r_at(x) if x > x_tip else 0.0
        th = th_c + (k_ang - math.pi) / math.pi * sector
        return proj(sy + r * math.cos(th), sz + r * math.sin(th))
    faces_s = []
    for k in range(Ns):
        a0, a1 = 2 * math.pi * k / Ns, 2 * math.pi * (k + 1) / Ns
        f = bm.faces.new((tip, ringsv[0][(k + 1) % Ns], ringsv[0][k]))
        for l, (x, an) in zip(f.loops, ((x_tip, (a0 + a1) / 2), (stations[0], a1), (stations[0], a0))):
            l[uv_s].uv = uv_of(x, an)
        faces_s.append(f)
    for i in range(len(stations) - 1):
        for k in range(Ns):
            a0, a1 = 2 * math.pi * k / Ns, 2 * math.pi * (k + 1) / Ns
            f = bm.faces.new((ringsv[i][k], ringsv[i][(k + 1) % Ns], ringsv[i + 1][(k + 1) % Ns], ringsv[i + 1][k]))
            for l, (x, an) in zip(f.loops, ((stations[i], a0), (stations[i], a1), (stations[i + 1], a1), (stations[i + 1], a0))):
                l[uv_s].uv = uv_of(x, an)
            faces_s.append(f)
    for f in faces_s:
        f.normal_update()
        c = mw_s @ f.calc_center_median()
        if (mw_s.to_3x3() @ f.normal).dot(c - Vector((c.x + 0.3, sy, sz))) < 0:
            f.normal_flip()
        f.smooth = True
    me_s = ob_s.data; bm.to_mesh(me_s); bm.free(); me_s.update()
    for poly in me_s.polygons:
        poly.use_smooth = True
    print('%s: closed, %d faces, profile %d rings x %.3f..%.3f, texture sector at %.0f deg (openings at %s deg)'
          % (sname, len(me_s.polygons), len(prof), x_tip, x_base, math.degrees(th_c), ', '.join('%.0f' % c for c in centres)))

# ================================================================ export
names = ('Exhaust', 'EngineInlets', 'DeicebootsWings', 'FrontCowls', 'FrontEngineCowls', 'Wings', 'PropConeLeft',
         'PropConeRight')
for o in bpy.data.objects:
    o.select_set(o.name in names)
bpy.context.view_layer.objects.active = exh
bpy.ops.export_scene.export_ac3d(filepath=OUT, axis_forward='-Z', axis_up='Y', use_selection=True, export_rots='apply',
                                 crease_angle=math.radians(61), merge_materials=False, global_doublesided=False)
print('Exhaust %d faces; EngineInlets %d; DeicebootsWings %d; Wings %d faces'
      % (len(exh.data.polygons), len(inl.data.polygons), len(boots.data.polygons), len(ow.data.polygons)))
print('exported', OUT)
