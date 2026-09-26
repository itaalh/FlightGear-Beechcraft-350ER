# King Air 350 interface controller for the FG1000 (loaded into the "fg1000" namespace).
# Derived from the FGData GenericInterfaceController (Stuart Buchanan, GPL v2+): same interface list,
# but the piston GenericEISPublisher and the generic fuel publisher/interface are replaced by a twin
# turboprop publisher fed from the King Air engines, tanks and electrical system.

var nasal_dir = getprop("/sim/fg-root") ~ "/Aircraft/Instruments-3d/FG1000/Nasal/";
io.load_nasal(nasal_dir ~ 'Interfaces/PropertyPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/PropertyUpdater.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/NavDataInterface.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericNavComPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericNavComUpdater.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericFMSPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericFMSUpdater.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericADCPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GFC700Interface.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GFC700Publisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GMA1347Interface.nas', "fg1000");

# ---------------------------------------------------------------------------
# Twin turboprop EIS publisher: both engines, fuel per side and DC electrical, sent as one
# "KingAirEngineData" EngineData notification to the King Air EIS (Nasal/fg1000-kingair-eis.nas).
# It also replaces the GenericFuelPublisher/Interface (single tank pair, fuel flow of engine 1 only).
# ---------------------------------------------------------------------------
var KingAirEISPublisher =
{
  new : func (period=0.2) {
    var obj = {
      parents : [
        KingAirEISPublisher,
        PeriodicPropertyPublisher.new(notifications.PFDEventNotification.EngineData, period)
      ],
      _eng : [props.globals.getNode("/engines/engine[0]", 1), props.globals.getNode("/engines/engine[1]", 1)],
      _fuel : props.globals.getNode("/consumables/fuel", 1),
    };
    return obj;
  },

  # tanks 0/1: left aux/main, 2/3: right main/aux (Aero/KingAir-350*.xml)
  _tankLbs : func(t) { me._fuel.getNode("tank[" ~ t ~ "]/level-lbs", 1).getValue() or 0; },
  _tankCapLbs : func(t) {
    var tank = me._fuel.getNode("tank[" ~ t ~ "]", 1);
    (tank.getNode("capacity-gal_us", 1).getValue() or 0) * (tank.getNode("density-ppg", 1).getValue() or 6.7);
  },

  publish : func() {
    var engines = [];
    foreach (var e; me._eng) {
      var pph = e.getNode("fuel-flow_pph", 1).getValue();
      if (pph == nil) pph = (e.getNode("fuel-flow-gph", 1).getValue() or 0) * 6.7;
      append(engines, {
        TRQ  : e.getNode("torque-pct", 1).getValue() or 0,
        ITT  : e.getNode("itt-degc", 1).getValue() or 0,
        PROP : e.getNode("rpm", 1).getValue() or 0,
        N1   : e.getNode("n1", 1).getValue() or 0,
        FF   : pph,
        OILP : e.getNode("oil-pressure-ind-psi", 1).getValue() or 0,
        OILT : ((e.getNode("oil-temperature-ind-degf", 1).getValue() or 32) - 32) / 1.8,
      });
    }
    var data = {
      Engines : engines,
      FuelLbs : [me._tankLbs(0) + me._tankLbs(1), me._tankLbs(2) + me._tankLbs(3)],
      FuelCapLbs : [me._tankCapLbs(0) + me._tankCapLbs(1), me._tankCapLbs(2) + me._tankCapLbs(3)],
      Volts : getprop("/systems/electrical/volts") or 0,
      Amps : getprop("/systems/electrical/amps") or 0,
      GenLoad : [getprop("/systems/electrical/gen-load[0]") or 0, getprop("/systems/electrical/gen-load[1]") or 0],
    };
    var notification = notifications.PFDEventNotification.new(
      "MFD", 1, notifications.PFDEventNotification.EngineData,
      { Id: "KingAirEngineData", Value: data } );
    me._transmitter.NotifyAll(notification);
  },
};

var KingAirInterfaceController = {

  _instance : nil,

  INTERFACE_LIST : [
    "NavDataInterface",
    "KingAirEISPublisher",
    "GenericNavComPublisher",
    "GenericNavComUpdater",
    "GenericFMSPublisher",
    "GenericFMSUpdater",
    "GenericADCPublisher",
    "GFC700Publisher",
    "GFC700Interface",
    "GMA1347Interface",
  ],

  getOrCreateInstance : func() {
    if (KingAirInterfaceController._instance == nil) {
      KingAirInterfaceController._instance = KingAirInterfaceController.new();
    }
    return KingAirInterfaceController._instance;
  },

  new : func() {
    return { parents : [KingAirInterfaceController], running : 0 };
  },

  start : func() {
    if (me.running) return;
    foreach (var interface; KingAirInterfaceController.INTERFACE_LIST) {
      var code = sprintf("me.%sInstance = fg1000.%s.new();", interface, interface);
      var instantiate = compile(code);
      instantiate();
    }
    foreach (var interface; KingAirInterfaceController.INTERFACE_LIST) {
      var code = 'me.' ~ interface ~ 'Instance.start();';
      var start_interface = compile(code);
      start_interface();
    }
    me.running = 1;
  },

  stop : func() {
    if (me.running == 0) return;
    foreach (var interface; KingAirInterfaceController.INTERFACE_LIST) {
      var code = 'me.' ~ interface ~ 'Instance.stop();';
      var stop_interface = compile(code);
      stop_interface();
    }
    me.running = 0;
  },

  restart : func() { me.stop(); me.start(); },
};
