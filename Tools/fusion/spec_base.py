"""Data model of the cockpit description (cockpit_spec.py): panels, their engraved markings and their controls.

Everything is plain data so that the three generators read the same description:
  atlas.py (Pillow)        -> Models/Fusion/fusion-panels*.png (+ lightmaps) and atlas.json
  build_cockpit.py (bpy)   -> Models/Fusion/fusion-cockpit.ac
  gen_xml.py               -> Models/Fusion/fusion-cockpit.xml, Nasal/fusion-lamps.nas

Units: panel coordinates in millimetres from the panel centre (x right, y up on the face), sizes in mm.
Bindings are small dicts turned into FlightGear <binding> elements by gen_xml.py:
  set(prop, value), toggle(prop), adjust(prop, step, lo, hi, wrap), nasal(script), fg1000(device, key, offset)
"""

WHITE = (0.93, 0.93, 0.90)
PANEL_GREY = (0.085, 0.085, 0.090)
BLACK = (0.02, 0.02, 0.02)
AMBER = (1.0, 0.62, 0.05)
GREEN = (0.15, 0.95, 0.30)
RED = (1.0, 0.12, 0.08)
CYAN = (0.35, 0.85, 1.0)

FONT = "SemiBold SemiCondensed"
FONT_BOLD = "Bold SemiCondensed"
FONT_COND = "SemiBold Condensed"


# ----------------------------------------------------------------------------------------------------------------
# bindings

def set_(prop, value):
    return {"command": "property-assign", "property": prop, "value": value}


def toggle(prop):
    return {"command": "property-toggle", "property": prop}


def adjust(prop, step, lo=None, hi=None, wrap=False):
    b = {"command": "property-adjust", "property": prop, "step": step, "wrap": wrap}
    if lo is not None:
        b["min"] = lo
    if hi is not None:
        b["max"] = hi
    return b


def nasal(script):
    return {"command": "nasal", "script": script}


def fg1000(device, key, offset=None):
    b = {"command": "FG1000HardKeyPushed", "device": device, "notification": key}
    if offset is not None:
        b["offset"] = offset
    return b


def softkey(device, n):
    return {"command": "FG1000SoftKeyPushed", "device": device, "offset": n}


CLICK = toggle("sim/sound/click")


# ----------------------------------------------------------------------------------------------------------------
class Mark:
    """Engraved marking on a panel face: text, polyline or rectangle."""

    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)


class Panel:
    def __init__(self, name, frame, w, h, radius=3.0, thick=3.0, elev=0.0, ppm=6, color=PANEL_GREY, screws=True,
                 material="plate", border=False, custom=False, backing=0.0):
        self.name = name
        self.frame = frame
        self.w, self.h = w, h
        self.radius = radius
        self.thick = thick            # plate thickness (mm), its face is at elev + thick
        self.elev = elev              # plate back off the structure (mm)
        self.ppm = ppm                # texture resolution (px per mm)
        self.color = color
        self.material = material
        self.screws = screws
        self.border = border
        self.custom = custom          # drawn in the atlas, surface built elsewhere (curved quadrant)
        self.backing = backing        # depth (mm) of a box behind the plate, horizontal, into the wall behind it
        self.marks = []
        self.controls = []

    @property
    def face_z(self):
        return self.elev + self.thick

    # markings ---------------------------------------------------------------------------------------------------
    def text(self, s, x, y, size=2.6, align="c", font=FONT, color=WHITE, lit=True, rot=0, spacing=0.0):
        self.marks.append(Mark("text", s=s, x=x, y=y, size=size, align=align, font=font, color=color, lit=lit,
                               rot=rot, spacing=spacing))

    def line(self, pts, width=0.35, color=WHITE, lit=True):
        self.marks.append(Mark("line", pts=pts, width=width, color=color, lit=lit))

    def rect(self, x0, y0, x1, y1, width=0.35, radius=0.0, color=WHITE, lit=True, fill=None):
        self.marks.append(Mark("rect", x0=x0, y0=y0, x1=x1, y1=y1, width=width, radius=radius, color=color, lit=lit,
                               fill=fill))

    def group(self, x0, y0, x1, y1, title=None, size=2.5, gap=1.5, bottom=None):
        """Engraved box with its title breaking the top line (and optional text breaking the bottom line)."""
        self.marks.append(Mark("group", x0=x0, y0=y0, x1=x1, y1=y1, title=title, size=size, gap=gap, bottom=bottom))

    def bracket(self, x0, x1, y, title=None, size=2.5, down=True, tick=1.8):
        """Horizontal bracket line with a centred title and end ticks (pointing down by default)."""
        self.marks.append(Mark("bracket", x0=x0, x1=x1, y=y, title=title, size=size, down=down, tick=tick))

    def add(self, control):
        control.panel = self
        self.controls.append(control)
        control.decorate(self)
        return control


# ----------------------------------------------------------------------------------------------------------------
class Control:
    kind = "control"

    def __init__(self, name, x, y, tooltip=None):
        self.name = name
        self.x, self.y = x, y
        self.tooltip = tooltip
        self.panel = None

    def decorate(self, panel):
        pass

    def obj(self, part):
        return "F.%s.%s" % (self.name, part)


class Toggle(Control):
    """Bat toggle switch. values: property values from the lowest (down / left) to the highest position;
    angles: lever angles (deg, positive = up/right) for each value; momentary: values that spring back to
    `rest` when the mouse button is released. labels: text next to each position (same order as values).
    guard: property that must be true (guard open) for the switch to move."""
    kind = "toggle"

    def __init__(self, name, x, y, prop, values=(0, 1), angles=None, labels=None, title=None, title_pos="above",
                 momentary=(), rest=None, tooltip=None, horizontal=False, guard=None, lever=16.0, prop_type="int",
                 title_size=2.5, label_size=2.2, label_side="right", on_change=None):
        super().__init__(name, x, y, tooltip)
        self.prop = prop
        self.values = list(values)
        n = len(self.values)
        self.angles = list(angles) if angles else ([-24, 24] if n == 2 else [-26, 0, 26])
        self.labels = labels
        self.title = title
        self.title_pos = title_pos
        self.momentary = list(momentary)
        self.rest = rest if rest is not None else (self.values[1] if n == 3 else self.values[0])
        self.horizontal = horizontal
        self.guard = guard
        self.lever = lever
        self.prop_type = prop_type
        self.title_size = title_size
        self.label_size = label_size
        self.label_side = label_side
        self.on_change = on_change          # extra bindings after each change (e.g. nasal)

    def decorate(self, p):
        if self.title:
            lines = self.title.split("\n")
            if self.title_pos == "above":
                y = self.y + 9.5 + (len(lines) - 1) * self.title_size * 1.15
                for k, t in enumerate(lines):
                    p.text(t, self.x, y - k * self.title_size * 1.15, self.title_size)
            elif self.title_pos == "below":
                y = self.y - 9.5
                for k, t in enumerate(lines):
                    p.text(t, self.x, y - k * self.title_size * 1.15, self.title_size)
        if self.labels:
            n = len(self.values)
            if self.horizontal:
                pos = {0: (-8.5, -5.0), 1: (8.5, -5.0)} if n == 2 else {0: (-8.5, -5.0), 1: (0, -8.5), 2: (8.5, -5.0)}
                for k, t in enumerate(self.labels):
                    if t:
                        dx, dy = pos[k]
                        p.text(t, self.x + dx, self.y + dy, self.label_size)
            else:
                side = 1 if self.label_side == "right" else -1
                al = "l" if side > 0 else "r"
                if n == 2:
                    ys = [-6.0, 6.0]
                else:
                    ys = [-6.5, 0.0, 6.5]
                for k, t in enumerate(self.labels):
                    if not t:
                        continue
                    for j, tl in enumerate(t.split("\n")):
                        p.text(tl, self.x + side * 5.0, self.y + ys[k] - 0.9 - j * self.label_size * 1.1,
                               self.label_size, align=al)


class Knob(Control):
    """Rotary control (FlightGear knob animation). style: 'selector' (pointer knob, discrete positions),
    'rheostat' (continuous), 'fgp' (Pro Line FGP knob), 'bar' (bar knob). angle = value * factor + offset (deg,
    clockwise positive as seen by the crew)."""
    kind = "knob"

    def __init__(self, name, x, y, prop, lo=0.0, hi=1.0, step=0.05, factor=270.0, offset=-135.0, style="rheostat",
                 d=13.0, h=10.0, wrap=False, positions=None, title=None, title_dy=None, tooltip=None, push=None,
                 action=None, shift_step=None, pos_radius=None, pos_size=2.0, title_size=2.5, color="knob",
                 prop_type="double"):
        super().__init__(name, x, y, tooltip)
        self.prop = prop
        self.lo, self.hi, self.step = lo, hi, step
        self.factor, self.offset = factor, offset
        self.style = style
        self.d, self.h = d, h
        self.wrap = wrap
        self.positions = positions          # [(value, label)] for selectors: labels around the knob
        self.title = title
        self.title_dy = title_dy
        self.push = push                    # bindings of a push on the knob cap
        self.action = action                # custom bindings instead of property-adjust (offset = +-1)
        self.shift_step = shift_step
        self.pos_radius = pos_radius
        self.pos_size = pos_size
        self.title_size = title_size
        self.color = color
        self.prop_type = prop_type

    def angle_of(self, value):
        return value * self.factor + self.offset

    def decorate(self, p):
        import math
        if self.title:
            dy = self.title_dy if self.title_dy is not None else self.d / 2 + 4.5
            for k, t in enumerate(self.title.split("\n")):
                p.text(t, self.x, self.y + dy - k * self.title_size * 1.15, self.title_size)
        if self.positions:
            r = self.pos_radius or (self.d / 2 + 4.0)
            for value, label in self.positions:
                a = math.radians(self.angle_of(value))
                # angle clockwise from 12 o'clock
                px, py = self.x + r * math.sin(a), self.y + r * math.cos(a)
                p.line([(self.x + (self.d / 2 + 0.6) * math.sin(a), self.y + (self.d / 2 + 0.6) * math.cos(a)),
                        (self.x + (self.d / 2 + 1.8) * math.sin(a), self.y + (self.d / 2 + 1.8) * math.cos(a))], 0.4)
                if label:
                    al = "c" if abs(math.sin(a)) < 0.35 else ("l" if math.sin(a) > 0 else "r")
                    p.text(label, px + (0.8 if al == "l" else (-0.8 if al == "r" else 0)), py - 0.9, self.pos_size,
                           align=al)


class DualKnob(Control):
    """Concentric knobs (FG1000 style): outer and inner rings turned with the mouse wheel / clicks, and a push
    on the inner knob. outer, inner: bindings run with offset +1 / -1; push: bindings."""
    kind = "dualknob"

    def __init__(self, name, x, y, outer, inner, push=None, d_outer=17.0, d_inner=11.0, title=None, tooltip=None,
                 title_size=2.3, outer_tip=None, inner_tip=None):
        super().__init__(name, x, y, tooltip)
        self.outer, self.inner, self.push = outer, inner, push
        self.d_outer, self.d_inner = d_outer, d_inner
        self.title = title
        self.title_size = title_size
        self.outer_tip, self.inner_tip = outer_tip, inner_tip

    def decorate(self, p):
        if self.title:
            for k, t in enumerate(self.title.split("\n")):
                p.text(t, self.x, self.y + self.d_outer / 2 + 4.0 - k * self.title_size * 1.15, self.title_size)


class Button(Control):
    """Push button with an engraved (or back-lit) legend on its cap. action: bindings on press; release:
    bindings on release. lamp: name of a lamp (sim/model/fusion/lamps/<lamp>) lighting the legend / a bar."""
    kind = "button"

    def __init__(self, name, x, y, w, h, action, legend=None, release=None, lamp=None, lamp_color=GREEN,
                 cap="cap", legend_color=BLACK, title=None, title_dy=None, tooltip=None, depth=5.0, travel=1.2,
                 legend_size=2.4, lamp_style="bar", title_size=2.4, repeatable=False):
        super().__init__(name, x, y, tooltip)
        self.w, self.h = w, h
        self.action = action
        self.release = release
        self.legend = legend
        self.lamp = lamp
        self.lamp_color = lamp_color
        self.cap = cap
        self.legend_color = legend_color
        self.title = title
        self.title_dy = title_dy
        self.depth = depth
        self.travel = travel
        self.legend_size = legend_size
        self.lamp_style = lamp_style          # bar (led bar in the cap), legend (lit legend), none
        self.title_size = title_size
        self.repeatable = repeatable

    def decorate(self, p):
        if self.title:
            dy = self.title_dy if self.title_dy is not None else self.h / 2 + 3.0
            for k, t in enumerate(self.title.split("\n")[::-1]):
                p.text(t, self.x, self.y + dy + k * self.title_size * 1.15, self.title_size)


class PushLight(Button):
    """Annunciator push button: square lens whose legend lights up (lamp), e.g. MASTER WARNING."""
    kind = "pushlight"

    def __init__(self, name, x, y, w, h, action, legend, lamp, color=RED, **kw):
        super().__init__(name, x, y, w, h, action, legend=legend, lamp=lamp, lamp_color=color, cap="lens",
                         legend_color=color, lamp_style="legend", depth=kw.pop("depth", 6.0), **kw)


class Lamp(Control):
    """Indicator light (no action): legend lit by sim/model/fusion/lamps/<lamp>. shape: rect or round."""
    kind = "lamp"

    def __init__(self, name, x, y, w, h, legend, lamp, color=GREEN, shape="rect", legend_size=2.2, tooltip=None,
                 depth=2.5):
        super().__init__(name, x, y, tooltip)
        self.w, self.h = w, h
        self.legend = legend
        self.lamp = lamp
        self.color = color
        self.shape = shape
        self.legend_size = legend_size
        self.depth = depth


class Gauge(Control):
    """Round gauge: bezel, printed dial (drawn by atlas.py from `dial`) and needles.
    needles: [(prop, [(value, angle_deg clockwise from 12 o'clock), ...], style)]."""
    kind = "gauge"

    def __init__(self, name, x, y, d, dial, needles, tooltip=None, bezel=4.0, depth=6.0):
        super().__init__(name, x, y, tooltip)
        self.d = d
        self.dial = dial
        self.needles = needles
        self.bezel = bezel
        self.depth = depth


class Hotspot(Control):
    """Invisible pick area (rectangle on the panel face) with bindings."""
    kind = "hotspot"

    def __init__(self, name, x, y, w, h, action, release=None, tooltip=None, z=0.5, buttons=(0,), wheel=None):
        super().__init__(name, x, y, tooltip)
        self.w, self.h = w, h
        self.action = action
        self.release = release
        self.z = z
        self.buttons = buttons
        self.wheel = wheel


class Decor(Control):
    """Static decoration built by a named Blender recipe (speaker grille, vent, placard...)."""
    kind = "decor"

    def __init__(self, name, x, y, recipe, **params):
        super().__init__(name, x, y)
        self.recipe = recipe
        self.params = params
