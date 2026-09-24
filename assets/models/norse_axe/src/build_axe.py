"""Builds the Norse bearded axe in Blender (run with the `bpy` module).

    python3 build_axe.py            # build + export GLB/.blend
    python3 build_axe.py --render   # additionally render preview images

Geometry is fully parametric (see axe_shape.py); textures come from
make_textures.py. The exported model uses metres, +Y up (glTF), with the
pivot in the middle of the leather grip so it can be attached to a hand bone.
"""
import math
import os
import sys

import bpy  # noqa: I001  (bpy must be imported before bmesh)
import bmesh
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import axe_shape as S  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, ".."))
TEX = os.path.join(ROOT, "textures")
PIVOT_Z = 0.5 * (S.GRIP_Z0 + S.GRIP_Z1)


# ------------------------------------------------------------- helpers ------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_mesh(name, verts, faces, face_uvs, material):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bverts = [bm.verts.new(v) for v in verts]
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for f, uvs in zip(faces, face_uvs):
        try:
            bf = bm.faces.new([bverts[i] for i in f])
        except ValueError:
            continue  # duplicate / degenerate
        for loop, uv in zip(bf.loops, uvs):
            loop[uv_layer].uv = uv
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(material)
    return ob


def finish(ob, bevel=None, smooth_angle=35.0):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    if bevel:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(40)
        m.use_clamp_overlap = True
        m.harden_normals = False
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))


# ----------------------------------------------------------- materials ------
def gltf_output_group():
    name = "glTF Material Output"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    g = bpy.data.node_groups.new(name, "ShaderNodeTree")
    g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    g.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    g.nodes.new("NodeGroupInput")
    return g


def make_material(name, prefix):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    def img(fname, colorspace):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(TEX, fname))
        n.image.colorspace_settings.name = colorspace
        return n

    base = img(f"{prefix}_basecolor.jpg", "sRGB")
    orm = img(f"{prefix}_orm.jpg", "Non-Color")
    nrm = img(f"{prefix}_normal.jpg", "Non-Color")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(orm.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = gltf_output_group()
    nt.links.new(sep.outputs["Red"], grp.inputs["Occlusion"])
    return mat


# --------------------------------------------------------------- blade ------
def build_blade(mat):
    Nu, Nv = 60, 40
    su = np.linspace(0, 1, Nu + 1)
    us = 1 - (1 - su) ** 1.3
    vs = 0.5 - 0.5 * np.cos(np.pi * np.linspace(0, 1, Nv + 1))
    UU, VV = np.meshgrid(us, vs, indexing="ij")
    X, Z = S.blade_point(UU, VV)
    T = S.blade_half_thickness(UU, VV)

    verts, faces, fuvs = [], [], []
    idx = {}
    for side in (1, -1):
        for i in range(Nu + 1):
            for j in range(Nv + 1):
                idx[side, i, j] = len(verts)
                verts.append((X[i, j], side * T[i, j], Z[i, j]))

    def uv_face(side, i, j):
        return S.blade_uv(X[i, j], Z[i, j], side)

    for side in (1, -1):
        for i in range(Nu):
            for j in range(Nv):
                c = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                faces.append([idx[side, a, b] for a, b in c])
                fuvs.append([uv_face(side, a, b) for a, b in c])

    def strip(ring, v_pos, v_neg):
        n = len(ring) - 1
        for k in range(n):
            (a, b), (c, d) = ring[k], ring[k + 1]
            ua = 0.05 + 0.9 * k / n
            ub = 0.05 + 0.9 * (k + 1) / n
            faces.append([idx[1, a, b], idx[1, c, d], idx[-1, c, d], idx[-1, a, b]])
            fuvs.append([(ua, v_pos), (ub, v_pos), (ub, v_neg), (ua, v_neg)])

    strip([(i, Nv) for i in range(Nu + 1)], 0.400, 0.415)   # top spine
    strip([(i, 0) for i in range(Nu + 1)], 0.420, 0.435)    # beard curve
    strip([(0, j) for j in range(Nv + 1)], 0.440, 0.445)    # hidden in the eye
    strip([(Nu, j) for j in range(Nv + 1)], 0.460, 0.470)   # cutting edge
    ob = make_mesh("Blade", verts, faces, fuvs, mat)
    finish(ob, bevel=0.0009)
    return ob


# ----------------------------------------------------------------- eye ------
def build_eye(mat):
    Nt = 72
    th = np.linspace(0, 2 * np.pi, Nt, endpoint=False)
    c, s = np.cos(th), np.sin(th)
    n = 2.6
    ox = np.sign(c) * np.abs(c) ** (2 / n) * np.where(c > 0, S.EYE_OUT_FRONT, S.EYE_OUT_BACK)
    oy = np.sign(s) * np.abs(s) ** (2 / n) * S.EYE_OUT_B
    ix, iy = S.EYE_IN_A * c, S.EYE_IN_B * s
    zb, zt = S.eye_z_range(th)

    rings, rv = [], []   # ring positions and their V coordinate

    def ring(x, y, z, v):
        rings.append(np.stack([x, y, z], 1))
        rv.append(v)

    K = 10
    for k in range(K + 1):                              # outer wall
        t = k / K
        z = zb + (zt - zb) * t
        bulge = 1.0 + 0.04 * np.sin(np.pi * t)          # slight barrel shape
        ring(ox * bulge, oy * bulge, z, 0.02 + 0.34 * (z.mean() + 0.065) / 0.12)
    for f, v in ((0.5, 0.365), (1.0, 0.37)):            # top annulus
        ring(ox + (ix - ox) * f, oy + (iy - oy) * f, zt, v)
    ring(ix, iy, zb, 0.38)                              # inner wall
    ring(ox + (ix - ox) * 0.5, oy + (iy - oy) * 0.5, zb, 0.385)
    # closing back to the outer bottom ring happens via wrap-around

    verts, faces, fuvs = [], [], []
    R = len(rings)
    for r in rings:
        verts += [tuple(p) for p in r]
    for r in range(R):
        r2 = (r + 1) % R
        v1, v2 = rv[r], rv[r2] if r2 else 0.39
        for i in range(Nt):
            i2 = (i + 1) % Nt
            faces.append([r * Nt + i, r * Nt + i2, r2 * Nt + i2, r2 * Nt + i])
            ua, ub = 0.02 + 0.96 * i / Nt, 0.02 + 0.96 * (i + 1) / Nt
            fuvs.append([(ua, v1), (ub, v1), (ub, v2), (ua, v2)])
    ob = make_mesh("Eye", verts, faces, fuvs, mat)
    finish(ob, bevel=0.0012)
    return ob


# ---------------------------------------------------------------- haft ------
def haft_ring(z, theta, grow=0.0):
    a, b, xc = S.haft_a(z) + grow, S.haft_b(z) + grow, S.haft_xc(z)
    return xc + a * np.cos(theta), b * np.sin(theta)


def build_haft(mat):
    Nt, Nz = 48, 140
    zs = np.linspace(S.HAFT_Z0, S.HAFT_Z1, Nz + 1)
    zs = np.unique(np.concatenate([zs, np.linspace(S.HAFT_Z0, S.HAFT_Z0 + 0.03, 12)]))
    L = S.HAFT_Z1 - S.HAFT_Z0
    th = np.linspace(0, 2 * np.pi, Nt, endpoint=False)
    verts, faces, fuvs = [], [], []
    for z in zs:
        x, y = haft_ring(z, th)
        verts += list(zip(x, y, np.full(Nt, z)))
    nz = len(zs)
    for k in range(nz - 1):
        for i in range(Nt):
            i2 = (i + 1) % Nt
            faces.append([k * Nt + i, k * Nt + i2, (k + 1) * Nt + i2, (k + 1) * Nt + i])
            va = 0.03 + 0.97 * (zs[k] - S.HAFT_Z0) / L
            vb = 0.03 + 0.97 * (zs[k + 1] - S.HAFT_Z0) / L
            ua, ub = i / Nt, (i + 1) / Nt
            fuvs.append([(ua, va), (ub, va), (ub, vb), (ua, vb)])
    # end caps with an inset ring (bevel-friendly) and end-grain UVs
    for (z, ring_start, cu) in ((zs[0], 0, 0.25), (zs[-1], (nz - 1) * Nt, 0.75)):
        xc = S.haft_xc(z)
        a, b = S.haft_a(z), S.haft_b(z)
        base = len(verts)
        for i in range(Nt):
            verts.append((xc + 0.85 * a * math.cos(th[i]), 0.85 * b * math.sin(th[i]), z))
        centre = len(verts)
        verts.append((xc, 0.0, z))

        def cuv(fx, fy):
            return (cu + 0.22 * fx, 0.0135 + 0.0125 * fy)
        for i in range(Nt):
            i2 = (i + 1) % Nt
            c1, s1, c2, s2 = math.cos(th[i]), math.sin(th[i]), math.cos(th[i2]), math.sin(th[i2])
            faces.append([ring_start + i, ring_start + i2, base + i2, base + i])
            fuvs.append([cuv(c1, s1), cuv(c2, s2), cuv(0.85 * c2, 0.85 * s2), cuv(0.85 * c1, 0.85 * s1)])
            faces.append([base + i, base + i2, centre])
            fuvs.append([cuv(0.85 * c1, 0.85 * s1), cuv(0.85 * c2, 0.85 * s2), cuv(0, 0)])
    ob = make_mesh("Haft", verts, faces, fuvs, mat)
    finish(ob, bevel=0.0015, smooth_angle=50)
    return ob


def build_wedge(mat):
    """Iron wedge driven into the top of the haft, splitting the end grain."""
    z0, z1 = S.HAFT_Z1 - 0.022, S.HAFT_Z1 + 0.0025
    xc = S.haft_xc(S.HAFT_Z1)
    hx = S.haft_a(S.HAFT_Z1) * 0.92
    verts = []
    for z, hy in ((z0, 0.0004), (z1, 0.0018)):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            verts.append((xc + sx * hx, sy * hy, z))
    faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    uv = [(0.1, 0.478), (0.3, 0.478), (0.3, 0.492), (0.1, 0.492)]
    ob = make_mesh("Wedge", verts, faces, [uv] * 6, mat)
    finish(ob, bevel=0.0004)
    return ob


# ---------------------------------------------------------------- grip ------
def build_grip(mat):
    """Leather strap wound as a helix. Mesh rows follow the helix so the
    overlapping strap edge is a clean step instead of a jagged diagonal."""
    Nt, M = 72, 14                      # samples around / rows per pitch
    p, z0, z1 = S.GRIP_PITCH, S.GRIP_Z0, S.GRIP_Z1
    Lg = z1 - z0
    turns = int(math.ceil(Lg / p)) + 2
    K = turns * M
    th_all = 2 * np.pi * np.arange(Nt + 1) / Nt
    verts, faces, fuvs = [], [], []

    def vid(i, k):
        return k * (Nt + 1) + i

    for k in range(K + 1):
        phi = (k % M) / M
        for i in range(Nt + 1):
            th = th_all[i]
            z_raw = z0 - p + p * (k / M - th / (2 * np.pi))
            z = min(max(z_raw, z0), z1)
            h = 0.0010 + 0.0010 * phi - 0.0004 * S.smoothstep(0.75, 1.0, phi) ** 2
            h *= S.smoothstep(0.0, 0.010, z_raw - z0) * S.smoothstep(0.0, 0.010, z1 - z_raw)
            h = max(h, 0.00015)
            x, y = haft_ring(z, np.array([th]), grow=h)
            verts.append((float(x[0]), float(y[0]), z))
    for k in range(K):
        for i in range(Nt):
            q = [vid(i, k), vid(i + 1, k), vid(i + 1, k + 1), vid(i, k + 1)]
            faces.append(q)
            uvq = []
            for (ii, kk) in ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1)):
                vx = verts[vid(ii, kk)]
                uvq.append((ii / Nt, (vx[2] - z0) / Lg))
            fuvs.append(uvq)
    # the ring i = Nt coincides with ring i = 0 shifted by M rows: weld the seam
    ob = make_mesh("Grip", verts, faces, fuvs, mat)
    finish(ob, smooth_angle=60)
    return ob


# --------------------------------------------------------------- export -----
def build():
    reset_scene()
    iron = make_material("Iron", "iron")
    wood = make_material("AshWood", "wood")
    leather = make_material("Leather", "leather")
    parts = [build_blade(iron), build_eye(iron), build_wedge(iron),
             build_haft(wood), build_grip(leather)]
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    axe = bpy.context.active_object
    axe.name = axe.data.name = "NorseBeardedAxe"
    # pivot at the centre of the grip
    axe.data.transform(__import__("mathutils").Matrix.Translation((0, 0, -PIVOT_Z)))
    axe.data.update()
    tri = axe.modifiers.new("Triangulate", "TRIANGULATE")
    tri.quad_method = "SHORTEST_DIAGONAL"
    bpy.ops.object.modifier_apply(modifier=tri.name)
    return axe


def export(axe):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    axe.select_set(True)
    glb = os.path.join(ROOT, "norse_axe.glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                              export_image_format="AUTO", export_apply=True,
                              export_tangents=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "norse_axe.blend"),
                                compress=True, relative_remap=True)
    tris = sum(len(p.vertices) - 2 for p in axe.data.polygons)
    dims = axe.dimensions
    print(f"exported {glb}  tris={tris}  size={dims.x:.3f} x {dims.y:.3f} x {dims.z:.3f} m")


if __name__ == "__main__":
    axe = build()
    export(axe)
    if "--render" in sys.argv:
        import render_preview
        render_preview.render(axe, ROOT, samples=int(os.environ.get("AXE_SAMPLES", 160)))
