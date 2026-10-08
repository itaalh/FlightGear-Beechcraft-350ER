"""King Air 350ER Pro Line Fusion flight deck: panels and controls (see spec_base.py for the data model).

Layout after the reference photographs (King Air 350ER and 360 with Collins Pro Line Fusion), scaled on the
displays. Functions: existing aircraft systems where they exist (Nasal/electrical.nas, kingair350.nas,
ice-protection.nas, pressurization.nas, annunciators.nas, autopilot.nas, FG1000), the rest in
Nasal/fusion-cockpit.nas. New cockpit switch properties live under controls/fusion/ (numbers, lowest = down).
"""

import math

import shell as S
from layout import Y0, Frame, tilted_frame, add, mul, rot_axis
from spec_base import *                     # noqa: F401,F403

PANELS = []
LAMPS = {}          # lamp name -> Nasal expression (true = lit), evaluated by Nasal/fusion-lamps.nas


def panel(*a, **kw):
    p = Panel(*a, **kw)
    PANELS.append(p)
    return p


def lamp(name, expr):
    LAMPS[name] = expr
    return name


FC = "controls/fusion/"            # cockpit switch properties
FCS = "FCS."                       # autopilot namespace (Nasal/autopilot.nas)


def tip(label, prop=None, script=None):
    return {"label": label, "property": prop, "script": script}


# =================================================================================================================
# GLARESHIELD
# =================================================================================================================
def brow_frame(s, z, tilt=8.0, out=0.0):
    """Frame on the aft face (brow) of the glareshield at lateral offset s and height z."""
    x = S.lip_x(s) - 0.004 * (z - S.brow_bottom(s)) / 0.1 + out
    # plan-view tangent of the brow line
    ds = 0.01
    dx = S.lip_x(s + ds) - S.lip_x(s - ds)
    yaw = math.degrees(math.atan2(dx, 2 * ds))
    return tilted_frame((x + 0.001, Y0 + s, z), tilt, yaw_deg=-yaw)


def glareshield():
    # ---- MASTER WARNING / MASTER CAUTION, pilot and copilot
    for side, s in (("L", -0.392), ("R", 0.392)):
        p = panel("GS.master" + side, brow_frame(s, 0.392), 46, 27, radius=2, ppm=12, screws=False)
        p.add(PushLight("MW" + side, -11.0, 2.5, 18.5, 15.0,
                        [set_("instrumentation/annunciators/warning/Master", 0), CLICK],
                        "MASTER\nWARNING", lamp("master_warning", 'getprop("instrumentation/annunciators/warning/flasher")'),
                        color=RED, tooltip=tip("Master warning: press to reset")))
        p.add(PushLight("MC" + side, 11.0, 2.5, 18.5, 15.0,
                        [set_("instrumentation/annunciators/caution/Master", 0), CLICK],
                        "MASTER\nCAUTION", lamp("master_caution", 'getprop("instrumentation/annunciators/caution/flasher")'),
                        color=AMBER, tooltip=tip("Master caution: press to reset")))
        p.text("PRESS TO RESET", -11.0, -9.5, 1.9)
        p.text("PRESS TO RESET", 11.0, -9.5, 1.9)

    # ---- engine fire extinguisher and firewall valve push-lights (hump shoulders)
    for side, s, eng in (("L", -0.142, 0), ("R", 0.142, 1)):
        p = panel("GS.fire" + side, brow_frame(s, 0.442, tilt=14.0), 50, 24, radius=2, ppm=12, screws=False)
        fire = lamp("fire_%d" % eng, 'getprop("controls/fusion/fire-test[%d]") == 1 and cb("fire-det")' % eng)
        disch = lamp("ext_disch_%d" % eng, 'getprop("controls/fusion/extinguisher[%d]") or getprop("controls/fusion/fire-test[%d]") == -1' % (eng, eng))
        fw = lamp("fw_valve_%d" % eng, 'getprop("controls/engines/engine[%d]/fire-handle")' % eng)
        order = (-12.0, 12.0) if side == "L" else (12.0, -12.0)
        p.add(PushLight("FIRE" + side, order[0], 0.0, 20.0, 17.0,
                        [nasal("fusion.fire_extinguisher(%d)" % eng)],
                        "%s ENG\nFIRE\nPUSH TO\nEXT" % side, fire, color=RED,
                        tooltip=tip("%s engine fire extinguisher (push to discharge)" % ("Left" if eng == 0 else "Right"))))
        p.add(Lamp("DISCH" + side, order[0], -10.2, 12.0, 3.2, "DISCH", disch, color=AMBER, legend_size=2.0))
        p.add(PushLight("FW" + side, order[1], 0.0, 20.0, 17.0,
                        [toggle("controls/engines/engine[%d]/fire-handle" % eng), CLICK],
                        "F/W VALVE\nPUSH\n\nCLOSED", fw, color=AMBER,
                        tooltip=tip("%s firewall fuel valve: %%s" % ("Left" if eng == 0 else "Right"),
                                    "controls/engines/engine[%d]/fire-handle" % eng,
                                    'return arg[0] ? "CLOSED" : "OPEN";')))

    # ---- marker beacon and TAWS annunciators (under the brow, left of the FGP)
    p = panel("GS.marker", brow_frame(-0.268, 0.331), 50, 12, radius=1.5, ppm=12, screws=False)
    for k, (nm, leg, col, expr) in enumerate([
            ("TAWS", "TERR", AMBER, 'getprop("instrumentation/mk-viii/outputs/discretes/gpws-alert") or getprop("instrumentation/mk-viii/outputs/discretes/gpws-warning")'),
            ("MKRO", "O", CYAN, 'getprop("instrumentation/marker-beacon/outer")'),
            ("MKRM", "M", AMBER, 'getprop("instrumentation/marker-beacon/middle")'),
            ("MKRI", "I", WHITE, 'getprop("instrumentation/marker-beacon/inner")')]):
        p.add(Lamp(nm, -18.0 + 12.0 * k, 0.0, 9.0, 7.0, leg, lamp("ann_" + nm.lower(), expr), color=col,
                   legend_size=2.6 if len(leg) == 1 else 2.2))

    # ---- RADIO CALL (lights with an ATC message on the radio, press to reset)
    p = panel("GS.radiocall", brow_frame(0.318, 0.331), 32, 12, radius=1.5, ppm=12, screws=False)
    p.add(PushLight("RADIOCALL", 0.0, 0.0, 26.0, 8.0, [set_(FC + "radio-call", 0), CLICK], "RADIO CALL",
                    lamp("radio_call", 'getprop("controls/fusion/radio-call")'), color=WHITE, legend_size=2.2,
                    tooltip=tip("Radio call: lights when ATC calls on the radio, press to reset")))


# =================================================================================================================
# FLIGHT GUIDANCE PANEL
# =================================================================================================================
FGP_FRAME = tilted_frame((S.lip_x(0) + 0.013, Y0, 0.358), 8.0)


def fgp():
    p = panel("FGP", FGP_FRAME, 414, 62, radius=3, thick=4, elev=8, ppm=8, color=(0.10, 0.10, 0.105), screws=True)
    p.rect(-204, -28, 204, 28, width=0.9, radius=2.0, color=(0.72, 0.70, 0.64), lit=False)
    for x in (-155, -127, -97, -76, -41, -11, 49, 81, 114, 152):
        p.line([(x, -24), (x, 24)], 0.4, color=(0.55, 0.55, 0.55), lit=False)
    ap = lambda n: [nasal('FCS.btn_pressed("%s", 1, 0);' % n), CLICK]
    btn = dict(w=10.5, h=8.0, cap="cap", lamp_style="bar", lamp_color=GREEN, legend=None, depth=5.0)
    cols = {"FDL": -173, "VS": -141, "FLC": -57, "NAV": -26, "HDG": 4, "APPR": 34, "ALT": 65, "YD": 97, "AP": 133,
            "FDR": 172}
    top, bot = 12.5, -10.5

    def b(name, x, y, title, action, lampname, lampexpr, tooltip):
        p.add(Button("FGP." + name, x, y, action=action, title=title, title_dy=6.8, title_size=2.4,
                     lamp=lamp(lampname, lampexpr) if lampname else None, tooltip=tip(tooltip), **btn))

    b("FDL", cols["FDL"], top, "FD", [nasal('FCS.gfc_key("FD");'), CLICK], "fgp_fd",
      'getprop("autopilot/annunciator/flight-director-enabled")', "Flight director on / off")
    b("FDR", cols["FDR"], top, "FD", [nasal('FCS.gfc_key("FD");'), CLICK], "fgp_fd",
      'getprop("autopilot/annunciator/flight-director-enabled")', "Flight director on / off")
    b("VS", cols["VS"], top, "VS", ap("vs"), "fgp_vs", 'getprop("autopilot/annunciator/vertical-mode") == "VS"',
      "VS: vertical speed hold (pitch wheel sets the rate)")
    b("VNAV", cols["VS"], bot, "VNAV", [nasal("fusion.vnav();"), CLICK], "fgp_vnav",
      'getprop("controls/fusion/vnav")', "VNAV: vertical navigation (see the message)")
    b("FLC", cols["FLC"], top, "FLC", ap("ias"), "fgp_flc", 'getprop("autopilot/annunciator/vertical-mode") == "FLC"',
      "FLC: flight level change (holds the SPEED target)")
    b("NAV", cols["NAV"], top, "NAV", ap("nav"), "fgp_nav",
      'var m = getprop("autopilot/annunciator/lateral-mode"); var a = getprop("autopilot/annunciator/lateral-mode-armed"); (m == "GPS" or m == "VOR" or m == "LOC") or (a != "" and a != nil)',
      "NAV: lateral navigation (source: CDI of the coupled PFD)")
    b("BANK", cols["NAV"], bot, "1/2 BANK", ap("bnk"), "fgp_bank",
      'getprop("instrumentation/fgc-65/app-65a/BANK") != ""', "1/2 BANK: bank limit 14 deg")
    b("HDG", cols["HDG"], top, "HDG", ap("hdg"), "fgp_hdg", 'getprop("autopilot/annunciator/lateral-mode") == "HDG"',
      "HDG: heading select")
    b("APPR", cols["APPR"], top, "APPR", ap("appr"), "fgp_appr",
      'getprop("instrumentation/fgc-65/internal/appr-armed") or getprop("instrumentation/fgc-65/internal/appr-active")',
      "APPR: approach (localizer and glideslope)")
    b("ALT", cols["ALT"], top, "ALT", ap("alt"), "fgp_alt", 'getprop("autopilot/annunciator/vertical-mode") == "ALT"',
      "ALT: altitude hold")
    b("YD", cols["YD"], top, "YD", ap("yd"), "fgp_yd", 'getprop("controls/flight/yaw-damper")', "YD: yaw damper")
    b("CPL", cols["YD"], bot, "CPL", [nasal("fusion.couple_toggle();"), CLICK], None, None,
      "CPL: autopilot coupled to the pilot or copilot PFD")
    b("AP", cols["AP"], top, "AP", [nasal('FCS.btn_pressed("ap", 1, 0);'), CLICK], "fgp_ap",
      'getprop("autopilot/annunciator/autopilot-enabled")', "AP: autopilot engage / disengage")
    # couple arrows (left / right) either side of CPL
    p.add(Lamp("FGP.CPLL", cols["YD"] - 9.0, bot, 4.0, 5.0, "<", lamp("cpl_left", 'getprop("controls/fusion/couple") == 0'),
               color=GREEN, legend_size=3.2))
    p.add(Lamp("FGP.CPLR", cols["YD"] + 9.0, bot, 4.0, 5.0, ">", lamp("cpl_right", 'getprop("controls/fusion/couple") == 1'),
               color=GREEN, legend_size=3.2))
    # YD/AP DISC bar
    p.add(Button("FGP.DISC", cols["AP"], bot - 1.0, 34.0, 10.0,
                 [nasal("fusion.ap_yd_disconnect();"), CLICK], title="YD/AP  DISC", title_dy=7.2, title_size=2.3,
                 cap="cap", lamp=None, tooltip=tip("YD/AP DISC: disconnects the autopilot and the yaw damper")))
    # knobs
    knob = dict(style="fgp", d=15.5, h=11.0, color="knob_grey")
    p.add(Knob("FGP.CRS1", cols["FDL"], bot + 0.5, "sim/model/fusion/knobs/crs1", title="CRS1", title_dy=10.0,
               action=[fg1000(1, "CRS")], push=[fg1000(1, "CRS_CENTER"), CLICK], factor=15, offset=0, step=1,
               tooltip=tip("CRS1: pilot PFD course (push: centre on the station)"), **knob))
    p.add(Knob("FGP.CRS2", cols["FDR"], bot + 0.5, "sim/model/fusion/knobs/crs2", title="CRS2", title_dy=10.0,
               action=[fg1000(3, "CRS")], push=[fg1000(3, "CRS_CENTER"), CLICK], factor=15, offset=0, step=1,
               tooltip=tip("CRS2: copilot PFD course (push: centre on the station)"), **knob))
    p.add(Knob("FGP.SPD", cols["FLC"], bot + 0.5, "sim/model/fusion/knobs/spd", title="SPEED", title_dy=10.0,
               action=[nasal("fusion.speed_knob(cmdarg().getNode(\"offset\").getValue());")],
               push=[nasal("fusion.speed_sync();"), CLICK], factor=15, offset=0, step=1,
               tooltip=tip("SPEED: FLC target %d kt (push: current speed)", "autopilot/settings/target-speed-kt"), **knob))
    p.add(Knob("FGP.HDGK", cols["HDG"], bot + 0.5, "sim/model/fusion/knobs/hdg", title="HDG", title_dy=10.0,
               action=[nasal("fusion.heading_knob(cmdarg().getNode(\"offset\").getValue());")],
               push=[nasal("fusion.heading_sync();"), CLICK], factor=15, offset=0, step=1,
               tooltip=tip("HDG: heading bug %03d (push: sync on the current heading)", "autopilot/settings/heading-bug-deg"),
               **knob))
    p.add(Knob("FGP.ALTK", cols["ALT"], bot + 0.5, "sim/model/fusion/knobs/alt", title="ALT", title_dy=10.0,
               action=[fg1000(1, "ALT_INNER")], shift_step=[fg1000(1, "ALT_OUTER")], factor=15, offset=0, step=1,
               tooltip=tip("ALT: preselected altitude %d ft (shift: 1000 ft)", "autopilot/settings/target-alt-ft"),
               **knob))
    # pitch wheel
    p.add(Decor("FGP.WHEEL", -112.0, 0.0, "pitch_wheel"))
    p.text("DOWN", -99.0, 18.0, 2.2)
    p.text("UP", -99.0, -21.0, 2.2)
    p.line([(-99.0, 14.5), (-99.0, -16.0)], 0.4)
    p.line([(-100.3, 12.5), (-99.0, 15.0), (-97.7, 12.5)], 0.4)
    p.line([(-100.3, -14.0), (-99.0, -16.5), (-97.7, -14.0)], 0.4)
    p.add(Hotspot("FGP.PITCHUP", -112.0, 9.0, 12.0, 18.0, [nasal("FCS.pitch_wheel(-1);")],
                  tooltip=tip("Pitch wheel: nose DOWN (VS / FLC / pitch target)"), wheel=([nasal("FCS.pitch_wheel(-1);")],
                                                                                     [nasal("FCS.pitch_wheel(1);")])))
    p.add(Hotspot("FGP.PITCHDN", -112.0, -9.0, 12.0, 18.0, [nasal("FCS.pitch_wheel(1);")],
                  tooltip=tip("Pitch wheel: nose UP"), wheel=([nasal("FCS.pitch_wheel(-1);")], [nasal("FCS.pitch_wheel(1);")])))


# =================================================================================================================
# STANDBY FLIGHT DISPLAY (canvas: Nasal/fusion-standby.nas)
# =================================================================================================================
STBY_FRAME = tilted_frame((S.lip_x(0) - 0.004, Y0, 0.458), 8.0)


def standby():
    p = panel("STBY", STBY_FRAME, 150, 104, radius=5, thick=6, elev=0, ppm=6, color=(0.07, 0.07, 0.075), screws=True)
    p.add(Decor("STBY.SCREEN", -14.0, 2.0, "screen", w=100.0, h=75.0, object="Fusion.Stby.screen"))
    p.add(Button("STBY.MENU", 55.0, 22.0, 11.0, 9.0, [nasal("fusion_standby.menu();"), CLICK], legend="MENU",
                 cap="bezel_key", legend_color=WHITE, legend_size=2.2, tooltip=tip("Standby display: MENU (declutter)")))
    p.add(Button("STBY.BARO", 55.0, 6.0, 11.0, 9.0, [nasal("fusion_standby.baro_std();"), CLICK], legend="BARO",
                 cap="bezel_key", legend_color=WHITE, legend_size=2.2, tooltip=tip("Standby display: BARO STD / setting")))
    p.add(Knob("STBY.KNOB", 55.0, -26.0, "instrumentation/altimeter[1]/setting-inhg", lo=27.5, hi=31.5, step=0.01,
               factor=900, offset=0, style="bar", d=15.0, h=9.0, shift_step=0.1,
               push=[nasal("fusion_standby.baro_sync();"), CLICK],
               tooltip=tip("Standby altimeter setting: %.2f inHg (push: pilot PFD setting)", "instrumentation/altimeter[1]/setting-inhg")))


# =================================================================================================================
# MAIN PANEL: audio control panels and display control strip
# =================================================================================================================
def audio_panel(side):
    k = 0 if side == "L" else 1
    u = -535.0 if side == "L" else 535.0
    fr = S.MP.sub(u, -18.0, 0.0)
    p = panel("AUDIO" + side, fr, 76, 238, radius=3, thick=3, elev=0, ppm=7)
    a = "controls/fusion/audio[%d]/" % k
    p.add(Knob("AUD%s.XMT" % side, 0.0, 88.0, a + "xmit", lo=0, hi=3, step=1, factor=40, offset=-60,
               style="selector", d=14.0, h=9.0, positions=[(0, "1"), (1, "2"), (2, "PA"), (3, "HF")], pos_size=2.4,
               title="XMT", title_dy=15.5, tooltip=tip("Transmitter: %s", a + "xmit",
                                                        'return ["COM 1", "COM 2", "PA", "HF"][int(arg[0] or 0)];')))
    p.add(Knob("AUD%s.VOL" % side, 0.0, 70.0, a + "master-vol", lo=0.0, hi=1.0, step=0.05, factor=270,
               offset=-135, style="rheostat", d=9.0, h=6.0, title=None,
               tooltip=tip("Audio master volume: %.2f", a + "master-vol")))
    p.text("VOL", 8.0, 64.0, 2.0, align="l")
    p.add(Lamp("AUD%s.T" % side, -22.0, 60.0, 4.0, 4.0, "", lamp("xmit_%d" % k, 'getprop("controls/fusion/ptt[%d]")' % k),
               color=GREEN, shape="round"))
    p.text("T", -27.0, 59.0, 2.2)
    rx = [("COMM1", -16.0, 38.0), ("COMM2", 8.0, 38.0), ("NAV1", -16.0, 10.0), ("NAV2", 8.0, 10.0),
          ("DME1", -16.0, -18.0), ("DME2", 8.0, -18.0), ("ADF", -16.0, -46.0), ("MKR", 8.0, -46.0),
          ("PA", 27.0, 10.0)]
    for nm, x, y in rx:
        p.add(Knob("AUD%s.%s" % (side, nm), x, y, a + nm.lower() + "-vol", lo=0.0, hi=1.0, step=0.05, factor=270,
                   offset=-135, style="receiver", d=10.0, h=8.0,
                   push=[toggle(a + nm.lower()), CLICK],
                   tooltip=tip("%s receiver: click to pull on / push off, wheel for the volume (%%.2f)" % nm,
                               a + nm.lower() + "-vol")))
    for title, y in (("COMM", 38.0), ("NAV", 10.0), ("DME", -18.0)):
        p.text("1", -16.0, y + 9.0, 2.2)
        p.text(title, -4.0, y + 9.0, 2.2)
        p.text("2", 8.0, y + 9.0, 2.2)
        p.line([(-14.0, y + 10.0), (-8.5, y + 10.0)], 0.35)
        p.line([(0.5, y + 10.0), (6.0, y + 10.0)], 0.35)
    p.text("ADF", -16.0, -37.0, 2.2)
    p.text("MKR", 8.0, -37.0, 2.2)
    p.text("PA", 27.0, 19.0, 2.2)
    p.add(Toggle("AUD%s.MIC" % side, 27.0, 40.0, a + "mic-oxy", values=(0, 1), labels=("NORM", "OXY"), title="MIC",
                 label_side="left", title_size=2.2, label_size=2.0, tooltip=tip("Microphone: %s", a + "mic-oxy",
                                                                                 'return arg[0] ? "OXYGEN MASK" : "NORMAL";')))
    p.add(Toggle("AUD%s.MKRHI" % side, 27.0, -46.0, a + "mkr-hi", values=(0, 1), labels=("LO", "HI"), title="SENS",
                 label_side="left", title_size=2.0, label_size=2.0,
                 tooltip=tip("Marker beacon sensitivity: %s", a + "mkr-hi", 'return arg[0] ? "HI" : "LO";')))
    p.add(Toggle("AUD%s.IDENT" % side, 14.0, -84.0, a + "filter", values=(0, 1, 2), labels=("IDENT", "BOTH", "VOICE"),
                 title=None, label_side="left", label_size=2.0,
                 tooltip=tip("NAV audio filter: %s", a + "filter", 'return ["IDENT", "BOTH", "VOICE"][int(arg[0] or 0)];')))
    p.add(Toggle("AUD%s.EMER" % side, -16.0, -84.0, a + "emer", values=(0, 1), labels=("NORM", "EMER"),
                 label_side="right", label_size=2.0,
                 tooltip=tip("Audio EMER: %s", a + "emer", 'return arg[0] ? "EMERGENCY (COM 1 direct)" : "NORMAL";')))
    # BARO knob of the PFD on this side (the Fusion baro set)
    dev = 1 if side == "L" else 3
    p.add(Knob("AUD%s.BARO" % side, -16.0, -63.0, "sim/model/fusion/knobs/baro%d" % k, style="fgp", d=11.0, h=8.0,
               action=[fg1000(dev, "BARO")], push=[nasal("fusion.baro_std(%d);" % dev), CLICK], factor=15, offset=0,
               step=1, color="knob", title=None,
               tooltip=tip("BARO: %s PFD altimeter setting (push: STD)" % ("pilot" if side == "L" else "copilot"))))
    p.text("BARO", 1.0, -64.0, 2.2, align="l")


def strip():
    p = panel("STRIP", S.MP.sub(-12.0, -131.0, 0.0), 470, 36, radius=2.5, thick=2.5, elev=0, ppm=7)
    t = dict(title_size=2.1, label_size=1.9)
    # PROP SYNC
    p.add(PushLight("PSYNC", -218.0, 1.0, 11.0, 11.0, [toggle(FC + "prop-sync"), CLICK], "ON",
                    lamp("prop_sync", 'getprop("controls/fusion/prop-sync")'), color=GREEN, legend_size=2.2,
                    title="PROP\nSYNC", title_dy=8.5, title_size=2.1,
                    tooltip=tip("Propeller synchrophaser: %s", FC + "prop-sync", 'return arg[0] ? "ON" : "OFF";')))
    for side, xs in (("L", (-192.0, -170.0)), ("R", (205.0, 183.0))):
        k = 0 if side == "L" else 1
        p.add(Toggle("DGFREE" + side, xs[0], 0.0, FC + "dg-free[%d]" % k, values=(0, 1), labels=("NORM", None),
                     title="DG\nFREE", **t, tooltip=tip("AHRS heading: %s", FC + "dg-free[%d]" % k,
                                                        'return arg[0] ? "DG FREE (slave off)" : "SLAVED";')))
        p.add(Toggle("SLEW" + side, xs[1], 0.0, FC + "slew[%d]" % k, values=(-1, 0, 1), labels=("-", None, "+"),
                     momentary=(-1, 1), rest=0, title="SLEW", **t,
                     tooltip=tip("DG slew (DG FREE only): hold + / -")))
    # display reversion
    p.bracket(-158.0, -106.0, 13.0, "DISPLAY REVERSION", size=2.0)
    for nm, x in (("PFD1", -152.0), ("MFD", -132.0), ("PFD2", -112.0)):
        p.add(Toggle("REV" + nm, x, -2.0, FC + "reversion-" + nm.lower(), values=(0, 1), labels=("NORM", None),
                     title=nm.replace("PFD", "PFD ") + "\nOFF", title_size=1.9, label_size=1.8,
                     tooltip=tip("%s display: %%s" % nm, FC + "reversion-" + nm.lower(),
                                 'return arg[0] ? "OFF (reversion)" : "NORM";')))
    for nm, x in (("AHS", -88.0), ("ADS", -66.0)):
        p.add(Toggle(nm + "SRC", x, -2.0, FC + nm.lower() + "-source", values=(0, 1), labels=("PFD 2", None),
                     title=nm + "\nSOURCE\nPFD 1", title_size=1.9, label_size=1.8,
                     tooltip=tip("%s source for the pilot PFD: %%s" % nm, FC + nm.lower() + "-source",
                                 'return arg[0] ? "#1" : "#2 (cross-side)";')))
    p.bracket(-46.0, 14.0, 13.0, "DISPLAY CONTROL INHIBIT", size=2.0)
    for nm, x, three in (("PFD1", -38.0, True), ("MFD", -16.0, False), ("PFD2", 6.0, True)):
        vals = (-1, 0, 1) if three else (0, 1)
        labs = ("CURSOR", "NORM", None) if three else ("NORM", None)
        p.add(Toggle("INH" + nm, x, -2.0, FC + "inhibit-" + nm.lower(), values=vals, labels=labs,
                     title=nm.replace("PFD", "PFD ") + "\nTOUCH", title_size=1.9, label_size=1.8,
                     tooltip=tip("%s: %%s" % nm, FC + "inhibit-" + nm.lower(),
                                 'return {"-1": "CURSOR CONTROL INHIBITED", "0": "NORMAL", "1": "TOUCH INHIBITED"}[sprintf("%d", arg[0] or 0)];')))
    # pilot's static air source
    p.add(Toggle("ALTSTATIC", 122.0, -2.0, "controls/switches/alt-static", values=(0, 1), labels=("NORM", None),
                 prop_type="bool", title="PILOT'S STATIC\nAIR SOURCE\nALTERNATE", title_size=1.9, label_size=1.8,
                 tooltip=tip("Pilot's static air source: %s", "controls/switches/alt-static",
                             'return arg[0] ? "ALTERNATE" : "NORMAL";')))
    p.add(Button("EMERFREQ", 152.0, 1.0, 11.0, 11.0, [nasal("fusion.emer_freq();"), CLICK], legend=None,
                 cap="cap_dark", title="EMER\nFREQ", title_dy=8.5, title_size=2.1,
                 tooltip=tip("EMER FREQ: COM 1 on 121.500")))


# =================================================================================================================
# LOWER PANEL BAND
# =================================================================================================================
def lp(name, x0, x1, **kw):
    w = x1 - x0
    return panel(name, S.LP.sub((x0 + x1) / 2, 0.0, 0.0), w, 156, radius=3, thick=3, elev=0, **kw)


def lower_panels():
    sw = dict(title_size=2.3, label_size=2.0)
    # ------------------------------------------------------------------ pilot subpanel
    p = lp("PSUB", -528.0, -283.0, ppm=5)
    p.add(Toggle("MASTER", -108.0, 52.0, FC + "master-emer", values=(1, 0), labels=("EMER\nOFF", "NORM"),
                 guard=FC + "master-guard", title="DC\nMASTER", **sw,
                 tooltip=tip("DC master: %s (guarded)", FC + "master-emer", 'return arg[0] ? "EMER OFF" : "NORM";')))
    p.add(Toggle("BAT", -84.0, 52.0, "controls/electric/battery-switch", values=(0, 1), labels=("OFF", "ON"),
                 prop_type="bool", title=None, **sw, tooltip=tip("Battery: %s", "controls/electric/battery-switch",
                                                               'return arg[0] ? "ON" : "OFF";')))
    p.text("BAT", -84.0, 40.0, 2.3)
    for nm, x, eng in (("LGEN", -62.0, 0), ("RGEN", -40.0, 1)):
        p.add(Toggle(nm, x, 52.0, FC + "gen[%d]" % eng, values=(-1, 0, 1), labels=("RESET", "OFF", "ON"),
                     momentary=(-1,), rest=0, **sw,
                     tooltip=tip("%s generator: %%s" % ("Left" if eng == 0 else "Right"), FC + "gen[%d]" % eng,
                                 'return ["RESET", "OFF", "ON"][int(arg[0] or 0) + 1];')))
        p.text(("L" if eng == 0 else "R") + " GEN", x, 40.0, 2.3)
    p.text("AVIONICS", -4.0, 56.0, 2.2, align="r")
    p.text("MASTER", -4.0, 52.5, 2.2, align="r")
    p.text("POWER", -4.0, 49.0, 2.2, align="r")
    p.add(Toggle("AVMASTER", 6.0, 52.0, "controls/electric/avionics-switch", values=(0, 1), labels=("OFF", "ON"),
                 prop_type="bool", **sw, tooltip=tip("Avionics master: %s", "controls/electric/avionics-switch",
                                                      'return arg[0] ? "ON" : "OFF";')))
    p.rect(-22.0, 40.0, 20.0, 64.0, 0.35, radius=1.0)
    p.add(Toggle("STBYDSP", -108.0, 8.0, FC + "stby-display", values=(-1, 0, 1), labels=("TEST", "OFF", "ON"),
                 momentary=(-1,), rest=0, title="STBY DISPLAY", **sw,
                 tooltip=tip("Standby display: %s", FC + "stby-display", 'return ["TEST", "OFF", "ON"][int(arg[0] or 0) + 1];')))
    p.add(Toggle("BUSSENSE", -64.0, 8.0, FC + "bus-sense", values=(-1, 0, 1), labels=("RESET", "NORM", "TEST"),
                 momentary=(-1, 1), rest=0, title="BUS SENSE", **sw, tooltip=tip("Bus sense: TEST / RESET (hold)")))
    p.add(Toggle("GENTIES", -36.0, 8.0, FC + "gen-ties", values=(-1, 0, 1), labels=("OPEN", "NORM", "MAN\nCLOSE"),
                 momentary=(1,), rest=0, title="GEN TIES", **sw,
                 tooltip=tip("Generator ties: %s", FC + "gen-ties", 'return ["OPEN", "NORM", "MAN CLOSE"][int(arg[0] or 0) + 1];')))
    # engine anti-ice and actuators (around the yoke column)
    p.group(18.0, -36.0, 88.0, 34.0, "ENG ANTI-ICE", size=2.3, bottom="ACTUATORS")
    for nm, x, eng in (("L", 36.0, 0), ("R", 70.0, 1)):
        p.add(Toggle("ENGICE" + nm, x, 16.0, "controls/anti-ice/engine[%d]/inlet-heat" % eng, values=(0, 1),
                     labels=("OFF", "ON"), prop_type="bool", title="LEFT" if eng == 0 else "RIGHT", **sw,
                     tooltip=tip("%s engine anti-ice: %%s" % ("Left" if eng == 0 else "Right"),
                                 "controls/anti-ice/engine[%d]/inlet-heat" % eng, 'return arg[0] ? "ON" : "OFF";')))
        p.add(Toggle("ACT" + nm, x, -20.0, "controls/anti-ice/engine[%d]/actuator-standby" % eng, values=(0, 1),
                     labels=("MAIN", "STBY"), prop_type="bool", **sw,
                     tooltip=tip("%s anti-ice actuator: %%s" % ("Left" if eng == 0 else "Right"),
                                 "controls/anti-ice/engine[%d]/actuator-standby" % eng,
                                 'return arg[0] ? "STANDBY" : "MAIN";')))
    # ignition and engine start
    p.group(-120.0, -74.0, -56.0, -28.0, "IGNITION AND\nENGINE START", size=2.1, bottom="STARTER ONLY")
    for nm, x, eng in (("L", -104.0, 0), ("R", -72.0, 1)):
        p.add(Toggle("START" + nm, x, -50.0, FC + "start[%d]" % eng, values=(-1, 0, 1), labels=(None, "OFF", "ON"),
                     momentary=(-1,), rest=0, title="LEFT" if eng == 0 else "RIGHT", title_size=2.1, label_size=2.0,
                     tooltip=tip("%s ignition and engine start: %%s" % ("Left" if eng == 0 else "Right"), FC + "start[%d]" % eng,
                                 'return ["STARTER ONLY", "OFF", "ON (starter + ignition)"][int(arg[0] or 0) + 1];')))
    p.group(-50.0, -74.0, -14.0, -28.0, "AUTOFEATHER", size=2.1)
    p.add(Toggle("AUTOFTHR", -38.0, -52.0, FC + "autofeather", values=(-1, 0, 1), labels=("TEST", "OFF", "ARM"),
                 momentary=(-1,), rest=0, **sw,
                 tooltip=tip("Autofeather: %s", FC + "autofeather", 'return ["TEST", "OFF", "ARM"][int(arg[0] or 0) + 1];')))
    p.group(-8.0, -74.0, 14.0, -28.0, "PROP\nGOV TEST", size=2.0)
    p.add(Toggle("PROPTEST", 3.0, -52.0, "controls/engines/prop-overspeed-test", values=(0, 1), labels=("OFF", "TEST"),
                 momentary=(1,), rest=0, prop_type="bool", title=None, label_side="left", **sw,
                 tooltip=tip("Propeller overspeed governor test (hold)")))
    p.group(24.0, -74.0, 88.0, -44.0, "AUTO IGNITION", size=2.1)
    for nm, x, eng in (("L", 40.0, 0), ("R", 70.0, 1)):
        p.add(Toggle("AUTOIGN" + nm, x, -60.0, "controls/engines/engine[%d]/auto-ignition" % eng, values=(0, 1),
                     labels=("OFF", "ARM"), prop_type="bool", **sw,
                     tooltip=tip("%s auto ignition: %%s" % ("Left" if eng == 0 else "Right"),
                                 "controls/engines/engine[%d]/auto-ignition" % eng, 'return arg[0] ? "ARMED" : "OFF";')))
    p.add(Decor("PSUB.COLUMN", 50.0, 62.0, "column_boot"))

    # ------------------------------------------------------------------ lights and ice protection
    p = lp("LTS", -279.0, -170.0, ppm=6)
    x0 = -44.0
    lights = [("LDGL", "controls/lighting/landing-lights[0]", "LEFT"), ("LDGR", "controls/lighting/landing-lights[1]", "RIGHT"),
              ("TAXI", "controls/lighting/taxi-lights", "TAXI"), ("ICEL", "controls/lighting/ice-light", "ICE"),
              ("NAVL", "controls/lighting/nav-lights", "NAV"), ("RECOG", "controls/lighting/recog-lights", "RECOG")]
    for k, (nm, prop, title) in enumerate(lights):
        x = x0 + 15.0 * k
        p.add(Toggle(nm, x, 50.0, prop, values=(0, 1), prop_type="bool", labels=None, title=title, title_size=2.1,
                     tooltip=tip("%s light: %%s" % title.capitalize(), prop, 'return arg[0] ? "ON" : "OFF";')))
    p.bracket(x0 - 4.0, x0 + 19.0, 66.0, "LANDING", size=2.1)
    p.bracket(x0 - 4.0, x0 + 79.0, 40.0, "OFF", size=2.0, down=False)
    p.text("L", 48.5, 58.0, 2.4)
    p.text("I", 48.5, 55.0, 2.4)
    p.text("G", 48.5, 52.0, 2.4)
    p.text("H", 48.5, 49.0, 2.4)
    p.text("T", 48.5, 46.0, 2.4)
    p.text("S", 48.5, 43.0, 2.4)
    p.group(-53.0, -76.0, 53.0, 34.0, "ICE PROTECTION", size=2.4, bottom="OFF")
    p.text("WSHLD ANTI-ICE", -34.0, 27.0, 2.0)
    p.text("NORMAL", -34.0, 23.5, 2.0)
    for nm, x, k in (("WSHLDP", -42.0, 0), ("WSHLDC", -26.0, 1)):
        p.add(Toggle(nm, x, 11.0, FC + "wshld[%d]" % k, values=(-1, 0, 1), labels=None,
                     title=None, label_size=1.8,
                     tooltip=tip("%s windshield anti-ice: %%s" % ("Pilot" if k == 0 else "Copilot"), FC + "wshld[%d]" % k,
                                 'return ["HI", "OFF", "NORMAL"][int(arg[0] or 0) + 1];')))
        p.text("PILOT" if k == 0 else "COPILOT", x, 0.5, 1.9)
    p.text("OFF", -34.0, 11.0, 1.9)
    p.text("HI", -34.0, 3.5, 1.9)
    p.text("PROP", -1.0, 27.0, 2.0)
    p.add(Toggle("PROPAUTO", -8.0, 11.0, "controls/anti-ice/prop-heat", values=(0, 1), prop_type="bool", labels=None,
                 title="AUTO", title_size=2.0, tooltip=tip("Propeller deice AUTO: %s", "controls/anti-ice/prop-heat",
                                                            'return arg[0] ? "ON" : "OFF";')))
    p.add(Toggle("PROPMAN", 7.0, 11.0, "controls/anti-ice/prop-heat-manual", values=(0, 1), prop_type="bool",
                 labels=None, momentary=(1,), rest=0, title="MANUAL", title_size=2.0,
                 tooltip=tip("Propeller deice MANUAL (hold)")))
    p.text("FUEL VENT", 32.0, 27.0, 2.0)
    for nm, x, k in (("FVENTL", 24.0, 0), ("FVENTR", 40.0, 1)):
        p.add(Toggle(nm, x, 11.0, "controls/anti-ice/fuel-vent-heat[%d]" % k, values=(0, 1), prop_type="bool",
                     labels=None, title=None,
                     tooltip=tip("%s fuel vent heat: %%s" % ("Left" if k == 0 else "Right"),
                                 "controls/anti-ice/fuel-vent-heat[%d]" % k, 'return arg[0] ? "ON" : "OFF";')))
        p.text("LEFT" if k == 0 else "RIGHT", x, 0.5, 1.9)
    p.add(Toggle("BRKDEICE", -42.0, -38.0, "controls/anti-ice/brake-deice", values=(0, 1), prop_type="bool",
                 labels=None, title="BRAKE\nDEICE", title_size=2.0,
                 tooltip=tip("Brake deice: %s", "controls/anti-ice/brake-deice", 'return arg[0] ? "ON" : "OFF";')))
    p.add(Toggle("SURFDEICE", -24.0, -38.0, FC + "surface-deice", values=(-1, 0, 1), labels=("MANUAL", None, "SINGLE"),
                 momentary=(-1, 1), rest=0, title="SURFACE\nDEICE", title_size=2.0, label_size=1.8, label_side="right",
                 tooltip=tip("Surface deice: SINGLE cycle (click) / MANUAL (hold)")))
    p.add(Toggle("STALLHEAT", -2.0, -38.0, "controls/anti-ice/stall-warn-heat", values=(0, 1), prop_type="bool",
                 labels=None, title="STALL\nWARN", title_size=2.0,
                 tooltip=tip("Stall warning heat: %s", "controls/anti-ice/stall-warn-heat", 'return arg[0] ? "ON" : "OFF";')))
    p.text("PITOT", 22.0, -24.0, 2.0)
    for nm, x, k in (("PITOTL", 14.0, 0), ("PITOTR", 30.0, 1)):
        p.add(Toggle(nm, x, -38.0, "controls/anti-ice/pitot-heat[%d]" % k, values=(0, 1), prop_type="bool",
                     labels=None, title=None,
                     tooltip=tip("%s pitot heat: %%s" % ("Left" if k == 0 else "Right"), "controls/anti-ice/pitot-heat[%d]" % k,
                                 'return arg[0] ? "ON" : "OFF";')))
        p.text("LEFT" if k == 0 else "RIGHT", x, -49.5, 1.9)
    p.add(Knob("GEARRELAY", 44.0, -38.0, "controls/fusion/cb/gear-relay", lo=0, hi=1, step=1, factor=0, offset=0,
               style="cb", d=9.0, h=6.0, push=[toggle("controls/fusion/cb/gear-relay"), CLICK], title="LANDING\nGEAR",
               title_size=1.8, tooltip=tip("Landing gear relay circuit breaker: %s", "controls/fusion/cb/gear-relay",
                                           'return arg[0] ? "PULLED" : "IN";')))
    p.text("RELAY", 44.0, -48.0, 1.8)

    # ------------------------------------------------------------------ landing gear, beacon, strobe
    p = lp("GEAR", -166.0, -92.0, ppm=6)
    p.text("LDG GEAR CONTROL", -8.0, 70.0, 2.1)
    p.add(Decor("GEAR.SLOT", -16.0, 20.0, "gear_slot"))
    p.text("UP", -2.0, 44.0, 2.0)
    p.line([(-2.0, 32.0), (-2.0, 41.5)], 0.45)
    p.line([(-3.3, 39.5), (-2.0, 42.0), (-0.7, 39.5)], 0.45)
    p.text("DN", -2.0, -1.0, 2.0)
    p.line([(-2.0, 12.0), (-2.0, 2.5)], 0.45)
    p.line([(-3.3, 4.5), (-2.0, 2.0), (-0.7, 4.5)], 0.45)
    p.add(Button("DNLOCKREL", -30.0, 2.0, 7.0, 7.0, [set_("controls/gear/downlock-release", 1), CLICK],
                 release=[set_("controls/gear/downlock-release", 0)], cap="red_round", title="DOWN\nLOCK\nREL",
                 title_dy=6.0, title_size=1.8, tooltip=tip("Down lock release (hold)")))
    p.add(Button("HDLTEST", -2.0, -24.0, 7.0, 7.0, [set_("controls/gear/lights-test", 1), CLICK],
                 release=[set_("controls/gear/lights-test", 0)], cap="cap_dark_round", title="HDL LT\nTEST",
                 title_dy=5.5, title_size=1.8, tooltip=tip("Landing gear handle and lights test (hold)")))
    p.group(6.0, -40.0, 36.0, 64.0, None)
    p.text("L", 34.0, 60.0, 2.2)
    for nm, x, prop, title in (("BEACON", 13.0, "controls/lighting/beacon/switch", "BEACON"),
                               ("STROBE", 28.0, "controls/lighting/strobe/switch", "STROBE")):
        p.add(Toggle(nm, x, 46.0, prop, values=(0, 1), prop_type="bool", labels=None, title=title, title_size=1.9,
                     tooltip=tip("%s: %%s" % title.capitalize(), prop, 'return arg[0] ? "ON" : "OFF";')))
    p.text("OFF", 20.5, 35.5, 1.9)
    p.text("GEAR", 16.0, 27.0, 1.9)
    p.text("DOWN", 16.0, 24.0, 1.9)
    test = ' or getprop("controls/gear/lights-test")'
    for nm, x, y, g in (("GNOSE", 16.0, 17.0, 0), ("GLEFT", 12.0, 9.5, 1), ("GRIGHT", 20.0, 9.5, 2)):
        p.add(Lamp(nm, x, y, 7.0 if g == 0 else 6.0, 5.5, "NOSE" if g == 0 else ("L" if g == 1 else "R"),
                   lamp("gear_%d" % g, '(getprop("gear/gear[%d]/position-norm") or 0) >= 0.999' % g + test),
                   color=GREEN, legend_size=1.7 if g == 0 else 2.2))
    p.add(Toggle("TAILFLOOD", 28.0, -16.0, "controls/lighting/logo-lights", values=(0, 1), prop_type="bool",
                 labels=None, title="TAIL\nFLOOD", title_size=1.9,
                 tooltip=tip("Tail flood lights: %s", "controls/lighting/logo-lights", 'return arg[0] ? "ON" : "OFF";')))
    p.text("OFF", 28.0, -27.5, 1.9)
    lamp("gear_handle", '(getprop("gear/gear[0]/position-norm") or 0) > 0.001 and (getprop("gear/gear[0]/position-norm") or 0) < 0.999'
                        ' or getprop("controls/gear/lights-test") or getprop("controls/fusion/gear-warn")')

    # ------------------------------------------------------------------ centre: pressurization and flap gauges
    p = lp("CTR", -88.0, 88.0, ppm=3, color=(0.06, 0.06, 0.063))
    p.add(Gauge("FLAPIND", -58.0, -38.0, 44.0, "flap", [("surface-positions/flap-pos-norm",
                                                          [(0.0, -60.0), (0.4, 0.0), (1.0, 60.0)], "white")]))
    p.add(Gauge("CABCLIMB", 0.0, -38.0, 44.0, "cabin_climb", [("systems/pressurization/cabin-rate-fpm",
                                                               [(-3000, -150.0), (-1000, -60.0), (0, 0.0), (1000, 60.0), (3000, 150.0)], "white")]))
    p.add(Gauge("CABALT", 58.0, -38.0, 44.0, "cabin_alt", [
        ("systems/pressurization/cabin-altitude-ft", [(-1000, -165.0), (0, -150.0), (20000, 120.0), (35000, 150.0)], "white"),
        ("systems/pressurization/diff-psi", [(0.0, -160.0), (7.0, -20.0)], "orange")]))

    # ------------------------------------------------------------------ environmental
    p = lp("ENV", 92.0, 236.0, ppm=6)
    p.group(-68.0, -70.0, 68.0, 68.0, "ENVIRONMENTAL", size=2.4)
    kn = dict(style="rheostat", d=15.0, h=10.0, title_size=2.1)
    for row, y, zone in ((0, 38.0, "cockpit"), (1, -26.0, "cabin")):
        p.add(Knob("BLOWER" + zone[:3].upper(), -48.0, y, FC + "env/blower-" + zone, lo=0, hi=2, step=1, factor=60,
                   offset=-60, style="selector", d=15.0, h=10.0, positions=[(0, "AUTO"), (1, "LO"), (2, "HI")],
                   pos_size=1.8, title="BLOWER", title_dy=13.5, title_size=2.1,
                   tooltip=tip("%s blower: %%s" % zone.capitalize(), FC + "env/blower-" + zone,
                               'return ["AUTO", "LOW", "HIGH"][int(arg[0] or 0)];')))
        p.add(Knob("TEMP" + zone[:3].upper(), -16.0, y, FC + "env/temp-" + zone, lo=0.0, hi=1.0, step=0.05,
                   factor=270, offset=-135, title="TEMP", title_dy=13.5, positions=[(0.0, None), (1.0, "INCR")],
                   pos_size=1.8, tooltip=tip("%s temperature: %%.0f %%%%" % zone.capitalize(), FC + "env/temp-" + zone,
                                             'return arg[0] * 100;'), **{k: v for k, v in kn.items() if k != "title_size"}))
        p.text(zone.upper(), -32.0, y - 14.0, 2.1)
        p.line([(-56.0, y - 12.5), (-44.0, y - 12.5)], 0.35)
        p.line([(-20.0, y - 12.5), (-8.0, y - 12.5)], 0.35)
    p.add(Knob("ENVMODE", 20.0, 38.0, FC + "env/mode", lo=0, hi=4, step=1, factor=45, offset=-90, style="selector",
               d=13.0, h=9.0, positions=[(0, "OFF"), (1, "AUTO"), (2, "MAN\nCOOL"), (3, "MAN\nHEAT"), (4, "ELEC\nHEAT")],
               pos_size=1.8, pos_radius=12.0, title=None,
               tooltip=tip("Environmental mode: %s", FC + "env/mode",
                           'return ["OFF", "AUTO", "MAN COOL", "MAN HEAT", "ELEC HEAT"][int(arg[0] or 0)];')))
    p.text("MODE", 20.0, 23.0, 2.1)
    p.add(Toggle("MANTEMP", 54.0, 36.0, FC + "env/man-temp", values=(-1, 0, 1), labels=("DECR", None, "INCR"),
                 momentary=(-1, 1), rest=0, title="MAN TEMP", title_size=1.9, label_size=1.8,
                 tooltip=tip("Manual temperature (MAN HEAT / MAN COOL): hold INCR / DECR")))
    p.add(Toggle("ENVBLEED", 12.0, -28.0, "controls/pressurization/envir-low", values=(0, 1), prop_type="bool",
                 labels=("NORMAL", "LOW"), title="ENVIR\nBLEED AIR", title_size=1.9, label_size=1.8,
                 tooltip=tip("Environmental bleed air: %s", "controls/pressurization/envir-low",
                             'return arg[0] ? "LOW" : "NORMAL";')))
    p.text("BLEED AIR VALVES", 46.0, -12.0, 1.9)
    for nm, x, k in (("BLEEDL", 36.0, 0), ("BLEEDR", 56.0, 1)):
        p.add(Toggle(nm, x, -28.0, FC + "bleed[%d]" % k, values=(-1, 0, 1), labels=None, title="LEFT" if k == 0 else "RIGHT",
                     title_size=1.8,
                     tooltip=tip("%s bleed air valve: %%s" % ("Left" if k == 0 else "Right"), FC + "bleed[%d]" % k,
                                 'return ["PNEU & ENVIR OFF", "ENVIR OFF", "OPEN"][int(arg[0] or 0) + 1];')))
    p.text("OPEN", 46.0, -21.0, 1.7)
    p.text("ENVIR", 46.0, -27.5, 1.7)
    p.text("OFF", 46.0, -30.0, 1.7)
    p.text("PNEU & ENVIR OFF", 46.0, -40.5, 1.8)

    # ------------------------------------------------------------------ copilot subpanel
    p = lp("CSUB", 240.0, 528.0, ppm=5)
    p.add(Toggle("WDEFOG", -128.0, 44.0, FC + "window-defog", values=(0, 1), labels=("OFF", "ON"), title="WINDOW\nDEFOG",
                 **sw, tooltip=tip("Side window defog: %s", FC + "window-defog", 'return arg[0] ? "ON" : "OFF";')))
    p.add(Toggle("CABTEST", -96.0, 44.0, FC + "cabin-warn-test", values=(-1, 0, 1), labels=("DIFF", "OFF", "CABIN\nALT"),
                 momentary=(-1, 1), rest=0, title="PRESS WARN\nTEST", title_size=2.0, label_size=1.9,
                 tooltip=tip("Cabin altitude / differential warning test (hold)")))
    p.group(-140.0, -74.0, -66.0, -24.0, "ENG FIRE TEST", size=2.1, bottom="EXT")
    for nm, x, k in (("FTESTL", -122.0, 0), ("FTESTR", -86.0, 1)):
        p.add(Toggle(nm, x, -48.0, FC + "fire-test[%d]" % k, values=(-1, 0, 1), labels=(None, "OFF" if k == 0 else None, None),
                     momentary=(-1, 1), rest=0, title=None, label_size=1.9,
                     tooltip=tip("%s engine fire test: DET (up) / EXT (down), hold" % ("Left" if k == 0 else "Right"))))
        p.text("LEFT" if k == 0 else "RIGHT", x, -66.0, 1.9)
    p.text("DET", -104.0, -33.0, 1.9)
    p.add(Gauge("CABTEMP", 8.0, -12.0, 46.0, "cabin_temp", [("systems/environment/cabin-temp-degc",
                                                              [(0, -60.0), (30, 60.0)], "white")]))
    p.add(Gauge("HOURS", 62.0, -12.0, 46.0, "hobbs", []))
    p.add(Gauge("OXY", 114.0, -12.0, 46.0, "oxygen", [("systems/oxygen/pressure-psi",
                                                       [(0, -135.0), (2000, 135.0)], "white")]))
    p.add(Decor("CSUB.COLUMN", -29.0, 62.0, "column_boot"))

    # ------------------------------------------------------------------ parking brake handle (left knee panel)
    p = panel("PBRAKE", S.LP.sub(-542.0, -40.0, 0.0), 24, 60, radius=2, thick=2, elev=0, ppm=8, screws=False,
              color=(0.07, 0.07, 0.072))
    p.text("PARKING", 0.0, 22.0, 2.0)
    p.text("BRAKE", 0.0, 19.0, 2.0)
    p.add(Decor("PBRAKE.HANDLE", 0.0, -2.0, "pbrake_handle"))
    p.add(Hotspot("PBRAKE.HS", 0.0, -2.0, 18.0, 22.0, [toggle("controls/gear/brake-parking"), CLICK],
                  tooltip=tip("Parking brake: %s", "controls/gear/brake-parking", 'return arg[0] ? "SET" : "OFF";'), z=12.0))


# =================================================================================================================
# PEDESTAL
# =================================================================================================================
import pedestal as PD                                   # noqa: E402


def pedestal():
    # ---- power quadrant: flat drawing of the curved surface (built by controls3d.build_pedestal)
    L = PD.arc_len_mm()
    p = panel("PED.QUAD", PD.aft_frame(-4.3, 0.0), PD.QUAD_HW * 2000, L, radius=0, ppm=5, color=(0.07, 0.07, 0.075),
              screws=False, custom=True)
    y = PD.quad_y_mm
    for nm, off, prop, table, style, length in PD.LEVERS:
        a0, a1 = table[0][1], table[-1][1]
        p.rect(off * 1000 - 3.2, y(a0 - 3), off * 1000 + 3.2, y(a1 + 3), 0.1, 1.5, color=(0.01, 0.01, 0.01), lit=False,
               fill=(0.01, 0.01, 0.01))
    p.text("POWER", -57.0, y(47), 2.8)
    p.text("PROP", -2.0, y(47), 2.8)
    p.text("CONDITION", 52.0, y(47), 2.8)
    for a, lab in ((30, "TAKEOFF"), (-8, "IDLE"), (-17, "BETA"), (-26, "REVERSE")):
        p.line([(-82.0, y(a)), (-76.0, y(a))], 0.6)
        p.text(lab, -84.0, y(a) - 1.1, 2.0, align="r")
    p.text("CAUTION", -90.0, y(-2), 2.2, color=(1.0, 0.75, 0.1))
    p.text("REVERSE", -90.0, y(-6), 1.8)
    p.text("ONLY WITH", -90.0, y(-9), 1.8)
    p.text("ENGINES", -90.0, y(-12), 1.8)
    p.text("RUNNING", -90.0, y(-15), 1.8)
    for a in (-13, 28):
        p.line([(-23.0, y(a)), (19.0, y(a))], 0.5)
    p.text("1450", 21.0, y(-13) - 1.0, 1.8, align="l")
    p.text("1700", 21.0, y(28) - 1.0, 1.8, align="l")
    # feather stripes behind the propeller levers
    for k in range(6):
        col = (0.85, 0.08, 0.06) if k % 2 == 0 else (0.92, 0.92, 0.9)
        p.rect(-23.0, y(-30) + k * 2.6, 19.0, y(-30) + (k + 1) * 2.6, 0.1, color=col, lit=False, fill=col)
    p.text("FEATHER", -2.0, y(-33) - 1.0, 2.4)
    for a, lab in ((10, "HIGH IDLE"), (-6, "LOW IDLE"), (-22, "FUEL CUTOFF")):
        p.line([(34.0, y(a)), (70.0, y(a))], 0.5)
        p.text(lab, 72.0, y(a) - 1.0, 1.9, align="l")
    p.text("FRICTION LOCK", -57.0, y(-33) - 1.0, 1.8)
    p.text("FRICTION LOCK", 52.0, y(-33) - 1.0, 1.8)

    # ---- elevator trim indicator (left side of the quadrant, ahead of the trim wheel)
    p = panel("PED.ETRIM", Frame((-4.418, Y0 - PD.QUAD_HW, -0.335), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), 32, 90,
              radius=2, thick=1.0, ppm=10, color=(0.06, 0.06, 0.065), screws=False)
    p.text("ELEV TRIM", 0.0, 40.0, 2.2)
    p.text("NOSE DN", -2.0, 33.0, 2.0)
    p.text("NOSE UP", -2.0, -36.0, 2.0)
    p.line([(-4.0, -30.0), (-4.0, 30.0)], 0.5)
    for k in range(-6, 7):
        p.line([(-8.0 if k % 3 == 0 else -6.0, k * 5.0), (-4.0, k * 5.0)], 0.4)
    p.rect(-3.6, -10.5, -1.0, 0.0, 0.1, color=GREEN, lit=False, fill=GREEN)
    p.text("T.O.", 6.0, -6.2, 1.8, align="l", color=GREEN)

    # ---- trim face: aileron and rudder trim knobs
    p = panel("PED.TRIM", PD.trim_face_frame(0.0), 236, 176, radius=3, thick=3, ppm=4, color=(0.07, 0.07, 0.075))
    p.add(Knob("ATRIM", -52.0, -12.0, "controls/flight/aileron-trim", lo=-1.0, hi=1.0, step=0.01, factor=100,
               offset=0, style="trim", d=44.0, h=16.0, shift_step=0.05,
               tooltip=tip("Aileron trim: %.2f", "controls/flight/aileron-trim")))
    p.text("AILERON TRIM", -52.0, 30.0, 2.8)
    p.text("LEFT", -80.0, 20.0, 2.4)
    p.text("RIGHT", -24.0, 20.0, 2.4)
    p.add(Knob("RTRIM", 56.0, -12.0, "controls/flight/rudder-trim", lo=-1.0, hi=1.0, step=0.01, factor=100,
               offset=0, style="trim", d=44.0, h=16.0, shift_step=0.05,
               tooltip=tip("Rudder trim: %.2f", "controls/flight/rudder-trim")))
    p.text("RUDDER TRIM", 56.0, 30.0, 2.8)
    p.text("LEFT", 28.0, 20.0, 2.4)
    p.text("RIGHT", 84.0, 20.0, 2.4)
    for cx in (-52.0, 56.0):
        for a in range(-100, 101, 20):
            r0, r1 = 25.0, 27.5 if a % 50 else 29.0
            p.line([(cx + r0 * math.sin(math.radians(a)), -12.0 + r0 * math.cos(math.radians(a))),
                    (cx + r1 * math.sin(math.radians(a)), -12.0 + r1 * math.cos(math.radians(a)))], 0.6)
    p.add(Knob("FRICPWR", -100.0, -62.0, FC + "friction[0]", lo=0.0, hi=1.0, step=0.1, factor=270, offset=-135,
               style="rheostat", d=12.0, h=9.0, tooltip=tip("Power lever friction lock: %.0f %%", FC + "friction[0]",
                                                          'return arg[0] * 100;')))
    p.add(Knob("FRICPC", 100.0, -62.0, FC + "friction[1]", lo=0.0, hi=1.0, step=0.1, factor=270, offset=-135,
               style="rheostat", d=12.0, h=9.0, tooltip=tip("Propeller / condition lever friction lock: %.0f %%",
                                                          FC + "friction[1]", 'return arg[0] * 100;')))
    p.text("FRICTION", -100.0, -48.0, 1.9)
    p.text("FRICTION", 100.0, -48.0, 1.9)

    # ---- cursor control panels (FG1000: FMS, range, keys, radios), pilot and copilot
    for k in (0, 1):
        side = "L" if k == 0 else "R"
        p = panel("CCP" + side, PD.aft_frame(-3.965, -0.113 if k == 0 else 0.113), 104, 120, radius=4, thick=4, ppm=6,
                  color=(0.075, 0.075, 0.08))
        cc = lambda key, arg="1": nasal('fusion.ccp(%d, "%s", %s);' % (k, key, arg))
        knob_off = 'cmdarg().getNode("offset").getValue()'
        labels = ("PFD 1", "MFD") if k == 0 else ("MFD", "PFD 2")
        p.add(Toggle("CCP%s.DSPL" % side, -30.0, 46.0, FC + "ccp[%d]/display" % k, values=(0, 1), labels=labels,
                     horizontal=True, title="DISPLAY", title_size=2.2, label_size=2.0,
                     tooltip=tip("Cursor control: %s", FC + "ccp[%d]/display" % k,
                                 'return arg[0] ? "%s" : "%s";' % (labels[1], labels[0]))))
        key = dict(w=16.0, h=9.0, cap="cap_dark", legend_color=WHITE, legend_size=2.3, depth=4.5)
        for nm, x, yk in (("MENU", 0.0, 48.0), ("FPL", 20.0, 48.0), ("PROC", 40.0, 48.0), ("DTO", -34.0, -6.0),
                          ("CLR", 40.0, 26.0), ("ENT", 40.0, 10.0)):
            leg = {"DTO": "D→", "FPL": "FPL"}.get(nm, nm)
            hk = {"DTO": "DTO"}.get(nm, nm)
            p.add(Button("CCP%s.%s" % (side, nm), x, yk, action=[cc(hk), CLICK], legend=leg if nm != "DTO" else "D>",
                         tooltip=tip("%s (selected display)" % {"DTO": "DIRECT TO"}.get(nm, nm)), **key))
        p.add(Knob("CCP%s.RANGE" % side, -34.0, 20.0, "sim/model/fusion/knobs/range%d" % k, style="fgp", d=14.0, h=9.0,
                   color="knob", action=[nasal('fusion.ccp(%d, "RANGE", %s);' % (k, knob_off))], push=[cc("JOYSTICK_PRESS"), CLICK],
                   factor=15, offset=0, step=1, title="RANGE", title_dy=10.5,
                   tooltip=tip("Map range (push: pan mode)")))
        p.add(DualKnob("CCP%s.FMS" % side, 6.0, 14.0, outer=[nasal('fusion.ccp(%d, "FMS_OUTER", %s);' % (k, knob_off))],
                       inner=[nasal('fusion.ccp(%d, "FMS_INNER", %s);' % (k, knob_off))], push=[cc("FMS_CRSR"), CLICK],
                       d_outer=30.0, d_inner=18.0, title="FMS",
                       tooltip=tip("FMS knob: outer = page group / cursor, inner = page / value; push = CRSR")))
        for nm, x, dev in (("NAV", -26.0, "NAV"), ("COM", 26.0, "COM")):
            p.add(DualKnob("CCP%s.%s" % (side, nm), x, -36.0,
                           outer=[nasal('fusion.ccp(%d, "%s_OUTER", %s);' % (k, dev, knob_off))],
                           inner=[nasal('fusion.ccp(%d, "%s_INNER", %s);' % (k, dev, knob_off))],
                           push=[cc(dev + "_TOGGLE"), CLICK], d_outer=18.0, d_inner=11.0, title=nm,
                           tooltip=tip("%s standby frequency: outer MHz, inner kHz (push: %s)" %
                                       (nm, "ident" if nm == "NAV" else "squelch"))))
            p.add(Button("CCP%s.%sXFR" % (side, nm), x, -54.0, action=[cc(dev + "_FREQ_TRANSFER"), CLICK],
                         legend="<>", tooltip=tip("%s frequency transfer" % nm), **dict(key, w=14.0, h=8.0)))
    # ---- multifunction keyboard (FG1000 KEY_INPUT on the display of the last used cursor panel)
    p = panel("MKP", PD.aft_frame(-3.965, 0.0), 116, 120, radius=4, thick=4, ppm=5, color=(0.075, 0.075, 0.08))
    kk = dict(w=9.5, h=8.5, cap="cap_dark", legend_color=WHITE, legend_size=2.6, depth=4.0, travel=1.0)
    for i, ch in enumerate("1234567890"):
        p.add(Button("MKP.%s" % ch, -49.5 + 11.0 * i, 48.0, action=[nasal('fusion.mkp("%s");' % ch), CLICK], legend=ch,
                     **kk))
    rows = ["ABCDEFGHI", "JKLMNOPQR", "STUVWXYZ"]
    for r, row in enumerate(rows):
        for i, ch in enumerate(row):
            p.add(Button("MKP.%s" % ch, -44.0 + 11.0 * i, 33.0 - 14.0 * r, action=[nasal('fusion.mkp("%s");' % ch), CLICK],
                         legend=ch, **kk))
    fk = dict(kk, w=21.0, legend_size=2.3)
    for i, (nm, hk) in enumerate((("D>", "DTO"), ("MENU", "MENU"), ("FPL", "FPL"), ("PROC", "PROC"))):
        p.add(Button("MKP.F%d" % i, -39.0 + 26.0 * i, -14.0, action=[nasal('fusion.mkp_key("%s");' % hk), CLICK],
                     legend=nm, **fk))
    for nm, hk, x in (("CLR", "CLR", -39.0), ("ENT", "ENT", 39.0)):
        p.add(Button("MKP." + nm, x, -30.0, action=[nasal('fusion.mkp_key("%s");' % hk), CLICK], legend=nm,
                     **dict(fk, w=30.0)))
    for nm, off, x in (("PG-", -1, -39.0), ("PG+", 1, 39.0)):
        p.add(Button("MKP.PAGE%d" % (0 if off < 0 else 1), x, -46.0,
                     action=[nasal('fusion.mkp_key("FMS_OUTER", %d);' % off), CLICK], legend=nm, **dict(fk, w=30.0)))
    p.add(Button("MKP.CRSR", 0.0, -38.0, action=[nasal('fusion.mkp_key("FMS_CRSR");'), CLICK], legend="CRSR",
                 **dict(fk, w=24.0)))
    p.text("KEYS TO: CURSOR PANEL IN USE", 0.0, -57.0, 1.9)

    # ---- pressurization controller, rudder boost, electric trim, stall warning test
    p = panel("PRESS", PD.aft_frame(-3.824, 0.0), 300, 70, radius=3, thick=3, ppm=6, color=(0.075, 0.075, 0.08))
    p.group(-146.0, -32.0, -8.0, 30.0, "PRESSURIZATION", size=2.3)
    p.add(Knob("CABALTSEL", -118.0, -6.0, "controls/pressurization/cabin-alt-ft", lo=-1000, hi=10000, step=100,
               factor=0.024, offset=-132, style="selector", d=18.0, h=10.0, shift_step=1000,
               positions=[(0, "0"), (2000, "2"), (4000, "4"), (6000, "6"), (8000, "8"), (10000, "10")],
               pos_size=2.0, title="CABIN ALT", title_dy=16.5, title_size=2.1,
               tooltip=tip("Cabin altitude selector: %d ft", "controls/pressurization/cabin-alt-ft")))
    p.add(Knob("CABRATE", -74.0, -6.0, "controls/pressurization/rate-fpm", lo=50, hi=2000, step=50, factor=0.1385,
               offset=-135, style="rheostat", d=13.0, h=9.0, positions=[(50, "MIN"), (2000, "MAX")], pos_size=1.9,
               title="RATE", title_dy=13.5, title_size=2.1,
               tooltip=tip("Cabin rate of change: %d ft/min", "controls/pressurization/rate-fpm")))
    p.add(Toggle("CABPRESS", -36.0, -6.0, FC + "cabin-press", values=(-1, 0, 1), labels=("TEST", "PRESS", "DUMP"),
                 momentary=(-1,), rest=0, title="CABIN PRESS", title_size=2.0, label_size=1.9,
                 tooltip=tip("Cabin pressure: %s", FC + "cabin-press", 'return ["TEST (hold)", "PRESS", "DUMP"][int(arg[0] or 0) + 1];')))
    p.add(Toggle("RUDBOOST", 20.0, -6.0, "controls/flight/rudder-boost", values=(0, 1), prop_type="bool",
                 labels=("OFF", "ON"), title="RUDDER\nBOOST", title_size=2.0, label_size=1.9,
                 tooltip=tip("Rudder boost: %s", "controls/flight/rudder-boost", 'return arg[0] ? "ON" : "OFF";')))
    p.add(Toggle("ELECTRIM", 58.0, -6.0, FC + "elec-trim", values=(0, 1), labels=("OFF", "ON"), title="ELEV TRIM",
                 title_size=2.0, label_size=1.9, tooltip=tip("Electric elevator trim (control wheel switches): %s",
                                                            FC + "elec-trim", 'return arg[0] ? "ON" : "OFF";')))
    p.add(Toggle("STALLTEST", 96.0, -6.0, FC + "stall-test", values=(0, 1), labels=("OFF", "TEST"), momentary=(1,),
                 rest=0, title="STALL WARN", title_size=2.0, label_size=1.9, tooltip=tip("Stall warning test (hold)")))
    p.add(Toggle("GEARWARN", 132.0, -6.0, FC + "gear-warn-test", values=(0, 1), labels=("OFF", "TEST"), momentary=(1,),
                 rest=0, title="LDG GEAR\nWARN", title_size=2.0, label_size=1.9,
                 tooltip=tip("Landing gear warning horn test (hold)")))

    # ---- cockpit voice recorder
    p = panel("CVR", PD.aft_frame(-3.715, -0.080), 150, 70, radius=3, thick=3, ppm=6, color=(0.075, 0.075, 0.08))
    p.text("COCKPIT VOICE RECORDER", 0.0, 26.0, 2.4)
    p.add(Button("CVR.TEST", -44.0, -4.0, 9.0, 9.0, [set_(FC + "cvr-test", 1), CLICK], release=[set_(FC + "cvr-test", 0)],
                 cap="cap_dark_round", title="TEST", title_dy=8.0, tooltip=tip("CVR test (hold: the green light shows)")))
    p.add(Lamp("CVR.LAMP", -18.0, -4.0, 7.0, 7.0, "", lamp("cvr_ok", 'getprop("controls/fusion/cvr-ok")'), color=GREEN,
               shape="round"))
    p.add(Button("CVR.ERASE", 16.0, -4.0, 9.0, 9.0, [nasal("fusion.cvr_erase();"), CLICK], cap="cap_dark_round",
                 title="ERASE", title_dy=8.0, tooltip=tip("CVR erase (on the ground, parking brake set)")))
    p.text("HEADSET", 48.0, 6.0, 2.0)
    p.add(Decor("CVR.JACK", 48.0, -6.0, "jack"))
    p = panel("PED.BLANK", PD.aft_frame(-3.715, 0.085), 150, 70, radius=3, thick=3, ppm=1, color=(0.075, 0.075, 0.08))


# =================================================================================================================
# OVERHEAD, SIDE WALLS (fuel panel, circuit breakers)
# =================================================================================================================
OVH_TILT_SW = 12.0
OVH_TILT_G = 45.0


def ovh_frame(x, z, tilt, y_off=0.0):
    """Overhead face looking down: u = +y, 'up' on the face = aft (the crew looks up and forward)."""
    t = math.radians(tilt)
    return Frame((x, Y0 + y_off, z), (0.0, 1.0, 0.0), (math.cos(t), 0.0, math.sin(t)))


OVH_SW_FRAME = ovh_frame(-4.075, 0.848, OVH_TILT_SW)
OVH_G_FRAME = ovh_frame(-4.228, 0.795, OVH_TILT_G)


def wall_frame(side, x, z, y, tilt=12.0, yaw=0.0):
    """Side wall face (pilot's side: side -1, copilot: +1) centred at (x, y, z), tilted up by `tilt`; u runs forward
    on the left wall and aft on the right wall so that the text reads from the seats. The cabin lining of
    Models/KingAir.ac (object "interior") comes inboard towards the nose: `yaw` turns the face to follow it, and y
    leaves 3 mm between the plate and the lining (the panels are backed by a box that goes into the lining)."""
    t = math.radians(tilt)
    if side < 0:
        u, v = (-1.0, 0.0, 0.0), (0.0, -math.sin(t), math.cos(t))
    else:
        u, v = (1.0, 0.0, 0.0), (0.0, math.sin(t), math.cos(t))
    if yaw:
        u, v = rot_axis(u, (0, 0, 1), side * yaw), rot_axis(v, (0, 0, 1), side * yaw)
    return Frame((x, y, z), u, v)


def overhead():
    p = panel("OVH", OVH_SW_FRAME, 380, 250, radius=4, thick=3, ppm=4.5, color=(0.075, 0.075, 0.08))
    kn = dict(style="rheostat", d=16.0, h=11.0, lo=0.0, hi=1.0, step=0.05, factor=270, offset=-135, title_size=2.4,
              title_dy=14.5, pos_size=2.0)
    p.add(Toggle("MSTRPANEL", -160.0, 66.0, "controls/lighting/master-panel", values=(0, 1), prop_type="bool",
                 labels=("OFF", "ON"), title="MASTER\nPANEL LIGHTS", title_size=2.3, label_size=2.1,
                 tooltip=tip("Master panel lights: %s", "controls/lighting/master-panel", 'return arg[0] ? "ON" : "OFF";')))
    for nm, x, prop, title, t in (
            ("PANELLTS", -105.0, "controls/lighting/instruments-norm", "PANEL\nLIGHTS", "Panel back lighting"),
            ("DSPL1", -45.0, "sim/model/fusion/display-brightness[0]", "PILOT\nDISPLAYS", "Pilot PFD and standby brightness"),
            ("DSPL2", 15.0, "sim/model/fusion/display-brightness[1]", "MFD", "MFD brightness"),
            ("DSPL3", 75.0, "sim/model/fusion/display-brightness[2]", "COPILOT\nDISPLAY", "Copilot PFD brightness"),
            ("FLOODP", -80.0, "sim/model/fusion/flood[0]", "PANEL\nFLOOD", "Instrument panel flood lights"),
            ("FLOODD", -20.0, "sim/model/fusion/flood[1]", "PEDESTAL\nFLOOD", "Pedestal flood lights"),
            ("FLOODO", 40.0, "sim/model/fusion/flood[2]", "OVERHEAD\nFLOOD", "Overhead and side panel flood lights")):
        y = 66.0 if nm in ("PANELLTS", "DSPL1", "DSPL2", "DSPL3") else 6.0
        p.add(Knob("OVH." + nm, x, y, prop, positions=[(0.0, "OFF"), (1.0, "BRT")],
                   title=title, tooltip=tip(t + ": %.0f %%", prop, 'return arg[0] * 100;'), **kn))
    p.add(Toggle("ANNDIM", 150.0, 66.0, FC + "annun-dim", values=(0, 1), labels=("BRT", "DIM"), title="ANNUN",
                 title_size=2.3, label_size=2.1,
                 tooltip=tip("Annunciators: %s", FC + "annun-dim", 'return arg[0] ? "DIM" : "BRIGHT";')))
    p.add(Knob("OVH.WIPER", -152.0, 6.0, "controls/electric/wipers/switch-pos", lo=-1, hi=2, step=1, factor=40,
               offset=-20, style="selector", d=15.0, h=10.0,
               positions=[(-1, "PARK"), (0, "OFF"), (1, "SLOW"), (2, "FAST")], pos_size=2.0,
               title="WINDSHIELD\nWIPER", title_dy=16.0, title_size=2.2, prop_type="int",
               tooltip=tip("Windshield wiper: %s", "controls/electric/wipers/switch-pos",
                           'return ["PARK", "OFF", "SLOW", "FAST"][math.min(3, math.max(0, int(arg[0] or 0) + 1))];')))
    p.text("DO NOT OPERATE ON DRY GLASS", -152.0, -16.0, 1.8)
    p.add(Toggle("SIGNS", 110.0, 6.0, FC + "cabin-signs", values=(0, 1, 2), labels=("OFF", "FSB", "NO SMK\n& FSB"),
                 title="CABIN SIGNS", title_size=2.2, label_size=1.9,
                 tooltip=tip("Cabin signs: %s", FC + "cabin-signs", 'return ["OFF", "FASTEN SEAT BELTS", "NO SMOKING & FSB"][int(arg[0] or 0)];')))
    p.add(Toggle("CABLIGHTS", 160.0, 6.0, FC + "cabin-lights", values=(0, 1, 2), labels=("OFF", "DIM", "BRT"),
                 title="CABIN\nLIGHTS", title_size=2.2, label_size=1.9,
                 tooltip=tip("Cabin lights: %s", FC + "cabin-lights", 'return ["OFF", "DIM", "BRIGHT"][int(arg[0] or 0)];')))
    # placards
    p.rect(-186.0, -118.0, -20.0, -40.0, 0.35, 1.0)
    p.text("OPERATING LIMITATIONS", -103.0, -46.0, 2.2)
    lines = ["THIS AIRPLANE MUST BE OPERATED IN THE NORMAL", "CATEGORY IN COMPLIANCE WITH THE OPERATING",
             "LIMITATIONS STATED IN THE FORM OF PLACARDS,", "MARKINGS AND MANUALS. NO ACROBATIC MANEUVERS,",
             "INCLUDING SPINS, APPROVED. FLIGHT IN KNOWN", "ICING CONDITIONS APPROVED WITH REQUIRED",
             "EQUIPMENT OPERATIVE. REFER TO THE AFM."]
    for k, t in enumerate(lines):
        p.text(t, -103.0, -53.0 - k * 8.5, 1.6)
    p.rect(20.0, -118.0, 186.0, -40.0, 0.35, 1.0)
    p.text("MAXIMUM ALTITUDE 35 000 FT", 103.0, -52.0, 2.0)
    p.text("VMO 263 KIAS  -  MMO 0.58", 103.0, -62.0, 2.0)
    p.text("VLE 184 KIAS  -  VLO 184 KIAS", 103.0, -72.0, 2.0)
    p.text("VFE APPR 202 KIAS  -  DOWN 158 KIAS", 103.0, -82.0, 2.0)
    p.text("VA 184 KIAS  -  VMCA 94 KIAS", 103.0, -92.0, 2.0)
    p.text("MAX CABIN DIFF 6.6 PSI", 103.0, -102.0, 2.0)

    p = panel("OVHG", OVH_G_FRAME, 330, 62, radius=3, thick=3, ppm=8, color=(0.07, 0.07, 0.075))
    for k, (nm, dial, needles) in enumerate((
            ("DCLOADL", "dcload_l", [("systems/electrical/gen-load[0]", [(0.0, -135.0), (1.0, 135.0)], "white")]),
            ("DCLOADR", "dcload_r", [("systems/electrical/gen-load[1]", [(0.0, -135.0), (1.0, 135.0)], "white")]),
            ("BATTAMP", "battamps", [("systems/electrical/ammeter", [(-100.0, -120.0), (0.0, 0.0), (100.0, 120.0)], "white")]),
            ("VOLTS", "volts", [("systems/electrical/volts", [(0.0, -135.0), (30.0, 135.0)], "white")]),
            ("PROPAMP", "propamps", [("systems/anti-ice/prop-deice-amps", [(0.0, -135.0), (40.0, 135.0)], "white")]),
            ("OAT", "oat", [("environment/temperature-degc", [(-50.0, -135.0), (50.0, 135.0)], "white")]))):
        p.add(Gauge("OVHG." + nm, -137.5 + 55.0 * k, 0.0, 40.0, dial, needles, bezel=3.0, depth=5.0))


def fuel_panel():
    p = panel("FUEL", wall_frame(-1, -4.285, 0.040, -0.7288, yaw=3.5), 330, 118, radius=4, thick=3, ppm=5,
              color=(0.06, 0.06, 0.065), backing=40.0)
    # u runs forward on the left wall: x > 0 = towards the nose
    for side, x, i in (("L", -70.0, 0), ("R", 70.0, 1)):
        p.add(Gauge("FQTY" + side, x, -8.0, 56.0, "fuelqty", [("sim/model/fusion/fuel-qty-ind[%d]" % i,
                                                                [(0.0, -120.0), (2000.0, 120.0)], "white")]))
        p.text("LEFT" if i == 0 else "RIGHT", x, -44.0, 2.4)
    p.text("FUEL QTY", 0.0, 50.0, 2.6)
    p.add(Toggle("XFEED", 0.0, 32.0, FC + "crossfeed", values=(-1, 0, 1), labels=("LEFT", "OFF", "RIGHT"),
                 horizontal=True, title="CROSSFEED FLOW", title_size=2.2, label_size=2.0,
                 tooltip=tip("Fuel crossfeed: %s", FC + "crossfeed",
                             'return ["LEFT (right main feeds left engine)", "OFF", "RIGHT (left main feeds right engine)"][int(arg[0] or 0) + 1];')))
    p.line([(-14.0, 30.0), (-30.0, 30.0)], 0.5)
    p.line([(14.0, 30.0), (30.0, 30.0)], 0.5)
    p.add(Toggle("FQSEL", 0.0, -30.0, FC + "fuel-qty-select", values=(-1, 0, 1), labels=("TEST", "MAIN", "AUXILIARY"),
                 momentary=(-1,), rest=0, title="FUEL QUANTITY", title_size=2.1, label_size=1.9,
                 tooltip=tip("Fuel quantity gauges: %s", FC + "fuel-qty-select",
                             'return ["TEST", "MAIN tanks", "AUXILIARY tanks"][int(arg[0] or 0) + 1];')))
    p.rect(-26.0, -4.0, 26.0, 18.0, 0.4, 0.5)
    p.text("USABLE FUEL", 0.0, 13.5, 1.8)
    p.text("2067 LB EACH MAIN", 0.0, 9.0, 1.7)
    p.text("533 LB EACH AUX", 0.0, 4.5, 1.7)
    p.text("SEE MANUAL", 0.0, 0.0, 1.7)
    for side, x, i in (("L", -142.0, 0), ("R", 142.0, 1)):
        p.add(Toggle("STBYPUMP" + side, x, 30.0, FC + "stby-pump[%d]" % i, values=(0, 1), labels=("OFF", "ON"),
                     title="STBY PUMP", title_size=2.0, label_size=1.9, label_side="left" if i == 1 else "right",
                     tooltip=tip("%s standby fuel pump: %%s" % ("Left" if i == 0 else "Right"), FC + "stby-pump[%d]" % i,
                                 'return arg[0] ? "ON" : "OFF";')))
        p.add(Toggle("AUXXFER" + side, x, -24.0, FC + "aux-xfer[%d]" % i, values=(-1, 0, 1),
                     labels=("OFF", "AUTO", "OVRD"), title="AUX XFER", title_size=2.0, label_size=1.9,
                     label_side="left" if i == 1 else "right",
                     tooltip=tip("%s aux transfer: %%s" % ("Left" if i == 0 else "Right"), FC + "aux-xfer[%d]" % i,
                                 'return ["OFF", "AUTO", "OVERRIDE"][int(arg[0] or 0) + 1];')))


# circuit breakers: id (controls/fusion/cb/<id>, 1 = pulled), label, amps
CB_LEFT = [
    ("FUEL SYSTEM", [("stby-pump[0]", "STBY PUMP\nLEFT", 10), ("stby-pump[1]", "STBY PUMP\nRIGHT", 10),
                     ("aux-xfer[0]", "AUX XFER\nLEFT", 5), ("aux-xfer[1]", "AUX XFER\nRIGHT", 5),
                     ("crossfeed", "CROSS\nFEED", 5), ("fuel-qty-main", "QTY IND\nMAIN", 5),
                     ("fuel-qty-aux", "QTY IND\nAUX", 5), ("fw-valve[0]", "F/W VALVE\nLEFT", 5),
                     ("fw-valve[1]", "F/W VALVE\nRIGHT", 5), ("fuel-press-warn", "FUEL PRESS\nWARN", 5)]),
    ("ENGINE", [("start[0]", "IGN START\nLEFT", 5), ("start[1]", "IGN START\nRIGHT", 5),
                ("auto-ign[0]", "AUTO IGN\nLEFT", 5), ("auto-ign[1]", "AUTO IGN\nRIGHT", 5),
                ("autofeather", "AUTO\nFEATHER", 5), ("prop-sync", "PROP\nSYNC", 5), ("prop-gov-test", "PROP GOV\nTEST", 5),
                ("eng-ice[0]", "ENG ANTI\nICE LEFT", 5), ("eng-ice[1]", "ENG ANTI\nICE RIGHT", 5),
                ("fire-det", "FIRE\nDETECT", 5)]),
    ("LIGHTS", [("landing-lights[0]", "LANDING\nLEFT", 15), ("landing-lights[1]", "LANDING\nRIGHT", 15),
                ("taxi-lights", "TAXI", 10), ("nav-lights", "NAV", 5), ("beacon", "BEACON", 5), ("strobe", "STROBE", 10),
                ("recog-lights", "RECOG", 10), ("ice-light", "ICE", 5), ("logo-lights", "TAIL\nFLOOD", 5),
                ("cabin-lights", "CABIN", 10)]),
    ("MISC", [("instrument-lights", "PANEL\nLIGHTS", 5), ("flood", "FLOOD\nLIGHTS", 5), ("wipers", "WSHLD\nWIPER", 10),
              ("hobbs", "HOUR\nMETER", 2), ("cvr", "CVR", 5), ("annunciators", "ANNUN\nPOWER", 5),
              ("gear-warn", "GEAR\nWARN", 5), ("stall-warn", "STALL\nWARN", 5), ("oxygen", "OXYGEN\nIND", 2),
              ("cabin-signs", "CABIN\nSIGNS", 5)]),
]
CB_RIGHT = [
    ("AVIONICS", [("fg1000-pfd", "PFD 1", 7), ("fg1000-mfd", "MFD", 7), ("fg1000-pfd2", "PFD 2", 7),
                  ("stby-display", "STBY\nDSPL", 5), ("comm", "COM 1", 5), ("comm[1]", "COM 2", 5), ("nav", "NAV 1", 3),
                  ("nav[1]", "NAV 2", 3), ("dme", "DME", 3), ("adf", "ADF", 3), ("transponder", "XPDR", 3)]),
    ("AVIONICS", [("audio-panel", "AUDIO\n1", 5), ("audio-panel[1]", "AUDIO\n2", 5), ("gps", "FMS\nGPS", 5),
                  ("fgc-65", "FLT GUID\nPANEL", 5), ("autopilot", "AP\nSERVOS", 5), ("mk-viii", "TAWS", 3),
                  ("turn-coordinator", "AHRS", 5), ("ccp", "CCP\nMKP", 3), ("avionics", "AVIONICS\nMASTER", 5),
                  ("ext-power", "EXT\nPWR", 5), ("gen[0]", "GEN CONT\nLEFT", 5)]),
    ("FLIGHT", [("gen[1]", "GEN CONT\nRIGHT", 5), ("flap-motor", "FLAP\nMOTOR", 20), ("flap-control", "FLAP\nCONTROL", 5),
                ("gear-control", "GEAR\nCONTROL", 5), ("elec-trim", "PITCH\nTRIM", 5), ("rudder-boost", "RUDDER\nBOOST", 5),
                ("yaw-damper", "YAW\nDAMP", 5), ("press-control", "PRESS\nCONTROL", 5), ("temp-control", "TEMP\nCONTROL", 5),
                ("blower[0]", "BLOWER\nCKPT", 15), ("blower[1]", "BLOWER\nCABIN", 20)]),
    ("ICE PROTECTION", [("window-heat[0]", "WSHLD\nPILOT", 25), ("window-heat[1]", "WSHLD\nCOPILOT", 25),
                        ("pitot-heat[0]", "PITOT\nLEFT", 7), ("pitot-heat[1]", "PITOT\nRIGHT", 7),
                        ("stall-warn-heat", "STALL\nHEAT", 7), ("prop-heat", "PROP\nDEICE", 25),
                        ("surface-deice", "SURF\nDEICE", 5), ("fuel-vent-heat[0]", "FUEL VENT\nLEFT", 5),
                        ("fuel-vent-heat[1]", "FUEL VENT\nRIGHT", 5), ("brake-deice", "BRAKE\nDEICE", 10),
                        ("window-defog", "WINDOW\nDEFOG", 7)]),
    ("ENVIRONMENTAL", [("bleed[0]", "BLEED VLV\nLEFT", 5), ("bleed[1]", "BLEED VLV\nRIGHT", 5),
                       ("elec-heat", "ELEC\nHEAT", 5)]),
]


def cb_panel(name, frame, groups, w, h, cols, dx, dy):
    p = panel(name, frame, w, h, radius=4, thick=3, ppm=5, color=(0.06, 0.06, 0.065), backing=40.0)
    x0 = -(cols - 1) * dx / 2.0
    y = h / 2.0 - 20.0
    for title, cbs in groups:
        p.line([(-w / 2 + 6, y + 12.5), (w / 2 - 6, y + 12.5)], 0.35)
        tw = len(title) * 1.35 + 4.0
        p.rect(-tw / 2 - 1.5, y + 11.0, tw / 2 + 1.5, y + 14.0, 0.1, color=(0.06, 0.06, 0.065), lit=False,
               fill=(0.06, 0.06, 0.065))
        p.text(title, 0.0, y + 12.5, 2.1)
        for k, (cid, label, amps) in enumerate(cbs):
            x = x0 + k * dx
            p.add(Knob("CB.%s" % cid.replace("[", "").replace("]", ""), x, y - 3.0,
                       "controls/fusion/cb/" + cid, lo=0, hi=1, step=1, factor=0, offset=0, style="cb",
                       d=8.5, h=5.5, push=[toggle("controls/fusion/cb/" + cid), CLICK], title=None,
                       tooltip=tip("Circuit breaker %s (%d A): %%s" % (label.replace("\n", " "), amps),
                                   "controls/fusion/cb/" + cid, 'return arg[0] ? "PULLED" : "IN";')))
            for j, t in enumerate(label.split("\n")):
                p.text(t, x, y + 7.2 - j * 2.3, 1.55)
            p.text(str(amps), x + 6.0, y - 9.0, 1.5, align="l")
        y -= dy
    return p


def side_panels():
    fuel_panel()
    cb_panel("CBL", wall_frame(-1, -4.270, -0.190, -0.7376, tilt=3.0, yaw=4.0), CB_LEFT, 360, 170, 10, 34.0, 38.0)
    cb_panel("CBR", wall_frame(1, -4.255, -0.080, 0.7587, tilt=3.0, yaw=4.0), CB_RIGHT, 380, 250, 11, 33.0, 43.0)


# =================================================================================================================
def build():
    glareshield()
    fgp()
    standby()
    audio_panel("L")
    audio_panel("R")
    strip()
    lower_panels()
    pedestal()
    overhead()
    side_panels()
    return PANELS, LAMPS


build()
