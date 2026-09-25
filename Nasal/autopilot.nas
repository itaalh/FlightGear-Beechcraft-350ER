#############################################################################
# Beechcraft King Air 350 - autopilot / flight director bridge (namespace FCS)
#
# The control loops run inside JSBSim (Systems/autopilot.xml, properties /fdm/jsbsim/ap/...).
# This module:
#   - implements the cockpit FGC panel (HDG, NAV, APPR, BC, ALT, AP, YD, SR, BNK, pitch wheel),
#   - accepts the standard FlightGear autopilot dialog (/autopilot/locks/...),
#   - feeds navigation data (heading bug, NAV1/LOC/GS) to the JSBSim loops,
#   - trims the elevator while engaged and handles altitude pre-select capture.
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

var annunciate = func {
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
        if (vertical == "") { vertical = "PIT"; target_pitch = getprop("orientation/pitch-deg") or 0; }
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
        target_vs = math.max(-3000, math.min(3000, target_vs + dir * 100));
        set.getNode("vertical-speed-fpm", 1).setDoubleValue(target_vs);
    } elsif (vertical == "IAS") {
        set.getNode("target-speed-kt", 1).setDoubleValue((set.getNode("target-speed-kt", 1).getValue() or 200) + dir);
    } elsif (vertical == "PIT") {
        target_pitch = math.max(-10, math.min(20, target_pitch + dir * 0.5));
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
        if (lateral == m or lat_armed == m) { lateral = (lateral == m) ? "" : lateral; lat_armed = ""; gs_armed = 0; if (vertical == "GS") vertical = "PIT"; }
        else {
            lat_armed = m;
            if (lateral == "") lateral = "HDG";       # fly the heading bug until capture
            gs_armed = (m == "APPR");
        }
    } elsif (name == "alt") {
        if (vertical == "ALT") { vertical = "PIT"; target_pitch = getprop("orientation/pitch-deg") or 0; }
        else {
            vertical = "ALT"; alt_armed = 0;
            set.getNode("target-altitude-ft", 1).setDoubleValue(math.round((getprop("instrumentation/altimeter/indicated-altitude-ft") or 0) / 10) * 10);
        }
    }
    fd_on = 1;
    annunciate();
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
    if (a == "altitude-hold") { vertical = "ALT"; alt_armed = 0; }
    elsif (a == "vertical-speed-hold") { vertical = "VS"; target_vs = set.getNode("vertical-speed-fpm", 1).getValue() or 0; alt_armed = 1; }
    elsif (a == "pitch-hold") { vertical = "PIT"; target_pitch = set.getNode("target-pitch-deg", 1).getValue() or 0; }
    elsif (a == "gs1-hold") { gs_armed = 1; if (lat_armed == "") lat_armed = "APPR"; }
    elsif (a == "agl-hold" or a == "aoa-hold") { vertical = "ALT"; }
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
    # heading bug: cockpit knob and dialog share the value
    var dlg_bug = set.getNode("heading-bug-deg", 1).getValue() or 0;
    if (math.abs(dlg_bug - heading_bug) > 0.5 and lateral == "HDG") heading_bug = dlg_bug;
    set.getNode("heading-bug-deg", 1).setDoubleValue(heading_bug);
    fgc.getNode("settings/hdg", 1).setDoubleValue(heading_bug);

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
    var alt_target = set.getNode("target-altitude-ft", 1).getValue() or 0;
    var alt_ind = getprop("instrumentation/altimeter/indicated-altitude-ft") or 0;
    var vs_now = (getprop("velocities/vertical-speed-fps") or 0) * 60;
    if (alt_armed and (vertical == "VS" or vertical == "IAS" or vertical == "PIT")) {
        var lead = math.max(150, math.abs(vs_now) * 0.12);
        if (math.abs(alt_target - alt_ind) < lead and (alt_target - alt_ind) * vs_now >= 0) {
            vertical = "ALT"; alt_armed = 0; gui.popupTip("Altitude captured"); annunciate();
        }
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
    # altitude target in true altitude (the JSBSim loop uses h-sl-ft)
    ap.getNode("target-altitude-ft", 1).setDoubleValue(alt_target + ((getprop("position/altitude-ft") or 0) - alt_ind));
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

    # auto-trim: transfer the autopilot elevator command into the pitch trim
    if (engaged) {
        var cmd = ap.getNode("elevator-cmd", 1).getValue() or 0;
        var trim = getprop("controls/flight/elevator-trim") or 0;
        trim = math.max(-1, math.min(1, trim + cmd * 0.35 * dt));
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
};

var timer = maketimer(0.1, update);

setlistener("sim/signals/fdm-initialized", func {
    setlistener("autopilot/locks/heading", lock_changed, 0, 0);
    setlistener("autopilot/locks/altitude", lock_changed, 0, 0);
    setlistener("autopilot/locks/speed", lock_changed, 0, 0);
    annunciate();
    timer.start();
    print("KingAir-350: autopilot bridge ok");
}, 0, 0);

# keyboard helpers
var toggle_ap = func { engage(!engaged); };
