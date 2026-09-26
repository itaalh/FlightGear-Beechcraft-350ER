#############################################################################
# King Air 350 - FG1000: source of the moving map background tiles.
#
# The FG1000 maps (MFD navigation map TOPO, PFD inset map) draw OpenStreetMap tiles through the FGData
# "OSM" tile layer ($FG_ROOT/Nasal/canvas/map/OSM.lcontroller): each tile is looked for in
# $FG_HOME/cache/maps/osm-cache/{z}/{x}/{y}.png and downloaded from tile.openstreetmap.org when missing.
# This module lets the aircraft use instead, without internet access:
# - "Local server": any XYZ (slippy map) tile server, e.g. http://localhost:8090/{z}/{x}/{y}.png; the tiles are
#   cached in $FG_HOME/cache/maps/<server name>/,
# - "Local folder": a folder of tiles laid out as {z}/{x}/{y}.png, read directly (nothing is downloaded; missing
#   tiles are left blank). FlightGear only lets Nasal read under FG_HOME, FG_ROOT, the aircraft and scenery
#   folders and the download folder, and FlightGear 2024.1 crashes on a refused read, even inside call(): the
#   folder is checked against those roots before any access (folders added with --allow-nasal-read are not
#   visible from Nasal; for tiles elsewhere, serve them with a local server).
# Placeholders: {z} {x} {y}, and {tms_y} (or {-y}) for TMS numbering (y counted from the south).
# Settings: King Air 350 > G1000: map tiles (Dialogs/g1000-maptiles-dlg.xml), kept in
# $FG_HOME/aircraft-data/ between sessions.
#
# License: GPL v2 or later
#############################################################################

var P = props.globals.getNode("/sim/model/g1000/map", 1);
var OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
var SOURCES = ["OpenStreetMap", "Local server", "Local folder"];
var BLANK = getprop("/sim/aircraft-dir") ~ "/Models/Instruments/FG1000/no-tile.png";

var layers = [];          # tile layers of the FG1000 maps, reconfigured when the settings change

var init_props = func {
    var defaults = {"source": SOURCES[0], "url": "http://localhost:8090/{z}/{x}/{y}.png",
                    "folder": "", "max-zoom": 18, "status": ""};
    foreach (var k; keys(defaults)) {
        var n = P.getNode(k, 1);
        var v = n.getValue();
        if (v == nil or (v == "" and defaults[k] != ""))
            n.setValue(defaults[k]);
    }
    aircraft.data.add(P.getNode("source"), P.getNode("url"), P.getNode("folder"), P.getNode("max-zoom"));
};

# folders FlightGear lets Nasal read (see above)
var readable_roots = func {
    var roots = [];
    var add = func(v) {
        if (v == nil or v == "") return;
        var windows = (size(v) > 1 and chr(v[1]) == ":") or find(";", v) >= 0;
        foreach (var r; split(windows ? ";" : ":", v)) {
            r = string.trim(string.replace(r, "\\", "/"));
            while (size(r) > 1 and r[size(r) - 1] == `/`) r = substr(r, 0, size(r) - 1);
            if (r != "") append(roots, r);
        }
    };
    foreach (var prop; ["/sim/fg-home", "/sim/fg-root", "/sim/fg-aircraft", "/sim/aircraft-dir", "/sim/fg-scenery",
                        "/sim/terrasync/scenery-dir", "/sim/paths/download-dir"])
        add(getprop(prop));
    return roots;
};

# 1 if FlightGear lets Nasal read the path (Windows paths compared without case)
var readable = func(path) {
    if (find("/../", path ~ "/") >= 0 or find("/./", path ~ "/") >= 0) return 0;
    var windows = size(path) > 1 and chr(path[1]) == ":";
    var p = windows ? string.lc(path) : path;
    foreach (var r; readable_roots()) {
        var rr = windows ? string.lc(r) : r;
        if (p == rr or substr(p, 0, size(rr) + 1) == rr ~ "/") return 1;
    }
    return 0;
};

var status = func(msg) {
    P.getNode("status", 1).setValue(msg);
    print("KingAir-350ER G1000 map: " ~ msg);
};

# Checks a URL or path template; returns it normalised ({-y} -> {tms_y}, forward slashes), or nil
var check_template = func(t) {
    if (t == nil) return nil;
    t = string.trim(t);
    t = string.replace(t, "\\", "/");
    t = string.replace(t, "{-y}", "{tms_y}");
    if (t == "" or find('"', t) >= 0) return nil;
    # only {z} {x} {y} {tms_y}, and all three coordinates
    var rest = t;
    foreach (var ph; ["{z}", "{x}", "{y}", "{tms_y}"])
        rest = string.replace(rest, ph, "");
    if (find("{", rest) >= 0 or find("}", rest) >= 0) return nil;
    if (find("{z}", t) < 0 or find("{x}", t) < 0 or (find("{y}", t) < 0 and find("{tms_y}", t) < 0)) return nil;
    return t;
};

# cache folder name of a tile server: host, port and path without the placeholders
var cache_name = func(url) {
    var s = url;
    foreach (var pre; ["http://", "https://"])
        if (string.imatch(s, pre ~ "*")) s = substr(s, size(pre));
    var i = find("{", s);
    if (i > 0) s = substr(s, 0, i);
    var out = "";
    for (var k = 0; k < size(s); k += 1) {
        var c = chr(s[k]);
        out ~= (string.isalnum(s[k]) or c == "." or c == "-") ? c : "_";
    }
    while (size(out) and out[size(out) - 1] == `_`) out = substr(out, 0, size(out) - 1);
    return "tiles-" ~ out;
};

var extension = func(url) {
    var u = string.lc(url);
    foreach (var e; [".jpg", ".jpeg"])
        if (find(e, u) >= 0) return ".jpg";
    return ".png";
};

var source = func {
    var s = P.getNode("source", 1).getValue();
    return (s == SOURCES[1]) ? "server" : ((s == SOURCES[2]) ? "folder" : "osm");
};

var folder_template = func {
    var f = P.getNode("folder", 1).getValue() or "";
    f = string.trim(string.replace(f, "\\", "/"));
    if (f == "") return nil;
    if (find("{z}", f) < 0) {                    # plain folder: standard {z}/{x}/{y}.png layout
        while (size(f) and f[size(f) - 1] == `/`) f = substr(f, 0, size(f) - 1);
        f ~= "/{z}/{x}/{y}.png";
    }
    f = check_template(f);
    if (f == nil) return nil;
    # the fixed part of the template (before the first placeholder) must be readable
    var fixed = substr(f, 0, find("{", f));
    while (size(fixed) > 1 and fixed[size(fixed) - 1] == `/`) fixed = substr(fixed, 0, size(fixed) - 1);
    return readable(fixed) ? f : "";
};

var configure = func(layer) {
    var src = source();
    layer.max_zoom = math.min(18, math.max(1, int(P.getNode("max-zoom", 1).getValue() or 18)));
    if (src == "server") {
        var url = check_template(P.getNode("url", 1).getValue());
        if (url == nil) {
            status("invalid server URL, back to OpenStreetMap");
            src = "osm";
        } else {
            layer.makeURL = string.compileTemplate(url);
            layer.makePath = string.compileTemplate(layer.maps_base ~ "/" ~ cache_name(url) ~ "/{z}/{x}/{y}" ~ extension(url));
            return;
        }
    }
    if (src == "folder") {
        var tpl = folder_template();
        if (tpl == nil) {
            status("invalid tile folder, back to OpenStreetMap");
        } elsif (tpl == "") {
            status(not_readable_msg());
        } else {
            var path = string.compileTemplate(tpl);
            # always an existing file, so the layer never downloads anything
            layer.makePath = func(pos) { var p = path(pos); return (io.stat(p) != nil) ? p : BLANK; };
            layer.makeURL = func(pos) { return ""; };
            return;
        }
    }
    layer.makeURL = string.compileTemplate(OSM_URL);
    layer.makePath = string.compileTemplate(layer.maps_base ~ "/osm-cache/{z}/{x}/{y}.png");
};

# hook into the FGData OSM layer controller: every tile layer created afterwards gets the configured source
var install = func {
    var reg = canvas.OverlayLayer.Controller.registry;
    if (!contains(reg, "OSM")) {
        status("OSM tile layer not found, map tiles unchanged");
        return;
    }
    var ctl = reg["OSM"];
    if (contains(ctl, "kingair_new")) return;
    ctl.kingair_new = ctl.new;
    ctl.new = func(layer) {
        var m = ctl.kingair_new(layer);
        append(layers, layer);
        configure(layer);
        return m;
    };
};

var not_readable_msg = func {
    return "FlightGear cannot read this folder: put it under " ~ getprop("/sim/fg-home") ~
           " or a scenery folder, or use Local server (back to OpenStreetMap)";
};

# tile coordinates of the aircraft position
var tile_at = func(z) {
    var lat = getprop("/position/latitude-deg"); var lon = getprop("/position/longitude-deg");
    var n = math.pow(2, z);
    var x = math.floor(n * (lon + 180) / 360);
    var y = math.floor((1 - math.ln(math.tan(lat * D2R) + 1 / math.cos(lat * D2R)) / math.pi) / 2 * n);
    return {z: z, x: x, y: y, tms_y: n - y - 1, type: "map"};
};

# dialog: apply the settings to the maps already displayed
var apply = func {
    var src = source();
    foreach (var l; layers) {
        configure(l);
        l.last_tile = [-1, -1];                  # reload every tile
        l.update();
    }
    aircraft.data.save();
    if (src == "server") status("tiles from " ~ (check_template(P.getNode("url", 1).getValue()) or "?"));
    elsif (src == "folder") {
        var tpl = folder_template();
        if (tpl != nil and tpl != "") status("tiles from " ~ tpl);
    }
    else status("tiles from OpenStreetMap (internet)");
};

# dialog: test the source at the aircraft position
var test = func {
    var src = source();
    if (src == "server") {
        var url = check_template(P.getNode("url", 1).getValue());
        if (url == nil) return status("URL: use {z} {x} {y} (or {tms_y})");
        var pos = tile_at(size(layers) ? layers[0].zoom : 10);   # zoom currently shown by the MFD map
        var u = string.compileTemplate(url)(pos);
        var p = getprop("/sim/fg-home") ~ "/cache/maps/" ~ cache_name(url) ~ "/test" ~ extension(url);
        var tile = pos.z ~ "/" ~ pos.x ~ "/" ~ pos.y;
        status("requesting " ~ u ~ " ...");
        http.save(u, p)
            .done(func { status("OK: tile " ~ tile ~ " received from the server"); })
            .fail(func(r) {
                if (r.status == 404)
                    status("the server answers, but has no tile " ~ tile ~ " (zoom " ~ pos.z ~ " or area not available)");
                else
                    status("no answer from " ~ u ~ " (" ~ r.status ~ " " ~ r.reason ~ ")");
            });
    } elsif (src == "folder") {
        var tpl = folder_template();
        if (tpl == nil) return status("folder: give a folder, or a template with {z} {x} {y}");
        if (tpl == "") return status(not_readable_msg());
        var path = string.compileTemplate(tpl);
        var found = [];
        for (var z = 1; z <= 18; z += 1)
            if (io.stat(path(tile_at(z))) != nil) append(found, z);
        if (size(found)) status("tiles found here for zoom " ~ string.join(" ", found));
        else status("no tile for this position in " ~ tpl);
    } else {
        status("OpenStreetMap needs internet access (cache: $FG_HOME/cache/maps/osm-cache)");
    }
};

var dialog = nil;
var open_dialog = func {
    if (dialog == nil)
        dialog = gui.Dialog.new("/sim/gui/dialogs/g1000-maptiles/dialog",
                                "Aircraft/KingAir-350/Dialogs/g1000-maptiles-dlg.xml");
    dialog.open();
};

init_props();
# before Nasal/fg1000-kingair.nas creates the displays (2 s after the FDM initialisation)
setlistener("/sim/signals/fdm-initialized", func { install(); }, 0, 0);
