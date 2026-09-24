"""Nordic / Viking age (c. 800-1050 AD) asset set."""
import math
import os
import sys

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge.pipeline import asset

pi = math.pi


def iron(name="iron", rust=0.25, **kw):
    kw.setdefault("rough", 0.45)
    return M.metal(name, "iron", wear=0.7, dirt=0.6, patina=(0.045, 0.04, 0.036), patina_amt=0.55,
                   rust=rust, pitting=0.3, **kw)


def rivets(points, r, mat, normal_axis=None, squash=0.55, name="rivet"):
    parts = []
    for i, p in enumerate(points):
        s = G.sphere(f"{name}{i}", r, segs=12, rings=6, mat=mat, scale=(1, 1, squash))
        if normal_axis is not None:
            n = np.asarray(normal_axis[i] if np.ndim(normal_axis) == 2 else normal_axis, dtype=float)
            q = __import__("mathutils").Vector((0, 0, 1)).rotation_difference(__import__("mathutils").Vector(n))
            G.xform(s, (0, 0, 0), q.to_euler())
        G.xform(s, p)
        parts.append(s)
    return G.join(parts, name)


# ------------------------------------------------------------------ 1 ------
@asset(res=2048, view=(18, 8), pivot="center", kind="weapon", title="Round shield")
def round_shield():
    R = 0.42
    # painted whirl of four red arms on a bone-white ground, plank seams
    c = D.Canvas(2048)
    for k in range(4):
        a0 = k * pi / 2
        t = np.linspace(0, 1, 60)
        r = 0.10 + 0.39 * t
        inner = [(0.5 + rr * math.cos(a0 + 1.5 * tt), 0.5 + rr * math.sin(a0 + 1.5 * tt)) for rr, tt in zip(r, t)]
        outer = [(0.5 + rr * math.cos(a0 + 1.5 * tt + 0.62), 0.5 + rr * math.sin(a0 + 1.5 * tt + 0.62))
                 for rr, tt in zip(r, t)]
        c.poly(inner + outer[::-1])
    red = c.blur(1.2).save("paint_red")
    s = D.Canvas(2048)
    xs = np.cumsum([0.0] + list(0.11 + 0.03 * np.random.default_rng(3).random(9)))
    for x in xs / xs[-1]:
        s.line([(x, 0), (x, 1)], 0.0022)
    seams = s.blur(0.8).save("seams")
    wood = M.wood("shield_wood", axis="X",
                  paint=(0.56, 0.49, 0.36), paint_wear=0.5, dirt=0.7, wear=0.4,
                  layers=[dict(mask=red, color=(0.30, 0.025, 0.015), vary=0.25, chip=0.5),
                          dict(mask=seams, color=(0.06, 0.04, 0.03), height=-0.8, rough=0.8)])
    disc = G.lathe("board", [(0, 0), (R - 0.003, 0), (R, 0.0035), (R - 0.003, 0.0075), (0.12, 0.0095),
                             (0, 0.0095)], segs=128, mat=wood)
    G.planar_uv(disc, "Z")
    leath = M.leather("rawhide", color=(0.23, 0.14, 0.07), wear=0.7, scale=2,
                      layers=[dict(mask=_stitches(), height=0.6, color=(0.12, 0.07, 0.03))])
    rim = G.torus("rim", R - 0.001, 0.0062, loc=(0, 0, 0.004), segs=160, rsegs=16, mat=leath)
    irn = iron("boss_iron", rust=0.2, hammer=0.6)
    a = np.linspace(0, pi / 2, 16)
    prof = [(0, 0.009), (0.105, 0.009), (0.106, 0.0118), (0.079, 0.0128), (0.074, 0.02), (0.074, 0.032)]
    prof += [(0.074 * math.cos(t), 0.032 + 0.068 * math.sin(t)) for t in a[1:]]
    G.lathe("boss", prof, segs=96, mat=irn)
    rivets([(0.092 * math.cos(t), 0.092 * math.sin(t), 0.0125) for t in np.linspace(0, 2 * pi, 6)[:-1]],
           0.0065, irn)
    rivets([((R - 0.03) * math.cos(t), (R - 0.03) * math.sin(t), 0.0095) for t in np.linspace(0, 2 * pi, 17)[:-1]],
           0.0035, irn, name="edge_rivet")
    G.box("grip", (0.52, 0.035, 0.022), loc=(0, 0, -0.011), bev=0.006, mat=M.wood("grip_wood", axis="X", dirt=0.7))
    G.transform_all(rot=G.rotd(90, 0, 0))


def _stitches():
    c = D.Canvas(4096, 256)
    for i in range(260):
        u = (i + 0.5) / 260
        c.line([(u - 0.0012, 0.15), (u + 0.0012, 0.85)], 0.0007)
    return c.blur(0.6).save("stitches")


# ------------------------------------------------------------------ 2 ------
@asset(res=2048, view=(0, 6), pose=(0, 90, 0), pivot="origin", kind="weapon", title="Viking sword")
def viking_sword():
    L = 0.765
    zs = np.linspace(0, L, 100)
    secs = []
    n = 44
    for z in zs:
        t = z / L
        w = 0.056 - 0.014 * t
        if t > 0.86:
            w *= max(math.sqrt(max(1 - t, 0) / 0.14), 0.012)
        th = 0.0066 - 0.0032 * t
        fd = 0.0014 * (1 - S(0.58, 0.8, t))
        fw = 0.022 * (1 - 0.35 * t)
        sec = []
        for s_ in np.linspace(0, 2 * pi, n, endpoint=False):
            x = w / 2 * math.cos(s_)
            sy = math.sin(s_)
            y = math.copysign((th / 2) * abs(sy) ** 0.62, sy)
            y -= math.copysign(fd * math.exp(-(x / (fw / 2)) ** 4), sy) if abs(sy) > 1e-6 else 0
            sec.append((x, y, z + 0.008))
        secs.append(sec)
    ins = D.Canvas(512, 4096)
    ins.text(0.25, 0.42, "+VLFBERH+T", size=0.02, font="serif_bold", angle=90)
    ins.text(0.75, 0.42, "+ I I I + I I I +", size=0.016, font="serif_bold", angle=90)
    inlay = ins.blur(0.8).save("inlay")

    def pattern_weld(nb):
        """Twisted-rod (pattern welded) core, visible in the fullers."""
        x, y, _ = nb.sep(nb.co(M.UV))
        zone = nb.math("MAXIMUM", nb.ss(nb.math("ABSOLUTE", nb.sub(x, 0.25)), 0.075, 0.045),
                       nb.ss(nb.math("ABSOLUTE", nb.sub(x, 0.75)), 0.075, 0.045))
        zone = nb.mul(zone, nb.ss(y, 0.72, 0.62))
        v = nb.combine(nb.mul(nb.math("ABSOLUTE", nb.sub(nb.math("FRACT", nb.mul(x, 2.0)), 0.5)), 60.0),
                       nb.mul(y, 90.0), 0.0)
        wv = nb.wave(1.0, v, kind="BANDS", axis="Y", distort=2.5, detail=2, dscale=1.5)
        return nb.mul(zone, nb.ss(wv, 0.45, 0.6))
    steel = M.metal("blade_steel", "steel", rough=0.2, rough_var=0.03, wear=0.35, dirt=0.35, scratches=0.5,
                    patina=(0.10, 0.095, 0.09), patina_amt=0.06, pitting=0.12, rust=0.02, scale=2,
                    layers=[dict(mask=pattern_weld, color=(0.20, 0.20, 0.21), rough=0.32, height=-0.08),
                            dict(mask=inlay, color=(0.92, 0.9, 0.86), metal=1.0, rough=0.16, height=-0.25)])
    G.loft("blade", secs, steel)
    irn = M.metal("hilt_iron", "iron", color=(0.26, 0.25, 0.24), rough=0.35, wear=0.7, dirt=0.6,
                  patina=(0.05, 0.045, 0.04), patina_amt=0.25, rust=0.05, pitting=0.2, scale=4, edge_radius=0.0015,
                  layers=[dict(mask=_ladder(), color=(0.86, 0.84, 0.8), metal=1.0, rough=0.2, height=-0.3)])

    def bar(name, length, depth, height, curve, taper):
        b = G.box(name, (length, depth, height), bev=0.0035, segs=3, mat=irn, subdiv=3)
        co = np.array([v.co[:] for v in b.data.vertices])
        t = co[:, 0] / (length / 2)
        co[:, 2] += curve * t ** 2
        co[:, 1] *= 1 - taper * t ** 2
        co[:, 2] *= 1 - 0.25 * taper * t ** 2
        for v, c in zip(b.data.vertices, co):
            v.co = c
        b.data.update()
        G.planar_uv(b, "Y")
        return b
    g = bar("guard", 0.118, 0.028, 0.017, -0.004, 0.3)
    G.xform(g, (0, 0, 0.0))
    grip = G.lathe("grip", [(0, 0), (0.0142, 0), (0.0158, -0.045), (0.0142, -0.09), (0, -0.09)], segs=40,
                   mat=M.leather("grip_leather", color=(0.07, 0.03, 0.013), scale=4))
    G.xform(grip, (0, 0, -0.0085), scale=(1, 0.72, 1))
    hel = [(0.0161 * math.cos(t), 0.0161 * 0.72 * math.sin(t), -0.013 - 0.077 * t / (26 * pi))
           for t in np.linspace(0, 26 * pi, 900)]
    silver = M.metal("wire_silver", "silver", rough=0.22, wear=0.3, patina=(0.06, 0.05, 0.045), patina_amt=0.45,
                     scale=6, scratches=0.2)
    G.tube("wire", hel, 0.00095, n=8, mat=silver, cap=True)
    for z in (-0.011, -0.093):
        rg = G.torus(f"wire_ring{z}", 0.0158, 0.0016, loc=(0, 0, 0), segs=40, rsegs=8, mat=silver)
        G.xform(rg, (0, 0, z), scale=(1, 0.72, 1))
    ug = bar("upper_guard", 0.08, 0.027, 0.014, 0.003, 0.25)
    G.xform(ug, (0, 0, -0.105))
    lobes = G.circle2d(0, 0.02, 0.019).union(G.circle2d(-0.022, 0.009, 0.012)).union(
        G.circle2d(0.022, 0.009, 0.012)).union(G.poly2d([(-0.036, 0), (0.036, 0), (0.03, 0.012), (-0.03, 0.012)]))
    lobes = lobes.difference(G.poly2d([(-0.06, -0.02), (0.06, -0.02), (0.06, 0.0), (-0.06, 0.0)]))
    pom = G.extrude("pommel", G.shape_polys(lobes.buffer(0.001)), 0.024, bev=0.0055, bres=3, plane="XZ", mat=irn)
    G.xform(pom, (0, 0, -0.1112), rot=(pi, 0, 0))


def S(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def _ladder():
    c = D.Canvas(1024)
    for i in range(40):
        u = (i + 0.5) / 40
        c.line([(u, 0.1), (u, 0.9)], 0.004)
    c.line([(0, 0.08), (1, 0.08)], 0.004).line([(0, 0.92), (1, 0.92)], 0.004)
    return c.blur(0.7).save("ladder")


# ------------------------------------------------------------------ 3 ------
@asset(res=2048, view=(32, 10), kind="armor", title="Spangenhelm")
def spangenhelm():
    a, b, h = 0.100, 0.118, 0.145
    irn = iron("helm_iron", rust=0.3, hammer=0.9)

    def surf(t, p, off=0.0):
        """Ellipsoid dome point: t polar (0 top .. pi/2 rim), p azimuth."""
        n = np.array([math.sin(t) * math.cos(p) / a, math.sin(t) * math.sin(p) / b, math.cos(t) / h])
        n /= np.linalg.norm(n)
        return np.array([a * math.sin(t) * math.cos(p), b * math.sin(t) * math.sin(p), h * math.cos(t)]) + n * off, n

    prof = [(a * math.sin(t), h * math.cos(t)) for t in np.linspace(pi / 2, 0, 40)]
    dome = G.lathe("dome", prof, segs=96, mat=irn)
    G.xform(dome, scale=(1, b / a, 1))
    G.solidify(dome, 0.0025, offset=1.0)
    for k, p in enumerate((0, pi / 2)):
        ts = np.linspace(-pi / 2 + 0.02, pi / 2 - 0.02, 90)
        pts, nrm = zip(*[surf(abs(t), p if t >= 0 else p + pi, 0.0024) for t in ts])
        G.strap(f"ridge{k}", pts, nrm, 0.024 - 0.006 * np.cos(ts) ** 8, 0.003, irn)
        rv = [surf(abs(t), p if t >= 0 else p + pi, 0.0052) for t in np.linspace(-1.35, 1.35, 12) if abs(t) > 0.15]
        rivets([r[0] for r in rv], 0.0032, irn, normal_axis=[r[1] for r in rv], name=f"rv{k}")
    ps = np.linspace(0, 2 * pi, 200)
    pts, nrm = zip(*[surf(pi / 2 - 0.09, p, 0.0024) for p in ps])
    band_pts = [(pp[0], pp[1], 0.013) for pp in pts]
    G.strap("brow", band_pts, [(q[0], q[1], 0) for q in nrm], 0.028, 0.0032, irn)
    rv = [(1.012 * a * 1.025 * math.cos(p), 1.012 * b * 1.02 * math.sin(p), 0.013) for p in np.linspace(0, 2 * pi, 25)[:-1]]
    rivets(rv, 0.003, irn, normal_axis=[(math.cos(p), math.sin(p), 0) for p in np.linspace(0, 2 * pi, 25)[:-1]],
           name="rvb")
    G.cyl("spike", 0.012, 0.022, loc=(0, 0, h + 0.004), r2=0.003, segs=24, mat=irn)
    # spectacle guard (Gjermundbu type), wrapped around the face
    eyes = G.circle2d(-0.034, -0.030, 0.026).union(G.circle2d(0.034, -0.030, 0.026))
    holes = G.circle2d(-0.034, -0.030, 0.0165).union(G.circle2d(0.034, -0.030, 0.0165))
    nose = G.poly2d([(-0.008, -0.012), (0.008, -0.012), (0.006, -0.09), (-0.006, -0.09)])
    top = G.poly2d([(-0.07, 0.0), (0.07, 0.0), (0.066, -0.014), (-0.066, -0.014)])
    guard = eyes.union(nose).union(top).difference(holes)
    gd = G.extrude("guard", G.shape_polys(guard.simplify(0.0003)), 0.004, bev=0.0012, plane="XZ", mat=irn)
    G.wrap_cyl(gd, b + 0.004, squash=1.0)
    G.xform(gd, (0, 0, 0.012), rot=G.rotd(0, 0, 0))


# ------------------------------------------------------------------ 4 ------
@asset(res=2048, view=(25, 20), pivot="center", kind="vessel", title="Drinking horn")
def drinking_horn():
    t = np.linspace(0, 1, 120)
    ang = 1.9 * t ** 1.15
    Rr = 0.24
    path = np.stack([Rr * np.sin(ang), 0.03 * np.sin(pi * t), Rr * (1 - np.cos(ang))], 1)
    radii = 0.046 * (1 - t) ** 0.85 + 0.004
    horn_m = _horn_material()
    h = G.tube("horn", path, radii, n=48, mat=horn_m, cap=False)
    G.solidify(h, 0.0028, offset=-1.0)
    bronze = M.metal("gilt_bronze", "bronze", color=(0.86, 0.62, 0.3), rough=0.3, patina=(0.08, 0.28, 0.2),
                     patina_amt=0.35, scale=4, edge_radius=0.0015,
                     layers=[dict(mask=_zigzag_band(), height=-0.5, color=(0.25, 0.15, 0.06), rough=0.6)])
    k = 7
    G.tube("mouth_band", path[:k], radii[:k] + 0.0035, n=64, mat=bronze, cap=True)
    G.torus("lip", radii[0] + 0.0012, 0.0022, loc=tuple(path[0]), rot=G.rotd(0, 90, 0), segs=64, mat=bronze)
    i0 = 55
    G.tube("mid_band", path[i0:i0 + 3], radii[i0:i0 + 3] + 0.0028, n=48, mat=bronze, cap=True)
    tip = path[-1]
    Tn = path[-1] - path[-3]
    Tn /= np.linalg.norm(Tn)
    term = [tip - Tn * 0.012 + Tn * s for s in np.linspace(0, 0.05, 20)]
    tr = [0.0065 + 0.004 * math.sin(pi * (s / 0.05)) ** 2 + (0.006 if s > 0.04 else 0) * S(0.04, 0.045, s)
          for s in np.linspace(0, 0.05, 20)]
    tr[-1] = 0.001
    G.tube("terminal", term, tr, n=32, mat=bronze, cap=True)
    for j, i in enumerate((10, 70)):
        p = path[i] + np.array([0, 0, radii[i] + 0.004])
        G.torus(f"ring{j}", 0.009, 0.0016, loc=tuple(p), rot=G.rotd(90, 0, 0), mat=bronze)


def _horn_material():
    nb = M.NB("horn")
    x, y, _ = nb.sep(nb.co(M.UV))
    streak = nb.noise(4, 8, 0.6, nb.mapv(nb.co(M.UV), scale=(40, 1.5, 1)))
    col = nb.ramp(nb.add(nb.mul(y, 0.9), nb.mul(streak, 0.25)),
                  [(0.0, (0.46, 0.30, 0.12)), (0.22, (0.30, 0.16, 0.05)), (0.45, (0.10, 0.05, 0.02)),
                   (0.7, (0.03, 0.02, 0.014))])
    col = nb.mix(col, nb.hsv(col, 0.5, 1.0, 0.7), nb.ss(streak, 0.55, 0.7))
    height = nb.mul(nb.noise(30, 6, 0.6, nb.mapv(nb.co(M.UV), scale=(80, 3, 1))), 0.3)
    return nb.done(col, nb.mr(streak, 0, 1, 0.22, 0.4), 0.0, nb.bump(height, 0.2, 0.001), **{"Coat Weight": 0.5})


def _zigzag_band():
    c = D.Canvas(2048, 256)
    c.zigzag(0.25, 0.75, n=64, width=0.0016)
    c.line([(0, 0.12), (1, 0.12)], 0.0012).line([(0, 0.88), (1, 0.88)], 0.0012)
    return c.blur(0.6).save("zigzag")


# ------------------------------------------------------------------ 5 ------
@asset(res=1024, view=(35, 22), kind="vessel", title="Stave tankard")
def stave_tankard():
    c = D.Canvas(1024)
    for k in range(14):
        u = k / 14 + 0.013
        c.line([(u, 0), (u, 1)], 0.002)
    staves = c.blur(0.8).save("staves")
    oak = M.wood("oak", light=(0.28, 0.17, 0.08), dark=(0.10, 0.06, 0.028), axis="Z", dirt=0.7,
                 wear=0.4, varnish=0.3, layers=[dict(mask=staves, height=-0.7, color=(0.05, 0.03, 0.015))])
    prof = [(0, 0), (0.064, 0), (0.066, 0.004), (0.058, 0.16), (0.055, 0.162), (0.050, 0.159), (0.056, 0.014),
            (0, 0.014)]
    G.lathe("body", prof, segs=96, mat=oak)
    irn = iron("hoop_iron", rust=0.3, scale=2)
    for i, z in enumerate((0.02, 0.085, 0.145)):
        r = 0.066 - (0.008 * z / 0.16)
        G.lathe(f"hoop{i}", [(r - 0.001, z - 0.008), (r + 0.0028, z - 0.008), (r + 0.0028, z + 0.008),
                             (r - 0.001, z + 0.008)], segs=96, mat=irn)
    path = G.curve_pts([(0.058, 0, 0.14), (0.10, 0, 0.138), (0.122, 0, 0.1), (0.112, 0, 0.05), (0.064, 0, 0.032)],
                       60)
    G.tube("handle", path, 0.0095, n=24, mat=oak, scale2=0.7)
    rivets([(0.068, 0, 0.14), (0.068, 0, 0.034)], 0.004, irn, normal_axis=(1, 0, 0))
    mead = M.liquid("mead", color=(0.45, 0.22, 0.04))
    G.cyl("mead", 0.0525, 0.001, loc=(0, 0, 0.128), segs=64, mat=mead)


# ------------------------------------------------------------------ 6 ------
@asset(res=1024, view=(10, 5), pivot="center", kind="artifact", title="Mjolnir pendant")
def mjolnir_pendant():
    from shapely.geometry import Polygon
    head = []
    for t in np.linspace(0, 1, 30):
        head.append((-0.0045 - 0.0135 * t ** 2.4, 0.014 - 0.014 * t))
    for t in np.linspace(0, 1, 30):
        x = -0.018 + 0.036 * t
        head.append((x, 0.0015 * math.sin(pi * t)))
    for t in np.linspace(1, 0, 30):
        head.append((0.0045 + 0.0135 * t ** 2.4, 0.014 - 0.014 * t))
    shape = Polygon(head).union(G.poly2d([(-0.0045, 0.012), (0.0045, 0.012), (0.004, 0.032), (-0.004, 0.032)]))
    c = D.Canvas(1024)
    # engraved triquetra-like interlace on the head (design UV = normalised bbox)
    for k in range(3):
        a0 = k * 2 * pi / 3
        pts = [(0.5 + 0.13 * math.cos(a0 + s) + 0.09 * math.cos(a0), 0.33 + 0.13 * math.sin(a0 + s) + 0.09 * math.sin(a0))
               for s in np.linspace(-2.2, 2.2, 40)]
        c.line(pts, 0.012)
    c.circle(0.5, 0.33, 0.2, fill=None, outline=255, width=0.01)
    eng = c.blur(1).save("engrave")
    silver = M.metal("silver", "silver", rough=0.22, wear=0.8, dirt=0.9, dirt_color=(0.015, 0.012, 0.01),
                     patina=(0.05, 0.045, 0.04), patina_amt=0.35, scale=12, edge_radius=0.0006,
                     scratches=0.4, layers=[dict(mask=eng, height=-0.6, color=(0.03, 0.025, 0.02), rough=0.6)])
    G.extrude("hammer", G.shape_polys(shape), 0.0055, bev=0.0014, bres=3, plane="XZ", mat=silver)
    G.torus("bail", 0.0042, 0.0013, loc=(0, 0, 0.0355), rot=G.rotd(0, 0, 90), segs=32, rsegs=10, mat=silver)
    outline = Polygon(head).buffer(-0.0017).exterior.coords
    pts = [p for i, p in enumerate(outline) if i % 3 == 0]
    rivets([(p[0], -0.0028, p[1]) for p in pts], 0.00068, silver, normal_axis=(0, -1, 0), squash=0.8, name="gran")
    rivets([(p[0], 0.0028, p[1]) for p in pts], 0.00068, silver, normal_axis=(0, 1, 0), squash=0.8, name="granb")


# ------------------------------------------------------------------ 7 ------
@asset(res=1024, view=(30, 28), kind="vessel", title="Soapstone pot")
def soapstone_pot():
    soot = dict(mask=M.axis_mask("Z", 0.09, 0.02, noise=0.06), color=(0.008, 0.007, 0.006), rough=0.95, height=0.2)
    stone = M.stone("soapstone", c1=(0.13, 0.14, 0.12), c2=(0.06, 0.065, 0.058), kind="limestone", rough=0.5,
                    scale=2, chips=0.5, layers=[soot, dict(mask=_tool_marks(), height=-0.4)])
    prof = [(0, 0), (0.08, 0.002), (0.13, 0.03), (0.152, 0.08), (0.158, 0.125), (0.155, 0.13), (0.145, 0.13),
            (0.143, 0.085), (0.12, 0.04), (0.07, 0.016), (0, 0.014)]
    pts = G.curve_pts(prof[:5], 30) + prof[5:7] + G.curve_pts(prof[7:], 30)
    G.lathe("pot", pts, segs=96, mat=stone)
    for sgn in (1, -1):
        lug = G.box(f"lug{sgn}", (0.03, 0.04, 0.028), loc=(sgn * 0.163, 0, 0.114), bev=0.006, mat=stone)
        hole = G.cyl("hole", 0.0065, 0.08, loc=(sgn * 0.166, -0.04, 0.114), rot=G.rotd(-90, 0, 0), segs=24)
        G.boolean(lug, hole)
    irn = iron("bail_iron", rust=0.5, scale=3)
    arc = [(0.166 * math.cos(t), 0, 0.114 + 0.2 * math.sin(t)) for t in np.linspace(0, pi, 80)]
    hook_r = [(0.166 + 0.012 * math.sin(t), 0.0, 0.114 - 0.012 + 0.012 * math.cos(t)) for t in np.linspace(pi, 2 * pi, 12)]
    hook_l = [(-x, y, z) for (x, y, z) in hook_r[::-1]]
    G.tube("bail", hook_l + arc[::-1][1:-1] + hook_r[::-1], 0.0038, n=12, mat=irn)


def _tool_marks():
    c = D.Canvas(1024)
    rng = np.random.default_rng(5)
    for _ in range(260):
        u, v = rng.random(2)
        L = 0.02 + rng.random() * 0.03
        c.line([(u, v), (u + 0.004, v + L)], 0.003)
    return c.blur(2).save("toolmarks")


# ------------------------------------------------------------------ 8 ------
@asset(res=2048, view=(-30, 22), kind="furniture", title="Sea chest")
def sea_chest():
    W, Dp, H = 0.78, 0.40, 0.34
    oak = M.wood("chest_oak", light=(0.26, 0.16, 0.075), dark=(0.09, 0.05, 0.022), axis="X", dirt=0.7, wear=0.5,
                 layers=[dict(mask=lambda nb: nb.ss(nb.wave(1 / 0.11, kind="BANDS", axis="Z", distort=0, detail=0,
                                                            profile="SAW"), 0.97, 1.0), height=-0.9,
                              color=(0.03, 0.02, 0.01))])
    t = 0.022
    G.box("front", (W, t, H), loc=(0, -Dp / 2 + t / 2, H / 2), bev=0.003, mat=oak)
    G.box("back", (W, t, H), loc=(0, Dp / 2 - t / 2, H / 2), bev=0.003, mat=oak)
    for s in (1, -1):
        G.box(f"end{s}", (t * 1.6, Dp + 0.02, H + 0.01), loc=(s * (W / 2 + t * 0.3), 0, H / 2), bev=0.004, mat=oak)
    G.box("bottom", (W, Dp, t), loc=(0, 0, t / 2), bev=0.002, mat=oak)
    G.box("lid", (W + 0.05, Dp + 0.05, 0.03), loc=(0, 0, H + 0.02), bev=0.006, mat=oak)
    irn = iron("chest_iron", rust=0.4, scale=1.5)
    # iron straps: across the lid and down front and back
    lt = H + 0.037
    for i, x in enumerate((-0.27, 0.0, 0.27)):
        G.box(f"strap_top{i}", (0.034, Dp + 0.056, 0.004), loc=(x, 0, lt), bev=0.0012, mat=irn)
        for sgn in (1, -1):
            G.box(f"strap_v{i}{sgn}", (0.034, 0.004, 0.09 if i == 1 else 0.2),
                  loc=(x, sgn * (Dp / 2 + 0.03), lt - (0.045 if i == 1 else 0.1)), bev=0.0012, mat=irn)
            if i != 1:
                G.box(f"strap_b{i}{sgn}", (0.034, 0.004, 0.19), loc=(x, sgn * (Dp / 2 + 0.002), H * 0.36),
                      bev=0.0012, mat=irn)
        rv = [(x, y, lt + 0.002) for y in np.linspace(-Dp / 2, Dp / 2, 6)]
        rivets(rv, 0.0045, irn, name=f"srv{i}")
    G.box("hasp_plate", (0.11, 0.006, 0.12), loc=(0, -Dp / 2 - 0.004, H * 0.6), bev=0.003, mat=irn)
    G.box("hasp", (0.03, 0.008, 0.11), loc=(0, -Dp / 2 - 0.03, H - 0.02), bev=0.003, mat=irn)
    G.box("hasp_top", (0.03, 0.03, 0.006), loc=(0, -Dp / 2 - 0.016, H + 0.034), bev=0.002, mat=irn)
    for s in (1, -1):
        G.torus(f"handle{s}", 0.04, 0.005, loc=(s * (W / 2 + 0.045), 0, H * 0.58), rot=G.rotd(90, 0, 90), mat=irn)
        G.box(f"staple{s}", (0.012, 0.05, 0.03), loc=(s * (W / 2 + 0.035), 0, H * 0.64), bev=0.003, mat=irn)


# ------------------------------------------------------------------ 9 ------
@asset(res=1024, view=(35, 25), pose=(0, 0, 0), kind="tool", title="Smithing hammer")
def smithing_hammer():
    secs = []
    n = 32
    xs = np.linspace(-0.055, 0.075, 60)
    for x in xs:
        if x < -0.03:
            w, h = 0.034, 0.034
            ch = 0.004 + 0.003 * S(-0.04, -0.055, x)
        elif x < 0.02:
            w, h = 0.036 + 0.004 * math.sin(pi * (x + 0.03) / 0.05), 0.034
            ch = 0.004
        else:
            k = (x - 0.02) / 0.055
            w, h = 0.034 * (1 - 0.1 * k), 0.034 * (1 - 0.82 * k ** 1.3)
            ch = 0.0015 + 0.003 * (1 - k)
        sec = []
        for s in np.linspace(0, 2 * pi, n, endpoint=False):
            cy, cz = math.cos(s), math.sin(s)
            sq = 4.0
            y = math.copysign(abs(cy) ** (2 / sq), cy) * w / 2
            z = math.copysign(abs(cz) ** (2 / sq), cz) * h / 2
            sec.append((x, y, z + 0.33))
        secs.append(sec)
    face = dict(mask=M.axis_mask("X", -0.05, -0.056), color=(0.55, 0.55, 0.56), rough=0.2, metal=1.0)
    irn = iron("hammer_iron", rust=0.15, scale=3, layers=[face])
    hd = G.loft("head", secs, irn)
    hole = G.box("eye", (0.028, 0.02, 0.06), loc=(0, 0, 0.33), bev=0.006)
    G.boolean(hd, hole)
    zs = np.linspace(0, 0.345, 40)
    hsecs = []
    for z in zs:
        a = 0.0135 + 0.003 * (1 - z / 0.345) + 0.004 * S(0.03, 0.0, z)
        b = a * 0.72
        hsecs.append([(a * math.cos(s), b * math.sin(s), z) for s in np.linspace(0, 2 * pi, 28, endpoint=False)])
    ash = M.wood("handle_ash", light=(0.42, 0.30, 0.17), dark=(0.20, 0.12, 0.055), axis="Z", dirt=0.6, wear=0.4,
                 layers=[dict(mask=M.axis_mask("Z", 0.25, 0.08, noise=0.05), color=(0.12, 0.07, 0.03), rough=0.35)])
    G.loft("handle", hsecs, ash)
    G.box("wedge", (0.004, 0.018, 0.012), loc=(0, 0, 0.349), bev=0.001, mat=irn)


# ----------------------------------------------------------------- 10 ------
@asset(res=2048, view=(0, 6), pose=(0, -90, 0), pivot="origin", kind="weapon", title="Bearded axe")
def bearded_axe():
    """The hero skeggox from models/norse_axe, re-baked through the pipeline."""
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "..", "models", "norse_axe", "src")
    sys.path.insert(0, src)
    import build_axe
    build_axe.build()
