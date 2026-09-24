"""Occupied Paris, 1940-1944: a comfortable bourgeois apartment."""
import math

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge.pipeline import asset

pi = math.pi


def walnut(name="walnut", **kw):
    kw.setdefault("varnish", 0.6)
    return M.wood(name, light=(0.16, 0.085, 0.04), dark=(0.05, 0.025, 0.012), axis="X", wear=0.4, dirt=0.5, **kw)


def bakelite(name="bakelite", color=(0.012, 0.009, 0.007), **kw):
    kw.setdefault("rough", 0.18)
    return M.plastic(name, color=color, wear=0.35, dirt=0.4, **kw)


def brass(name="brass", **kw):
    kw.setdefault("rough", 0.25)
    return M.metal(name, "brass", wear=0.5, dirt=0.6, patina=(0.12, 0.09, 0.04), patina_amt=0.35, scratches=0.3,
                   scale=4, **kw)


def chrome(name="chrome", **kw):
    return M.metal(name, "chrome", rough=0.08, rough_var=0.05, wear=0.2, dirt=0.4, scratches=0.3, pitting=0.2,
                   scale=4, **kw)


# ------------------------------------------------------------------ 1 ------
@asset(res=2048, view=(-22, 10), kind="device", title="Art deco tube radio")
def tube_radio():
    W, Dp, H = 0.36, 0.22, 0.42
    arch = G.poly2d([(-W / 2, 0), (W / 2, 0)] + [(W / 2 * math.cos(t), H - W / 2 + W / 2 * math.sin(t) * 0.85)
                                                  for t in np.linspace(0, pi, 60)])
    wal = walnut("radio_walnut", ring_scale=35)
    shell = G.extrude("cabinet", G.shape_polys(arch), Dp, bev=0.008, bres=3, plane="XZ", mat=wal)
    _ = shell
    # front fretwork panel with art-deco slots, cloth behind
    fret = arch.buffer(-0.03)
    cut = None
    for k in range(-6, 7):
        x = k * 0.018
        slot = G.poly2d([(x - 0.005, 0.18), (x + 0.005, 0.18), (x + 0.005, H - 0.07 - abs(k) * 0.011),
                         (x - 0.005, H - 0.07 - abs(k) * 0.011)]).buffer(0.004)
        cut = slot if cut is None else cut.union(slot)
    panel = fret.difference(G.poly2d([(-1, 0), (1, 0), (1, 0.16), (-1, 0.16)])).difference(cut)
    fp = G.extrude("fret", G.shape_polys(panel.simplify(0.0003)), 0.008, bev=0.0015, plane="XZ",
                   mat=walnut("fret_walnut", ring_scale=40, paint=None))
    G.xform(fp, (0, -Dp / 2 - 0.004, 0))
    cloth = M.fabric("grille_cloth", color=(0.32, 0.25, 0.14), color2=(0.25, 0.2, 0.12), weave=500, rough=0.9,
                     fuzz=0.4)
    G.box("cloth", (W - 0.07, 0.004, H - 0.23), loc=(0, -Dp / 2 + 0.001, 0.17 + (H - 0.23) / 2), mat=cloth)
    # dial
    dial = D.Canvas(2048, 512)
    stations = ["PARIS-PTT", "RADIO-CITÉ", "LONDRES", "POSTE PARISIEN", "LYON", "RADIO-PARIS", "GENÈVE"]
    for i, s in enumerate(stations):
        dial.text(0.08 + 0.84 * i / (len(stations) - 1), 0.62, s, size=0.09, font="sans")
    for i in range(41):
        u = 0.06 + 0.88 * i / 40
        dial.line([(u, 0.28), (u, 0.4 if i % 5 == 0 else 0.34)], 0.0018)
        if i % 5 == 0:
            dial.text(u, 0.18, str(200 + i * 10), size=0.08, font="sans")
    dp = dial.blur(0.4).save("dial")
    face = M.plastic("dial_face", color=(0.62, 0.52, 0.33), rough=0.4, wear=0.0, dirt=0.3,
                     layers=[dict(mask=dp, color=(0.03, 0.02, 0.015))])
    dl = G.box("dial", (0.24, 0.004, 0.06), loc=(0, -Dp / 2 - 0.004, 0.11), mat=face)
    G.planar_uv(dl, "Y")
    G.box("dial_glass", (0.245, 0.002, 0.064), loc=(0, -Dp / 2 - 0.009, 0.11), mat=M.glass("radio_glass"))
    G.box("needle", (0.0015, 0.002, 0.05), loc=(-0.03, -Dp / 2 - 0.007, 0.11), mat=M.plastic("needle_red",
                                                                                              color=(0.5, 0.02, 0.01)))
    bk = bakelite("knob_bakelite", color=(0.05, 0.02, 0.008), marble=(0.12, 0.05, 0.015))
    for x in (-0.12, -0.04, 0.04, 0.12):
        kb = G.lathe(f"knob{x}", G.curve_pts([(0, 0), (0.017, 0), (0.019, 0.004), (0.016, 0.02), (0.012, 0.024),
                                              (0, 0.025)], 20), segs=40, mat=bk)
        G.xform(kb, (x, -Dp / 2 - 0.002, 0.045), rot=G.rotd(90, 0, 0))
    for s in (1, -1):
        G.box(f"foot{s}", (0.05, Dp - 0.02, 0.012), loc=(s * (W / 2 - 0.04), 0, -0.006), bev=0.003, mat=wal)


# ------------------------------------------------------------------ 2 ------
@asset(res=2048, view=(-28, 26), kind="device", title="Bakelite telephone")
def telephone():
    bk = bakelite("phone_bakelite")
    secs = []
    for z in np.linspace(0, 0.085, 24):
        t = z / 0.085
        w = 0.105 - 0.035 * t ** 1.3
        d = 0.16 - 0.06 * t ** 1.2
        ring = []
        for a in np.linspace(0, 2 * pi, 64, endpoint=False):
            ca, sa = math.cos(a), math.sin(a)
            ring.append((math.copysign(abs(ca) ** 0.45, ca) * w, math.copysign(abs(sa) ** 0.45, sa) * d / 2 +
                         0.01 * t, z))
        secs.append(ring)
    G.loft("body", secs, bk)
    # rotary dial on the sloped front
    ring = D.Canvas(1024)
    for k in range(10):
        a = math.radians(60 + 28 * k)
        ring.text(0.5 + 0.33 * math.cos(a), 0.5 + 0.33 * math.sin(a), str((k + 1) % 10), size=0.08, font="sans_bold")
    rp = ring.save("dial_numbers")
    card = M.plastic("dial_card", color=(0.65, 0.6, 0.5), rough=0.5, wear=0.0, layers=[dict(mask=rp,
                                                                                            color=(0.02, 0.02, 0.02))])
    card_ob = G.cyl("dial_card", 0.037, 0.003, segs=64, mat=card)
    G.planar_uv(card_ob, "Z")
    disc = G.cyl("dial_disc", 0.038, 0.005, loc=(0, 0, 0.003), segs=64, bev=0.0015, mat=chrome("dial_chrome"))
    for k in range(10):
        a = math.radians(60 + 28 * k)
        h = G.cyl(f"hole{k}", 0.0068, 0.02, loc=(0.027 * math.cos(a), 0.027 * math.sin(a), -0.005), segs=24)
        G.boolean(disc, h)
    stop = G.box("stop", (0.012, 0.003, 0.003), loc=(0.03, -0.028, 0.009), bev=0.0008, mat=chrome("stop_chrome"))
    parts = [card_ob, disc, stop]
    for p in parts:
        G.xform(p, (0, 0, 0), rot=G.rotd(-28, 0, 0))
        G.xform(p, (0, -0.058, 0.064))
    # cradle forks
    for s in (1, -1):
        fork = G.curve_pts([(s * 0.06, 0.02, 0.083), (s * 0.062, 0.02, 0.1), (s * 0.08, 0.02, 0.112),
                            (s * 0.09, 0.02, 0.104)], 20)
        G.tube(f"fork{s}", fork, 0.006, n=16, mat=bk)
    # handset resting on the cradle
    hs = G.curve_pts([(-0.105, 0.02, 0.1), (-0.06, 0.02, 0.125), (0.0, 0.02, 0.13), (0.06, 0.02, 0.125),
                      (0.105, 0.02, 0.1)], 60)
    G.tube("handset", hs, 0.011, n=24, mat=bk, scale2=0.8)
    for s in (1, -1):
        cup = G.lathe(f"cup{s}", G.curve_pts([(0.0, 0), (0.012, 0), (0.026, 0.018), (0.028, 0.03), (0.024, 0.034),
                                             (0.0, 0.03)], 30), segs=48, mat=bk)
        G.xform(cup, (s * 0.108, 0.02, 0.078), rot=G.rotd(0, s * 18, 0))
    cord = M.fabric("cord_cloth", color=(0.06, 0.045, 0.03), weave=1500, rough=0.8)
    hel = [(0.11 + 0.01 * t + 0.006 * math.cos(t * 40), -0.07 + 0.012 * math.sin(t * 40) - 0.02 * t, 0.004 + 0.004 * t)
           for t in np.linspace(0, 3, 400)]
    G.tube("cord", hel, 0.0028, n=8, mat=cord)


# ------------------------------------------------------------------ 3 ------
@asset(res=1024, view=(25, 35), kind="tableware", title="Limoges cup and saucer")
def cup_and_saucer():
    cprof = [(0, 0.003), (0.022, 0.003), (0.023, 0.0), (0.026, 0.0), (0.028, 0.006), (0.04, 0.03), (0.046, 0.055),
             (0.047, 0.058), (0.044, 0.058), (0.042, 0.055), (0.036, 0.03), (0.022, 0.008), (0, 0.007)]
    pts = G.curve_pts(cprof, 120)
    V = lambda z: G.lathe_v(pts, z)  # noqa: E731
    flowers = D.Canvas(2048)
    rng = np.random.default_rng(9)
    for k in range(6):
        u = (k + 0.5) / 6
        v = V(0.038)
        for j in range(5):
            a = 2 * pi * j / 5
            flowers.circle(u + 0.012 * math.cos(a), v + 0.012 * math.sin(a), 0.008)
        for j in range(4):
            a = rng.random() * 2 * pi
            flowers.line([(u, v), (u + 0.04 * math.cos(a), v + 0.03 * math.sin(a))], 0.003)
    fl = flowers.blur(1).save("roses")
    goldline = D.Canvas(2048)
    goldline.hband(V(0.0555), V(0.058)).hband(V(0.05), V(0.051))
    gl = goldline.save("gold_lines")
    porc = M.ceramic("limoges", color=(0.78, 0.77, 0.74), rough=0.08, glaze=True, speckle=0.0, chips=0.05, dirt=0.2,
                     crackle=0.0, layers=[dict(mask=fl, color=(0.45, 0.06, 0.08), vary=0.3),
                                          dict(mask=gl, color=(1.0, 0.72, 0.3), metal=1.0, rough=0.2)])
    G.lathe("cup", pts, segs=96, mat=porc)
    handle = G.curve_pts([(0.043, 0, 0.05), (0.065, 0, 0.05), (0.068, 0, 0.03), (0.045, 0, 0.018)], 30)
    G.tube("handle", handle, 0.0045, n=16, mat=porc, scale2=0.6)
    sprof = [(0, 0.002), (0.045, 0.002), (0.046, 0.0), (0.052, 0.0), (0.06, 0.004), (0.085, 0.012), (0.088, 0.015),
             (0.085, 0.015), (0.06, 0.007), (0.05, 0.005), (0, 0.005)]
    sp = G.curve_pts(sprof, 60)
    sg = D.Canvas(1024)
    sg.hband(G.lathe_v(sp, 0.011), G.lathe_v(sp, 0.0125))
    saucer_m = M.ceramic("limoges_saucer", color=(0.78, 0.77, 0.74), rough=0.08, glaze=True, speckle=0.0,
                         chips=0.05, dirt=0.2, layers=[dict(mask=sg.save("saucer_gold"), color=(1.0, 0.72, 0.3),
                                                            metal=1.0, rough=0.2)])
    sc = G.lathe("saucer", sp, segs=96, mat=saucer_m)
    _ = sc
    for o in G.all_meshes():
        if o.name in ("cup", "handle"):
            G.xform(o, (0, 0, 0.005))
    G.cyl("coffee", 0.0405, 0.001, loc=(0, 0, 0.051), segs=64, mat=M.liquid("coffee", color=(0.03, 0.012, 0.004),
                                                                            rough=0.02))
    spoon = G.curve_pts([(-0.02, 0.045, 0.012), (0.03, 0.055, 0.02), (0.07, 0.06, 0.016)], 30)
    ag = M.metal("spoon_silver", "silver", rough=0.12, wear=0.2, dirt=0.4, patina=(0.05, 0.045, 0.04),
                 patina_amt=0.3, scale=10)
    G.tube("spoon_handle", spoon, np.linspace(0.0022, 0.0035, 30), n=10, mat=ag, scale2=0.35)
    bowl = G.sphere("spoon_bowl", 0.012, segs=24, rings=12, mat=ag, scale=(1.3, 0.8, 0.3))
    G.xform(bowl, (-0.03, 0.043, 0.011))


# ------------------------------------------------------------------ 4 ------
@asset(res=2048, view=(-30, 14), kind="furniture", title="Leather club chair", max_tris=60000)
def club_chair():
    lea = M.leather("club_leather", color=(0.16, 0.06, 0.025), rough=0.45, wear=0.9, dirt=0.5, scale=1.0)
    seat = G.box("seat", (0.62, 0.62, 0.22), loc=(0, 0.0, 0.2), bev=0.05, segs=4, mat=lea)
    _ = seat
    cush = G.box("cushion", (0.5, 0.56, 0.1), loc=(0, -0.03, 0.36), bev=0.045, segs=5, mat=lea)
    G.displace(cush, 0.006, scale=0.15)
    # back wraps round into the arms: U-shaped path, rounded superellipse section
    path = [(0.33, y, 0) for y in np.linspace(-0.31, 0.05, 14)[:-1]]
    path += [(0.33 * math.cos(a), 0.05 + 0.26 * math.sin(a), 0) for a in np.linspace(0, pi, 30)]
    path += [(-0.33, y, 0) for y in np.linspace(0.05, -0.31, 14)[1:]]
    P = np.array(path)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    secs = []
    for i, p in enumerate(P):
        nrm = np.array([T[i, 1], -T[i, 0], 0.0])
        back = max(0.0, (p[1] - 0.05) / 0.26)
        hgt = 0.63 + 0.2 * back ** 1.2
        thick = 0.12 + 0.03 * back
        ring = []
        for k in range(28):
            sa = 2 * pi * k / 28
            cx, cz = math.cos(sa), math.sin(sa)
            px = math.copysign(abs(cx) ** 0.45, cx) * thick / 2
            pz = (math.copysign(abs(cz) ** 0.35, cz) + 1) / 2 * (hgt - 0.1) + 0.1
            ring.append(tuple(p + nrm * px + np.array([0, 0, pz])))
        secs.append(ring)
    G.loft("back_arms", secs, lea)
    wal = walnut("chair_legs")
    for x in (0.26, -0.26):
        for y in (0.25, -0.25):
            G.cyl(f"leg{x}{y}", 0.025, 0.09, loc=(x, y, 0.0), r2=0.02, segs=24, bev=0.004, mat=wal)
    br = brass("nail_brass")
    front = [(x, -0.311, 0.115) for x in np.linspace(-0.27, 0.27, 24)]
    for i, p in enumerate(front):
        n = G.sphere(f"nail{i}", 0.006, loc=p, segs=10, rings=5, mat=br, scale=(1, 0.5, 1))
        _ = n


# ------------------------------------------------------------------ 5 ------
@asset(res=2048, view=(-35, 18), kind="device", title="Horn gramophone")
def gramophone():
    oak = M.wood("gramo_oak", light=(0.26, 0.15, 0.07), dark=(0.09, 0.05, 0.02), axis="X", varnish=0.6, wear=0.4)
    G.box("case", (0.32, 0.32, 0.13), loc=(0, 0, 0.065), bev=0.006, mat=oak)
    G.box("plinth", (0.34, 0.34, 0.02), loc=(0, 0, 0.01), bev=0.004, mat=oak)
    felt = M.fabric("felt", color=(0.12, 0.02, 0.02), weave=900, rough=0.95, fuzz=0.6)
    G.cyl("platter", 0.125, 0.008, loc=(0, 0, 0.13), segs=96, mat=felt)
    rec = D.Canvas(2048)
    for k in range(260):
        rec.circle(0.5, 0.5, 0.2 + 0.29 * k / 260, fill=None, outline=255, width=0.0005)
    grooves = rec.save("grooves")
    lab = D.Canvas(2048)
    lab.circle(0.5, 0.5, 0.18)
    lab.text(0.5, 0.58, "PATHÉ", size=0.05, font="serif_bold", fill=0)
    lab.text(0.5, 0.44, "Parlez-moi d'amour", size=0.025, font="serif", fill=0)
    lab.circle(0.5, 0.5, 0.012, fill=0)
    lb = lab.save("label")
    shellac = M.plastic("shellac", color=(0.008, 0.007, 0.006), rough=0.18, wear=0.0, dirt=0.2,
                        layers=[dict(mask=grooves, height=-0.3, rough=0.35),
                                dict(mask=lb, color=(0.45, 0.06, 0.03), rough=0.6, height=0.1)])
    r = G.cyl("record", 0.125, 0.002, loc=(0, 0, 0.138), segs=128, mat=shellac)
    G.planar_uv(r, "Z")
    ni = chrome("gramo_nickel")
    G.cyl("spindle", 0.004, 0.02, loc=(0, 0, 0.13), segs=16, mat=ni)
    G.cyl("arm_base", 0.018, 0.02, loc=(0.12, 0.12, 0.13), segs=32, bev=0.003, mat=ni)
    arm = G.curve_pts([(0.12, 0.12, 0.15), (0.11, 0.06, 0.16), (0.07, 0.0, 0.165), (0.05, -0.02, 0.165)], 30)
    G.tube("tonearm", arm, np.linspace(0.012, 0.008, 30), n=20, mat=ni)
    sb = G.cyl("soundbox", 0.03, 0.014, loc=(0.045, -0.035, 0.145), rot=G.rotd(90, 0, 30), segs=48, bev=0.003,
               mat=ni)
    _ = sb
    br = brass("horn_brass", rough=0.2)
    hp = G.curve_pts([(0.12, 0.12, 0.16), (0.14, 0.17, 0.25), (0.1, 0.22, 0.4), (0.0, 0.2, 0.52)], 60)
    t = np.linspace(0, 1, 60)
    G.tube("horn_neck", hp, 0.012 + 0.03 * t ** 3, n=32, mat=br, cap=False)
    bell = G.lathe("bell", [(0.042, 0.0)] + [(0.042 + 0.2 * (s ** 2.2), 0.3 * s) for s in np.linspace(0.02, 1, 40)] +
                   [(0.245, 0.305)], segs=12 * 8, mat=br, caps=False)
    for v in bell.data.vertices:
        a = math.atan2(v.co.y, v.co.x)
        k = 1 + 0.06 * (v.co.z / 0.3) * abs(math.cos(a * 6))
        v.co.x *= k
        v.co.y *= k
    G.solidify(bell, 0.0015)
    G.xform(bell, (0, 0, 0), rot=G.rotd(-80, 0, 0))
    G.xform(bell, tuple(hp[-1]))
    G.tube("crank", [(0.16, 0.0, 0.07), (0.2, 0.0, 0.07), (0.2, 0.0, 0.03)], 0.004, n=10, mat=ni)
    G.cyl("crank_knob", 0.008, 0.03, loc=(0.2, 0.0, 0.03), rot=G.rotd(0, 90, 0), segs=16,
          mat=M.wood("knob_wood", varnish=0.5))


# ------------------------------------------------------------------ 6 ------
@asset(res=2048, view=(0, 8), pose=(0, 0, 0), pivot="center", kind="weapon", title="Walther P38")
def walther_p38():
    blue = M.metal("blued_steel", "gunmetal", color=(0.05, 0.05, 0.06), rough=0.3, wear=0.9, dirt=0.5,
                   scratches=0.6, pitting=0.2, rust=0.05, scale=6, edge_radius=0.0015)
    slide = G.poly2d([(-0.1, 0.095), (0.075, 0.095), (0.078, 0.108), (0.07, 0.12), (-0.02, 0.12), (-0.028, 0.113),
                      (-0.1, 0.113)])
    s = G.extrude("slide", G.shape_polys(slide), 0.03, bev=0.002, plane="XZ", mat=blue)
    ej = G.box("ejection", (0.05, 0.03, 0.014), loc=(-0.01, -0.0, 0.122))
    G.boolean(s, ej)
    barrel = G.cyl("barrel", 0.0085, 0.13, loc=(-0.1, 0, 0.113), rot=G.rotd(0, 90, 0), segs=32, mat=blue)
    bore = G.cyl("bore", 0.0045, 0.02, loc=(-0.105, 0, 0.113), rot=G.rotd(0, 90, 0), segs=24)
    G.boolean(barrel, bore)
    frame = G.poly2d([(-0.06, 0.083), (0.07, 0.083), (0.075, 0.095), (-0.06, 0.095)])
    grip = G.poly2d([(0.02, 0.083), (0.075, 0.083), (0.085, 0.07), (0.075, 0.0), (0.03, 0.0), (0.028, 0.02),
                     (0.035, 0.07)])
    tg = G.poly2d([(-0.03, 0.085), (0.025, 0.085), (0.025, 0.06), (0.0, 0.05), (-0.02, 0.053), (-0.03, 0.068)])
    tgi = G.poly2d([(-0.022, 0.08), (0.018, 0.08), (0.018, 0.064), (0.0, 0.057), (-0.015, 0.06), (-0.022, 0.07)])
    fr = frame.union(grip).union(tg.difference(tgi))
    G.extrude("frame", G.shape_polys(fr), 0.028, bev=0.0022, plane="XZ", mat=blue)
    trig = G.poly2d([(0.004, 0.083), (0.009, 0.083), (0.008, 0.07), (0.003, 0.064), (0.001, 0.066), (0.005, 0.072)])
    G.extrude("trigger", G.shape_polys(trig), 0.006, bev=0.001, plane="XZ", mat=blue)
    ham = G.poly2d([(0.07, 0.1), (0.078, 0.1), (0.088, 0.118), (0.083, 0.122), (0.074, 0.112)])
    G.extrude("hammer", G.shape_polys(ham), 0.009, bev=0.0015, plane="XZ", mat=blue)
    chk = D.Canvas(1024)
    for k in range(-40, 41):
        chk.line([(k / 40, 0), (k / 40 + 1, 1)], 0.003)
        chk.line([(k / 40, 1), (k / 40 + 1, 0)], 0.003)
    ck = chk.blur(0.6).save("checker")
    grips = M.plastic("grip_bakelite", color=(0.05, 0.02, 0.01), rough=0.35, wear=0.5, dirt=0.6,
                      layers=[dict(mask=ck, height=-0.8, invert=True)])
    gp = grip.buffer(-0.004)
    for sgn in (1, -1):
        g = G.extrude(f"grip{sgn}", G.shape_polys(gp), 0.006, bev=0.0022, plane="XZ", mat=grips)
        G.xform(g, (0, sgn * 0.0155, 0))
    G.cyl("screw", 0.004, 0.036, loc=(0.052, -0.018, 0.045), rot=G.rotd(-90, 0, 0), segs=16, mat=blue)
    G.box("front_sight", (0.004, 0.003, 0.006), loc=(-0.095, 0, 0.122), bev=0.001, mat=blue)
    G.box("rear_sight", (0.006, 0.012, 0.006), loc=(0.06, 0, 0.122), bev=0.001, mat=blue)
    G.box("safety", (0.012, 0.036, 0.006), loc=(0.055, 0, 0.114), bev=0.002, mat=blue)


# ------------------------------------------------------------------ 7 ------
@asset(res=2048, view=(20, 12), kind="device", title="Art deco table lamp")
def table_lamp():
    br = brass("lamp_brass", rough=0.2)
    base = G.curve_pts([(0, 0), (0.09, 0), (0.092, 0.012), (0.075, 0.016), (0.074, 0.028), (0.055, 0.032),
                        (0.054, 0.042), (0.03, 0.046), (0.014, 0.06), (0.012, 0.33), (0.02, 0.335), (0.02, 0.35),
                        (0.0, 0.35)], 80)
    G.lathe("base", base, segs=64, mat=br)
    G.lathe("marble_step", [(0, 0.012), (0.08, 0.012), (0.08, 0.02), (0, 0.02)], segs=64,
            mat=M.stone("black_marble", c1=(0.02, 0.02, 0.022), c2=(0.05, 0.05, 0.05), kind="marble",
                        veins=(0.5, 0.48, 0.45), vein_amt=0.8, polish=0.8, rough=0.2, scale=8))
    shade_m = M.fabric("silk_shade", color=(0.55, 0.42, 0.24), weave=900, rough=0.8, sheen=0.4,
                       layers=[dict(mask=M.axis_mask("Z", 0.46, 0.38, noise=0.02), color=(0.36, 0.26, 0.12))])
    sh = G.lathe("shade", [(0.17, 0.3), (0.08, 0.47)], segs=36 * 4, mat=shade_m, caps=False)
    for v in sh.data.vertices:
        a = math.atan2(v.co.y, v.co.x)
        k = 1 + 0.03 * abs(math.sin(a * 18))
        v.co.x *= k
        v.co.y *= k
    G.solidify(sh, 0.0015)
    G.torus("rim_bot", 0.171, 0.003, loc=(0, 0, 0.3), segs=128, mat=br)
    G.torus("rim_top", 0.081, 0.0025, loc=(0, 0, 0.47), segs=96, mat=br)
    G.lathe("bulb", G.curve_pts([(0.0, 0.35), (0.015, 0.36), (0.03, 0.39), (0.028, 0.42), (0.0, 0.44)], 30),
            segs=32, mat=M.emissive("bulb_glow", color=(1.0, 0.72, 0.42), strength=4.0))
    for k in range(3):
        a = 2 * pi * k / 3
        G.tube(f"spider{k}", [(0.02 * math.cos(a), 0.02 * math.sin(a), 0.44), (0.08 * math.cos(a), 0.08 * math.sin(a),
                                                                                0.47)], 0.0015, n=6, mat=br)


# ------------------------------------------------------------------ 8 ------
@asset(res=2048, view=(-20, 30), kind="device", title="Portable typewriter", max_tris=80000)
def typewriter():
    enamel = M.plastic("typewriter_enamel", color=(0.012, 0.011, 0.01), rough=0.35, wear=0.6, dirt=0.5, scale=4)
    secs = []
    for z in np.linspace(0, 0.09, 20):
        t = z / 0.09
        w = 0.3 - 0.02 * t
        d0, d1 = -0.14 + 0.12 * t ** 1.4, 0.12
        ring = []
        for a in np.linspace(0, 2 * pi, 48, endpoint=False):
            ca, sa = math.cos(a), math.sin(a)
            x = math.copysign(abs(ca) ** 0.3, ca) * w / 2
            y = (d0 + d1) / 2 + math.copysign(abs(sa) ** 0.3, sa) * (d1 - d0) / 2
            ring.append((x, y, z))
        secs.append(ring)
    G.loft("body", secs, enamel)
    keys = "AZERTYUIOP QSDFGHJKLM WXCVBN,;:"
    rows = [keys[0:10], keys[11:21], keys[22:31]]
    lg = D.Canvas(2048, 256)
    k_all = [c for r in rows for c in r] + list("1234567890")
    for i, ch in enumerate(k_all):
        lg.text((i + 0.5) / len(k_all), 0.5, ch, size=0.45, font="sans_bold")
    legend = lg.save("key_legend")
    keycap = M.plastic("keycap", color=(0.01, 0.01, 0.01), rough=0.3, wear=0.3,
                       layers=[dict(mask=legend, color=(0.7, 0.68, 0.62))])
    ch = chrome("key_chrome")
    idx = 0
    for r, row in enumerate(["1234567890"] + rows):
        for i, c in enumerate(row):
            x = -0.105 + i * 0.022 + r * 0.006
            y = -0.13 + 0.03 * (3 - r) * 0 + 0.028 * r
            z = 0.02 + 0.014 * r
            kidx = k_all.index(c)
            cap = G.cyl(f"key{r}{i}", 0.0085, 0.004, loc=(x, y, z + 0.012), segs=24, bev=0.001, mat=keycap)
            me = cap.data
            lay = me.uv_layers["design"]
            for li, loop in enumerate(me.loops):
                co = me.vertices[loop.vertex_index].co
                lay.data[li].uv = ((kidx + 0.5 + (co.x - x) / 0.017) / len(k_all), 0.5 + (co.y - y) / 0.017 * 8)
            G.torus(f"ring{r}{i}", 0.0088, 0.0012, loc=(x, y, z + 0.0145), segs=24, rsegs=6, mat=ch)
            G.cyl(f"stem{r}{i}", 0.0012, 0.04, loc=(x, y + 0.02, z - 0.01), rot=G.rotd(-60, 0, 0), segs=6, mat=ch)
            idx += 1
    G.box("spacebar", (0.14, 0.012, 0.006), loc=(0.0, -0.155, 0.018), bev=0.002, mat=ch)
    rubber = M.plastic("platen_rubber", color=(0.015, 0.015, 0.015), rough=0.6, wear=0.2, dirt=0.3)
    G.cyl("platen", 0.022, 0.30, loc=(-0.15, 0.1, 0.11), rot=G.rotd(0, 90, 0), segs=48, mat=rubber)
    for s in (1, -1):
        G.cyl(f"knob{s}", 0.02, 0.018, loc=(s * 0.168 - (0.018 if s > 0 else 0), 0.1, 0.11), rot=G.rotd(0, 90, 0),
              segs=48, bev=0.003, mat=enamel)
    G.box("carriage", (0.34, 0.035, 0.02), loc=(0, 0.12, 0.09), bev=0.004, mat=ch)
    G.tube("return_lever", [(-0.17, 0.08, 0.12), (-0.2, 0.05, 0.14), (-0.21, 0.02, 0.145)], 0.003, n=8, mat=ch)
    txt = D.Canvas(1024, 1400)
    lines = ["COMBAT", "", "Organe du Mouvement", "de Libération Française", "", "Paris, le 14 juillet 1943", "",
             "Français ! L'heure approche.", "Tenez-vous prêts.", "Ne collaborez pas.", "", "Vive la France libre."]
    for i, l in enumerate(lines):
        txt.text(0.1, 0.72 - i * 0.045, l, size=0.028 if i else 0.05, font="mono", anchor="lm")
    tp = txt.blur(0.3).save("typed")
    paper = M.paper("typing_paper", color=(0.72, 0.69, 0.6), fibers="rice", stains=0.15, dirt=0.1,
                    layers=[dict(mask=tp, color=(0.03, 0.03, 0.05), opacity=0.9)])
    path = [(0.1 + 0.024 * math.cos(a), 0.11 + 0.024 * math.sin(a)) for a in np.linspace(-2.6, pi / 2, 24)]
    path += [(0.1 + 0.003 * t + 0.02 * t * t, 0.134 + 0.13 * t) for t in np.linspace(0.05, 1, 16)]
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.array(path), axis=0), axis=1))]
    pverts, pfaces, puv = [], [], []
    for (y, z) in path:
        pverts += [(-0.105, y, z), (0.105, y, z)]
    for i in range(len(path) - 1):
        a, b = i * 2, (i + 1) * 2
        v0, v1 = L[i] / L[-1], L[i + 1] / L[-1]
        pfaces.append([a, b, b + 1, a + 1])
        puv.append([(0, v0), (0, v1), (1, v1), (1, v0)])
    sheet = G.mesh("paper", pverts, pfaces, puv, paper)
    G.solidify(sheet, 0.0004)
    for s in (1, -1):
        G.cyl(f"spool{s}", 0.018, 0.008, loc=(s * 0.09, 0.05, 0.09), segs=32, mat=ch)


# ------------------------------------------------------------------ 9 ------
@asset(res=2048, view=(15, 8), kind="tableware", title="Bordeaux bottle and glass")
def wine_and_glass():
    bottle_g = M.glass("bottle_glass", color=(0.05, 0.16, 0.06), rough=0.03)
    prof = G.curve_pts([(0, 0), (0.035, 0.0), (0.0375, 0.004), (0.0375, 0.2), (0.034, 0.225), (0.016, 0.25),
                        (0.0135, 0.29), (0.0145, 0.3), (0.013, 0.305), (0.011, 0.305), (0.011, 0.25),
                        (0.033, 0.22), (0.0345, 0.2), (0.0345, 0.012), (0.012, 0.024), (0, 0.03)], 90)
    G.lathe("bottle", prof, segs=64, mat=bottle_g)
    G.lathe("wine_in", [(0, 0.031), (0.012, 0.025), (0.0343, 0.013), (0.0343, 0.17), (0, 0.17)], segs=64,
            mat=M.liquid("bordeaux", color=(0.14, 0.004, 0.012)))
    lab = D.Canvas(2048, 1024)
    lab.text(0.5, 0.8, "CHÂTEAU", size=0.08, font="serif")
    lab.text(0.5, 0.64, "MONTROSE", size=0.13, font="serif_bold")
    lab.text(0.5, 0.46, "SAINT-ESTÈPHE", size=0.06, font="serif")
    lab.text(0.5, 0.3, "1937", size=0.12, font="serif_bold")
    lab.text(0.5, 0.14, "Mis en bouteille au Château", size=0.045, font="serif")
    lab.rect(0.04, 0.04, 0.96, 0.05).rect(0.04, 0.95, 0.96, 0.96)
    lp = lab.save("label")
    paper = M.paper("label_paper", color=(0.66, 0.6, 0.46), fibers="rice", stains=0.5, dirt=0.3,
                    layers=[dict(mask=lp, color=(0.05, 0.03, 0.02), opacity=0.95)])
    lbl = G.lathe("label", [(0.0379, 0.06), (0.0379, 0.16)], segs=48, mat=paper, caps=False, angle=pi * 0.9)
    G.xform(lbl, rot=(0, 0, -0.95 * pi))
    G.solidify(lbl, 0.0003)
    foil = M.metal("capsule_foil", "copper", color=(0.45, 0.05, 0.05), rough=0.35, wear=0.3, scale=10)
    G.lathe("capsule", [(0.0152, 0.26), (0.0152, 0.306), (0.013, 0.308), (0, 0.308)], segs=48, mat=foil)
    glass = M.glass("wine_glass", color=(0.95, 0.97, 0.96), rough=0.01)
    gp = G.curve_pts([(0, 0), (0.035, 0), (0.036, 0.002), (0.004, 0.006), (0.0035, 0.1), (0.02, 0.11),
                      (0.038, 0.14), (0.04, 0.18), (0.035, 0.21), (0.0335, 0.21), (0.0385, 0.18), (0.0365, 0.14),
                      (0.019, 0.112), (0.0, 0.106)], 90)
    gl = G.lathe("glass", gp, segs=64, mat=glass)
    G.xform(gl, (0.1, -0.04, 0))
    wn = G.lathe("glass_wine", G.curve_pts([(0, 0.107), (0.018, 0.112), (0.033, 0.135), (0.036, 0.15), (0, 0.15)],
                                           20), segs=64, mat=M.liquid("wine_in_glass", color=(0.14, 0.004, 0.012)))
    G.xform(wn, (0.1, -0.04, 0))
    G.cyl("cork", 0.0125, 0.04, loc=(-0.07, -0.05, 0.0125), rot=G.rotd(90, 0, 20), segs=24,
          mat=M.stone("cork", c1=(0.45, 0.3, 0.16), c2=(0.3, 0.18, 0.08), kind="granite", rough=0.9, scale=6))


# ----------------------------------------------------------------- 10 ------
@asset(res=2048, view=(-25, 18), kind="clothing", title="Felt fedora")
def fedora():
    felt = M.fabric("felt", color=(0.07, 0.065, 0.06), weave=2500, rough=0.9, fuzz=0.6, sheen=0.5, wear=0.4)
    crown = G.lathe("crown", G.curve_pts([(0.085, 0.0), (0.086, 0.04), (0.08, 0.1), (0.06, 0.125), (0.02, 0.118),
                                          (0.0, 0.11)], 50), segs=96, mat=felt, caps=False)
    for v in crown.data.vertices:
        x, y, z = v.co
        a = math.atan2(y, x)
        pinch = 1 - 0.08 * max(0, math.cos(a + pi / 2)) ** 4 * (z / 0.12) ** 2
        v.co.x = x * pinch * 1.15
        v.co.y = y * (1 - 0.1 * (z / 0.12) ** 2)
        crease = math.exp(-(x / 0.025) ** 2) * 0.03 * (z / 0.125) ** 3
        v.co.z = z - crease
    G.solidify(crown, 0.0025)
    brim = G.lathe("brim", [(0.08, 0.0), (0.155, 0.0)], segs=128, mat=felt, caps=False)
    for v in brim.data.vertices:
        x, y, z = v.co
        r = math.hypot(x, y)
        a = math.atan2(y, x)
        t = (r - 0.08) / 0.075
        up = 0.03 * t ** 2 * (0.5 + 0.5 * math.sin(a)) - 0.012 * t ** 2 * max(0, -math.sin(a))
        v.co.x = x * 1.12
        v.co.z = up
    G.solidify(brim, 0.003)
    band = M.fabric("grosgrain", color=(0.02, 0.018, 0.016), weave=1800, rough=0.6, sheen=0.7)
    bnd = G.lathe("band", [(0.087, 0.004), (0.0885, 0.004), (0.0885, 0.036), (0.087, 0.036)], segs=128, mat=band)
    G.xform(bnd, scale=(1.15, 1.0, 1.0))
    bow = G.box("bow", (0.004, 0.035, 0.03), loc=(-0.1, -0.02, 0.02), bev=0.003, mat=band)
    _ = bow
