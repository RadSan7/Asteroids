"""Geometry helpers for procedural assets (Blender bpy, metres, Z up).

Every builder returns a mesh object linked to the scene. Builders that know
their parametrisation also write a "design" UV layer that material masks and
decals use (the pipeline later creates a separate non-overlapping "bake" UV).
"""
import math

import bpy  # noqa: I001  (bpy must be imported before bmesh)
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector

DESIGN = "design"


# ----------------------------------------------------------------- basics ---
def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def activate(ob):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def set_mat(ob, mat):
    if mat is not None:
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    return ob


def mesh(name, verts, faces, uvs=None, mat=None, weld=1e-6, recalc=True):
    """verts: list of xyz, faces: index lists, uvs: per-face list of (u,v) per corner."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bv = [bm.verts.new(v) for v in verts]
    bm.verts.ensure_lookup_table()
    lay = bm.loops.layers.uv.new(DESIGN)
    for k, f in enumerate(faces):
        try:
            bf = bm.faces.new([bv[i] for i in f])
        except ValueError:
            continue
        if uvs is not None:
            for loop, uv in zip(bf.loops, uvs[k]):
                loop[lay].uv = uv
    if weld:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=weld)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return set_mat(_link(bpy.data.objects.new(name, me)), mat)


def xform(ob, loc=(0, 0, 0), rot=(0, 0, 0), scale=None, apply=True):
    """Transform and (by default) bake the transform into the mesh."""
    if scale is not None:
        ob.scale = scale if hasattr(scale, "__len__") else (scale,) * 3
    ob.rotation_euler = Euler(rot, "XYZ")
    ob.location = loc
    if apply:
        ob.data.transform(ob.matrix_basis)
        ob.matrix_basis = Matrix.Identity(4)
        ob.data.update()
    return ob


def rotd(x=0, y=0, z=0):
    return tuple(math.radians(a) for a in (x, y, z))


def copy(ob, name=None):
    n = ob.copy()
    n.data = ob.data.copy()
    n.name = name or ob.name + "_c"
    return _link(n)


def join(objs, name=None):
    objs = [o for o in objs if o is not None]
    for o in objs:
        apply_mods(o)
    activate(objs[0])
    for o in objs:
        o.select_set(True)
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.active_object
    if name:
        ob.name = ob.data.name = name
    return ob


def delete(ob):
    bpy.data.objects.remove(ob, do_unlink=True)


# -------------------------------------------------------------- modifiers ---
def mod(ob, kind, **props):
    m = ob.modifiers.new(kind.title(), kind.upper())
    for k, v in props.items():
        setattr(m, k, v)
    return m


def apply_mods(ob):
    if ob.type != "MESH":
        activate(ob)
        bpy.ops.object.convert(target="MESH")
        return ob
    activate(ob)
    for m in list(ob.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError:
            ob.modifiers.remove(m)
    return ob


def bevel(ob, width, segs=2, angle=40, apply=True, clamp=True):
    mod(ob, "bevel", width=width, segments=segs, limit_method="ANGLE",
        angle_limit=math.radians(angle), use_clamp_overlap=clamp)
    return apply_mods(ob) if apply else ob


def subsurf(ob, levels=2, apply=True, crease=None):
    mod(ob, "subsurf", levels=levels, render_levels=levels)
    return apply_mods(ob) if apply else ob


def solidify(ob, thick, offset=-1.0, apply=True, rim=True):
    mod(ob, "solidify", thickness=thick, offset=offset, use_rim=rim, use_even_offset=True)
    return apply_mods(ob) if apply else ob


def deform(ob, method, angle=0.0, factor=0.0, axis="Z", apply=True, origin=None):
    """SimpleDeform: method TWIST | BEND | TAPER | STRETCH."""
    m = mod(ob, "simple_deform", deform_method=method, deform_axis=axis)
    if method in ("TWIST", "BEND"):
        m.angle = math.radians(angle)
    else:
        m.factor = factor
    if origin is not None:
        e = bpy.data.objects.new(ob.name + "_origin", None)
        _link(e)
        e.location = origin
        m.origin = e
        apply_mods(ob)
        delete(e)
        return ob
    return apply_mods(ob) if apply else ob


def displace(ob, strength, scale=0.05, kind="CLOUDS", depth=2, mid=0.5, uv=False, apply=True, image=None):
    tex = bpy.data.textures.new(ob.name + "_disp", "IMAGE" if image else kind)
    if image:
        tex.image = bpy.data.images.load(image) if isinstance(image, str) else image
        tex.extension = "EXTEND"
    else:
        tex.noise_scale = scale
        if hasattr(tex, "noise_depth"):
            tex.noise_depth = depth
    m = mod(ob, "displace", texture=tex, strength=strength, mid_level=mid)
    if uv or image:
        m.texture_coords = "UV"
        m.uv_layer = DESIGN
    else:
        m.texture_coords = "OBJECT" if False else "LOCAL"
    return apply_mods(ob) if apply else ob


def boolean(ob, cutter, op="DIFFERENCE", keep=False, solver="EXACT"):
    m = mod(ob, "boolean", operation=op, object=cutter, solver=solver)
    apply_mods(ob)
    if not keep:
        delete(cutter)
    return ob


def smooth(ob, angle=35):
    activate(ob)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    return ob


def flat(ob):
    activate(ob)
    bpy.ops.object.shade_flat()
    return ob


# ------------------------------------------------------------- primitives ---
def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), bev=0.0, segs=2, mat=None, subdiv=0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    if subdiv:
        mod(ob, "subsurf", levels=subdiv, subdivision_type="SIMPLE")
        apply_mods(ob)
    xform(ob, (0, 0, 0), (0, 0, 0), size)
    if bev:
        bevel(ob, bev, segs)
    _box_uv(ob)
    xform(ob, loc, rot)
    return set_mat(ob, mat)


def _box_uv(ob):
    """Planar-by-dominant-axis design UVs in metres (tileable materials)."""
    me = ob.data
    lay = me.uv_layers.get(DESIGN) or me.uv_layers.new(name=DESIGN)
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            lay.data[li].uv = (co[a], co[b])


def planar_uv(ob, axis="Y", fit=True, stretch=False):
    """Project design UVs along an axis; fit=True normalises to 0..1 over bbox
    (keeping aspect), stretch=True fills 0..1 on both axes."""
    me = ob.data
    lay = me.uv_layers.get(DESIGN) or me.uv_layers.new(name=DESIGN)
    a, b = {"X": (1, 2), "Y": (0, 2), "Z": (0, 1)}[axis]
    co = np.array([v.co[:] for v in me.vertices])
    lo, hi = co.min(0), co.max(0)
    span = max(hi[a] - lo[a], hi[b] - lo[b]) or 1.0
    for li, loop in enumerate(me.loops):
        c = co[loop.vertex_index]
        if stretch:
            lay.data[li].uv = ((c[a] - lo[a]) / ((hi[a] - lo[a]) or 1), (c[b] - lo[b]) / ((hi[b] - lo[b]) or 1))
        elif fit:
            lay.data[li].uv = ((c[a] - lo[a]) / span, (c[b] - lo[b]) / span)
        else:
            lay.data[li].uv = (c[a], c[b])
    return ob


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), segs=48, bev=0.0, mat=None, r2=None, caps=True):
    """Cylinder / cone frustum along Z from z=0 to z=h (before transform)."""
    r2 = r if r2 is None else r2
    prof = [(0, 0), (r, 0), (r2, h), (0, h)] if caps else [(r, 0), (r2, h)]
    ob = lathe(name, prof, segs=segs, mat=mat)
    if bev:
        bevel(ob, bev, 2)
    return xform(ob, loc, rot)


def sphere(name, r, loc=(0, 0, 0), segs=48, rings=24, mat=None, scale=None):
    prof = [(r * math.sin(t), -r * math.cos(t)) for t in np.linspace(0, math.pi, rings + 1)]
    ob = lathe(name, prof, segs=segs, mat=mat)
    return xform(ob, loc, (0, 0, 0), scale)


def torus(name, R, r, loc=(0, 0, 0), rot=(0, 0, 0), segs=64, rsegs=16, mat=None):
    pts = [(R + r * math.cos(t), r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, rsegs + 1)]
    ob = lathe(name, pts, segs=segs, mat=mat, caps=False)
    return xform(ob, loc, rot)


def lathe(name, profile, segs=64, mat=None, caps=True, angle=2 * math.pi, smooth_angle=None):
    """Revolve a (r, z) polyline around Z. Design UV: u = angle, v = arc length."""
    prof = np.array(profile, dtype=float)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))]
    vco = seg / (seg[-1] or 1)
    full = abs(angle - 2 * math.pi) < 1e-6
    cols = segs + 1
    verts, faces, uvs = [], [], []
    for i in range(cols):
        t = angle * i / segs
        c, s = math.cos(t), math.sin(t)
        for (r, z) in prof:
            verts.append((r * c, r * s, z))
    n = len(prof)
    for i in range(segs):
        for j in range(n - 1):
            a, b = i * n + j, (i + 1) * n + j
            faces.append([a, b, b + 1, a + 1])
            u0, u1 = i / segs, (i + 1) / segs
            uvs.append([(u0, vco[j]), (u1, vco[j]), (u1, vco[j + 1]), (u0, vco[j + 1])])
    ob = mesh(name, verts, faces, uvs, mat)
    if smooth_angle:
        smooth(ob, smooth_angle)
    return ob


def loft(name, sections, mat=None, closed=True, cap=True):
    """Skin a list of rings (each an (N,3) array with equal N). Design UV: u around, v along."""
    secs = [np.asarray(s, dtype=float) for s in sections]
    N = len(secs[0])
    verts = [tuple(p) for s in secs for p in s]
    faces, uvs = [], []
    ncol = N if closed else N - 1
    L = len(secs)
    for k in range(L - 1):
        for i in range(ncol):
            i2 = (i + 1) % N
            faces.append([k * N + i, k * N + i2, (k + 1) * N + i2, (k + 1) * N + i])
            u0, u1 = i / ncol, (i + 1) / ncol
            v0, v1 = k / (L - 1), (k + 1) / (L - 1)
            uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    if cap and closed:
        for k, flip in ((0, True), (L - 1, False)):
            f = [k * N + i for i in range(N)]
            faces.append(f[::-1] if flip else f)
            c = secs[k][:, :2]
            lo, hi = c.min(0), c.max(0)
            span = max(hi - lo) or 1
            uv = [tuple((p - lo) / span) for p in c]
            uvs.append(uv[::-1] if flip else uv)
    return mesh(name, verts, faces, uvs, mat)


# ------------------------------------------------------------------ curves --
def _curve_obj(name, splines, dims="2D", fill="BOTH", extrude=0.0, bevel=0.0, bres=2,
               res=12, closed=True, radii=None, profile=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = dims
    if dims == "2D":
        cu.fill_mode = fill
    else:
        cu.fill_mode = "FULL"
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = bres
    cu.resolution_u = res
    if profile is not None:
        cu.bevel_mode = "OBJECT"
        cu.bevel_object = profile
        cu.use_fill_caps = True
    for k, pts in enumerate(splines):
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            x, y, z = (p[0], p[1], 0.0) if len(p) == 2 else p
            sp.points[i].co = (x, y, z, 1.0)
            if radii is not None:
                sp.points[i].radius = radii[i]
        sp.use_cyclic_u = closed
    return _link(bpy.data.objects.new(name, cu))


def extrude(name, polys, depth, bev=0.0, bres=2, plane="XZ", mat=None, uv_fit=True):
    """Solid from 2D polygon(s) (outer + holes, even-odd). Built in XY, then
    rotated so the shape lies in `plane`; thickness is along the remaining axis."""
    if np.ndim(polys[0]) == 1:
        polys = [polys]
    ob = _curve_obj(name, polys, extrude=max(depth / 2 - bev, 0.0), bevel=bev, bres=bres)
    ob = apply_mods(ob)
    ob.name = name
    planar_uv(ob, "Z", fit=uv_fit)
    rot = {"XY": (0, 0, 0), "XZ": (math.pi / 2, 0, 0), "YZ": (math.pi / 2, 0, math.pi / 2)}[plane]
    xform(ob, (0, 0, 0), rot)
    return set_mat(ob, mat)


def sweep(name, path, radius=0.005, mat=None, closed=False, res=10, radii=None, rect=None,
          profile_pts=None, caps=True):
    """Tube (or rectangular strap with rect=(w, h), or custom 2D profile) along a 3D polyline."""
    prof = None
    if rect is not None or profile_pts is not None:
        pts = profile_pts or [(-rect[0] / 2, -rect[1] / 2), (rect[0] / 2, -rect[1] / 2),
                              (rect[0] / 2, rect[1] / 2), (-rect[0] / 2, rect[1] / 2)]
        prof = _curve_obj(name + "_prof", [pts], dims="2D", fill="NONE")
    ob = _curve_obj(name, [path], dims="3D", bevel=0 if prof else radius, bres=max(2, res // 4),
                    closed=closed, radii=radii, profile=prof)
    ob.data.use_fill_caps = caps
    ob.data.twist_mode = "MINIMUM"
    if prof is None:
        ob.data.bevel_resolution = max(2, res // 4)
    ob.data.use_uv_as_generated = True
    ob = apply_mods(ob)
    ob.name = name
    if prof is not None:
        delete(prof)
    _ensure_design(ob)
    return set_mat(ob, mat)


def _ensure_design(ob):
    me = ob.data
    if me.uv_layers:
        me.uv_layers[0].name = DESIGN
    else:
        me.uv_layers.new(name=DESIGN)


def text(name, s, size=0.05, depth=0.004, bev=0.0005, font=None, mat=None, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = s
    cu.size = size
    cu.extrude = depth / 2
    cu.bevel_depth = bev
    cu.align_x = align
    cu.align_y = "CENTER"
    if font:
        cu.font = bpy.data.fonts.load(font)
    ob = apply_mods(_link(bpy.data.objects.new(name, cu)))
    ob.name = name
    _ensure_design(ob)
    return set_mat(ob, mat)


# ------------------------------------------------------------ distribution --
def ring_points(n, r, z=0.0, phase=0.0):
    return [(r * math.cos(phase + 2 * math.pi * i / n), r * math.sin(phase + 2 * math.pi * i / n), z)
            for i in range(n)]


def radial_array(ob, count, axis="Z", keep=True):
    parts = [ob]
    for i in range(1, count):
        c = copy(ob)
        rot = [0, 0, 0]
        rot["XYZ".index(axis)] = 2 * math.pi * i / count
        xform(c, (0, 0, 0), rot)
        parts.append(c)
    return join(parts, ob.name)


def scatter(template, transforms, name=None):
    """transforms: iterable of (loc, rot, scale). Returns one joined object."""
    parts = []
    for loc, rot, sc in transforms:
        c = copy(template)
        xform(c, loc, rot, sc)
        parts.append(c)
    delete(template)
    return join(parts, name or template.name)


def curve_pts(ctrl, n=64, closed=False):
    """Catmull-Rom through control points -> dense polyline (2D or 3D)."""
    P = np.asarray(ctrl, dtype=float)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    segs = len(P) - 3
    per = max(2, n // segs)
    for i in range(segs):
        p0, p1, p2, p3 = P[i:i + 4]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(P[-2])
    # resample to exactly n points, evenly spaced along the arc
    A = np.array(out)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(A, axis=0), axis=1))]
    t = np.linspace(0, s[-1], n)
    R = np.stack([np.interp(t, s, A[:, k]) for k in range(A.shape[1])], 1)
    return [tuple(p) for p in R]


def bbox(ob):
    co = np.array([ob.matrix_world @ Vector(c) for c in ob.bound_box])
    return co.min(0), co.max(0)


# ------------------------------------------------------------ path tools ---
def frames(path, up=(0, 0, 1)):
    """Parallel-transport frames along a polyline: returns (T, N, B) arrays."""
    P = np.asarray(path, dtype=float)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    up = np.asarray(up, dtype=float)
    n0 = np.cross(T[0], up)
    if np.linalg.norm(n0) < 1e-6:
        n0 = np.cross(T[0], (1, 0, 0))
    n0 /= np.linalg.norm(n0)
    N = [n0]
    for i in range(1, len(P)):
        n = N[-1] - T[i] * np.dot(N[-1], T[i])
        N.append(n / (np.linalg.norm(n) + 1e-12))
    N = np.array(N)
    B = np.cross(T, N)
    return T, N, B


def tube(name, path, radii, n=32, mat=None, cap=True, scale2=None, up=(0, 0, 1)):
    """Circular (or elliptical with scale2) tube along a polyline with per-point radius."""
    P = np.asarray(path, dtype=float)
    radii = np.broadcast_to(np.asarray(radii, dtype=float), (len(P),))
    s2 = np.broadcast_to(np.asarray(scale2 if scale2 is not None else 1.0, dtype=float), (len(P),))
    T, N, B = frames(P, up)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    secs = [P[i] + radii[i] * (np.outer(np.cos(th), N[i]) + s2[i] * np.outer(np.sin(th), B[i]))
            for i in range(len(P))]
    return loft(name, secs, mat, closed=True, cap=cap)


def strap(name, path, normals, width, thick, mat=None, cap=True):
    """Flat band lying on a surface: path points + outward surface normals."""
    P = np.asarray(path, dtype=float)
    Nn = np.asarray(normals, dtype=float)
    Nn = Nn / (np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-12)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    Bs = np.cross(T, Nn)
    Bs /= np.linalg.norm(Bs, axis=1, keepdims=True) + 1e-12
    w = np.broadcast_to(np.asarray(width, dtype=float), (len(P),))
    secs = []
    for i in range(len(P)):
        a, b = Bs[i] * w[i] / 2, Nn[i] * thick
        secs.append([P[i] - a, P[i] + a, P[i] + a + b, P[i] - a + b])
    return loft(name, secs, mat, closed=True, cap=cap)


def wrap_cyl(ob, R, squash=1.0):
    """Bend a flat part (built in XZ, thin along Y, centred on x=0) onto a
    vertical cylinder of radius R whose front faces -Y."""
    for v in ob.data.vertices:
        x, y, z = v.co
        a = x / R
        r = R - y
        v.co = (r * math.sin(a), -r * math.cos(a) * squash, z)
    ob.data.update()
    return ob


def all_meshes():
    return [o for o in bpy.context.scene.objects if o.type in ("MESH", "CURVE", "FONT")]


def transform_all(loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    for o in all_meshes():
        apply_mods(o)
        xform(o, loc, rot, scale)


# ------------------------------------------------------------- 2D shapes ---
def shape_polys(geom):
    """shapely (Multi)Polygon -> list of rings for extrude() (outer + holes)."""
    from shapely.geometry import MultiPolygon, Polygon
    geoms = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    rings = []
    for g in geoms:
        if not isinstance(g, Polygon) or g.is_empty:
            continue
        rings.append(list(g.exterior.coords)[:-1])
        rings += [list(h.coords)[:-1] for h in g.interiors]
    return rings


def circle2d(cx, cy, r, n=64):
    from shapely.geometry import Point
    return Point(cx, cy).buffer(r, quad_segs=max(4, n // 4))


def poly2d(pts):
    from shapely.geometry import Polygon
    return Polygon(pts)


def line2d(pts, width, cap=1):
    from shapely.geometry import LineString
    return LineString(pts).buffer(width / 2, cap_style=cap, join_style=1, quad_segs=8)


def lathe_v(profile, z):
    """Design-UV v on the OUTER wall of a lathe profile at height z (profile as
    passed to lathe(): rising along the outside first)."""
    P = np.asarray(profile, dtype=float)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    v = seg / seg[-1]
    top = int(np.argmax(P[:, 1]))
    for i in range(top):
        z0, z1 = P[i, 1], P[i + 1, 1]
        if min(z0, z1) <= z <= max(z0, z1) and z1 != z0:
            f = (z - z0) / (z1 - z0)
            return float(v[i] + f * (v[i + 1] - v[i]))
    return float(v[top] if z > P[top, 1] else 0.0)


def tag_random(ob, value=None, rng=None):
    """Write a per-part random float attribute "rand" (used by texmat to offset textures)."""
    import random
    v = value if value is not None else (rng.random() if rng is not None else random.random())
    me = ob.data
    a = me.attributes.get("rand") or me.attributes.new("rand", "FLOAT", "POINT")
    a.data.foreach_set("value", [v] * len(me.vertices))
    return ob
