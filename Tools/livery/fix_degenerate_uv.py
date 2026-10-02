"""Give every textured polygon a non-zero UV area.
With the normal map enabled, FlightGear/OSG derive tangents from the UVs; polygons whose UVs collapse to a point
or a line (flaps, flap strips, gear pistons, most of the nose cone, a few slivers) get no tangent and render black.
Each degenerate polygon gets a sub-texel 'wobble' (0.6 texel at 4096) so the sampled colour does not change."""
import numpy as np, sys

SRC, DST = sys.argv[1], sys.argv[2]
DELTA = 0.00015
lines = open(SRC, encoding='latin-1').read().split('\n')
out = []; i = 0; textured = False; name = None; fixed = {}
while i < len(lines):
    l = lines[i]
    if l.startswith('OBJECT'):
        textured = False; name = None
    elif l.startswith('name '):
        name = l[5:].strip().strip('"')
    elif l.startswith('texture '):
        textured = True
    if l.startswith('refs ') and textured:
        n = int(l.split()[1])
        refs = [lines[i + 1 + k].split() for k in range(n)]
        uv = np.array([[float(r[1]), float(r[2])] for r in refs])
        degenerate = False
        for k in range(1, n - 1):
            a = uv[k] - uv[0]; b = uv[k + 1] - uv[0]
            if abs(a[0] * b[1] - a[1] * b[0]) < 1e-9:
                degenerate = True
                break
        out.append(l)
        if degenerate and n >= 3:
            for k, r in enumerate(refs):
                t = 2 * np.pi * k / n
                out.append(f'{r[0]} {uv[k,0] + DELTA * np.cos(t):.6f} {uv[k,1] + DELTA * np.sin(t):.6f}')
            fixed[name] = fixed.get(name, 0) + 1
        else:
            out.extend(lines[i + 1:i + 1 + n])
        i += 1 + n
        continue
    out.append(l); i += 1
open(DST, 'w', encoding='latin-1').write('\n'.join(out))
print('polygons fixed:', fixed)
