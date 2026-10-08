"""Structure of the Pro Line Fusion flight deck: glareshield, main instrument panel, lower panel band, display
bezels. Dimensions from the reference photographs scaled on the 14.1-in 16:10 displays (304 x 190 mm active area)
and fitted to the fuselage of Models/KingAir.ac (windshield base, side walls).
"""

import math

from layout import Y0, Frame, tilted_frame, add, mul, rounded_rect

# ----------------------------------------------------------------------------------------------------------------
# frames

# main instrument panel: display plane, top leaning forward 8 deg, centred on the displays
MP = tilted_frame((-4.650, Y0, 0.190), 8.0)
MP_U = (-0.575, 0.575)          # half widths (m) along u
MP_V = (-0.155, 0.121)          # along v

# lower panel band: hangs from the bottom edge of the main panel, 35 deg from vertical
_lp_top = MP.p(0, MP_V[0] * 1000)
LP_TILT = 35.0
LP_H = 0.160
LP = tilted_frame(add(_lp_top, mul((math.sin(math.radians(LP_TILT)), 0, -math.cos(math.radians(LP_TILT))), LP_H / 2)),
                  LP_TILT)
LP_U = (-0.555, 0.555)

# displays: pilot PFD, MFD, copilot PFD (FG1000 displays 1, 2, 3)
DISPLAY_W, DISPLAY_H = 0.325, 0.215       # bezel
SCREEN_W, SCREEN_H = 0.304, 0.190         # 14.1 in, 16:10
CANVAS_W = SCREEN_H * 4.0 / 3.0           # FG1000 canvas: 1024 x 768 (4:3) in the middle of the screen
DISPLAY_X = [-0.335, 0.0, 0.335]          # centres along MP u (m)
DISPLAY_Z = 0.030                         # bezel front, off the panel face
SCREEN_Z = 0.024

# ----------------------------------------------------------------------------------------------------------------
# windshield base (inner edge of Windows.001 in Models/KingAir.ac), symmetric about Y0: |s| -> (x, z)
WS_BASE = [(0.000, -4.799, 0.442), (0.123, -4.799, 0.441), (0.219, -4.797, 0.439), (0.315, -4.793, 0.436),
           (0.411, -4.788, 0.430), (0.475, -4.782, 0.424), (0.537, -4.771, 0.413), (0.596, -4.753, 0.395),
           (0.649, -4.727, 0.371), (0.695, -4.695, 0.339), (0.729, -4.665, 0.310), (0.752, -4.604, 0.303)]
WS_SLOPE = 0.696                          # windshield rise per metre aft (side view, 35 deg)


def interp(table, s, col):
    s = abs(s)
    for a, b in zip(table, table[1:]):
        if s <= b[0]:
            t = (s - a[0]) / (b[0] - a[0])
            return a[col] + t * (b[col] - a[col])
    return table[-1][col]


def ws_x(s):
    return interp(WS_BASE, s, 1)


def ws_z(s):
    return interp(WS_BASE, s, 2)


def glass_z(x, s):
    """Height of the windshield inner surface at station x (aft of its base) and lateral offset s."""
    return ws_z(s) + max(0.0, x - ws_x(s)) * WS_SLOPE


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# glareshield ------------------------------------------------------------------------------------------------------
GS_END = 0.735                            # lateral end of the glareshield (side windows)
HUMP_H = 0.085                            # standby display housing above the brow line


def lip_x(s):
    """Aft face (brow) of the glareshield in plan view."""
    a = abs(s)
    return -4.585 + 1.60 * max(0.0, a - 0.45) ** 2


def brow_bottom(s):
    """Lower edge of the brow: level over the displays, then the hood wraps down to the side walls."""
    a = abs(s)
    return 0.322 - 0.120 * smooth(0.585, GS_END, a)


def brow_top(s):
    a = abs(s)
    base = ws_z(s) - 0.012
    return base + HUMP_H * (1.0 - smooth(0.100, 0.245, a))


def gs_section(s):
    """Glareshield cross-section at lateral offset s (list of (x, z)), from the underside next to the main
    panel, round the brow (lip, aft face, top edge), along the top surface to the windshield base."""
    xl = lip_x(s)
    zb = brow_bottom(s)
    zt = max(zb + 0.012, brow_top(s))
    h = zt - zb
    mp_top = MP.p(0, MP_V[1] * 1000)
    x_under = mp_top[0] if abs(s) <= MP_U[1] else xl - 0.05
    pts = [(x_under, zb + 0.002), (xl - 0.006, zb), (xl, zb + 0.005), (xl - 0.002, zb + 0.35 * h),
           (xl - 0.006, zb + 0.80 * h), (xl - 0.011, zt - 0.004), (xl - 0.020, zt)]
    xf = ws_x(s) + 0.004
    x0 = xl - 0.020
    for k in range(1, 6):
        x = x0 + (xf - x0) * k / 6.0
        pts.append((x, min(zt, glass_z(x, s) - 0.016)))
    pts.append((xf, ws_z(s) - 0.008))
    pts.append((xf, ws_z(s) - 0.060))
    return pts


GS_STATIONS = [0.0, 0.03, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22, 0.245, 0.28, 0.33, 0.39, 0.45,
               0.50, 0.54, 0.58, 0.62, 0.66, 0.69, 0.71, GS_END]
