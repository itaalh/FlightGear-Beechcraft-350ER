#############################################################################
# King Air 350ER G1000 - mouse on the moving maps of the FG1000 displays (MFD navigation map, PFD inset map):
# - wheel over the map: range (wheel up: zoom in),
# - click on the orientation box (top right of the map): NORTH UP / HDG UP,
# - click and drag: pan the map; double click: map centred on the aircraft again.
# The FGData FG1000 map (NavMap.nas) only writes the orientation label (setOrientation is a TODO) and cannot be
# panned: every map gets here its own source for the "Aircraft position" map controller, whose position is the
# aircraft position plus the pan offset and whose heading is 0 (north up) or the true heading (heading up). The
# aircraft symbol (layer APS) is given the aircraft position as model, instead of the map centre.
# The events come from the canvas of each display: on the Pro Line Fusion screens the canvas placements capture
# the mouse ("capture-events", Nasal/fg1000-kingair.nas).
#
# License: GPL v2 or later
#############################################################################

var ORIENT_NORTH = 0;            # fg1000.ORIENTATIONS: NORTH UP
var ORIENT_HDG = 3;              #                      HDG UP
var INHIBIT = {1: "pfd1", 2: "mfd", 3: "pfd2"};   # touch inhibit of the Fusion screens (fusion-cockpit.nas)
var DOUBLE_CLICK = 0.4;          # s

var system = nil;                # fg1000.FG1000
var maps = [];                   # NavMaps set up here
var count = 0;

# the aircraft symbol stays on the aircraft, wherever the map centre is (MapStructure getpos: geo.Coord model)
var AIRCRAFT = geo.Coord.new();
AIRCRAFT.latlon = func { return geo.aircraft_position().latlon(); };

# per map: pan offset (metres north and east of the aircraft) and orientation, and its position source
var setup = func(m) {
    if (contains(m, "_ka_source")) return;
    count += 1;
    m._ka_source = "kingair-map-" ~ count;
    m._ka_north = 0;
    m._ka_east = 0;
    m._ka_orient = ORIENT_NORTH;
    canvas.Map.Controller.get("Aircraft position").SOURCES[m._ka_source] = {
        getPosition: func {
            var pos = geo.aircraft_position();
            if (m._ka_north != 0 or m._ka_east != 0)
                pos.apply_course_distance(math.atan2(m._ka_east, m._ka_north) * R2D,
                                          math.sqrt(m._ka_north * m._ka_north + m._ka_east * m._ka_east));
            return subvec(pos.latlon(), 0, 2);
        },
        getAltitude: func { return getprop("/position/altitude-ft"); },
        getHeading: func {
            return (m._ka_orient == ORIENT_HDG) ? (getprop("/orientation/heading-deg") or 0) : 0;
        },
    };
    append(maps, m);
};

# hook into fg1000.NavMap: the map element is created each time the map is shown (lazy loading)
var patch = func {
    var NM = fg1000.NavMap;
    if (contains(NM, "_ka_create")) return;
    NM._ka_create = NM.createMapElement;
    NM._ka_orientation = NM.setOrientation;
    NM.createMapElement = func {
        if (me._map != nil or me._static) return call(NM._ka_create, [], me);
        setup(me);
        var orient = me._ka_orient;
        call(NM._ka_create, [], me);                     # also sets the orientation back to NORTH UP
        me._map.setController("Aircraft position", me._ka_source);
        # aircraft symbol on the aircraft: NavMap gives the layer options as "options:", which Map.addLayer
        # (argument "opts") ignores, so the APS model is set here
        var aps = me._map.getLayer("APS");
        if (aps != nil) {
            aps.controller._model = AIRCRAFT;
            aps.symbol.model = AIRCRAFT;
        }
        me.setOrientation(orient);
    };
    NM.setOrientation = func(orientation) {
        me._ka_orient = orientation;
        call(NM._ka_orientation, [orientation], me);
    };
};

# map area in canvas pixels [x0, y0, x1, y1]
var area = func(m) {
    var c = m._center;
    if (m._clip != "") {                                 # "rect(top, right, bottom, left)", px from the centre
        var v = [];
        foreach (var s; split(",", substr(m._clip, 5, size(m._clip) - 6)))
            append(v, num(string.trim(string.replace(s, "px", ""))) or 0);
        return [c[0] + v[3], c[1] + v[0], c[0] + v[1], c[1] + v[2]];
    }
    return [150, 56, 2 * c[0] - 150, 743];              # MFD: right of the EIS, between header and footer
};

# map of the display under the canvas point, or nil
var map_at = func(display, x, y) {
    foreach (var m; maps) {
        if (m._page.mfd != display or m._map == nil or !m._map.getVisible() or !m._group.getVisible()) continue;
        var a = area(m);
        if (x >= a[0] and x <= a[2] and y >= a[1] and y <= a[3]) return m;
    }
    return nil;
};

# orientation box of the FG1000 SVG, top right corner of the map [x, y, w, h] (MFD map or PFD inset)
var orientation_box = func(m) {
    var a = area(m);
    return (m._clip != "") ? [a[2] - 81.2, a[1] + 0.7, 79.9, 22.0] : [a[2] - 71.9, a[1] - 0.5, 74.3, 20.0];
};

# RECENTER box, just under it, shown while the map is panned
var recenter_box = func(m) {
    var b = orientation_box(m);
    return [b[0], b[1] + b[3] + 3, b[2], b[3]];
};

var inside = func(b, x, y) { return x >= b[0] and x <= b[0] + b[2] and y >= b[1] and y <= b[1] + b[3]; };
var on_orientation = func(m, x, y) { return inside(orientation_box(m), x, y); };
var on_recenter = func(m, x, y) { return panned(m) and inside(recenter_box(m), x, y); };
var panned = func(m) { return m._ka_north != 0 or m._ka_east != 0; };

# drawn in the group of the orientation label (the page group is under the map), in the SVG coordinates of that
# group: MFD legend (moved as a whole beside the Nearest pages) or PFD inset
var draw_recenter = func(m) {
    if (!contains(m, "_ka_button")) {
        var b = (m._clip != "") ? [146.8, 492.7 + 25, 79.9, 22.0] : [952.1, 55.5 + 23, 74.3, 20.0];
        var g = m._orientationDisplay.getParent().createChild("group", "kingair-recenter");
        g.createChild("path").rect(b[0], b[1], b[2], b[3])
            .setColorFill(m._clip != "" ? [0, 0, 0] : [0.1, 0.19, 0.19]).setColor(1, 1, 1).setStrokeLineWidth(1);
        g.createChild("text").setText("RECENTER").setFont("LiberationFonts/LiberationSansNarrow-Regular.ttf")
            .setFontSize(15).setColor(1, 1, 1).setAlignment("center-center")
            .setTranslation(b[0] + b[2] / 2, b[1] + b[3] / 2 + 1);
        m._ka_button = g;
    }
    m._ka_button.setVisible(panned(m));
};

var refresh = func(m) {
    draw_recenter(m);
    var ctrl = m._map.getController();
    if (ctrl != nil) call(func ctrl.update_pos(), [], nil, nil, var err = []);
};

# drag of (dx, dy) canvas pixels: the map follows the mouse
var pan = func(m, dx, dy) {
    var mpp = (m._map.getRange() or 10) * 1852 / (m._map.getScreenRange() or 344.5);   # metres per pixel
    var h = (m._map.getHdg() or 0) * D2R;
    m._ka_north += mpp * (dx * math.sin(h) + dy * math.cos(h));
    m._ka_east += mpp * (dy * math.sin(h) - dx * math.cos(h));
    refresh(m);
};

var recentre = func(m) {
    m._ka_north = 0;
    m._ka_east = 0;
    refresh(m);
};

var listen = func(index) {
    var display = system.getDisplay(index);
    var drag = nil;                                      # {map, moved} from mousedown to the click
    var last_click = -1;
    var inhibited = func { return getprop("/controls/fusion/inhibit-" ~ INHIBIT[index]) == 1; };
    var cv = display.getCanvas();

    cv.addEventListener("wheel", func(e) {
        if (inhibited()) return;
        var m = map_at(display, e.clientX, e.clientY);
        if (m == nil) return;
        if (e.deltaY > 0) { m.zoomIn(); } elsif (e.deltaY < 0) { m.zoomOut(); }
    });
    cv.addEventListener("mousedown", func(e) {
        drag = nil;
        if (inhibited()) return;
        var m = map_at(display, e.clientX, e.clientY);
        if (m != nil and !on_orientation(m, e.clientX, e.clientY) and !on_recenter(m, e.clientX, e.clientY))
            drag = {map: m, moved: 0};
    });
    cv.addEventListener("drag", func(e) {
        if (drag == nil or drag.map._map == nil) return;
        if (math.abs(e.deltaX) > 300 or math.abs(e.deltaY) > 300) return;   # pointer left the screen
        drag.moved += math.abs(e.deltaX) + math.abs(e.deltaY);
        pan(drag.map, e.deltaX, e.deltaY);
    });
    cv.addEventListener("click", func(e) {
        var moved = (drag != nil) ? drag.moved : 0;
        drag = nil;
        if (inhibited() or moved > 4) return;
        var m = map_at(display, e.clientX, e.clientY);
        if (m == nil) return;
        if (on_orientation(m, e.clientX, e.clientY)) {
            m.setOrientation((m._ka_orient == ORIENT_HDG) ? ORIENT_NORTH : ORIENT_HDG);
            refresh(m);
            return;
        }
        if (on_recenter(m, e.clientX, e.clientY)) return recentre(m);
        var t = systime();
        if (t - last_click < DOUBLE_CLICK) { recentre(m); t = -1; }
        last_click = t;
    });
};

# called by Nasal/fg1000-kingair.nas: patch() before the displays are created (a map may be created with its
# page), init() once they are
var init = func(fg1000system) {
    system = fg1000system;
    patch();
    foreach (var i; [1, 2, 3]) listen(i);
};
