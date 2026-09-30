"""Writes the FlightGear animation file of the Pro Line Fusion cockpit from cockpit_spec.py.

python gen_xml.py  -> Models/Fusion/fusion-cockpit.xml, Nasal/fusion-lamps.nas
(needs Tools/fusion/_build/pivots.json from build_cockpit.py)
"""

import json
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cockpit_spec as SPEC                    # noqa: E402
import shell as S                              # noqa: E402
from spec_base import (Button, DualKnob, Gauge, Hotspot, Knob, Lamp, PushLight, Toggle, Decor,  # noqa: E402
                       GREEN, RED, AMBER, WHITE)

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Models", "Fusion", "fusion-cockpit.xml")
LAMPS_NAS = os.path.join(REPO, "Nasal", "fusion-lamps.nas")


class X:
    """Tiny XML writer."""

    def __init__(self):
        self.lines = []
        self.ind = 1

    def open(self, tag):
        self.lines.append("  " * self.ind + "<%s>" % tag)
        self.ind += 1

    def close(self, tag):
        self.ind -= 1
        self.lines.append("  " * self.ind + "</%s>" % tag)

    def el(self, tag, value, attr=""):
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif isinstance(value, float):
            value = ("%.5f" % value).rstrip("0").rstrip(".")
        self.lines.append("  " * self.ind + "<%s%s>%s</%s>" % (tag, attr, escape(str(value)), tag))

    def comment(self, text):
        self.lines.append("")
        self.lines.append("  " * self.ind + "<!-- %s -->" % text)

    def raw(self, text):
        for line in text.strip("\n").split("\n"):
            self.lines.append("  " * self.ind + line)


def vec(x, tag, v):
    x.open(tag)
    for k, c in zip(("x-m", "y-m", "z-m") if tag == "center" else ("x", "y", "z"), v):
        x.el(k, round(c, 5))
    x.close(tag)


def binding(x, b):
    x.open("binding")
    x.el("command", b["command"])
    for k, v in b.items():
        if k in ("command",):
            continue
        if k == "script":
            x.el("script", v)
        elif k == "step" and b["command"] == "property-adjust" and b.get("knob"):
            x.el("factor", v)
        elif k == "knob":
            continue
        else:
            x.el(k, v)
    x.close("binding")


def nasal_str(s):
    return '"%s"' % s.replace('"', '\\"')


def nasal_vec(vals):
    return "[" + ", ".join(str(int(v)) if isinstance(v, (int, bool)) else str(v) for v in vals) + "]"


def tooltip(x, tid, t):
    if not t:
        return
    x.open("hovered")
    x.open("binding")
    x.el("command", "set-tooltip")
    x.el("tooltip-id", tid)
    x.el("label", t["label"])
    if t.get("property"):
        x.el("property", t["property"])
        if t.get("script"):
            x.el("mapping", "nasal")
            x.el("script", t["script"])
    x.close("binding")
    x.close("hovered")


def pick(x, obj, actions, tip=None, tid=None, visible=True, release=None, repeatable=False, buttons=(0,), wheel=None,
         condition=None):
    x.open("animation")
    x.el("type", "pick")
    x.el("object-name", obj)
    if not visible:
        x.el("visible", False)
    x.open("action")
    for b in buttons:
        x.el("button", b)
    x.el("repeatable", repeatable)
    for b in actions:
        if condition:
            b = dict(b)
        binding_c(x, b, condition)
    if release:
        x.open("mod-up")
        for b in release:
            binding_c(x, b, condition)
        x.close("mod-up")
    x.close("action")
    if wheel:
        for btn, acts in ((3, wheel[0]), (4, wheel[1])):
            x.open("action")
            x.el("button", btn)
            x.el("repeatable", False)
            for b in acts:
                binding_c(x, b, condition)
            x.close("action")
    tooltip(x, tid or obj, tip)
    x.close("animation")


def binding_c(x, b, condition):
    if not condition:
        return binding(x, b)
    x.open("binding")
    x.el("command", b["command"])
    for k, v in b.items():
        if k != "command":
            x.el(k, v)
    x.raw("<condition>\n%s\n</condition>" % condition)
    x.close("binding")


# -----------------------------------------------------------------------------------------------------------------
def gen_toggle(x, t, piv):
    a = piv[t.name]
    x.comment("switch %s" % t.name)
    x.open("animation")
    x.el("type", "rotate")
    x.el("object-name", t.obj("lever"))
    x.el("property", t.prop)
    x.open("interpolation")
    for v, ang in zip(t.values, t.angles):
        x.open("entry")
        x.el("ind", int(v) if not isinstance(v, bool) else int(v))
        x.el("dep", ang)
        x.close("entry")
    x.close("interpolation")
    vec(x, "center", a["pivot"])
    axis = [-c for c in a["u"]] if not t.horizontal else a["v"]
    vec(x, "axis", axis)
    x.close("animation")
    vals = nasal_vec(t.values)
    guard = nasal_str(t.guard) if t.guard else "nil"
    mom = nasal_vec(t.momentary)
    ptype = nasal_str(t.prop_type)
    for part, d in (("up", 1), ("dn", -1)):
        act = [{"command": "nasal",
                "script": "fusion.switch(%s, %s, %d, %s, %s, %s);" % (nasal_str(t.prop), vals, d, ptype, guard, mom)}]
        rel = None
        if t.momentary:
            rel = [{"command": "nasal", "script": "fusion.switch_release(%s, %s, %s, %s);" % (
                nasal_str(t.prop), str(t.rest), mom, ptype)}]
        wheel = ([{"command": "nasal", "script": "fusion.switch(%s, %s, 1, %s, %s, %s, 1);" % (
                    nasal_str(t.prop), vals, ptype, guard, mom)}],
                 [{"command": "nasal", "script": "fusion.switch(%s, %s, -1, %s, %s, %s, 1);" % (
                    nasal_str(t.prop), vals, ptype, guard, mom)}])
        pick(x, t.obj("hs." + part), act, tip=t.tooltip, tid="F." + t.name, visible=False, release=rel, wheel=wheel)
    if t.guard:
        x.open("animation")
        x.el("type", "rotate")
        x.el("object-name", t.obj("guard"))
        x.el("property", t.guard)
        x.el("factor", 95.0)
        vec(x, "center", a["hinge"])
        vec(x, "axis", [-c for c in a["u"]])
        x.close("animation")
        pick(x, t.obj("hs.guard"), [{"command": "nasal", "script": "fusion.guard(%s, %s, %s, %s);" % (
            nasal_str(t.guard), nasal_str(t.prop), str(t.values[-1]), ptype)}],
             tip={"label": "Guard: %s", "property": t.guard, "script": 'return arg[0] ? "OPEN" : "CLOSED";'},
             tid="F." + t.name + ".guard", visible=False)


def gen_knob(x, k, piv):
    a = piv[k.name]
    x.comment("knob %s" % k.name)
    if k.style == "cb":
        x.open("animation")
        x.el("type", "translate")
        x.el("object-name", k.obj("knob"))
        x.el("property", k.prop)
        x.el("factor", 0.004)
        vec(x, "axis", a["normal"])
        x.close("animation")
        pick(x, k.obj("knob"), k.push, tip=k.tooltip, tid="F." + k.name)
        return
    x.open("animation")
    x.el("type", "knob")
    x.el("object-name", k.obj("knob"))
    x.el("property", k.prop)
    x.el("factor", k.factor)
    x.el("offset-deg", k.offset)
    vec(x, "center", a["pivot"])
    vec(x, "axis", a["axis"])
    x.open("action")
    if k.action:
        for b in k.action:
            binding(x, b)
        # visual turn of the knob
        binding(x, {"command": "property-adjust", "property": k.prop, "step": 1, "knob": True, "min": 0, "max": 24,
                    "wrap": True})
    else:
        binding(x, {"command": "property-adjust", "property": k.prop, "step": k.step, "knob": True, "min": k.lo,
                    "max": k.hi, "wrap": k.wrap})
    x.close("action")
    if k.shift_step is not None:
        x.open("shift-action")
        if isinstance(k.shift_step, list):
            for b in k.shift_step:
                binding(x, b)
            binding(x, {"command": "property-adjust", "property": k.prop, "step": 1, "knob": True, "min": 0,
                        "max": 24, "wrap": True})
        else:
            binding(x, {"command": "property-adjust", "property": k.prop, "step": k.shift_step, "knob": True,
                        "min": k.lo, "max": k.hi, "wrap": k.wrap})
        x.close("shift-action")
    tooltip(x, "F." + k.name, k.tooltip)
    x.close("animation")
    if k.push:
        pick(x, k.obj("push"), k.push, tip=k.tooltip, tid="F." + k.name + ".push", visible=False)


def gen_dualknob(x, k, piv):
    a = piv[k.name]
    x.comment("concentric knobs %s" % k.name)
    for part, acts, tip in (("outer", k.outer, k.outer_tip), ("inner", k.inner, k.inner_tip)):
        prop = "sim/model/fusion/knobs/%s-%s" % (k.name.replace(".", "-"), part)
        x.open("animation")
        x.el("type", "knob")
        x.el("object-name", k.obj(part))
        x.el("property", prop)
        x.el("factor", 15.0)
        vec(x, "center", a["pivot"])
        vec(x, "axis", a["axis"])
        x.open("action")
        for b in acts:
            binding(x, b)
        binding(x, {"command": "property-adjust", "property": prop, "step": 1, "knob": True, "min": 0, "max": 24,
                    "wrap": True})
        x.close("action")
        tooltip(x, "F." + k.name + "." + part, tip or k.tooltip)
        x.close("animation")
    if k.push:
        pick(x, k.obj("push"), k.push, tip=k.tooltip, tid="F." + k.name + ".push", visible=False)


def gen_button(x, b, piv):
    a = piv[b.name]
    press = "sim/model/fusion/press/" + b.name.replace(".", "-")
    x.comment("button %s" % b.name)
    objs = [b.obj("cap")] + ([b.obj("lamp")] if b.lamp and b.lamp_style == "bar" else [])
    x.open("animation")
    x.el("type", "translate")
    for o in objs:
        x.el("object-name", o)
    x.el("property", press)
    x.el("factor", -b.travel / 1000.0)
    vec(x, "axis", a["normal"])
    x.close("animation")
    act = [{"command": "property-assign", "property": press, "value": 1}] + b.action
    rel = [{"command": "property-assign", "property": press, "value": 0}] + (b.release or [])
    pick(x, b.obj("cap"), act, tip=b.tooltip, tid="F." + b.name, release=rel, repeatable=b.repeatable)
    if b.lamp:
        obj = b.obj("lamp") if b.lamp_style == "bar" else b.obj("cap")
        emission(x, [obj], b.lamp, b.lamp_color, 1.0 if b.lamp_style == "bar" else 1.6)


def emission(x, objs, lamp, color, gain=1.4):
    x.open("animation")
    x.el("type", "material")
    for o in objs:
        x.el("object-name", o)
    x.open("emission")
    x.el("red", round(color[0] * gain, 3))
    x.el("green", round(color[1] * gain, 3))
    x.el("blue", round(color[2] * gain, 3))
    x.el("factor-prop", "sim/model/fusion/lamps/" + lamp)
    x.close("emission")
    x.close("animation")


def gen_lamp(x, l, piv):
    x.comment("lamp %s" % l.name)
    emission(x, [l.obj("lamp")], l.lamp, l.color, 1.8)


def gen_gauge(x, g, piv):
    a = piv[g.name]
    x.comment("gauge %s" % g.name)
    for k, (prop, table, style) in enumerate(g.needles):
        x.open("animation")
        x.el("type", "rotate")
        x.el("object-name", g.obj("needle%d" % k))
        x.el("property", prop)
        x.open("interpolation")
        for v, ang in table:
            x.open("entry")
            x.el("ind", v)
            x.el("dep", ang)
            x.close("entry")
        x.close("interpolation")
        vec(x, "center", a["pivot"])
        vec(x, "axis", a["axis"])
        x.close("animation")
    if g.dial == "hobbs" and "digit_step" in a:
        # drums: 1000, 100, 10, 1 hours and tenths (Nasal/fusion-cockpit.nas writes sim/model/fusion/hobbs/d<k>)
        step = a["digit_step"]
        for k in range(5):
            x.open("animation")
            x.el("type", "textranslate")
            x.el("object-name", g.obj("d%d" % k))
            x.el("property", "sim/model/fusion/hobbs/d%d" % k)
            x.el("factor", -step)
            if k < 4:
                x.el("step", 1)
            x.open("axis")
            x.el("x", 0)
            x.el("y", 1)
            x.el("z", 0)
            x.close("axis")
            x.close("animation")


def gen_hotspot(x, h, piv):
    x.comment("hotspot %s" % h.name)
    pick(x, h.obj("hs"), h.action, tip=h.tooltip, tid="F." + h.name, visible=False, release=h.release,
         wheel=h.wheel)


def gen_decor(x, d, piv):
    if d.recipe == "gear_slot":
        a = piv["GEAR"]
        x.comment("landing gear handle")
        x.open("animation")
        x.el("type", "rotate")
        x.el("object-name", "F.GEAR.handle")
        x.el("object-name", "F.GEAR.handle.lamp")
        x.el("property", "controls/gear/gear-down")
        x.open("interpolation")
        x.raw("<entry><ind>0</ind><dep>14</dep></entry>\n<entry><ind>1</ind><dep>-14</dep></entry>")
        x.close("interpolation")
        vec(x, "center", a["pivot"])
        vec(x, "axis", [-c for c in a["axis"]])
        x.close("animation")
        pick(x, "F.GEAR.hs", [{"command": "nasal", "script": "fusion.gear_handle();"}],
             tip={"label": "Landing gear: %s", "property": "controls/gear/gear-down",
                  "script": 'return arg[0] ? "DOWN" : "UP";'}, tid="F.GEAR", visible=False)
        emission(x, ["F.GEAR.handle.lamp"], "gear_handle", RED, 1.8)
    elif d.recipe == "pbrake_handle":
        a = piv["PBRAKE"]
        x.comment("parking brake handle")
        x.open("animation")
        x.el("type", "translate")
        x.el("object-name", "F.PBRAKE.handle")
        x.el("property", "controls/gear/brake-parking")
        x.el("factor", 0.025)
        vec(x, "axis", a["normal"])
        x.close("animation")
    elif d.recipe == "pitch_wheel":
        a = piv["FGP.WHEEL"]
        x.comment("pitch wheel")
        x.open("animation")
        x.el("type", "rotate")
        x.el("object-name", "F.FGP.WHEEL.wheel")
        x.el("property", "sim/model/fusion/knobs/pitch")
        x.el("factor", 20.0)
        vec(x, "center", a["pivot"])
        vec(x, "axis", a["axis"])
        x.close("animation")


GEN = {Toggle: gen_toggle, Knob: gen_knob, DualKnob: gen_dualknob, Button: gen_button, PushLight: gen_button, Lamp: gen_lamp,
       Gauge: gen_gauge, Hotspot: gen_hotspot, Decor: gen_decor}


def gen_screens(x):
    x.comment("self-lit displays (the canvas replaces the texture, the emission keeps them readable at night)")
    x.open("animation")
    x.el("type", "material")
    for o in ("Fusion.Screen1", "Fusion.Screen2", "Fusion.Screen3", "Fusion.Stby.screen"):
        x.el("object-name", o)
    x.open("emission")
    for c in ("red", "green", "blue"):
        x.el(c, 1.0)
    x.el("factor-prop", "sim/model/fusion/display-brightness")
    x.close("emission")
    x.close("animation")
    x.comment("FG1000 displays: touch softkeys along the bottom of each screen (FG1000 softkeys 1-12)")
    for n in (1, 2, 3):
        name = {1: "pfd1", 2: "mfd", 3: "pfd2"}[n]
        cond = "<not><equals><property>controls/fusion/inhibit-%s</property><value>1</value></equals></not>" % name
        for k in range(1, 13):
            pick(x, "Display%d.sk%d" % (n, k), [{"command": "FG1000SoftKeyPushed", "device": n, "offset": k}],
                 tip={"label": "Softkey %d (touch)" % k}, tid="F.sk%d.%d" % (n, k), visible=False, condition=cond)


def gen_yokes(x, piv):
    x.comment("===== control wheels: elevator (fore / aft), aileron (turn), menu King Air 350 > Yokes visible")
    for k in ("L", "R"):
        a = piv["YOKE" + k]
        objs = ["F.YOKE%s.%s" % (k, p) for p in ("wheel", "apdisc", "trimdn", "trimup", "ptt")]
        x.open("animation")
        x.el("type", "select")
        for o in objs + ["F.YOKE%s.column" % k]:
            x.el("object-name", o)
        x.raw("<condition><property>sim/model/yokes-visible</property></condition>")
        x.close("animation")
        x.open("animation")
        x.el("type", "translate")
        for o in objs + ["F.YOKE%s.column" % k]:
            x.el("object-name", o)
        x.el("property", "controls/flight/elevator")
        x.el("factor", -0.075)
        vec(x, "axis", a["axis"])
        x.close("animation")
        x.open("animation")
        x.el("type", "rotate")
        for o in objs:
            x.el("object-name", o)
        x.el("property", "controls/flight/aileron")
        x.el("factor", -40.0)
        vec(x, "center", a["hub"])
        vec(x, "axis", a["axis"])
        x.close("animation")
        side = 0 if k == "L" else 1
        press = "sim/model/fusion/press/yoke-%s-" % k.lower()
        for part, travel, act, rel, tip, rep in (
                ("apdisc", 0.0015, [{"command": "nasal", "script": "fusion.ap_yd_disconnect();"}], [],
                 "AP / YD disconnect, trim interrupt", False),
                ("trimdn", 0.0015, [{"command": "nasal", "script": "fusion.trim(1);"}], [],
                 "Pitch trim: nose DOWN (hold)", True),
                ("trimup", 0.0015, [{"command": "nasal", "script": "fusion.trim(-1);"}], [],
                 "Pitch trim: nose UP (hold)", True),
                ("ptt", 0.002, [{"command": "nasal", "script": "fusion.ptt(%d, 1);" % side}],
                 [{"command": "nasal", "script": "fusion.ptt(%d, 0);" % side}], "Push to talk (transmitter: XMT selector)",
                 False)):
            obj = "F.YOKE%s.%s" % (k, part)
            x.open("animation")
            x.el("type", "translate")
            x.el("object-name", obj)
            x.el("property", press + part)
            x.el("factor", -travel)
            vec(x, "axis", a["normal"] if part != "ptt" else [-c for c in a["normal"]])
            x.close("animation")
            pick(x, obj, [{"command": "property-assign", "property": press + part, "value": 1}] + act,
                 tip={"label": tip}, tid=obj, repeatable=rep,
                 release=[{"command": "property-assign", "property": press + part, "value": 0}] + rel)


def knob_drag(x, obj, prop, a, actions, shift_actions, tip, tid, factor=0.0, axis=None):
    """FlightGear knob animation used as a lever handle: mouse wheel or vertical drag, no rotation of its own."""
    x.open("animation")
    x.el("type", "knob")
    x.el("object-name", obj)
    x.el("property", prop)
    x.el("factor", factor)
    vec(x, "center", a["pivot"])
    vec(x, "axis", axis or a["axis"])
    x.el("drag-direction", "vertical")
    x.el("drag-scale-px", 8)
    x.open("action")
    for b in actions:
        binding(x, b)
    x.close("action")
    if shift_actions:
        x.open("shift-action")
        for b in shift_actions:
            binding(x, b)
        x.close("shift-action")
    tooltip(x, tid, tip)
    x.close("animation")


def gen_pedestal(x, piv):
    import pedestal as PD
    off = 'cmdarg().getNode("offset").getValue()'
    x.comment("===== pedestal: power, propeller and condition levers (wheel or vertical drag; shift: both levers)")
    for nm, lat, prop, table, style, length in PD.LEVERS:
        a = piv[nm]
        i = int(nm[-1])
        objs = ["F.%s.lever" % nm] + (["F.PWR0.ga", "F.PWR0.ghs"] if nm == "PWR0" else [])
        x.open("animation")
        x.el("type", "rotate")
        for o in objs:
            x.el("object-name", o)
        x.el("property", prop)
        x.open("interpolation")
        for v, ang in table:
            x.open("entry")
            x.el("ind", v)
            x.el("dep", ang)
            x.close("entry")
        x.close("interpolation")
        vec(x, "center", a["pivot"])
        vec(x, "axis", a["axis"])
        x.close("animation")
        if style == "power":
            act = [{"command": "nasal", "script": "fusion.power_lever(%d, %s);" % (i, off)}]
            sh = [{"command": "nasal", "script": "fusion.power_lever(-1, %s);" % off}]
            tip = {"label": "%s power lever: %%s" % ("Left" if i == 0 else "Right"), "property": prop,
                   "script": 'return arg[0] < -0.001 ? sprintf("BETA / REVERSE %d %%", -arg[0] * 100) : sprintf("%d %%", arg[0] * 100);'}
        elif style == "prop":
            act = [{"command": "property-adjust", "property": prop, "step": 0.02, "knob": True, "min": 0.0, "max": 1.0}]
            sh = [{"command": "nasal", "script": 'fusion.lever_both("propeller-pitch", 0.02, %s);' % off}]
            tip = {"label": "%s propeller lever: %%s" % ("Left" if i == 0 else "Right"), "property": prop,
                   "script": 'return arg[0] < 0.04 ? "FEATHER" : sprintf("%d rpm", 1450 + 250 * math.clamp((arg[0] - 0.08) / 0.92, 0, 1));'}
        else:
            act = [{"command": "property-adjust", "property": prop, "step": 0.5, "knob": True, "min": 0.0, "max": 1.0}]
            sh = [{"command": "nasal", "script": 'fusion.lever_both("condition", 0.5, %s);' % off}]
            tip = {"label": "%s condition lever: %%s" % ("Left" if i == 0 else "Right"), "property": prop,
                   "script": 'return arg[0] < 0.25 ? "FUEL CUTOFF" : (arg[0] < 0.75 ? "LOW IDLE" : "HIGH IDLE");'}
        knob_drag(x, "F.%s.lever" % nm, prop, a, act, sh, tip, "F." + nm)
    pick(x, "F.PWR0.ga", [{"command": "nasal", "script": "fusion.go_around();"}], tip={"label": "GO AROUND"},
         tid="F.PWR0.ga")
    pick(x, "F.PWR0.ghs", [{"command": "nasal", "script": "fusion.gear_horn_silence();"}],
         tip={"label": "Landing gear warning horn SILENCE"}, tid="F.PWR0.ghs")

    x.comment("flap lever: UP / APPROACH / DOWN")
    x.open("animation")
    x.el("type", "translate")
    x.el("object-name", "F.FLAP.handle")
    x.el("property", "controls/flight/flaps")
    x.open("interpolation")
    for v, d in ((0, 0.030), (0.4, 0.0), (1, -0.030)):
        x.raw("<entry><ind>%s</ind><dep>%s</dep></entry>" % (v, d))
    x.close("interpolation")
    vec(x, "axis", [0, 0, 1])
    x.close("animation")
    knob_drag(x, "F.FLAP.handle", "controls/flight/flaps", {"pivot": [0, 0, 0], "axis": [0, 1, 0]},
              [{"command": "nasal", "script": "controls.flapsDown(-%s);" % off}], None,
              {"label": "Flaps: %s (wheel or drag)", "property": "controls/flight/flaps",
               "script": 'return arg[0] < 0.2 ? "UP" : (arg[0] < 0.7 ? "APPROACH" : "DOWN");'}, "F.FLAP")

    x.comment("elevator trim wheel and indicator")
    a = piv["TRIMWHEEL"]
    x.open("animation")
    x.el("type", "knob")
    x.el("object-name", "F.TRIMWHEEL")
    x.el("property", "controls/flight/elevator-trim")
    x.el("factor", 600.0)
    vec(x, "center", a["pivot"])
    vec(x, "axis", a["axis"])
    x.el("drag-direction", "vertical")
    x.el("drag-scale-px", 4)
    x.open("action")
    binding(x, {"command": "property-adjust", "property": "controls/flight/elevator-trim", "step": 0.004, "knob": True,
                "min": -1.0, "max": 1.0})
    x.close("action")
    x.open("shift-action")
    binding(x, {"command": "property-adjust", "property": "controls/flight/elevator-trim", "step": 0.02, "knob": True,
                "min": -1.0, "max": 1.0})
    x.close("shift-action")
    tooltip(x, "F.TRIMWHEEL", {"label": "Elevator trim: %s (wheel: roll forward = nose down)",
                               "property": "controls/flight/elevator-trim",
                               "script": 'return sprintf("%+.2f", arg[0]);'})
    x.close("animation")
    x.open("animation")
    x.el("type", "translate")
    x.el("object-name", "F.ETRIM.pointer")
    x.el("property", "controls/flight/elevator-trim")
    x.el("factor", 0.030)
    vec(x, "axis", [0, 0, 1])
    x.close("animation")


EFFECT = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated by Tools/fusion/gen_xml.py - do not edit. Back lighting of the panel markings drawn on
     fusion-panel-%(n)d.png: lightmap fusion-panel-%(n)d-lm.png, brightness sim/model/fusion/panel-lights-norm
     (instrument lights dimmer on the DC bus, Nasal/fusion-cockpit.nas). -->
<PropertyList>
  <name>fusion-panel-%(n)d</name>
  <inherits-from>Effects/model-combined-deferred</inherits-from>
  <parameters>
    <lightmap-enabled type="int">1</lightmap-enabled>
    <lightmap-multi type="int">0</lightmap-multi>
    <lightmap-factor type="float" n="0"><use>/sim/model/fusion/panel-lights-norm</use></lightmap-factor>
    <lightmap-color type="vec3d" n="0">2.4 2.2 1.85</lightmap-color>
    <texture n="3">
      <image>Aircraft/KingAir-350/Models/Fusion/fusion-panel-%(n)d-lm.png</image>
      <filter>linear-mipmap-linear</filter>
      <wrap-s>clamp</wrap-s>
      <wrap-t>clamp</wrap-t>
      <internal-format>normalized</internal-format>
    </texture>
  </parameters>
</PropertyList>
"""


def gen_effects(x):
    with open(os.path.join(HERE, "_build", "objects.json")) as fh:
        objs = json.load(fh)
    pages = {}
    for name, tex in objs.items():
        if tex and tex.startswith("fusion-panel-"):
            pages.setdefault(int(tex.split("-")[2].split(".")[0]), []).append(name)
    eff_dir = os.path.join(REPO, "Models", "Fusion", "Effects")
    os.makedirs(eff_dir, exist_ok=True)
    x.comment("===== back lighting of the markings (lightmaps), one effect per texture page")
    for n in sorted(pages):
        with open(os.path.join(eff_dir, "fusion-panel-%d.eff" % n), "w", newline="\n") as fh:
            fh.write(EFFECT % {"n": n})
        x.open("effect")
        x.el("inherits-from", "Aircraft/KingAir-350/Models/Fusion/Effects/fusion-panel-%d" % n)
        for o in sorted(pages[n]):
            x.el("object-name", o)
        x.close("effect")


def write_lamps():
    lines = ["# Generated by Tools/fusion/gen_xml.py from Tools/fusion/cockpit_spec.py - do not edit.",
             "# Lamp conditions of the Pro Line Fusion cockpit; Nasal/fusion-cockpit.nas writes",
             "# sim/model/fusion/lamps/<name> (emission factor of the lamp objects).",
             "", "var LAMPS = {"]
    for name, expr in sorted(SPEC.LAMPS.items()):
        lines.append('    "%s": func { %s },' % (name, expr))
    lines.append("};")
    with open(LAMPS_NAS, "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    with open(os.path.join(HERE, "_build", "pivots.json")) as fh:
        piv = json.load(fh)
    x = X()
    x.lines = ['<?xml version="1.0" encoding="UTF-8"?>',
               "<!-- Generated by Tools/fusion/gen_xml.py from Tools/fusion/cockpit_spec.py - do not edit.",
               "     King Air 350ER Pro Line Fusion flight deck (KingAir-350ER-G1000). -->",
               "<PropertyList>", "", "  <path>fusion-cockpit.ac</path>"]
    for p in SPEC.PANELS:
        x.comment("===== panel %s" % p.name)
        for c in p.controls:
            GEN[type(c)](x, c, piv)
    gen_effects(x)
    gen_screens(x)
    gen_yokes(x, piv)
    gen_pedestal(x, piv)
    # hotspot material objects are never drawn
    x.lines.append("</PropertyList>")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(x.lines) + "\n")
    write_lamps()
    print("wrote", OUT, "and", LAMPS_NAS)


if __name__ == "__main__":
    main()
