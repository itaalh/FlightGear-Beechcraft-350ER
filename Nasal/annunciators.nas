#############################################################################
# Beechcraft King Air 350 - annunciators / crew alerting
#
# One alert list drives:
# - the warning (red) and caution/advisory annunciator panel of the classic cockpit
#   (instrumentation/annunciators/warning|caution/<lamp>, Models/flightdeck.xml),
# - the MASTER WARNING / MASTER CAUTION flashers (reset by pressing them) and the annunciator test,
# - the CAS messages of the G1000 (instrumentation/cas/message[n], shown by Nasal/fg1000-kingair.nas).
#
# Messages and triggers follow the King Air 350 annunciator tables (FlightSafety King Air 300/350
# Pilot Training Manual, tables 4-4 to 4-7). Only the conditions that the simulated systems can
# produce are wired: there is no fire detection, bleed air leak, hydraulic or autopilot monitor model,
# so those lamps stay dark (they still light with the annunciator test).
#
# License: GPL v2 or later
#############################################################################

var ann   = props.globals.getNode("instrumentation/annunciators", 1);
var cas   = props.globals.getNode("instrumentation/cas", 1);
var power = props.globals.getNode("systems/electrical/outputs/annunciators", 1);

var WARNING  = 0;
var CAUTION  = 1;
var ADVISORY = 2;     # advisory and status annunciators

# panel lamps without a simulated source: forced on by the annunciator test only
var UNWIRED_LAMPS = ["warning/AP-fail", "warning/AP-trim", "warning/L-bleed-air", "warning/R-bleed-air",
                     "warning/L-env-fail", "warning/R-env-fail",
                     "warning/emer-lights", "caution/LFuelCol", "caution/RFuelCol"];

var eng = func(i, p) { getprop("engines/engine[" ~ i ~ "]/" ~ p) or 0; };
var ectl = func(i, p) { getprop("controls/engines/engine[" ~ i ~ "]/" ~ p) or 0; };
var tank_lbs = func(t) { getprop("consumables/fuel/tank[" ~ t ~ "]/level-lbs") or 0; };
var door_open = func(d) { (getprop("sim/model/door-positions/" ~ d ~ "/position-norm") or 0) > 0.01; };
var gear_down = func { getprop("controls/gear/gear-down"); };

# text, level, panel lamp (nil: G1000 CAS only), condition, optional delay (s) before it shows
var ALERTS = [
    # ---- warnings (table 4-4)
    { text: "#1 AC BUS",      level: WARNING, lamp: "warning/L-ac-bus",
      cond: func { (getprop("systems/electrical/LH-ac-bus") or 0) < 100 } },
    { text: "#2 AC BUS",      level: WARNING, lamp: "warning/R-ac-bus",
      cond: func { (getprop("systems/electrical/RH-ac-bus") or 0) < 100 } },
    # airstair or cargo door open (the classic panel has a lamp for each)
    { text: "DOOR UNLOCKED",  level: WARNING, lamp: nil,
      cond: func { door_open("passenger") or door_open("crew") or door_open("leftbagage") or door_open("rightbagage") } },
    { text: nil,              level: WARNING, lamp: "warning/cbn-door",
      cond: func { door_open("passenger") or door_open("crew") } },
    { text: nil,              level: WARNING, lamp: "warning/crg-door",
      cond: func { door_open("leftbagage") or door_open("rightbagage") } },
    # pressurization (Nasal/pressurization.nas); CABIN ALT TEST / CABIN DIFF WARN TEST switch
    { text: "CABIN ALT HI",   level: WARNING, lamp: "warning/cbn-alt",
      cond: func { (getprop("systems/pressurization/cabin-altitude-ft") or 0) > 12000
                   or getprop("controls/pressurization/cabin-alt-test") } },
    { text: "CABIN DIFF HI",  level: WARNING, lamp: "warning/cbn-diff",
      cond: func { (getprop("systems/pressurization/diff-psi") or 0) > 6.9
                   or getprop("controls/pressurization/diff-warn-test") } },
    # boost pressure below ~10 psi: the engine-driven pump only delivers above ~12 % N1 (no standby pump model)
    { text: "L FUEL PRES LO", level: WARNING, lamp: "warning/L-fuel-psi",
      cond: func { eng(0, "n1") < 12 } },
    { text: "R FUEL PRES LO", level: WARNING, lamp: "warning/R-fuel-psi",
      cond: func { eng(1, "n1") < 12 } },
    { text: "L OIL PRES LO",  level: WARNING, lamp: "warning/L-oil-psi",
      cond: func { eng(0, "oil-pressure-ind-psi") < 60 } },
    { text: "R OIL PRES LO",  level: WARNING, lamp: "warning/R-oil-psi",
      cond: func { eng(1, "oil-pressure-ind-psi") < 60 } },

    # ---- cautions (table 4-5)
    { text: "L DC GEN",       level: CAUTION, lamp: "caution/LDCgen",
      cond: func { (getprop("systems/electrical/gen-load[0]") or 0) == 0 } },
    { text: "R DC GEN",       level: CAUTION, lamp: "caution/RDCgen",
      cond: func { (getprop("systems/electrical/gen-load[1]") or 0) == 0 } },
    # main system below ~300 lb (30 min at maximum continuous power), 5-7 s sensor delay
    { text: "L FUEL QTY",     level: CAUTION, lamp: "caution/LFQty", delay: 6,
      cond: func { tank_lbs(1) < 300 } },
    { text: "R FUEL QTY",     level: CAUTION, lamp: "caution/RFQty", delay: 6,
      cond: func { tank_lbs(2) < 300 } },
    # aux tank still holds fuel but does not transfer (transfer pump switched off)
    { text: "L NO FUEL XFR",  level: CAUTION, lamp: nil,
      cond: func { getprop("controls/fuel/Laux-switch") == "off" and tank_lbs(0) > 10 and eng(0, "running") } },
    { text: "R NO FUEL XFR",  level: CAUTION, lamp: nil,
      cond: func { getprop("controls/fuel/Raux-switch") == "off" and tank_lbs(3) > 10 and eng(1, "running") } },
    # high charge rate: battery recharging after an engine start
    { text: "BATTERY CHARGE", level: CAUTION, lamp: "caution/BATchg",
      cond: func { (getprop("systems/electrical/gen-load[0]") or getprop("systems/electrical/gen-load[1]"))
                   and (getprop("systems/electrical/battery-charge") or 1) < 0.95 } },
    { text: "EXT PWR",        level: CAUTION, lamp: nil,
      cond: func { getprop("controls/electric/external-power") and getprop("gear/gear[1]/wow") } },
    { text: "RVS NOT READY",  level: CAUTION, lamp: nil,
      cond: func { gear_down() and (ectl(0, "propeller-pitch") < 0.98 or ectl(1, "propeller-pitch") < 0.98) } },
    { text: "AUTOFTHER OFF",  level: CAUTION, lamp: nil,
      cond: func { gear_down() and !getprop("controls/engines/autofeather") } },
    { text: "L BL AIR OFF",   level: CAUTION, lamp: nil,
      cond: func { getprop("controls/pressurization/bleed-air[0]") == 0 } },   # nil before init
    { text: "R BL AIR OFF",   level: CAUTION, lamp: nil,
      cond: func { getprop("controls/pressurization/bleed-air[1]") == 0 } },   # nil before init
    { text: "RUD BOOST OFF",  level: CAUTION, lamp: nil,
      cond: func { !getprop("controls/flight/rudder-boost") } },

    # ---- advisories (table 4-6) and status (table 4-7)
    # switch on, or auto-ignition armed with the torque below 17 % (Nasal/kingair350.nas drives it)
    { text: "L IGNITION ON",  level: ADVISORY, lamp: "caution/Lignition",
      cond: func { ectl(0, "ignition") } },
    { text: "R IGNITION ON",  level: ADVISORY, lamp: "caution/Rignition",
      cond: func { ectl(1, "ignition") } },
    # inertial separator vanes in the icing position (Nasal/ice-protection.nas)
    { text: "L ENG ANTI-ICE", level: ADVISORY, lamp: nil,
      cond: func { (getprop("systems/anti-ice/engine[0]/vane-pos-norm") or 0) > 0.99 } },
    { text: "R ENG ANTI-ICE", level: ADVISORY, lamp: nil,
      cond: func { (getprop("systems/anti-ice/engine[1]/vane-pos-norm") or 0) > 0.99 } },
    { text: "WING DEICE",     level: ADVISORY, lamp: nil,
      cond: func { getprop("systems/anti-ice/wing-boots") } },
    { text: "TAIL DEICE",     level: ADVISORY, lamp: nil,
      cond: func { getprop("systems/anti-ice/tail-boots") } },
    { text: "L BK DEICE ON",  level: ADVISORY, lamp: nil,
      cond: func { getprop("systems/anti-ice/brake-deice") } },
    { text: "R BK DEICE ON",  level: ADVISORY, lamp: nil,
      cond: func { getprop("systems/anti-ice/brake-deice") } },
    { text: "MAN TIES CLOSE", level: ADVISORY, lamp: nil,
      cond: func { getprop("controls/electric/gen-ties-man-close") } },
    { text: "FUEL CROSSFEED", level: ADVISORY, lamp: "caution/FXfer",
      cond: func { (getprop("controls/fuel/crossfeed") or 0) != 0 } },
    # armed with the power levers above ~88 % N1
    { text: "L AUTOFEATHER",  level: ADVISORY, lamp: nil,
      cond: func { getprop("controls/engines/autofeather") and eng(0, "n1") > 88 } },
    { text: "R AUTOFEATHER",  level: ADVISORY, lamp: nil,
      cond: func { getprop("controls/engines/autofeather") and eng(1, "n1") > 88 } },
    { text: "L PROP PITCH",   level: ADVISORY, lamp: nil,
      cond: func { ectl(0, "reverser") } },
    { text: "R PROP PITCH",   level: ADVISORY, lamp: nil,
      cond: func { ectl(1, "reverser") } },
    { text: "CABIN ALTITUDE", level: ADVISORY, lamp: nil,
      cond: func { (getprop("systems/pressurization/cabin-altitude-ft") or 0) > 10000
                   or getprop("controls/pressurization/cabin-alt-test") } },
    { text: "LDG/TAXI LIGHT", level: ADVISORY, lamp: "caution/Taxi",
      cond: func { !gear_down() and (getprop("controls/lighting/taxi-lights") or getprop("controls/lighting/landing-lights")
                                     or getprop("controls/lighting/landing-lights[1]")) } },
];

# active messages, highest priority first: [{ text, level, since }]. Read by the G1000 CAS window.
var messages = [];

var raw_since = {};      # alert index -> time its condition became true (for the delay)
var onset = {};          # text -> time the message appeared
var blink = 0;

var update = func {
    var powered = (power.getValue() or 0) > 18;
    var test = ann.getNode("warning/test", 1).getBoolValue();
    var now = getprop("sim/time/elapsed-sec") or 0;
    blink = !blink;

    var new_warning = 0;
    var new_caution = 0;
    var any_warning = 0;
    var any_caution = 0;
    var active = [];

    forindex (var k; ALERTS) {
        var a = ALERTS[k];
        var on = 0;
        if (powered and a.cond()) {
            if (raw_since[k] == nil) raw_since[k] = now;
            on = (now - raw_since[k]) >= (a["delay"] or 0);
        } else {
            raw_since[k] = nil;
        }
        if (a.lamp != nil) ann.getNode(a.lamp, 1).setBoolValue(on or (powered and test));
        if (a.text == nil) continue;
        if (on) {
            if (onset[a.text] == nil) {
                onset[a.text] = now;
                if (a.level == WARNING) new_warning = 1;
                if (a.level == CAUTION) new_caution = 1;
            }
            if (a.level == WARNING) any_warning = 1;
            if (a.level == CAUTION) any_caution = 1;
            append(active, { text: a.text, level: a.level, since: onset[a.text] });
        } else {
            onset[a.text] = nil;
        }
    }
    foreach (var l; UNWIRED_LAMPS) ann.getNode(l, 1).setBoolValue(powered and test);

    # a new warning / caution (re)triggers its master; it goes out when pressed or when nothing is left
    var mw = ann.getNode("warning/Master", 1);
    var mc = ann.getNode("caution/Master", 1);
    if (new_warning) mw.setBoolValue(1);
    if (new_caution) mc.setBoolValue(1);
    if (!any_warning) mw.setBoolValue(0);
    if (!any_caution) mc.setBoolValue(0);
    ann.getNode("warning/flasher", 1).setBoolValue(powered and (test or (mw.getBoolValue() and blink)));
    ann.getNode("caution/flasher", 1).setBoolValue(powered and (test or (mc.getBoolValue() and blink)));

    # priority: warnings, cautions, advisories; newest first within a level
    messages = sort(active, func(a, b) {
        if (a.level != b.level) return a.level - b.level;
        return b.since - a.since;
    });

    cas.removeChildren("message");
    forindex (var i; messages) {
        var n = cas.getNode("message[" ~ i ~ "]", 1);
        n.getNode("text", 1).setValue(messages[i].text);
        n.getNode("level", 1).setIntValue(messages[i].level);
    }
    cas.getNode("count", 1).setIntValue(size(messages));
};

var timer = maketimer(0.25, update);
setlistener("sim/signals/fdm-initialized", func { timer.start(); }, 0, 0);
