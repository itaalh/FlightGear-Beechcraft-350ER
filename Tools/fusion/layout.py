"""Geometry vocabulary of the King Air 350 Pro Line Fusion cockpit (plain Python, used by every tool).

Model frame: x aft, y right, z up, metres (the FlightGear model frame of Models/KingAir.xml).
A panel is a flat face described by a Frame: origin (its centre), u (to the right on the face) and v (up on the
face); the normal u x v points towards the crew. Control positions and label coordinates on a panel are in
millimetres from the panel centre (x along u, y along v).
"""

import math

Y0 = 0.015          # cockpit centre line (the fuselage model is 1.5 cm off y = 0)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


def rot_axis(v, axis, deg):
    """Rotate vector v about the unit vector axis (Rodrigues)."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    k = axis
    return add(add(mul(v, c), mul(cross(k, v), s)), mul(k, dot(k, v) * (1 - c)))


class Frame:
    def __init__(self, origin, u, v):
        self.o = tuple(origin)
        self.u = norm(u)
        # re-orthogonalise v against u
        v = sub(v, mul(self.u, dot(v, self.u)))
        self.v = norm(v)
        self.n = cross(self.u, self.v)

    def p(self, x_mm, y_mm, z_mm=0.0):
        """World point of panel coordinates (mm), z along the normal (towards the crew)."""
        return add(self.o, add(mul(self.u, x_mm / 1000.0), add(mul(self.v, y_mm / 1000.0), mul(self.n, z_mm / 1000.0))))

    def dir(self, x, y, z=0.0):
        return add(mul(self.u, x), add(mul(self.v, y), mul(self.n, z)))

    def sub(self, x_mm, y_mm, z_mm=0.0, rot_u_deg=0.0, rot_v_deg=0.0):
        """Child frame at a panel point, optionally tilted about its own u then v axes."""
        u, v = self.u, self.v
        if rot_u_deg:
            v = rot_axis(v, u, rot_u_deg)
        if rot_v_deg:
            u = rot_axis(u, v, rot_v_deg)
        return Frame(self.p(x_mm, y_mm, z_mm), u, v)


def tilted_frame(origin, tilt_back_deg, yaw_deg=0.0):
    """Face towards the crew (normal +x), u = +y; the top leans forward by tilt_back_deg; yaw turns the face
    about z (positive: the face looks towards +y, i.e. the panel's right side comes aft)."""
    t = math.radians(tilt_back_deg)
    u = (0.0, 1.0, 0.0)
    v = (-math.sin(t), 0.0, math.cos(t))
    if yaw_deg:
        u = rot_axis(u, (0, 0, 1), yaw_deg)
        v = rot_axis(v, (0, 0, 1), yaw_deg)
    return Frame(origin, u, v)


def rounded_rect(w, h, r, seg=6, cx=0.0, cy=0.0):
    """Counter-clockwise outline (list of 2D points) of a w x h rectangle with corner radius r."""
    r = max(0.0, min(r, w / 2.0, h / 2.0))
    pts = []
    if r <= 1e-9:
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    corners = [(cx + w / 2 - r, cy - h / 2 + r, -90), (cx + w / 2 - r, cy + h / 2 - r, 0),
               (cx - w / 2 + r, cy + h / 2 - r, 90), (cx - w / 2 + r, cy - h / 2 + r, 180)]
    for (ox, oy, a0) in corners:
        for i in range(seg + 1):
            a = math.radians(a0 + 90.0 * i / seg)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def circle(r, n=24, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]
