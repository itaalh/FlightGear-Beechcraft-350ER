"""Blender helpers shared by the cockpit scripts (camera at the FlightGear eye points, preview renders)."""

import math
import os
import sys

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# FlightGear view 0 (KingAir-350ER-G1000-set.xml): x-offset-m = model y, y-offset-m = model z, z-offset-m = model x
PILOT_EYE = Vector((-4.00, -0.34, 0.58))
COPILOT_EYE = Vector((-4.00, 0.37, 0.58))


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def look_camera(name, eye, heading_deg=0.0, pitch_deg=0.0, hfov_deg=62.0):
    """Camera at eye looking forward (-x), heading_deg positive to the left as in FlightGear, pitch up positive."""
    cam = bpy.data.cameras.new(name)
    cam.sensor_fit = "HORIZONTAL"
    cam.angle = math.radians(hfov_deg)
    cam.clip_start = 0.01
    cam.clip_end = 100.0
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = eye
    # base orientation: camera -Z along model -x, camera +Y along model +z
    base = Euler((math.radians(90.0), 0.0, math.radians(90.0)), "XYZ")
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = base
    # FlightGear heading offset turns left (towards -y) for positive values, pitch offset up for positive values
    ob.rotation_euler.rotate(Euler((0.0, math.radians(pitch_deg), 0.0), "XYZ"))
    ob.rotation_euler.rotate(Euler((0.0, 0.0, math.radians(heading_deg)), "XYZ"))
    return ob


def render(path, camera, res=(1600, 900), engine="BLENDER_WORKBENCH", samples=16, color="TEXTURE"):
    scn = bpy.context.scene
    scn.camera = camera
    scn.render.engine = engine
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = "PNG"
    if engine == "BLENDER_WORKBENCH":
        sh = scn.display.shading
        sh.light = "STUDIO"
        sh.color_type = color
        sh.show_specular_highlight = True
        sh.show_cavity = False
        scn.display.render_aa = "8"
    else:
        try:
            scn.eevee.taa_render_samples = samples
        except AttributeError:
            pass
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
