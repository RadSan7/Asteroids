"""Ancient Egypt (New Kingdom, c. 1550-1070 BC) asset set."""
import math

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge.pipeline import asset

pi = math.pi
LAPIS = (0.035, 0.07, 0.30)
TURQ = (0.10, 0.45, 0.42)
CARN = (0.45, 0.06, 0.02)
EBLUE = (0.05, 0.22, 0.55)   # Egyptian blue pigment


def gold(name="gold", **kw):
    kw.setdefault("rough", 0.24)
    kw.setdefault("scale", 4)
    return M.metal(name, "gold", wear=0.4, dirt=0.7, dirt_color=(0.05, 0.03, 0.01), scratches=0.3, **kw)


def bronze(name="bronze", **kw):
    kw.setdefault("rough", 0.35)
    return M.metal(name, "bronze", wear=0.7, dirt=0.6, patina=(0.06, 0.24, 0.17), patina_amt=0.6, pitting=0.3,
                   scale=3, **kw)


def lapis(name="lapis", scale=20):
    return M.gem(name, color=LAPIS, color2=(0.10, 0.16, 0.45), veins=0.2, rough=0.18, scale=scale,
                 layers=[dict(mask=lambda nb: nb.ss(nb.noise(900, 2, 0.5), 0.72, 0.76), color=(0.8, 0.65, 0.3),
                              metal=1.0, rough=0.2)])


def bbox_uv(shape, x, y):
    minx, miny, maxx, maxy = shape.bounds
    span = max(maxx - minx, maxy - miny)
    return (x - minx) / span, (y - miny) / span


# ------------------------------------------------------------------ 1 ------
@asset(res=2048, view=(0, 5), pose=(0, 0, 0), pivot="origin", kind="weapon", title="Khopesh")
def khopesh():
    shaft = G.poly2d([(-0.013, -0.13), (0.013, -0.13), (0.012, 0.28), (-0.012, 0.28)])
    cres = G.circle2d(0.075, 0.34, 0.108, 160).difference(G.circle2d(0.105, 0.322, 0.086, 160))
    cres = cres.intersection(G.poly2d([(-0.1, 0.255), (0.3, 0.255), (0.3, 0.6), (-0.1, 0.6)]))
    blade = shaft.union(cres).buffer(0.0008)
    c = D.Canvas(2048)
    u, v = bbox_uv(blade, 0.0, 0.14)
    c.text(u, v, D.hieroglyphs(11, 5), size=0.05, font="hiero", angle=90)
    cu, cv = bbox_uv(blade, 0.0, 0.14)
    c.d.rounded_rectangle([c.px(cu - 0.035, cv + 0.14), c.px(cu + 0.035, cv - 0.14)], radius=60, outline=255,
                          width=c.pw(0.004))
    eng = c.blur(0.8).save("cartouche")
    br = bronze("blade_bronze", rough=0.3, layers=[dict(mask=eng, height=-0.6, color=(0.10, 0.05, 0.02), rough=0.7)])
    G.extrude("blade", G.shape_polys(blade), 0.0065, bev=0.0026, bres=3, plane="XZ", mat=br)
    ebony = M.wood("ebony", light=(0.035, 0.025, 0.02), dark=(0.01, 0.008, 0.006), axis="Z", varnish=0.5, dirt=0.3)
    grip = G.poly2d([(-0.017, -0.125), (0.017, -0.125), (0.0165, -0.005), (-0.0165, -0.005)]).buffer(0.002)
    for s in (1, -1):
        p = G.extrude(f"grip{s}", G.shape_polys(grip), 0.007, bev=0.0028, plane="XZ", mat=ebony)
        G.xform(p, (0, s * 0.0062, 0))
    au = gold("rivet_gold")
    for z in (-0.1, -0.06, -0.02):
        G.cyl(f"rivet{z}", 0.0035, 0.024, loc=(0, -0.012, z), rot=G.rotd(-90, 0, 0), segs=16, bev=0.0012, mat=au)
    pom = G.lathe("pommel", [(0, 0), (0.016, 0), (0.021, 0.008), (0.017, 0.016), (0, 0.016)], segs=32, mat=au)
    G.xform(pom, (0, 0, -0.143), scale=(1, 0.7, 1))


# ------------------------------------------------------------------ 2 ------
@asset(res=2048, view=(10, 18), kind="vessel", title="Lotus chalice")
def lotus_chalice():
    prof = [(0, 0), (0.042, 0), (0.044, 0.006), (0.030, 0.01), (0.012, 0.03), (0.011, 0.045), (0.02, 0.055),
            (0.045, 0.075), (0.066, 0.105), (0.078, 0.14), (0.083, 0.172), (0.086, 0.18), (0.08, 0.182),
            (0.075, 0.17), (0.07, 0.14), (0.06, 0.11), (0.04, 0.085), (0, 0.075)]
    pts = G.curve_pts(prof, 100)
    V = lambda z: G.lathe_v(pts, z)  # noqa: E731
    c = D.Canvas(2048)
    n = 16
    for k in range(n):
        u0 = k / n
        for (w, z1) in ((1.0, 0.168), (0.55, 0.13)):
            uc = u0 + (0.5 / n if w < 1 else 0)
            v0, v1 = V(0.062), V(z1)
            ptsp = [(uc - w * 0.45 / n * math.sin(pi * t) ** 0.8, v0 + (v1 - v0) * t) for t in np.linspace(0, 1, 40)]
            ptsp += [(uc + w * 0.45 / n * math.sin(pi * t) ** 0.8, v0 + (v1 - v0) * t) for t in np.linspace(1, 0, 40)]
            c.line(ptsp, 0.0022, closed=True)
    petals = c.blur(1.2).save("petals")
    t = D.Canvas(2048)
    t.hband(V(0.172), V(0.1735)).hband(V(0.1795), V(0.181))
    t.text(0.25, (V(0.1735) + V(0.1795)) / 2, D.hieroglyphs(3, 12), size=0.016, font="hiero")
    ins = t.blur(0.7).save("inscription")
    alab = M.stone("alabaster", c1=(0.78, 0.72, 0.60), c2=(0.62, 0.55, 0.42), kind="marble", veins=(0.55, 0.47, 0.34),
                   vein_amt=0.35, rough=0.32, polish=0.5, scale=6, chips=0.15, dirt=0.4,
                   layers=[dict(mask=petals, height=-0.5, color=(0.5, 0.43, 0.32)),
                           dict(mask=ins, color=EBLUE, rough=0.6, height=-0.2)])
    G.lathe("cup", pts, segs=128, mat=alab)
    plain = M.stone("alabaster_h", c1=(0.78, 0.72, 0.60), c2=(0.62, 0.55, 0.42), kind="marble", scale=6,
                    veins=(0.55, 0.47, 0.34), vein_amt=0.35, rough=0.32, polish=0.5, chips=0.1)
    for s in (1, -1):
        path = G.curve_pts([(s * 0.03, 0, 0.035), (s * 0.075, 0, 0.05), (s * 0.105, 0, 0.1), (s * 0.1, 0, 0.15),
                            (s * 0.088, 0, 0.17)], 50)
        G.tube(f"stem{s}", path, 0.0065, n=20, mat=plain)
        bud = G.lathe(f"bud{s}", [(0, 0), (0.009, 0.004), (0.013, 0.014), (0.008, 0.026), (0, 0.032)], segs=24,
                      mat=plain)
        G.xform(bud, (s * 0.103, 0, 0.098), rot=G.rotd(0, s * 12, 0))


# ------------------------------------------------------------------ 3 ------
@asset(res=2048, view=(0, 5), pivot="bottom", kind="artifact", title="Ankh")
def ankh():
    from shapely import affinity
    outer = affinity.scale(G.circle2d(0, 0.19, 0.05, 96), 0.78, 1.0)
    inner = affinity.scale(G.circle2d(0, 0.195, 0.031, 96), 0.62, 1.0)
    bar = G.poly2d([(-0.085, 0.118), (-0.077, 0.14), (0.077, 0.14), (0.085, 0.118), (0.077, 0.098),
                    (-0.077, 0.098)])
    stem = G.poly2d([(-0.028, 0.0), (0.028, 0.0), (0.013, 0.1), (-0.013, 0.1)])
    shape = outer.difference(inner).union(bar).union(stem).buffer(0.0015)
    c = D.Canvas(2048)
    for off in (0.012,):
        ring = shape.buffer(-off)
        for g in G.shape_polys(ring):
            c.line([bbox_uv(shape, *p) for p in g], 0.004, closed=True)
    inl = c.blur(1).save("inlay")
    c2 = D.Canvas(2048)
    u, v = bbox_uv(shape, 0, 0.05)
    c2.text(u, v, D.hieroglyphs(21, 3), size=0.05, font="hiero", angle=90)
    gly = c2.blur(0.8).save("glyphs")
    au = gold("ankh_gold", rough=0.2, layers=[dict(mask=inl, color=LAPIS, metal=0.0, rough=0.3, height=-0.3),
                                              dict(mask=gly, height=-0.5, color=(0.25, 0.14, 0.03))])
    G.extrude("ankh", G.shape_polys(shape), 0.014, bev=0.004, bres=3, plane="XZ", mat=au)


# ------------------------------------------------------------------ 4 ------
@asset(res=2048, view=(15, 12), kind="artifact", title="Crook and flail")
def crook_and_flail():
    def bands(n, c1, c2):
        return dict(mask=lambda nb: nb.ss(nb.wave(n, nb.co(M.UV), kind="BANDS", axis="Y", distort=0, detail=0,
                                                  profile="SAW"), 0.46, 0.5), color=c2, metal=0.0, rough=0.25)
    au = gold("crook_gold", rough=0.22, layers=[bands(3.5, None, EBLUE)])
    # crook (heka)
    path = [(0, 0, z) for z in np.linspace(0, 0.28, 30)]
    curl = [(0.035 - 0.035 * math.cos(t), 0, 0.28 + 0.035 * math.sin(t) * (1 + 0.1 * t)) for t in
            np.linspace(0.05, pi * 1.25, 40)]
    P = np.array(path + curl)
    G.tube("crook", P, 0.0085, n=24, mat=au)
    G.sphere("crook_end", 0.0098, loc=(0, 0, -0.002), segs=24, rings=12, mat=au)
    # flail (nekhakha)
    au2 = gold("flail_gold", rough=0.22, layers=[bands(3.0, None, EBLUE)])
    G.tube("flail_shaft", [(0.09, 0, z) for z in np.linspace(0, 0.3, 30)], 0.0085, n=24, mat=au2)
    G.sphere("flail_knob", 0.012, loc=(0.09, 0, 0.305), segs=24, rings=12, mat=au2)
    beads = [M.gem("bead_blue", color=EBLUE, rough=0.2, veins=0, scale=40), gold("bead_gold"),
             M.gem("bead_red", color=CARN, rough=0.2, veins=0, scale=40)]
    top = np.array([0.09, 0.0, 0.296])
    for k, ang in enumerate((18, 30, 42)):
        a = math.radians(ang)
        d = np.array([math.sin(a), 0.012 * (k - 1) / 0.012 * 0.25, -math.cos(a)])
        d /= np.linalg.norm(d)
        s = 0.004
        for i in range(9):
            big = i % 2 == 0
            h = 0.014 if big else 0.006
            m = beads[(i // 2) % 3] if big else beads[1]
            b = G.cyl(f"bead{k}{i}", 0.0048 if big else 0.0056, h, segs=16, bev=0.0015, mat=m)
            G.xform(b, (0, 0, 0), rot=(0, pi - a, 0))
            G.xform(b, tuple(top + d * s))
            s += h + 0.001
        tip = G.lathe(f"drop{k}", [(0, 0), (0.007, 0.012), (0.006, 0.02), (0, 0.024)], segs=16, mat=beads[1])
        G.xform(tip, (0, 0, 0), rot=(0, pi - a, 0))
        G.xform(tip, tuple(top + d * (s + 0.024)))


# ------------------------------------------------------------------ 5 ------
@asset(res=2048, view=(0, 62), pivot="bottom", max_tris=90000, kind="clothing", title="Usekh collar")
def usekh_collar():
    a0, a1 = math.radians(-35), math.radians(215)
    rows = [(0.085, 0.009, "gold"), (0.097, 0.012, "carn"), (0.111, 0.012, "turq"), (0.125, 0.012, "lapis"),
            (0.139, 0.012, "turq"), (0.153, 0.012, "carn"), (0.168, 0.016, "drop")]
    mats = dict(gold=gold("collar_gold"), carn=M.gem("carnelian", color=CARN, rough=0.2, veins=0.1, scale=30),
                turq=M.gem("turquoise", color=TURQ, color2=(0.2, 0.55, 0.5), rough=0.35, veins=0.35, scale=30),
                lapis=lapis("collar_lapis", 30),
                drop=M.ceramic("faience", color=(0.05, 0.35, 0.30), rough=0.2, glaze=True, crackle=0.3,
                               speckle=0.2, scale=20, chips=0.3))
    for ri, (r, h, key) in enumerate(rows):
        w = 0.0052 if key != "drop" else 0.0068
        n = int((a1 - a0) * r / (w + 0.0006))
        tmpl = (G.lathe(f"t{ri}", [(0, 0), (w * 0.42, 0.001), (w * 0.52, h * 0.4), (w * 0.3, h), (0, h)], segs=10)
                if key == "drop" else G.cyl(f"t{ri}", w / 2, h, segs=10, bev=0.0012))
        G.set_mat(tmpl, mats[key])
        tr = []
        for i in range(n):
            a = a0 + (a1 - a0) * (i + 0.5) / n
            tr.append(((r * math.cos(a), r * math.sin(a), w / 2), (0, pi / 2, a), None))
        # templates point along +Z; rotate so they lie radially in the XY plane
        G.scatter(tmpl, [((x, y, z), (rx, ry, rz)) + (s,) for (x, y, z), (rx, ry, rz), s in
                         [((p[0][0] - (h / 2) * math.cos(p[1][2]), p[0][1] - (h / 2) * math.sin(p[1][2]), p[0][2]),
                           (0, pi / 2, p[1][2]), None) for p in tr]], name=f"row{ri}")
    au = mats["gold"]
    for s, a in ((1, a0), (-1, a1)):
        term = G.circle2d(0, 0, 1)
        pts = [(0.075, -0.012), (0.19, -0.02), (0.19, 0.02), (0.075, 0.012)]
        tt = G.extrude(f"term{s}", [pts], 0.008, bev=0.002, plane="XY", mat=au)
        G.xform(tt, (0, 0, 0.004), rot=(0, 0, a - s * 0.045))
        _ = term


# ------------------------------------------------------------------ 6 ------
@asset(res=1024, view=(25, 35), kind="artifact", title="Heart scarab")
def heart_scarab():
    def grooves(nb):
        x, y, z = nb.sep(nb.co())
        mid = nb.mul(nb.ss(nb.math("ABSOLUTE", x), 0.0009, 0.0003), nb.ss(y, 0.006, 0.004))
        pron = nb.ss(nb.math("ABSOLUTE", nb.sub(y, nb.add(0.006, nb.mul(nb.mul(x, x), -8.0)))), 0.0009, 0.0003)
        return nb.math("MAXIMUM", mid, pron)
    lap = lapis("scarab_body", 60)
    body = G.sphere("body", 1.0, segs=64, rings=32, mat=None, scale=(0.020, 0.028, 0.013))
    G.set_mat(body, _scarab_mat(grooves))
    G.xform(body, (0, 0, 0.004))
    base = G.extrude("base", [G.shape_polys(__import__("shapely").affinity.scale(G.circle2d(0, 0, 1, 96), 0.021,
                                                                                 0.029))[0]], 0.006,
                     bev=0.0015, plane="XY", mat=lap)
    G.xform(base, (0, 0, 0.003))
    head = G.poly2d([(-0.012, 0.022), (0.012, 0.022), (0.0135, 0.029), (0.007, 0.036), (0.0035, 0.034),
                     (0, 0.037), (-0.0035, 0.034), (-0.007, 0.036), (-0.0135, 0.029)]).buffer(0.001)
    hd = G.extrude("head", G.shape_polys(head), 0.007, bev=0.002, plane="XY", mat=lap)
    G.xform(hd, (0, 0, 0.007))
    legmat = lapis("scarab_legs", 60)
    for s in (1, -1):
        for k, (y0, ang) in enumerate(((0.016, 40), (0.0, 95), (-0.016, 140))):
            a = math.radians(ang)
            pts = [(s * 0.018, y0, 0.006), (s * 0.024, y0 + 0.006 * math.cos(a), 0.0045),
                   (s * 0.022, y0 + 0.014 * math.cos(a), 0.002)]
            G.tube(f"leg{s}{k}", G.curve_pts(pts, 12), 0.0018, n=10, mat=legmat)
    au = gold("mount_gold", scale=20, edge_radius=0.0008)
    ring = G.lathe("band", [(0.0205, 0.0), (0.0225, 0.0), (0.0225, 0.0035), (0.0205, 0.0035)], segs=96, mat=au)
    G.xform(ring, scale=(1, 1.38, 1))


def _scarab_mat(grooves):
    return M.gem("scarab_shell", color=LAPIS, color2=(0.12, 0.2, 0.5), veins=0.25, rough=0.15, scale=60,
                 layers=[dict(mask=grooves, height=-0.8, color=(0.02, 0.02, 0.05)),
                         dict(mask=lambda nb: nb.ss(nb.noise(900, 2, 0.5), 0.72, 0.76), color=(0.8, 0.65, 0.3),
                              metal=1.0, rough=0.2)])


# ------------------------------------------------------------------ 7 ------
@asset(res=2048, view=(10, 38), pivot="bottom", kind="artifact", title="Papyrus scroll")
def papyrus_scroll():
    H = 0.26
    # cross-section curve: small curl, flat sheet, then a rolled bundle
    flat = [(x, 0.0) for x in np.linspace(0.0, 0.34, 200)]
    turns = 4.2
    roll = []
    for t in np.linspace(0, turns * 2 * pi, 500)[1:]:
        r = 0.026 - 0.016 * t / (turns * 2 * pi)
        roll.append((0.34 + r * math.sin(t), 0.026 - r * math.cos(t)))
    curve = [(0.012 * math.cos(t), 0.012 + 0.012 * math.sin(t)) for t in np.linspace(-pi / 2 - 1.2 * pi, -pi / 2, 20)]
    curve = curve + flat[1:] + roll
    curve = np.array(curve)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(curve, axis=0), axis=1))]
    U = seg / seg[-1]
    ny = 8
    verts, faces, uvs = [], [], []
    for i, (x, z) in enumerate(curve):
        for j in range(ny + 1):
            y = H * j / ny
            wob = 0.0012 * math.sin(7 * y / H + 3 * x) * (1 if 0.02 < x < 0.33 and z < 0.001 else 0)
            verts.append((x, y, z + wob))
    for i in range(len(curve) - 1):
        for j in range(ny):
            a, b = i * (ny + 1) + j, (i + 1) * (ny + 1) + j
            faces.append([a, b, b + 1, a + 1])
            uvs.append([(U[i], j / ny), (U[i + 1], j / ny), (U[i + 1], (j + 1) / ny), (U[i], (j + 1) / ny)])
    flat_u0, flat_u1 = U[20], U[20 + 199]
    ink = D.Canvas(4096, 1024)
    red = D.Canvas(4096, 1024)
    cols = 14
    for k in range(cols):
        u = flat_u0 + (flat_u1 - flat_u0) * (0.05 + 0.55 * k / cols)
        ink.text(u, 0.5, D.hieroglyphs(100 + k, 11), size=0.07, font="hiero", angle=90)
        ink.line([(u + 0.0165 * (flat_u1 - flat_u0) / 0.6, 0.06), (u + 0.0165 * (flat_u1 - flat_u0) / 0.6, 0.94)], 0.0006)
    vx = flat_u0 + (flat_u1 - flat_u0) * 0.8
    ink.text(vx, 0.46, chr(0x13062) + chr(0x1319D) + chr(0x13000), size=0.26, font="hiero")
    ink.line([(flat_u0 + 0.01, 0.06), (flat_u1 - 0.01, 0.06)], 0.001).line([(flat_u0 + 0.01, 0.94),
                                                                            (flat_u1 - 0.01, 0.94)], 0.001)
    red.text(flat_u0 + (flat_u1 - flat_u0) * 0.05, 0.5, D.hieroglyphs(7, 11), size=0.07, font="hiero", angle=90)
    inkp = ink.blur(0.5).save("ink")
    redp = red.blur(0.5).save("rubric")
    pap = M.paper("papyrus", color=(0.55, 0.43, 0.24), stains=0.5,
                  layers=[dict(mask=inkp, color=(0.02, 0.018, 0.016), rough=0.6, opacity=0.92),
                          dict(mask=redp, color=(0.35, 0.05, 0.02), rough=0.6, opacity=0.9)])
    sh = G.mesh("sheet", verts, faces, uvs, pap)
    G.solidify(sh, 0.0006, offset=1.0)


# ------------------------------------------------------------------ 8 ------
@asset(res=2048, view=(20, 12), kind="vessel", title="Blue-painted jar")
def blue_painted_jar():
    prof = [(0, 0), (0.03, 0.002), (0.08, 0.04), (0.14, 0.14), (0.16, 0.26), (0.15, 0.36), (0.11, 0.44),
            (0.065, 0.49), (0.058, 0.52), (0.07, 0.54), (0.072, 0.552), (0.062, 0.556), (0.055, 0.54),
            (0.05, 0.51), (0.06, 0.48), (0.1, 0.43), (0.14, 0.35), (0.15, 0.26), (0.13, 0.14), (0.07, 0.05),
            (0.02, 0.016), (0, 0.014)]
    pts = G.curve_pts(prof, 140)
    V = lambda z: G.lathe_v(pts, z)  # noqa: E731
    c = D.Canvas(2048)
    bl = D.Canvas(2048)
    rd = D.Canvas(2048)
    for z in (0.295, 0.335, 0.395, 0.47):
        rd.hband(V(z), V(z + 0.005))
    for (z0, z1) in ((0.30, 0.333), (0.34, 0.393)):
        v0, v1 = V(z0), V(z1)
        for k in range(36):
            u = (k + 0.5) / 36
            pp = [(u - 0.009 * math.sin(pi * t), v0 + (v1 - v0) * t) for t in np.linspace(0, 1, 20)]
            pp += [(u + 0.009 * math.sin(pi * t), v0 + (v1 - v0) * t) for t in np.linspace(1, 0, 20)]
            bl.poly(pp)
            c.line(pp, 0.0012, closed=True)
    bl.hband(V(0.40), V(0.425))
    bl.dots(V(0.445), n=48, r=0.005)
    for k in range(18):
        u = (k + 0.5) / 18
        c.line([(u, V(0.16)), (u + 0.01, V(0.23)), (u - 0.01, V(0.27))], 0.0015)
        bl.circle(u - 0.01, V(0.27), 0.009)
    blue = bl.blur(1).save("blue")
    red = rd.blur(1).save("red")
    black = c.blur(0.8).save("black")
    clay = M.ceramic("jar_clay", color=(0.58, 0.40, 0.25), rough=0.8, speckle=0.4, chips=0.4, dirt=0.6,
                     layers=[dict(mask=blue, color=(0.07, 0.25, 0.55), vary=0.3, rough=0.85),
                             dict(mask=red, color=(0.38, 0.07, 0.03), rough=0.85),
                             dict(mask=black, color=(0.03, 0.025, 0.02), rough=0.85)])
    G.lathe("jar", pts, segs=96, mat=clay)
    mud = M.stone("mud_seal", c1=(0.30, 0.22, 0.14), c2=(0.18, 0.13, 0.08), kind="limestone", rough=0.9,
                  scale=8, chips=0.2)
    seal = G.lathe("seal", [(0, 0.54), (0.066, 0.54), (0.075, 0.555), (0.06, 0.585), (0.03, 0.598),
                            (0, 0.6)], segs=64, mat=mud)
    G.displace(seal, 0.004, scale=0.01)


# ------------------------------------------------------------------ 9 ------
@asset(res=1024, view=(25, 10), kind="instrument", title="Sistrum")
def sistrum():
    br = bronze("sistrum_bronze", rough=0.3)
    au = gold("sistrum_gold", rough=0.25)
    G.lathe("handle", G.curve_pts([(0, 0), (0.014, 0), (0.016, 0.006), (0.011, 0.02), (0.012, 0.11),
                                   (0.016, 0.12), (0.03, 0.15), (0.035, 0.158), (0, 0.16)], 80), segs=48, mat=au)
    loop = [(0.05 * math.sin(t), 0, 0.16 + 0.065 * (1 - math.cos(t))) for t in np.linspace(-pi * 0.95, pi * 0.95, 90)]
    G.tube("loop", loop, 0.0045, n=16, mat=br, scale2=1.6)
    for k, z in enumerate((0.19, 0.225, 0.26)):
        w = 0.05 * math.sin(math.acos(1 - (z - 0.16) / 0.065)) if z < 0.29 else 0.03
        rod = [(-w - 0.012, 0, z + 0.004), (-w - 0.006, 0, z)] + [(x, 0, z) for x in np.linspace(-w, w, 20)] + \
              [(w + 0.006, 0, z), (w + 0.012, 0, z + 0.004)]
        G.tube(f"rod{k}", rod, 0.0018, n=10, mat=br)
        for j, x in enumerate(np.linspace(-w * 0.6, w * 0.6, 3)):
            G.cyl(f"jingle{k}{j}", 0.0075, 0.0014, loc=(x + 0.003 * (j - 1), 0, z - 0.0007), rot=G.rotd(0, 90, 0),
                  segs=24, bev=0.0005, mat=br)
    G.sphere("finial", 0.006, loc=(0, 0, 0.292), segs=16, rings=8, mat=au)


# ----------------------------------------------------------------- 10 ------
@asset(res=2048, view=(-25, 35), kind="game", title="Senet board")
def senet_board():
    W, Dp, H = 0.36, 0.105, 0.065
    ebony = M.wood("senet_ebony", light=(0.06, 0.035, 0.02), dark=(0.015, 0.01, 0.006), axis="X", varnish=0.4,
                   wear=0.5)
    G.box("box", (W, Dp, H), loc=(0, 0, H / 2), bev=0.003, mat=ebony)
    G.box("drawer", (0.2, 0.004, 0.035), loc=(0.05, -Dp / 2 - 0.001, H * 0.45), bev=0.001, mat=ebony)
    G.cyl("knob", 0.005, 0.008, loc=(0.05, -Dp / 2 - 0.002, H * 0.45), rot=G.rotd(90, 0, 0), segs=16,
          mat=gold("knob_gold"))
    grid = D.Canvas(2048, 600)
    ivory_sq = D.Canvas(2048, 600)
    marks = {26: chr(0x1320D), 27: chr(0x13212), 28: chr(0x132B8), 29: chr(0x13212), 25: chr(0x1321C),
             15: chr(0x13200)}
    for r in range(3):
        for k in range(10):
            idx = r * 10 + (k if r != 1 else 9 - k) + 1
            u0, v0 = 0.02 + k * 0.096, 0.04 + r * 0.31
            ivory_sq.rect(u0 + 0.004, v0 + 0.012, u0 + 0.092, v0 + 0.298)
            if idx in marks:
                grid.text(u0 + 0.048, v0 + 0.155, marks[idx], size=0.2, font="hiero")
    iv = ivory_sq.save("ivory")
    mk = grid.blur(0.6).save("marks")
    ivory = M.plastic("ivory_inlay", color=(0.62, 0.55, 0.42), rough=0.35, wear=0.3,
                      layers=[dict(mask=iv, invert=True, color=(0.03, 0.02, 0.012), rough=0.3),
                              dict(mask=mk, color=(0.03, 0.02, 0.015), height=-0.6)])
    top = G.box("top", (W - 0.012, Dp - 0.012, 0.004), loc=(0, 0, H + 0.001), bev=0.001, mat=ivory)
    G.planar_uv(top, "Z")
    pieces = [M.ceramic("piece_blue", color=(0.05, 0.25, 0.45), glaze=True, rough=0.25, crackle=0.2, scale=30),
              M.ceramic("piece_white", color=(0.6, 0.55, 0.45), glaze=True, rough=0.3, crackle=0.2, scale=30)]
    for i in range(5):
        cone = G.lathe(f"cone{i}", [(0, 0), (0.0085, 0), (0.009, 0.004), (0.0045, 0.02), (0.0055, 0.024),
                                    (0, 0.026)], segs=24, mat=pieces[0])
        G.xform(cone, (-0.16 + i * 0.075, 0.1 + 0.01 * (i % 2), 0.0))
        spool = G.lathe(f"spool{i}", [(0, 0), (0.008, 0), (0.0085, 0.003), (0.006, 0.008), (0.0085, 0.013),
                                      (0.008, 0.016), (0, 0.016)], segs=24, mat=pieces[1])
        G.xform(spool, (-0.13 + i * 0.075, 0.14 - 0.01 * (i % 2), 0.0))
    stick_m = M.wood("throw_sticks", light=(0.42, 0.30, 0.18), dark=(0.2, 0.12, 0.06), axis="X", dirt=0.5,
                     paint=None)
    for i in range(4):
        st = G.box(f"stick{i}", (0.12, 0.011, 0.004), bev=0.0016, mat=stick_m)
        G.xform(st, (0.21 + 0.012 * i, -0.02 + 0.017 * i, 0.002 + 0.0001 * i), rot=G.rotd(0, 0, 70 + 6 * i))
