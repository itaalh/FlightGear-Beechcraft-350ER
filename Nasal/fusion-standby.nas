#############################################################################
# Beechcraft King Air 350ER Pro Line Fusion - standby flight display (namespace fusion_standby)
#
# Canvas drawn on the screen of the standby unit (object Fusion.Stby.screen, Models/Fusion/fusion-cockpit.ac):
# attitude with pitch ladder and roll scale, airspeed and altitude tapes with readouts, heading, slip indicator
# and its own altimeter setting (instrumentation/altimeter[1]/setting-inhg: knob, push = pilot setting, BARO key =
# STD). MENU declutters the heading and slip lines. Powered by the STBY DISPLAY switch (ON / OFF / TEST) from the
# DC bus, with its internal battery for 30 minutes when the bus fails.
#
# License: GPL v2 or later
#############################################################################

var W = 400;
var H = 300;
var PX_DEG = 5.2;          # pitch ladder scale
var cv = nil;
var root = nil;
var horizon = nil;
var horizon_rot = nil;
var elems = {};
var declutter = 0;
var std = 0;
var battery_s = 1800.0;

var FONT = "LiberationFonts/LiberationSansNarrow-Bold.ttf";

var txt = func(g, x, y, size, align, color = nil) {
    var t = g.createChild("text").setFont(FONT).setFontSize(size, 1.0).setAlignment(align).setTranslation(x, y);
    t.setColor(color == nil ? [1, 1, 1] : color);
    return t;
};

var build = func {
    cv = canvas.new({"name": "Fusion standby", "size": [512, 384], "view": [W, H], "mipmapping": 1});
    cv.setColorBackground(0, 0, 0, 1);
    cv.addPlacement({"node": "Fusion.Stby.screen"});
    root = cv.createGroup();

    # ---- attitude
    var att = root.createChild("group");
    att.set("clip", "rect(22px, 318px, 262px, 82px)");        # top, right, bottom, left
    horizon_rot = att.createChild("group").setTranslation(200, 142);
    horizon = horizon_rot.createChild("group");
    horizon.createChild("path").rect(-400, -600, 800, 600).setColorFill(0.16, 0.42, 0.85).setColor(0.16, 0.42, 0.85);
    horizon.createChild("path").rect(-400, 0, 800, 600).setColorFill(0.50, 0.30, 0.12).setColor(0.50, 0.30, 0.12);
    horizon.createChild("path").moveTo(-400, 0).lineTo(400, 0).setColor(1, 1, 1).setStrokeLineWidth(2);
    for (var p = -40; p <= 40; p += 5) {
        if (p == 0) continue;
        var w = (math.mod(p, 10) == 0) ? 50 : 24;
        horizon.createChild("path").moveTo(-w / 2, -p * PX_DEG).lineTo(w / 2, -p * PX_DEG).setColor(1, 1, 1).setStrokeLineWidth(2);
        if (math.mod(p, 10) == 0) {
            txt(horizon, -w / 2 - 6, -p * PX_DEG + 5, 14, "right-baseline").setText(sprintf("%d", math.abs(p)));
            txt(horizon, w / 2 + 6, -p * PX_DEG + 5, 14, "left-baseline").setText(sprintf("%d", math.abs(p)));
        }
    }
    # roll scale (fixed) and pointer (moves with the horizon)
    var rs = root.createChild("group").setTranslation(200, 142);
    foreach (var a; [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]) {
        var r0 = 104;
        var r1 = (math.abs(a) == 30 or math.abs(a) == 60 or a == 0) ? 116 : 110;
        var s = math.sin(a * D2R);
        var c = math.cos(a * D2R);
        rs.createChild("path").moveTo(r0 * s, -r0 * c).lineTo(r1 * s, -r1 * c).setColor(1, 1, 1).setStrokeLineWidth(2);
    }
    elems.roll_ptr = horizon_rot.createChild("path").moveTo(0, -102).lineTo(-7, -90).lineTo(7, -90).close()
                     .setColorFill(1, 1, 1).setColor(1, 1, 1);
    # aircraft symbol
    var ac = root.createChild("group").setTranslation(200, 142);
    ac.createChild("path").moveTo(-70, 0).lineTo(-28, 0).lineTo(-28, 10).moveTo(28, 10).lineTo(28, 0).lineTo(70, 0)
        .setColor(1, 0.85, 0).setStrokeLineWidth(5);
    ac.createChild("path").rect(-4, -4, 8, 8).setColorFill(1, 0.85, 0).setColor(1, 0.85, 0);
    # slip indicator
    elems.slip = root.createChild("path").rect(-7, 0, 14, 5).setColorFill(1, 1, 1).setColor(1, 1, 1).setTranslation(200, 52);
    elems.slip_group = elems.slip;

    # ---- airspeed tape (left) and altitude tape (right)
    var bg = root.createChild("group");
    bg.createChild("path").rect(0, 22, 80, 240).setColorFill(0.15, 0.15, 0.17, 0.85);
    bg.createChild("path").rect(320, 22, 80, 240).setColorFill(0.15, 0.15, 0.17, 0.85);
    elems.spd_tape = root.createChild("group");
    elems.spd_tape.set("clip", "rect(22px, 80px, 262px, 0px)");
    elems.spd_marks = elems.spd_tape.createChild("group");
    for (var v = 0; v <= 400; v += 10) {
        var y = -v * 3.0;
        elems.spd_marks.createChild("path").moveTo(64, y).lineTo(80, y).setColor(1, 1, 1).setStrokeLineWidth(2);
        if (math.mod(v, 20) == 0) txt(elems.spd_marks, 58, y + 6, 16, "right-baseline").setText(sprintf("%d", v));
    }
    elems.alt_tape = root.createChild("group");
    elems.alt_tape.set("clip", "rect(22px, 400px, 262px, 320px)");
    elems.alt_marks = elems.alt_tape.createChild("group");
    elems.alt_labels = [];
    for (var k = -8; k <= 8; k += 1) {
        var y = -k * 25.0;
        elems.alt_marks.createChild("path").moveTo(320, y).lineTo(334, y).setColor(1, 1, 1).setStrokeLineWidth(2);
        append(elems.alt_labels, txt(elems.alt_marks, 338, y + 6, 15, "left-baseline"));
    }
    # readout boxes
    root.createChild("path").rect(4, 128, 70, 28).setColorFill(0, 0, 0).setColor(1, 1, 1).setStrokeLineWidth(2);
    elems.ias = txt(root, 68, 150, 22, "right-baseline");
    root.createChild("path").rect(322, 128, 76, 28).setColorFill(0, 0, 0).setColor(1, 1, 1).setStrokeLineWidth(2);
    elems.alt = txt(root, 394, 150, 22, "right-baseline");

    # ---- heading and baro
    root.createChild("path").rect(80, 262, 240, 38).setColorFill(0.08, 0.08, 0.1, 1);
    elems.hdg = txt(root, 200, 292, 24, "center-baseline");
    elems.hdg_box = root.createChild("path").rect(170, 268, 60, 30).setColor(1, 1, 1).setStrokeLineWidth(2);
    elems.baro = txt(root, 396, 18, 16, "right-baseline", [0.3, 1, 1]);
    elems.ias_unit = txt(root, 6, 18, 14, "left-baseline", [0.3, 1, 1]).setText("KT");

    # ---- test / off pages
    elems.test = root.createChild("group");
    elems.test.createChild("path").rect(0, 0, W, H).setColorFill(1, 1, 1);
    txt(elems.test, 200, 160, 40, "center-baseline", [0, 0, 0]).setText("TEST");
    elems.test.hide();
    elems.batt = txt(root, 200, 40, 16, "center-baseline", [1, 0.8, 0]).setText("ON BAT");
    elems.batt.hide();
};

var powered = func(dt) {
    var sw = getprop("/controls/fusion/stby-display");
    if (sw == nil) sw = 1;
    if (sw == 0) return 0;
    if ((getprop("/systems/electrical/volts") or 0) > 20) {
        battery_s = math.min(1800, battery_s + dt * 0.5);
        elems.batt.hide();
        return 1;
    }
    if (battery_s <= 0) return 0;
    battery_s -= dt;
    elems.batt.show();
    return 1;
};

var update = func {
    var dt = 0.05;
    if (!powered(dt)) {
        cv.set("visible", 0);
        return;
    }
    cv.set("visible", 1);
    var test = (getprop("/controls/fusion/stby-display") or 0) == -1;
    if (test) { elems.test.show(); return; }
    elems.test.hide();

    var pitch = getprop("/orientation/pitch-deg") or 0;
    var roll = getprop("/orientation/roll-deg") or 0;
    horizon_rot.setRotation(-roll * D2R);
    horizon.setTranslation(0, pitch * PX_DEG);

    var ias = math.max(0, getprop("/instrumentation/airspeed-indicator/indicated-speed-kt") or 0);
    elems.spd_marks.setTranslation(0, 142 + ias * 3.0);
    elems.ias.setText(ias < 30 ? "---" : sprintf("%d", ias));

    var setting = std ? 29.92 : (getprop("/instrumentation/altimeter[1]/setting-inhg") or 29.92);
    var p = getprop("/systems/static/pressure-inhg") or 29.92;
    var alt = 145442.16 * (1 - math.pow(p / setting, 0.190263));
    var base = math.floor(alt / 100) * 100;
    elems.alt_marks.setTranslation(0, 142 + (alt - base) * 0.25);
    forindex (var k; elems.alt_labels) {
        var v = base + (k - 8) * 100;
        elems.alt_labels[k].setText(math.mod(v, 200) == 0 ? sprintf("%d", v) : "");
    }
    elems.alt.setText(sprintf("%d", math.round(alt / 10) * 10));
    elems.baro.setText(std ? "STD" : sprintf("%.2f IN", setting));

    if (declutter) { elems.hdg.hide(); elems.hdg_box.hide(); elems.slip.hide(); }
    else {
        elems.hdg.show(); elems.hdg_box.show(); elems.slip.show();
        elems.hdg.setText(sprintf("%03d", math.mod(math.round(getprop("/orientation/heading-magnetic-deg") or 0) + 359, 360) + 1));
        var slip = getprop("/instrumentation/slip-skid-ball/indicated-slip-skid") or 0;
        elems.slip.setTranslation(200 + math.clamp(slip * 12, -40, 40), 52);
    }
};

# keys and knob (Models/Fusion/fusion-cockpit.xml)
var menu = func { declutter = !declutter; };
var baro_std = func { std = !std; gui.popupTip("Standby altimeter: " ~ (std ? "STD" : sprintf("%.2f inHg", getprop("/instrumentation/altimeter[1]/setting-inhg") or 29.92))); };
var baro_sync = func {
    std = 0;
    setprop("/instrumentation/altimeter[1]/setting-inhg", getprop("/instrumentation/altimeter/setting-inhg") or 29.92);
};

var timer = maketimer(0.05, update);
setlistener("/sim/signals/fdm-initialized", func {
    if (!getprop("/sim/model/fusion/cockpit")) return;
    build();
    timer.start();
}, 0, 0);
