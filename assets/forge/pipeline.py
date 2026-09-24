"""Asset pipeline: build -> join -> bake UV -> bake PBR maps -> GLB -> preview.

Theme modules register builders with @asset(...). A builder creates mesh
objects (with procedural materials from forge.mat) and returns nothing or a
list of objects; every mesh in the scene becomes part of the asset.
"""
import json
import math
import os
import time

import bpy
import numpy as np
from mathutils import Vector

from . import geo as G

REG = {}


def asset(res=1024, view=(35, 18), pose=(0, 0, 0), pivot="bottom", max_tris=60000, smooth=40,
          title=None, kind="prop", lens=55, dist=1.0, floor=True, samples=48):
    """Register a builder. view=(azimuth°, elevation°) of the preview camera;
    pose = extra XYZ rotation (deg) applied for the preview only."""
    def deco(fn):
        REG[fn.__name__] = dict(fn=fn, res=res, view=view, pose=pose, pivot=pivot, max_tris=max_tris,
                                smooth=smooth, title=title or fn.__name__.replace("_", " ").title(),
                                kind=kind, lens=lens, dist=dist, floor=floor, samples=samples,
                                module=fn.__module__)
        return fn
    return deco


# ------------------------------------------------------------------ scene ---
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.unit_settings.system = "METRIC"


def _meshes():
    return [o for o in bpy.context.scene.objects if o.type in ("MESH", "CURVE", "FONT")]


def _tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# -------------------------------------------------------------- assemble ---
def assemble(spec, name):
    objs = _meshes()
    for o in objs:
        G.apply_mods(o)
        if not o.data.materials:
            raise RuntimeError(f"part {o.name} has no material")
        if G.DESIGN not in o.data.uv_layers:
            o.data.uv_layers.new(name=G.DESIGN)
    ob = G.join(objs, name)
    # pivot
    lo, hi = G.bbox(ob)
    if spec["pivot"] == "bottom":
        off = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
    elif spec["pivot"] == "center":
        off = Vector((lo + hi) / 2)
    elif spec["pivot"] == "origin":
        off = Vector((0, 0, 0))
    else:
        off = Vector(spec["pivot"])
    ob.data.transform(__import__("mathutils").Matrix.Translation(-off))
    ob.data.update()
    # budget
    t = _tris(ob)
    if t > spec["max_tris"]:
        m = G.mod(ob, "decimate", ratio=spec["max_tris"] / t, use_collapse_triangulate=True)
        G.apply_mods(ob)
    if spec["smooth"]:
        G.smooth(ob, spec["smooth"])
    return ob


def bake_uv(ob):
    me = ob.data
    uv = me.uv_layers.new(name="bake")
    me.uv_layers.active = uv
    G.activate(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    return uv


# ------------------------------------------------------------------- bake ---
def _principled(mat):
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    raise RuntimeError(f"material {mat.name} has no Principled BSDF")


def _out(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL")


def _src(nt, sock, as_color=True):
    """Return (socket or value) feeding a Principled input."""
    if sock.is_linked:
        return sock.links[0].from_socket
    v = sock.default_value
    return tuple(v) if hasattr(v, "__len__") else v


def _emit_setup(mat, mode, ao_dist):
    nt = mat.node_tree
    b = _principled(mat)
    em = nt.nodes.new("ShaderNodeEmission")
    tmp = [em]
    if mode == "color":
        s = _src(nt, b.inputs["Base Color"])
        if isinstance(s, tuple):
            em.inputs["Color"].default_value = s
        else:
            nt.links.new(s, em.inputs["Color"])
    else:  # ORM packed: R = AO, G = roughness, B = metallic
        comb = nt.nodes.new("ShaderNodeCombineColor")
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.samples = 6
        ao.inputs["Distance"].default_value = ao_dist
        nrm = b.inputs["Normal"]
        if nrm.is_linked:
            nt.links.new(nrm.links[0].from_socket, ao.inputs["Normal"])
        tmp += [comb, ao]
        tex_ao = next((n for n in nt.nodes if n.label == "tex_ao"), None)
        if tex_ao is not None:
            mul = nt.nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            tmp.append(mul)
            nt.links.new(ao.outputs["AO"], mul.inputs[0])
            nt.links.new(tex_ao.outputs["Color"], mul.inputs[1])
            nt.links.new(mul.outputs[0], comb.inputs[0])
        else:
            nt.links.new(ao.outputs["AO"], comb.inputs[0])
        for i, key in ((1, "Roughness"), (2, "Metallic")):
            s = _src(nt, b.inputs[key])
            if isinstance(s, (int, float)):
                comb.inputs[i].default_value = s
            else:
                nt.links.new(s, comb.inputs[i])
        nt.links.new(comb.outputs[0], em.inputs["Color"])
    out = _out(mat)
    orig = out.inputs["Surface"].links[0].from_socket
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return orig, tmp


def _restore(mat, orig, tmp):
    nt = mat.node_tree
    nt.links.new(orig, _out(mat).inputs["Surface"])
    for n in tmp:
        nt.nodes.remove(n)


def bake_maps(ob, res, workdir, ao_dist):
    sc = bpy.context.scene
    sc.render.bake.margin = 12
    sc.render.bake.use_clear = True
    mats = [m for m in ob.data.materials]
    imgs = {}
    for key, cs in (("color", "sRGB"), ("orm", "Non-Color"), ("normal", "Non-Color")):
        im = bpy.data.images.new(f"{ob.name}_{key}", res, res, alpha=False)
        im.colorspace_settings.name = cs
        imgs[key] = im
    targets = {}
    for m in mats:
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        targets[m.name] = n
    G.activate(ob)

    def point(img):
        for m in mats:
            n = targets[m.name]
            n.image = img
            m.node_tree.nodes.active = n

    for mode in ("color", "orm"):
        point(imgs[mode])
        saved = [(m, *_emit_setup(m, mode, ao_dist)) for m in mats]
        sc.cycles.samples = 6
        bpy.ops.object.bake(type="EMIT")
        for m, orig, tmp in saved:
            _restore(m, orig, tmp)
    point(imgs["normal"])
    sc.cycles.samples = 4
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    for m in mats:
        m.node_tree.nodes.remove(targets[m.name])
    paths = {}
    for k, im in imgs.items():
        p = os.path.join(workdir, f"{ob.name}_{k}.png")
        im.filepath_raw = p
        im.file_format = "PNG"
        im.save()
        paths[k] = p
    return imgs


def final_material(name, imgs):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "bake"

    def tex(im):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = im
        nt.links.new(uv.outputs[0], n.inputs["Vector"])
        return n
    c, o, nm = tex(imgs["color"]), tex(imgs["orm"]), tex(imgs["normal"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.uv_map = "bake"
    nt.links.new(c.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(o.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], b.inputs["Metallic"])
    nt.links.new(nm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], b.inputs["Normal"])
    grp = bpy.data.node_groups.get("glTF Material Output")
    if grp is None:
        grp = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        grp.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
        grp.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
        grp.nodes.new("NodeGroupInput")
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = grp
    nt.links.new(sep.outputs["Red"], g.inputs["Occlusion"])
    return mat


def swap_materials(ob, final):
    me = ob.data
    for i, m in enumerate(me.materials):
        if not m.get("nobake"):
            me.materials[i] = final
    # drop duplicate slots pointing at the same material
    activate = G.activate(ob)
    bpy.ops.object.material_slot_remove_unused()


def cleanup_uv(ob):
    me = ob.data
    for nm in [u.name for u in me.uv_layers]:
        if nm != "bake" and not nm.startswith(".") and nm in me.uv_layers:
            me.uv_layers.remove(me.uv_layers[nm])
    me.uv_layers["bake"].name = "UVMap"
    for m in me.materials:
        for n in m.node_tree.nodes:
            if n.type == "UVMAP" and n.uv_map == "bake":
                n.uv_map = "UVMap"
            if n.type == "NORMAL_MAP" and n.uv_map == "bake":
                n.uv_map = "UVMap"


def export(ob, path):
    t = ob.modifiers.new("tri", "TRIANGULATE")
    G.apply_mods(ob)
    G.activate(ob)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True,
                              export_image_format="JPEG", export_jpeg_quality=88, export_apply=True,
                              export_tangents=True, export_yup=True)


# ----------------------------------------------------------------- render ---
def _area(name, loc, target, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.shape = "RECTANGLE"
    d.size, d.size_y = size
    d.energy, d.color = energy, color
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def render_preview(ob, spec, path, res=900):
    sc = bpy.context.scene
    ob.rotation_euler = tuple(math.radians(a) for a in spec["pose"])
    bpy.context.view_layer.update()
    lo, hi = G.bbox(ob)
    ob.location.z -= lo[2]
    ob.location.x -= (lo[0] + hi[0]) / 2
    ob.location.y -= (lo[1] + hi[1]) / 2
    bpy.context.view_layer.update()
    lo, hi = G.bbox(ob)
    c = Vector((lo + hi) / 2)
    R = max(float(np.linalg.norm(hi - lo)) / 2, 0.02)
    # floor + soft gradient world
    if spec["floor"]:
        bpy.ops.mesh.primitive_plane_add(size=R * 60, location=(0, 0, 0))
        fl = bpy.context.active_object
        fm = bpy.data.materials.new("floor")
        bs = fm.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (0.035, 0.032, 0.03, 1)
        bs.inputs["Roughness"].default_value = 0.55
        fl.data.materials.append(fm)
    w = bpy.data.worlds.new("w")
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes["Background"]
    grad = nt.nodes.new("ShaderNodeTexGradient")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.015, 0.015, 0.017, 1)
    ramp.color_ramp.elements[1].color = (0.9, 0.9, 0.92, 1)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.45
    # camera framed on the bounding sphere
    az, el = (math.radians(a) for a in spec["view"])
    lens = spec["lens"]
    fov = 2 * math.atan(18 / lens)
    d = R / math.sin(fov / 2) * 1.08 * spec["dist"]
    dirv = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_start = R * 0.01
    cd.clip_end = R * 400
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    cam.location = c + dirv * d
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    # lights scale with the object so exposure is consistent
    k = 11.0
    kd, rd, fd = d * 1.1, d * 1.2, d * 1.4

    def around(a_deg, e_deg, dist):
        a, e = math.radians(a_deg) + az, math.radians(e_deg)
        return tuple(c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist)
    _area("key", around(-45, 45, kd), c, (R * 1.6, R * 1.2), k * kd * kd, (1.0, 0.95, 0.88))
    _area("rim", around(150, 30, rd), c, (R * 0.8, R * 2.0), k * 1.3 * rd * rd, (0.82, 0.9, 1.0))
    _area("fill", around(60, 10, fd), c, (R * 1.5, R * 0.8), k * 0.25 * fd * fd)
    sc.cycles.samples = spec["samples"]
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 90
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ drive ---
def run(theme, name, outroot, workroot):
    spec = REG[name]
    t0 = time.time()
    outdir = os.path.join(outroot, theme)
    os.makedirs(outdir, exist_ok=True)
    work = os.path.join(workroot, theme, name)
    os.makedirs(work, exist_ok=True)
    os.environ["FORGE_WORK"] = work
    reset()
    spec["fn"]()
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "CPU"
    ob = assemble(spec, name)
    lo, hi = G.bbox(ob)
    size = float(np.linalg.norm(hi - lo))
    if os.environ.get("FORGE_QUICK"):
        qdir = os.path.join("/tmp/forge_quick", theme)
        os.makedirs(qdir, exist_ok=True)
        for o in list(bpy.context.scene.objects):
            if o is not ob:
                bpy.data.objects.remove(o, do_unlink=True)
        zoom = float(os.environ.get("FORGE_ZOOM", "1"))
        spec = dict(spec, samples=16, dist=spec["dist"] / zoom)
        render_preview(ob, spec, os.path.join(qdir, f"{name}.jpg"), res=int(os.environ.get("FORGE_RES", "560")))
        return dict(theme=theme, name=name, title=spec["title"], tris=_tris(ob), glb_kb=0,
                    dims_m=[round(float(x), 3) for x in (hi - lo)])
    if os.environ.get("FORGE_DRY"):
        return dict(theme=theme, name=name, title=spec["title"], tris=_tris(ob), glb_kb=0,
                    dims_m=[round(float(x), 3) for x in (hi - lo)], mats=len(ob.data.materials))
    t1 = time.time()
    bake_uv(ob)
    imgs = bake_maps(ob, spec["res"], work, ao_dist=max(0.01, size * 0.08))
    t2 = time.time()
    final = final_material(f"{name}_mat", imgs)
    swap_materials(ob, final)
    cleanup_uv(ob)
    glb = os.path.join(outdir, f"{name}.glb")
    export(ob, glb)
    tris = _tris(ob)
    dims = [round(float(x), 4) for x in (hi - lo)]
    for o in list(bpy.context.scene.objects):
        if o is not ob:
            bpy.data.objects.remove(o, do_unlink=True)
    t3 = time.time()
    render_preview(ob, spec, os.path.join(outdir, f"{name}.jpg"))
    t4 = time.time()
    meta = dict(theme=theme, name=name, title=spec["title"], kind=spec["kind"], tris=tris, dims_m=dims,
                texture=spec["res"], materials=[m.name for m in ob.data.materials],
                glb_kb=os.path.getsize(glb) // 1024, seconds=round(time.time() - t0, 1),
                t_build=round(t1 - t0), t_bake=round(t2 - t1), t_render=round(t4 - t3))
    with open(os.path.join(outdir, f"{name}.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return meta
