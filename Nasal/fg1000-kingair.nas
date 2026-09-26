#############################################################################
# King Air 350 - FG1000 (Garmin G1000 NXi retrofit) integration.
#
# Follows the reference integration of the FGData c182t: the FG1000 Nasal is loaded from
# $FG_ROOT/Aircraft/Instruments-3d/FG1000 into the "fg1000" namespace, with King Air specific parts:
# - interface controller with a twin turboprop engine/fuel publisher (Nasal/fg1000-kingair-interfaces.nas),
# - twin turboprop EIS strip on the MFD (Nasal/fg1000-kingair-eis.nas, Models/Instruments/FG1000/EIS-KingAir.svg),
# - pilot and copilot PFDs (FG1000 displays 1 and 3) with the MFD in between, as in the G1000 NXi retrofits,
# - PFDs: King Air 350 V-speeds and airspeed tape markings, CAS messages in the annunciation window
#   (fed by Nasal/annunciators.nas).
# Speeds and markings: FlightSafety King Air 300/350 Pilot Training Manual (airspeed limits, 350 airspeed
# indicator markings) and the King Air 350 checklist (Vr).
#
# The displays are the GDU-1044B bezel models placed by Models/KingAir-G1000.xml.
# Power: /systems/electrical/outputs/fg1000-pfd, fg1000-mfd and fg1000-pfd2 (Nasal/electrical.nas, avionics bus).
#
# License: GPL v2 or later
#############################################################################

var fg_root = getprop("/sim/fg-root");
var nasal_dir = fg_root ~ "/Aircraft/Instruments-3d/FG1000/Nasal/";
var aircraft_dir = getprop("/sim/aircraft-dir");
var available = (io.stat(nasal_dir ~ "FG1000.nas") != nil);

var fg1000system = nil;

# FG1000 display index -> power output (Nasal/electrical.nas). Display 3 is the copilot PFD (GDU-1044B.3.xml).
var PFDS = [1, 3];
var POWER = {1: "fg1000-pfd", 2: "fg1000-mfd", 3: "fg1000-pfd2"};

# ---------------------------------------------------------------------------
# PFD airspeed tape (King Air 350 airspeed indicator markings)
# ---------------------------------------------------------------------------
var VSO   = 81;     # full flap stall speed: bottom of the white arc
var VS    = 96;     # flaps up stall speed: wide/narrow white arc limit
var VFE   = 158;    # flaps down
var VFE_APP = 202;  # flaps approach
var VMO   = 263;
var VMCA  = 94;     # red line
var VYSE  = 125;    # blue line

var tape_y = func(kt) { 284.5 - 5.711 * kt; };   # FG1000 speed tape: 5.711 px/kt, 0 kt at y 284.5

var draw_speed_tape = func(pfd) {
    var g = pfd.PFDInstruments.getElement("SpeedTape").createChild("group", "KingAirSpeedMarks");
    var band = func(from, to, x, w, colour) {
        g.createChild("path").rect(x, tape_y(to), w, (to - from) * 5.711).setColorFill(colour).setColor(colour);
    };
    var line = func(kt, colour) {
        g.createChild("path").rect(222, tape_y(kt) - 1.5, 17, 3).setColorFill(colour).setColor(colour);
    };
    # white arc: wide from Vso to Vs, narrow up to Vfe; approach flap limit tick
    band(VSO, VS, 233, 6, [1, 1, 1]);
    band(VS, VFE, 236, 3, [1, 1, 1]);
    g.createChild("path").rect(229, tape_y(VFE_APP) - 1, 10, 2).setColorFill(1, 1, 1).setColor(1, 1, 1);
    # Vmo barber pole
    for (var kt = VMO; kt < 460; kt += 10) {
        band(kt, kt + 5, 233, 6, [1, 0, 0]);
        band(kt + 5, kt + 10, 233, 6, [1, 1, 1]);
    }
    line(VMCA, [1, 0, 0]);
    line(VYSE, [0.2, 0.5, 1]);
};

var set_vspeeds = func(config) {
    config.set("Vne", VMO);         # IAS box turns red above Vmo
    config.set("Vr", 110);          # rotate (checklist: V1 105, Vr 110, V2 115)
    config.set("Vx", 125);          # two-engine best angle of climb
    config.set("Vy", 140);          # two-engine best rate of climb
    config.set("Vglide", 135);      # maximum range glide
};

# ---------------------------------------------------------------------------
# PFD CAS window: the FG1000 annunciation window (right of the altitude tape) lists the messages
# of Nasal/annunciators.nas, warnings (red) first, then cautions (amber) and advisories (white).
# Unacknowledged warnings/cautions (MASTER WARNING/CAUTION not yet pressed) flash in inverse video.
# ---------------------------------------------------------------------------
var CAS_LINES = 5;
var CAS_COLOURS = [[1, 0.1, 0.1], [1, 0.85, 0], [1, 1, 1]];

var cas = [];          # one entry per PFD: {pfd, lines, visible}
var cas_blink = 0;
var cas_timer = nil;

var init_cas = func(pfd) {
    var win = pfd.PFDInstruments.getElement("Annunciation");
    var lines = [];
    for (var i = 0; i < CAS_LINES; i += 1) {
        append(lines, win.createChild("text")
            .setFont("LiberationFonts/LiberationSansNarrow-Regular.ttf")
            .setFontSize(17, 1.0)
            .setAlignment("left-baseline")
            .setDrawMode(canvas.Text.TEXT + canvas.Text.FILLEDBOUNDINGBOX)   # background = inverse video
            .setColorFill(0, 0, 0, 0)
            .setTranslation(882, 404 + 20 * i)
            .setText(""));
    }
    append(cas, {pfd: pfd, lines: lines, visible: -1});
    if (cas_timer == nil) {
        cas_timer = maketimer(0.25, update_cas);
        cas_timer.start();
    }
};

var update_cas = func {
    var msgs = annunciators.messages;
    var show = size(msgs) > 0;
    cas_blink = !cas_blink;
    var unack = [getprop("instrumentation/annunciators/warning/Master"),
                 getprop("instrumentation/annunciators/caution/Master"), 0];
    foreach (var c; cas) {
        if (show != c.visible) {
            c.pfd.PFDInstruments.setAnnunciation(show);
            c.visible = show;
        }
        for (var i = 0; i < CAS_LINES; i += 1) {
            var t = c.lines[i];
            if (i >= size(msgs)) {
                t.setText("").setColorFill(0, 0, 0, 0);
                continue;
            }
            var colour = CAS_COLOURS[msgs[i].level];
            t.setText(msgs[i].text);
            if (unack[msgs[i].level] and cas_blink) {
                t.setColor(0, 0, 0).setColorFill(colour);
            } else {
                t.setColor(colour).setColorFill(0, 0, 0, 0);
            }
        }
    }
};

# ---------------------------------------------------------------------------

var init = func {
    if (!available) {
        gui.popupTip("FG1000 not found in this FlightGear installation ($FG_ROOT/Aircraft/Instruments-3d/FG1000): G1000 displays disabled", 10);
        print("KingAir-350ER G1000: FG1000 not found in " ~ nasal_dir);
        return;
    }
    setprop("/sim/model/g1000/enabled", 1);

    io.load_nasal(nasal_dir ~ "FG1000.nas", "fg1000");
    # King Air interface controller (replaces Interfaces/GenericInterfaceController.nas)
    io.load_nasal(aircraft_dir ~ "/Nasal/fg1000-kingair-interfaces.nas", "fg1000");
    # King Air EIS (replaces EIS/EIS-C182T.nas)
    io.load_nasal(aircraft_dir ~ "/Nasal/fg1000-kingair-eis.nas", "fg1000");

    var interfaceController = fg1000.KingAirInterfaceController.getOrCreateInstance();
    interfaceController.start();

    fg1000system = fg1000.FG1000.getOrCreateInstance(fg1000.KingAirEIS,
                                                     aircraft_dir ~ "/Models/Instruments/FG1000/EIS-KingAir.svg");
    set_vspeeds(fg1000system.getConfigStore());
    fg1000system.addPFD(1);
    fg1000system.addMFD(2);
    fg1000system.addPFD(3);
    foreach (var i; [1, 2, 3])
        fg1000system.display(i);

    foreach (var i; PFDS) {
        var pfd = fg1000system.getDisplay(i);
        # the PFD also parses the EIS SVG (reversionary mode is not simulated): keep its frame hidden
        pfd._svg.getElementById("EISGroup").hide();
        draw_speed_tape(pfd);
        init_cas(pfd);
    }

    # displays follow the avionics bus
    foreach (var i; [1, 2, 3]) {
        (func(index) {
            setlistener("/systems/electrical/outputs/" ~ POWER[index], func(n) {
                if ((n.getValue() or 0) > 15) fg1000system.show(index); else fg1000system.hide(index);
            }, 1, 0);
        })(i);
    }

    print("KingAir-350ER G1000: FG1000 pilot PFD, MFD and copilot PFD initialised");
};

# pop-up windows (menu)
var gui_pfd = func { if (fg1000system != nil) fg1000system.displayGUI(1, 0.66); };
var gui_mfd = func { if (fg1000system != nil) fg1000system.displayGUI(2, 0.66); };
var gui_pfd2 = func { if (fg1000system != nil) fg1000system.displayGUI(3, 0.66); };

setlistener("/sim/signals/fdm-initialized", func { settimer(init, 2.0); }, 0, 0);
