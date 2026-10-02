"""Pedestal of the Pro Line Fusion flight deck: power quadrant geometry shared by the spec, the Blender builder and
the animation generator (plain Python).

Model frame: x aft, y right, z up (m). Lever angles in degrees from vertical, positive forward.
"""

import math

from layout import Y0, Frame

PIVOT = (-4.330, -0.420)          # lever pivot axis (x, z), along y
QUAD_R = 0.200                    # quadrant surface radius about the pivot
QUAD_A = (65.0, -35.0)            # quadrant arc: front and aft edges
QUAD_HW = 0.100                   # half width of the quadrant (y)
BODY_HW = 0.120                   # half width of the pedestal under the quadrant
TOWER_X = (-4.548, -4.515)        # front tower under the lower panel (x range)
TOWER_TOP = -0.098
TRIM_FACE = ((-4.215, -0.256), (-4.050, -0.330))     # sloped face with the aileron and rudder trim knobs
AFT_X = (-4.050, -3.520)          # aft pedestal (CCP, keyboard, pressurization, CVR)
AFT_Z = -0.330
AFT_HW = 0.172
FLOOR_Z = -0.560

# levers: name, lateral offset (m), property (model), [(value, angle)], knob style, length (m), tooltip
LEVERS = [
    ("PWR0", -0.068, "sim/model/fusion/power-lever[0]", [(-1.0, -26.0), (0.0, -8.0), (1.0, 30.0)], "power", 0.330),
    ("PWR1", -0.046, "sim/model/fusion/power-lever[1]", [(-1.0, -26.0), (0.0, -8.0), (1.0, 30.0)], "power", 0.330),
    ("PROP0", -0.012, "controls/engines/engine[0]/propeller-pitch",
     [(0.0, -28.0), (0.04, -21.0), (0.08, -13.0), (1.0, 28.0)], "prop", 0.315),
    ("PROP1", 0.008, "controls/engines/engine[1]/propeller-pitch",
     [(0.0, -28.0), (0.04, -21.0), (0.08, -13.0), (1.0, 28.0)], "prop", 0.315),
    ("COND0", 0.042, "controls/engines/engine[0]/condition", [(0.0, -22.0), (0.5, -6.0), (1.0, 10.0)], "cond", 0.300),
    ("COND1", 0.062, "controls/engines/engine[1]/condition", [(0.0, -22.0), (0.5, -6.0), (1.0, 10.0)], "cond", 0.300),
]

TRIM_WHEEL = {"x": -4.300, "z": -0.335, "y": -0.109, "r": 0.086, "w": 0.020}
FLAP_SLOT = {"x": -4.285, "z": -0.305, "y": 0.100, "travel": 0.030}


def arc_point(a_deg, r=QUAD_R):
    a = math.radians(a_deg)
    return (PIVOT[0] - r * math.sin(a), PIVOT[1] + r * math.cos(a))


def arc_len_mm():
    return QUAD_R * math.radians(QUAD_A[0] - QUAD_A[1]) * 1000.0


def quad_y_mm(a_deg):
    """Vertical coordinate (mm) on the flat drawing of the quadrant (PED.QUAD) of the lever angle a."""
    mid = (QUAD_A[0] + QUAD_A[1]) / 2.0
    return QUAD_R * math.radians(a_deg - mid) * 1000.0


# aft pedestal top: horizontal, u = +y, v = forward (-x), normal up
def aft_frame(x, y_off, z=AFT_Z):
    return Frame((x, Y0 + y_off, z), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0))


def trim_face_frame(y_off, along=0.5):
    """Frame on the sloped trim face (normal up and aft)."""
    (x0, z0), (x1, z1) = TRIM_FACE
    x = x0 + (x1 - x0) * along
    z = z0 + (z1 - z0) * along
    d = (x0 - x1, z0 - z1)               # towards the front, up the slope
    n = math.hypot(*d)
    return Frame((x, Y0 + y_off, z), (0.0, 1.0, 0.0), (d[0] / n, 0.0, d[1] / n))
