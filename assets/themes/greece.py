"""Ancient Greece / Mount Olympus (Archaic-Classical, c. 600-400 BC) asset set."""
import math

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge.pipeline import asset

pi = math.pi
TERRA = (0.55, 0.24, 0.10)       # Attic clay orange
GLOSS = (0.012, 0.010, 0.009)    # black gloss


def bronze(name="bronze", **kw):
    kw.setdefault("rough", 0.28)
    kw.setdefault("patina_amt", 0.45)
    return M.metal(name, "bronze", wear=0.7, dirt=0.6, patina=(0.07, 0.26, 0.19), pitting=0.25, scale=3, **kw)


def gold(name="gold", **kw):
    kw.setdefault("rough", 0.22)
    kw.setdefault("scale", 5)
    return M.metal(name, "gold", wear=0.4, dirt=0.6, dirt_color=(0.05, 0.03, 0.01), scratches=0.25, **kw)


def runner(c, u, v, h, flip=1.0, pose=0.0):
    """Black-figure runner silhouette at (u, v) with height h (UV units)."""
    s = h
    w = s * 0.075
    hip = (u, v + 0.48 * s)
    neck = (u + 0.06 * s * flip, v + 0.78 * s)
    c.circle(neck[0] + 0.02 * s * flip, v + 0.88 * s, 0.075 * s)
    c.line([hip, neck], w * 1.8)
    a = 0.6 + 0.2 * pose
    knee_f = (hip[0] + 0.22 * s * flip, hip[1] - 0.14 * s)
    foot_f = (knee_f[0] - 0.02 * s * flip, v + 0.02 * s)
    knee_b = (hip[0] - 0.16 * s * flip, hip[1] - 0.2 * s)
    foot_b = (knee_b[0] - 0.2 * s * flip, knee_b[1] - 0.1 * s)
    c.line([hip, knee_f, foot_f], w * 1.3)
    c.line([hip, knee_b, foot_b], w * 1.3)
    sh = (neck[0] - 0.01 * s * flip, neck[1] - 0.04 * s)
    c.line([sh, (sh[0] + 0.2 * s * flip, sh[1] + 0.02 * s), (sh[0] + 0.3 * s * flip, sh[1] + 0.16 * s * a)], w)
    c.line([sh, (sh[0] - 0.18 * s * flip, sh[1] - 0.1 * s), (sh[0] - 0.3 * s * flip, sh[1] + 0.02 * s)], w)


# ------------------------------------------------------------------ 1 ------
@asset(res=2048, view=(-35, 8), kind="armor", title="Corinthian helmet", max_tris=70000)
def corinthian_helmet():
    secs = []
    zs = np.linspace(0.0, 0.26, 44)
    n = 96
    for z in zs:
        t = z / 0.26
        dome = math.sqrt(max(1 - ((z - 0.15) / 0.11) ** 2, 0)) if z > 0.15 else 1.0
        rx = 0.098 * dome * (1 + 0.04 * math.sin(pi * t))
        ry_f = 0.115 * dome
        ry_b = (0.118 + 0.03 * (1 - t) ** 3) * dome
        ring = []
        for a in np.linspace(0, 2 * pi, n, endpoint=False):
            ca, sa = math.cos(a), math.sin(a)
            ry = ry_f if sa < 0 else ry_b
            ring.append((rx * ca, ry * sa + 0.01, z))
        secs.append(ring)
    secs[-1] = [(0.0, 0.01, 0.26 + 0.002)] * n
    shell = G.loft("shell", secs, None, closed=True, cap=False)
    G.solidify(shell, 0.003, offset=-1.0)
    cut = G.poly2d([(-0.055, 0.12), (0.055, 0.12), (0.055, 0.095), (0.012, 0.085), (0.012, 0.0),
                    (-0.012, 0.0), (-0.012, 0.085), (-0.055, 0.095)])
    eyes = G.circle2d(-0.034, 0.108, 0.022).union(G.circle2d(0.034, 0.108, 0.022))
    slit = G.poly2d([(-0.011, -0.02), (0.011, -0.02), (0.015, 0.07), (-0.015, 0.07)])
    opening = eyes.union(slit).union(G.poly2d([(-0.05, 0.1), (0.05, 0.1), (0.04, 0.118), (-0.04, 0.118)]))
    opening = opening.difference(G.poly2d([(-0.008, 0.085), (0.008, 0.085), (0.0055, 0.125), (-0.0055, 0.125)]))
    cutter = G.extrude("cutter", G.shape_polys(opening.buffer(0.004)), 0.2, plane="XZ")
    G.xform(cutter, (0, -0.1, 0.0))
    G.boolean(shell, cutter)
    for s in (1, -1):
        notch = G.cyl(f"notch{s}", 0.03, 0.08, loc=(s * 0.14, 0.055, 0.0), rot=G.rotd(0, 90, 0), segs=32)
        G.xform(notch, scale=(1, 1, 1))
        G.boolean(shell, notch)
    c = D.Canvas(2048)
    for s in (1, -1):
        pts = [(0.75 + s * (0.012 + 0.07 * t), 0.505 + 0.035 * math.sin(pi * t)) for t in np.linspace(0, 1, 30)]
        c.line(pts, 0.006)
    brows = c.blur(2).save("brows")
    br = bronze("helm_bronze", rough=0.25, hammer=0.5,
                layers=[dict(mask=_rim_holes(), height=-0.8, color=(0.02, 0.015, 0.01)),
                        dict(mask=brows, height=1.0)])
    G.set_mat(shell, br)
    hair = M.fabric("crest_hair", color=(0.30, 0.02, 0.012), weave=2400, rough=0.6, sheen=0.9, fuzz=0.5)
    arc = [(0, 0.01 + 0.14 * math.cos(t), 0.262 + 0.035 * math.sin(t) ** 0.7) for t in np.linspace(0.25, pi - 0.1, 60)]
    crest = G.strap("crest", arc, [(0, 0, 1)] * 60, np.linspace(0.02, 0.028, 60), 0.075, hair)
    G.displace(crest, 0.004, scale=0.004)
    holder = [(0, 0.01 + 0.13 * math.cos(t), 0.258 + 0.02 * math.sin(t) ** 0.7) for t in np.linspace(0.3, pi - 0.2, 40)]
    G.strap("holder", holder, [(0, 0, 1)] * 40, 0.026, 0.008, bronze("holder_bronze"))


def _rim_holes():
    c = D.Canvas(2048)
    for k in range(80):
        c.circle((k + 0.5) / 80, 0.012, 0.0022)
    return c.save("rim_holes")


# ------------------------------------------------------------------ 2 ------
@asset(res=2048, view=(15, 10), pivot="center", kind="weapon", title="Hoplon shield")
def hoplon():
    R = 0.45
    c = D.Canvas(2048)
    c.poly([(0.5, 0.78), (0.64, 0.24), (0.585, 0.24), (0.5, 0.6), (0.415, 0.24), (0.36, 0.24)])
    lam = c.blur(1).save("lambda")
    band = D.Canvas(2048)
    for k in range(64):
        a0 = 2 * pi * k / 64
        pts = []
        for (r, da) in ((0.465, 0), (0.492, 0), (0.492, 0.07), (0.472, 0.07), (0.472, 0.035), (0.482, 0.035)):
            a = a0 + da
            pts.append((0.5 + r * math.cos(a), 0.5 + r * math.sin(a)))
        band.line(pts, 0.0025)
    meander = band.blur(0.8).save("rim_meander")
    br = bronze("aspis_bronze", rough=0.22, hammer=0.3, patina_amt=0.35,
                layers=[dict(mask=lam, color=(0.24, 0.02, 0.01), metal=0.0, rough=0.6, vary=0.3),
                        dict(mask=meander, height=-0.6, color=(0.12, 0.07, 0.03))])
    prof = [(0, 0.10), (0.2, 0.09), (0.33, 0.06), (0.39, 0.03), (0.405, 0.012), (0.41, 0.004), (R, 0.0),
            (R + 0.004, 0.004), (R, 0.009), (0.41, 0.012), (0.398, 0.03), (0.325, 0.058), (0.2, 0.084),
            (0, 0.094)]
    disc = G.lathe("aspis", G.curve_pts(prof[:7], 60) + prof[7:9] + G.curve_pts(prof[9:], 60), segs=160, mat=br)
    G.planar_uv(disc, "Z")
    wood = M.wood("aspis_wood", axis="X", dirt=0.6)
    porpax = G.box("porpax", (0.12, 0.05, 0.02), loc=(0, 0, 0.08), bev=0.006, mat=bronze("porpax_bronze"))
    _ = porpax
    cord = G.curve_pts([(0.38, -0.05, 0.02), (0.3, 0.0, 0.05), (0.38, 0.05, 0.02)], 20)
    G.tube("antilabe", cord, 0.004, n=8, mat=M.fabric("cord", color=(0.25, 0.18, 0.1), weave=300))
    _ = wood
    G.transform_all(rot=G.rotd(90, 0, 0))


# ------------------------------------------------------------------ 3 ------
@asset(res=2048, view=(0, 6), pose=(0, 90, 0), pivot="origin", kind="weapon", title="Xiphos")
def xiphos():
    L = 0.5
    secs = []
    for z in np.linspace(0, L, 70):
        t = z / L
        w = 0.042 + 0.018 * math.sin(pi * min(t / 0.75, 1.0)) ** 1.5
        if t > 0.7:
            w *= max(math.sqrt(max(1 - t, 0) / 0.3), 0.015)
        th = 0.007 - 0.004 * t
        pts = []
        for s in np.linspace(0, 2 * pi, 36, endpoint=False):
            x = w / 2 * math.cos(s)
            sy = math.sin(s)
            y = math.copysign(th / 2 * abs(sy) ** 0.5, sy)
            pts.append((x, y, z + 0.006))
        secs.append(pts)
    G.loft("blade", secs, M.metal("xiphos_iron", "steel", rough=0.3, wear=0.4, dirt=0.4, scratches=0.6,
                                  patina=(0.05, 0.045, 0.04), patina_amt=0.3, rust=0.12, pitting=0.3, scale=2))
    br = bronze("hilt_bronze")
    g = G.box("guard", (0.085, 0.028, 0.012), bev=0.004, mat=br, subdiv=2)
    G.deform(g, "BEND", angle=-10, axis="Y")
    G.planar_uv(g, "Y")
    bone = M.plastic("bone_grip", color=(0.52, 0.46, 0.34), rough=0.45, wear=0.5, dirt=0.6,
                     marble=(0.42, 0.36, 0.26), scale=6)
    grip = G.lathe("grip", G.curve_pts([(0, 0), (0.012, 0), (0.0165, -0.04), (0.012, -0.085), (0, -0.085)], 30),
                   segs=40, mat=bone)
    G.xform(grip, (0, 0, -0.006), scale=(1, 0.72, 1))
    for z in (-0.03, -0.06):
        G.cyl(f"pin{z}", 0.0028, 0.03, loc=(0, -0.015, z), rot=G.rotd(-90, 0, 0), segs=12, mat=br)
    pom = G.lathe("pommel", [(0, 0), (0.022, 0), (0.024, 0.005), (0.018, 0.012), (0, 0.012)], segs=40, mat=br)
    G.xform(pom, (0, 0, -0.103), scale=(1, 0.75, 1))


# ------------------------------------------------------------------ 4 ------
@asset(res=2048, view=(0, 8), kind="vessel", title="Black-figure amphora")
def amphora():
    prof = [(0, 0), (0.055, 0), (0.058, 0.012), (0.045, 0.03), (0.06, 0.07), (0.13, 0.2), (0.16, 0.3),
            (0.15, 0.38), (0.1, 0.44), (0.068, 0.47), (0.062, 0.5), (0.066, 0.57), (0.085, 0.6), (0.088, 0.615),
            (0.075, 0.62), (0.068, 0.61), (0.055, 0.57), (0.052, 0.5), (0.06, 0.47), (0.09, 0.44), (0.14, 0.38),
            (0.15, 0.3), (0.12, 0.2), (0.05, 0.07), (0, 0.06)]
    pts = G.curve_pts(prof, 150)
    V = lambda z: G.lathe_v(pts, z)  # noqa: E731
    gl = D.Canvas(2048)
    gl.rect(0, 0.0, 1, 1)
    for u0 in (0.03, 0.53):
        gl.rect(u0, V(0.18), u0 + 0.44, V(0.36), fill=0)
    gl.rect(0, V(0.07), 1, V(0.15), fill=0)
    gloss_mask = gl
    fig = D.Canvas(2048)
    hgt = V(0.345) - V(0.19)
    for i, u in enumerate((0.1, 0.2, 0.3, 0.4)):
        runner(fig, u, V(0.19), hgt, flip=1.0, pose=i % 2)
    for i, u in enumerate((0.6, 0.72, 0.84)):
        runner(fig, u, V(0.19), hgt, flip=-1.0, pose=i % 2)
    for k in range(40):
        u = (k + 0.5) / 40
        fig.poly([(u - 0.01, V(0.075)), (u + 0.01, V(0.075)), (u, V(0.145))])
    inc = D.Canvas(2048)
    inc.meander(V(0.365), V(0.39), u0=0.0, u1=1.0, n=40, width=0.0025)
    for k in range(60):
        u = (k + 0.5) / 60
        inc.line([(u, V(0.415)), (u, V(0.435))], 0.004)
    body = gloss_mask.blur(1).save("gloss")
    figs = fig.blur(0.8).save("figures")
    incs = inc.blur(0.5).save("incised")
    clay = M.ceramic("attic_clay", color=TERRA, rough=0.55, speckle=0.2, chips=0.35, dirt=0.5,
                     layers=[dict(mask=body, color=GLOSS, rough=0.22),
                             dict(mask=figs, color=GLOSS, rough=0.25, height=0.05),
                             dict(mask=incs, color=TERRA, rough=0.6, height=-0.2)])
    G.lathe("body", pts, segs=96, mat=clay)
    handle_m = M.ceramic("handle_gloss", color=GLOSS, rough=0.22, glaze=True, chips=0.3, body=TERRA)
    for s in (1, -1):
        h = G.curve_pts([(s * 0.063, 0, 0.56), (s * 0.12, 0, 0.56), (s * 0.135, 0, 0.5), (s * 0.12, 0, 0.44)], 40)
        G.tube(f"handle{s}", h, 0.011, n=20, mat=handle_m, scale2=0.55)


# ------------------------------------------------------------------ 5 ------
@asset(res=2048, view=(10, 42), kind="vessel", title="Red-figure kylix")
def kylix():
    c = D.Canvas(2048)
    c.rect(0, 0, 1, 1)
    c.circle(0.5, 0.5, 0.16, fill=0)
    owl = D.Canvas(2048)
    owl.poly([(0.47, 0.40), (0.53, 0.40), (0.555, 0.5), (0.545, 0.575), (0.5, 0.6), (0.455, 0.575), (0.445, 0.5)],
             fill=255)
    owl.circle(0.48, 0.555, 0.012, fill=0).circle(0.52, 0.555, 0.012, fill=0)
    owl.circle(0.48, 0.555, 0.005).circle(0.52, 0.555, 0.005)
    for k in range(6):
        owl.line([(0.475 + 0.01 * (k % 3), 0.47 - 0.02 * (k // 3)), (0.48 + 0.01 * (k % 3), 0.46 - 0.02 * (k // 3))],
                 0.002, fill=0)
    owl.line([(0.42, 0.39), (0.58, 0.39)], 0.004)
    owl.line([(0.57, 0.43), (0.62, 0.5), (0.6, 0.53)], 0.004)
    owl.text(0.5, 0.35, "ΑΘΕ", size=0.03, font="serif_bold")
    gl = c.blur(1).save("kylix_gloss")
    fig = owl.blur(0.6).save("owl")
    clay = M.ceramic("kylix_clay", color=TERRA, rough=0.5, speckle=0.15, chips=0.3, dirt=0.4,
                     layers=[dict(mask=gl, color=GLOSS, rough=0.2), dict(mask=fig, color=TERRA, rough=0.5)])
    prof = [(0, 0), (0.045, 0), (0.047, 0.006), (0.012, 0.012), (0.009, 0.05), (0.03, 0.06), (0.09, 0.075),
            (0.12, 0.088), (0.123, 0.092), (0.118, 0.092), (0.088, 0.08), (0.03, 0.07), (0, 0.068)]
    cup = G.lathe("cup", G.curve_pts(prof, 150), segs=128, mat=clay)
    G.planar_uv(cup, "Z")
    hm = M.ceramic("kylix_handle", color=GLOSS, rough=0.22, glaze=True, chips=0.3, body=TERRA)
    for s in (1, -1):
        h = [(s * 0.1 * math.cos(t) + s * 0.03, 0.13 * math.sin(t) * 0.0 + 0.045 * math.sin(t * 2 - pi / 2) * 0,
              0.077) for t in np.linspace(0, 1, 2)]
        arc = [(s * (0.105 + 0.03 * math.sin(t)), 0.045 * math.cos(t), 0.079 + 0.004 * math.sin(t))
               for t in np.linspace(0, pi, 30)]
        G.tube(f"handle{s}", arc, 0.0055, n=14, mat=hm)
        _ = h


# ------------------------------------------------------------------ 6 ------
@asset(res=1024, view=(0, 55), kind="clothing", title="Golden laurel wreath")
def laurel_wreath():
    au = gold("wreath_gold", rough=0.2)
    R = 0.095
    for s in (1, -1):
        arc = [(R * math.cos(a), R * math.sin(a), 0.006 + 0.004 * math.sin(a * 3)) for a in
               np.linspace(-pi / 2 + s * 0.2, -pi / 2 + s * (pi - 0.1), 80)]
        G.tube(f"stem{s}", arc, np.linspace(0.0024, 0.0012, 80), n=10, mat=au)
    leaf = G.poly2d([(0, 0)] + [(0.0075 * math.sin(pi * t) ** 0.7, 0.042 * t) for t in np.linspace(0, 1, 9)][1:] +
                    [(-0.0075 * math.sin(pi * t) ** 0.7, 0.042 * t) for t in np.linspace(1, 0, 9)][1:])
    tmpl = G.extrude("leaf", G.shape_polys(leaf), 0.0012, bev=0.0005, plane="XY", mat=au)
    G.deform(tmpl, "BEND", angle=25, axis="X")
    tr = []
    rng = np.random.default_rng(4)
    for s in (1, -1):
        for i in range(34):
            t = i / 33
            a = -pi / 2 + s * (0.3 + t * (pi - 0.45))
            p = (R * math.cos(a), R * math.sin(a), 0.006)
            tang = a + s * pi / 2
            for side in (1, -1):
                rot = (0.35 * side + rng.normal(0, 0.1), 0.2 * rng.normal(), tang - pi / 2 + side * 0.55 - s * 0.3)
                tr.append((p, rot, 0.75 + 0.35 * (1 - t) * rng.random() * 0.5 + 0.2 * (1 - t)))
    G.scatter(tmpl, tr, "leaves")
    for s in (1, -1):
        for i in range(8):
            a = -pi / 2 + s * (0.5 + i * 0.35)
            G.sphere(f"berry{s}{i}", 0.0035, loc=(R * 0.93 * math.cos(a), R * 0.93 * math.sin(a), 0.01), segs=12,
                     rings=6, mat=au)


# ------------------------------------------------------------------ 7 ------
@asset(res=2048, view=(15, 12), kind="instrument", title="Chelys lyre")
def chelys_lyre():
    shell = _tortoise_material()
    body = G.sphere("shell", 1.0, segs=64, rings=32, scale=(0.11, 0.13, 0.05))
    for v in body.data.vertices:
        if v.co.z < 0:
            v.co.z *= 0.25
    G.planar_uv(body, "Z")
    G.set_mat(body, shell)
    G.xform(body, (0, 0, 0.13), rot=G.rotd(90, 0, 0))
    horn = M.plastic("arm_horn", color=(0.05, 0.03, 0.018), marble=(0.25, 0.15, 0.06), rough=0.3, scale=6)
    for s in (1, -1):
        arm = G.curve_pts([(s * 0.05, 0, 0.2), (s * 0.085, 0, 0.3), (s * 0.075, 0, 0.4), (s * 0.1, 0, 0.47),
                           (s * 0.125, 0, 0.49)], 50)
        G.tube(f"arm{s}", arm, np.linspace(0.013, 0.008, 50), n=20, mat=horn)
    wood = M.wood("yoke_wood", axis="X", varnish=0.3)
    G.cyl("yoke", 0.009, 0.24, loc=(-0.12, 0, 0.455), rot=G.rotd(0, 90, 0), segs=24, mat=wood)
    gut = M.fabric("gut_string", color=(0.55, 0.45, 0.3), weave=3000, rough=0.4)
    br = bronze("tail_bronze")
    G.box("tailpiece", (0.07, 0.012, 0.012), loc=(0, -0.04, 0.03), bev=0.003, mat=br)
    G.box("bridge", (0.075, 0.006, 0.012), loc=(0, -0.056, 0.12), bev=0.002, mat=wood)
    for k in range(7):
        x = -0.03 + 0.01 * k
        G.tube(f"string{k}", [(x, -0.045, 0.03), (x * 1.1, -0.06, 0.12), (x * 1.4, -0.009, 0.455)], 0.0007, n=6,
               mat=gut)
        G.torus(f"collar{k}", 0.0105, 0.0035, loc=(x * 1.4, 0, 0.455), rot=G.rotd(0, 90, 0), segs=16, rsegs=8,
                mat=M.leather(f"collar_leather{k}", color=(0.2, 0.1, 0.05), scale=10))


def _tortoise_material():
    c = D.Canvas(1024)
    rng = np.random.default_rng(6)
    pts = [(0.5 + 0.12 * rng.normal(), 0.5 + 0.15 * rng.normal()) for _ in range(14)]
    from scipy.spatial import Voronoi
    vor = Voronoi(np.array(pts + [(-2, -2), (3, -2), (-2, 3), (3, 3)]))
    for a, b in vor.ridge_vertices:
        if a >= 0 and b >= 0:
            c.line([tuple(vor.vertices[a]), tuple(vor.vertices[b])], 0.006)
    scutes = c.blur(2).save("scutes")
    nb = M.NB("tortoiseshell")
    blot = nb.noise(25, 8, 0.7, distort=1.0)
    col = nb.ramp(blot, [(0.3, (0.02, 0.012, 0.005)), (0.55, (0.20, 0.09, 0.02)), (0.75, (0.45, 0.25, 0.06))])
    col, r, m, h = M.apply_layers(nb, col, 0.25, 0.0, nb.mul(blot, 0.1),
                                  [dict(mask=scutes, height=-1.0, color=(0.02, 0.01, 0.005))])
    return nb.done(col, r, 0.0, nb.bump(h, 0.3, 0.002), **{"Coat Weight": 0.5})


# ------------------------------------------------------------------ 8 ------
@asset(res=2048, view=(0, 10), pose=(0, 90, 0), pivot="center", kind="artifact", title="Thunderbolt of Zeus")
def thunderbolt():
    au = gold("bolt_gold", rough=0.18)
    G.lathe("grip", G.curve_pts([(0, -0.06), (0.018, -0.06), (0.024, -0.03), (0.02, 0.0), (0.024, 0.03),
                                 (0.018, 0.06), (0, 0.06)], 40), segs=48, mat=au)
    for z in (-0.045, 0.0, 0.045):
        G.torus(f"band{z}", 0.022, 0.004, loc=(0, 0, z), segs=48, mat=au)
    rng = np.random.default_rng(12)
    for end in (1, -1):
        fl = G.lathe(f"flare{end}", [(0, 0), (0.02, 0), (0.035, 0.03), (0.0, 0.035)], segs=48, mat=au)
        G.xform(fl, (0, 0, 0), rot=G.rotd(0 if end > 0 else 180, 0, 0))
        G.xform(fl, (0, 0, end * 0.058))
        for k in range(5):
            a = 2 * pi * k / 5 + (0.3 if end < 0 else 0)
            spread = 0.035 if k else 0.0
            pts = [(0, 0, end * 0.08)]
            L = 0.28 if k == 0 else 0.22
            for i in range(1, 8):
                t = i / 7
                zig = 0.018 * (1 if i % 2 else -1) * (1 - t)
                r = spread * math.sin(pi * t * 0.8) + zig
                pts.append((r * math.cos(a) - zig * math.sin(a), r * math.sin(a) + zig * math.cos(a),
                            end * (0.08 + L * t)))
            G.tube(f"bolt{end}{k}", pts, np.linspace(0.009, 0.0015, len(pts)) * (1.2 if k == 0 else 1), n=12, mat=au)
    _ = rng


# ------------------------------------------------------------------ 9 ------
@asset(res=1024, view=(20, 35), kind="device", title="Terracotta oil lamp")
def oil_lamp():
    c = D.Canvas(1024)
    for k in range(12):
        a = 2 * pi * k / 12
        pts = [(0.35 + 0.11 * t * math.cos(a) + 0.02 * math.sin(pi * t) * math.cos(a + pi / 2),
                0.5 + 0.11 * t * math.sin(a) + 0.02 * math.sin(pi * t) * math.sin(a + pi / 2)) for t in np.linspace(0, 1, 16)]
        pts += [(0.35 + 0.11 * t * math.cos(a) - 0.02 * math.sin(pi * t) * math.cos(a + pi / 2),
                 0.5 + 0.11 * t * math.sin(a) - 0.02 * math.sin(pi * t) * math.sin(a + pi / 2)) for t in np.linspace(1, 0, 16)]
        c.poly(pts)
    c.circle(0.35, 0.5, 0.14, fill=None, outline=255, width=0.008)
    rosette = c.blur(2).save("rosette")
    clay = M.ceramic("lamp_clay", color=(0.50, 0.25, 0.12), rough=0.7, speckle=0.3, chips=0.3, dirt=0.6,
                     layers=[dict(mask=rosette, height=0.8),
                             dict(mask=M.axis_mask("X", 0.07, 0.1, noise=0.01), color=(0.03, 0.02, 0.015),
                                  rough=0.9)])
    body = G.lathe("body", G.curve_pts([(0, 0), (0.03, 0), (0.035, 0.004), (0.045, 0.012), (0.047, 0.02),
                                        (0.043, 0.028), (0.0, 0.026)], 40), segs=64, mat=clay)
    nozzle = G.loft("nozzle", [[(x, 0.016 * math.cos(a) * (1 - 0.2 * t), 0.014 + 0.01 * math.sin(a) * (1 - 0.1 * t))
                                for a in np.linspace(0, 2 * pi, 24, endpoint=False)]
                               for t, x in zip(np.linspace(0, 1, 12), np.linspace(0.02, 0.085, 12))], clay)
    G.planar_uv(body, "Z")
    hole = G.cyl("wick", 0.0055, 0.03, loc=(0.078, 0, 0.01), segs=16)
    G.boolean(nozzle, hole)
    fill = G.cyl("fill", 0.007, 0.03, loc=(0.0, 0, 0.01), segs=16)
    G.boolean(body, fill)
    G.torus("handle", 0.013, 0.004, loc=(-0.05, 0, 0.022), rot=G.rotd(90, 0, 0), segs=32, mat=clay)


# ----------------------------------------------------------------- 10 ------
@asset(res=2048, view=(0, 5), pose=(0, 90, 0), pivot="bottom", kind="weapon", title="Trident of Poseidon")
def trident():
    au = M.metal("trident_bronze", "bronze", color=(0.85, 0.62, 0.32), rough=0.22, wear=0.5, dirt=0.5,
                 patina=(0.05, 0.3, 0.25), patina_amt=0.5, scale=3)
    wood = M.wood("shaft_wood", axis="Z", dirt=0.5, wear=0.4)
    G.cyl("shaft", 0.016, 1.15, loc=(0, 0, 0), segs=32, mat=wood, r2=0.014)
    for z in (0.0, 0.35, 0.7, 1.12):
        cl = G.lathe(f"collar{z}", [(0.017, 0), (0.021, 0.004), (0.021, 0.022), (0.017, 0.026)], segs=32, mat=au)
        G.xform(cl, (0, 0, z - 0.004))
    G.lathe("socket", G.curve_pts([(0.017, 1.14), (0.024, 1.17), (0.02, 1.2), (0.03, 1.22), (0.0, 1.235)], 30),
            segs=40, mat=au)
    cross = G.curve_pts([(-0.1, 0, 1.3), (-0.07, 0, 1.24), (0, 0, 1.225), (0.07, 0, 1.24), (0.1, 0, 1.3)], 40)
    G.tube("crossbar", cross, 0.012, n=20, mat=au, scale2=0.6)
    for x, top in ((-0.1, 1.46), (0.0, 1.5), (0.1, 1.46)):
        base = 1.3 if x else 1.225
        G.tube(f"prong{x}", [(x, 0, base), (x * 1.02, 0, top - 0.06)], 0.009, n=16, mat=au, scale2=0.7)
        tip = G.poly2d([(-0.018, 0.0), (0.018, 0.0), (0.0, 0.1)]).union(
            G.poly2d([(0.0, 0.02), (0.028, -0.01), (0.012, 0.035)])).union(
            G.poly2d([(0.0, 0.02), (-0.028, -0.01), (-0.012, 0.035)]))
        t = G.extrude(f"tip{x}", G.shape_polys(tip), 0.008, bev=0.0028, plane="XZ", mat=au)
        G.xform(t, (x * 1.02, 0, top - 0.07))
