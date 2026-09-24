"""Cycles preview renders of the axe (used by build_axe.py --render)."""
import math
import os

import bpy
from mathutils import Euler, Vector

KEY, RIM, FILL = 28.0, 30.0, 4.0     # area light power (W) - scene is small


def _world(strength=0.25):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexGradient")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], sky.inputs["Vector"])
    nt.links.new(sky.outputs["Fac"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.022, 1)
    ramp.color_ramp.elements[1].color = (0.55, 0.58, 0.62, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def _area(name, loc, target, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.shape = "RECTANGLE"
    d.size, d.size_y = size
    d.energy = energy
    d.color = color
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def _slate_material():
    m = bpy.data.materials.new("Slate")
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 3.0
    n1.inputs["Detail"].default_value = 12
    n1.inputs["Roughness"].default_value = 0.62
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 60.0
    n2.inputs["Detail"].default_value = 8
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 2.2
    for n in (n1, n2, vor):
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.018, 0.019, 0.021, 1)
    ramp.color_ramp.elements[1].color = (0.075, 0.072, 0.068, 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.45
    rr.inputs["To Max"].default_value = 0.85
    nt.links.new(n2.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    crack = nt.nodes.new("ShaderNodeMapRange")
    crack.inputs["From Min"].default_value = 0.0
    crack.inputs["From Max"].default_value = 0.02
    nt.links.new(vor.outputs["Distance"], crack.inputs["Value"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    add.inputs[1].default_value = 0.3
    nt.links.new(n2.outputs["Fac"], add.inputs[0])
    nt.links.new(crack.outputs["Result"], add.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(add.outputs["Value"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def _camera(loc, target, lens, focus_obj=None, fstop=4.0):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if focus_obj is not None:
        cd.dof.use_dof = True
        cd.dof.focus_object = focus_obj
        cd.dof.aperture_fstop = fstop
    bpy.context.scene.camera = cam
    return cam


def _setup_render(res, samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = int(os.environ.get("AXE_PCT", 100))
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92


def _clear_extras(keep):
    for o in list(bpy.data.objects):
        if o is not keep:
            bpy.data.objects.remove(o, do_unlink=True)


def render(axe, root, samples=160):
    out_dir = os.path.join(root, "previews")
    os.makedirs(out_dir, exist_ok=True)

    # ---------- shot 1: lying on a slate slab, runes up, shallow depth of field
    _clear_extras(axe)
    _setup_render((1600, 1000), samples)
    _world(0.08)
    axe.rotation_euler = Euler((math.radians(90), 0, math.radians(-28)), "XYZ")
    bpy.context.view_layer.update()
    zmin = min((axe.matrix_world @ Vector(c)).z for c in axe.bound_box)
    axe.location.z -= zmin
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.data.materials.append(_slate_material())
    M = axe.matrix_world
    head = M @ Vector((0.07, 0.0, 0.53))
    focus = bpy.data.objects.new("Focus", None)
    bpy.context.scene.collection.objects.link(focus)
    focus.location = head
    mid = M @ Vector((0.04, 0, 0.26))
    hdir = (M.to_3x3() @ Vector((0, 0, 1))).normalized()      # along the haft
    bdir = (M.to_3x3() @ Vector((1, 0, 0))).normalized()      # towards the edge
    cam_loc = mid - 0.66 * bdir - 0.12 * hdir + Vector((0, 0, 0.85))
    _camera(cam_loc, mid - 0.03 * hdir, 42, focus, 5.6)
    _area("Key", tuple(mid + Vector((-0.7, -0.5, 1.1))), tuple(mid), (1.0, 0.7), KEY, (1.0, 0.94, 0.86))
    _area("Rim", tuple(mid + 0.9 * bdir + Vector((0, 0, 0.35))), tuple(mid), (0.4, 1.4), RIM, (0.8, 0.88, 1.0))
    _area("Fill", tuple(mid - 1.2 * bdir + Vector((0, 0, 0.25))), tuple(mid), (1.0, 0.4), FILL)
    bpy.context.scene.render.filepath = os.path.join(out_dir, "axe_hero.jpg")
    bpy.ops.render.render(write_still=True)

    # ---------- shot 2: close-up of the head and the silver-inlaid runes
    cam = bpy.context.scene.camera
    head_c = M @ Vector((0.08, 0.0, 0.51))
    cam.location = head_c - 0.13 * bdir + 0.06 * hdir + Vector((0, 0, 0.30))
    cam.rotation_euler = (head_c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 70
    cam.data.dof.aperture_fstop = 8
    focus.location = head_c
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1400, 1000
    bpy.context.scene.render.filepath = os.path.join(out_dir, "axe_closeup.jpg")
    bpy.ops.render.render(write_still=True)

    # ---------- shot 3: studio side view, standing
    _clear_extras(axe)
    axe.location = (0, 0, 0)
    axe.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    _world(0.30)
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 900, 1400
    c = Vector((0.05, 0, 0.225))
    _camera(c + Vector((0.12, -1.45, 0.05)), c, 60)
    _area("Key", (-0.9, -1.0, 1.0), c, (1.0, 1.0), KEY * 1.4, (1.0, 0.96, 0.9))
    _area("Rim", (0.8, 0.9, 0.8), c, (0.4, 1.4), RIM * 1.4, (0.85, 0.9, 1.0))
    _area("Top", (0.0, -0.2, 1.4), c, (0.6, 0.6), 8)
    bpy.context.scene.render.filepath = os.path.join(out_dir, "axe_studio.jpg")
    bpy.ops.render.render(write_still=True)
