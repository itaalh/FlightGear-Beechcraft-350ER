#############################################################################
# Beechcraft King Air 350 - ice protection
#
# Switches of the ICE PROTECTION panel (Models/flightdeck.xml), after the FlightSafety King Air 300/350
# Pilot Training Manual:
# - engine anti-ice (inertial separator vanes, ~20 s travel; L/R ENG ANTI-ICE advisory once in position),
# - surface deice: SINGLE cycle inflates the wing boots (~6 s, WING DEICE) then the tail boots
#   (~4 s, TAIL DEICE),
# - propeller deice (AUTO: heated in sequence, 26-32 A on the prop ammeter; MANUAL: momentary),
# - windshield, pitot, stall warning, fuel vent and brake deice heat.
# Outputs under /systems/anti-ice/, read by Nasal/annunciators.nas and Nasal/electrical.nas.
#
# License: GPL v2 or later
#############################################################################

var ctl = props.globals.getNode("controls/anti-ice", 1);
var sys = props.globals.getNode("systems/anti-ice", 1);

var VANE_TRAVEL_S = 20.0;
var WING_BOOTS_S = 6.0;
var TAIL_BOOTS_S = 4.0;

var dt = 0.25;
var boot_t = -1;          # time into the surface deice cycle, -1 = idle
var prop_t = 0;

var dc_ok = func { (getprop("systems/electrical/volts") or 0) > 20; };

var update = func {
    var dc = dc_ok();

    # inertial separator vanes: electric actuators, move towards the selected position
    foreach (var i; [0, 1]) {
        var n = sys.getNode("engine[" ~ i ~ "]/vane-pos-norm", 1);
        var pos = n.getValue() or 0;
        var target = ctl.getNode("engine[" ~ i ~ "]/inlet-heat", 1).getBoolValue() ? 1 : 0;
        if (dc) pos += math.clamp(target - pos, -dt / VANE_TRAVEL_S, dt / VANE_TRAVEL_S);
        n.setDoubleValue(pos);
    }

    # surface deice: one wing + tail cycle per SINGLE selection (needs engine bleed air)
    var bleed = getprop("engines/engine[0]/running") or getprop("engines/engine[1]/running");
    if (boot_t < 0 and ctl.getNode("wing-deice-cycle", 1).getBoolValue() and dc and bleed) boot_t = 0;
    if (boot_t >= 0) {
        boot_t += dt;
        if (boot_t > WING_BOOTS_S + TAIL_BOOTS_S) boot_t = -1;
    }
    sys.getNode("wing-boots", 1).setBoolValue(boot_t >= 0 and boot_t <= WING_BOOTS_S);
    sys.getNode("tail-boots", 1).setBoolValue(boot_t > WING_BOOTS_S);

    # propeller deice: AUTO cycles the heating elements, the ammeter reads 26-32 A; MANUAL overrides
    var prop_auto = ctl.getNode("prop-heat", 1).getBoolValue();
    var prop_man = ctl.getNode("prop-heat-manual", 1).getBoolValue();
    prop_t += dt;
    var amps = 0;
    if (dc and (prop_auto or prop_man)) amps = 29 + 3 * math.sin(prop_t * 0.07);
    sys.getNode("prop-deice-amps", 1).setDoubleValue(amps);

    # heaters: on when switched and powered
    foreach (var h; ["window-heat[0]", "window-heat[1]", "pitot-heat[0]", "pitot-heat[1]", "stall-warn-heat",
                     "fuel-vent-heat[0]", "fuel-vent-heat[1]", "brake-deice"])
        sys.getNode(h, 1).setBoolValue(dc and ctl.getNode(h, 1).getBoolValue());
};

# extra DC load for the electrical system (A)
var load_amps = func {
    var a = sys.getNode("prop-deice-amps", 1).getValue() or 0;
    foreach (var h; ["window-heat[0]", "window-heat[1]"]) if (sys.getNode(h, 1).getBoolValue()) a += 25;
    foreach (var h; ["pitot-heat[0]", "pitot-heat[1]", "stall-warn-heat", "fuel-vent-heat[0]", "fuel-vent-heat[1]"])
        if (sys.getNode(h, 1).getBoolValue()) a += 5;
    if (sys.getNode("brake-deice", 1).getBoolValue()) a += 10;
    return a;
};

# switch properties are declared as booleans (off) so that the panel animations and the checklists read them
var SWITCHES = ["controls/anti-ice/engine[0]/inlet-heat", "controls/anti-ice/engine[1]/inlet-heat",
                "controls/anti-ice/engine[0]/actuator-standby", "controls/anti-ice/engine[1]/actuator-standby",
                "controls/anti-ice/pitot-heat[0]", "controls/anti-ice/pitot-heat[1]", "controls/anti-ice/stall-warn-heat",
                "controls/anti-ice/window-heat[0]", "controls/anti-ice/window-heat[1]", "controls/anti-ice/prop-heat",
                "controls/anti-ice/prop-heat-manual", "controls/anti-ice/wing-deice-cycle",
                "controls/anti-ice/fuel-vent-heat[0]", "controls/anti-ice/fuel-vent-heat[1]", "controls/anti-ice/brake-deice",
                "controls/switches/alt-static", "controls/electric/gen-ties-man-close", "controls/electric/bus-sense-reset",
                "controls/engines/prop-overspeed-test", "controls/engines/engine[0]/fire-handle",
                "controls/engines/engine[1]/fire-handle", "controls/gear/lights-test", "controls/gear/downlock-release"];

var timer = maketimer(dt, update);
setlistener("sim/signals/fdm-initialized", func {
    foreach (var p; SWITCHES) {
        var n = props.globals.getNode(p, 1);
        if (n.getType() != "BOOL") n.setBoolValue(n.getBoolValue());
    }
    timer.start();
}, 0, 0);
