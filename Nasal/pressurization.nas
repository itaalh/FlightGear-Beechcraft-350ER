#############################################################################
# Beechcraft King Air 350 - cabin pressurization
#
# After the FlightSafety King Air 300/350 Pilot Training Manual, chapter 12:
# - inflow: P3 bleed air of each engine (BLEED AIR VALVE switches), ENVIR BLEED AIR NORMAL / LOW;
# - the controller drives the cabin to the selected CABIN ALT at the selected RATE;
# - the outflow / safety valves limit the differential to 6.5-6.6 psid (cabin ~2700 ft at FL200,
#   ~8700 ft at FL310, ~10200 ft at FL350) and open when outside pressure exceeds cabin pressure
#   (below the selected altitude the cabin follows the aircraft);
# - on the ground the squat switch dumps the cabin, unless CABIN PRESS is held to TEST;
#   CABIN PRESS DUMP depressurizes in flight;
# - without bleed air the cabin leaks down towards ambient.
# Outputs under /systems/pressurization/ (cabin altitude, rate, differential); CABIN ALTITUDE,
# CABIN ALT HI and CABIN DIFF HI are raised by Nasal/annunciators.nas. Controls: menu
# King Air 350 > Pressurization (Systems/pressurization-dlg.xml).
#
# License: GPL v2 or later
#############################################################################

var ctl = props.globals.getNode("controls/pressurization", 1);
var sys = props.globals.getNode("systems/pressurization", 1);

var MAX_DIFF_PSI = 6.5;          # regulated differential (6.6 psid: 6.5 +0.1/-0.0)
var INHG_PER_PSI = 2.036;
var LEAK_TAU_S = 180.0;          # cabin leak time constant without inflow
var dt = 0.5;

# ISA pressure altitude (ft) <-> static pressure (inHg)
var alt_of = func(p_inhg) { 145442.16 * (1 - math.pow(math.max(p_inhg, 0.1) / 29.92126, 0.190263)); };
var p_of = func(alt_ft) { 29.92126 * math.pow(1 - alt_ft / 145442.16, 5.25588); };

var p_cabin = nil;
var last_alt = nil;
var rate_f = 0;

var init = func {
    ctl.getNode("bleed-air[0]", 1).setBoolValue(1);
    ctl.getNode("bleed-air[1]", 1).setBoolValue(1);
    if (ctl.getNode("cabin-alt-ft", 1).getValue() == nil) ctl.getNode("cabin-alt-ft", 1).setDoubleValue(7000);
    if (ctl.getNode("rate-fpm", 1).getValue() == nil) ctl.getNode("rate-fpm", 1).setDoubleValue(500);
    if (ctl.getNode("cabin-press", 1).getValue() == nil) ctl.getNode("cabin-press", 1).setValue("press");
    p_cabin = nil;           # set from the ambient pressure on the first update (valid once the FDM runs)
    timer.start();
};

var update = func {
    var p_amb = getprop("environment/pressure-inhg") or 29.92;
    if (p_cabin == nil) p_cabin = p_amb;
    var mode = ctl.getNode("cabin-press", 1).getValue() or "press";
    var wow = getprop("gear/gear[1]/wow");
    var dc = (getprop("systems/electrical/volts") or 0) > 20;

    # bleed air inflow from each running engine with its valve open
    var inflow = 0;
    foreach (var i; [0, 1]) {
        var ok = ctl.getNode("bleed-air[" ~ i ~ "]", 1).getBoolValue()
                 and (getprop("engines/engine[" ~ i ~ "]/n1") or 0) > 50;
        sys.getNode("bleed-air[" ~ i ~ "]", 1).setBoolValue(ok);
        if (ok) inflow += 1;
    }

    var dumped = (mode == "dump") or (wow and mode != "test") or !dc;
    var p_max = p_amb + MAX_DIFF_PSI * INHG_PER_PSI;       # relief valve limit
    var alt = alt_of(p_cabin);

    if (dumped) {
        # safety valve open: cabin follows ambient within a few seconds
        p_cabin += (p_amb - p_cabin) * math.min(1, dt / 3.0);
    } elsif (inflow == 0) {
        # no inflow: leak down towards ambient
        p_cabin += (p_amb - p_cabin) * dt / LEAK_TAU_S;
    } else {
        # controller: move towards the selected cabin altitude at the selected rate
        var target = ctl.getNode("cabin-alt-ft", 1).getValue() or 7000;
        var rate = math.clamp(ctl.getNode("rate-fpm", 1).getValue() or 500, 50, 2000);
        # with LOW bleed flow, or one engine only, the cabin cannot be driven down as fast
        if (ctl.getNode("envir-low", 1).getBoolValue() or inflow == 1) rate = math.min(rate, 1000);
        var step = rate / 60 * dt;
        alt += math.clamp(target - alt, -step, step);
        p_cabin = p_of(alt);
    }
    # outflow / safety valve relief (max differential) and negative pressure relief
    p_cabin = math.clamp(p_cabin, p_amb, p_max);

    var cabin_alt = alt_of(p_cabin);
    if (last_alt != nil) rate_f += ((cabin_alt - last_alt) / dt * 60 - rate_f) * 0.2;
    last_alt = cabin_alt;

    sys.getNode("cabin-altitude-ft", 1).setDoubleValue(cabin_alt);
    sys.getNode("cabin-rate-fpm", 1).setDoubleValue(rate_f);
    sys.getNode("diff-psi", 1).setDoubleValue((p_cabin - p_amb) / INHG_PER_PSI);
    # aircraft altitude reached at maximum differential with the selected cabin altitude (ACFT ALT scale)
    var sel = ctl.getNode("cabin-alt-ft", 1).getValue() or 7000;
    sys.getNode("acft-alt-at-max-diff-ft", 1).setDoubleValue(alt_of(p_of(sel) - MAX_DIFF_PSI * INHG_PER_PSI));
};

var timer = maketimer(dt, update);
setlistener("sim/signals/fdm-initialized", func { init(); }, 0, 0);
