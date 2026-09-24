"""Assemble a 12 x 8 m Viking hall from the built viking_hall kit pieces and render it.

    python3 -m forge.demo_hall          # needs library/viking_hall/*.glb

Writes library/viking_hall/_demo_hall.glb (instanced pieces) and
_demo_exterior.jpg / _demo_cutaway.jpg.
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bpy  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

KIT = os.path.join(ROOT, "library", "viking_hall")
pi = math.pi
MASTERS = {}
PLACED = []


def load(name):
    if name not in MASTERS:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(KIT, name + ".glb"))
        new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
        ob = new[0]
        ob.parent = None
        ob.matrix_world = __import__("mathutils").Matrix.Identity(4)
        ob.hide_render = ob.hide_viewport = True
        MASTERS[name] = ob
    return MASTERS[name]


def put(name, loc, rz=0.0, group="hall"):
    m = load(name)
    o = m.copy()
    o.name = f"{name}_{len(PLACED)}"
    bpy.context.scene.collection.objects.link(o)
    o.hide_render = o.hide_viewport = False
    o.location = loc
    o.rotation_mode = "XYZ"          # glTF import leaves QUATERNION mode, which ignores rotation_euler
    o.rotation_euler = Euler((0, 0, rz))
    o["group"] = group
    PLACED.append(o)
    return o


def build(length=6):
    Lx = 2.0 * length
    for i in range(length):
        x = 2.0 * i
        put("foundation_2m", (x, -4, 0))
        put("foundation_2m", (x, 4, 0))
        put("wall_plank_door_2m" if i == 2 else "wall_plank_2m", (x, -4, 0.5), group="front")
        put("wall_wattle_2m" if i in (1, 4) else "wall_plank_2m", (x, 4, 0.5))
        put("rafter_pair_8m", (x + (0.12 if i == 0 else 0.0), 0, 3.0))
        put("roof_thatch_2m", (x, 0, 3.0), group="roof_front")
        put("roof_thatch_2m", (x + 2, 0, 3.0), rz=pi, group="roof_back")
        put("roof_ridge_2m", (x, 0, 3.0), group="roof_back")
        for y in (-2, 2):
            put("beam_2m", (x, y, 4.5), group="roof_back")
        for j in range(4):
            put("floor_earth_2x2", (x, -4 + 2 * j, 0.5))
    put("rafter_pair_8m", (Lx - 0.12, 0, 3.0))
    for xe in (0.0, Lx):
        for j in range(4):
            put("foundation_2m", (xe, -4 + 2 * j, 0), rz=pi / 2)
            put("wall_plank_2m", (xe, -4 + 2 * j, 0.5), rz=pi / 2, group="end" if xe else "end0")
        put("gable_wall_8m", (xe, 0, 3.0), group="end" if xe else "end0")
        put("gable_finial", (xe + (0.1 if xe else -0.1), 0, 3.0), group="roof_back")
    for (x, y) in ((0, -4), (0, 4), (Lx, -4), (Lx, 4)):
        put("foundation_corner", (x, y, 0))
        put("post_corner", (x, y, 0.5))
    for x in (2.0, 6.0, 10.0):
        put("tie_beam_8m", (x, 0, 3.0), group="roof_back")
        for y in (-2, 2):
            put("post_hall", (x, y, 0.5))
    # interior
    put("hearth_long", (Lx / 2, 0, 0.5))
    for i in (1, 2, 3, 4):
        put("bench_2m", (2.0 * i, 3.87, 0.5))
    for i in (0, 3, 4):
        put("bench_2m", (2.0 * i + 2, -3.87, 0.5), rz=pi)
    put("door_plank", (4.57, -4.0, 0.72), rz=math.radians(75), group="front")
    put("hay_sheaf", (10.8, 3.0, 0.95), rz=0.4)
    put("hay_sheaf", (11.2, 2.6, 0.95), rz=1.2)
    # yard
    put("hay_pile", (Lx + 2.2, -2.0, 0.0), group="yard")
    put("hay_sheaf", (Lx + 1.2, 1.0, 0.0), group="yard")
    put("plank_stack", (7.0, -6.6, 0.0), rz=0.05, group="yard")
    put("log_pile", (-1.2, 2.5, 0.0), rz=pi / 2, group="yard")
    put("log_pile", (-1.2, 1.7, 0.0), rz=pi / 2 + 0.1, group="yard")
    put("stones_loose", (2.5, -6.2, 0.0), group="yard")
    put("stones_loose", (Lx + 1.0, 3.5, 0.0), rz=2.0, group="yard")


def environment():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    w = bpy.data.worlds.new("sky")
    sc.world = w
    nt = w.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = "MULTIPLE_SCATTERING"
    except TypeError:
        sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(24)
    sky.sun_rotation = math.radians(215)
    nt.links.new(sky.outputs[0], nt.nodes["Background"].inputs[0])
    nt.nodes["Background"].inputs[1].default_value = 0.18
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 1.6
    sun.angle = math.radians(1.5)
    so = bpy.data.objects.new("sun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = Euler((math.radians(66), 0, math.radians(35)))
    bpy.ops.mesh.primitive_plane_add(size=120, location=(6, 0, 0.0))
    g = bpy.context.active_object
    m = bpy.data.materials.new("ground")
    t = m.node_tree
    b = t.nodes["Principled BSDF"]
    n1 = t.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.8
    n1.inputs["Detail"].default_value = 12
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.03, 0.018, 1)
    ramp.color_ramp.elements[1].color = (0.06, 0.08, 0.03, 1)
    t.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    t.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    bump = t.nodes.new("ShaderNodeBump")
    n2 = t.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 40
    t.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    t.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    g.data.materials.append(m)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -0.3
    sc.cycles.use_denoising = True


def shoot(path, loc, target, lens=28, res=(1600, 900), samples=96):
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 90
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build()
    # export the assembled hall (instances share mesh data)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in PLACED:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(KIT, "_demo_hall.glb"), export_format="GLB",
                              use_selection=True, export_image_format="JPEG", export_jpeg_quality=85)
    environment()
    shoot(os.path.join(KIT, "_demo_exterior.jpg"), (-7.5, -15.5, 5.5), (6.5, 0, 2.6))
    for o in PLACED:
        if o["group"] in ("roof_front", "roof_back", "front", "end0"):
            o.hide_render = True
    shoot(os.path.join(KIT, "_demo_cutaway.jpg"), (-2.0, -11.0, 11.5), (6.0, 0.8, 0.8), lens=24)


if __name__ == "__main__":
    main()
