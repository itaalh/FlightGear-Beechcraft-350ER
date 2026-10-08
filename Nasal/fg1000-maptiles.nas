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
# Placeholders, in any order: {z} {x} {y}, {tms_y} (or {-y}) for TMS numbering (y counted from the south), {s}
# (subdomain a, b or c), {q} (or {quadkey}, Bing numbering), {bbox} (or {bbox-epsg-3857}: tile bounds in EPSG:3857
# metres, for a WMS server), and the WMTS names {TileMatrix} {TileCol} {TileRow}.
# The URL needs no file extension: FlightGear picks the image decoder from the name of the cached file, so the
# format of the server (PNG or JPEG) is read from the first bytes of a test tile (Test, Apply, and at start-up) and
# the tiles are cached with the matching extension.
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
                    "folder": "", "max-zoom": 18, "status": "", "format": "", "format-url": "",
                    "name": "", "selected": ""};
    foreach (var k; keys(defaults)) {
        var n = P.getNode(k, 1);
        var v = n.getValue();
        if (v == nil or (v == "" and defaults[k] != ""))
            n.setValue(defaults[k]);
    }
    # format: image format detected for the server URL format-url (png or jpg)
    # servers/server[]: saved servers {name, url, max-zoom}
    aircraft.data.add(P.getNode("source"), P.getNode("url"), P.getNode("folder"), P.getNode("max-zoom"),
                      P.getNode("format"), P.getNode("format-url"), P.getNode("name"), P.getNode("selected"),
                      P.getNode("servers", 1));
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

# placeholders: other names accepted for them, then the value of each one for a tile {z, x, y, tms_y}
var ALIASES = {"-y": "tms_y", "zoom": "z", "TileMatrix": "z", "TileCol": "x", "TileRow": "y", "quadkey": "q",
               "bbox-epsg-3857": "bbox"};
var MERCATOR = 20037508.342789244;      # half the extent of the EPSG:3857 square, metres
var FIELDS = {
    "z": func(p) { return p.z; },
    "x": func(p) { return p.x; },
    "y": func(p) { return p.y; },
    "tms_y": func(p) { return p.tms_y; },
    "s": func(p) { return chr(`a` + math.mod(p.x + p.y, 3)); },
    "q": func(p) {
        var q = "";
        for (var i = p.z; i > 0; i -= 1) {
            var m = math.pow(2, i - 1);
            q ~= math.mod(math.floor(p.x / m), 2) + 2 * math.mod(math.floor(p.y / m), 2);
        }
        return q;
    },
    "bbox": func(p) {
        var t = 2 * MERCATOR / math.pow(2, p.z);
        var x0 = -MERCATOR + p.x * t; var y1 = MERCATOR - p.y * t;
        return sprintf("%.6f,%.6f,%.6f,%.6f", x0, y1 - t, x0 + t, y1);
    },
};

# Checks a URL or path template; returns it normalised (placeholder aliases replaced, forward slashes), or nil
var check_template = func(t) {
    if (t == nil) return nil;
    t = string.trim(t);
    t = string.replace(t, "\\", "/");
    foreach (var a; keys(ALIASES))
        t = string.replace(t, "{" ~ a ~ "}", "{" ~ ALIASES[a] ~ "}");
    if (t == "" or find('"', t) >= 0) return nil;
    # only known placeholders, enough to locate a tile
    var used = {};
    var rest = t;
    while (1) {
        var a = find("{", rest); var b = find("}", rest);
        if (a < 0 and b < 0) break;
        if (a < 0 or b < a) return nil;
        var name = substr(rest, a + 1, b - a - 1);
        if (!contains(FIELDS, name)) return nil;
        used[name] = 1;
        rest = substr(rest, b + 1);
    }
    if (contains(used, "q") or contains(used, "bbox")) return t;
    if (contains(used, "z") and contains(used, "x") and (contains(used, "y") or contains(used, "tms_y"))) return t;
    return nil;
};

# function tile {z, x, y, tms_y} -> URL or path, for a template checked by check_template()
var compile_template = func(t) {
    var parts = [];          # literal text, and [placeholder] vectors
    while (1) {
        var a = find("{", t);
        if (a < 0) { append(parts, t); break; }
        var b = find("}", t);
        append(parts, substr(t, 0, a), [substr(t, a + 1, b - a - 1)]);
        t = substr(t, b + 1);
    }
    return func(pos) {
        var s = "";
        foreach (var p; parts)
            s ~= (typeof(p) == "vector") ? FIELDS[p[0]](pos) : p;
        return s;
    };
};

# cache folder name of a tile server: host, port and path before the first placeholder, and a checksum of the
# whole URL (two layers of the same server get different folders)
var cache_name = func(url) {
    var s = url;
    foreach (var pre; ["http://", "https://"])
        if (string.imatch(s, pre ~ "*")) s = substr(s, size(pre));
    var i = find("{", s);
    if (i > 0) s = substr(s, 0, i);
    var out = "";
    for (var k = 0; k < size(s) and size(out) < 60; k += 1) {
        var c = chr(s[k]);
        out ~= (string.isalnum(s[k]) or c == "." or c == "-") ? c : "_";
    }
    while (size(out) and out[size(out) - 1] == `_`) out = substr(out, 0, size(out) - 1);
    var h = 0;
    for (var k = 0; k < size(url); k += 1) h = math.mod(h * 31 + url[k], 16777216);
    return sprintf("tiles-%s-%06x", out, h);
};

# extension of the cached tiles: the format detected for this URL, else guessed from the URL
var extension = func(url) {
    if (P.getNode("format-url", 1).getValue() == url) {
        var f = P.getNode("format", 1).getValue();
        if (f == "png" or f == "jpg") return "." ~ f;
    }
    var u = string.lc(url);
    return (find("jpg", u) >= 0 or find("jpeg", u) >= 0) ? ".jpg" : ".png";
};

# image format of a downloaded file, from its first bytes: png, jpg, webp, gif, or the start of the text the server
# sent instead of an image (an error page, a WMS exception...)
var FORMAT_NAMES = {"png": "PNG", "jpg": "JPEG"};
var image_format = func(path) {
    var f = io.open(path, "rb");
    var buf = bits.buf(256);
    var n = io.read(f, buf, 256);
    io.close(f);
    var s = substr(buf, 0, n);
    if (size(s) < 4) return "an empty answer";
    if (s[0] == 0x89 and substr(s, 1, 3) == "PNG") return "png";
    if (s[0] == 0xFF and s[1] == 0xD8) return "jpg";
    if (substr(s, 0, 4) == "RIFF" and size(s) >= 12 and substr(s, 8, 4) == "WEBP") return "webp";
    if (substr(s, 0, 4) == "GIF8") return "gif";
    var text = "";
    for (var k = 0; k < size(s) and size(text) < 80; k += 1)
        text ~= (s[k] >= 32 and s[k] < 127) ? chr(s[k]) : " ";
    return "text: " ~ string.trim(text);
};

# extension of the tiles of a plain folder (zoom/x/y.ext), from the first tile found in it
var folder_extension = func(f) {
    var d = f;
    for (var level = 0; level < 2; level += 1) {        # first zoom folder, then its first x folder
        var sub = nil;
        foreach (var n; directory(d) or [])
            if (num(n) != nil) { sub = n; break; }
        if (sub == nil) return ".png";
        d ~= "/" ~ sub;
    }
    foreach (var n; directory(d) or []) {
        var i = find(".", n);
        if (i > 0 and num(substr(n, 0, i)) != nil) return string.lc(substr(n, i));
    }
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
    if (find("{", f) < 0) {                      # plain folder: standard {z}/{x}/{y} layout, .png or .jpg
        while (size(f) and f[size(f) - 1] == `/`) f = substr(f, 0, size(f) - 1);
        if (!readable(f)) return "";
        f ~= "/{z}/{x}/{y}" ~ folder_extension(f);
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
            layer.makeURL = compile_template(url);
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
            var path = compile_template(tpl);
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

var URL_HELP = "URL: use {z} {x} {y} (or {-y} for TMS), or {q}, or {bbox} (WMS)";
var UNSUPPORTED = {"webp": "WebP", "gif": "GIF"};
# network errors (curl codes) explained: FlightGear does not use the Windows proxy settings
var NET_ERRORS = {
    "5": "proxy name not found: check the --proxy option",
    "6": "server name not found: no DNS for FlightGear here, or a proxy is needed (launcher option --proxy=host:port)",
    "7": "server unreachable: wrong port, firewall, or a proxy is needed (launcher option --proxy=host:port)",
    "28": "server too slow to answer (time-out)",
    "35": "HTTPS handshake failed: try http:// instead of https://",
    "60": "HTTPS certificate not trusted by FlightGear (internal certificate authority): try http://",
};

# applies the settings to the maps already displayed
var reload = func {
    foreach (var l; layers) {
        configure(l);
        l.last_tile = [-1, -1];                  # reload every tile
        l.update();
    }
};

# Downloads a tile of the server at the aircraft position (zoom shown by the MFD map, then coarser zooms if the
# server has none there) and reads its format: the tiles are then cached with the matching extension
var probe = func(url) {
    var z0 = size(layers) ? layers[0].zoom : 10;
    var zooms = [];
    foreach (var z; [z0, z0 - 3, z0 - 6, 1])
        if (z >= 1 and (!size(zooms) or z < zooms[-1])) append(zooms, z);
    var make = compile_template(url);
    var path = getprop("/sim/fg-home") ~ "/cache/maps/" ~ cache_name(url) ~ "/probe.tile";
    var attempt = func(i) {
        var pos = tile_at(zooms[i]);
        var u = make(pos);
        var tile = pos.z ~ "/" ~ pos.x ~ "/" ~ pos.y;
        status("requesting " ~ u ~ " ...");
        http.save(u, path)
            .done(func {
                var fmt = image_format(path);
                if (contains(FORMAT_NAMES, fmt)) {
                    var known = P.getNode("format-url", 1).getValue() == url and P.getNode("format", 1).getValue() == fmt;
                    P.getNode("format", 1).setValue(fmt);
                    P.getNode("format-url", 1).setValue(url);
                    if (!known) { reload(); aircraft.data.save(); }
                    status("OK: tile " ~ tile ~ " received from the server (" ~ FORMAT_NAMES[fmt] ~ ")");
                } elsif (contains(UNSUPPORTED, fmt)) {
                    status("the server sends " ~ UNSUPPORTED[fmt] ~ " tiles, which FlightGear cannot display: set it to PNG or JPEG");
                } else {
                    status("the server sends no image for tile " ~ tile ~ " (" ~ fmt ~ ")");
                }
            })
            .fail(func(r) {
                if (r.status == 404 and i + 1 < size(zooms)) return attempt(i + 1);
                if (r.status == 404)
                    status("the server answers, but has no tile here (zoom " ~ zooms[-1] ~ " to " ~ zooms[0] ~ ")");
                elsif (contains(NET_ERRORS, "" ~ r.status))
                    status(NET_ERRORS["" ~ r.status] ~ " (" ~ u ~ ")");
                else
                    status("no answer from " ~ u ~ " (" ~ r.status ~ " " ~ r.reason ~ ")");
            });
    };
    attempt(0);
};

# dialog: apply the settings to the maps already displayed
var apply = func {
    var src = source();
    reload();
    aircraft.data.save();
    if (src == "server") {
        var url = check_template(P.getNode("url", 1).getValue());
        if (url == nil) return status(URL_HELP ~ ": " ~ (P.getNode("url", 1).getValue() or ""));
        status("tiles from " ~ url);
        probe(url);
    } elsif (src == "folder") {
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
        if (url == nil) return status(URL_HELP ~ ": " ~ (P.getNode("url", 1).getValue() or ""));
        probe(url);
    } elsif (src == "folder") {
        var tpl = folder_template();
        if (tpl == nil) return status("folder: give a folder, or a template with {z} {x} {y}");
        if (tpl == "") return status(not_readable_msg());
        var path = compile_template(tpl);
        var found = [];
        for (var z = 1; z <= 18; z += 1)
            if (io.stat(path(tile_at(z))) != nil) append(found, z);
        if (size(found)) status("tiles found here for zoom " ~ string.join(" ", found));
        else status("no tile for this position in " ~ tpl);
    } else {
        status("OpenStreetMap needs internet access (cache: $FG_HOME/cache/maps/osm-cache)");
    }
};

# dialog: Paste buttons (the dialog input fields do not take Ctrl+V); first line of the clipboard, trimmed
var paste = func(field) {
    var t = clipboard.getText(clipboard.CLIPBOARD) or "";
    foreach (var eol; ["\r", "\n"]) {
        var i = find(eol, t);
        if (i >= 0) t = substr(t, 0, i);
    }
    t = string.trim(t);
    if (t == "") return status("the clipboard holds no text");
    P.getNode(field, 1).setValue(t);
    status("pasted, press Test or Apply");
};

# saved servers: names listed by the dialog combo (never empty: PUI needs at least one entry)
var SAVED = props.globals.getNode("/sim/gui/dialogs/g1000-maptiles/saved", 1);
var NONE = "(no saved server)";

var find_server = func(name) {
    foreach (var n; P.getNode("servers", 1).getChildren("server"))
        if (n.getValue("name") == name) return n;
    return nil;
};

var refresh_saved = func {
    SAVED.removeChildren("value");
    var list = P.getNode("servers", 1).getChildren("server");
    if (!size(list)) SAVED.getNode("value[0]", 1).setValue(NONE);
    forindex (var i; list)
        SAVED.getNode("value[" ~ i ~ "]", 1).setValue(list[i].getValue("name"));
    gui.dialog_update("g1000-maptiles", "saved");
};

# dialog Save: stores the URL and max zoom under the name (replaces a server of the same name)
var save_server = func {
    var name = string.trim(P.getValue("name") or "");
    if (name == "" or name == NONE) return status("give the server a name, then Save");
    var url = check_template(P.getValue("url"));
    if (url == nil) return status(URL_HELP ~ ": " ~ (P.getValue("url") or ""));
    var n = find_server(name);
    var known = n != nil;
    if (!known) n = P.getNode("servers", 1).addChild("server");
    n.setValues({"name": name, "url": url, "max-zoom": P.getValue("max-zoom") or 18});
    P.setValue("name", name);
    P.setValue("selected", name);
    refresh_saved();
    aircraft.data.save();
    status((known ? "updated: " : "saved: ") ~ name);
};

# dialog Delete: removes the server chosen in the list
var delete_server = func {
    var name = P.getValue("selected") or "";
    var n = find_server(name);
    if (n == nil) return status("choose a saved server in the list, then Delete");
    n.remove();
    P.setValue("selected", "");
    refresh_saved();
    aircraft.data.save();
    status("deleted: " ~ name);
};

# dialog: a saved server chosen in the list is used at once
var select_server = func {
    var n = find_server(P.getValue("selected") or "");
    if (n == nil) return;
    P.setValue("name", n.getValue("name"));
    P.setValue("url", n.getValue("url"));
    P.setValue("max-zoom", n.getValue("max-zoom") or 18);
    P.setValue("source", SOURCES[1]);
    apply();
};

var dialog = nil;
var open_dialog = func {
    if (dialog == nil)
        dialog = gui.Dialog.new("/sim/gui/dialogs/g1000-maptiles/dialog",
                                "Aircraft/KingAir-350/Dialogs/g1000-maptiles-dlg.xml");
    refresh_saved();
    dialog.open();
};

init_props();
refresh_saved();
# before Nasal/fg1000-kingair.nas creates the displays (2 s after the FDM initialisation)
setlistener("/sim/signals/fdm-initialized", func {
    install();
    # format of the server not read yet for this URL
    if (source() == "server") {
        var url = check_template(P.getNode("url", 1).getValue());
        if (url != nil and P.getNode("format-url", 1).getValue() != url) probe(url);
    }
}, 0, 0);
