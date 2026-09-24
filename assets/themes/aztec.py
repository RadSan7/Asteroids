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
            b = G.extrude(f"obs{s}{i}", G.shape_polys(blade), 0.006, bev=0.0012, plane="XY", mat=obs)
            G.xform(b, (s * 0.038, 0, z), rot=(0, -pi / 2, 0 if s > 0 else pi))
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
    relief = c.blur(2).save("sunstone_relief")
    st = basalt("sunstone_basalt", scale=2,
                layers=[dict(mask=relief, height=1.0),
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
@asset(res=2048, view=(-15, 5), pivot="bottom", kind="artifact", title="Turquoise mosaic mask")
def mosaic_mask():
    ms = mosaic("turquoise_mosaic", [TURQ, (0.12, 0.5, 0.45), (0.05, 0.3, 0.3), (0.2, 0.55, 0.5), JADE], scale=260)
    face = G.sphere("face", 1.0, segs=64, rings=48, scale=(0.08, 0.06, 0.1))
    for v in face.data.vertices:
        x, y, z = v.co
        if y > 0:
            v.co.y = y * 0.15
        v.co.y -= 0.018 * math.exp(-((x / 0.012) ** 2) - ((z + 0.005) / 0.03) ** 2) * (y < 0)
        v.co.y += 0.012 * math.exp(-((abs(x) - 0.03) / 0.02) ** 2 - ((z - 0.03) / 0.012) ** 2) * (y < 0)
    G.set_mat(face, ms)
    for s in (1, -1):
        eye = G.sphere(f"eye_hole{s}", 0.016, loc=(s * 0.03, -0.06, 0.018), segs=24, rings=12, scale=(1.2, 1, 0.6))
        G.boolean(face, eye)
    mouth = G.box("mouth", (0.045, 0.1, 0.012), loc=(0, -0.06, -0.045), bev=0.004)
    G.boolean(face, mouth)
    shell = M.gem("shell_white", color=(0.75, 0.72, 0.62), veins=0.1, rough=0.3, scale=60)
    for s in (1, -1):
        G.sphere(f"eye_shell{s}", 0.016, loc=(s * 0.03, -0.045, 0.018), segs=24, rings=12, mat=shell,
                 scale=(1.1, 0.5, 0.55))
        G.sphere(f"pupil{s}", 0.006, loc=(s * 0.03, -0.053, 0.018), segs=16, rings=8, mat=obsidian("pupil"))
    teeth = M.gem("shell_teeth", color=(0.8, 0.76, 0.66), veins=0, rough=0.3, scale=80)
    for i in range(8):
        x = -0.018 + 0.036 * i / 7
        G.box(f"tooth{i}", (0.004, 0.006, 0.007), loc=(x, -0.052, -0.041), bev=0.0012, mat=teeth)
    G.xform(G.join(G.all_meshes(), "mask"), rot=G.rotd(0, 0, 0))


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
    fl = M.stone("flint", c1=(0.55, 0.45, 0.35), c2=(0.3, 0.22, 0.16), kind="limestone", rough=0.35, scale=20,
                 chips=0.7, dirt=0.3, polish=0.3)
    blade = G.poly2d([(0, 0.0), (0.028, 0.03), (0.036, 0.09), (0.02, 0.17), (0.0, 0.2), (-0.02, 0.17),
                      (-0.036, 0.09), (-0.028, 0.03)])
    b = G.extrude("blade", G.shape_polys(blade), 0.014, bev=0.0065, bres=3, plane="XZ", mat=fl)
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
@asset(res=2048, view=(0, 12), pivot="bottom", kind="clothing", title="Quetzal feather headdress",
       max_tris=90000)
def feather_headdress():
    au = gold("penacho_gold")
    band = G.lathe("band", [(0.09, 0.0), (0.095, 0.0), (0.095, 0.06), (0.09, 0.06)], segs=96, mat=au,
                   angle=pi * 1.1)
    G.xform(band, rot=(0, 0, -0.55 * pi - pi / 2 + pi / 2 - pi * 0.05))
    for k in range(9):
        a = -pi / 2 - 0.9 + 1.8 * k / 8
        G.sphere(f"disc{k}", 0.012, loc=(0.097 * math.cos(a), 0.097 * math.sin(a), 0.03), segs=20, rings=10, mat=au,
                 scale=(1, 1, 1))
    quetzal = M.feather("quetzal", c1=(0.01, 0.30, 0.10), c2=(0.02, 0.18, 0.22), tip=(0.02, 0.06, 0.15))
    blue = M.feather("cotinga", c1=(0.02, 0.18, 0.5), c2=(0.03, 0.3, 0.6), tip=(0.01, 0.05, 0.2))
    red = M.feather("spoonbill", c1=(0.55, 0.08, 0.1), c2=(0.6, 0.18, 0.2), tip=(0.3, 0.02, 0.03))
    rng = np.random.default_rng(5)
    for layer, (mat, L, n, rise, spread) in enumerate(((quetzal, 0.55, 23, 0.0, 1.35), (blue, 0.3, 19, 0.02, 1.2),
                                                        (red, 0.18, 15, 0.04, 1.05))):
        shape = G.poly2d([(0, -0.01)] + [(L * t, 0.028 * math.sin(pi * t) ** 0.6 * (1 - 0.3 * t) * (1 + layer * 0.3))
                                         for t in np.linspace(0.02, 1, 20)] +
                         [(L * t, -0.028 * math.sin(pi * t) ** 0.6 * (1 - 0.3 * t) * (1 + layer * 0.3))
                          for t in np.linspace(1, 0.02, 20)])
        tmpl = G.extrude(f"f{layer}", G.shape_polys(shape), 0.0016, bev=0.0005, plane="XY", mat=mat)
        G.planar_uv(tmpl, "Z")
        G.deform(tmpl, "BEND", angle=-25 - 10 * layer, axis="Y")
        tr = []
        for i in range(n):
            t = i / (n - 1)
            a = pi / 2 + spread * (t - 0.5) * 2
            tilt = -0.25 - 0.1 * layer + rng.normal(0, 0.04)
            tr.append(((0.08 * math.cos(a) * 0.3, 0.02 - 0.012 * layer, 0.05 + rise),
                       (0, -(a - pi / 2), 0), None))
            tr[-1] = ((0.02 * math.cos(a), 0.015 - 0.012 * layer, 0.05 + rise), (tilt, -a, 0), None)
        G.scatter(tmpl, tr, f"feathers{layer}")
    for o in G.all_meshes():
        if o.name.startswith("feathers"):
            G.xform(o, (0, 0, 0), rot=(0, 0, 0))


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
@asset(res=2048, view=(0, 40), pivot="bottom", kind="artifact", title="Screenfold codex")
def codex():
    pages = 5
    W, H = 0.16, 0.2
    c = D.Canvas(4096, 1024)
    rng = np.random.default_rng(11)
    for p in range(pages):
        u0 = p / pages
        c.rect(u0 + 0.005, 0.02, u0 + 0.195, 0.025).rect(u0 + 0.005, 0.975, u0 + 0.195, 0.98)
        for k in range(3):
            v = 0.25 + 0.25 * k
            u = u0 + 0.05 + 0.1 * rng.random()
            c.circle(u, v + 0.08, 0.018)
            c.line([(u, v + 0.06), (u, v - 0.05)], 0.008)
            c.line([(u - 0.03, v + 0.02), (u + 0.03, v - 0.02)], 0.006)
            for j in range(4):
                c.circle(u0 + 0.14 + 0.012 * (j % 2), v - 0.08 + 0.05 * j / 2, 0.008)
    ink = c.blur(0.8).save("codex_ink")
    colr = D.Canvas(4096, 1024)
    for p in range(pages):
        u0 = p / pages
        for k in range(3):
            colr.rect(u0 + 0.12, 0.18 + 0.25 * k, u0 + 0.19, 0.3 + 0.25 * k)
    fill = colr.save("codex_fill")
    deer = M.paper("deerskin_gesso", color=(0.72, 0.66, 0.52), fibers="rice", stains=0.35, dirt=0.4,
                   layers=[dict(mask=fill, color=RED, rough=0.9, opacity=0.8),
                           dict(mask=ink, color=(0.02, 0.018, 0.015), opacity=0.95)])
    verts, faces, uvs = [], [], []
    for i in range(pages + 1):
        x = i * W * 0.92
        z = 0.0 if i % 2 == 0 else 0.03
        verts += [(x, 0.0, z), (x, H, z)]
    for i in range(pages):
        a, b = i * 2, (i + 1) * 2
        faces.append([a, b, b + 1, a + 1])
        uvs.append([(i / pages, 0), ((i + 1) / pages, 0), ((i + 1) / pages, 1), (i / pages, 1)])
    sh = G.mesh("pages", verts, faces, uvs, deer)
    G.solidify(sh, 0.0025)
    wood = M.wood("codex_cover", light=(0.2, 0.1, 0.05), dark=(0.07, 0.035, 0.015), axis="X", paint=(0.04, 0.2, 0.18),
                  paint_wear=0.6)
    G.box("cover", (W * 0.95, H * 1.02, 0.008), loc=(-W * 0.48, H / 2, 0.004), bev=0.002, mat=wood)
