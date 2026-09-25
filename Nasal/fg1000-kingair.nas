#############################################################################
# King Air 350 - FG1000 (Garmin G1000 NXi retrofit) integration.
#
# Follows the reference integration of the FGData c182t: the FG1000 Nasal is loaded from
# $FG_ROOT/Aircraft/Instruments-3d/FG1000 into the "fg1000" namespace, with a King Air specific
# interface controller (turboprop engine data instead of the piston EIS publisher).
#
# The displays are the GDU-1044B bezel models placed by Models/KingAir-G1000.xml.
# Power: /systems/electrical/outputs/fg1000-pfd and fg1000-mfd (Nasal/electrical.nas, avionics bus).
#
# License: GPL v2 or later
#############################################################################

var fg_root = getprop("/sim/fg-root");
var nasal_dir = fg_root ~ "/Aircraft/Instruments-3d/FG1000/Nasal/";
var aircraft_dir = getprop("/sim/aircraft-dir");
var available = (io.stat(nasal_dir ~ "FG1000.nas") != nil);

var fg1000system = nil;

var init = func {
    if (!available) {
        gui.popupTip("FG1000 not found in this FlightGear installation ($FG_ROOT/Aircraft/Instruments-3d/FG1000): G1000 displays disabled", 10);
        print("KingAir-350ER G1000: FG1000 not found in " ~ nasal_dir);
        return;
    }
    setprop("/sim/model/g1000/enabled", 1);

    io.load_nasal(nasal_dir ~ "FG1000.nas", "fg1000");
    # King Air interface controller (replaces Interfaces/GenericInterfaceController.nas)
    io.load_nasal(aircraft_dir ~ "/Nasal/fg1000-kingair-interfaces.nas", "fg1000");

    var interfaceController = fg1000.KingAirInterfaceController.getOrCreateInstance();
    interfaceController.start();

    fg1000system = fg1000.FG1000.getOrCreateInstance();
    fg1000system.addPFD(1);
    fg1000system.addMFD(2);
    fg1000system.display(1);
    fg1000system.display(2);

    # displays follow the avionics bus
    setlistener("/systems/electrical/outputs/fg1000-pfd", func(n) {
        if ((n.getValue() or 0) > 15) fg1000system.show(1); else fg1000system.hide(1);
    }, 1, 0);
    setlistener("/systems/electrical/outputs/fg1000-mfd", func(n) {
        if ((n.getValue() or 0) > 15) fg1000system.show(2); else fg1000system.hide(2);
    }, 1, 0);

    print("KingAir-350ER G1000: FG1000 PFD/MFD initialised");
};

# pop-up windows (menu)
var gui_pfd = func { if (fg1000system != nil) fg1000system.displayGUI(1, 0.66); };
var gui_mfd = func { if (fg1000system != nil) fg1000system.displayGUI(2, 0.66); };

setlistener("/sim/signals/fdm-initialized", func { settimer(init, 2.0); }, 0, 0);
