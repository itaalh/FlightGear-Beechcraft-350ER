"""Blender script: builds the ventral pod of the ALSR "Vador" and the two ventral fins of the King Air 350 under the
imported fuselage, and exports them to AC3D.

Run inside Blender (4.1 or later, io_scene_ac3d add-on enabled), for example:

    blender --background --python Tools/pod/alsr_pod.py -- --out /tmp/alsr-pod.ac
    python Tools/pod/splice_ac.py /tmp/alsr-pod.ac          # then merge into Models/KingAir.ac

or paste it in Blender's text editor / send it through Blender's MCP server. If no "Fuselage" object exists,
Models/KingAir.ac is imported first (axes: -Z forward, Y up, so that Blender X/Y/Z = FlightGear model x/y/z:
x aft, y right, z up).

Pod (F-WTAO / F-RACH photographs and the manufacturer's drawing, profile checked by the project author): one
"canoe" fairing lofted along the belly, with a flat bottom, rounded chines and vertical sides. The front section
is a thin flat plate (0.14 m) with a semicircular bow and a quarter-round front edge; a gentle S-shaped ramp at
x -3.75..-3.05 leads to the deep body (0.56 m, 0.8 m wide) under the cabin, kept to the wing trailing edge, then a tapered stern
ending behind the wing. The rear EO/IR turret sits at the stern; the camera is retracted and its flush disc
AlsrSensorCover closes the opening (this aircraft has no front turret). The top of the pod runs 12 cm inside the
fuselage so that no gap shows.
Delta fins: the two long, low ventral fins under the tail cone, canted outwards (object DeltaFins, every livery).
UVs reuse the lower right fuselage side of the body texture (white in every livery) and, for the disc, a uniform
grey spot of the gear texture; nothing has to be painted.
"""
import bpy, bmesh, math, os, sys, tempfile
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MODELS = os.path.join(ROOT, 'Models')
if not os.path.exists(os.path.join(MODELS, 'KingAir.ac')):     # run from somewhere else: look for the aircraft directory
    for p in (os.getcwd(), os.path.dirname(bpy.data.filepath or '')):
        if os.path.exists(os.path.join(p, 'Models', 'KingAir.ac')):
            ROOT = p; MODELS = os.path.join(ROOT, 'Models'); break

P = dict(
    x_front=-4.42,                       # tip of the bow (just behind the nose-gear bay)
    bow_len=0.40, bow_w=0.36,            # bow in plan: semi-ellipse, bow_len long, half-width bow_w at its end
    bow_ramp=0.14, bow_depth=0.14,       # front face: quarter round (bow_ramp = bow_depth) up to the belly
    bow_chine=0.08,                      # radius of the rounded lower edges of the front plate
    # stations aft of the bow: (x, half-width, depth below the belly centreline, chine radius), in metres.
    # Shallow flat front section (0.14-0.16 m), gentle S-shaped ramp at x -3.75..-3.05 (about 30 deg, rounded at
    # both ends) down to the deep body (0.56 m), body kept to the wing trailing edge. Width 0.8 m.
    body=[(-4.28, 0.36, 0.14, 0.08), (-3.75, 0.37, 0.16, 0.08), (-3.40, 0.38, 0.36, 0.10), (-3.05, 0.39, 0.56, 0.10),
          (-2.80, 0.40, 0.56, 0.10), (-0.50, 0.40, 0.56, 0.10)],
    step=(-3.95, -2.85),                 # x range of the ramp, sampled finely
    x_end=0.60, stern_len=1.10,          # tapered stern: semi-ellipse in plan, elliptic profile, ends behind the wing
    stern_w=0.40, stern_depth=0.56,
    disc_x=-0.72, cover_r=0.22, cover_thickness=0.03, cover_proud=0.008,   # retracted rear turret, on the flat keel
    wall_up=0.12,                        # how far the walls run up inside the fuselage
    m_arc=6, m_flat=6,                   # points per chine arc, per flat bottom
    dx_fine=0.025, dx=0.10,
    # ventral delta fins under the tail cone (side-profile photograph of F-RACG): long and low, root on the lower
    # fuselage at y_root from below the roundel to near the tail, leading and trailing edges swept aft, canted
    # cant_deg from the vertical (down and outwards)
    fins=dict(x_le=3.10, x_te=4.95, tip_le=3.50, tip_te=4.80, span=0.42, cant_deg=35.0, y_root=0.25, sink=0.12,
              thickness=0.04),
    # UVs: lower right fuselage side of the texture, u along x, v by distance above the belly seam; grey spot for the disc
    u0=0.4836, ku=0.0681, u_max=0.49, v_seam=0.972, kv=0.045, grey_uv=(0.917, 0.30),
)
if 'PARAMS' in globals():
    P.update(globals()['PARAMS'])
OUT = globals().get('OUT') or os.path.join(tempfile.gettempdir(), 'alsr-pod.ac')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--out' in argv:
    OUT = argv[argv.index('--out') + 1]

# ---------------------------------------------------------------- reference model
if 'Fuselage' not in bpy.data.objects:
    bpy.ops.import_scene.import_ac3d(filepath=os.path.join(MODELS, 'KingAir.ac'), axis_forward='-Z', axis_up='Y',
                                     collection_name='KingAir')
fus = bpy.data.objects['Fuselage']
bm_f = bmesh.new(); bm_f.from_mesh(fus.data); bm_f.transform(fus.matrix_world)
bvh = BVHTree.FromBMesh(bm_f)


def zb(x, y):
    """Height of the belly skin at (x, y): first hit of a vertical ray cast from below."""
    hit = bvh.ray_cast(Vector((x, y, -3.0)), Vector((0, 0, 1)), 6.0)
    return None if hit[0] is None else hit[0].z


def catmull(pts, x):
    """Monotone cubic (Fritsch-Carlson) interpolation of the columns of pts (sorted by x) at x: no overshoot
    at the ramp, flat where the data is flat."""
    xs = [p[0] for p in pts]
    if x <= xs[0]: return list(pts[0][1:])
    if x >= xs[-1]: return list(pts[-1][1:])
    n = len(xs)
    for i in range(n - 1):
        if xs[i] <= x <= xs[i + 1]:
            break
    out = []
    for c in range(1, len(pts[0])):
        ys = [p[c] for p in pts]
        h = [xs[k + 1] - xs[k] for k in range(n - 1)]
        delta = [(ys[k + 1] - ys[k]) / h[k] for k in range(n - 1)]
        m = [0.0] * n
        for k in range(1, n - 1):
            if delta[k - 1] * delta[k] > 0:
                w1 = 2 * h[k] + h[k - 1]; w2 = h[k] + 2 * h[k - 1]
                m[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
        m[0] = delta[0]; m[-1] = delta[-1]
        t = (x - xs[i]) / h[i]
        v = ((2*t**3 - 3*t**2 + 1) * ys[i] + (t**3 - 2*t**2 + t) * h[i] * m[i]
             + (-2*t**3 + 3*t**2) * ys[i + 1] + (t**3 - t**2) * h[i] * m[i + 1])
        out.append(max(v, 0.0))
    return out


x_front = P['x_front']
x_bow = x_front + P['bow_len']           # end of the bow in plan
x_ramp = x_front + P['bow_ramp']         # where the bottom reaches its full depth
xend = P['x_end']
x_stern0 = xend - P['stern_len']


def section_params(x):
    """(half-width, depth, chine radius) at station x."""
    w, d, rc = catmull(P['body'], x)[:3]
    if x < x_bow:
        t = (x_bow - x) / P['bow_len']
        w = P['bow_w'] * math.sqrt(max(1.0 - t * t, 0.0))
    if x < x_ramp:
        t = (x_ramp - x) / P['bow_ramp']
        d = P['bow_depth'] * math.sqrt(max(1.0 - t * t, 0.0))
        rc = P['bow_chine']
    if x > x_stern0:
        t = (x - x_stern0) / P['stern_len']
        f = math.sqrt(max(1.0 - t * t, 0.0))
        w = P['stern_w'] * f; d = P['stern_depth'] * f
    return w, d, rc


def section(w, d, zc, rc):
    """Hull section, right side top to left side top: vertical side, chine arc, flat bottom, chine arc, side."""
    rc = min(rc, 0.9 * d, 0.9 * w)
    ma = P['m_arc']; nf = P['m_flat']
    pts = [(w, zc)]
    for k in range(ma + 1):
        a = (math.pi / 2) * k / ma
        pts.append((w - rc + rc * math.cos(a), zc - d + rc - rc * math.sin(a)))
    for k in range(1, nf):
        pts.append(((w - rc) * (1.0 - 2.0 * k / nf), zc - d))
    for k in range(ma, -1, -1):
        a = (math.pi / 2) * k / ma
        pts.append((-(w - rc) - rc * math.cos(a), zc - d + rc - rc * math.sin(a)))
    pts.append((-w, zc))
    return pts


def uv_body(x, s):
    return (min(P['u0'] + P['ku'] * x, P['u_max']), P['v_seam'] - P['kv'] * min(s, 1.0))


for nm in ('AlsrPod', 'AlsrSensorCover', 'DeltaFins'):
    o = bpy.data.objects.get(nm)
    if o:
        me = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me)
col = bpy.data.collections.get('ALSR') or bpy.data.collections.new('ALSR')
if col.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(col)
mat = bpy.data.materials.get('Material6.001') or fus.data.materials[0]

# ---------------------------------------------------------------- stations
xs = []
x = x_front + 0.01
while x < xend - 1e-6:
    xs.append(x)
    fine = x < x_bow + 0.1 or P['step'][0] <= x <= P['step'][1] or x > xend - 0.4
    x += P['dx_fine'] if fine else (P['dx'] if x < x_stern0 else P['dx'] / 2)

# ---------------------------------------------------------------- loft
bm = bmesh.new()
uv_lay = bm.loops.layers.uv.new('UVMap')
rings = []
for x in xs:
    w, d, rc = section_params(x)
    zc = zb(x, 0.0)
    if w < 0.012 or d < 0.004 or zc is None:
        continue
    hull = [Vector((x, y, z)) for (y, z) in section(w, d, zc, rc)]
    i0 = min(range(len(hull)), key=lambda i: abs(hull[i].y) + (0 if hull[i].z < zc - 0.5 * d else 10))
    sb = [0.0] * len(hull)                                # arc length from the keel, for the UVs
    for k in range(i0 + 1, len(hull)):
        sb[k] = sb[k - 1] + (hull[k] - hull[k - 1]).length
    for k in range(i0 - 1, -1, -1):
        sb[k] = sb[k + 1] + (hull[k] - hull[k + 1]).length
    zr = zb(x, w) or zc; zl = zb(x, -w) or zc
    topR = Vector((x, w, zr + P['wall_up'])); topL = Vector((x, -w, zl + P['wall_up']))
    pts = [topR] + hull + [topL]
    ss = [sb[0] + (topR - hull[0]).length] + sb + [sb[-1] + (topL - hull[-1]).length]
    rings.append(([bm.verts.new(p) for p in pts], ss, x))
nose = bm.verts.new(Vector((x_front, 0.0, zb(x_front, 0.0) - 0.002)))
xt = xend; tipv = bm.verts.new(Vector((xt, 0.0, zb(xt, 0.0) - 0.002)))
bm.verts.ensure_lookup_table()


def quad(a, b, c, d, uvs):
    try:
        f = bm.faces.new((a, b, c, d))
    except ValueError:
        return
    for l, uv in zip(f.loops, uvs): l[uv_lay].uv = uv


def fan(ring, ss, x, apex, xa, reverse):
    N = len(ring)
    for k in range(N - 1):
        tri = (ring[k], ring[k + 1], apex) if reverse else (ring[k + 1], ring[k], apex)
        try:
            f = bm.faces.new(tri)
        except ValueError:
            continue
        uvs = [uv_body(x, ss[k]), uv_body(x, ss[k + 1]), uv_body(xa, 0.0)] if reverse else \
              [uv_body(x, ss[k + 1]), uv_body(x, ss[k]), uv_body(xa, 0.0)]
        for l, uv in zip(f.loops, uvs): l[uv_lay].uv = uv
    try:
        f = bm.faces.new((ring[N - 1], ring[0], apex) if reverse else (ring[0], ring[N - 1], apex))
        for l in f.loops: l[uv_lay].uv = uv_body(x, 1.0)
    except ValueError:
        pass


for (ra, sa, xa), (rb, sbb, xb) in zip(rings, rings[1:]):
    N = len(ra)
    for k in range(N - 1):
        quad(ra[k], rb[k], rb[k + 1], ra[k + 1],
             [uv_body(xa, sa[k]), uv_body(xb, sbb[k]), uv_body(xb, sbb[k + 1]), uv_body(xa, sa[k + 1])])
    quad(ra[N - 1], rb[N - 1], rb[0], ra[0], [uv_body(xa, 1.0)] * 4)       # top strip, inside the fuselage
fan(rings[0][0], rings[0][1], rings[0][2], nose, x_front, True)             # bow fan
fan(rings[-1][0], rings[-1][1], rings[-1][2], tipv, xt, False)              # stern fan
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
pod_me = bpy.data.meshes.new('AlsrPod'); bm.to_mesh(pod_me); bm.free()
pod = bpy.data.objects.new('AlsrPod', pod_me); col.objects.link(pod); pod.data.materials.append(mat)

# ---------------------------------------------------------------- disc closing the retracted rear turret
xd = P['disc_x']
z_keel = zb(xd, 0.0) - section_params(xd)[1]
bm = bmesh.new(); uv_lay = bm.loops.layers.uv.new('UVMap')
t = P['cover_thickness']
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=64, radius1=P['cover_r'], radius2=P['cover_r'],
                      depth=t, matrix=Matrix.Translation((xd, 0.0, z_keel - P['cover_proud'] + t / 2)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    for l in f.loops: l[uv_lay].uv = P['grey_uv']
cov_me = bpy.data.meshes.new('AlsrSensorCover'); bm.to_mesh(cov_me); bm.free()
cov = bpy.data.objects.new('AlsrSensorCover', cov_me); col.objects.link(cov); cov.data.materials.append(mat)

# ---------------------------------------------------------------- delta fins (both sides, one object)
F = P['fins']; th = math.radians(F['cant_deg'])
bm = bmesh.new(); uv_lay = bm.loops.layers.uv.new('UVMap')
root_z = []
for side in (1, -1):
    sdir = Vector((0.0, side * math.sin(th), -math.cos(th)))      # span direction: down and outwards
    nrm = Vector((0.0, side * math.cos(th), math.sin(th)))        # plate normal

    def root(x):
        z = zb(x, side * F['y_root'])
        if z is None:
            z = zb(x, 0.0) or -0.3
        root_z.append(round(z, 3))
        return Vector((x, side * F['y_root'], z)) - sdir * F['sink']
    r0 = root(F['x_le']); r1 = root(F['x_te'])
    L = F['span'] + F['sink']
    poly = [(F['x_le'], 0.0), (F['x_te'], 0.0), (F['tip_te'], L), (F['tip_le'], L)]

    def pt(x, v, off):
        base = r0.lerp(r1, (x - F['x_le']) / (F['x_te'] - F['x_le']))
        return base + sdir * v + nrm * off * (1.0 - 0.6 * v / L)      # thinner towards the tip
    t2 = F['thickness'] / 2
    top = [bm.verts.new(pt(x, v, +t2)) for x, v in poly]
    bot = [bm.verts.new(pt(x, v, -t2)) for x, v in poly]
    faces = [top, list(reversed(bot))] + [[top[i], bot[i], bot[(i + 1) % 4], top[(i + 1) % 4]] for i in range(4)]
    for fv in faces:
        try:
            f = bm.faces.new(fv)
        except ValueError:
            continue
        for l in f.loops:
            co = l.vert.co
            l[uv_lay].uv = (0.25 + 0.05 * (co.x - F['x_le']), 0.965 - 0.03 * (co - r0).dot(sdir) / L)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
fin_me = bpy.data.meshes.new('DeltaFins'); bm.to_mesh(fin_me); bm.free()
fins = bpy.data.objects.new('DeltaFins', fin_me); col.objects.link(fins); fins.data.materials.append(mat)

for o in (pod, cov, fins):                             # smooth shading, sharp edges above 50 degrees
    me = o.data
    for p in me.polygons: p.use_smooth = True
    bm = bmesh.new(); bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(50):
            e.smooth = False
    bm.to_mesh(me); bm.free(); me.update()

# ---------------------------------------------------------------- export
for o in bpy.data.objects:
    o.select_set(o.name in ('AlsrPod', 'AlsrSensorCover', 'DeltaFins'))
bpy.context.view_layer.objects.active = pod
bpy.ops.export_scene.export_ac3d(filepath=OUT, axis_forward='-Z', axis_up='Y', use_selection=True, export_rots='apply',
                                 crease_angle=math.radians(61), merge_materials=False, global_doublesided=False)
bb = [pod.matrix_world @ Vector(c) for c in pod.bound_box]
print('AlsrPod: %d faces, x %.2f..%.2f, y +-%.2f, z %.2f..%.2f; keel at disc z %.3f; AlsrSensorCover: %d faces; '
      'DeltaFins: %d faces, root z %s' % (len(pod_me.polygons), min(v.x for v in bb), max(v.x for v in bb),
                                           max(v.y for v in bb), min(v.z for v in bb), max(v.z for v in bb), z_keel,
                                           len(cov_me.polygons), len(fin_me.polygons), root_z))
print('exported', OUT)
