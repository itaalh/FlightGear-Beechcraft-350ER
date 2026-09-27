"""Rolling moment recovered by the wing from the propeller slipstream swirl (King Air 350, both propellers
clockwise seen from behind). Weissinger lifting line (horseshoe vortices at c/4, control points at 3c/4), full
span, swirl incidence change dalpha(y) = -sign(y - yp) * v_theta(|y - yp|) / Va behind each propeller.
Result expressed as a fraction of the total propeller torque (2 Q)."""
import numpy as np, math

b = 57.92; s = b / 2; c_root, c_tip = 7.2, 3.9          # ft (MAC ~ 5.8 ft)
yp = 109.1 / 12; R = 105 / 2 / 12; r_nac = 1.2           # ft
chord = lambda y: c_root + (c_tip - c_root) * abs(y) / s

N = 400
yb = -s + (s * 2) * (0.5 * (1 - np.cos(np.linspace(0, math.pi, N + 1))))   # cosine spacing, panel edges
yc = 0.5 * (yb[:-1] + yb[1:]); dy = np.diff(yb)
cc = np.array([chord(y) for y in yc])

def seg3(P, A, B):
    """velocity induced at P by a unit vortex segment A -> B (Biot-Savart)."""
    r1 = P - A; r2 = P - B; r0 = B - A
    cr = np.cross(r1, r2); n = cr @ cr
    if n < 1e-10: return np.zeros(3)
    return cr / (4 * math.pi * n) * (r0 @ (r1 / np.linalg.norm(r1) - r2 / np.linalg.norm(r2)))

FAR = 1e5
A = np.zeros((N, N))
for i in range(N):
    P = np.array([0.75 * cc[i], yc[i], 0.0])
    for j in range(N):
        x0 = 0.25 * cc[j]
        a = np.array([x0, yb[j], 0.0]); bb = np.array([x0, yb[j + 1], 0.0])
        w = seg3(P, np.array([FAR, yb[j], 0.0]), a) + seg3(P, a, bb) + seg3(P, bb, np.array([FAR, yb[j + 1], 0.0]))
        A[i, j] = w[2]
S_w = np.sum(cc * dy)
g = np.linalg.solve(A, -np.ones(N) * 1.0 * 0.1)        # V = 1, alpha = 0.1 rad
print(f"check: wing area {S_w:.1f} ft2, CL_alpha = {np.sum(g * dy) * 2 / S_w / 0.1:.2f} /rad (theory ~5.2 for AR 10.8)")

def run(profile, V=361.0, Va=382.0, Q=3244.0, rho=0.00187):
    x = np.linspace(0.2, 1.0, 400); vt = profile(x)
    # scale v_theta so that the swirl carries the torque: Q = int rho Va v_theta r 2 pi r dr
    Qunit = np.trapezoid(rho * Va * vt * (x * R) ** 2 * 2 * math.pi, x * R)
    k = Q / Qunit
    def vtheta(d):
        d = np.abs(d) / R
        return np.where((d * R > r_nac) & (d <= 1.0), k * np.interp(d, x, vt, left=0, right=0), 0.0)
    dalpha = np.zeros(N)
    for side in (-1, 1):
        d = yc - side * yp
        dalpha += -np.sign(d) * vtheta(d) / Va
    # flow tangency: w_induced + V * dalpha = 0 at the control points (A = upward velocity per unit gamma)
    gam = np.linalg.solve(A, -V * dalpha)
    dL = rho * V * gam * dy
    L_roll = -np.sum(dL * yc)           # positive = right wing down
    return L_roll / (2 * Q), np.max(np.abs(np.degrees(dalpha)))

profiles = {
    "Gamma const (v ~ 1/r)": lambda x: 1 / x * np.clip((x - 0.2) / 0.1, 0, 1) * np.clip((1 - x) / 0.08, 0, 1),
    "Gamma ~ x(1-x)":        lambda x: (x - 0.2) * (1 - x) / x,
    "solid body":            lambda x: x * np.clip((1 - x) / 0.08, 0, 1),
}
for name, p in profiles.items():
    for V, Va in ((361, 382), (190, 225)):
        frac, amax = run(p, V=V, Va=Va)
        print(f"{name:24s} V {V} fps: wing recovers {frac * 100:5.1f} % of the propeller torque (max swirl {amax:4.1f} deg)")
