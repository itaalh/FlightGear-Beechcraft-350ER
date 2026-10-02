"""Minimal AC3D parser: returns list of objects with world-space triangles and UVs."""
import numpy as np

def parse_ac(path):
    with open(path, 'r', encoding='latin-1') as f:
        lines = f.read().split('\n')
    i = 0
    materials = []
    objects = []

    def parse_object(i, parent_loc, parent_rot):
        # lines[i] starts with OBJECT
        obj = {'name': None, 'loc': np.zeros(3), 'rot': np.eye(3), 'texture': None,
               'verts': None, 'surfs': [], 'type': lines[i].split()[1]}
        i += 1
        kids = 0
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                i += 1; continue
            tok = l.split()
            k = tok[0]
            if k == 'name':
                obj['name'] = l[5:].strip().strip('"')
            elif k == 'loc':
                obj['loc'] = np.array([float(t) for t in tok[1:4]])
            elif k == 'rot':
                obj['rot'] = np.array([float(t) for t in tok[1:10]]).reshape(3, 3)
            elif k == 'texture':
                obj['texture'] = l[8:].strip().strip('"')
            elif k == 'numvert':
                n = int(tok[1])
                v = np.array([[float(t) for t in lines[i + 1 + j].split()[:3]] for j in range(n)])
                obj['verts'] = v
                i += n
            elif k == 'numsurf':
                ns = int(tok[1])
                i += 1
                for s in range(ns):
                    # SURF
                    flags = int(lines[i].split()[1], 0); i += 1
                    mat = 0
                    if lines[i].startswith('mat'):
                        mat = int(lines[i].split()[1]); i += 1
                    nr = int(lines[i].split()[1]); i += 1
                    refs = []
                    for r in range(nr):
                        t = lines[i + r].split()
                        refs.append((int(t[0]), float(t[1]), float(t[2])))
                    i += nr
                    obj['surfs'].append((flags, mat, refs))
                continue
            elif k == 'kids':
                kids = int(tok[1])
                i += 1
                break
            i += 1
        # world transform (AC: child vertices are in parent space after rot then loc)
        wrot = parent_rot @ obj['rot']
        wloc = parent_rot @ obj['loc'] + parent_loc
        if obj['verts'] is not None:
            obj['wverts'] = (wrot @ obj['verts'].T).T + wloc
        objects.append(obj)
        for c in range(kids):
            i = parse_object(i, wloc, wrot)
        return i

    while i < len(lines):
        l = lines[i]
        if l.startswith('MATERIAL'):
            materials.append(l)
            i += 1
        elif l.startswith('OBJECT'):
            i = parse_object(i, np.zeros(3), np.eye(3))
        else:
            i += 1
    return objects, materials


def triangulate(obj):
    """Return (tri_pos [N,3,3], tri_uv [N,3,2]) for polygon surfaces (fan triangulation)."""
    P = []; UV = []
    if obj.get('wverts') is None:
        return np.zeros((0, 3, 3)), np.zeros((0, 3, 2))
    V = obj['wverts']
    for flags, mat, refs in obj['surfs']:
        typ = flags & 0x0F
        if typ != 0 or len(refs) < 3:
            continue
        for j in range(1, len(refs) - 1):
            r = (refs[0], refs[j], refs[j + 1])
            P.append([V[a[0]] for a in r])
            UV.append([(a[1], a[2]) for a in r])
    return np.array(P).reshape(-1, 3, 3), np.array(UV).reshape(-1, 3, 2)
