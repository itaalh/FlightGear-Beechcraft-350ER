#############################################################################
# Beechcraft King Air 350 - electrical system (simplified)
#
# 28 V DC: two 300 A starter-generators (one per engine, cockpit switches = bus-tie), 24 V battery,
# external power. 115 V AC from the inverter (LH/RH AC bus switches) for the EFIS and the gyros.
# Outputs feed the standard FlightGear instruments (/systems/electrical/outputs/...).
#
# License: GPL v2 or later
#############################################################################

var elec = props.globals.getNode("controls/electric", 1);
var out  = props.globals.getNode("systems/electrical/outputs", 1);
var sys  = props.globals.getNode("systems/electrical", 1);
var light = props.globals.getNode("controls/lighting", 1);

var battery_charge = 1.0;      # 0..1
var BATTERY_AH = 42.0;

var update = func {
    var dt = 0.2;
    var batt_sw = elec.getNode("battery-switch", 1).getBoolValue();
    var ext_sw  = elec.getNode("external-power", 1).getBoolValue() and (getprop("gear/gear[1]/wow") or 0);
    var gen = [0, 0];
    # heaters and deicers (Nasal/ice-protection.nas), shared by the generators on line
    var extra = contains(globals, "iceprotection") ? iceprotection.load_amps() : 0;
    var ngen_on = 0;
    foreach (var i; [0, 1])
        if ((getprop("engines/engine[" ~ i ~ "]/running") or 0) and elec.getNode("engine[" ~ i ~ "]/bus-tie", 1).getBoolValue()
            and (getprop("engines/engine[" ~ i ~ "]/n1") or 0) > 52) ngen_on += 1;
    foreach (var i; [0, 1]) {
        var n1 = getprop("engines/engine[" ~ i ~ "]/n1") or 0;
        var running = getprop("engines/engine[" ~ i ~ "]/running") or 0;
        var sw = elec.getNode("engine[" ~ i ~ "]/bus-tie", 1).getBoolValue();
        gen[i] = (running and sw and n1 > 52) ? 1 : 0;
        sys.getNode("gen-load[" ~ i ~ "]", 1).setDoubleValue(gen[i] ? (0.35 + 0.15 * (ngen_on > 1 ? 0 : 1) + extra / 300.0 / ngen_on) : 0);
    }
    var ngen = gen[0] + gen[1];
    var volts = 0.0;
    if (ngen > 0 or ext_sw) volts = 28.5;
    elsif (batt_sw) volts = 22.0 + 2.5 * battery_charge;
    # battery current (BATT AMP gauge, + = charge): on its own the battery feeds the bus (25 A + heaters) and the
    # starters (about 300 A each while cranking); with a generator or external power on line it recharges, at a
    # current that falls as it fills up. Disconnected when the battery switch is off.
    var batt_amps = 0.0;
    if (batt_sw and ngen == 0 and !ext_sw) {
        batt_amps = -(25.0 + extra);
        foreach (var i; [0, 1])
            if (getprop("controls/engines/engine[" ~ i ~ "]/starter") and (getprop("engines/engine[" ~ i ~ "]/n1") or 0) < 50)
                batt_amps -= 300.0;
    } elsif (batt_sw) {
        batt_amps = math.min(60.0, 2.0 + 150.0 * (1.0 - battery_charge));
    }
    battery_charge += dt / 3600.0 * batt_amps / BATTERY_AH;
    battery_charge = math.min(1.0, math.max(0.0, battery_charge));
    sys.getNode("ammeter", 1).setDoubleValue(batt_amps);
    if (batt_sw and ngen == 0 and battery_charge < 0.05) volts = 18.0;

    var dc = (volts > 20) ? 1 : 0;
    sys.getNode("volts", 1).setDoubleValue(volts);
    sys.getNode("battery-charge", 1).setDoubleValue(battery_charge);
    sys.getNode("amps", 1).setDoubleValue(ngen > 0 ? 40 : (batt_sw ? -25 - extra : 0));

    # AC (inverter)
    var inv = elec.getNode("inverter-switch", 1).getBoolValue();
    var ac = (dc and inv) ? 115.0 : 0.0;
    sys.getNode("AC", 1).setDoubleValue(ac);
    var lh_ac = ac * (elec.getNode("LH-AC-bus", 1).getBoolValue() ? 1 : 0);
    var rh_ac = ac * (elec.getNode("RH-AC-bus", 1).getBoolValue() ? 1 : 0);
    sys.getNode("LH-ac-bus", 1).setDoubleValue(lh_ac);
    sys.getNode("RH-ac-bus", 1).setDoubleValue(rh_ac);
    # electric gyros: the attitude indicators are driven through a pseudo "suction" (5 inHg = ok)
    sys.getNode("gyro-suction-inhg", 1).setDoubleValue((lh_ac > 0 or rh_ac > 0) ? 5.0 : 0.0);

    # avionics bus
    var av = elec.getNode("avionics-switch", 1).getBoolValue() ? volts : 0.0;
    foreach (var n; ["nav", "nav[1]", "comm", "comm[1]", "adf", "dme", "gps", "transponder", "turn-coordinator", "mk-viii", "fgc-65", "audio-panel", "autopilot", "fg1000-pfd", "fg1000-mfd"])
        out.getNode(n, 1).setDoubleValue(av);
    out.getNode("efis[0]", 1).setDoubleValue(elec.getNode("efis/bank[0]", 1).getBoolValue() ? lh_ac / 115.0 * 29 : 0);
    out.getNode("efis[1]", 1).setDoubleValue(elec.getNode("efis/bank[1]", 1).getBoolValue() ? rh_ac / 115.0 * 29 : 0);
    out.getNode("efis", 1).setDoubleValue(out.getNode("efis[0]").getValue());

    # lights
    var pwr = dc ? volts : 0.0;
    out.getNode("lights/landing-lights[0]", 1).setDoubleValue(pwr * (light.getNode("landing-lights[0]", 1).getBoolValue() ? 1 : 0));
    out.getNode("lights/landing-lights[1]", 1).setDoubleValue(pwr * (light.getNode("landing-lights[1]", 1).getBoolValue() ? 1 : 0));
    out.getNode("lights/taxi-lights", 1).setDoubleValue(pwr * (light.getNode("taxi-lights", 1).getBoolValue() ? 1 : 0));
    out.getNode("lights/logo-lights", 1).setDoubleValue(pwr * (light.getNode("logo-lights", 1).getBoolValue() ? 1 : 0));
    out.getNode("lights/nav-lights", 1).setDoubleValue(pwr * (light.getNode("nav-lights", 1).getBoolValue() ? 1 : 0));
    out.getNode("lights/recog-lights", 1).setDoubleValue(pwr * (light.getNode("recog-lights", 1).getBoolValue() ? 1 : 0));
    out.getNode("lights/instrument-lights", 1).setDoubleValue(pwr * (light.getNode("instruments-norm", 1).getValue() or 0));
    out.getNode("lights/eng-lights", 1).setDoubleValue(pwr * (light.getNode("eng-norm", 1).getValue() or 0));
    out.getNode("lights/strobe", 1).setDoubleValue(pwr * (getprop("sim/model/lights/strobe/state") or 0));
    out.getNode("lights/beacon", 1).setDoubleValue(pwr * (getprop("sim/model/lights/beacon/state") or 0));
    # starters
    out.getNode("starter[0]", 1).setDoubleValue(pwr * (getprop("controls/engines/engine[0]/starter") or 0));
    out.getNode("starter[1]", 1).setDoubleValue(pwr * (getprop("controls/engines/engine[1]/starter") or 0));
    # misc buses used by generic instruments
    out.getNode("bus-dc", 1).setDoubleValue(pwr);
    out.getNode("annunciators", 1).setDoubleValue(pwr);
};

var timer = maketimer(0.2, update);
setlistener("sim/signals/fdm-initialized", func { timer.start(); print("KingAir-350: electrical system ok"); }, 0, 0);
