"""Level flight (clean, 1700 rpm, default load ~13 500 lb): elevator (= pitch trim), power lever and blade angle vs
KCAS for one altitude. Source of the LEVEL_* tables of Nasal/kingair350.nas (start in the air).
Usage: python t_level.py <altitude ft>   (1000, 10000, 20000, 28000)"""
import sys
from sim2 import mk, Hold
alt = int(sys.argv[1])
out = []
for v in [100, 110, 120, 130, 150, 170, 190, 210, 230, 250]:
    f = mk(alt, v, 0, 0, thr=0.5)
    c = Hold(f, alt)                       # altitude with elevator, wings level; speed with a slow PI on the power lever
    dt = f['simulation/dt']; it = 0.0; t = 0.0; hist = []
    while t < 240:
        ve = v - f['velocities/vc-kts']; it = max(-150, min(150, it + ve * dt))
        c.thr = max(0.0, min(1.0, 0.5 + 0.03 * ve + 0.004 * it)); c.step(); t += dt
        if t > 200: hist.append((f['fcs/elevator-cmd-norm'], c.thr, f['propulsion/engine[0]/blade-angle'], f['velocities/vc-kts'], f['position/h-sl-ft']))
    n = len(hist); e = sum(h[0] for h in hist) / n; th = sum(h[1] for h in hist) / n; b = sum(h[2] for h in hist) / n
    ok = all(abs(h[3] - v) < 1.5 for h in hist) and all(abs(h[4] - alt) < 50 for h in hist) and 0.001 < th < 0.999
    out.append(f"{v}:{'' if ok else '!'}e{e:+.3f} t{th:.2f} b{b:4.1f}")
print(f"{alt:6d} ft: " + "  ".join(out) + "   (! = not held: stall or power limit)")
