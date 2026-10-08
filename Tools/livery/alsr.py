"""Paint the French Air and Space Force ALSR 'Vador' livery (serial 1030, F-RACH) for the King Air 350ER and the
normal map shared by all liveries.

    python3 alsr.py                 # writes Models/Liveries/ALSR.png and Models/Effects/KingAir-350-normalmap.png
    python3 alsr.py --out /tmp/x    # writes into another folder

All positions are model coordinates (AC3D frame: x aft, y up, z left, metres), measured on photographs of the
aircraft projected onto the 3D model (see README.md in this folder). Requirements: numpy, scipy, pillow, numba,
opencv-python (only for the fill), the DINish fonts (DINISH_DIR)."""
import os, argparse, numpy as np, time
from PIL import Image
import paint_lib as L
from maps import Maps, load_model, MODELS
from panels import height_map, normal_map

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=None, help='output folder (default: the aircraft Models/ folders)')
ap.add_argument('--size', type=int, default=4096)
args = ap.parse_args()

T0 = time.time()
M = Maps(load_model(), size=args.size)

S = M.S
used = M.obj >= 0
pos = M.pos; nrm = M.nrm
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]

def c(rgb):
    return np.array(rgb, np.float32) / 255.0

WHITE = c((238, 238, 236))
GREY = c((170, 173, 176))          # low-visibility markings grey (measured ~0.73 x white)
RED_R = c((200, 28, 44))           # roundel red
BLUE_R = c((22, 52, 122))          # roundel blue
YELLOW = c((236, 184, 34))         # roundel outline
RED = c((204, 30, 36))             # propeller band, DANGER, door arrow, exit text
BLACK = c((30, 30, 32))
RUBBER = c((38, 38, 40))
GEARGREY = c((196, 197, 196))

FUS = ['Fuselage', 'MainEntrance', 'MainEntranceTrim', 'FrontCargoDoorLeft', 'FrontCargoDoorRight',
       'FrontCargoDoorStripsLeft', 'FrontCargoDoorStripsRight', 'NoseCone', 'NoseConeStrips',
       'GearsDoorFront.Closed', 'GearDoorFront.Open1', 'GearDoorFront.Open2', 'WindowPlugL1']
FIN = ['VertStab', 'Rudder']
WING = ['Wings', 'AileronsLeft', 'AileronsRigth', 'AiltrimtabLeft', 'AiltrimtabsRight']
KEEP = ['PropLeft', 'PropRight', 'PropConeLeft', 'PropConeRight', 'PropCone', 'PropConeDisks',
        'TiresFront', 'TiresLeft', 'TiresRight', 'FuelCaps', 'WingLightsLeft', 'WingLightsRight', 'TailLight']
WHEELS = ['WheelsFront', 'WheelsLeft', 'WheelsRight']
GEAR = ['AxleshaftsFront', 'AxleshaftsLeft', 'AxleshaftsRight', 'TorqueLinksFront', 'TorqueLinksLeft',
        'TorqueLinksRight', 'TorqueLinksLeft2', 'TorqueLinksLeft3', 'TorqueLinksRight2', 'TorqueLinkBoltsFront',
        'TorqueLinkBoltsLeft', 'TorqueLinkBoltsRight', 'TrunnionFront', 'TrunnionLeft', 'TrunnionRight',
        'LGPistonFront', 'LGPistonLeft', 'LGPistonRight']
BOOTS = ['DeicebootsWings', 'DeicebootsHorizStab']
EXHAUST = ['Exhaust']
NACELLE = ['FrontCowls', 'FrontEngineCowls', 'MidEngineCowls', 'LowerEngCowls', 'TopEngineCowl', 'WngCowl', 'EngCowlStrips']

# ------------------------------------------------------------------ base
tex = np.zeros((S, S, 3), np.float32)
tex[:] = WHITE
proto = np.asarray(Image.open(os.path.join(MODELS, 'prototype.png')).convert('RGB')
                   .resize((S, S), Image.LANCZOS)).astype(np.float32) / 255.0
m = M.objmask(KEEP); tex[m] = proto[m]
m = M.objmask(WHEELS); tex[m] = np.clip(proto[m] * 2.5, 0, 0.82)
m = M.objmask(GEAR); tex[m] = GEARGREY
m = M.objmask(BOOTS); tex[m] = RUBBER
# exhaust stacks: heat-stained steel, darker towards the outlet (aft end)
m = M.objmask(EXHAUST)
fx = np.clip((x[m] + 5.05) / 0.55, 0, 1)[:, None]
tex[m] = c((128, 118, 106)) * (1 - fx) + c((52, 46, 42)) * fx

paint = used & ~M.objmask(KEEP + WHEELS + GEAR + BOOTS + EXHAUST)

# subtle paint variation (large, soft) so the white is not flat
n1 = L.value_noise(S, 6, 1, octaves=3)
n2 = L.value_noise(S, 48, 2, octaves=2)
var = 1.0 + 0.010 * n1 + 0.004 * n2
tex[paint] *= var[paint][:, None]
print('base', time.time() - T0)

# ------------------------------------------------------------------ helpers
EX = np.array([1.0, 0, 0]); EY = np.array([0, 1.0, 0]); EZ = np.array([0, 0, 1.0])

def side_mask(objs, side, thr=0.25):
    """side=+1 left (z>0, facing +z), -1 right."""
    return M.objmask(objs) & (side * z > 0) & (side * nrm[..., 2] > thr)

def decal(cv, origin, d, u, mask):
    a = cv.finish()
    return L.project(tex, M, a, cv, origin, d, u, mask)

def frame(side):
    """reading direction and up vector for a vertical surface seen from the given side."""
    return (EX if side > 0 else -EX), EY

# ------------------------------------------------------------------ fuselage registration F-RACH
# left side, measured letter centres (x) and extents: F 1.202-1.406, - 1.47-1.674, R 1.73-1.924,
# A 1.99-2.21, C 2.257-2.47, H 2.498-2.711 ; baseline y 0.008, cap height 0.334
REG_X0, REG_X1 = 1.202, 2.711
REG_CAP, REG_BASE = 0.334, 0.008
reg_centres = [('F', 1.304), ('-', 1.572), ('R', 1.827), ('A', 2.100), ('C', 2.363), ('H', 2.605)]

def registration(side):
    d, u = frame(side)
    cv = L.Canvas2D(-0.05, 1.56, -0.05, 0.40, res=600)
    # canvas s measured from REG_X0 along the reading direction
    # same distance from the start of the string on both sides; on the right side the string starts
    # at the aft end (REG_X1) and reads forward, so the roundel sits next to the F there (photo of 1018)
    for ch, xc in reg_centres:
        s = xc - REG_X0
        chr_ = ch
        if chr_ == '-':
            w = 0.204; th = 0.045
            cv.rect(s - w / 2, 0.165 - th / 2 - REG_BASE, s + w / 2, 0.165 + th / 2 - REG_BASE, tuple(int(v * 255) for v in GREY) + (255,))
        else:
            cv.glyph(s, 0.0, chr_, REG_CAP, tuple(int(v * 255) for v in GREY) + (255,), 'Medium', stretch=0.93)
    origin = np.array([REG_X0 if side > 0 else REG_X1, REG_BASE, 0.0])
    return decal(cv, origin, d, u, side_mask(FUS, side))

# ------------------------------------------------------------------ roundel
def roundel_canvas(R):
    cv = L.Canvas2D(-R - 0.01, R + 0.01, -R - 0.01, R + 0.01, res=1000)
    for rr, col in [(1.0, YELLOW), (0.9, RED_R), (0.6, WHITE), (0.3, BLUE_R)]:
        cv.ellipse(0, 0, rr * R, rr * R, color=tuple(int(v * 255) for v in col) + (255,))
    return cv

def fus_roundel(side):
    cv = roundel_canvas(0.1675)
    d, u = frame(side)
    return decal(cv, np.array([3.115, 0.378, 0]), d, u, side_mask(FUS, side))

# ------------------------------------------------------------------ static-port box, small plates
def static_port(side, with_square):
    d, u = frame(side)
    cv = L.Canvas2D(-0.05, 1.45, -0.10, 0.55, res=1000)
    k = tuple(int(v * 255) for v in BLACK) + (255,)
    x0, x1, y0, y1 = 2.148, 2.782, -0.025, 0.467
    arm, th = 0.036, 0.009
    def S_(xx): return (xx - 2.1) if side > 0 else (2.1 + 1.4 - xx) - 0.0
    # corners in canvas coords: s along reading direction
    xs = [x0, x1]
    for xx in xs:
        s = S_(xx)
        inward = 1 if ((xx == x0) == (side > 0)) else -1   # arm direction along s
        for yy, up in [(y1, -1), (y0, 1)]:
            cv.rect(min(s, s + inward * arm), yy - th / 2, max(s, s + inward * arm), yy + th / 2, k)
            cv.rect(s - th / 2, min(yy, yy + up * arm), s + th / 2, max(yy, yy + up * arm), k)
    # static port plate: small flush plate with three holes
    s = S_(2.476)
    cv.rrect(s - 0.012, 0.162, s + 0.012, 0.240, 0.004, color=(196, 198, 200, 255))
    for yy in (0.178, 0.201, 0.224):
        cv.ellipse(s, yy, 0.0035, 0.0035, color=(40, 40, 42, 255))
    if with_square:
        s = S_(3.51)
        cv.rect(s - 0.022, 0.335, s + 0.022, 0.366, (50, 52, 54, 255))
    origin = np.array([2.1 if side > 0 else 3.5, 0.0, 0.0])
    return decal(cv, origin, d, u, side_mask(FUS, side))

# ------------------------------------------------------------------ ARMEE DE L'AIR
TITLE = "ARMEE DE L'AIR"
def title(side):
    d, u = frame(side)
    cap = 0.178; base = 0.083; x0, x1 = -1.800, -0.070
    cv = L.Canvas2D(-0.05, 1.80, -0.05, 0.25, res=700)
    w0 = cv.text_width(TITLE, cap, 'Medium')
    # ink width ~ advance width minus side bearings; fit tracking so the ink spans x0..x1
    import PIL.ImageFont as IF
    f = IF.truetype(L.font('Medium'), int(round(cv.m(cap) / L.CAP_RATIO)))
    bb0 = f.getbbox(TITLE[0], anchor='ls'); bbN = f.getbbox(TITLE[-1], anchor='ls')
    lsb = bb0[0] / (cv.res * L.SS); rsb = (f.getlength(TITLE[-1]) - bbN[2]) / (cv.res * L.SS)
    ink = w0 - lsb - rsb
    tracking = ((x1 - x0) - ink) / (len(TITLE) - 1)
    cv.tracked_text(-lsb, 0.0, TITLE, cap, tuple(int(v * 255) for v in GREY) + (255,), 'Medium', tracking)
    origin = np.array([x0 if side > 0 else x1, base, 0.0])
    print('title tracking %.4f m' % tracking)
    return decal(cv, origin, d, u, side_mask(FUS, side))

# ------------------------------------------------------------------ left side only: emergency exit, plug ring, door
def emergency_exit():
    d, u = frame(1)
    cv = L.Canvas2D(-0.35, 0.35, -0.02, 0.10, res=2000)
    r = tuple(int(v * 255) for v in RED) + (255,)
    for txt, base, w in [('DEACTIVATED', 0.029, 0.240), ('EMERGENCY EXIT', 0.0, 0.305)]:
        cap = 0.022
        wn = cv.text_width(txt, cap, 'Bold')
        tr = (w - wn) / (len(txt) - 1)
        cv.tracked_text(-w / 2, base, txt, cap, r, 'Bold', tr)
    n = decal(cv, np.array([-2.44, 0.690, 0]), d, u, side_mask(FUS, 1))
    # plugged window: thin dark outline ring just outside the hole
    P = M.data['WindowPlugL1'][0].reshape(-1, 3)
    info = dict(xc=P[:, 0].mean(), yc=P[:, 1].mean(),
                hole_ax=(P[:, 0].max() - P[:, 0].min()) / 2 - 0.006, hole_ay=(P[:, 1].max() - P[:, 1].min()) / 2 - 0.006)
    info['xc'] = (P[:, 0].max() + P[:, 0].min()) / 2; info['yc'] = (P[:, 1].max() + P[:, 1].min()) / 2
    cv = L.Canvas2D(-0.25, 0.25, -0.25, 0.25, res=2000)
    cv.ellipse(0, 0, info['hole_ax'] + 0.003, info['hole_ay'] + 0.003, outline=(58, 58, 60, 255), width=0.0045)
    n += decal(cv, np.array([info['xc'], info['yc'], 0]), d, u, side_mask(['WindowPlugL1', 'Fuselage'], 1))
    return n

def door_marks():
    d, u = frame(1)
    cv = L.Canvas2D(0.30, 1.10, 0.0, 0.45, res=2000)
    r = tuple(int(v * 255) for v in RED) + (255,)
    # flush handle
    cv.rrect(0.713, 0.241, 0.777, 0.276, 0.010, color=(38, 38, 40, 255))
    cv.rrect(0.722, 0.250, 0.768, 0.267, 0.006, color=(70, 72, 74, 255))
    # release button ring
    cv.ellipse(0.797, 0.262, 0.013, 0.013, outline=r, width=0.004)
    # curved red arrow (turn to open)
    cc = (0.815, 0.232); R = 0.128
    cv.arc(cc[0], cc[1], R, 6, -100, r, 0.010)
    a = np.radians(-100); tip = (cc[0] + R * np.cos(a), cc[1] + R * np.sin(a))
    tang = np.array([np.sin(a), -np.cos(a)])      # clockwise tangent
    nrm2 = np.array([np.cos(a), np.sin(a)])
    p0 = np.array(tip) + tang * 0.030
    cv.polygon([tuple(p0), tuple(np.array(tip) - tang * 0.004 + nrm2 * 0.017), tuple(np.array(tip) - tang * 0.004 - nrm2 * 0.017)], r)
    # small instruction lines (placard text)
    cv.text(0.782, 0.352, 'PUSH BUTTON', 0.012, r, 'Bold')
    cv.text(0.782, 0.332, 'TURN HANDLE TO OPEN', 0.012, r, 'Bold')
    return decal(cv, np.array([0.0, 0.0, 0.0]), d, u, side_mask(['MainEntrance', 'MainEntranceTrim', 'Fuselage'], 1))

# ------------------------------------------------------------------ nose: propeller danger band
BAND_X, BAND_W, BAND_TOP = -5.36, 0.075, 0.23
def prop_band():
    m = M.objmask(FUS) & (np.abs(x - BAND_X) < BAND_W / 2 + 0.004) & (y < BAND_TOP + 0.004)
    ii, jj = np.nonzero(m)
    # analytic anti-aliased edges (texel ~3.5 mm)
    e1 = (BAND_W / 2 - np.abs(x[ii, jj] - BAND_X)) / 0.0025
    e2 = (BAND_TOP - y[ii, jj]) / 0.0025
    a = np.clip(np.minimum(e1, e2) * 0.5 + 0.5, 0, 1)[:, None]
    tex[ii, jj] = tex[ii, jj] * (1 - a) + RED * a
    # HELICE, white, reading downwards inside the band, both sides
    n = 0
    for side in (1, -1):
        d = -EY; u = EX if side > 0 else -EX
        cv = L.Canvas2D(-0.01, 0.34, -0.04, 0.04, res=2500)
        cap = 0.042
        txt = 'HELICE'
        wn = cv.text_width(txt, cap, 'Bold'); w = 0.300
        tr = (w - wn) / (len(txt) - 1)
        cv.tracked_text(0.0, -cap / 2, txt, cap, (245, 245, 245, 255), 'Bold', tr)
        n += decal(cv, np.array([BAND_X, -0.330, 0]), d, u, side_mask(FUS, side, 0.2))
    return n

def danger(side):
    d, u = frame(side)
    r = tuple(int(v * 255) for v in RED) + (255,)
    cap = 0.052; base = -0.523
    cv = L.Canvas2D(-0.80, 0.80, -0.08, 0.10, res=2000)
    # s = signed distance from band centre along the reading direction
    fwd = lambda xx: (xx - BAND_X) * (1 if side > 0 else -1)
    for (xa, xb) in [(-5.967, -5.600), (-5.050, -4.652)]:
        sa, sb = sorted([fwd(xa), fwd(xb)])
        wn = cv.text_width('DANGER', cap, 'Bold')
        tr = ((sb - sa) - wn) / 5
        cv.tracked_text(sa, 0.0, 'DANGER', cap, r, 'Bold', tr)
    # arrows pointing at the band
    ym = cap / 2
    for (tail, head) in [(-5.567, BAND_X - BAND_W / 2 - 0.004), (-5.083, BAND_X + BAND_W / 2 + 0.004)]:
        st, sh = fwd(tail), fwd(head)
        dirn = np.sign(sh - st)
        cv.rect(min(st, sh - dirn * 0.040), ym - 0.0085, max(st, sh - dirn * 0.040), ym + 0.0085, r)
        cv.polygon([(sh, ym), (sh - dirn * 0.046, ym + 0.022), (sh - dirn * 0.046, ym - 0.022)], r)
    return decal(cv, np.array([BAND_X, base, 0]), d, u, side_mask(FUS, side))

def blue_placard():
    d, u = frame(1)
    cv = L.Canvas2D(-0.08, 0.08, -0.04, 0.04, res=2000)
    cv.rrect(-0.059, -0.017, 0.059, 0.017, 0.003, color=(32, 92, 172, 255))
    cv.rect(-0.050, -0.004, 0.050, 0.004, (230, 235, 240, 255))
    return decal(cv, np.array([-5.199, -0.083, 0]), d, u, side_mask(FUS, 1))

# ------------------------------------------------------------------ fin serial 1030
def fin_serial(side):
    d, u = frame(side)
    cv = L.Canvas2D(-0.05, 0.50, -0.03, 0.21, res=1200)
    cap = 0.175
    x0, x1 = 5.05, 5.49
    import PIL.ImageFont as IF
    f = IF.truetype(L.font('Medium'), int(round(cv.m(cap) / L.CAP_RATIO)))
    txt = '1030'
    bb0 = f.getbbox(txt[0], anchor='ls'); bbN = f.getbbox(txt[-1], anchor='ls')
    lsb = bb0[0] / (cv.res * L.SS); rsb = (f.getlength(txt[-1]) - bbN[2]) / (cv.res * L.SS)
    ink = cv.text_width(txt, cap) - lsb - rsb
    tr = ((x1 - x0) - ink) / 3
    cv.tracked_text(-lsb, 0.0, txt, cap, tuple(int(v * 255) for v in GREY) + (255,), 'Medium', tr)
    origin = np.array([x0 if side > 0 else x1, 2.295, 0])
    return decal(cv, origin, d, u, side_mask(FIN, side))

# ------------------------------------------------------------------ wings
def wing_registration(side):
    """F-RACH on the upper surface of the right wing (side=-1, measured on the photo) and, mirrored, on the lower
    surface of the left wing (side=+1, ICAO Annex 7 position). Both read from the root to the tip with the tops of
    the letters towards the leading edge; the lower one is readable from below, nose up."""
    d = EZ * side; u = -EX                       # d x u = -y (lower surface) for side=+1, +y (upper) for side=-1
    cap = 0.49
    cents = [('F', 4.61), ('-', 5.065), ('R', 5.49), ('A', 5.97), ('C', 6.37), ('H', 6.81)]   # |z| of the letters
    cv = L.Canvas2D(-0.05, 2.80, -0.05, 0.55, res=400)
    g = tuple(int(v * 255) for v in GREY) + (255,)
    for ch, zc in cents:
        s = zc - 4.30                            # measured from |z| = 4.30 towards the tip
        if ch == '-':
            cv.rect(s - 0.15, 0.49 * 0.49 - 0.033, s + 0.15, 0.49 * 0.49 + 0.033, g)
        else:
            cv.glyph(s, 0.0, ch, cap, g, 'Medium', stretch=1.08)
    surface = (nrm[..., 1] < -0.3) if side > 0 else (nrm[..., 1] > 0.3)
    m = M.objmask(WING) & (side * z > 0) & surface
    return decal(cv, np.array([-1.600, 0, 4.30 * side]), d, u, m)

def wing_roundel(side):
    """Roundel on the upper surface of the left wing (side=+1, measured on the photo) and, mirrored, under the right
    wing (side=-1), as on French military aircraft."""
    cv = roundel_canvas(0.24)
    # seen from above: d=+x, u=-z (d x u = +y); seen from below: d=+x, u=+z (d x u = -y)
    d = EX; u = -EZ * side
    surface = (nrm[..., 1] > 0.3) if side > 0 else (nrm[..., 1] < -0.3)
    m = M.objmask(WING) & (side * z > 0) & surface
    return decal(cv, np.array([-1.845, 0, 5.95 * side]), d, u, m)

for side in (1, -1):
    print('reg', side, registration(side))
    print('roundel', side, fus_roundel(side))
    print('static', side, static_port(side, side > 0))
    print('title', side, title(side))
    print('danger', side, danger(side))
    print('fin', side, fin_serial(side))
print('exit', emergency_exit())
print('door', door_marks())
print('band', prop_band())
print('placard', blue_placard())
print('wing reg (upper right)', wing_registration(-1))
print('wing reg (lower left)', wing_registration(1))
print('wing roundel (upper left)', wing_roundel(1))
print('wing roundel (lower right)', wing_roundel(-1))
print('decals', time.time() - T0)

# ------------------------------------------------------------------ panel lines / rivets (height), weathering
H, ao = height_map(M)
tex *= (1.0 - ao)[..., None]

# belly grime aft of the nose gear, a touch browner and darker towards the lowest line
fm = M.objmask(['Fuselage', 'GearsDoorFront.Closed', 'LowerStabFin'])
g = np.clip((-0.40 - y) / 0.40, 0, 1) * np.clip((x + 5.2) / 1.5, 0, 1)
streak = 0.5 + 0.5 * L.value_noise(S, 90, 7, octaves=2)
k = (0.050 * g * streak)[..., None]
tex[fm] = (tex * (1 - k) + c((150, 140, 125)) * k)[fm]

# exhaust soot on the nacelle sides behind the stacks and on the wing just outboard/inboard of the nacelle
nm = M.objmask(NACELLE + ['Wings'])
zc = 2.76
dz = np.abs(np.abs(z) - zc)
behind = np.clip((x + 4.55) / 0.25, 0, 1) * np.exp(-np.clip(x + 4.5, 0, None) / 2.2)
band = np.exp(-((y + 0.18) / 0.20) ** 2) * np.clip((dz - 0.20) / 0.25, 0, 1) * np.exp(-np.clip(dz - 0.45, 0, None) / 0.35)
k2 = (0.13 * behind * band * (0.6 + 0.4 * streak))[..., None]
tex[nm] = (tex * (1 - k2) + c((70, 66, 62)) * k2)[nm]

# light grime inside the gear doors (edges) and around fuel caps
gm = M.objmask(['GearsDoorLeft.Closed', 'GearsDoorRight.Closed', 'GearDoorLeft.Open1', 'GearDoorLeft.Open2',
                'GearDoorRight.Open1', 'GearDoorRight.Open2'])
tex[gm] *= 0.96

# ------------------------------------------------------------------ finish
tex = np.clip(tex, 0, 1)
final = L.dilate_fill(tex, used, maxdist=40, fill=WHITE * 0.9)
# flaps have collapsed UVs pointing at (0.003, 0.006): give that (otherwise unused) spot the wing white
fr0, fc0 = int((1 - 0.006) * S), int(0.003 * S)
patch = np.zeros((S, S), bool); patch[fr0 - 8:fr0 + 9, max(fc0 - 8, 0):fc0 + 9] = True
final[patch & ~used] = WHITE
img = Image.fromarray((final * 255 + 0.5).astype(np.uint8), 'RGB').convert('RGBA')
liv = os.path.join(args.out, 'ALSR.png') if args.out else os.path.join(MODELS, 'Liveries', 'ALSR.png')
os.makedirs(os.path.dirname(liv), exist_ok=True)
img.save(liv, optimize=True)
print('livery', liv, time.time() - T0)

# ------------------------------------------------------------------ normal map (shared by every livery), alpha = gloss
del final, img, tex, proto, n1, n2, var, streak, g, k, k2, behind, band, dz
import gc; gc.collect()
gloss = np.ones((S, S), np.float32)
for names, g in [(BOOTS, 0.25), (['TiresFront', 'TiresLeft', 'TiresRight'], 0.12), (EXHAUST, 0.35),
                 (['PropLeft', 'PropRight'], 0.5), (GEAR, 0.8), (WHEELS, 0.7)]:
    gloss[M.objmask(names)] = g
nm = normal_map(M, H, gloss)
nm[~used] = (128, 128, 255, 255)
nmp = os.path.join(args.out, 'KingAir-350-normalmap.png') if args.out else os.path.join(MODELS, 'Effects', 'KingAir-350-normalmap.png')
Image.fromarray(nm, 'RGBA').save(nmp, optimize=True)
print('normal map', nmp, time.time() - T0)
