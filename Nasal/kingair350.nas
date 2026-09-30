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

        # ignition while starting (not in STARTER ONLY, Pro Line Fusion cockpit) and auto-ignition (armed by default)
        # below 55 % N1
        var starting = ctl[i].getNode("starter", 1).getBoolValue();
        var starter_only = ctl[i].getNode("starter-only", 1).getBoolValue();
        var auto_ign = ctl[i].getNode("auto-ignition", 1).getValue();
        var n1 = eng[i].getNode("n1", 1).getValue() or 0.0;
        var running = eng[i].getNode("running", 1).getBoolValue();
        var ign_cb = !getprop("controls/fusion/cb/auto-ign[" ~ i ~ "]");       # Pro Line Fusion cockpit breaker
        ctl[i].getNode("ignition", 1).setBoolValue((starting and !starter_only) or ((auto_ign == nil or auto_ign) and ign_cb and running and n1 < 55));

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

# joystick / keyboard "Mixture" controls move the condition levers (a turboprop has no mixture):
# FlightGear's joystick dialog only offers mixture axes and buttons. Same scale: 0 = FUEL CUT-OFF,
# 0.5 = LOW IDLE, 1 = HIGH IDLE. Listeners fire on changes only and are set after the FDM
# initialisation, so the mixture value of the -set.xml (1.0) never opens the fuel by itself.
# The "Mixture All Engines" axis needs nothing more: FGData (controls.nas) turns its raw -1..1 value
# into each engine's mixture, which these listeners follow.
var mixture_to_condition = func(i, v) {
    ctl[i].getNode("condition", 1).setDoubleValue(math.clamp(v or 0, 0, 1));
};
setlistener("sim/signals/fdm-initialized", func {
    foreach (var i; ENGINES) {
        (func(i) {
            setlistener("controls/engines/engine[" ~ i ~ "]/mixture", func(n) { mixture_to_condition(i, n.getValue()); }, 0, 0);
        })(i);
    }
}, 0, 0);

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

# start in the air with the engines running. The JSBSim start-up trim cannot converge with these governed
# propellers (it steps the engines by 0.5 s and the governor then swings from stop to stop): it fails and
# leaves the propellers nearly feathered below 200 rpm, where the governor cannot move the blades (no thrust),
# or at two different speeds (strong yaw, then roll), the power levers at idle and no trim. A level-flight state
# is set instead: both propellers at the blade angle of level flight, the power for level flight, the pitch trim
# for the airspeed and the gear up above 150 KCAS (cruise start; below, an approach start keeps it down). The
# airframe is then held for 4 s (JSBSim velocity integrators off: same speed and attitude, straight flight)
# while the engines run and the governors bring both propellers on speed; the aileron trim is set on release.
# The propeller rpm itself cannot be set from FlightGear. Tables from JSBSim level-flight runs (clean,
# 1700 rpm, 13 500 lb).
var LEVEL_KCAS  = [110, 120, 130, 150, 170, 190, 210, 230, 250];
var LEVEL_TRIM  = [-0.163, -0.109, -0.067, -0.005, 0.054, 0.099, 0.129, 0.152, 0.170];
var LEVEL_ALT   = [1000, 10000, 20000, 28000];
var LEVEL_POWER = [[0.30, 0.29, 0.31, 0.33, 0.39, 0.44, 0.52, 0.60, 0.69],
                   [0.33, 0.33, 0.34, 0.38, 0.43, 0.50, 0.59, 0.70, 1.00],
                   [0.39, 0.39, 0.41, 0.46, 0.53, 0.62, 0.76, 1.00, 1.00],
                   [0.50, 0.50, 0.52, 0.58, 0.68, 0.86, 1.00, 1.00, 1.00]];
var LEVEL_BLADE = [[18.2, 19.7, 21.2, 24.2, 27.2, 30.2, 33.1, 35.9, 38.5],
                   [21.3, 22.9, 24.4, 27.7, 30.9, 34.0, 37.2, 40.1, 42.7],
                   [25.5, 27.1, 28.7, 32.2, 35.7, 39.0, 42.3, 45.1, 45.1],
                   [29.4, 31.0, 32.8, 36.4, 40.0, 43.3, 44.2, 44.3, 44.3]];

# position of x in the ascending list xs, clamped at both ends: [interval index, fraction]
var lookup = func(xs, x) {
    var n = size(xs) - 1;
    if (x <= xs[0]) return [0, 0];
    if (x >= xs[n]) return [n - 1, 1];
    var i = 0;
    while (x > xs[i + 1]) i += 1;
    return [i, (x - xs[i]) / (xs[i + 1] - xs[i])];
};
var interp = func(xs, ys, x) {
    var k = lookup(xs, x);
    return ys[k[0]] + (ys[k[0] + 1] - ys[k[0]]) * k[1];
};
var interp_level = func(table, alt, kcas) {
    var k = lookup(LEVEL_ALT, alt);
    var lo = interp(LEVEL_KCAS, table[k[0]], kcas);
    return lo + (interp(LEVEL_KCAS, table[k[0] + 1], kcas) - lo) * k[1];
};

var init_in_air = func {
    if (getprop("sim/presets/onground") or (getprop("position/altitude-agl-ft") or 0) < 50) return;
    var kcas = getprop("velocities/airspeed-kt") or 0;
    var alt = getprop("position/altitude-ft") or 0;
    var weight = getprop("fdm/jsbsim/inertia/weight-lbs") or 13500;
    var power = interp_level(LEVEL_POWER, alt, kcas);
    var blade = interp_level(LEVEL_BLADE, alt, kcas);
    foreach (var i; ENGINES) {
        ctl[i].getNode("throttle", 1).setDoubleValue(power);
        jsb[i].getNode("blade-angle", 1).setDoubleValue(blade);
    }
    # the pitch trim follows the lift coefficient: airspeed scaled to the table weight
    setprop("controls/flight/elevator-trim", interp(LEVEL_KCAS, LEVEL_TRIM, kcas * math.sqrt(13500 / weight)));
    if (kcas > 150) setprop("controls/gear/gear-down", 0);
    hold_airframe(4);
};

var HOLD_PROPS = ["fdm/jsbsim/simulation/integrator/rate/rotational", "fdm/jsbsim/simulation/integrator/rate/translational"];
var hold_saved = nil;
var hold_airframe = func(t) {
    if (hold_saved == nil) {
        hold_saved = [];
        foreach (var p; HOLD_PROPS) {
            var v = getprop(p);
            append(hold_saved, v);
            if (v != nil) setprop(p, 0);
        }
    }
    settimer(release_airframe, t);
};
var release_airframe = func {
    if (hold_saved == nil) return;
    forindex (var k; HOLD_PROPS)
        if (hold_saved[k] != nil) setprop(HOLD_PROPS[k], hold_saved[k]);
    hold_saved = nil;
    trim_roll();
};

# aileron trim for the steady roll moments: residual propeller torque and lateral CG offset (pilot seat, lift
# acting on the centre line). Ailerons: Cl 0.10 per radian of average deflection, 0.349 rad of average
# deflection per unit of command (Aero/KingAir-350*.xml).
var trim_roll = func {
    var l = (getprop("fdm/jsbsim/moments/l-prop-lbsft") or 0) + (getprop("fdm/jsbsim/aero/moment/Roll_prop_swirl") or 0)
          + (getprop("fdm/jsbsim/inertia/weight-lbs") or 0) * (getprop("fdm/jsbsim/inertia/cg-y-in") or 0) / 12;
    var qsb = (getprop("fdm/jsbsim/aero/qbar-psf") or 0) * 310 * 57.92;
    if (qsb > 1000) setprop("controls/flight/aileron-trim", math.clamp(-l / (qsb * 0.10 * 0.349), -0.2, 0.2));
};

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
        init_in_air();
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
# windshield wipers: selector PARK / OFF / SLOW / FAST (controls/electric/wipers/switch-pos -1..2) on the DC bus.
# The blades sweep outboard and back (sim/model/wipers/position-norm, 0 = parked); OFF stops them where they
# are, PARK brings them back to the parked position and the selector springs back to OFF.
# --------------------------------------------------------------------------
var wiper_sw = props.globals.getNode("controls/electric/wipers/switch-pos", 1);
var wiper_pos = props.globals.getNode("sim/model/wipers/position-norm", 1);
var wiper_dir = 1;
var WIPER_RATE = [0.9, 1.25, 2.2];      # sweeps (0 -> 1) per second: PARK, SLOW, FAST

var update_wipers = func {
    var dt = 0.05;
    var sw = int(wiper_sw.getValue() or 0);
    var pos = wiper_pos.getValue() or 0;
    var powered = (getprop("systems/electrical/volts") or 0) > 20 and !getprop("controls/fusion/cb/wipers");
    if (!powered or sw == 0) {
        wiper_timer.stop();
        return;
    }
    if (sw < 0) {                                 # PARK: back to the stop, then OFF
        pos = math.max(0, pos - WIPER_RATE[0] * dt);
        if (pos == 0) { wiper_sw.setIntValue(0); wiper_dir = 1; }
    } else {
        pos += wiper_dir * WIPER_RATE[sw] * dt;
        if (pos >= 1) { pos = 1; wiper_dir = -1; }
        if (pos <= 0) { pos = 0; wiper_dir = 1; }
    }
    wiper_pos.setDoubleValue(pos);
};
var wiper_timer = maketimer(0.05, update_wipers);
setlistener(wiper_sw, func { if (int(wiper_sw.getValue() or 0) != 0) wiper_timer.start(); }, 0, 0);
setlistener("systems/electrical/volts", func(n) {
    if ((n.getValue() or 0) > 20 and int(wiper_sw.getValue() or 0) != 0 and !wiper_timer.isRunning) wiper_timer.start();
}, 0, 0);

# yokes shown or hidden (menu King Air 350 > Yokes visible): kept between sessions
aircraft.data.add("sim/model/yokes-visible");

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
