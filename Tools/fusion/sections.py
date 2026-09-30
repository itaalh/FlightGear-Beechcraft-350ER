"""Draws plane sections of AC3D models (PNG, PIL) to measure the cockpit envelope.

python sections.py out_prefix model.ac[:obj1,obj2] ... [--x -4.9,-4.6] [--y -0.34,0] [--z 0.3,0.5]
Each --x station gives a y-z section, each --y a x-z section, each --z a x-y section. Colours per file.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import ac3d

COLORS = [(40, 40, 40), (200, 40, 40), (40, 90, 220), (20, 150, 60), (180, 110, 0)]


def load(spec):
    path, _, names = spec.partition(":")
    names = set(n for n in names.split(",") if n)
    ac = ac3d.read_ac(path)
    tris = []
    for o, loc in ac3d.walk(ac.world):
        if not o.verts or (names and o.name not in names):
            continue
        vs = [ac3d.ac_to_model((v[0] + loc[0], v[1] + loc[1], v[2] + loc[2])) for v in o.verts]
        for flags, mat, refs in o.surfs:
            if flags & 0xF:
                continue
            idx = [r[0] for r in refs]
            for k in range(1, len(idx) - 1):
                tris.append((vs[idx[0]], vs[idx[k]], vs[idx[k + 1]]))
    return tris


def slice_tris(tris, axis, c):
    """Segments of the intersection with the plane coord[axis] = c, in the two other coordinates."""
    others = [i for i in range(3) if i != axis]
    segs = []
    for t in tris:
        d = [p[axis] - c for p in t]
        pts = []
        for i in range(3):
            a, b = t[i], t[(i + 1) % 3]
            da, db = d[i], d[(i + 1) % 3]
            if (da < 0) != (db < 0):
                s = da / (da - db)
                pts.append(tuple(a[j] + s * (b[j] - a[j]) for j in others))
        if len(pts) == 2:
            segs.append(pts)
    return segs


def draw(out, sets, axis, c, lo, hi, scale=900):
    w = int((hi[0] - lo[0]) * scale) + 80
    h = int((hi[1] - lo[1]) * scale) + 80
    img = Image.new("RGB", (w, h), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)

    def P(p):
        return (40 + (p[0] - lo[0]) * scale, h - 40 - (p[1] - lo[1]) * scale)

    # grid every 0.1 m
    g = [round(lo[0] - lo[0] % 0.1, 3), round(lo[1] - lo[1] % 0.1, 3)]
    x = g[0]
    while x <= hi[0] + 1e-9:
        dr.line([P((x, lo[1])), P((x, hi[1]))], fill=(225, 225, 225))
        dr.text(P((x, lo[1])), "%.1f" % x, fill=(120, 120, 120), font=font)
        x += 0.1
    y = g[1]
    while y <= hi[1] + 1e-9:
        dr.line([P((lo[0], y)), P((hi[0], y))], fill=(225, 225, 225))
        dr.text(P((lo[0], y)), "%.1f" % y, fill=(120, 120, 120), font=font)
        y += 0.1
    for k, tris in enumerate(sets):
        for s in slice_tris(tris, axis, c):
            dr.line([P(s[0]), P(s[1])], fill=COLORS[k % len(COLORS)], width=2)
    names = "xyz"
    others = [names[i] for i in range(3) if i != axis]
    dr.text((10, 10), "%s = %.3f   (horizontal %s, vertical %s)" % (names[axis], c, others[0], others[1]),
            fill=(0, 0, 0), font=font)
    img.save(out)
    print(out)


def main():
    args = sys.argv[1:]
    prefix = args.pop(0)
    stations = {"--x": [], "--y": [], "--z": []}
    specs = []
    while args:
        a = args.pop(0)
        if a in stations:
            stations[a] = [float(v) for v in args.pop(0).split(",")]
        else:
            specs.append(a)
    sets = [load(s) for s in specs]
    box = {"x": (-5.1, -3.4), "y": (-0.9, 0.9), "z": (-0.7, 1.0)}
    for c in stations["--x"]:
        draw("%s_x%.2f.png" % (prefix, c), sets, 0, c, (box["y"][0], box["z"][0]), (box["y"][1], box["z"][1]))
    for c in stations["--y"]:
        draw("%s_y%.2f.png" % (prefix, c), sets, 1, c, (box["x"][0], box["z"][0]), (box["x"][1], box["z"][1]))
    for c in stations["--z"]:
        draw("%s_z%.2f.png" % (prefix, c), sets, 2, c, (box["x"][0], box["y"][0]), (box["x"][1], box["y"][1]))


if __name__ == "__main__":
    main()
