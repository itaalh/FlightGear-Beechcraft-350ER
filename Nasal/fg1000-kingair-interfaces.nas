# King Air 350 interface controller for the FG1000 (loaded into the "fg1000" namespace).
# Derived from the FGData GenericInterfaceController (Stuart Buchanan, GPL v2+): same interface list,
# but the piston GenericEISPublisher is replaced by a turboprop publisher fed from the King Air engines.

var nasal_dir = getprop("/sim/fg-root") ~ "/Aircraft/Instruments-3d/FG1000/Nasal/";
io.load_nasal(nasal_dir ~ 'Interfaces/PropertyPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/PropertyUpdater.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/NavDataInterface.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericNavComPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericNavComUpdater.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericFMSPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericFMSUpdater.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericADCPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericFuelInterface.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GenericFuelPublisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GFC700Interface.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GFC700Publisher.nas', "fg1000");
io.load_nasal(nasal_dir ~ 'Interfaces/GMA1347Interface.nas', "fg1000");

# ---------------------------------------------------------------------------
# Turboprop EIS publisher: the FG1000 EIS strip was designed for a single piston engine, so the
# King Air values are mapped onto its fields (engine 1 shown; the analogue gauges in the panel
# still show both engines):
#   RPM            propeller rpm            MAN (in Hg)   torque %          FuelFlow (gph) engine 1
#   Oil press/temp engine 1                 EGT (norm)    ITT / 1000        CHT (deg F)    ITT in deg F
# ---------------------------------------------------------------------------
var GenericEISPublisher =
{
  new : func (period=0.25) {
    var obj = {
      parents : [
        GenericEISPublisher,
        PeriodicPropertyPublisher.new(notifications.PFDEventNotification.EngineData, period)
      ],
    };
    obj.addPropMap("RPM", "/engines/engine[0]/rpm");
    obj.addPropMap("Man", "/engines/engine[0]/torque-pct");
    obj.addPropMap("MBusVolts", "/systems/electrical/volts");
    obj.addPropMap("EBusVolts", "/systems/electrical/volts");
    obj.addPropMap("MBattAmps", "/systems/electrical/amps");
    obj.addPropMap("SBattAmps", "/systems/electrical/amps");
    obj.addPropMap("EngineHours", "/sim/time/hobbs/engine");
    obj.addPropMap("FuelFlowGPH", "/engines/engine[0]/fuel-flow-gph");
    obj.addPropMap("OilPressurePSI", "/engines/engine[0]/oil-pressure-psi");
    obj.addPropMap("OilTemperatureF", "/engines/engine[0]/oil-temperature-degf");
    obj.addPropMap("EGTNorm", "/engines/engine[0]/itt-norm");
    obj.addPropMap("CHTDegF", "/engines/engine[0]/itt_degf");
    obj.addPropMap("VacuumSuctionInHG", "/systems/electrical/gyro-suction-inhg");
    return obj;
  },

  publish : func() {
    var engineData0 = {};
    foreach (var propmap; me._propmaps) {
      engineData0[propmap.getName()] = propmap.getValue();
    }
    var engineData = [];
    append(engineData, engineData0);
    var notification = notifications.PFDEventNotification.new(
      "MFD", 1, notifications.PFDEventNotification.EngineData,
      { Id: "EngineData", Value: engineData } );
    me._transmitter.NotifyAll(notification);
  },
};

var KingAirInterfaceController = {

  _instance : nil,

  INTERFACE_LIST : [
    "NavDataInterface",
    "GenericEISPublisher",
    "GenericNavComPublisher",
    "GenericNavComUpdater",
    "GenericFMSPublisher",
    "GenericFMSUpdater",
    "GenericADCPublisher",
    "GenericFuelInterface",
    "GenericFuelPublisher",
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
