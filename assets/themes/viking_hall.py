"""Viking longhouse / mead-hall MODULAR KIT.

Metrics (metres, Z up, hall length along X, span along Y):
  GRID        2.0   every wall / floor / roof module is 2 m along X
  FOUND_H     0.5   stone plinth from ground (z=0) to floor level
  WALL_H      2.5   wall module height; wall base sits on the plinth (z=0.5)
  WALL_TOP    3.0   world height of the top plate
  SPAN        8.0   outer wall lines at y = -4 / +4
  PITCH       45 deg, eave overhang 0.6 m, ridge 4.0 m above WALL_TOP (z=7.0)

Pivots (the point that snaps to the grid):
  foundation_2m, wall_*_2m, beam_2m, floor_*    start of the module (x=0), wall centre line, base
  foundation_corner, posts, hearth, props        centre of the footprint, base
  door_plank                                     hinge axis, bottom of the leaf
  tie_beam_8m, rafter_pair_8m, gable_wall_8m,
  roof_thatch_2m, roof_ridge_2m, gable_finial     hall centre line (y=0) at WALL_TOP level (z=3.0 in world)
  roof_thatch_2m covers the -Y slope; rotate 180 deg about Z (and shift +2 m in X) for the +Y slope.
  post_hall (4.0 m) stands on the floor (z=0.5) in two rows at y=+-2; purlins (beam_2m) sit on it at z=4.5.
  door_plank hangs in wall_plank_door_2m at local (0.57, 0, 0.22).
"""
import math

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge import texsynth as T
from forge.pipeline import asset

pi = math.pi
GRID, FOUND_H, WALL_H, SPAN, EAVE, RISE = 2.0, 0.5, 2.5, 8.0, 0.6, 4.0
HALF = SPAN / 2
SLOPE_L = (HALF + EAVE) * math.sqrt(2)
VERT = (pi / 2, -pi / 2, 0)      # plank(): length -> Z, width -> X, thickness -> Y


# ================================================================ materials
def _moss(zmax, amount=1.0):
    return [dict(mask=M.axis_mask("Z", zmax, 0.0, noise=0.25, nscale=4), color=(0.05, 0.055, 0.03), rough=0.9,
                 opacity=0.7 * amount, height=0.1),
            dict(mask=lambda nb: nb.mul(nb.ss(nb.sep(nb.co())[2], zmax * 0.6, 0.0),
                                        nb.ss(nb.noise(9, 8, 0.7), 0.55, 0.65)),
                 color=(0.05, 0.09, 0.025), rough=0.95, height=0.5, opacity=amount)]


def adze_layer(strength=0.6, axis="X"):
    st = {"X": (0.8, 3.0, 3.0), "Y": (3.0, 0.8, 3.0), "Z": (3.0, 3.0, 0.8)}[axis]
    return dict(mask=lambda nb: nb.math("POWER", nb.voronoi(14, nb.mapv(scale=st), feature="F1"), 2.0),
                height=strength)


def oak(name, axis="Z", weather=0.6, cracks=0.5, adze=0.0, damp=0.0, **kw):
    """Oak from synthesized boards: weathered (silver, checked) or fresh (interior)."""
    tex = T.get("oak_weathered" if weather >= 0.5 else "oak_aged")
    layers = list(kw.pop("layers", []) or [])
    if adze:
        layers.append(adze_layer(adze, axis))
    if damp:
        layers += _moss(damp)
    return M.texmat(name, tex, "box", axis=axis, bump=0.9 if weather >= 0.5 else 0.5, dirt=0.45, wear=0.25,
                    layers=layers)


def beam_oak(name, axis="X"):
    return oak(name, axis=axis, weather=0.6, adze=0.8)


def fieldstone(name, moss_z=0.18):
    return M.texmat(name, T.get("granite"), "box", axis="Z", bump=0.8, dirt=0.5, wear=0.2,
                    layers=_moss(moss_z) if moss_z > 0 else None)


def thatch(name, mode="slope"):
    moss = dict(mask=lambda nb: nb.mul(nb.ss(nb.noise(2.2, 10, 0.7), 0.58, 0.68),
                                       nb.ss(nb.sep(nb.co())[2], 2.0, -0.4)),
                color=(0.045, 0.065, 0.02), rough=0.95, height=0.3)
    patchy = dict(mask=lambda nb: nb.ss(nb.noise(1.1, 6, 0.6), 0.45, 0.7), color=(0.20, 0.18, 0.15),
                  opacity=0.35)
    return M.texmat(name, T.get("thatch"), mode, bump=0.9, dirt=0.3, wear=0.0, layers=[patchy, moss])


def earth(name):
    return M.texmat(name, T.get("earth"), "planar", bump=1.5, dirt=0.0, wear=0.0)


def daub(name):
    grime = dict(mask=M.axis_mask("Z", 0.8, 0.1, noise=0.3, nscale=3), color=(0.12, 0.09, 0.06), opacity=0.5)
    return M.texmat(name, T.get("daub"), "box", axis="Z", bump=1.3, dirt=0.4, wear=0.3, layers=[grime])


def iron(name="iron"):
    return M.metal(name, "iron", rough=0.5, wear=0.7, dirt=0.7, patina=(0.04, 0.035, 0.03), patina_amt=0.6, rust=0.35,
                   pitting=0.3, scale=3)


def straw(name="straw"):
    return M.plastic(name, color=(0.22, 0.17, 0.08), marble=(0.12, 0.095, 0.05), rough=0.65, wear=0.0, dirt=0.6,
                     scale=20)


def hazel(name="hazel"):
    return M.wood(name, light=(0.16, 0.10, 0.06), dark=(0.06, 0.04, 0.025), axis="X", weather=0.3, pores=0.2,
                  dirt=0.5, ring_scale=120)


# ================================================================== helpers
def deform(ob, fn):
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = fn(co.reshape(-1, 3))
    me.vertices.foreach_set("co", np.asarray(co, dtype=float).ravel())
    me.update()
    return ob


def snoise(P, seed, freq=4.0, k=7):
    """Smooth pseudo-noise from random sinusoids (numpy, deterministic)."""
    rng = np.random.default_rng(seed)
    out = np.zeros(len(P))
    for i in range(k):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        f = freq * (1.6 ** i) * (0.7 + 0.6 * rng.random())
        out += np.sin(P @ d * f + rng.random() * 6.28) / (1.7 ** i)
    return out / 1.6


def plank(name, L, W, T, loc, rot, mat, seed, bow=0.008, twist=0.02):
    """Hand-split plank along its local X, deformed, then placed."""
    ob = G.box(name, (L, W, T), bev=min(0.006, T * 0.3), segs=2, mat=mat, subdiv=3)
    rng = np.random.default_rng(seed)
    b = bow * rng.normal()
    tw = twist * rng.normal()

    def f(co):
        t = co[:, 0] / (L / 2)
        co[:, 2] += b * (1 - t ** 2)
        a = tw * t
        y, z = co[:, 1].copy(), co[:, 2].copy()
        co[:, 1] = y * np.cos(a) - z * np.sin(a)
        co[:, 2] = y * np.sin(a) + z * np.cos(a)
        co[:, 1] *= 1 + 0.05 * np.sin(t * 2.3 + seed)
        co += (snoise(co * [1, 3, 3], seed, 1.5)[:, None] * [0, 0.002, 0.0015])
        return co
    deform(ob, f)
    G._box_uv(ob)
    G.tag_random(ob, (seed * 0.61803) % 1.0)
    return G.xform(ob, loc, rot)


def hewn(name, L, w, h, loc, rot, mat, seed, bow=0.012):
    """Axe-hewn timber along local X (slightly irregular faces, softened arrises)."""
    ob = G.box(name, (L, w, h), bev=0.018, segs=3, mat=mat, subdiv=3)

    def f(co):
        t = co[:, 0] / (L / 2)
        co[:, 2] += bow * (1 - t ** 2)
        n = snoise(co * [0.6, 4, 4], seed, 1.2)
        co[:, 1] *= 1 + 0.04 * n
        co[:, 2] *= 1 + 0.03 * snoise(co * [0.6, 4, 4], seed + 7, 1.2)
        return co
    deform(ob, f)
    G._box_uv(ob)
    G.tag_random(ob, (seed * 0.4142 + 0.3) % 1.0)
    return G.xform(ob, loc, rot)


def rock(name, dims, loc, mat, seed, rot=(0, 0, 0), flat_top=None, flat_bottom=True, rough=0.14, facets=4, sub=None):
    """Angular fieldstone: rounded box, noise, then a few random split planes."""
    sub = sub or (4 if max(dims) > 0.4 else 3 if max(dims) > 0.1 else 2)
    ob = G.box(name, (1, 1, 1), mat=mat, subdiv=sub)
    rng = np.random.default_rng(seed)

    def f(co):
        n = co / np.linalg.norm(co, axis=1, keepdims=True)
        co = co * 0.72 + n * 0.28 * 0.5
        co += n * (rough * snoise(co, seed, 2.5) + 0.35 * rough * snoise(co, seed + 1, 7.0))[:, None]
        for _ in range(facets):
            d = rng.normal(size=3)
            d[2] *= 0.5
            d /= np.linalg.norm(d)
            lim = 0.36 + 0.1 * rng.random()
            h = co @ d
            over = h > lim
            co[over] -= np.outer(h[over] - lim, d) * 0.92
        co *= np.array(dims)
        if flat_bottom:
            co[:, 2] = np.maximum(co[:, 2], -dims[2] * 0.42)
        if flat_top is not None:
            co[:, 2] = np.minimum(co[:, 2], flat_top)
        return co
    deform(ob, f)
    G._box_uv(ob)
    G.tag_random(ob, (seed * 0.7548) % 1.0)
    return G.xform(ob, loc, rot)


def split_widths(total, lo, hi, seed, gap=0.004):
    rng = np.random.default_rng(seed)
    ws = []
    while sum(ws) + len(ws) * gap < total - hi:
        ws.append(lo + (hi - lo) * rng.random())
    ws.append(total - sum(ws) - len(ws) * gap)
    return ws


def pegs(points, axis_rot, mat, r=0.014, L=0.06, name="peg"):
    for i, p in enumerate(points):
        G.cyl(f"{name}{i}", r, L, loc=p, rot=axis_rot, segs=10, bev=0.003, mat=mat)


def knot_band(name, n=6, v0=0.0, v1=1.0, width=0.01):
    """Interlaced ribbon band (Borre/Mammen-like) for carved decoration."""
    c = D.Canvas(2048)
    for k in range(2):
        pts = [(u, v0 + (v1 - v0) * (0.5 + 0.38 * math.sin(2 * pi * n * u + k * pi))) for u in np.linspace(0, 1, 800)]
        c.line(pts, width)
    for i in range(n * 2):
        u = (i + 0.25) / (n * 2)
        c.circle(u, v0 + (v1 - v0) * 0.5, width * 0.9)
    c.hband(v0, v0 + width * 0.8).hband(v1 - width * 0.8, v1)
    return c.blur(1.2).save(name)


# ============================================================ foundations
@asset(res=2048, view=(-25, 18), pivot="origin", kind="kit", title="Foundation 2m", max_tris=24000)
def foundation_2m():
    st = fieldstone("plinth_stone")
    rng = np.random.default_rng(1)
    k = 0
    for course, (zc, h, seed) in enumerate(((0.13, 0.3, 1), (0.37, 0.26, 2))):
        x = 0.0
        ws = split_widths(GRID, 0.26, 0.5, seed + 10, gap=0.0)
        if course:
            ws = ws[::-1]
        for L in ws:
            hh = h * (0.85 + 0.25 * rng.random())
            rock(f"s{k}", (L * 1.06, 0.44 + 0.06 * rng.random(), hh), (x + L / 2, 0.015 * rng.normal(), zc), st,
                 100 + k, flat_top=h / 2, rot=(0.04 * rng.normal(), 0.04 * rng.normal(), 0.08 * rng.normal()))
            x += L
            k += 1
    for i in range(16):
        rock(f"chink{i}", (0.07 + 0.05 * rng.random(), 0.08, 0.05 + 0.03 * rng.random()),
             (0.05 + 1.9 * rng.random(), -0.22 + 0.44 * (i % 2), 0.25 + 0.03 * rng.normal()), st, 300 + i, rough=0.2,
             rot=(0, 0, rng.random() * pi))


@asset(res=1024, view=(-35, 22), pivot="origin", kind="kit", title="Foundation corner")
def foundation_corner():
    st = fieldstone("corner_stone")
    rock("c0", (0.6, 0.58, 0.3), (0, 0, 0.14), st, 11, flat_top=0.15, facets=6)
    rock("c1", (0.54, 0.5, 0.26), (0.02, -0.01, 0.37), st, 12, flat_top=0.13, rot=(0, 0, 0.35), facets=6)
    rock("c2", (0.14, 0.12, 0.1), (0.3, 0.26, 0.26), st, 13, rot=(0, 0, 1.0))
    rock("c3", (0.12, 0.1, 0.08), (-0.29, -0.25, 0.25), st, 14, rot=(0, 0, 2.0))


@asset(res=2048, view=(-20, 40), pivot="origin", kind="kit", title="Floor earth 2x2")
def floor_earth_2x2():
    bpy_grid = G.box("earth", (2.0, 2.0, 0.06), loc=(1.0, 1.0, -0.03), mat=earth("packed_earth"), subdiv=5)

    def f(co):
        edge = np.clip(np.minimum.reduce([co[:, 0], 2 - co[:, 0], co[:, 1], 2 - co[:, 1]]) / 0.2, 0, 1)
        top = co[:, 2] > -0.001
        co[top, 2] += (0.012 * snoise(co[top] * [1, 1, 0], 5, 2.0) + 0.006) * edge[top]
        return co
    deform(bpy_grid, f)
    stm = straw("floor_straw")
    rng = np.random.default_rng(3)
    for i in range(45):
        p = np.array([0.05 + 1.9 * rng.random(), 0.05 + 1.9 * rng.random(), 0.007])
        a = rng.random() * pi
        L = 0.05 + 0.12 * rng.random()
        d = np.array([math.cos(a), math.sin(a), 0]) * L / 2
        G.tube(f"straw{i}", [p - d, p + d * 0.2 + [0, 0, 0.002], p + d], 0.0012, n=4, mat=stm, scale2=0.5)


@asset(res=2048, view=(-20, 40), pivot="origin", kind="kit", title="Floor planks 2x2")
def floor_planks_2x2():
    wd = oak("floor_oak", axis="X", weather=0.25, cracks=0.4)
    y = 0.0
    for i, w in enumerate(split_widths(2.0, 0.2, 0.3, 21, gap=0.005)):
        plank(f"pl{i}", 2.0, w, 0.045, (1.0, y + w / 2, -0.0225), (0, 0, 0), wd, 30 + i, bow=0.003)
        pegs([(0.1, y + w / 2, -0.001), (1.9, y + w / 2, -0.001)], (0, 0, 0), wd, r=0.012, L=0.004, name=f"n{i}")
        y += w + 0.005
    jo = beam_oak("joist_oak", axis="Y")
    for x in (0.5, 1.5):
        hewn(f"joist{x}", 2.0, 0.14, 0.14, (x, 1.0, -0.117), (0, 0, pi / 2), jo, int(x * 10))


# ================================================================== walls
def _wall_frame(sill_mat, pmat, n_pegs=4):
    hewn("sill", GRID, 0.26, 0.22, (1.0, 0, 0.11), (0, 0, 0), sill_mat, 1)
    hewn("plate", GRID, 0.26, 0.2, (1.0, 0, WALL_H - 0.1), (0, 0, 0), sill_mat, 2)
    xs = np.linspace(0.25, 1.75, n_pegs)
    pegs([(x, -0.13, 0.11) for x in xs] + [(x, -0.13, WALL_H - 0.1) for x in xs], (pi / 2, 0, 0), pmat)
    pegs([(x, 0.13, 0.11) for x in xs] + [(x, 0.13, WALL_H - 0.1) for x in xs], (pi / 2, 0, 0), pmat, name="pb")


@asset(res=2048, view=(-20, 10), pivot="origin", kind="kit", title="Wall plank 2m")
def wall_plank_2m():
    beams = beam_oak("wall_beam_oak")
    boards = oak("wall_board_oak", axis="Z", weather=0.75, damp=0.35)
    _wall_frame(beams, beams)
    x = 0.0
    for i, w in enumerate(split_widths(GRID, 0.2, 0.32, 7)):
        plank(f"board{i}", WALL_H - 0.3, w, 0.06, (x + w / 2, 0.003 * (i % 2), WALL_H / 2), VERT, boards,
              40 + i, bow=0.01)
        x += w + 0.004


@asset(res=2048, view=(-20, 10), pivot="origin", kind="kit", title="Wall plank door 2m")
def wall_plank_door_2m():
    beams = beam_oak("door_beam_oak")
    boards = oak("door_board_oak", axis="Z", weather=0.75, damp=0.35)
    _wall_frame(beams, beams)
    for i, x0 in enumerate((0.45, 1.43)):
        hewn(f"jamb{i}", 1.86, 0.12, 0.2, (x0 + 0.06, 0, 0.22 + 0.93), (0, pi / 2, 0), beams, 60 + i, bow=0.004)
    hewn("lintel", 1.3, 0.2, 0.2, (1.0, 0, 2.18), (0, 0, 0), beams, 70, bow=0.004)
    x = 0.0
    for i, w in enumerate(split_widths(GRID, 0.2, 0.3, 17)):
        c = x + w / 2
        if 0.42 < c < 1.58:
            pl = 0.14
            plank(f"above{i}", pl, w, 0.06, (c, 0, 2.29 + 0.01), VERT, boards, 80 + i, bow=0.0)
        else:
            plank(f"board{i}", WALL_H - 0.3, w, 0.06, (c, 0.003 * (i % 2), WALL_H / 2), VERT, boards,
                  90 + i, bow=0.01)
        x += w + 0.004


@asset(res=1024, view=(-25, 8), pivot="origin", kind="kit", title="Plank door")
def door_plank():
    boards = oak("leaf_oak", axis="Z", weather=0.5, cracks=0.3)
    W, H = 0.9, 1.84
    x = 0.0
    for i, w in enumerate(split_widths(W, 0.2, 0.26, 5)):
        plank(f"b{i}", H, w, 0.04, (x + w / 2, 0, H / 2), VERT, boards, 10 + i, bow=0.004)
        x += w + 0.003
    battens = oak("batten_oak", axis="X", weather=0.4)
    for z in (0.3, 1.5):
        plank(f"batten{z}", W - 0.06, 0.12, 0.035, (W / 2, 0.037, z), (0, 0, 0), battens, int(z * 10), bow=0.0)
    ang = math.atan2(1.2, W - 0.12)
    plank("brace", math.hypot(1.2, W - 0.12), 0.1, 0.03, (W / 2, 0.035, 0.9), (0, -ang, 0), battens, 3, bow=0.0)
    irn = iron("door_iron")
    for z in (0.3, 1.5):
        strap = G.poly2d([(0.0, -0.022), (0.66, -0.016), (0.72, -0.035), (0.76, 0.0), (0.72, 0.035), (0.66, 0.016),
                          (0.0, 0.022)])
        s = G.extrude(f"hinge{z}", G.shape_polys(strap), 0.006, bev=0.0015, plane="XZ", mat=irn)
        G.xform(s, (0.0, -0.024, z))
        G.cyl(f"knuckle{z}", 0.016, 0.1, loc=(0.0, -0.01, z - 0.05), segs=16, mat=irn)
        for k, xx in enumerate((0.1, 0.3, 0.5, 0.7)):
            G.sphere(f"nail{z}{k}", 0.008, loc=(xx, -0.027, z), segs=10, rings=5, mat=irn, scale=(1, 0.5, 1))
    G.torus("ring", 0.05, 0.007, loc=(0.78, -0.04, 0.95), rot=(pi / 2, 0, 0), segs=32, rsegs=10, mat=irn)
    G.box("ring_plate", (0.07, 0.006, 0.09), loc=(0.78, -0.023, 1.0), bev=0.002, mat=irn)


@asset(res=2048, view=(-20, 10), pivot="origin", kind="kit", title="Wall wattle and daub 2m", max_tris=80000)
def wall_wattle_2m():
    beams = beam_oak("wattle_beam_oak")
    _wall_frame(beams, beams)
    hz = hazel("wattle_hazel")
    stakes = np.linspace(0.12, 1.88, 7)
    for i, x in enumerate(stakes):
        G.cyl(f"stake{i}", 0.02, WALL_H - 0.3, loc=(x, 0, 0.15), segs=10, mat=hz)
    zs = np.arange(0.28, WALL_H - 0.22, 0.075)
    for j, z in enumerate(zs):
        xs = np.linspace(0.0, GRID, 60)
        path = [(x, 0.028 * math.cos(pi * (x - 0.12) / (stakes[1] - stakes[0]) + j * pi), z) for x in xs]
        G.tube(f"withy{j}", path, 0.013, n=6, mat=hz)
    dm = daub("daub")
    for sgn in (1, -1):
        slab = G.box(f"daub{sgn}", (GRID - 0.02, 0.05, WALL_H - 0.42), loc=(1.0, sgn * 0.058, WALL_H / 2),
                     mat=dm, subdiv=5, bev=0.01)

        def f(co, s=sgn):
            face = np.sign(co[:, 1] - s * 0.058) == s
            co[face, 1] += s * (0.022 * snoise(co[face] * [1, 0, 1], 40 + s, 2.0)
                                + 0.008 * snoise(co[face] * [1, 0, 1], 50 + s, 9.0))
            return co
        deform(slab, f)
        if sgn < 0:
            for k, (cx, cz, r) in enumerate(((0.45, 0.55, 0.3), (1.45, 1.75, 0.2), (1.25, 0.4, 0.14),
                                             (0.9, 1.3, 0.1))):
                blob = rock(f"hole{k}", (r * 2, 0.2, r * 1.6), (cx, -0.06, cz), None, 70 + k, flat_bottom=False,
                            rough=0.3)
                G.boolean(slab, blob)


@asset(res=2048, view=(-60, 10), pivot="origin", kind="kit", title="Gable wall 8m")
def gable_wall_8m():
    boards = oak("gable_oak", axis="Z", weather=0.8, cracks=0.6)
    y = -HALF
    for i, w in enumerate(split_widths(SPAN, 0.2, 0.3, 33)):
        y0, y1 = y, y + w
        top0, top1 = RISE - abs(y0), RISE - abs(y1)
        if abs((y0 + y1) / 2) < 0.45:
            top0 = top1 = min(top0, top1, 3.05)        # smoke hole under the ridge
        poly = [(y0, -0.12), (y1, -0.12), (y1, top1), (y0, top0)]
        b = G.extrude(f"g{i}", [poly], 0.055, bev=0.006, plane="YZ", mat=boards)
        G.tag_random(b, (i * 0.618) % 1.0)
        G.xform(b, (0.004 * ((i * 7) % 3 - 1), 0, 0))
        y += w + 0.004
    bat = beam_oak("gable_batten", axis="Y")
    for zb, Lb in ((1.2, 5.4), (2.55, 2.6)):
        hewn(f"batten{zb}", Lb, 0.1, 0.12, (-0.07, 0, zb), (0, 0, pi / 2), bat, int(zb * 10), bow=0.0)
        pegs([(-0.13, yy, zb) for yy in np.linspace(-Lb / 2 + 0.2, Lb / 2 - 0.2, 6)], (0, pi / 2, 0), bat, L=0.05,
             name=f"bp{zb}")
    hewn("hole_sill", 0.95, 0.1, 0.1, (-0.07, 0, 3.02), (0, 0, pi / 2), bat, 77, bow=0.0)


# ================================================================== frame
@asset(res=1024, view=(-30, 8), pivot="origin", kind="kit", title="Corner post")
def post_corner():
    hewn("post", WALL_H, 0.28, 0.28, (0, 0, WALL_H / 2), (0, pi / 2, 0), beam_oak("post_oak", axis="Z"), 3,
         bow=0.01)


@asset(res=2048, view=(-20, 6), pivot="origin", kind="kit", title="Carved hall post")
def post_hall():
    Hh = 4.0
    prof = [(0, 0)] + [(0.175 - 0.02 * (z / Hh) + 0.006 * math.sin(pi * z / Hh), z)
                       for z in np.linspace(0, Hh - 0.25, 40)] + [(0, Hh - 0.25)]
    V = lambda z: G.lathe_v(prof, z)  # noqa: E731
    band = D.Canvas(2048)
    for (z0, z1) in ((1.55, 1.95), (3.0, 3.25)):
        sub = knot_band("tmp", n=5)
        from PIL import Image
        im = Image.open(sub).resize((2048, max(8, int((V(z1) - V(z0)) * 2048))))
        band.im.paste(im.resize((band.W * band.ss, max(8, int((V(z1) - V(z0)) * band.H * band.ss)))),
                      (0, int((1 - V(z1)) * band.H * band.ss)))
    carve = band.save("post_carving")
    wd = oak("hall_post_oak", axis="Z", weather=0.35, cracks=0.6,
             layers=[dict(mask=carve, height=-1.2, color=(0.035, 0.022, 0.014)),
                     dict(mask=carve, invert=False, color=(0.22, 0.03, 0.015), opacity=0.35)])
    G.lathe("post", prof, segs=40, mat=wd)
    hewn("capital", 0.5, 0.36, 0.25, (0, 0, Hh - 0.125), (0, 0, 0), beam_oak("capital_oak"), 4, bow=0.0)


@asset(res=1024, view=(-25, 12), pivot="origin", kind="kit", title="Beam 2m")
def beam_2m():
    hewn("beam", GRID, 0.24, 0.24, (1.0, 0, 0.12), (0, 0, 0), beam_oak("beam_oak"), 9)


@asset(res=2048, view=(-70, 12), pivot="origin", kind="kit", title="Tie beam 8m")
def tie_beam_8m():
    hewn("tie", SPAN + 0.6, 0.26, 0.3, (0, 0, 0.15), (0, 0, pi / 2), beam_oak("tie_oak", axis="Y"), 19, bow=0.03)
    pegs([(-0.16, y, 0.15) for y in (-HALF, HALF)], (0, pi / 2, 0), beam_oak("tie_peg", axis="X"), r=0.02, L=0.32)


@asset(res=2048, view=(-75, 8), pivot="origin", kind="kit", title="Rafter pair 8m")
def rafter_pair_8m():
    mt = beam_oak("rafter_oak", axis="Y")
    for s in (1, -1):
        y0, z0 = s * (HALF + EAVE), -EAVE
        y1, z1 = s * 0.08, RISE - 0.08
        L = math.hypot(y1 - y0, z1 - z0) + 0.35
        cy, cz = (y0 + y1) / 2 - s * 0.07, (z0 + z1) / 2 - 0.07
        hewn(f"rafter{s}", L, 0.2, 0.14, (0, cy, cz), (0, -pi / 4, -s * pi / 2), mt, 30 + s, bow=0.006)
    hewn("collar", 3.4, 0.12, 0.18, (0, 0, 2.3), (0, 0, pi / 2), mt, 40, bow=0.0)
    pegs([(0.09, s * 1.6, 2.3) for s in (1, -1)] + [(0.09, 0, RISE - 0.35)], (0, pi / 2, 0), mt, r=0.018, L=0.2)


# =================================================================== roof
@asset(res=4096, view=(-35, 25), pivot="origin", kind="kit", title="Thatch roof 2m", max_tris=90000)
def roof_thatch_2m():
    """Water-reed/straw thatch laid in overlapping courses on the -Y slope.
    Outer surface is continuous-looking: each course steps out only a few cm,
    butts are ragged, the whole coat sags and swells slightly."""
    th = thatch("thatch")
    rng = np.random.default_rng(4)
    nx = 48
    step, clen = 0.36, 1.05
    k = 0
    s0 = 0.0
    while s0 < SLOPE_L - 0.15:
        s1 = min(s0 + clen, SLOPE_L + 0.08)
        ns = 7
        butt = 0.36 if k == 0 else 0.30
        verts, faces = [], []
        for side in (0, 1):
            for i in range(nx + 1):
                x = -0.03 + (GRID + 0.06) * i / nx
                for j in range(ns + 1):
                    t = j / ns
                    s = s0 + (s1 - s0) * t
                    if j == 0:
                        s += 0.012 * math.sin(x * 17 + k * 2.3) + 0.008 * rng.normal()
                    off = (butt - 0.05 * t ** 0.8) if side == 0 else 0.0
                    if side == 0:
                        off += 0.025 * math.sin(x * 2.1 + s * 1.3 + k) + 0.012 * rng.normal() * (j > 0)
                    y = -(HALF + EAVE) + s / math.sqrt(2)
                    z = -EAVE + s / math.sqrt(2)
                    verts.append((x, y - off / math.sqrt(2), z + off / math.sqrt(2)))
        N = (nx + 1) * (ns + 1)

        def vid(side, i, j):
            return side * N + i * (ns + 1) + j
        for i in range(nx):
            for j in range(ns):
                faces.append([vid(0, i, j), vid(0, i + 1, j), vid(0, i + 1, j + 1), vid(0, i, j + 1)])
                faces.append([vid(1, i, j + 1), vid(1, i + 1, j + 1), vid(1, i + 1, j), vid(1, i, j)])
        for i in range(nx):
            faces.append([vid(1, i, 0), vid(1, i + 1, 0), vid(0, i + 1, 0), vid(0, i, 0)])
            faces.append([vid(0, i, ns), vid(0, i + 1, ns), vid(1, i + 1, ns), vid(1, i, ns)])
        for i in (0, nx):
            for j in range(ns):
                faces.append([vid(0, i, j), vid(0, i, j + 1), vid(1, i, j + 1), vid(1, i, j)])
        G.mesh(f"course{k}", verts, faces, None, th)
        k += 1
        s0 += step


@asset(res=2048, view=(-30, 25), pivot="origin", kind="kit", title="Ridge 2m")
def roof_ridge_2m():
    th = thatch("ridge_thatch", mode="planar")
    W = 1.05

    def top(y):
        return RISE - abs(y) + 0.30 + 0.22 * math.exp(-(y / 0.45) ** 2)
    secs = []
    for x in np.linspace(-0.03, GRID + 0.03, 36):
        ring = [(x, y, top(y) + 0.02 * math.sin(x * 3.1 + y * 4)) for y in np.linspace(-W, W, 40)]
        ring += [(x, y, RISE - abs(y) + 0.12) for y in np.linspace(W, -W, 20)]
        secs.append(ring)
    G.loft("saddle", secs, th, closed=True, cap=True)
    hz = hazel("ridge_hazel")
    for yy in (-0.72, -0.4, 0.4, 0.72):
        G.tube(f"ligger{yy}", [(x, yy, top(yy) + 0.012) for x in np.linspace(-0.02, GRID + 0.02, 30)], 0.014, n=8,
               mat=hz)
    for i in range(10):
        x0 = 0.05 + i * 0.2
        for (ya, yb) in ((-0.72, -0.4), (0.4, 0.72)):
            for d in (1, -1):
                a = (x0, ya, top(ya) + 0.02)
                b = (x0 + 0.1 * d, yb, top(yb) + 0.02)
                G.tube(f"spar{i}{ya}{d}", [a, b], 0.009, n=6, mat=hz)


@asset(res=2048, view=(-80, 12), pivot="origin", kind="kit", title="Gable dragon finials")
def gable_finial():
    c = D.Canvas(2048)
    knot = knot_band("finial_knot", n=10, v0=0.40, v1=0.60, width=0.006)
    board_m = oak("finial_oak", axis="Y", weather=0.4, cracks=0.5,
                  layers=[dict(mask=knot, height=-1.0, color=(0.03, 0.02, 0.012)),
                          dict(mask=knot, color=(0.25, 0.03, 0.015), opacity=0.4)])
    _ = c
    for s in (1, -1):
        # board runs from the eave up past the ridge, ending in a dragon head
        y0, z0 = s * (HALF + EAVE + 0.05), -EAVE - 0.05
        d = np.array([-s, 1.0]) / math.sqrt(2)
        nrm = np.array([1.0, s * 1.0]) / math.sqrt(2) * (1 if s < 0 else 1)
        Lb = SLOPE_L + 0.22 + 0.9
        p0 = np.array([y0, z0])
        w = 0.36
        pts = [p0 - nrm * w / 2, p0 + d * Lb - nrm * w / 2]
        # dragon head beyond the crossing, curling outward
        head = _dragon(p0 + d * Lb, d, -s)
        pts += head
        pts += [p0 + d * Lb + nrm * w / 2, p0 + nrm * w / 2]
        poly = [(float(p[0]), float(p[1])) for p in pts]
        from shapely.geometry import Polygon
        pg = Polygon(poly).buffer(0.01).buffer(-0.01).difference(_dragon_eye(p0 + d * Lb, d, -s)).difference(_dragon_eye(p0 + d * Lb, d, -s))
        b = G.extrude(f"board{s}", G.shape_polys(pg), 0.06, bev=0.01, bres=2, plane="YZ", mat=board_m)
        G.xform(b, (0.03 * s, 0, 0))


def _dragon(base, d, side):
    """Carved dragon-head profile (neck at `base`, snout along d); returns outline points."""
    n = np.array([-d[1], d[0]]) * side
    spec = [(0.0, 0.18), (0.22, 0.24), (0.4, 0.33), (0.5, 0.46), (0.56, 0.5), (0.6, 0.4), (0.72, 0.3),
            (0.92, 0.24), (1.08, 0.17), (1.16, 0.08), (1.1, 0.03), (0.96, 0.03), (0.82, 0.0), (0.98, -0.04),
            (1.1, -0.07), (1.12, -0.12), (0.96, -0.16), (0.7, -0.19), (0.4, -0.21), (0.15, -0.2), (0.0, -0.18)]
    return [base + d * a * 0.95 + n * b * 0.95 for (a, b) in spec]


def _dragon_eye(base, d, side):
    n = np.array([-d[1], d[0]]) * side
    c = base + d * 0.76 + n * 0.14
    return G.circle2d(float(c[0]), float(c[1]), 0.035, 24)


# ================================================================ interior
@asset(res=2048, view=(-30, 32), pivot="origin", kind="kit", title="Long hearth")
def hearth_long():
    st = fieldstone("hearth_stone", moss_z=-1)
    rng = np.random.default_rng(8)
    k = 0
    for (x0, y0, x1, y1) in ((-1.0, -0.45, 1.0, -0.45), (-1.0, 0.45, 1.0, 0.45), (-1.0, -0.45, -1.0, 0.45),
                             (1.0, -0.45, 1.0, 0.45)):
        L = math.hypot(x1 - x0, y1 - y0)
        n = int(L / 0.24)
        for i in range(n + 1):
            t = i / n
            rock(f"kerb{k}", (0.24, 0.18, 0.16), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.06), st, 500 + k,
                 rot=(0, 0, rng.random() * pi))
            k += 1
    ash = M.stone("ash", c1=(0.30, 0.29, 0.27), c2=(0.08, 0.075, 0.07), kind="limestone", rough=0.95, chips=0.0,
                  dirt=0.5, scale=4)
    bed = G.box("ash_bed", (1.9, 0.8, 0.06), loc=(0, 0, 0.02), mat=ash, subdiv=4)
    deform(bed, lambda co: co + np.array([0, 0, 1.0])[None, :] * (0.015 * snoise(co, 9, 6.0))[:, None] * (co[:, 2:3] > 0.03))
    char = M.wood("char", light=(0.02, 0.017, 0.015), dark=(0.004, 0.004, 0.004), axis="X", cracks=1.0, dirt=0.0,
                  weather=0.0, rough=0.7)
    ember = M.emissive("embers", color=(1.0, 0.28, 0.05), strength=6.0, base=(0.1, 0.03, 0.01))
    for i in range(4):
        a = rng.normal(0, 0.5)
        G.cyl(f"log{i}", 0.05 + 0.02 * rng.random(), 0.7, loc=(-0.3 + 0.2 * i, -0.2 + 0.13 * i, 0.08),
              rot=(0, pi / 2, a), segs=16, bev=0.01, mat=char)
    for i in range(24):
        rock(f"ember{i}", (0.04, 0.035, 0.025), (-0.4 + 0.8 * rng.random(), -0.25 + 0.5 * rng.random(), 0.055), ember,
             800 + i, rough=0.3)
    irn = iron("tripod_iron")
    top = np.array([0.35, 0.0, 1.25])
    for i in range(3):
        a = 2 * pi * i / 3
        G.tube(f"leg{i}", [top, top + np.array([0.55 * math.cos(a), 0.55 * math.sin(a), -1.22])], 0.012, n=8, mat=irn)
    for i in range(7):
        G.torus(f"link{i}", 0.02, 0.005, loc=(0.35, 0.0, 1.2 - i * 0.05), rot=(0, 0, pi / 2 * (i % 2)) if False else
                ((pi / 2) * (i % 2), 0, 0), segs=12, rsegs=6, mat=irn)
    G.lathe("cauldron", G.curve_pts([(0, 0.46), (0.12, 0.47), (0.2, 0.55), (0.21, 0.66), (0.19, 0.74), (0.2, 0.76),
                                     (0.185, 0.76), (0.175, 0.74), (0.19, 0.66), (0.18, 0.56), (0.11, 0.48),
                                     (0, 0.475)], 40), segs=48, mat=irn)
    G.xform(G.all_meshes()[0], (0, 0, 0)) if False else None
    for o in G.all_meshes():
        if o.name == "cauldron":
            G.xform(o, (0.35, 0.0, 0.0))
    G.tube("bail", [(0.35 + 0.2 * math.cos(t), 0.0, 0.76 + 0.3 * math.sin(t)) for t in np.linspace(0, pi, 30)],
           0.006, n=6, mat=irn)


@asset(res=2048, view=(-35, 22), pivot="origin", kind="kit", title="Sleeping bench 2m")
def bench_2m():
    top_m = oak("bench_oak", axis="X", weather=0.2, cracks=0.3)
    post_m = beam_oak("bench_post", axis="Z")
    D_ = 1.1
    y = -D_
    for i, w in enumerate(split_widths(D_, 0.2, 0.26, 12)):
        plank(f"top{i}", GRID, w, 0.045, (1.0, y + w / 2, 0.45 - 0.0225), (0, 0, 0), top_m, 60 + i, bow=0.003)
        y += w + 0.005
    plank("front", GRID, 0.3, 0.04, (1.0, -D_ - 0.02, 0.28), (pi / 2, 0, 0), top_m, 70, bow=0.004)
    for x in (0.08, 1.92):
        for yy in (-D_ + 0.06, -0.06):
            hewn(f"post{x}{yy}", 0.43, 0.1, 0.1, (x, yy, 0.215), (0, pi / 2, 0), post_m, int(abs(x * 100 + yy * 10)), bow=0)
    fur = M.fabric("sheepskin", color=(0.52, 0.47, 0.38), weave=3500, rough=0.97, fuzz=1.0, sheen=1.0, wear=0.0)
    pelt = G.box("pelt", (1.1, 0.8, 0.05), loc=(0.8, -0.55, 0.48), mat=fur, subdiv=4, bev=0.02)
    deform(pelt, lambda co: co + np.array([0, 0, 1.0])[None, :] * (0.02 * snoise(co * [3, 3, 0], 3, 2.0))[:, None])
    G.displace(pelt, 0.012, scale=0.02)
    wool = M.fabric("wool_blanket", color=(0.20, 0.05, 0.025), color2=(0.26, 0.2, 0.1), weave=900, rough=0.9)
    bl = G.box("blanket", (0.5, 0.4, 0.12), loc=(1.6, -0.3, 0.51), mat=wool, subdiv=3, bev=0.04)
    G.displace(bl, 0.01, scale=0.05)


# =================================================================== props
@asset(res=2048, view=(-30, 22), pivot="origin", kind="prop", title="Hay pile", max_tris=90000)
def hay_pile():
    stm = straw("hay")
    base = G.sphere("mound", 1.0, segs=48, rings=24, mat=stm, scale=(0.75, 0.55, 0.42))
    deform(base, lambda co: np.c_[co[:, 0], co[:, 1], np.maximum(co[:, 2], 0)] +
           (0.06 * snoise(co * 2, 5, 3.0))[:, None] * (co / (np.linalg.norm(co, axis=1, keepdims=True) + 1e-9)))
    rng = np.random.default_rng(6)
    for i in range(650):
        u, v = rng.random() * 2 * pi, rng.random() * pi / 2
        p = np.array([0.75 * math.cos(u) * math.sin(v + 0.3), 0.55 * math.sin(u) * math.sin(v + 0.3),
                      0.42 * math.cos(v + 0.3)]) * (0.95 + 0.1 * rng.random())
        p[2] = max(p[2], 0.01)
        d = rng.normal(size=3)
        d[2] *= 0.3
        d /= np.linalg.norm(d)
        L = 0.15 + 0.35 * rng.random()
        mid = p + d * L / 2 + np.array([0, 0, 0.02 * rng.normal()])
        G.tube(f"s{i}", [p, mid, p + d * L], 0.0022, n=4, mat=stm)


@asset(res=1024, view=(-25, 12), pivot="origin", kind="prop", title="Hay sheaf")
def hay_sheaf():
    stm = straw("sheaf_straw")
    rng = np.random.default_rng(9)
    for i in range(260):
        r = 0.11 * math.sqrt(rng.random())
        a = rng.random() * 2 * pi
        x, y = r * math.cos(a), r * math.sin(a)
        spread = 1.6 + 0.4 * rng.random()
        path = [(x * spread, y * spread, 0.0), (x, y, 0.45), (x * spread * 1.2, y * spread * 1.2, 0.9 + 0.08 * rng.random())]
        G.tube(f"st{i}", G.curve_pts(path, 5), 0.0028, n=4, mat=stm)
    rope = M.fabric("twine", color=(0.22, 0.16, 0.08), weave=1500, rough=0.85)
    hel = [(0.122 * math.cos(t), 0.122 * math.sin(t), 0.43 + 0.04 * t / (6 * pi)) for t in np.linspace(0, 6 * pi, 120)]
    G.tube("band", hel, 0.006, n=8, mat=rope)


@asset(res=2048, view=(-30, 20), pivot="origin", kind="prop", title="Plank stack")
def plank_stack():
    wd = oak("stack_oak", axis="X", weather=0.5, cracks=0.5)
    st = beam_oak("sticker_oak", axis="Y")
    z = 0.0
    for layer in range(3):
        for k, y in enumerate((-0.12, 0.3)):
            hewn(f"sticker{layer}{k}", 0.8, 0.05, 0.05, (y * 3 - 0.5, 0.05, z + 0.025), (0, 0, pi / 2), st,
                 layer * 10 + k, bow=0)
        z += 0.05
        y = -0.35
        for i, w in enumerate(split_widths(0.75, 0.16, 0.24, 100 + layer, gap=0.03)):
            plank(f"p{layer}{i}", 2.4, w, 0.045, (0.0, y + w / 2, z + 0.0225), (0, 0, 0.01 * layer), wd,
                  200 + layer * 10 + i, bow=0.006)
            y += w + 0.03
        z += 0.045


@asset(res=2048, view=(-30, 18), pivot="origin", kind="prop", title="Firewood pile")
def log_pile():
    bark = M.wood("bark", light=(0.08, 0.06, 0.045), dark=(0.02, 0.016, 0.012), axis="X", cracks=1.0, weather=0.5,
                  ring_scale=8, bump_strength=0.6, pores=0.8)
    endg = M.wood("end_grain", light=(0.35, 0.25, 0.15), dark=(0.16, 0.1, 0.05), axis="X", ring_scale=70,
                  cracks=0.6, weather=0.2)
    rng = np.random.default_rng(2)
    rows = [(0.0, 5), (0.15, 4), (0.29, 3), (0.42, 2)]
    for r, (z, n) in enumerate(rows):
        for i in range(n):
            y = (i - (n - 1) / 2) * 0.16
            R = 0.07 + 0.012 * rng.random()
            L = 0.5 + 0.05 * rng.random()
            x = 0.03 * rng.normal()
            side = G.cyl(f"bark{r}{i}", R, L, loc=(x - L / 2, y, z + R), rot=(0, pi / 2, 0), segs=18, mat=bark,
                         caps=False)
            _ = side
            for e in (0, 1):
                cap = G.cyl(f"end{r}{i}{e}", R * 0.97, 0.004, loc=(x - L / 2 + e * (L - 0.004), y, z + R),
                            rot=(0, pi / 2, 0), segs=18, mat=endg)
                _ = cap


@asset(res=2048, view=(-25, 20), pivot="origin", kind="prop", title="Fieldstones")
def stones_loose():
    st = fieldstone("loose_stone", moss_z=0.12)
    rng = np.random.default_rng(13)
    specs = [((0.5, 0.4, 0.3), (0, 0)), ((0.35, 0.3, 0.22), (0.45, 0.15)), ((0.28, 0.25, 0.18), (-0.38, 0.22)),
             ((0.2, 0.18, 0.14), (0.2, -0.35)), ((0.16, 0.14, 0.1), (-0.2, -0.32)), ((0.12, 0.1, 0.08), (0.55, -0.2)),
             ((0.6, 0.45, 0.28), (-0.1, 0.65))]
    for i, (d, (x, y)) in enumerate(specs):
        rock(f"stone{i}", d, (x, y, d[2] * 0.42), st, 900 + i, rot=(0, 0, rng.random() * pi), rough=0.18)
