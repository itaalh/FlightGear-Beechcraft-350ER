"""Procedural surface detail for the King Air: panel joints (grooves), flush-rivet rows and access panels,
defined in model space and evaluated per texel. Returns a height map (metres) and a groove AO term."""
import numpy as np

GD = 0.0008    # groove depth (m)
GW = 0.0030    # groove half-width (gaussian sigma, m)
RH = 0.00018   # rivet row height
RW = 0.0028    # rivet row sigma
AO_K = 0.055   # darkening at the bottom of a joint


def groove(dist):
    e = np.exp(-(dist / GW) ** 2)
    return -GD * e, AO_K * e


def rivets(dist_row, along, pitch, h=RH):
    """modulated ridge: continuous enough to survive texture sampling, dotted at close range."""
    return h * np.exp(-(dist_row / RW) ** 2) * (0.35 + 0.65 * (0.5 + 0.5 * np.cos(2 * np.pi * along / pitch)) ** 3)


def rrect_dist(a, b, a0, a1, b0, b1, r):
    """distance to the outline of a rounded rectangle in (a,b) plane"""
    ca = (a0 + a1) / 2; cb = (b0 + b1) / 2; ha = (a1 - a0) / 2 - r; hb = (b1 - b0) / 2 - r
    qa = np.abs(a - ca) - ha; qb = np.abs(b - cb) - hb
    outside = np.hypot(np.maximum(qa, 0), np.maximum(qb, 0)) + np.minimum(np.maximum(qa, qb), 0)
    return np.abs(outside - r)


def profile_from(verts, axis, bins, keys):
    """min/max per bin of verts along axis"""
    out = {}
    idx = np.digitize(verts[:, axis], bins)
    for k, (col, fn) in keys.items():
        vals = np.full(len(bins) + 1, np.nan)
        for b in np.unique(idx):
            sel = verts[idx == b, col]
            if len(sel): vals[b] = fn(sel)
        ok = ~np.isnan(vals)
        centers = np.concatenate([[bins[0]], (bins[:-1] + bins[1:]) / 2, [bins[-1]]])
        out[k] = (centers[ok], vals[ok])
    return out


def height_map(M):
    S = M.S
    H = np.zeros((S, S), np.float32); AO = np.zeros((S, S), np.float32)
    d = M.data

    def run(names, fn):
        m = M.objmask(names)
        ii, jj = np.nonzero(m)
        p = M.pos[ii, jj].astype(np.float64); n = M.nrm[ii, jj]
        h, ao = fn(p[:, 0], p[:, 1], p[:, 2], n)
        H[ii, jj] += h; AO[ii, jj] = np.maximum(AO[ii, jj], ao)

    # ---------------- fuselage
    fm_ = M.objmask(['Fuselage'])
    FV = M.pos[fm_][::7].astype(np.float64)          # dense surface samples (the mesh has long faces)
    bins = np.arange(-7.1, 7.2, 0.05)
    pr = profile_from(FV, 0, bins, {'ymin': (1, np.min), 'ymax': (1, np.max), 'zmax': (2, lambda v: np.max(np.abs(v)))})
    from scipy.ndimage import median_filter, uniform_filter1d
    for k in pr:
        xs_, vs_ = pr[k]
        vs_ = uniform_filter1d(median_filter(vs_, 9, mode='nearest'), 5, mode='nearest')
        pr[k] = (xs_, vs_)
    def fus(x, y, z, n):
        ymin = np.interp(x, *pr['ymin']); ymax = np.interp(x, *pr['ymax']); zmax = np.interp(x, *pr['zmax'])
        yc = (ymin + ymax) / 2; hy = np.maximum((ymax - ymin) / 2, 0.05); hz = np.maximum(zmax, 0.05)
        th = np.arctan2((y - yc) / hy, np.abs(z) / hz)
        r = 0.5 * (hy + hz); g = th * r
        h = np.zeros_like(x); ao = np.zeros_like(x)
        on_body = (x > -6.60) & (x < 6.9)
        # circumferential skin joints
        for xs in [-6.05, -4.86, -3.36, -1.745, -0.27, 1.26, 2.07, 3.02, 3.96, 4.86, 5.62]:
            gh, ga = groove(x - xs); h += gh * on_body; ao = np.maximum(ao, ga * on_body)
            for off in (-0.016, 0.016):
                h += rivets(x - xs - off, g, 0.028) * on_body
        # frames (single rivet rows)
        for xf in np.arange(-5.45, 5.6, 0.5):
            if min(abs(xf - v) for v in [-4.86, -3.36, -1.745, -0.27, 1.26, 2.07, 3.02, 3.96, 4.86]) < 0.12:
                continue
            h += rivets(x - xf, g, 0.032, RH * 0.7) * on_body
        # longitudinal lap joints (both sides), cabin and tail cone only
        lap = (x > -4.70) & (x < 5.40)
        for thl in np.radians([50.0, -3.0, -47.0]):
            gl = thl * r
            gh, ga = groove(g - gl); h += gh * lap; ao = np.maximum(ao, ga * lap)
            h += rivets(g - gl - 0.013, x, 0.030) * lap
        # top and belly butt joints
        top = np.abs(z) < 0.012 + 0 * x
        gh, ga = groove(np.abs(z)); msk = (y > yc) & on_body & (x > -4.8) & (x < 4.6)
        h += gh * msk; ao = np.maximum(ao, ga * msk)
        msk = (y < yc) & on_body & (x > -4.7) & (x < 5.2)
        h += gh * msk; ao = np.maximum(ao, ga * msk)
        # left emergency hatch outline (deactivated exit) around the second cabin window
        left = z > 0
        dh = rrect_dist(x, y, -2.66, -2.16, 0.175, 0.840, 0.07)
        gh, ga = groove(dh); h += gh * left; ao = np.maximum(ao, ga * left)
        # belly access panels with screws
        for (a0, a1) in [(-1.25, -0.80), (2.35, 2.80), (-4.35, -4.00)]:
            m = (y < yc - 0.6 * hy)
            dh = rrect_dist(x, z, a0, a1, -0.14, 0.14, 0.03)
            gh, ga = groove(dh); h += gh * m; ao = np.maximum(ao, ga * m)
        # nose avionics access panels (both sides, below the vent grille)
        m = (np.abs(z) > 0.3)
        dh = rrect_dist(x, y, -6.45, -6.25, -0.52, -0.36, 0.025)
        gh, ga = groove(dh); h += gh * m; ao = np.maximum(ao, ga * m)
        # only on the outer skin: window tunnels / rims and other faces not facing outwards get no detail
        rn = np.stack([np.zeros_like(x), (y - yc) / hy ** 2, z / hz ** 2], -1)
        rn /= np.linalg.norm(rn, axis=1, keepdims=True) + 1e-9
        wgt = np.clip((np.abs(np.sum(rn * n, 1)) - 0.70) / 0.15, 0, 1)
        return h * wgt, ao * wgt
    run(['Fuselage'], fus)

    # ---------------- wings (+ailerons)
    WV = d['Wings'][0].reshape(-1, 3)
    def wing(x, y, z, n):
        s = np.abs(z); top = n[:, 1] >= 0
        h = np.zeros_like(x); ao = np.zeros_like(x)
        outer = s > 3.35; inner = (s > 0.9) & (s < 2.35)
        x_fs = np.where(outer, -2.28, -2.72)
        x_rs = np.where(s >= 5.25, -1.33 - (s - 5.25) / 3.5 * 0.50, -1.10)
        span_ok = outer | inner
        for xs_ in (x_fs, x_rs):
            for off in (-0.012, 0.012):
                h += rivets(x - xs_ - off, s, 0.030) * span_ok
        # ribs
        for sr in list(np.arange(3.6, 8.7, 0.45)) + [1.30, 1.75, 2.15]:
            m = span_ok & (x > x_fs - 0.03) & (x < x_rs + 0.03)
            h += rivets(s - sr, x, 0.034) * m
        # spanwise skin joint on the upper surface, chordwise splice
        x_mid = (x_fs + x_rs) / 2 + 0.08
        gh, ga = groove(x - x_mid); m = top & outer
        h += gh * m; ao = np.maximum(ao, ga * m)
        gh, ga = groove(s - 5.95); m = outer & (x > -2.38) & (x < x_rs)
        h += gh * m; ao = np.maximum(ao, ga * m)
        # lower surface fuel-tank / inspection covers with screws
        bot = ~top
        for sc in [3.95, 4.90, 5.85, 6.80, 7.75]:
            dh = rrect_dist(x, s, -2.10, -1.80, sc - 0.09, sc + 0.09, 0.03)
            gh, ga = groove(dh); h += gh * bot; ao = np.maximum(ao, ga * bot)
            ang = np.arctan2(s - sc, (x + 1.95) / 1.6)
            ring = np.abs(np.hypot((x + 1.95) / 1.6, s - sc) - 0.085)
            h += rivets(ring, ang * 0.085, 0.085 * 2 * np.pi / 12, RH * 1.2) * bot
        return h, ao
    run(['Wings'], wing)

    def aileron(x, y, z, n):
        s = np.abs(z); h = np.zeros_like(x)
        for sr in np.arange(5.35, 8.8, 0.20):
            h += rivets(s - sr, x, 0.025, RH * 0.8)
        return h, np.zeros_like(x)
    run(['AileronsLeft', 'AileronsRigth', 'ElevatorsLeft', 'ElevatorsRight'], aileron)

    # ---------------- nacelles
    NV = np.concatenate([d[k][0].reshape(-1, 3) for k in ['FrontEngineCowls', 'MidEngineCowls', 'LowerEngCowls', 'WngCowl']])
    NV = NV[NV[:, 2] > 0]
    ycn = (NV[:, 1].min() + NV[:, 1].max()) / 2; zcn = (NV[:, 2].min() + NV[:, 2].max()) / 2
    def nacelle(x, y, z, n):
        az = np.abs(z)
        phi = np.arctan2(y - ycn, az - zcn); rr = np.hypot(y - ycn, az - zcn); arc = phi * np.maximum(rr, 0.2)
        h = np.zeros_like(x); ao = np.zeros_like(x)
        # side seams (mid height, outboard and inboard) and top seam
        for ph in (0.0, np.pi, np.pi / 2):
            dphi = np.angle(np.exp(1j * (phi - ph)))
            dd = dphi * np.maximum(rr, 0.2)
            m = (x > -5.05) & (x < -1.0)
            gh, ga = groove(dd); h += gh * m; ao = np.maximum(ao, ga * m)
            h -= rivets(dd - 0.018, x, 0.065, RH * 1.3) * m     # camlock dimples
        for xs in (-4.48, -3.49, -2.62):
            gh, ga = groove(x - xs); h += gh; ao = np.maximum(ao, ga)
            h -= rivets(x - xs - 0.018, arc, 0.065, RH * 1.3)
        return h, ao
    run(['FrontEngineCowls', 'MidEngineCowls', 'LowerEngCowls', 'TopEngineCowl', 'WngCowl', 'FrontCowls'], nacelle)

    # ---------------- fin / rudder
    def fin(x, y, z, n):
        h = np.zeros_like(x)
        le = 4.271 + (y - 1.994) * 0.854
        hinge = 4.88 + (y - 1.332) * 0.693
        m = (y > 1.35)
        for xs_ in (le + 0.10, hinge - 0.045):
            h += rivets(x - xs_, y, 0.030) * m
        for yr in (1.62, 1.92, 2.22, 2.50):
            h += rivets(y - yr, x, 0.032) * m * (x > le + 0.05)
        return h, np.zeros_like(x)
    run(['VertStab', 'Rudder'], fin)

    def stab(x, y, z, n):
        s = np.abs(z); h = np.zeros_like(x)
        for xs_ in (5.00 + s * 0.12, 5.86):
            h += rivets(x - xs_, s, 0.028)
        for sr in np.arange(0.45, 3.0, 0.40):
            h += rivets(s - sr, x, 0.030) * (x < 5.9)
        return h, np.zeros_like(x)
    run(['Horstab'], stab)

    return H, np.clip(AO, 0, 0.2)


def normal_map(M, H, gloss, chunk=256):
    """tangent-space normal map (OpenGL convention, green = +v) from a metric height map; alpha = gloss.
    Processed in row blocks to keep memory low."""
    S = M.S
    used = M.obj >= 0
    out = np.empty((S, S, 4), np.uint8)
    for r0 in range(0, S, chunk):
        a0 = max(r0 - 1, 0); a1 = min(r0 + chunk + 1, S)
        P = M.pos[a0:a1].astype(np.float32); O = M.obj[a0:a1]; Hh = H[a0:a1]
        # neighbours (edge-replicated)
        def nb(a, di, dj):
            b = np.roll(a, (di, dj), (0, 1))
            return b
        du = np.linalg.norm(nb(P, 0, -1) - nb(P, 0, 1), axis=-1) / 2
        dv = np.linalg.norm(nb(P, -1, 0) - nb(P, 1, 0), axis=-1) / 2
        same_u = (nb(O, 0, -1) == O) & (nb(O, 0, 1) == O)
        same_v = (nb(O, -1, 0) == O) & (nb(O, 1, 0) == O)
        aniso = np.maximum(du, dv) / np.maximum(np.minimum(du, dv), 1e-6)
        ok_u = same_u & (du > 1e-5) & (du < 0.05) & (aniso < 3)
        ok_v = same_v & (dv > 1e-5) & (dv < 0.05) & (aniso < 3)
        gu = np.where(ok_u, (nb(Hh, 0, -1) - nb(Hh, 0, 1)) / 2 / np.maximum(du, 1e-5), 0)
        gv = np.where(ok_v, -(nb(Hh, -1, 0) - nb(Hh, 1, 0)) / 2 / np.maximum(dv, 1e-5), 0)
        gu = np.clip(gu, -0.6, 0.6); gv = np.clip(gv, -0.6, 0.6)
        l = np.sqrt(gu * gu + gv * gv + 1)
        rgb = np.stack([-gu / l, -gv / l, 1 / l], -1) * 0.5 + 0.5
        blk = np.concatenate([rgb, gloss[a0:a1][..., None]], -1)
        blk = (blk * 255 + 0.5).astype(np.uint8)
        blk[O < 0] = (128, 128, 255, 255)
        # first/last rows of the block are halo (except at the texture border)
        s0 = r0 - a0; s1 = s0 + min(chunk, S - r0)
        out[r0:r0 + (s1 - s0)] = blk[s0:s1]
    # the halo rows at the very top/bottom of the texture used wrapped neighbours: neutralise them
    out[0] = out[1]; out[-1] = out[-2]
    return out
