#############################################################################
# Beechcraft King Air 350 - autopilot / flight director bridge (namespace FCS)
#
# The control loops run inside JSBSim (Systems/autopilot.xml, properties /fdm/jsbsim/ap/...).
# This module:
#   - implements the cockpit FGC panel (HDG, NAV, APPR, BC, ALT, ALTS, VS, CLIMB, AP, YD, SR, BNK, pitch wheel),
#   - accepts the standard FlightGear autopilot dialog (/autopilot/locks/...),
#   - disconnects when the standard engage property /controls/autoflight/autopilot/engage is cleared
#     by the "Autopilot disconnect" joystick action (controls.autopilotDisconnect()), like the AP
#     disconnect button of the control wheel; it never engages the autopilot,
#   - feeds navigation data (heading bug, NAV1/LOC/GS) to the JSBSim loops,
#   - trims the elevator while engaged and handles altitude pre-select capture,
#   - G1000 variant: takes the GDU bezel keys (AP, FD, HDG, NAV, APR, BC, ALT, VS, FLC, NOSE UP/DN, through the
#     FGData GFC700Interface), follows the CDI source of the pilot PFD (GPS / NAV1 / NAV2; GPS = NAV1 slaved to the
#     GPS, i.e. the active flight plan), captures the ALT SEL altitude and shows its modes on the PFD
#     (/autopilot/annunciator/..., published to the FG1000 by the GFC700Publisher). See Nasal/fg1000-kingair.nas.
#
# License: GPL v2 or later
#############################################################################

var ap  = props.globals.getNode("fdm/jsbsim/ap", 1);
var fgc = props.globals.getNode("instrumentation/fgc-65", 1);
var locks = props.globals.getNode("autopilot/locks", 1);
var set   = props.globals.getNode("autopilot/settings", 1);
var nav   = props.globals.getNode("instrumentation/nav[0]", 1);

var engaged   = 0;
var fd_on     = 0;
var lateral   = "";      # "", HDG, NAV, APPR, BC
var lat_armed = "";      # "", NAV, APPR, BC
var vertical  = "";      # "", ALT, VS, IAS, GS, PIT
var alt_armed = 0;
var gs_armed  = 0;
var soft_ride = 0;
var half_bank = 0;
var updating_locks = 0;
var target_pitch = 0.0;
var target_vs = 0.0;
var alt_offset = nil;    # true - indicated altitude, low-pass filtered (the altimeter lags)
var bug_written = nil;   # heading bug value written at the last update
var alt_hold = nil;      # altitude held in ALT (indicated ft)
var nav_source = "NAV1"; # NAV1, NAV2 or GPS (G1000 CDI; the FGC GPS button slaves NAV1 to the GPS as well)
var nav0 = props.globals.getNode("instrumentation/nav[0]", 1);
var ann = props.globals.getNode("autopilot/annunciator", 1);

var g1000 = func { getprop("sim/model/g1000/enabled") or 0; };

# altitude pre-select (ALTS capture): the G1000 ALT SEL knob, otherwise the autopilot dialog value
var preselect = func {
    var g = getprop("autopilot/settings/target-alt-ft");
    if (g1000() and g != nil) return g;
    return set.getNode("target-altitude-ft", 1).getValue() or 0;
};

# pitch hold target, shared with the G1000 NOSE UP / NOSE DN keys (/autopilot/settings/target-pitch-deg)
var set_target_pitch = func(v) {
    target_pitch = v;
    set.getNode("target-pitch-deg", 1).setDoubleValue(v);
};

var set_alt_hold = func(ft) {
    alt_hold = ft;
    set.getNode("target-altitude-ft", 1).setDoubleValue(ft);      # shown by the autopilot dialog
};

# lateral guidance source: G1000 CDI of the pilot PFD
var set_nav_source = func(src) {
    if (src != "GPS" and src != "NAV2") src = "NAV1";
    nav_source = src;
    nav = props.globals.getNode(src == "NAV2" ? "instrumentation/nav[1]" : "instrumentation/nav[0]", 1);
    nav0.getNode("slaved-to-gps", 1).setBoolValue(src == "GPS");
    annunciate();
};
var gps_guidance = func { nav_source != "NAV2" and nav0.getNode("slaved-to-gps", 1).getBoolValue(); };

# standard FlightGear engage property: created here (FlightGear does not), so that the generic
# "Autopilot disconnect" joystick action finds it; kept equal to the autopilot state by annunciate()
var ap_engage = props.globals.getNode("controls/autoflight/autopilot[0]/engage", 1);
ap_engage.setBoolValue(0);
var syncing_engage = 0;

var annunciate = func {
    syncing_engage = 1;
    ap_engage.setBoolValue(engaged);
    syncing_engage = 0;
    fgc.getNode("internal/lateral", 1).setValue(lateral);
    fgc.getNode("internal/lateral-arm", 1).setValue(lat_armed);
    fgc.getNode("internal/vertical", 1).setValue(vertical == "PIT" ? "" : vertical);
    fgc.getNode("internal/vertical-arm", 1).setValue(gs_armed ? "GS" : (alt_armed ? "ALT" : ""));
    fgc.getNode("internal/nav-armed", 1).setBoolValue(lat_armed == "NAV");
    fgc.getNode("internal/nav-active", 1).setBoolValue(lateral == "NAV");
    fgc.getNode("internal/appr-armed", 1).setBoolValue(lat_armed == "APPR" or lat_armed == "BC");
    fgc.getNode("internal/appr-active", 1).setBoolValue(lateral == "APPR" or lateral == "BC");
    fgc.getNode("app-65a/AP", 1).setValue(engaged ? "AP" : "AP DISENGAGED");
    fgc.getNode("app-65a/YD", 1).setValue(getprop("controls/flight/yaw-damper") ? "YD" : "");
    fgc.getNode("app-65a/SR", 1).setValue(soft_ride ? "SR" : "");
    fgc.getNode("app-65a/BANK", 1).setValue(half_bank ? "1/2 BANK" : "");
    # G1000 PFD (GFC700Publisher): status, active and armed modes, reference
    var nav_name = func(m) {
        if (m == "BC") return "BC";
        if (gps_guidance()) return "GPS";
        return (m == "APPR" or nav.getNode("nav-loc", 1).getBoolValue()) ? "LOC" : "VOR";
    };
    var on = engaged or fd_on;
    ann.getNode("autopilot-enabled", 1).setBoolValue(engaged);
    ann.getNode("flight-director-enabled", 1).setBoolValue(fd_on or engaged);
    ann.getNode("lateral-mode", 1).setValue(!on ? "" : (lateral == "HDG" ? "HDG" : (lateral == "" ? "ROL" : nav_name(lateral))));
    ann.getNode("lateral-mode-armed", 1).setValue(on and lat_armed != "" ? nav_name(lat_armed) : "");
    var vm = {"ALT": "ALT", "VS": "VS", "IAS": "FLC", "GS": "GS", "PIT": "PIT", "": "PIT"}[vertical];
    ann.getNode("vertical-mode", 1).setValue(on ? vm : "");
    ann.getNode("vertical-mode-armed", 1).setValue(!on ? "" : (gs_armed ? "GS" : (alt_armed ? "ALTS" : "")));
    var ref = "";
    if (vertical == "VS") ref = sprintf("%+ifpm", set.getNode("vertical-speed-fpm", 1).getValue() or 0);
    elsif (vertical == "IAS") ref = sprintf("%i kt", set.getNode("target-speed-kt", 1).getValue() or 0);
    elsif (vertical == "ALT" and alt_hold != nil) ref = sprintf("%ift", alt_hold);
    ann.getNode("vertical-mode-target", 1).setValue(on ? ref : "");
    # keep the FlightGear autopilot dialog in sync
    updating_locks = 1;
    var h = "";
    if (engaged or fd_on) {
        if (lateral == "HDG") h = "dg-heading-hold";
        elsif (lateral == "NAV" or lateral == "APPR" or lateral == "BC") h = "nav1-hold";
        elsif (engaged) h = "wing-leveler";
    }
    locks.getNode("heading", 1).setValue(h);
    var v = "";
    if (engaged or fd_on) {
        if (vertical == "ALT") v = "altitude-hold";
        elsif (vertical == "VS") v = "vertical-speed-hold";
        elsif (vertical == "IAS") v = "speed-with-pitch-trim";
        elsif (vertical == "GS") v = "gs1-hold";
        elsif (vertical == "PIT") v = "pitch-hold";
    }
    locks.getNode("altitude", 1).setValue(v);
    locks.getNode("speed", 1).setValue(vertical == "IAS" ? "speed-with-pitch-trim" : "");
    updating_locks = 0;
};

var engage = func(on) {
    if (on and !engaged) {
        if (getprop("gear/gear[1]/wow")) { gui.popupTip("Autopilot cannot be engaged on the ground"); return; }
        if ((getprop("systems/electrical/outputs/fgc-65") or 0) < 20) { gui.popupTip("Autopilot: no electrical power"); return; }
        engaged = 1;
        if (vertical == "") { vertical = "PIT"; set_target_pitch(getprop("orientation/pitch-deg") or 0); }
        gui.popupTip("Autopilot ENGAGED");
    } elsif (!on and engaged) {
        engaged = 0;
        setprop("sim/sound/ap-disconnect", 1);
        settimer(func { setprop("sim/sound/ap-disconnect", 0); }, 2.0);
        gui.popupTip("Autopilot DISENGAGED");
    }
    annunciate();
};

var pitch_wheel = func(dir) {
    if (vertical == "VS" or vertical == "ALT" or vertical == "") {
        if (vertical != "VS") { target_vs = math.round((getprop("velocities/vertical-speed-fps") or 0) * 60 / 100) * 100; vertical = "VS"; alt_armed = 1; }
        else target_vs = set.getNode("vertical-speed-fpm", 1).getValue() or 0;     # also moved by the G1000 keys
        target_vs = math.max(-3000, math.min(3000, target_vs + dir * 100));
        set.getNode("vertical-speed-fpm", 1).setDoubleValue(target_vs);
    } elsif (vertical == "IAS") {
        set.getNode("target-speed-kt", 1).setDoubleValue((set.getNode("target-speed-kt", 1).getValue() or 200) + dir);
    } elsif (vertical == "PIT") {
        set_target_pitch(math.max(-10, math.min(20, target_pitch + dir * 0.5)));
    }
    annunciate();
};

# name: hdg nav appr bc alt ap yd sr bnk ; state 1 = pressed
var btn_pressed = func(name, state, toggle = 0) {
    if (!state) return;
    if (name == "ap") {
        engage(!engaged);
        return;
    }
    if (name == "yd") { kingair350.toggle_yaw_damper(); annunciate(); return; }
    if (name == "sr") { soft_ride = !soft_ride; ap.getNode("bank-limit-deg", 1).setDoubleValue(soft_ride ? 15 : (half_bank ? 14 : 27)); annunciate(); return; }
    if (name == "bnk") { half_bank = !half_bank; ap.getNode("bank-limit-deg", 1).setDoubleValue(half_bank ? 14 : (soft_ride ? 15 : 27)); annunciate(); return; }
    if (name == "hdg") {
        if (lateral == "HDG") { lateral = ""; }
        else { lateral = "HDG"; lat_armed = ""; }
    } elsif (name == "nav" or name == "appr" or name == "bc") {
        var m = (name == "nav") ? "NAV" : (name == "appr" ? "APPR" : "BC");
        if (lateral == m or lat_armed == m) { lateral = (lateral == m) ? "" : lateral; lat_armed = ""; gs_armed = 0; if (vertical == "GS") { vertical = "PIT"; set_target_pitch(getprop("orientation/pitch-deg") or 0); } }
        else {
            lat_armed = m;
            if (lateral == "") lateral = "HDG";       # fly the heading bug until capture
            gs_armed = (m == "APPR");
        }
    } elsif (name == "alt") {
        if (vertical == "ALT") { vertical = "PIT"; set_target_pitch(getprop("orientation/pitch-deg") or 0); }
        else {
            vertical = "ALT"; alt_armed = 0;
            set_alt_hold(math.round((getprop("instrumentation/altimeter/indicated-altitude-ft") or 0) / 10) * 10);
        }
    } elsif (name == "vs") {
        # VS: hold the current vertical speed (pitch wheel adjusts it), altitude pre-select armed
        if (vertical == "VS") { vertical = "PIT"; set_target_pitch(getprop("orientation/pitch-deg") or 0); }
        else {
            target_vs = math.max(-3000, math.min(3000, math.round((getprop("velocities/vertical-speed-fps") or 0) * 60 / 100) * 100));
            set.getNode("vertical-speed-fpm", 1).setDoubleValue(target_vs);
            vertical = "VS"; alt_armed = 1;
        }
    } elsif (name == "climb" or name == "ias") {
        # CLIMB / IAS: hold the current indicated airspeed with pitch, altitude pre-select armed
        if (vertical == "IAS") { vertical = "PIT"; set_target_pitch(getprop("orientation/pitch-deg") or 0); }
        else {
            set.getNode("target-speed-kt", 1).setDoubleValue(math.round(getprop("instrumentation/airspeed-indicator/indicated-speed-kt") or 150));
            vertical = "IAS"; alt_armed = 1;
        }
    } elsif (name == "alts") {
        # ALTS: arm / disarm the capture of the pre-selected altitude
        alt_armed = !alt_armed;
    }
    fd_on = 1;
    annunciate();
};

# G1000 bezel keys (FASCIA names written by the FGData GFC700Interface to /autopilot/lateral-mode-button);
# NOSE UP / NOSE DN are applied by the GFC700Interface itself to the PIT / VS / FLC targets
var gfc_key = func(k) {
    if (k == "AP") return btn_pressed("ap", 1);
    if (k == "FD") {
        if (engaged) return gui.popupTip("FD: the flight director stays on with the autopilot engaged");
        fd_on = !fd_on;
        if (!fd_on) { lateral = ""; lat_armed = ""; vertical = ""; alt_armed = 0; gs_armed = 0; }
        return annunciate();
    }
    var map = {"HDG": "hdg", "NAV": "nav", "APR": "appr", "BC": "bc", "ALT": "alt", "VS": "vs", "FLC": "ias"};
    if (contains(map, k)) return btn_pressed(map[k], 1);
    if (k == "VNV") return gui.popupTip("VNV: vertical navigation is not available on this autopilot");
};

# ---------------------------------------------------------------------------
# FlightGear autopilot dialog -> modes
# ---------------------------------------------------------------------------
var lock_changed = func {
    if (updating_locks) return;
    var h = locks.getNode("heading", 1).getValue() or "";
    var a = locks.getNode("altitude", 1).getValue() or "";
    var s = locks.getNode("speed", 1).getValue() or "";
    if (h == "dg-heading-hold" or h == "true-heading-hold") { lateral = "HDG"; lat_armed = ""; }
    elsif (h == "nav1-hold") { if (lateral != "NAV" and lateral != "APPR" and lateral != "BC") { lat_armed = "NAV"; if (lateral == "") lateral = "HDG"; } }
    elsif (h == "wing-leveler") { lateral = ""; lat_armed = ""; }
    elsif (h == "") { lateral = ""; lat_armed = ""; }
    if (a == "altitude-hold") { vertical = "ALT"; alt_armed = 0; alt_hold = set.getNode("target-altitude-ft", 1).getValue() or 0; }
    elsif (a == "vertical-speed-hold") { vertical = "VS"; target_vs = set.getNode("vertical-speed-fpm", 1).getValue() or 0; alt_armed = 1; }
    elsif (a == "pitch-hold") { vertical = "PIT"; target_pitch = set.getNode("target-pitch-deg", 1).getValue() or 0; }
    elsif (a == "gs1-hold") { gs_armed = 1; if (lat_armed == "") lat_armed = "APPR"; }
    elsif (a == "agl-hold" or a == "aoa-hold") { vertical = "ALT"; alt_hold = set.getNode("target-altitude-ft", 1).getValue() or 0; }
    elsif (s == "speed-with-pitch-trim") { vertical = "IAS"; alt_armed = 1; }
    elsif (a == "" and s == "") { if (vertical != "GS") vertical = engaged ? "PIT" : ""; }
    var want = (h != "" or a != "" or s != "");
    if (want and !engaged) { engage(1); }
    elsif (!want and engaged) { engage(0); }
    annunciate();
};

# ---------------------------------------------------------------------------
# periodic update: capture logic, data feed to JSBSim, auto-trim
# ---------------------------------------------------------------------------
var update = func {
    var dt = 0.1;
    var magvar = getprop("environment/magnetic-variation-deg") or 0;
    var heading_bug = fgc.getNode("settings/hdg", 1).getValue() or 0;
    # heading bug: the FGC-65 knob, the G1000 HDG knobs and the autopilot dialog share the value;
    # the last one turned wins (the G1000 and the dialog write autopilot/settings/heading-bug-deg)
    var ext_bug = set.getNode("heading-bug-deg", 1).getValue() or 0;
    if (bug_written != nil and math.abs(ext_bug - bug_written) > 0.01 and math.abs(heading_bug - bug_written) < 0.01)
        heading_bug = ext_bug;
    set.getNode("heading-bug-deg", 1).setDoubleValue(heading_bug);
    fgc.getNode("settings/hdg", 1).setDoubleValue(heading_bug);
    bug_written = heading_bug;

    # NAV data
    var in_range = nav.getNode("in-range", 1).getBoolValue();
    var is_loc = nav.getNode("nav-loc", 1).getBoolValue();
    var defl = nav.getNode("heading-needle-deflection-norm", 1).getValue() or 0;
    var course = nav.getNode("radials/selected-deg", 1).getValue() or 0;
    var dist_m = nav.getNode("nav-distance", 1).getValue() or 0;
    var dist_nm = dist_m > 300 ? dist_m / 1852.0 : 10.0;
    var has_gs = nav.getNode("has-gs", 1).getBoolValue() and nav.getNode("gs-in-range", 1).getBoolValue();
    var gs_defl = nav.getNode("gs-needle-deflection-norm", 1).getValue() or 0;

    # lateral capture
    if (lat_armed != "" and in_range and math.abs(defl) < 0.85) {
        lateral = lat_armed; lat_armed = "";
        gui.popupTip((lateral == "APPR" ? "Localizer" : (lateral == "BC" ? "Back course" : "NAV")) ~ " captured");
        annunciate();
    }
    if ((lateral == "NAV" or lateral == "APPR" or lateral == "BC") and !in_range) {
        # signal lost: fall back to heading hold and re-arm
        lat_armed = lateral; lateral = "HDG"; annunciate();
    }
    # glideslope capture (from below or above, within half scale)
    if (gs_armed and (lateral == "APPR") and has_gs and math.abs(gs_defl) < 0.5) {
        gs_armed = 0; vertical = "GS"; alt_armed = 0; gui.popupTip("Glideslope captured"); annunciate();
    }
    # altitude pre-select capture
    var alt_sel = preselect();
    var alt_ind = getprop("instrumentation/altimeter/indicated-altitude-ft") or 0;
    var vs_now = (getprop("velocities/vertical-speed-fps") or 0) * 60;
    if (alt_armed and (vertical == "VS" or vertical == "IAS" or vertical == "PIT")) {
        var lead = math.max(150, math.abs(vs_now) * 0.12);
        if (math.abs(alt_sel - alt_ind) < lead and (alt_sel - alt_ind) * vs_now >= 0) {
            vertical = "ALT"; alt_armed = 0; set_alt_hold(alt_sel); gui.popupTip("Altitude captured"); annunciate();
        }
    }
    if (alt_hold == nil) alt_hold = set.getNode("target-altitude-ft", 1).getValue() or 0;
    # PIT: the target may also be moved by the G1000 NOSE UP / NOSE DN keys
    if (vertical == "PIT") {
        var tp = set.getNode("target-pitch-deg", 1).getValue();
        if (tp != nil) target_pitch = tp;
    }

    # feed JSBSim
    ap.getNode("engaged", 1).setBoolValue(engaged);
    ap.getNode("fd-on", 1).setBoolValue(fd_on);
    var rm = 0;
    if (lateral == "HDG") rm = 1;
    elsif (lateral == "NAV" or lateral == "APPR") rm = 2;
    elsif (lateral == "BC") rm = 3;
    ap.getNode("roll-mode", 1).setIntValue(rm);
    var pm = 0;
    if (vertical == "ALT") pm = 1;
    elsif (vertical == "VS") pm = 2;
    elsif (vertical == "IAS") pm = 3;
    elsif (vertical == "GS") pm = 4;
    ap.getNode("pitch-mode", 1).setIntValue(pm);
    var true_hdg = heading_bug + magvar;
    if (locks.getNode("heading", 1).getValue() == "true-heading-hold") true_hdg = set.getNode("true-heading-deg", 1).getValue() or 0;
    ap.getNode("target-heading-true-deg", 1).setDoubleValue(true_hdg);
    # altitude target in true altitude (the JSBSim loop uses h-sl-ft); the true - indicated offset is
    # filtered (~10 s) so that the altimeter lag in climbs and descents does not move the target
    var off = (getprop("position/altitude-ft") or 0) - alt_ind;
    alt_offset = (alt_offset == nil) ? off : alt_offset + (off - alt_offset) * dt / 10.0;
    ap.getNode("target-altitude-ft", 1).setDoubleValue(alt_hold + alt_offset);
    ap.getNode("target-vs-fpm", 1).setDoubleValue(set.getNode("vertical-speed-fpm", 1).getValue() or 0);
    ap.getNode("target-ias-kt", 1).setDoubleValue(set.getNode("target-speed-kt", 1).getValue() or 200);
    ap.getNode("target-pitch-deg", 1).setDoubleValue(target_pitch);
    ap.getNode("nav-deflection", 1).setDoubleValue(defl);
    ap.getNode("nav-valid", 1).setBoolValue(in_range);
    ap.getNode("nav-is-loc", 1).setBoolValue(is_loc);
    ap.getNode("nav-course-true-deg", 1).setDoubleValue(course + magvar);
    ap.getNode("nav-distance-nm", 1).setDoubleValue(dist_nm);
    ap.getNode("gs-deflection", 1).setDoubleValue(gs_defl);
    ap.getNode("gs-valid", 1).setBoolValue(has_gs);

    # auto-trim: slowly offload a sustained autopilot elevator command into the pitch trim (deadband 0.03,
    # 0.03 /s per unit of command). A faster trim adds a second integrator to the JSBSim pitch loop and makes
    # ALT / VS hold oscillate (checked with the JSBSim loop alone: 0.35 /s diverges to +-13 deg pitch).
    if (engaged) {
        var cmd = ap.getNode("elevator-cmd", 1).getValue() or 0;
        var excess = (cmd > 0.03) ? cmd - 0.03 : ((cmd < -0.03) ? cmd + 0.03 : 0);
        var trim = getprop("controls/flight/elevator-trim") or 0;
        trim = math.max(-1, math.min(1, trim + excess * 0.03 * dt));
        setprop("controls/flight/elevator-trim", trim);
        fgc.getNode("internal/trim", 1).setValue(math.abs(cmd) > 0.15 ? (cmd < 0 ? "TRIM UP" : "TRIM DN") : "");
        # disconnect on stall warning or excessive attitude
        if (math.abs(getprop("orientation/roll-deg") or 0) > 60 or (getprop("orientation/alpha-deg") or 0) > 14) {
            engage(0); gui.popupTip("Autopilot disconnected: attitude");
        }
        # pilot override: large stick input disconnects the AP
        if (math.abs(getprop("controls/flight/elevator") or 0) > 0.5 or math.abs(getprop("controls/flight/aileron") or 0) > 0.6) {
            engage(0); gui.popupTip("Autopilot disconnected: pilot override");
        }
    } else {
        fgc.getNode("internal/trim", 1).setValue("");
    }
    # flight director bars for the EADI
    fgc.getNode("fd/pitch-deg", 1).setDoubleValue(getprop("fdm/jsbsim/ap/fd-pitch-deg") or 0);
    fgc.getNode("fd/roll-deg", 1).setDoubleValue(getprop("fdm/jsbsim/ap/fd-roll-deg") or 0);
    # and for the G1000 PFD (commanded attitude, GFC700Publisher)
    set.getNode("target-roll-deg", 1).setDoubleValue(getprop("fdm/jsbsim/ap/roll-target-filt-deg") or 0);
    if (vertical != "PIT") set.getNode("target-pitch-deg", 1).setDoubleValue(getprop("fdm/jsbsim/ap/pitch-target-deg") or 0);
    # the lateral mode name follows the guidance source (GPS / VOR / LOC)
    if (lateral != "" or lat_armed != "") annunciate();
};

var timer = maketimer(0.1, update);

setlistener("sim/signals/fdm-initialized", func {
    setlistener("autopilot/locks/heading", lock_changed, 0, 0);
    setlistener("autopilot/locks/altitude", lock_changed, 0, 0);
    setlistener("autopilot/locks/speed", lock_changed, 0, 0);
    # engage property written from outside: disconnect only, like the control wheel AP disconnect
    # button (engaging stays on the FGC panel AP button, Ctrl-F or the F11 dialog)
    setlistener(ap_engage, func(n) {
        if (syncing_engage) return;
        if (!n.getBoolValue() and engaged) engage(0);
        else annunciate();       # any other write: back to the real state
    }, 0, 0);
    annunciate();
    timer.start();
    print("KingAir-350: autopilot bridge ok");
}, 0, 0);

# keyboard helpers
var toggle_ap = func { engage(!engaged); };
