"""Aztec / Mexica jungle (c. 1400-1521) asset set."""
import math

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge.pipeline import asset

pi = math.pi
TURQ = (0.06, 0.40, 0.36)
JADE = (0.04, 0.24, 0.12)
RED = (0.40, 0.04, 0.02)
OCHRE = (0.55, 0.30, 0.07)


def obsidian(name="obsidian", scale=20):
    return M.gem(name, color=(0.006, 0.006, 0.007), color2=(0.02, 0.022, 0.025), veins=0.05, rough=0.06,
                 cloud=0.3, scale=scale, dirt=0.1)


def basalt(name="basalt", **kw):
    kw.setdefault("rough", 0.8)
    return M.stone(name, c1=(0.16, 0.15, 0.14), c2=(0.07, 0.068, 0.065), kind="limestone", chips=0.5, dirt=0.6,
                   **kw)


def gold(name="gold", **kw):
    return M.metal(name, "gold", rough=0.25, wear=0.5, dirt=0.7, dirt_color=(0.05, 0.03, 0.01), scale=5, **kw)


def mosaic(name, colors, scale=180.0, grout=(0.05, 0.04, 0.03), rough=0.25):
    """Turquoise / shell / jade tessera mosaic (object-space voronoi tiles)."""
    nb = M.NB(name)
    cell = nb.voronoi(scale, feature="F1", out="Color", rand=0.9)
    edge = nb.voronoi(scale, feature="DISTANCE_TO_EDGE", rand=0.9)
    g = nb.gray(cell)
    stops = [(i / max(1, len(colors) - 1), c) for i, c in enumerate(colors)]
    col = nb.ramp(g, stops, interp="CONSTANT")
    col = nb.mix(col, nb.hsv(col, 0.5, 1.0, 0.75), nb.noise(scale * 2, 4, 0.6))
    gm = nb.mr(edge, 0.0, 0.06, 1, 0)
    col = nb.mix(col, grout, gm)
    col = nb.mix(col, (0.03, 0.02, 0.012), nb.mul(nb.cavity(0.01), 0.6, clamp=True))
    height = nb.sub(nb.mul(nb.ss(edge, 0.0, 0.12), 0.6), nb.mul(nb.noise(scale * 0.5, 3), 0.2))
    return nb.done(col, nb.mixf(rough, 0.8, gm), 0.0, nb.bump(height, 0.5, 0.001))


# ------------------------------------------------------------------ 1 ------
@asset(res=2048, view=(0, 8), pose=(0, 90, 0), pivot="bottom", kind="weapon", title="Macuahuitl")
def macuahuitl():
    wood = M.wood("macua_wood", light=(0.22, 0.12, 0.05), dark=(0.07, 0.035, 0.015), axis="Z", dirt=0.6, wear=0.5,
                  layers=[dict(mask=_glyph_band(), color=RED, rough=0.8, chip=0.4)])
    paddle = G.poly2d([(-0.018, 0.0), (0.018, 0.0), (0.02, 0.28), (0.042, 0.36), (0.046, 0.82), (0.034, 0.9),
                       (-0.034, 0.9), (-0.046, 0.82), (-0.042, 0.36), (-0.02, 0.28)]).buffer(0.004)
    G.extrude("paddle", G.shape_polys(paddle), 0.022, bev=0.006, bres=3, plane="XZ", mat=wood)
    obs = obsidian("macua_obsidian")
    rng = np.random.default_rng(3)
    for s in (1, -1):
        for i, z in enumerate(np.linspace(0.40, 0.86, 12)):
            w = 0.028 + 0.006 * rng.random()
            h = 0.034 + 0.008 * rng.random()
            blade = G.poly2d([(0, -w / 2), (h * 0.8, -w / 2 + 0.004), (h, 0.0 + 0.004 * rng.normal()),
                              (h * 0.8, w / 2 - 0.004), (0, w / 2)])
            b = G.extrude(f"obs{s}{i}", G.shape_polys(blade), 0.006, bev=0.0012, plane="XZ", mat=obs)
            G.xform(b, (s * 0.034, 0, z), rot=(0, 0, 0 if s > 0 else pi))
    leather = M.leather("wrist_thong", color=(0.2, 0.1, 0.05), scale=4)
    hel = [(0.022 * math.cos(t), 0.013 * math.sin(t), 0.02 + 0.2 * t / (16 * pi)) for t in np.linspace(0, 16 * pi, 500)]
    G.tube("wrap", hel, 0.0028, n=8, mat=leather)
    loop = [(0.0, 0.012 + 0.03 * math.sin(t), -0.03 * (1 - math.cos(t)) + 0.01) for t in np.linspace(0, 2 * pi, 40)]
    G.tube("lanyard", loop, 0.0025, n=8, mat=leather)


def _glyph_band():
    c = D.Canvas(1024)
    c.step_fret(0.40, 0.46, n=6).step_fret(0.86, 0.92, n=6)
    return c.blur(1).save("fret")


# ------------------------------------------------------------------ 2 ------
@asset(res=2048, view=(15, 8), pivot="center", kind="weapon", title="Chimalli feather shield")
def chimalli():
    R = 0.34
    c = D.Canvas(2048)
    # xicalcoliuhqui (step-fret spiral) design in gold on turquoise feathers
    for k in range(4):
        a = k * pi / 2
        pts = []
        for s in range(8):
            r = 0.1 + 0.045 * s
            aa = a + 0.28 * s
            pts += [(0.5 + r * math.cos(aa), 0.5 + r * math.sin(aa)), (0.5 + r * math.cos(aa + 0.28),
                                                                      0.5 + r * math.sin(aa + 0.28))]
        c.line(pts, 0.03)
    c.circle(0.5, 0.5, 0.08)
    design = c.blur(1).save("fret_spiral")
    feathers = M.NB("feather_mosaic")
    nb = feathers
    v = nb.voronoi(420, nb.mapv(scale=(1, 1, 3)), feature="F1", out="Distance")
    col = nb.mix(TURQ, nb.hsv(TURQ, 0.5, 1.2, 0.6), nb.ss(v, 0.2, 0.8))
    col, r, m, h = M.apply_layers(nb, col, 0.55, 0.0, nb.mul(v, 0.4),
                                  [dict(mask=design, color=(0.75, 0.52, 0.12), rough=0.35, metal=0.9, height=0.4)])
    fm = nb.done(col, r, m, nb.bump(h, 0.4, 0.001), **{"Sheen Weight": 0.6})
    disc = G.lathe("disc", [(0, 0.0), (R - 0.004, 0.0), (R, 0.004), (R - 0.004, 0.012), (0, 0.016)], segs=128,
                   mat=fm)
    G.planar_uv(disc, "Z")
    au = gold("chimalli_gold")
    G.torus("rim", R, 0.006, loc=(0, 0, 0.006), segs=160, mat=au)
    fringe = M.feather("fringe", c1=(0.02, 0.28, 0.1), c2=(0.03, 0.35, 0.15), tip=(0.5, 0.35, 0.02))
    tmpl = G.extrude("feather", G.shape_polys(G.poly2d([(0, -0.012), (0.12, -0.004), (0.13, 0.0), (0.12, 0.004),
                                                         (0, 0.012)])), 0.002, bev=0.0006, plane="XY", mat=fringe)
    G.planar_uv(tmpl, "Z")
    tr = []
    for i in range(19):
        a = -pi / 2 - 0.9 + 1.8 * i / 18
        tr.append(((R * 0.92 * math.cos(a), R * 0.92 * math.sin(a), -0.004), (0, 0, a), None))
    G.scatter(tmpl, tr, "fringe")
    G.transform_all(rot=G.rotd(90, 0, 0))


# ------------------------------------------------------------------ 3 ------
@asset(res=2048, view=(0, 10), pivot="center", kind="artifact", title="Sun stone")
def sun_stone():
    c = D.Canvas(2048)
    c.circle(0.5, 0.5, 0.1, fill=None, outline=255, width=0.012)
    c.text(0.5, 0.5, "☉", size=0.12, font="sans")
    for k in range(4):
        a = pi / 4 + k * pi / 2
        c.poly([(0.5 + 0.11 * math.cos(a - 0.3), 0.5 + 0.11 * math.sin(a - 0.3)),
                (0.5 + 0.2 * math.cos(a), 0.5 + 0.2 * math.sin(a)),
                (0.5 + 0.11 * math.cos(a + 0.3), 0.5 + 0.11 * math.sin(a + 0.3))])
    for ring, n in ((0.24, 20), (0.3, 40), (0.37, 8), (0.44, 60)):
        c.circle(0.5, 0.5, ring, fill=None, outline=255, width=0.006)
        for k in range(n):
            a = 2 * pi * k / n
            if n == 20:
                c.d.rectangle([c.px(0.5 + 0.27 * math.cos(a) - 0.015, 0.5 + 0.27 * math.sin(a) + 0.015),
                               c.px(0.5 + 0.27 * math.cos(a) + 0.015, 0.5 + 0.27 * math.sin(a) - 0.015)],
                              outline=255, width=c.pw(0.004))
            elif n == 40:
                c.circle(0.5 + 0.335 * math.cos(a), 0.5 + 0.335 * math.sin(a), 0.01)
            elif n == 8:
                c.poly([(0.5 + 0.3 * math.cos(a - 0.12), 0.5 + 0.3 * math.sin(a - 0.12)),
                        (0.5 + 0.43 * math.cos(a), 0.5 + 0.43 * math.sin(a)),
                        (0.5 + 0.3 * math.cos(a + 0.12), 0.5 + 0.3 * math.sin(a + 0.12))])
            else:
                c.line([(0.5 + 0.44 * math.cos(a), 0.5 + 0.44 * math.sin(a)),
                        (0.5 + 0.48 * math.cos(a + 0.04), 0.5 + 0.48 * math.sin(a + 0.04))], 0.006)
    relief = c.grow(2).blur(1.2).save("sunstone_relief")
    st = basalt("sunstone_basalt", scale=2, bump_strength=1.6,
                layers=[dict(mask=relief, height=1.0, invert=True, color=(0.05, 0.048, 0.045)),
                        dict(mask=lambda nb: nb.mul(nb.ss(nb.noise(6, 8, 0.7), 0.55, 0.7), 0.5),
                             color=(0.35, 0.08, 0.03), rough=0.9)])
    disc = G.lathe("disc", [(0, 0), (0.29, 0), (0.3, 0.01), (0.3, 0.07), (0.29, 0.08), (0, 0.08)], segs=160,
                   mat=st)
    G.planar_uv(disc, "Z")
    G.mod(disc, "subsurf", levels=2, subdivision_type="SIMPLE")
    G.apply_mods(disc)
    G.displace(disc, 0.006, image=relief, mid=0.2)
    G.transform_all(rot=G.rotd(90, 0, 0))


# ------------------------------------------------------------------ 4 ------
@asset(res=2048, view=(-18, 4), pivot="bottom", kind="artifact", title="Turquoise mosaic mask")
def mosaic_mask():
    """Xiuhtecuhtli-style turquoise mosaic face (front shell, ~17 cm)."""
    ms = mosaic("turquoise_mosaic", [TURQ, (0.12, 0.5, 0.45), (0.05, 0.3, 0.3), (0.2, 0.55, 0.5), JADE], scale=300)
    nu, nv = 64, 72
    verts, faces = [], []

    def g(x, z, cx, cz, sx, sz):
        return math.exp(-(((x - cx) / sx) ** 2) - (((z - cz) / sz) ** 2))
    for j in range(nv + 1):
        z = -0.09 + 0.18 * j / nv
        for i in range(nu + 1):
            a = -pi / 2 * 0.98 + pi * 0.98 * i / nu
            wz = 0.078 * math.sqrt(max(1 - (z / 0.095) ** 2, 0.02)) * (1 - 0.18 * max(0, -z / 0.09))
            x = wz * math.sin(a)
            depth = 0.06 * math.cos(a) * math.sqrt(max(1 - (z / 0.1) ** 2, 0.05))
            depth += 0.022 * g(x, z, 0, -0.005, 0.011, 0.03)            # nose
            depth += 0.008 * g(abs(x), z, 0.028, 0.03, 0.03, 0.008)     # brow ridge
            depth -= 0.012 * g(abs(x), z, 0.028, 0.012, 0.018, 0.011)   # eye sockets
            depth -= 0.01 * g(x, z, 0, -0.045, 0.024, 0.01)             # mouth
            depth += 0.006 * g(abs(x), z, 0.035, -0.025, 0.02, 0.02)    # cheeks
            verts.append((x, -depth, z))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append([a, a + 1, a + nu + 2, a + nu + 1])
    face = G.mesh("face", verts, faces, None, ms)
    G.solidify(face, 0.006, offset=1.0)
    mouth = G.poly2d([(-0.022, -0.05), (0.022, -0.05), (0.018, -0.04), (-0.018, -0.04)]).buffer(0.003)
    cut = G.extrude("mouth_cut", G.shape_polys(mouth), 0.2, plane="XZ")
    G.xform(cut, (0, -0.05, 0))
    G.boolean(face, cut)
    shell = M.gem("shell_white", color=(0.72, 0.68, 0.58), veins=0.1, rough=0.3, scale=60)
    pyr = M.metal("pyrite", "gold", color=(0.55, 0.45, 0.2), rough=0.25, wear=0.2, dirt=0.4, scale=40)
    from shapely import affinity
    for s_ in (1, -1):
        eye = affinity.scale(G.circle2d(0, 0, 1, 48), 0.017, 0.0085)
        e = G.extrude(f"eye{s_}", G.shape_polys(eye), 0.004, bev=0.0012, plane="XZ", mat=shell)
        G.xform(e, (s_ * 0.028, -0.058, 0.012))
        p = G.cyl(f"pupil{s_}", 0.0055, 0.002, loc=(0, 0, 0), rot=G.rotd(90, 0, 0), segs=24, bev=0.0006, mat=pyr)
        G.xform(p, (s_ * 0.028, -0.0605, 0.012))
    teeth = M.gem("shell_teeth", color=(0.8, 0.76, 0.66), veins=0, rough=0.3, scale=80)
    for i in range(8):
        x = -0.017 + 0.034 * i / 7
        G.box(f"tooth{i}", (0.0036, 0.008, 0.007), loc=(x, -0.05, -0.0415), bev=0.001, mat=teeth)
    for s_ in (1, -1):
        G.cyl(f"ear{s_}", 0.012, 0.006, loc=(s_ * 0.079, -0.005, 0.0), rot=G.rotd(0, 90, 0), segs=24, bev=0.002,
              mat=gold("ear_gold"))


# ------------------------------------------------------------------ 5 ------
@asset(res=2048, view=(20, 22), kind="vessel", title="Tripod bowl")
def tripod_bowl():
    prof = [(0, 0.03), (0.05, 0.03), (0.1, 0.045), (0.13, 0.07), (0.14, 0.1), (0.142, 0.104), (0.136, 0.104),
            (0.133, 0.1), (0.122, 0.074), (0.095, 0.052), (0.05, 0.04), (0, 0.038)]
    pts = G.curve_pts(prof, 120)
    V = lambda z: G.lathe_v(pts, z)  # noqa: E731
    c = D.Canvas(2048)
    c.step_fret(V(0.06), V(0.095), n=10)
    blk = c.blur(1).save("fret")
    r = D.Canvas(2048)
    r.hband(V(0.096), V(0.104)).hband(V(0.05), V(0.056))
    red = r.save("redbands")
    clay = M.ceramic("aztec_orange", color=(0.58, 0.28, 0.10), rough=0.6, speckle=0.3, chips=0.3, dirt=0.5,
                     layers=[dict(mask=red, color=RED, rough=0.7),
                             dict(mask=blk, color=(0.02, 0.018, 0.015), rough=0.65)])
    G.lathe("bowl", pts, segs=128, mat=clay)
    for k in range(3):
        a = 2 * pi * k / 3
        leg = G.lathe(f"leg{k}", G.curve_pts([(0, 0), (0.012, 0), (0.018, 0.02), (0.02, 0.04), (0, 0.045)], 20),
                      segs=24, mat=clay)
        G.xform(leg, (0.075 * math.cos(a), 0.075 * math.sin(a), 0.0), rot=(0, 0, a))
        G.xform(leg, scale=(1, 1, 1))
    cacao = M.stone("cacao_beans", c1=(0.2, 0.08, 0.04), c2=(0.1, 0.04, 0.02), kind="limestone", rough=0.5, scale=40)
    rng = np.random.default_rng(2)
    for i in range(14):
        a, rr = rng.random() * 2 * pi, 0.08 * math.sqrt(rng.random())
        G.sphere(f"bean{i}", 0.011, loc=(rr * math.cos(a), rr * math.sin(a), 0.048 + 0.006 * rng.random()),
                 segs=12, rings=8, mat=cacao, scale=(1.0, 0.6, 0.45))


# ------------------------------------------------------------------ 6 ------
@asset(res=2048, view=(25, 25), kind="tool", title="Metate and mano")
def metate_mano():
    st = basalt("metate_basalt", scale=4, layers=[dict(mask=lambda nb: nb.ss(nb.sep(nb.co())[2], 0.1, 0.13),
                                                        color=(0.2, 0.19, 0.18), rough=0.55)])
    top = G.box("slab", (0.46, 0.28, 0.06), loc=(0, 0, 0.1), bev=0.02, segs=4, mat=st, subdiv=3)
    for v in top.data.vertices:
        v.co.z -= 0.018 * (1 - (v.co.x / 0.23) ** 2) * (v.co.z > 0.11)
        v.co.z += 0.03 * (v.co.x / 0.23) * (v.co.z > 0.0)
    for x in (-0.16, 0.16):
        for y in (-0.09, 0.09):
            G.cyl(f"leg{x}{y}", 0.028, 0.08 + (0.03 if x > 0 else 0.0), loc=(x, y, 0.0), r2=0.022, segs=24,
                  bev=0.006, mat=st)
    mano = G.lathe("mano", G.curve_pts([(0, -0.15), (0.02, -0.148), (0.032, -0.12), (0.035, 0.0), (0.032, 0.12),
                                        (0.02, 0.148), (0, 0.15)], 40), segs=48, mat=st)
    G.xform(mano, (0.02, 0.0, 0.165), rot=G.rotd(90, 0, 0))
    corn = M.fabric("maize_flour", color=(0.62, 0.52, 0.3), weave=3000, rough=0.95, fuzz=0.8)
    pile = G.sphere("flour", 0.05, loc=(-0.12, 0.0, 0.118), segs=32, rings=16, mat=corn, scale=(1.2, 1.0, 0.3))
    G.displace(pile, 0.006, scale=0.02)


# ------------------------------------------------------------------ 7 ------
@asset(res=2048, view=(0, 20), pose=(0, 0, 0), pivot="bottom", kind="weapon", title="Tecpatl ritual knife")
def tecpatl():
    obs = obsidian("knife_flint")
    flake = dict(mask=lambda nb: nb.ss(nb.voronoi(40, feature="F1"), 0.15, 0.6), height=0.8)
    fl = M.stone("flint", c1=(0.42, 0.36, 0.28), c2=(0.2, 0.16, 0.12), kind="marble", veins=(0.12, 0.1, 0.08),
                 vein_amt=0.4, rough=0.3, scale=12, chips=0.6, dirt=0.3, polish=0.4, layers=[flake],
                 bump_strength=0.8)
    blade = G.poly2d([(0, 0.0), (0.028, 0.03), (0.036, 0.09), (0.02, 0.17), (0.0, 0.2), (-0.02, 0.17),
                      (-0.036, 0.09), (-0.028, 0.03)])
    b = G.extrude("blade", G.shape_polys(blade), 0.011, bev=0.005, bres=3, plane="XZ", mat=fl)
    G.xform(b, (0, 0, 0.1))
    _ = obs
    ms = mosaic("handle_mosaic", [TURQ, (0.7, 0.62, 0.5), RED, JADE, (0.05, 0.05, 0.05)], scale=300)
    grip = G.lathe("grip", G.curve_pts([(0, 0.0), (0.02, 0.0), (0.024, 0.02), (0.018, 0.06), (0.022, 0.1),
                                        (0.03, 0.11), (0, 0.112)], 40), segs=48, mat=ms)
    G.xform(grip, scale=(1, 0.7, 1))
    head = G.sphere("eagle_head", 0.022, loc=(0.0, -0.006, 0.02), segs=32, rings=16, mat=ms, scale=(1, 0.9, 1.2))
    beak = G.lathe("beak", [(0, 0), (0.008, 0.002), (0.004, 0.02), (0, 0.024)], segs=16, mat=gold("beak_gold"))
    G.xform(beak, (0, -0.02, 0.018), rot=G.rotd(80, 0, 0))
    _ = head


# ------------------------------------------------------------------ 8 ------
@asset(res=2048, view=(0, 10), pivot="bottom", kind="clothing", title="Quetzal feather headdress",
       max_tris=100000)
def feather_headdress():
    """Penacho: quetzal tail feathers fanned above a gold-studded band."""
    au = gold("penacho_gold")
    band_m = mosaic("band_mosaic", [TURQ, (0.08, 0.35, 0.33), (0.6, 0.45, 0.1)], scale=320)
    band = G.lathe("band", [(0.092, 0.0), (0.1, 0.0), (0.1, 0.075), (0.092, 0.075)], segs=64, mat=band_m,
                   angle=pi * 1.15)
    G.xform(band, rot=(0, 0, -pi * 0.075))
    for k in range(11):
        a = -pi * 0.05 + pi * 1.05 * k / 10
        G.cyl(f"disc{k}", 0.0105, 0.004, loc=(0.101 * math.cos(a), 0.101 * math.sin(a), 0.037),
              rot=(pi / 2, 0, a + pi / 2), segs=24, bev=0.0012, mat=au)
    quetzal = M.feather("quetzal", c1=(0.01, 0.20, 0.08), c2=(0.01, 0.12, 0.16), tip=(0.01, 0.06, 0.12))
    blue = M.feather("cotinga", c1=(0.02, 0.13, 0.42), c2=(0.02, 0.22, 0.55), tip=(0.01, 0.05, 0.2))
    red = M.feather("spoonbill", c1=(0.48, 0.07, 0.09), c2=(0.55, 0.16, 0.18), tip=(0.25, 0.02, 0.03))
    brown = M.feather("squirrel_cuckoo", c1=(0.25, 0.1, 0.03), c2=(0.35, 0.18, 0.06), tip=(0.05, 0.03, 0.02))
    rng = np.random.default_rng(5)
    layers = [(quetzal, 0.62, 0.028, 44, 0.02, 1.45), (blue, 0.32, 0.03, 36, 0.035, 1.35),
              (red, 0.2, 0.026, 32, 0.05, 1.25), (brown, 0.11, 0.022, 28, 0.065, 1.15)]
    for li, (mat, L, W, n, lift, spread) in enumerate(layers):
        for i in range(n):
            t = (i + 0.5 * rng.random()) / n
            a = (t - 0.5) * 2 * spread
            Li = L * (0.8 + 0.3 * rng.random()) * (1 - 0.15 * abs(t - 0.5))
            w = W * (0.85 + 0.3 * rng.random())
            pts = [(0.0, -w * 0.15)] + [(Li * u, w * math.sin(pi * min(u / 0.9, 1)) ** 0.7 * (1 - 0.35 * u) / 2 + 0.0)
                                         for u in np.linspace(0.05, 1, 14)]
            pts += [(Li * u, -w * math.sin(pi * min(u / 0.9, 1)) ** 0.7 * (1 - 0.35 * u) / 2)
                    for u in np.linspace(1, 0.05, 14)] + [(0.0, w * 0.15)]
            f = G.extrude(f"f{li}_{i}", G.shape_polys(G.poly2d(pts).buffer(0)), 0.0014, bev=0.0004, plane="XY",
                          mat=mat)
            G.planar_uv(f, "Z", stretch=True)
            G.deform(f, "BEND", angle=-(20 + 25 * rng.random()) * (1.3 - 0.2 * li), axis="Y")
            back = 0.35 + 0.12 * li + 0.08 * rng.normal()
            G.xform(f, (0, 0, 0), rot=(0, -pi / 2, 0))
            G.xform(f, (0, 0, 0), rot=(0, 0, pi / 2))
            G.xform(f, (0, 0, 0), rot=(back, 0, 0))
            G.xform(f, (0, 0, 0), rot=(0, a, 0))
            G.xform(f, (0.0, 0.07 - 0.012 * li, 0.06 + lift))
    G.cyl("shaft_bundle", 0.02, 0.05, loc=(0, 0.06, 0.05), segs=24, mat=au)


# ------------------------------------------------------------------ 9 ------
@asset(res=2048, view=(-25, 20), kind="instrument", title="Teponaztli slit drum")
def teponaztli():
    c = D.Canvas(2048)
    c.step_fret(0.18, 0.3, n=8).step_fret(0.7, 0.82, n=8)
    carve = c.blur(1.5).save("drum_carving")
    wood = M.wood("drum_wood", light=(0.26, 0.13, 0.05), dark=(0.08, 0.04, 0.015), axis="X", dirt=0.7, wear=0.5,
                  layers=[dict(mask=carve, height=-1.0, color=(0.05, 0.025, 0.01))])
    body = G.lathe("body", G.curve_pts([(0, -0.26), (0.07, -0.255), (0.085, -0.2), (0.09, 0.0), (0.085, 0.2),
                                        (0.07, 0.255), (0, 0.26)], 60), segs=64, mat=wood)
    G.xform(body, (0, 0, 0.09), rot=G.rotd(0, 90, 0))
    slot = G.poly2d([(-0.16, -0.004), (0.16, -0.004), (0.16, 0.004), (0.02, 0.004), (0.02, 0.035), (-0.02, 0.035),
                     (-0.02, 0.004), (-0.16, 0.004)]).union(
        G.poly2d([(-0.02, -0.035), (0.02, -0.035), (0.02, 0.0), (-0.02, 0.0)])).buffer(0.003)
    cut = G.extrude("slot", G.shape_polys(slot), 0.2, plane="XY")
    G.xform(cut, (0, 0, 0.12))
    G.boolean(body, cut)
    for s in (1, -1):
        head = G.sphere(f"jaguar{s}", 0.05, loc=(s * 0.26, 0, 0.1), segs=32, rings=16, mat=wood,
                        scale=(0.8, 1.0, 0.9))
        _ = head
    for i, x in enumerate((-0.07, 0.07)):
        G.tube(f"mallet{i}", [(x, -0.14, 0.012), (x + 0.02, -0.34, 0.012)], 0.006, n=10,
               mat=M.wood("mallet_wood", axis="Y"))
        G.sphere(f"mallet_head{i}", 0.02, loc=(x, -0.14, 0.02), segs=24, rings=12,
                 mat=M.plastic("rubber_ball", color=(0.02, 0.018, 0.015), rough=0.6), scale=(1, 1, 0.95))


# ----------------------------------------------------------------- 10 ------
@asset(res=2048, view=(-10, 38), pivot="bottom", kind="artifact", title="Screenfold codex")
def codex():
    """Borgia-style screenfold: gesso on deerskin, painted day-sign panels, cover boards."""
    pages, W, H = 6, 0.16, 0.2
    rng = np.random.default_rng(11)
    layers = {k: D.Canvas(4096, 1024) for k in ("red", "yellow", "blue", "black", "turq")}
    for p in range(pages):
        u0 = p / pages
        pw = 1 / pages
        R = lambda a, b, c, d, k="black": layers[k].rect(u0 + a * pw, b, u0 + c * pw, d)  # noqa: E731
        R(0.03, 0.03, 0.97, 0.05, "red")
        R(0.03, 0.95, 0.97, 0.97, "red")
        for row in range(2):
            v0 = 0.08 + row * 0.44
            R(0.06, v0, 0.94, v0 + 0.4, "red")
            R(0.08, v0 + 0.015, 0.92, v0 + 0.385, "yellow")
            cx = u0 + pw * (0.35 + 0.2 * rng.random())
            cy = v0 + 0.2
            # stylised figure: headdress, head, body, limbs in codex palette
            layers["turq"].poly([(cx - 0.012, cy + 0.1), (cx + 0.012, cy + 0.1), (cx + 0.02, cy + 0.16),
                                 (cx - 0.02, cy + 0.16)])
            layers["red"].circle(cx, cy + 0.075, 0.012)
            layers["blue"].rect(cx - 0.01, cy - 0.03, cx + 0.01, cy + 0.06)
            layers["black"].line([(cx - 0.01, cy + 0.04), (cx - 0.03, cy + 0.0), (cx - 0.025, cy - 0.02)], 0.003)
            layers["black"].line([(cx + 0.01, cy + 0.04), (cx + 0.032, cy + 0.07)], 0.003)
            layers["black"].line([(cx - 0.006, cy - 0.03), (cx - 0.012, cy - 0.12)], 0.004)
            layers["black"].line([(cx + 0.006, cy - 0.03), (cx + 0.016, cy - 0.12)], 0.004)
            layers["black"].circle(cx + 0.004, cy + 0.08, 0.003)
            for d in range(int(rng.integers(3, 9))):
                layers["red"].circle(u0 + pw * (0.75 + 0.1 * (d % 2)), v0 + 0.05 + 0.04 * (d // 2), 0.006)
                layers["black"].circle(u0 + pw * (0.75 + 0.1 * (d % 2)), v0 + 0.05 + 0.04 * (d // 2), 0.006,
                                       fill=None, outline=255, width=0.001)
            for f in range(3):
                layers["black"].poly([(u0 + pw * (0.2 + 0.2 * f), v0 + 0.03), (u0 + pw * (0.24 + 0.2 * f), v0 + 0.03),
                                      (u0 + pw * (0.23 + 0.2 * f), v0 + 0.06), (u0 + pw * (0.21 + 0.2 * f), v0 + 0.06)])
    cols = dict(red=(0.42, 0.03, 0.02), yellow=(0.55, 0.38, 0.06), blue=(0.04, 0.12, 0.35),
                turq=(0.05, 0.3, 0.26), black=(0.015, 0.012, 0.01))
    lay = [dict(mask=layers[k].blur(0.6).save(f"codex_{k}"), color=cols[k], rough=0.85, opacity=0.92)
           for k in ("yellow", "red", "blue", "turq", "black")]
    deer = M.paper("deerskin_gesso", color=(0.66, 0.60, 0.46), fibers="rice", stains=0.4, dirt=0.45, layers=lay)
    verts, faces, uvs = [], [], []
    ang = math.radians(28)
    x = 0.0
    for i in range(pages + 1):
        z = 0.0 if i % 2 == 0 else W * math.sin(ang)
        verts += [(x, 0.0, z), (x, H, z)]
        x += W * math.cos(ang)
    for i in range(pages):
        a, b = i * 2, (i + 1) * 2
        faces.append([a, b, b + 1, a + 1])
        uvs.append([(i / pages, 0), ((i + 1) / pages, 0), ((i + 1) / pages, 1), (i / pages, 1)])
    sh = G.mesh("pages", verts, faces, uvs, deer)
    G.solidify(sh, 0.003)
    cover = M.wood("codex_cover", light=(0.2, 0.1, 0.05), dark=(0.07, 0.035, 0.015), axis="X",
                   paint=(0.05, 0.28, 0.24), paint_wear=0.5)
    G.box("cover_a", (0.005, H * 1.03, W * 0.98), loc=(-0.004, H / 2, W * 0.49), bev=0.0015, mat=cover)
    G.box("cover_b", (0.005, H * 1.03, W * 0.98), loc=(x + 0.004, H / 2, W * 0.49), bev=0.0015, mat=cover)
