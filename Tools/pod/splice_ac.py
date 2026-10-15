#!/usr/bin/env python3
"""Insert (or replace) the top-level objects of an exported AC3D file into Models/KingAir.ac.

    python splice_ac.py <exported.ac> [--target ../../Models/KingAir.ac] [--mat 2] [--set-mat NAME=INDEX ...]
                        [--remove NAME ...]

The objects keep their name, vertices, surfaces and UVs; their material index is rewritten to --mat
(2 = "Material6.001", the fuselage material of KingAir.ac) for new objects, or to the index of the object they
replace (which also gives them its surface flags, two-sided in KingAir.ac); --set-mat forces the material index
of a named object; --remove deletes an object from the target. The Blender exporter's "data" lines are dropped
and the texture is forced to prototype.png (the livery system replaces it). Objects of the target that have
the same names are replaced, so the script can be run again after a change of the model.
"""
import argparse, collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read_objects(lines):
    """Split an AC3D file into (header_lines, world_header_lines, [object_block_lines...]).
    Only flat files (no nested kids) are supported, which is the case of KingAir.ac."""
    i = 0
    while not lines[i].startswith('OBJECT world'):
        i += 1
    header = lines[:i]
    j = i
    while not lines[j].startswith('kids '):
        j += 1
    world = lines[i:j + 1]
    objs = []
    k = j + 1
    while k < len(lines):
        if not lines[k].strip():
            k += 1
            continue
        assert lines[k].startswith('OBJECT '), 'unexpected line %d: %r' % (k + 1, lines[k])
        e = k
        while not lines[e].startswith('kids '):
            e += 1
        assert lines[e].strip() == 'kids 0', 'nested objects are not supported (line %d)' % (e + 1)
        objs.append(lines[k:e + 1])
        k = e + 1
    return header, world, objs


def obj_name(block):
    for l in block:
        if l.startswith('name '):
            return l.split('"')[1]
    return None


def clean(block, mat, surf=None):
    out = []
    i = 0
    while i < len(block):
        l = block[i]
        if l.startswith('data '):
            n = int(l.split()[1])
            # the data payload spans the following lines (n bytes); the Blender exporter writes one line
            i += 2
            continue
        if l.startswith('mat '):
            l = 'mat %d' % mat
        if l.startswith('texture '):
            l = 'texture "prototype.png"'
        if surf and l.startswith('SURF '):
            l = 'SURF %s' % surf
        out.append(l)
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exported')
    ap.add_argument('--target', default=os.path.join(HERE, '..', '..', 'Models', 'KingAir.ac'))
    ap.add_argument('--mat', type=int, default=2)
    ap.add_argument('--set-mat', action='append', default=[], metavar='NAME=INDEX')
    ap.add_argument('--remove', action='append', default=[], metavar='NAME')
    a = ap.parse_args()
    forced = {k: int(v) for k, v in (x.split('=') for x in a.set_mat)}

    src = open(a.exported, encoding='latin-1').read().split('\n')
    _, _, src_objs = read_objects(src)
    names = [obj_name(b) for b in src_objs]

    tgt = open(a.target, encoding='latin-1', newline='').read()
    nl = '\r\n' if '\r\n' in tgt else '\n'
    lines = tgt.split(nl)
    header, world, objs = read_objects(lines)
    # an object that replaces an existing one keeps the material index and the surface flags of the original
    # (KingAir.ac is two-sided, SURF 0X30, and its normals are not consistently oriented; the Blender exporter
    # writes one-sided SURF 0X10)
    old_mat = {}; old_surf = {}
    for b in objs:
        flags = collections.Counter(l.split()[1] for l in b if l.startswith('SURF '))
        if flags:
            old_surf[obj_name(b)] = flags.most_common(1)[0][0]
        for l in b:
            if l.startswith('mat '):
                old_mat[obj_name(b)] = int(l.split()[1]); break
    new = [clean(b, forced.get(obj_name(b), old_mat.get(obj_name(b), a.mat)), old_surf.get(obj_name(b))) for b in src_objs]
    removed = [obj_name(b) for b in objs if obj_name(b) in a.remove and obj_name(b) not in names]
    objs = [b for b in objs if obj_name(b) not in removed]
    kept = [b for b in objs if obj_name(b) not in names]
    replaced = len(objs) - len(kept)
    objs = kept + new
    world[-1] = 'kids %d' % len(objs)
    out = header + world
    for b in objs:
        out += b
    open(a.target, 'w', encoding='latin-1', newline='').write(nl.join(out) + nl)
    print('%s: %d objects (%d replaced, %d added%s): %s' % (os.path.relpath(a.target), len(objs), replaced,
                                                            len(new) - replaced,
                                                            ', removed ' + ', '.join(removed) if removed else '',
                                                            ', '.join(names)))


if __name__ == '__main__':
    main()
