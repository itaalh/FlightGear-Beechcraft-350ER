#############################################################################
# Beechcraft King Air 350 - aircraft systems (FlightGear / JSBSim)
#
# - engine management: condition levers (cut-off / low idle / high idle), start logic, gauges
# - beta / reverse toggle, autofeather arming
# - lights, doors, tyre smoke, livery
# - automatic start-up sequence
#
# License: GPL v2 or later
#############################################################################

var ENGINES = [0, 1];

var eng   = [props.globals.getNode("engines/engine[0]", 1), props.globals.getNode("engines/engine[1]", 1)];
var ctl   = [props.globals.getNode("controls/engines/engine[0]", 1), props.globals.getNode("controls/engines/engine[1]", 1)];
var jsb   = [props.globals.getNode("fdm/jsbsim/propulsion/engine[0]", 1), props.globals.getNode("fdm/jsbsim/propulsion/engine[1]", 1)];
var elec  = props.globals.getNode("controls/electric", 1);
var fuel  = props.globals.getNode("controls/fuel", 1);

# --------------------------------------------------------------------------
# doors, lights, smoke, livery
# --------------------------------------------------------------------------
var crew_door      = aircraft.door.new("sim/model/door-positions/crew", 2, 0);
var passenger_door = aircraft.door.new("sim/model/door-positions/passenger", 3, 0);
var left_bag_door  = aircraft.door.new("sim/model/door-positions/leftbagage", 2, 0);
var right_bag_door = aircraft.door.new("sim/model/door-positions/rightbagage", 2, 0);

var beacon = aircraft.light.new("sim/model/lights/beacon", [0.08, 1.0], "controls/lighting/beacon/switch");
var strobe = aircraft.light.new("sim/model/lights/strobe", [0.05, 0.05, 0.05, 1.2], "controls/lighting/strobe/switch");

aircraft.livery.init("Aircraft/KingAir-350/Models/Liveries");

var smoke = [];
foreach (var g; [0, 1, 2]) append(smoke, aircraft.tyresmoke.new(g));

# --------------------------------------------------------------------------
# engines
# --------------------------------------------------------------------------
var last_condition = [-1, -1];

var update_engines = func {
    var battery = elec.getNode("battery-switch", 1).getBoolValue();
    var extpwr  = elec.getNode("external-power", 1).getBoolValue();
    var power_for_start = battery or extpwr;

    foreach (var i; ENGINES) {
        var cond = ctl[i].getNode("condition", 1).getValue() or 0.0;
        # condition lever in CUT-OFF, or fire handle pulled (firewall fuel shutoff valve), closes the fuel (JSBSim cutoff)
        ctl[i].getNode("cutoff", 1).setBoolValue(cond < 0.05 or ctl[i].getNode("fire-handle", 1).getBoolValue());

        # the JSBSim starter needs "generator power": electrical power available for the starter/generator
        elec.getNode("engine[" ~ i ~ "]/generator", 1).setBoolValue(power_for_start);

        # auto-ignition while starting or when selected
        var starting = ctl[i].getNode("starter", 1).getBoolValue();
        var n1 = eng[i].getNode("n1", 1).getValue() or 0.0;
        var running = eng[i].getNode("running", 1).getBoolValue();
        ctl[i].getNode("ignition", 1).setBoolValue(starting or (running and n1 < 55));

        # gauges: torque %, ITT, propeller rpm
        eng[i].getNode("rpm", 1).setDoubleValue(eng[i].getNode("thruster/rpm", 1).getValue() or 0.0);
        eng[i].getNode("torque-pct", 1).setDoubleValue(jsb[i].getNode("torque-pct", 1).getValue() or 0.0);
        eng[i].getNode("itt-degc", 1).setDoubleValue(jsb[i].getNode("itt-c", 1).getValue() or 0.0);
        eng[i].getNode("itt-norm", 1).setDoubleValue((jsb[i].getNode("itt-c", 1).getValue() or 0.0) / 1000.0);
        eng[i].getNode("prop-feathered", 1).setBoolValue((getprop("fdm/jsbsim/fcs/feather-pos-norm[" ~ i ~ "]") or 0) > 0.5);
        eng[i].getNode("autofeather-active", 1).setBoolValue((getprop("fdm/jsbsim/systems/engines/autofeather-active[" ~ i ~ "]") or 0) > 0.5);

        # simple oil model for the gauges: both are damped low-pass filters (10 Hz timer) so a
        # tick-to-tick wobble in N1 or in the running/starting flags does not show up as needle jitter,
        # same as the real gauges' own mechanical damping. Written to their own "-ind" properties:
        # JSBSim rewrites oil-pressure-psi / oil-temperature-degf every frame with its own (low) values,
        # and sharing them made the needles jump between the two models.
        var oilt = eng[i].getNode("oil-temperature-ind-degf", 1).getValue() or 60;
        var target_t = running ? (150 + 0.4 * n1) : 60;
        eng[i].getNode("oil-temperature-ind-degf", 1).setDoubleValue(oilt + (target_t - oilt) * 0.01);

        var oilp = eng[i].getNode("oil-pressure-ind-psi", 1).getValue() or 0;
        var target_p = running ? (60 + 0.5 * n1) : (starting ? 15 : 0);
        eng[i].getNode("oil-pressure-ind-psi", 1).setDoubleValue(oilp + (target_p - oilp) * 0.15);
    }

    # aux tank transfer pumps (AUTO / OFF): priority 0 disables the tank in JSBSim
    setprop("fdm/jsbsim/propulsion/tank[0]/priority", fuel.getNode("Laux-switch", 1).getValue() == "off" ? 0 : 1);
    setprop("fdm/jsbsim/propulsion/tank[3]/priority", fuel.getNode("Raux-switch", 1).getValue() == "off" ? 0 : 1);

    # crossfeed switch (cockpit: left / off / right) -> JSBSim crossfeed (+1: left main feeds right engine)
    var xf = fuel.getNode("transfer", 1).getValue();
    fuel.getNode("crossfeed", 1).setIntValue(xf == "left" ? 1 : (xf == "right" ? -1 : 0));
};

var engine_timer = maketimer(0.1, update_engines);

# --------------------------------------------------------------------------
# beta / reverse range: with the power levers at idle, lift over the gate (Delete key or menu).
# In reverse, the power levers control the blade angle (beta) and then the reverse power.
# --------------------------------------------------------------------------
var toggle_reverse = func {
    var any_on = 0;
    foreach (var i; ENGINES) if (ctl[i].getNode("reverser", 1).getBoolValue()) any_on = 1;
    if (!any_on) {
        var thr = 0;
        foreach (var i; ENGINES) if ((ctl[i].getNode("throttle", 1).getValue() or 0) > thr) thr = ctl[i].getNode("throttle", 1).getValue();
        if (thr > 0.15) {
            gui.popupTip("Power levers must be at IDLE to enter the beta/reverse range");
            return;
        }
        if (!getprop("gear/gear[1]/wow")) {
            gui.popupTip("Reverse is only available on the ground");
            return;
        }
    }
    foreach (var i; ENGINES) {
        ctl[i].getNode("throttle", 1).setDoubleValue(0.0);
        ctl[i].getNode("reverser", 1).setBoolValue(!any_on);
    }
    gui.popupTip(any_on ? "Power levers: FORWARD range" : "Power levers: BETA / REVERSE range");
};

var toggle_autofeather = func {
    var n = props.globals.getNode("controls/engines/autofeather", 1);
    n.setBoolValue(!n.getBoolValue());
    gui.popupTip("Autofeather " ~ (n.getBoolValue() ? "ARMED" : "OFF"));
};

var toggle_yaw_damper = func {
    var n = props.globals.getNode("controls/flight/yaw-damper", 1);
    n.setBoolValue(!n.getBoolValue());
    setprop("instrumentation/fgc-65/app-65a/YD", n.getBoolValue() ? "YD" : "");
    gui.popupTip("Yaw damper " ~ (n.getBoolValue() ? "ON" : "OFF"));
};

var toggle_rudder_boost = func {
    var n = props.globals.getNode("controls/flight/rudder-boost", 1);
    n.setBoolValue(!n.getBoolValue());
    gui.popupTip("Rudder boost " ~ (n.getBoolValue() ? "ON" : "OFF"));
};

# condition lever helper for keyboard users: cycles CUT-OFF (0) / LOW IDLE (0.5) / HIGH IDLE (1)
var condition_step = func(dir) {
    foreach (var i; ENGINES) {
        if (!ctl[i].getNode("selected", 1).getBoolValue()) continue;
        var c = ctl[i].getNode("condition", 1).getValue() or 0;
        var v = c;
        if (dir > 0) v = (c < 0.25) ? 0.5 : 1.0;
        else         v = (c > 0.75) ? 0.5 : 0.0;
        ctl[i].getNode("condition", 1).setDoubleValue(v);
    }
    var c = ctl[0].getNode("condition", 1).getValue();
    gui.popupTip("Condition levers: " ~ (c < 0.25 ? "FUEL CUT-OFF" : (c < 0.75 ? "LOW IDLE" : "HIGH IDLE")));
};

# --------------------------------------------------------------------------
# automatic start-up (menu)
# --------------------------------------------------------------------------
var autostart_state = 0;
var autostart_engine = 0;
var autostart_t = 0;

var autostart = func {
    if (autostart_state != 0) return;
    if (eng[0].getNode("running").getBoolValue() and eng[1].getNode("running").getBoolValue()) {
        gui.popupTip("Both engines are already running");
        return;
    }
    gui.popupTip("Automatic start: battery ON, avionics OFF, condition levers CUT-OFF");
    elec.getNode("battery-switch", 1).setBoolValue(1);
    elec.getNode("avionics-switch", 1).setBoolValue(0);
    setprop("controls/gear/brake-parking", 1);
    foreach (var i; ENGINES) {
        ctl[i].getNode("throttle", 1).setDoubleValue(0);
        ctl[i].getNode("propeller-pitch", 1).setDoubleValue(1);
        ctl[i].getNode("condition", 1).setDoubleValue(0);
        ctl[i].getNode("reverser", 1).setBoolValue(0);
        elec.getNode("engine[" ~ i ~ "]/bus-tie", 1).setBoolValue(0);
    }
    autostart_engine = eng[0].getNode("running").getBoolValue() ? 1 : 0;
    autostart_state = 1; autostart_t = 0;
    autostart_timer.start();
};

var autostart_step = func {
    var i = autostart_engine;
    autostart_t += 0.5;
    var n1 = eng[i].getNode("n1", 1).getValue() or 0;
    if (autostart_state == 1) {
        # engage the starter
        ctl[0].getNode("selected", 1).setBoolValue(i == 0);
        ctl[1].getNode("selected", 1).setBoolValue(i == 1);
        ctl[i].getNode("starter", 1).setBoolValue(1);
        gui.popupTip("Engine " ~ (i + 1) ~ ": starter ON");
        autostart_state = 2; autostart_t = 0;
    } elsif (autostart_state == 2) {
        ctl[i].getNode("starter", 1).setBoolValue(1);
        if (n1 >= 12) {
            ctl[i].getNode("condition", 1).setDoubleValue(0.5);
            gui.popupTip("Engine " ~ (i + 1) ~ ": N1 12 %, condition lever LOW IDLE - light-off");
            autostart_state = 3; autostart_t = 0;
        } elsif (autostart_t > 30) {
            gui.popupTip("Engine " ~ (i + 1) ~ ": starter did not spin the engine (check battery)");
            ctl[i].getNode("starter", 1).setBoolValue(0);
            autostart_state = 0; autostart_timer.stop();
        }
    } elsif (autostart_state == 3) {
        if (n1 < 50) ctl[i].getNode("starter", 1).setBoolValue(1);
        if (eng[i].getNode("running", 1).getBoolValue() and n1 > 58) {
            ctl[i].getNode("starter", 1).setBoolValue(0);
            elec.getNode("engine[" ~ i ~ "]/bus-tie", 1).setBoolValue(1);
            gui.popupTip("Engine " ~ (i + 1) ~ ": idle, generator ON");
            autostart_state = 4; autostart_t = 0;
        } elsif (autostart_t > 45) {
            gui.popupTip("Engine " ~ (i + 1) ~ ": start aborted");
            ctl[i].getNode("starter", 1).setBoolValue(0);
            ctl[i].getNode("condition", 1).setDoubleValue(0);
            autostart_state = 0; autostart_timer.stop();
        }
    } elsif (autostart_state == 4) {
        if (autostart_t < 3) return;
        if (i == 0 and !eng[1].getNode("running").getBoolValue()) {
            autostart_engine = 1; autostart_state = 1; autostart_t = 0;
        } else {
            elec.getNode("avionics-switch", 1).setBoolValue(1);
            elec.getNode("inverter-switch", 1).setBoolValue(1);
            setprop("controls/lighting/beacon/switch", 1);
            setprop("controls/lighting/nav-lights", 1);
            setprop("sim/model/start-idling", 1);
            gui.popupTip("Both engines running - avionics ON. Ready to taxi.");
            autostart_state = 0; autostart_timer.stop();
        }
    }
};
var autostart_timer = maketimer(0.5, autostart_step);

# automatic start when FlightGear starts with running engines (--prop:/sim/presets/running=true or
# the "start with engines running" option): set the levers accordingly
var init_running = func {
    if (getprop("engines/engine[0]/running") or getprop("engines/engine[1]/running") or getprop("sim/presets/running")) {
        foreach (var i; ENGINES) {
            ctl[i].getNode("condition", 1).setDoubleValue(0.5);
            ctl[i].getNode("propeller-pitch", 1).setDoubleValue(1);
            elec.getNode("engine[" ~ i ~ "]/bus-tie", 1).setBoolValue(1);
        }
        elec.getNode("battery-switch", 1).setBoolValue(1);
        elec.getNode("avionics-switch", 1).setBoolValue(1);
    }
};

# --------------------------------------------------------------------------
# shutdown helper (menu)
# --------------------------------------------------------------------------
var shutdown = func {
    foreach (var i; ENGINES) {
        ctl[i].getNode("throttle", 1).setDoubleValue(0);
        ctl[i].getNode("condition", 1).setDoubleValue(0);
        ctl[i].getNode("reverser", 1).setBoolValue(0);
    }
    gui.popupTip("Condition levers CUT-OFF");
};

# --------------------------------------------------------------------------
# init
# --------------------------------------------------------------------------
setlistener("sim/signals/fdm-initialized", func {
    setprop("instrumentation/fgc-65/settings/hdg", getprop("orientation/heading-magnetic-deg") or 0);
    init_running();
    engine_timer.start();
    print("KingAir-350: systems initialised");
}, 0, 0);

setlistener("sim/signals/reinit", func {
    autostart_state = 0; autostart_timer.stop();
    settimer(init_running, 1.0);
}, 0, 0);
