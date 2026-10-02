# King Air 350 Engine Indication System for the FG1000 (loaded into the "fg1000" namespace).
#
# Replaces the single piston engine EIS of FGData (EIS-C182T) with a twin turboprop strip: each engine
# parameter is a horizontal scale with the left engine pointer above it and the right engine pointer
# below it, the two digital values on each side of the title (G1000 twin turboprop layout).
# Colour bands are the King Air 350 instrument markings (FlightSafety King Air 300/350 Pilot Training
# Manual, figure 1-16). The strip is drawn here, inside the EISGroup frame of
# Models/Instruments/FG1000/EIS-KingAir.svg; data comes from KingAirEISPublisher
# (Nasal/fg1000-kingair-interfaces.nas).
#
# License: GPL v2 or later

var nasal_dir = getprop("/sim/fg-root") ~ "/Aircraft/Instruments-3d/FG1000/Nasal/";
io.load_nasal(nasal_dir ~ 'EIS/EISStyles.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'EIS/EISOptions.nas', "fg1000");

var EIS_FONT = "LiberationFonts/LiberationSansNarrow-Regular.ttf";

var EIS_WHITE  = [1.0, 1.0, 1.0];
var EIS_GREEN  = [0.0, 0.85, 0.0];
var EIS_YELLOW = [1.0, 0.85, 0.0];
var EIS_RED    = [1.0, 0.1, 0.1];
var EIS_GREY   = [0.45, 0.45, 0.45];
var EIS_CYAN   = [0.0, 0.85, 0.85];

# key in the engine data, title, scale, value format, colour bands [from, to, colour]
var EIS_GAUGES = [
    { key: "TRQ",  title: "TRQ %",    min: 0,    max: 120,  fmt: "%.0f",
      bands: [[0, 100, EIS_GREEN], [100, 120, EIS_RED]] },
    { key: "ITT",  title: "ITT °C",   min: 100,  max: 1100, fmt: "%.0f",       # 1000 C: starting only
      bands: [[400, 820, EIS_GREEN], [820, 1100, EIS_RED]] },
    { key: "PROP", title: "PROP RPM", min: 800,  max: 1900, fmt: "%.0f",
      bands: [[1450, 1700, EIS_GREEN], [1700, 1900, EIS_RED]] },
    { key: "N1",   title: "TURB %",   min: 0,    max: 110,  fmt: "%.1f",
      bands: [[62, 104, EIS_GREEN], [104, 110, EIS_RED]] },
    { key: "FF",   title: "FF PPH",   min: 0,    max: 800,  fmt: "%.0f",       # no limitation markings
      bands: [] },
    { key: "OILP", title: "OIL PSI",  min: 0,    max: 200,  fmt: "%.0f",
      bands: [[0, 60, EIS_RED], [60, 90, EIS_YELLOW], [90, 135, EIS_GREEN], [196, 200, EIS_RED]] },
    { key: "OILT", title: "OIL °C",   min: -40,  max: 120,  fmt: "%.0f",
      bands: [[-40, 0, EIS_YELLOW], [0, 99, EIS_GREEN], [99, 110, EIS_YELLOW], [110, 120, EIS_RED]] },
];

var EIS_X0 = 12;         # scale left end
var EIS_W = 126;         # scale width
var EIS_TOP = 62;        # first gauge
var EIS_ROW = 56;        # gauge block height

# colour of a value: the band it is in (white outside the bands and in the green)
var eis_zone_colour = func(gauge, value) {
    foreach (var b; gauge.bands) {
        if (value >= b[0] and value <= b[1]) return (b[2] == EIS_GREEN) ? EIS_WHITE : b[2];
    }
    if (size(gauge.bands) and value > gauge.bands[-1][1]) return gauge.bands[-1][2];
    return EIS_WHITE;
};

var KingAirEIS =
{
  new : func (mfd, myCanvas, device, svg)
  {
    var obj = {
      parents : [
        KingAirEIS,
        MFDPage.new(mfd, myCanvas, device, svg, "EIS", "")
      ],
      _gauges : [],
    };

    obj.setController(fg1000.KingAirEISController.new(obj, svg));

    var root = svg.getElementById("EISGroup");
    var y = EIS_TOP;
    foreach (var g; EIS_GAUGES) {
      append(obj._gauges, obj._drawGauge(root, g, y));
      y += EIS_ROW;
    }

    # lower part of the strip, below the engine gauges: the ENGINE summary, or the SYSTEM or FUEL page
    # chosen with the ENGINE softkey menu
    obj._low = {};
    foreach (var m; ["ENGINE", "SYSTEM", "FUEL"])
      obj._low[m] = root.createChild("group");
    obj._drawSystem(obj._low.SYSTEM, y);
    obj._drawFuel(obj._low.FUEL, y);
    root = obj._low.ENGINE;

    # fuel: both sides on one scale (full scale = side capacity, set on the first data)
    root.createChild("path").moveTo(4, y - 4).horizTo(146).setColor(EIS_GREY).setStrokeLineWidth(1);
    obj._fuel = obj._drawGauge(root,
      { key: "FUEL", title: "FUEL LBS", min: 0, max: 2600, fmt: "%.0f", bands: [] }, y);
    obj._fuelTotal = obj._text(root, "TOTAL", 8, y + 66, 13, "left-baseline", EIS_CYAN);
    obj._fuelTotalValue = obj._text(root, "", 146, y + 66, 16, "right-baseline", EIS_WHITE);
    y += EIS_ROW + 22;

    # DC electrical
    root.createChild("path").moveTo(4, y - 4).horizTo(146).setColor(EIS_GREY).setStrokeLineWidth(1);
    obj._text(root, "DC VOLTS", 8, y + 14, 13, "left-baseline", EIS_CYAN);
    obj._volts = obj._text(root, "", 146, y + 14, 16, "right-baseline", EIS_WHITE);
    obj._text(root, "DC AMPS", 8, y + 34, 13, "left-baseline", EIS_CYAN);
    obj._amps = obj._text(root, "", 146, y + 34, 16, "right-baseline", EIS_WHITE);
    obj._text(root, "GEN LOAD %", 8, y + 54, 13, "left-baseline", EIS_CYAN);
    obj._loadL = obj._text(root, "", 108, y + 54, 16, "right-baseline", EIS_WHITE);
    obj._loadR = obj._text(root, "", 146, y + 54, 16, "right-baseline", EIS_WHITE);
    obj._text(root, "PROP DEICE A", 8, y + 74, 13, "left-baseline", EIS_CYAN);
    obj._propAmps = obj._text(root, "", 146, y + 74, 16, "right-baseline", EIS_WHITE);
    y += 88;

    # pressurization (Nasal/pressurization.nas)
    root.createChild("path").moveTo(4, y - 4).horizTo(146).setColor(EIS_GREY).setStrokeLineWidth(1);
    obj._text(root, "CABIN ALT FT", 8, y + 14, 13, "left-baseline", EIS_CYAN);
    obj._cabinAlt = obj._text(root, "", 146, y + 14, 16, "right-baseline", EIS_WHITE);
    obj._text(root, "CABIN RATE FPM", 8, y + 34, 13, "left-baseline", EIS_CYAN);
    obj._cabinRate = obj._text(root, "", 146, y + 34, 16, "right-baseline", EIS_WHITE);
    obj._text(root, "DIFF PSI", 8, y + 54, 13, "left-baseline", EIS_CYAN);
    obj._diff = obj._text(root, "", 146, y + 54, 16, "right-baseline", EIS_WHITE);

    obj._fuelMax = nil;
    obj._fuelStart = nil;
    obj.setMode("ENGINE");
    return obj;
  },

  # ENGINE, SYSTEM or FUEL in the lower part of the strip
  setMode : func(mode) {
    me._mode = mode;
    foreach (var m; keys(me._low))
      me._low[m].setVisible(m == mode);
  },

  # a line of the SYSTEM / FUEL pages: cyan label, one value (right) or the L and R values
  _row : func(parent, label, y, dual = 0) {
    me._text(parent, label, 8, y, 13, "left-baseline", EIS_CYAN);
    if (dual)
      return [me._text(parent, "", 108, y, 16, "right-baseline", EIS_WHITE),
              me._text(parent, "", 146, y, 16, "right-baseline", EIS_WHITE)];
    return me._text(parent, "", 146, y, 16, "right-baseline", EIS_WHITE);
  },

  _separator : func(parent, y) {
    parent.createChild("path").moveTo(4, y).horizTo(146).setColor(EIS_GREY).setStrokeLineWidth(1);
  },

  # SYSTEM page: electrical, bleed air and ice protection, pressurization (rows of 18 px: 14 rows above the softkeys)
  _drawSystem : func(p, y) {
    var s = {};
    me._separator(p, y - 4);
    me._text(p, "L", 108, y + 10, 11, "right-baseline", EIS_GREY);
    me._text(p, "R", 146, y + 10, 11, "right-baseline", EIS_GREY);
    y += 8;
    s.volts     = me._row(p, "DC VOLTS", y += 18);
    s.battAmps  = me._row(p, "BATT AMPS", y += 18);
    s.battChg   = me._row(p, "BATT CHG %", y += 18);
    s.genLoad   = me._row(p, "GEN LOAD %", y += 18, 1);
    s.acVolts   = me._row(p, "INV AC V", y += 18);
    me._separator(p, y + 7);
    y += 6;
    s.bleed     = me._row(p, "BLEED AIR", y += 18, 1);
    s.vanes     = me._row(p, "ICE VANES", y += 18, 1);
    s.wshld     = me._row(p, "W/S HEAT", y += 18, 1);
    s.boots     = me._row(p, "SURF DEICE", y += 18);
    s.propAmps  = me._row(p, "PROP DEICE A", y += 18);
    me._separator(p, y + 7);
    y += 6;
    s.cabinAlt  = me._row(p, "CABIN ALT FT", y += 18);
    s.cabinRate = me._row(p, "CAB RATE FPM", y += 18);
    s.diff      = me._row(p, "DIFF PSI", y += 18);
    s.cabinSel  = me._row(p, "CAB SEL FT", y += 18);
    me._sys = s;
  },

  # FUEL page: each tank, fuel flow, endurance and range, crossfeed
  _drawFuel : func(p, y) {
    var f = {};
    me._separator(p, y - 4);
    me._text(p, "L", 108, y + 10, 11, "right-baseline", EIS_GREY);
    me._text(p, "R", 146, y + 10, 11, "right-baseline", EIS_GREY);
    y += 8;
    f.main      = me._row(p, "MAIN LBS", y += 19, 1);
    f.aux       = me._row(p, "AUX LBS", y += 19, 1);
    f.side      = me._row(p, "SIDE LBS", y += 19, 1);
    f.total     = me._row(p, "TOTAL LBS", y += 19);
    me._separator(p, y + 7);
    y += 6;
    f.ff        = me._row(p, "FF PPH", y += 19, 1);
    f.ffTotal   = me._row(p, "FF TOTAL PPH", y += 19);
    f.endurance = me._row(p, "ENDURANCE", y += 19);
    f.range     = me._row(p, "RANGE NM", y += 19);
    f.used      = me._row(p, "USED LBS", y += 19);
    me._separator(p, y + 7);
    y += 6;
    f.crossfeed = me._row(p, "CROSSFEED", y += 19);
    me._fuelPage = f;
  },

  _onOff : func(v) { v ? "ON" : "OFF"; },

  _text : func(parent, text, x, y, size, align, colour) {
    return parent.createChild("text")
      .setFont(EIS_FONT)
      .setFontSize(size, 1.0)
      .setAlignment(align)
      .setTranslation(x, y)
      .setColor(colour)
      .setText(text);
  },

  _band : func(parent, g, from, to, colour, y) {
    var x1 = EIS_X0 + EIS_W * (math.clamp(from, g.min, g.max) - g.min) / (g.max - g.min);
    var x2 = EIS_X0 + EIS_W * (math.clamp(to, g.min, g.max) - g.min) / (g.max - g.min);
    parent.createChild("path").rect(x1, y, math.max(x2 - x1, 1), 6).setColorFill(colour).setColor(colour);
  },

  # One gauge block at y: title and values, scale, L pointer above (points down) and R below (points up)
  _drawGauge : func(root, g, y) {
    var gauge = { def: g, y: y };
    me._text(root, g.title, 75, y + 13, 13, "center-baseline", EIS_CYAN);
    gauge.valueL = me._text(root, "", 44, y + 14, 16, "right-baseline", EIS_WHITE);
    gauge.valueR = me._text(root, "", 146, y + 14, 16, "right-baseline", EIS_WHITE);

    root.createChild("path").rect(EIS_X0, y + 28, EIS_W, 6).setColorFill(0.2, 0.2, 0.2).setColor(EIS_GREY);
    gauge.bands = root.createChild("group");     # under the pointers
    foreach (var b; g.bands) me._band(gauge.bands, g, b[0], b[1], b[2], y + 28);

    gauge.ptrL = root.createChild("group");
    gauge.ptrL.createChild("path")
      .moveTo(-6, -13).lineTo(6, -13).lineTo(6, -5).lineTo(0, 0).lineTo(-6, -5).close()
      .setColorFill(EIS_WHITE).setColor(0, 0, 0);
    me._text(gauge.ptrL, "L", 0, -5, 11, "center-baseline", [0, 0, 0]);

    gauge.ptrR = root.createChild("group");
    gauge.ptrR.createChild("path")
      .moveTo(-6, 13).lineTo(6, 13).lineTo(6, 5).lineTo(0, 0).lineTo(-6, 5).close()
      .setColorFill(EIS_WHITE).setColor(0, 0, 0);
    me._text(gauge.ptrR, "R", 0, 12, 11, "center-baseline", [0, 0, 0]);

    me._setPointers(gauge, 0, 0);
    return gauge;
  },

  _setPointers : func(gauge, vl, vr) {
    var g = gauge.def;
    var xl = EIS_X0 + EIS_W * (math.clamp(vl, g.min, g.max) - g.min) / (g.max - g.min);
    var xr = EIS_X0 + EIS_W * (math.clamp(vr, g.min, g.max) - g.min) / (g.max - g.min);
    gauge.ptrL.setTranslation(xl, gauge.y + 27);
    gauge.ptrR.setTranslation(xr, gauge.y + 35);
  },

  _setGauge : func(gauge, vl, vr) {
    var g = gauge.def;
    me._setPointers(gauge, vl, vr);
    # colour from the displayed (rounded) value: a propeller governed at 1700.2 rpm reads 1700, not red
    var tl = sprintf(g.fmt, vl);
    var tr = sprintf(g.fmt, vr);
    gauge.valueL.setText(tl).setColor(eis_zone_colour(g, num(tl)));
    gauge.valueR.setText(tr).setColor(eis_zone_colour(g, num(tr)));
  },

  updateEngineData : func(data) {
    forindex (var i; EIS_GAUGES) {
      var key = EIS_GAUGES[i].key;
      me._setGauge(me._gauges[i], data.Engines[0][key], data.Engines[1][key]);
    }

    # fuel scale: side capacity, 0-265 lb no-takeoff range
    var cap = math.max(data.FuelCapLbs[0], data.FuelCapLbs[1]);
    if (cap > 0 and me._fuelMax != cap) {
      me._fuelMax = cap;
      me._fuel.def.max = cap;
      me._fuel.def.bands = [[0, 265, EIS_YELLOW], [265, cap, EIS_GREEN]];
      me._fuel.bands.removeAllChildren();
      foreach (var b; me._fuel.def.bands) me._band(me._fuel.bands, me._fuel.def, b[0], b[1], b[2], me._fuel.y + 28);
    }
    me._setGauge(me._fuel, data.FuelLbs[0], data.FuelLbs[1]);
    me._fuelTotalValue.setText(sprintf("%.0f", data.FuelLbs[0] + data.FuelLbs[1]));

    me._volts.setText(sprintf("%.1f", data.Volts));
    me._amps.setText(sprintf("%+.0f", data.Amps));
    me._loadL.setText(sprintf("%.0f", data.GenLoad[0] * 100));
    me._loadR.setText(sprintf("%.0f", data.GenLoad[1] * 100));
    me._propAmps.setText(sprintf("%.0f", data.PropAmps));

    # cabin altitude: white, amber above 10000 ft (CABIN ALTITUDE), red above 12000 ft (CABIN ALT HI);
    # differential: green 0-6.6 psi (approved range), red above
    var ca = data.CabinAlt;
    me._cabinAlt.setText(sprintf("%.0f", math.round(ca, 50)))
      .setColor(ca > 12000 ? EIS_RED : (ca > 10000 ? EIS_YELLOW : EIS_WHITE));
    me._cabinRate.setText(sprintf("%+.0f", math.round(data.CabinRate, 50)));
    me._diff.setText(sprintf("%.1f", data.DiffPsi)).setColor(data.DiffPsi > 6.6 ? EIS_RED : EIS_WHITE);

    if (me._mode == "SYSTEM") me._updateSystem(data);
    elsif (me._mode == "FUEL") me._updateFuel(data);
  },

  _updateSystem : func(data) {
    var s = me._sys;
    s.volts.setText(sprintf("%.1f", data.Volts)).setColor(data.Volts < 24 ? EIS_YELLOW : EIS_WHITE);
    s.battAmps.setText(sprintf("%+.0f", data.BattAmps));
    s.battChg.setText(sprintf("%.0f", data.BattCharge * 100)).setColor(data.BattCharge < 0.5 ? EIS_YELLOW : EIS_WHITE);
    forindex (var i; [0, 1]) {
      s.genLoad[i].setText(data.GenLoad[i] > 0 ? sprintf("%.0f", data.GenLoad[i] * 100) : "OFF")
        .setColor(data.GenLoad[i] > 0 ? EIS_WHITE : EIS_YELLOW);
      s.bleed[i].setText(me._onOff(data.BleedAir[i])).setColor(data.BleedAir[i] ? EIS_WHITE : EIS_YELLOW);
      # inertial separator vanes: RET(racted), EXT(ended), or moving
      var v = data.IceVanes[i];
      s.vanes[i].setText(v > 0.98 ? "EXT" : (v < 0.02 ? "RET" : "TRAN")).setColor(v < 0.02 ? EIS_WHITE : EIS_CYAN);
      s.wshld[i].setText(me._onOff(data.WshldHeat[i]));
    }
    s.acVolts.setText(sprintf("%.0f", data.AcVolts)).setColor(data.AcVolts < 100 ? EIS_YELLOW : EIS_WHITE);
    s.boots.setText(data.WingBoots ? "WING" : (data.TailBoots ? "TAIL" : "OFF"))
      .setColor(data.WingBoots or data.TailBoots ? EIS_CYAN : EIS_WHITE);
    s.propAmps.setText(sprintf("%.0f", data.PropAmps));
    var ca = data.CabinAlt;
    s.cabinAlt.setText(sprintf("%.0f", math.round(ca, 50)))
      .setColor(ca > 12000 ? EIS_RED : (ca > 10000 ? EIS_YELLOW : EIS_WHITE));
    s.cabinRate.setText(sprintf("%+.0f", math.round(data.CabinRate, 50)));
    s.diff.setText(sprintf("%.1f", data.DiffPsi)).setColor(data.DiffPsi > 6.6 ? EIS_RED : EIS_WHITE);
    s.cabinSel.setText(sprintf("%.0f", math.round(data.CabinSel, 50)));
  },

  _updateFuel : func(data) {
    var f = me._fuelPage;
    # tanks 0/1: left aux/main, 2/3: right main/aux
    var main = [data.TankLbs[1], data.TankLbs[2]];
    var aux = [data.TankLbs[0], data.TankLbs[3]];
    var ff = [data.Engines[0].FF, data.Engines[1].FF];
    forindex (var i; [0, 1]) {
      f.main[i].setText(sprintf("%.0f", main[i]));
      f.aux[i].setText(sprintf("%.0f", aux[i]));
      # 265 lb a side: no take-off range of the fuel gauges
      f.side[i].setText(sprintf("%.0f", data.FuelLbs[i])).setColor(data.FuelLbs[i] < 265 ? EIS_YELLOW : EIS_WHITE);
      f.ff[i].setText(sprintf("%.0f", ff[i]));
    }
    var total = data.FuelLbs[0] + data.FuelLbs[1];
    var ffTotal = ff[0] + ff[1];
    f.total.setText(sprintf("%.0f", total));
    f.ffTotal.setText(sprintf("%.0f", ffTotal));
    if (ffTotal > 20) {
      var hours = total / ffTotal;
      f.endurance.setText(sprintf("%d:%02d", int(hours), int(math.mod(hours * 60, 60))));
      f.range.setText(data.GroundSpeed > 30 ? sprintf("%.0f", hours * data.GroundSpeed) : "---");
    } else {
      f.endurance.setText("--:--");
      f.range.setText("---");
    }
    # fuel used since the start of the session (back to 0 after refuelling)
    if (me._fuelStart == nil or total > me._fuelStart) me._fuelStart = total;
    f.used.setText(sprintf("%.0f", me._fuelStart - total));
    var xf = data.Crossfeed;
    f.crossfeed.setText(xf > 0.5 ? "L > R" : (xf < -0.5 ? "R > L" : "OFF")).setColor(xf != 0 ? EIS_CYAN : EIS_WHITE);
  },

  # Menu tree. engineMenu is referenced from most pages as softkey 0:
  # pg.addMenuItem(0, "ENGINE", pg, pg.mfd.EIS.engineMenu);
  # ENGINE, SYSTEM and FUEL choose the lower part of the strip; the selected one is highlighted.
  # Menu callbacks are called without an object (no "me").
  _menu : func(device, pg, active) {
    pg.clearMenu();
    pg.resetMenuColors();
    pg.addMenuItem(0, "ENGINE", pg, pg.mfd.EIS.engineMenu);
    pg.addMenuItem(1, "SYSTEM", pg, pg.mfd.EIS.systemMenu);
    pg.addMenuItem(2, "FUEL", pg, pg.mfd.EIS.fuelMenu);
    pg.addMenuItem(8, "BACK", pg, pg.topMenu);
    device.updateMenus();
    device.svg.getElementById("SoftKey" ~ active ~ "-bg").setColorFill(0.7, 0.7, 0.7);
    device.svg.getElementById("SoftKey" ~ active).setColor(0.0, 0.0, 0.0);
  },

  engineMenu : func(device, pg, menuitem) {
    pg.mfd.EIS.setMode("ENGINE");
    KingAirEIS._menu(device, pg, 0);
  },

  systemMenu : func(device, pg, menuitem) {
    pg.mfd.EIS.setMode("SYSTEM");
    KingAirEIS._menu(device, pg, 1);
  },

  fuelMenu : func(device, pg, menuitem) {
    pg.mfd.EIS.setMode("FUEL");
    KingAirEIS._menu(device, pg, 2);
  },

  offdisplay : func() {
    me._group.setVisible(0);

    # Reset the menu colours (as the FGData EIS does)
    for(var i = 0; i < 12; i +=1) {
      var name = sprintf("SoftKey%d",i);
      me.device.svg.getElementById(name ~ "-bg").setColorFill(0.0,0.0,0.0);
      me.device.svg.getElementById(name).setColor(1.0,1.0,1.0);
    }
    me.getController().offdisplay();
  },
  ondisplay : func() {
    me._group.setVisible(1);
    me.getController().ondisplay();
  },
};

var KingAirEISController =
{
  new : func (page, svg)
  {
    return { parents : [ KingAirEISController ], _recipient : nil, _page : page, transmitter : nil };
  },

  RegisterWithEmesary : func(transmitter = nil) {
    if (transmitter == nil)
      transmitter = emesary.GlobalTransmitter;

    if (me._recipient == nil) {
      me._recipient = emesary.Recipient.new("KingAirEISController_" ~ me._page.device.designation);
      var page = me._page;
      me._recipient.Receive = func(notification)
      {
        if (notification.NotificationType == notifications.PFDEventNotification.DefaultType and
            notification.Event_Id == notifications.PFDEventNotification.EngineData and
            notification.EventParameter.Id == "KingAirEngineData")
        {
          page.updateEngineData(notification.EventParameter.Value);
          return emesary.Transmitter.ReceiptStatus_OK;
        }
        return emesary.Transmitter.ReceiptStatus_NotProcessed;
      };
    }
    transmitter.Register(me._recipient);
    me.transmitter = transmitter;
  },

  DeRegisterWithEmesary : func(transmitter = nil) {
    if (me.transmitter != nil)
      me.transmitter.DeRegister(me._recipient);
    me.transmitter = nil;
  },

  ondisplay : func() { me.RegisterWithEmesary(); },
  offdisplay : func() { me.DeRegisterWithEmesary(); },
};
