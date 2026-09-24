"""Jade Dynasty - modern imperial China: polished jade, gold, black lacquer, celadon."""
import math

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge.pipeline import asset

pi = math.pi


def jade(name="jade", color=(0.03, 0.22, 0.09), scale=12, **kw):
    kw.setdefault("rough", 0.1)
    return M.gem(name, color=color, color2=(0.18, 0.42, 0.22), veins=0.3, cloud=0.8, scale=scale, **kw)


def white_jade(name="white_jade", scale=12, **kw):
    return M.gem(name, color=(0.62, 0.64, 0.55), color2=(0.78, 0.78, 0.7), veins=0.15, rough=0.12, scale=scale, **kw)


def gold(name="gold", **kw):
    kw.setdefault("rough", 0.18)
    kw.setdefault("scale", 5)
    return M.metal(name, "gold", wear=0.2, dirt=0.3, scratches=0.15, **kw)


def lacquer(name="black_lacquer", color=(0.012, 0.01, 0.009), **kw):
    kw.setdefault("rough", 0.14)
    return M.plastic(name, color=color, wear=0.25, dirt=0.25, **kw)


def cloud_mask(name, n=6, size=2048, width=0.012, rows=(0.5,)):
    c = D.Canvas(size)
    for v in rows:
        for k in range(n):
            u = (k + 0.5) / n
            c.cloud_scroll(u - 0.04, v, 0.045, width=width)
            c.cloud_scroll(u + 0.04, v, 0.045, width=width, flip=True)
            c.line([(u - 0.04, v - 0.045), (u + 0.04, v - 0.045)], width)
    return c.blur(1).save(name)


# ------------------------------------------------------------------ 1 ------
@asset(res=2048, view=(0, 6), pose=(0, 90, 0), pivot="origin", kind="weapon", title="Jade jian")
def jade_jian():
    L = 0.74
    secs = []
    for z in np.linspace(0, L, 70):
        t = z / L
        w = 0.034 - 0.006 * t
        if t > 0.93:
            w *= max(math.sqrt(max(1 - t, 0) / 0.07), 0.02)
        th = 0.0058 - 0.0022 * t
        # diamond (lozenge) section with a central ridge, slightly hollow-ground faces
        pts = []
        for s in np.linspace(0, 1, 9):
            pts.append((w / 2 * (1 - s), th / 2 * s ** 0.8))
        for s in np.linspace(0, 1, 9)[1:]:
            pts.append((-w / 2 * s, th / 2 * (1 - s) ** 0.8))
        pts += [(x, -y) for (x, y) in pts[::-1][1:-1]]
        sec = [(x, y, z + 0.004) for x, y in pts]
        secs.append(sec)
    steel = M.metal("jian_steel", "steel", rough=0.16, wear=0.2, dirt=0.2, scratches=0.35, scale=3,
                    layers=[dict(mask=_blade_inscription(), color=(1.0, 0.72, 0.3), rough=0.2, height=-0.3)])
    G.loft("blade", secs, steel)
    jd = jade("guard_jade", scale=20,
              layers=[dict(mask=cloud_mask("guard_clouds", 2, rows=(0.5,)), height=0.8, color=(0.02, 0.15, 0.06))])
    guard = G.poly2d([(-0.05, 0.0), (-0.035, 0.018), (0.0, 0.026), (0.035, 0.018), (0.05, 0.0), (0.03, -0.012),
                      (0.0, -0.016), (-0.03, -0.012)]).buffer(0.003)
    g = G.extrude("guard", G.shape_polys(guard), 0.03, bev=0.006, bres=3, plane="XZ", mat=jd)
    G.xform(g, (0, 0, -0.002))
    silk = M.fabric("silk_cord", color=(0.012, 0.01, 0.01), weave=900, rough=0.5, sheen=0.8,
                    layers=[dict(mask=_diamond_wrap(), height=0.8, color=(0.05, 0.045, 0.04))], uv=True)
    grip = G.lathe("grip", [(0, 0), (0.0145, 0), (0.0155, -0.08), (0.0145, -0.16), (0, -0.16)], segs=48, mat=silk)
    G.xform(grip, (0, 0, -0.016), scale=(1, 0.75, 1))
    au = gold("jian_gold")
    for z in (-0.018, -0.172):
        fr = G.lathe(f"ferrule{z}", [(0.0155, 0), (0.0175, 0.0), (0.0175, 0.012), (0.0155, 0.012)], segs=48, mat=au)
        G.xform(fr, (0, 0, z - (0.006 if z < -0.1 else 0.0)), scale=(1, 0.75, 1))
    pom = G.lathe("pommel", G.curve_pts([(0, 0), (0.02, 0.002), (0.024, 0.012), (0.018, 0.024), (0, 0.028)], 30),
                  segs=48, mat=jade("pommel_jade", scale=20))
    G.xform(pom, (0, 0, -0.21), scale=(1, 0.6, 1))
    t = G.torus("tassel_ring", 0.006, 0.0015, loc=(0, 0, -0.214), rot=G.rotd(90, 0, 0), mat=au)
    _ = t


def _blade_inscription():
    c = D.Canvas(512, 4096)
    c.text(0.25, 0.35, "天下太平", size=0.024, font="cjk", angle=-90)
    c.text(0.75, 0.35, "七星", size=0.024, font="cjk", angle=-90)
    for k in range(7):
        c.circle(0.25, 0.55 + 0.02 * k + 0.006 * (k % 2), 0.006)
    return c.blur(0.6).save("blade_inscription")


def _diamond_wrap():
    c = D.Canvas(1024)
    for k in range(-20, 21):
        c.line([(k / 20, 0), (k / 20 + 1, 1)], 0.006)
        c.line([(k / 20, 1), (k / 20 + 1, 0)], 0.006)
    return c.blur(1).save("wrap")


# ------------------------------------------------------------------ 2 ------
@asset(res=2048, view=(0, 16), kind="artifact", title="Bi disc on stand")
def bi_disc():
    c = D.Canvas(2048)
    rng = np.random.default_rng(2)
    for i in range(34):
        for j in range(34):
            u, v = (i + 0.5 * (j % 2)) / 34, j / 34
            r = math.hypot(u - 0.5, v - 0.5)
            if 0.17 < r < 0.47:
                c.circle(u, v, 0.0085)
    c.circle(0.5, 0.5, 0.485, fill=None, outline=255, width=0.006)
    c.circle(0.5, 0.5, 0.165, fill=None, outline=255, width=0.006)
    grain = c.blur(2.5).save("grain")
    _ = rng
    jd = jade("bi_jade", color=(0.05, 0.25, 0.11), scale=8, layers=[dict(mask=grain, height=1.2)])
    disc = G.lathe("bi", [(0.03, -0.004), (0.098, -0.004), (0.1, -0.002), (0.1, 0.002), (0.098, 0.004),
                          (0.03, 0.004), (0.029, 0.0), (0.03, -0.004)], segs=160, mat=jd)
    G.planar_uv(disc, "Z")
    G.xform(disc, (0, 0, 0.128), rot=G.rotd(90, 0, 0))
    lq = lacquer("stand_lacquer")
    G.box("base", (0.17, 0.06, 0.018), loc=(0, 0, 0.009), bev=0.004, mat=lq)
    for s in (1, -1):
        post = G.box(f"post{s}", (0.012, 0.018, 0.05), loc=(s * 0.055, 0, 0.042), bev=0.003, mat=lq)
        _ = post
    cradle = [(x, 0, 0.128 - math.sqrt(max(0.1 ** 2 - x ** 2, 0)) - 0.004) for x in np.linspace(-0.07, 0.07, 40)]
    G.tube("cradle", cradle, 0.005, n=12, mat=gold("stand_gold"))


# ------------------------------------------------------------------ 3 ------
@asset(res=2048, view=(30, 18), kind="vessel", title="Zisha teapot")
def zisha_teapot():
    clay = M.ceramic("zisha", color=(0.10, 0.045, 0.03), rough=0.5, speckle=0.5, chips=0.05, dirt=0.3, wear=0.3,
                     scale=6)
    prof = [(0, 0), (0.035, 0), (0.037, 0.004), (0.06, 0.018), (0.072, 0.045), (0.07, 0.07), (0.055, 0.088),
            (0.042, 0.092), (0.042, 0.095), (0.036, 0.095), (0.036, 0.086), (0.0, 0.086)]
    G.lathe("body", G.curve_pts(prof, 90), segs=96, mat=clay)
    G.lathe("lid", G.curve_pts([(0, 0.105), (0.02, 0.103), (0.038, 0.097), (0.041, 0.094), (0.0355, 0.093),
                                (0.0, 0.093)], 30), segs=96, mat=clay)
    G.sphere("knob", 0.0095, loc=(0, 0, 0.113), segs=32, rings=16, mat=jade("knob_jade", scale=40),
             scale=(1, 1, 0.8))
    spout = G.curve_pts([(0.055, 0, 0.035), (0.085, 0, 0.05), (0.105, 0, 0.075), (0.118, 0, 0.095)], 40)
    G.tube("spout", spout, np.linspace(0.013, 0.0055, 40), n=24, mat=clay, cap=True)
    handle = G.curve_pts([(-0.055, 0, 0.08), (-0.09, 0, 0.085), (-0.105, 0, 0.055), (-0.088, 0, 0.028),
                          (-0.062, 0, 0.026)], 50)
    G.tube("handle", handle, 0.007, n=20, mat=clay, scale2=0.75)
    G.torus("rim_gold", 0.0415, 0.0012, loc=(0, 0, 0.0955), segs=96, mat=gold("rim_gold"))
    G.torus("foot_gold", 0.0365, 0.001, loc=(0, 0, 0.003), segs=96, mat=gold("foot_gold"))


# ------------------------------------------------------------------ 4 ------
@asset(res=1024, view=(20, 38), kind="vessel", title="Celadon bowl")
def celadon_bowl():
    gl = M.ceramic("celadon", color=(0.32, 0.46, 0.34), rough=0.12, glaze=True, crackle=0.6, speckle=0.1,
                   chips=0.05, dirt=0.3, scale=5, drips=0.2)
    prof = [(0, 0.008), (0.03, 0.008), (0.031, 0.0), (0.036, 0.0), (0.04, 0.012), (0.07, 0.032), (0.09, 0.058),
            (0.098, 0.072), (0.097, 0.074), (0.092, 0.072), (0.085, 0.058), (0.065, 0.034), (0.03, 0.018),
            (0.0, 0.016)]
    G.lathe("bowl", G.curve_pts(prof, 120), segs=128, mat=gl)
    G.torus("gold_rim", 0.0955, 0.0017, loc=(0, 0, 0.0735), segs=128, mat=gold("bowl_gold"))
    G.torus("gold_foot", 0.0335, 0.001, loc=(0, 0, 0.001), segs=96, mat=gold("foot_gold2"))


# ------------------------------------------------------------------ 5 ------
@asset(res=2048, view=(25, 16), kind="artifact", title="Bronze ding censer")
def ding_censer():
    prof = [(0, 0.05), (0.06, 0.05), (0.09, 0.07), (0.105, 0.11), (0.108, 0.16), (0.114, 0.168), (0.114, 0.172),
            (0.104, 0.172), (0.1, 0.162), (0.098, 0.115), (0.085, 0.078), (0.055, 0.062), (0, 0.06)]
    V = lambda z: G.lathe_v(prof, z)  # noqa: E731
    c = D.Canvas(2048)
    c.meander(V(0.135), V(0.157), n=30)
    for k in range(6):
        u = (k + 0.5) / 6
        vc = V(0.118)
        c.cloud_scroll(u - 0.025, vc, 0.012, width=0.0035)
        c.cloud_scroll(u + 0.025, vc, 0.012, width=0.0035, flip=True)
        c.circle(u, vc, 0.005)
    relief = c.blur(1.5).save("taotie")
    br = M.metal("ding_bronze", "bronze", color=(0.62, 0.40, 0.22), rough=0.3, wear=0.8, dirt=0.7,
                 patina=(0.08, 0.28, 0.2), patina_amt=0.45, scale=3,
                 layers=[dict(mask=relief, height=1.0)])
    G.lathe("bowl", prof, segs=128, mat=br)
    for k in range(3):
        a = k * 2 * pi / 3 + pi / 6
        leg = G.lathe(f"leg{k}", [(0, 0), (0.014, 0), (0.012, 0.01), (0.009, 0.04), (0.012, 0.06), (0, 0.062)],
                      segs=24, mat=br)
        G.xform(leg, (0.07 * math.cos(a), 0.07 * math.sin(a), 0.0))
    for s in (1, -1):
        ear = [(s * 0.1, -0.03, 0.165), (s * 0.1, -0.03, 0.215), (s * 0.1, 0.03, 0.215), (s * 0.1, 0.03, 0.165)]
        G.strap(f"ear{s}", G.curve_pts(ear, 30), [(s, 0, 0)] * 30, 0.012, 0.008, br)
    lid = G.lathe("lid", G.curve_pts([(0, 0.2), (0.05, 0.195), (0.09, 0.182), (0.1, 0.174), (0.0, 0.174)], 30),
                  segs=96, mat=br)
    _ = lid
    G.sphere("lid_jade", 0.022, loc=(0, 0, 0.206), segs=40, rings=20, mat=jade("censer_jade", scale=25),
             scale=(1, 1, 0.75))


# ------------------------------------------------------------------ 6 ------
@asset(res=2048, view=(0, 30), pivot="bottom", kind="accessory", title="Folding fan")
def folding_fan():
    n = 24
    span = math.radians(160)
    R0, R1 = 0.07, 0.25
    ink = D.Canvas(2048, 512)
    rng = np.random.default_rng(8)
    for layer, (v0, amp, col) in enumerate(((0.3, 0.35, 255), (0.25, 0.25, 170))):
        pts = [(0, v0)]
        for u in np.linspace(0, 1, 60):
            pts.append((u, v0 + amp * abs(math.sin(u * 9 + layer * 2 + rng.random() * 0.4)) * (0.6 + 0.4 * rng.random())))
        pts.append((1, v0))
        ink.poly(pts, fill=col)
    ink.text(0.82, 0.62, "山水", size=0.14, font="cjk", angle=0)
    inkp = ink.blur(2).save("ink_wash")
    seal = D.Canvas(2048, 512)
    seal.rect(0.9, 0.35, 0.93, 0.47)
    sealp = seal.save("seal")
    leaf = M.paper("fan_silk", color=(0.62, 0.58, 0.48), fibers="rice", stains=0.2, dirt=0.2,
                   layers=[dict(mask=inkp, color=(0.02, 0.025, 0.03), opacity=0.9, rough=0.8),
                           dict(mask=sealp, color=(0.4, 0.02, 0.01))])
    verts, faces, uvs = [], [], []
    m = n * 2
    for i in range(m + 1):
        a = -span / 2 + span * i / m
        zoff = 0.006 if i % 2 else 0.0
        for j, r in enumerate((R0, R1)):
            verts.append((r * math.sin(a), r * math.cos(a), zoff * (r / R1)))
    for i in range(m):
        a, b = i * 2, (i + 1) * 2
        faces.append([a, b, b + 1, a + 1])
        uvs.append([(i / m, 0), ((i + 1) / m, 0), ((i + 1) / m, 1), (i / m, 1)])
    lf = G.mesh("leaf", verts, faces, uvs, leaf)
    G.solidify(lf, 0.0006, offset=0)
    jd = jade("rib_jade", scale=30)
    for i in range(0, n + 1):
        a = -span / 2 + span * i / n
        w = 0.011 if i in (0, n) else 0.006
        L = R1 + 0.004 if i in (0, n) else R0 + 0.01
        rib = G.box(f"rib{i}", (w, L, 0.0022), loc=(0, L / 2 - 0.012, 0.0), bev=0.0008, mat=jd)
        G.xform(rib, (0, 0, 0.0035 + 0.0008 * (i % 2)), rot=(0, 0, -a))
    au = gold("fan_gold")
    G.cyl("rivet", 0.005, 0.012, loc=(0, 0, -0.0025), segs=24, bev=0.001, mat=au)
    tassel = M.fabric("tassel_silk", color=(0.35, 0.015, 0.01), weave=1500, rough=0.5, sheen=0.9)
    for k in range(18):
        a = -0.4 + 0.8 * k / 17
        p = G.curve_pts([(0, -0.012, 0.0), (0.004 * a, -0.03, -0.001), (0.012 * a, -0.075, 0.0)], 12)
        G.tube(f"thread{k}", p, 0.0009, n=6, mat=tassel)
    G.sphere("tassel_bead", 0.0065, loc=(0, -0.022, 0.0), segs=24, rings=12, mat=jade("bead_jade", scale=40))


# ------------------------------------------------------------------ 7 ------
@asset(res=2048, view=(20, 10), kind="device", title="Silk lantern")
def silk_lantern():
    silk = M.fabric("lantern_silk", color=(0.40, 0.02, 0.015), weave=700, rough=0.55, sheen=0.5,
                    layers=[dict(mask=_lantern_char(), color=(0.9, 0.62, 0.2), metal=1.0, rough=0.25)], uv=True)
    ribs = 16
    prof = [(0.06, 0.0), (0.12, 0.04), (0.145, 0.11), (0.12, 0.18), (0.06, 0.22)]
    body = G.lathe("silk", G.curve_pts(prof, 60), segs=ribs * 8, mat=silk, caps=False)
    for v in body.data.vertices:
        a = math.atan2(v.co.y, v.co.x)
        k = 1 - 0.035 * (1 - abs(math.cos(a * ribs / 2)))
        v.co.x *= k
        v.co.y *= k
    G.solidify(body, 0.0008)
    au = gold("lantern_gold", rough=0.25)
    pts = G.curve_pts(prof, 60)
    for k in range(ribs):
        a = 2 * pi * k / ribs
        G.tube(f"rib{k}", [(r * 1.004 * math.cos(a), r * 1.004 * math.sin(a), z) for r, z in pts], 0.0017, n=8,
               mat=au)
    lq = lacquer("lantern_lacquer")
    G.lathe("cap_top", [(0.0, 0.215), (0.07, 0.215), (0.072, 0.232), (0.05, 0.24), (0, 0.24)], segs=64, mat=lq)
    G.lathe("cap_bot", [(0.0, -0.02), (0.05, -0.02), (0.072, -0.012), (0.07, 0.005), (0, 0.005)], segs=64, mat=lq)
    G.torus("hanger", 0.018, 0.0028, loc=(0, 0, 0.262), rot=G.rotd(90, 0, 0), mat=au)
    tassel = M.fabric("lantern_tassel", color=(0.40, 0.02, 0.015), weave=1500, rough=0.5, sheen=0.9)
    G.sphere("tassel_bead", 0.012, loc=(0, 0, -0.04), segs=32, rings=16, mat=jade("lantern_jade", scale=30))
    for k in range(40):
        a = 2 * pi * k / 40
        p = [(0.005 * math.cos(a), 0.005 * math.sin(a), -0.05), (0.009 * math.cos(a), 0.009 * math.sin(a), -0.15)]
        G.tube(f"thread{k}", p, 0.0011, n=6, mat=tassel)
    G.torus("tassel_band", 0.0075, 0.002, loc=(0, 0, -0.062), mat=au)


def _lantern_char():
    c = D.Canvas(2048)
    for k in range(4):
        c.text((k + 0.5) / 4, 0.5, "福", size=0.22, font="cjk")
    c.meander(0.06, 0.12, n=40).meander(0.88, 0.94, n=40)
    return c.blur(0.8).save("fu")


# ------------------------------------------------------------------ 8 ------
@asset(res=2048, view=(30, 25), kind="artifact", title="Jade seal and cinnabar box")
def jade_seal():
    jd = jade("seal_jade", color=(0.04, 0.2, 0.08), scale=15)
    G.box("seal", (0.05, 0.05, 0.05), loc=(0, 0, 0.025), bev=0.004, mat=jd)
    # coiled chi-dragon knob (stylised): a twisting loop
    t = np.linspace(0, 1.6 * 2 * pi, 160)
    path = np.stack([0.016 * np.cos(t) * (1 - 0.15 * t / t[-1]), 0.012 * np.sin(t), 0.058 + 0.004 * t], 1)
    G.tube("dragon", path, 0.0065 * (1 - 0.6 * (t / t[-1]) ** 2) + 0.001, n=24, mat=jd)
    G.sphere("head", 0.0085, loc=tuple(path[0] + np.array([0.004, 0, 0.002])), segs=24, rings=12, mat=jd,
             scale=(1.3, 1, 0.9))
    # seal face (carved reversed characters) - visible when seal is turned
    face = D.Canvas(1024)
    face.text(0.5, 0.5, "玉璽", size=0.5, font="cjk")
    fp = face.save("seal_face")
    red = M.plastic("cinnabar", color=(0.45, 0.02, 0.01), rough=0.7, wear=0.0, dirt=0.3,
                    layers=[dict(mask=fp, height=-1.0, invert=False)])
    pad = G.cyl("paste", 0.0335, 0.010, loc=(0.075, 0.0, 0.006), segs=64, mat=red)
    G.planar_uv(pad, "Z")
    G.displace(pad, 0.001, scale=0.004)
    por = M.ceramic("ink_box", color=(0.72, 0.72, 0.68), rough=0.12, glaze=True, crackle=0.1, speckle=0.05,
                    layers=[dict(mask=_blue_band(), color=(0.03, 0.08, 0.35))])
    bx = G.lathe("box", [(0, 0), (0.038, 0), (0.04, 0.004), (0.04, 0.018), (0.036, 0.018), (0.035, 0.006),
                         (0, 0.006)], segs=96, mat=por)
    G.xform(bx, (0.075, 0, 0))
    lid = G.lathe("box_lid", G.curve_pts([(0, 0.026), (0.03, 0.024), (0.041, 0.016), (0.041, 0.008),
                                          (0.039, 0.008), (0.0, 0.02)], 30), segs=96, mat=por)
    G.xform(lid, (0.07, 0.09, -0.008))


def _blue_band():
    c = D.Canvas(1024)
    c.hband(0.30, 0.34).hband(0.70, 0.74)
    for k in range(8):
        c.cloud_scroll((k + 0.5) / 8, 0.52, 0.04, width=0.008)
    return c.blur(1).save("blue_band")


# ------------------------------------------------------------------ 9 ------
@asset(res=1024, view=(10, 40), pivot="bottom", kind="clothing", title="Buyao hairpin")
def buyao_hairpin():
    au = gold("pin_gold", rough=0.2)
    pin = G.curve_pts([(0.0, 0.0, 0.003), (0.08, 0.0, 0.003), (0.16, 0.0, 0.004)], 30)
    G.tube("pin", pin, np.linspace(0.0012, 0.0028, 30), n=12, mat=au)
    jd = jade("petal_jade", color=(0.05, 0.3, 0.12), scale=60)
    cx = 0.175
    for k in range(5):
        a = 2 * pi * k / 5
        petal = G.poly2d([(0, 0), (0.008, 0.006), (0.009, 0.014), (0.0, 0.019), (-0.009, 0.014), (-0.008, 0.006)])
        p = G.extrude(f"petal{k}", G.shape_polys(petal.buffer(0.0008)), 0.0025, bev=0.001, plane="XY", mat=jd)
        G.xform(p, (cx, 0, 0.005), rot=(0.25, 0, a))
    G.sphere("pistil", 0.0045, loc=(cx, 0, 0.009), segs=20, rings=10, mat=au)
    pearl = M.gem("pearl", color=(0.75, 0.72, 0.66), color2=(0.85, 0.8, 0.78), veins=0, rough=0.15, scale=80)
    for k in range(3):
        y = -0.012 + 0.012 * k
        chain = [(cx + 0.012, y, 0.004), (cx + 0.03, y * 1.4, 0.003), (cx + 0.05, y * 1.8, 0.004)]
        G.tube(f"chain{k}", G.curve_pts(chain, 12), 0.0005, n=6, mat=au)
        G.sphere(f"pearl{k}", 0.0038, loc=(cx + 0.054, y * 1.8, 0.004), segs=20, rings=10, mat=pearl)
        G.sphere(f"jb{k}", 0.0025, loc=(cx + 0.031, y * 1.4, 0.003), segs=16, rings=8, mat=jd)


# ----------------------------------------------------------------- 10 ------
@asset(res=2048, view=(15, 40), kind="tool", title="Jade abacus")
def jade_abacus():
    rose = M.wood("rosewood", light=(0.12, 0.04, 0.02), dark=(0.04, 0.012, 0.006), axis="X", varnish=0.6,
                  wear=0.4)
    W, H, T = 0.30, 0.16, 0.022
    for s in (1, -1):
        G.box(f"side{s}", (0.016, T, H), loc=(s * (W / 2 - 0.008), 0, H / 2), bev=0.002, mat=rose)
        G.box(f"rail{s}", (W, T, 0.014), loc=(0, 0, H / 2 + s * (H / 2 - 0.007)), bev=0.002, mat=rose)
    G.box("beam", (W - 0.02, T * 0.8, 0.009), loc=(0, 0, H * 0.68), bev=0.0015, mat=rose)
    au = gold("abacus_gold")
    jd = jade("bead_jade", scale=40)
    rods = 13
    bead = [(0, -0.0045), (0.006, -0.004), (0.0098, 0.0), (0.006, 0.004), (0, 0.0045)]
    rng = np.random.default_rng(1)
    for k in range(rods):
        x = -W / 2 + 0.024 + (W - 0.048) * k / (rods - 1)
        G.cyl(f"rod{k}", 0.0014, H - 0.02, loc=(x, 0, 0.01), segs=8, mat=au)
        up = rng.integers(0, 3)
        for i in range(2):
            zz = (H - 0.018 - (1 - i) * 0.0092) if i < up else (H * 0.68 + 0.0095 + i * 0.0092)
            b = G.lathe(f"u{k}{i}", bead, segs=20, mat=jd)
            G.xform(b, (x, 0, zz))
        dn = rng.integers(0, 6)
        for i in range(5):
            zz = (H * 0.68 - 0.0095 - (4 - i) * 0.0092) if i >= 5 - dn else (0.018 + i * 0.0092)
            b = G.lathe(f"d{k}{i}", bead, segs=20, mat=jd)
            G.xform(b, (x, 0, zz))
    for s in (1, -1):
        for z in (0.007, H - 0.007):
            G.box(f"corner{s}{z}", (0.02, T + 0.002, 0.016), loc=(s * (W / 2 - 0.008), 0, z), bev=0.002, mat=au)
