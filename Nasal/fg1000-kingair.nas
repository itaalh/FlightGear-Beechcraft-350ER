#############################################################################
# King Air 350 - FG1000 (Garmin G1000 NXi retrofit) integration.
#
# Follows the reference integration of the FGData c182t: the FG1000 Nasal is loaded from
# $FG_ROOT/Aircraft/Instruments-3d/FG1000 into the "fg1000" namespace, with King Air specific parts:
# - interface controller with a twin turboprop engine/fuel publisher (Nasal/fg1000-kingair-interfaces.nas),
# - twin turboprop EIS strip on the MFD (Nasal/fg1000-kingair-eis.nas, Models/Instruments/FG1000/EIS-KingAir.svg),
# - pilot and copilot PFDs (FG1000 displays 1 and 3) with the MFD in between, as in the G1000 NXi retrofits,
# - PFDs: King Air 350 V-speeds and airspeed tape markings, CAS messages in the annunciation window
#   (fed by Nasal/annunciators.nas),
# - autopilot: the GDU autopilot keys and the CDI source of the pilot PFD drive the King Air autopilot
#   (Nasal/autopilot.nas, namespace FCS), whose modes are shown on the PFD.
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
# PFD time box: UTC (Z) in 24 h, as the cockpit clocks, instead of the FG1000 default local time in 12 h
# ("LCL", /sim/time/local-day-seconds). The controller refreshes it every second.
# ---------------------------------------------------------------------------
var set_utc_time = func(pfd) {
    var label = pfd._svg.getElementById("text6095");          # "LCL" in PFDInstruments.svg
    if (label != nil) label.setText("UTC");
    pfd.PFDInstruments.updateTime = func(time_sec) {
        var t = int(getprop("/sim/time/utc/day-seconds") or 0);
        me.setTextElement("TIME-text", sprintf("%02d:%02d:%02d", int(t / 3600), math.mod(int(t / 60), 60), math.mod(t, 60)));
    };
};

# ---------------------------------------------------------------------------
# Autopilot: the FGData GFC700Interface turns the GDU autopilot keys into /autopilot/lateral-mode-button
# (written on every press) and applies NOSE UP / NOSE DN itself; the CDI key of the pilot PFD (device 1)
# selects the lateral guidance source (GPS / NAV1 / NAV2).
# ---------------------------------------------------------------------------
var cdi_recipient = nil;

var init_autopilot = func {
    setlistener("/autopilot/lateral-mode-button", func(n) { FCS.gfc_key(n.getValue() or ""); }, 0, 1);
    cdi_recipient = emesary.Recipient.new("KingAirCDISource");
    cdi_recipient.Receive = func(notification) {
        if (notification.NotificationType == notifications.PFDEventNotification.DefaultType
            and notification.Event_Id == notifications.PFDEventNotification.FMSData
            and (notification.Device_Id == 1 or notification.Device_Id == 3)
            and typeof(notification.EventParameter) == "hash"
            and contains(notification.EventParameter, "AutopilotNAVSource")) {
            var src = notification.EventParameter["AutopilotNAVSource"];
            # Pro Line Fusion cockpit: the CPL key couples the autopilot to the pilot (1) or copilot (3) PFD
            if (fusion_cockpit()) fusion.set_cdi_source(notification.Device_Id, src);
            elsif (notification.Device_Id == 1) FCS.set_nav_source(src);
        }
        return emesary.Transmitter.ReceiptStatus_NotProcessed;     # also seen by the GFC700Interface
    };
    emesary.GlobalTransmitter.Register(cdi_recipient);
    # the PFD starts with the CDI on GPS
    FCS.set_nav_source("GPS");
    # ALT SEL starts at 0 in the FG1000: start from the autopilot dialog value instead
    var sel = getprop("/autopilot/settings/target-alt-ft");
    if (sel == nil or sel == 0)
        setprop("/autopilot/settings/target-alt-ft", getprop("/autopilot/settings/target-altitude-ft") or 10000);
};

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
    if (fusion_cockpit()) {
        # Pro Line Fusion cockpit: the screens of Models/Fusion/fusion-cockpit.ac, with display reversion
        init_fusion_screens();
    } else {
        foreach (var i; [1, 2, 3])
            fg1000system.display(i);
    }

    foreach (var i; PFDS) {
        var pfd = fg1000system.getDisplay(i);
        # the PFD also parses the EIS SVG (reversionary mode is not simulated): keep its frame hidden
        pfd._svg.getElementById("EISGroup").hide();
        draw_speed_tape(pfd);
        init_cas(pfd);
        set_utc_time(pfd);
    }

    # displays follow the avionics bus
    foreach (var i; [1, 2, 3]) {
        (func(index) {
            setlistener("/systems/electrical/outputs/" ~ POWER[index], func(n) {
                if ((n.getValue() or 0) > 15) fg1000system.show(index); else fg1000system.hide(index);
            }, 1, 0);
        })(i);
    }

    # key and knob backlighting of the GDU bezels (FGData lightmap, factor 0..1) with the instrument lights
    # (dimmer King Air 350 > Lights > Instruments, on the DC bus: systems/electrical/outputs/lights/instrument-lights)
    setlistener("/systems/electrical/outputs/lights/instrument-lights", func(n) {
        setprop("/instrumentation/FG1000/Lightmap", math.min(1, (n.getValue() or 0) / 28.0));
    }, 1, 0);

    init_autopilot();
    print("KingAir-350ER G1000: FG1000 pilot PFD, MFD and copilot PFD initialised");
};

# ---------------------------------------------------------------------------
# Pro Line Fusion cockpit (Models/Fusion/fusion-cockpit.xml): the three FG1000 displays are drawn on the screens
# Fusion.Screen1..3. DISPLAY REVERSION: a display switched OFF goes dark; the pilot (or copilot) PFD is then shown
# on the MFD screen, as the Fusion composite reversion.
# ---------------------------------------------------------------------------
var fusion_cockpit = func { getprop("/sim/model/fusion/cockpit") or 0; };
var placements = {};

var place = func(screen, index) {
    if (placements[screen] != nil) { placements[screen].remove(); placements[screen] = nil; }
    if (index == nil) return;
    placements[screen] = fg1000system.getDisplay(index).getCanvas().addPlacement({"node": "Fusion.Screen" ~ screen});
};

var update_reversion = func {
    var off1 = getprop("/controls/fusion/reversion-pfd1") or 0;
    var off2 = getprop("/controls/fusion/reversion-mfd") or 0;
    var off3 = getprop("/controls/fusion/reversion-pfd2") or 0;
    place(1, off1 ? nil : 1);
    place(3, off3 ? nil : 3);
    place(2, off2 ? nil : (off1 ? 1 : (off3 ? 3 : 2)));
};

var init_fusion_screens = func {
    update_reversion();
    foreach (var p; ["reversion-pfd1", "reversion-mfd", "reversion-pfd2"])
        setlistener("/controls/fusion/" ~ p, update_reversion, 0, 0);
};

# pop-up windows (menu)
var gui_pfd = func { if (fg1000system != nil) fg1000system.displayGUI(1, 0.66); };
var gui_mfd = func { if (fg1000system != nil) fg1000system.displayGUI(2, 0.66); };
var gui_pfd2 = func { if (fg1000system != nil) fg1000system.displayGUI(3, 0.66); };

setlistener("/sim/signals/fdm-initialized", func { settimer(init, 2.0); }, 0, 0);
