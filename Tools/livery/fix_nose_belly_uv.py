#!/usr/bin/env python3
"""Realign the UVs of the lower-left fuselage strip beside the nose-gear doors on the doors' mapping.

In Models/KingAir.ac the belly skin of the Fuselage just outboard of the nose-gear doors (left side, texture rows
v 0.62-0.63 of the left fuselage island) shares its texels with GearDoorFront.Open1 / GearsDoorFront.Closed, but
with a mapping offset by about 7.5 cm in x (u = 0.8715 + 0.0681 (-5.181 - x) for the fuselage against
u = 0.8777 + 0.0707 (-5.349 - x) for the doors). The livery painter (alsr.py) can only paint those texels for one
of the two, and paints them for the doors: the propeller band then showed a 7.5 cm jog on the fuselage strip.
This script gives the strip the doors' mapping, so that both objects agree and the band is straight; the livery
does not need to be regenerated. Run once:

    python fix_nose_belly_uv.py            # edits Models/KingAir.ac in place, idempotent
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
AC = os.path.normpath(os.path.join(HERE, '..', '..', 'Models', 'KingAir.ac'))


def door_u(x):
    return 0.8777 + 0.0707 * (-5.349 - x)


def main():
    raw = open(AC, 'rb').read()
    nl = b'\r\n' if b'\r\n' in raw else b'\n'
    lines = raw.decode('latin-1').split(nl.decode())
    i = 0; name = None; verts = []; changed = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('name '):
            name = l.split('"')[1]
        elif l.startswith('numvert'):
            nv = int(l.split()[1])
            verts = [tuple(float(t) for t in lines[i + 1 + j].split()[:3]) for j in range(nv)]
            i += nv
        elif l.startswith('numsurf') and name == 'Fuselage':
            ns = int(l.split()[1]); i += 1
            for _ in range(ns):
                while not lines[i].startswith('refs'):
                    i += 1
                nr = int(lines[i].split()[1]); first = i + 1
                refs = [lines[first + k].split() for k in range(nr)]
                pts = [(verts[int(r[0])], float(r[1]), float(r[2])) for r in refs]
                # left island (u >= 0.84), rows of the strip (v <= 0.6295), within the doors' x range, left side (z > 0)
                if all(u >= 0.84 and v <= 0.6295 for _, u, v in pts) and \
                        all(-6.7 <= p[0] <= -4.75 and p[2] > 0 for p, _, _ in pts):
                    for k, r in enumerate(refs):
                        x = verts[int(r[0])][0]
                        new_u = door_u(x)
                        if abs(new_u - float(r[1])) > 1e-6:
                            lines[first + k] = '%s %.6f %s' % (r[0], new_u, r[2]); changed += 1
                i = first + nr
            continue
        i += 1
    if changed:
        open(AC, 'wb').write(nl.decode().join(lines).encode('latin-1'))
    print('%s: %d surface refs remapped' % (os.path.relpath(AC), changed))


if __name__ == '__main__':
    main()
