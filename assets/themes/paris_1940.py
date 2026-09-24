"""Occupied Paris, 1940-1944: a comfortable bourgeois apartment."""
import math

import numpy as np

from forge import decal as D
from forge import geo as G
from forge import mat as M
from forge import texsynth as T
from forge.pipeline import asset

pi = math.pi


def walnut(name="walnut", axis="X", **kw):
    """French-polished walnut veneer (synthesized flat-sawn figure), low-gloss varnish."""
    return M.texmat(name, T.get("walnut"), "box", axis=axis, bump=0.25, rough_mul=0.45, dirt=0.35, wear=0.35,
                    scale=0.6)


def oak_polished(name, axis="X"):
    return M.texmat(name, T.get("oak_fresh"), "box", axis=axis, bump=0.25, rough_mul=0.5, dirt=0.3, wear=0.3)


def bakelite(name="bakelite", color=(0.012, 0.009, 0.007), **kw):
    kw.setdefault("rough", 0.18)
    return M.plastic(name, color=color, wear=0.35, dirt=0.4, **kw)


def brass(name="brass", **kw):
    kw.setdefault("rough", 0.25)
    return M.metal(name, "brass", wear=0.5, dirt=0.6, patina=(0.12, 0.09, 0.04), patina_amt=0.12, scratches=0.3,
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
    wal = walnut("radio_walnut", axis="Z")
    shell = G.extrude("cabinet", G.shape_polys(arch), Dp, bev=0.008, bres=3, plane="XZ", mat=wal)
    _ = shell
    # front fretwork panel with art-deco slots, cloth behind
    fret = arch.buffer(-0.03)
    # grille: many narrow vertical slats (4 mm) with 8 mm openings, the openings following the arch
    opening = arch.buffer(-0.05).difference(G.poly2d([(-1, 0), (1, 0), (1, 0.185), (-1, 0.185)]))
    cut = None
    for k in range(-12, 13):
        x = k * 0.0125
        slot = G.poly2d([(x - 0.0042, 0.185), (x + 0.0042, 0.185), (x + 0.0042, 1.0), (x - 0.0042, 1.0)])
        cut = slot if cut is None else cut.union(slot)
    cut = cut.intersection(opening).buffer(0.0008)
    panel = fret.difference(G.poly2d([(-1, 0), (1, 0), (1, 0.16), (-1, 0.16)])).difference(cut)
    fp = G.extrude("fret", G.shape_polys(panel.simplify(0.0003)), 0.008, bev=0.0015, plane="XZ",
                   mat=walnut("fret_walnut", axis="Z"))
    G.xform(fp, (0, -Dp / 2 - 0.004, 0))
    cloth = M.fabric("grille_cloth", color=(0.42, 0.33, 0.19), color2=(0.36, 0.28, 0.16), weave=2200, rough=0.9,
                     fuzz=0.4)
    cl_shape = arch.buffer(-0.026).difference(G.poly2d([(-1, 0), (1, 0), (1, 0.165), (-1, 0.165)]))
    cl = G.extrude("cloth", G.shape_polys(cl_shape), 0.004, plane="XZ", mat=cloth)
    G.xform(cl, (0, -Dp / 2 + 0.001, 0))
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
    body = G.box("body", (0.2, 0.15, 0.075), loc=(0, 0, 0.0375), bev=0.018, segs=4, mat=bk)
    cut = G.box("slope_cut", (0.4, 0.2, 0.2), loc=(0, -0.075 - 0.1 * 0.62 + 0.035, 0.075 + 0.1 * 0.78 - 0.035),
                rot=G.rotd(-50, 0, 0))
    G.boolean(body, cut)
    G.bevel(body, 0.004, 2, angle=30)
    G.box("neck", (0.11, 0.065, 0.04), loc=(0, 0.035, 0.09), bev=0.012, segs=3, mat=bk)
    G.box("felt_base", (0.19, 0.14, 0.004), loc=(0, 0, -0.002), bev=0.001,
          mat=M.fabric("felt_green", color=(0.03, 0.08, 0.04), weave=1500, rough=0.95))
    # rotary dial on the sloped front
    ring = D.Canvas(1024)
    for k in range(10):
        a = math.radians(60 + 28 * k)
        ring.text(0.5 + 0.37 * math.cos(a), 0.5 + 0.37 * math.sin(a), str((k + 1) % 10), size=0.08, font="sans_bold")
    rp = ring.save("dial_numbers")
    card = M.plastic("dial_card", color=(0.65, 0.6, 0.5), rough=0.5, wear=0.0, layers=[dict(mask=rp,
                                                                                            color=(0.02, 0.02, 0.02))])
    card_ob = G.cyl("dial_card", 0.044, 0.003, segs=64, mat=card)
    G.planar_uv(card_ob, "Z")
    disc = G.cyl("dial_disc", 0.045, 0.005, loc=(0, 0, 0.003), segs=64, bev=0.0015, mat=chrome("dial_chrome"))
    for k in range(10):
        a = math.radians(60 + 28 * k)
        h = G.cyl(f"hole{k}", 0.0075, 0.02, loc=(0.033 * math.cos(a), 0.033 * math.sin(a), -0.005), segs=24)
        G.boolean(disc, h)
    stop = G.box("stop", (0.014, 0.003, 0.004), loc=(0.036, -0.034, 0.009), bev=0.0008, mat=chrome("stop_chrome"))
    G.cyl("dial_hub", 0.012, 0.009, loc=(0, 0, 0.004), segs=32, bev=0.002, mat=chrome("hub_chrome"))
    parts_extra = [o for o in G.all_meshes() if o.name == "dial_hub"]
    parts = [card_ob, disc, stop] + parts_extra
    for p in parts:
        G.xform(p, (0, 0, 0), rot=G.rotd(50, 0, 0))
        G.xform(p, (0, -0.058, 0.057))
    # cradle forks
    for s in (1, -1):
        fork = G.curve_pts([(s * 0.04, 0.035, 0.105), (s * 0.05, 0.035, 0.118), (s * 0.07, 0.035, 0.125),
                            (s * 0.08, 0.035, 0.118)], 20)
        G.tube(f"fork{s}", fork, 0.006, n=16, mat=bk)
    # handset resting on the cradle
    hs = G.curve_pts([(-0.11, 0.035, 0.11), (-0.06, 0.035, 0.135), (0.0, 0.035, 0.14), (0.06, 0.035, 0.135),
                      (0.11, 0.035, 0.11)], 60)
    G.tube("handset", hs, 0.011, n=24, mat=bk, scale2=0.8)
    for s in (1, -1):
        cup = G.lathe(f"cup{s}", G.curve_pts([(0.0, 0), (0.012, 0), (0.026, 0.018), (0.028, 0.03), (0.024, 0.034),
                                             (0.0, 0.03)], 30), segs=48, mat=bk)
        G.xform(cup, (s * 0.112, 0.035, 0.122), rot=G.rotd(180, -s * 20, 0))
    cord = M.fabric("cord_cloth", color=(0.06, 0.045, 0.03), weave=1500, rough=0.8)
    guide = np.array(G.curve_pts([(-0.105, 0.03, 0.08), (-0.14, 0.05, 0.03), (-0.12, 0.11, 0.006),
                                  (-0.02, 0.12, 0.006), (0.05, 0.08, 0.02)], 200))
    T, N, B = G.frames(guide)
    tt = np.linspace(0, 1, 200)
    coil = guide + 0.006 * (np.cos(tt * 160)[:, None] * N + np.sin(tt * 160)[:, None] * B)
    G.tube("cord", coil, 0.0022, n=8, mat=cord)


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
    wal = walnut("chair_legs", axis="Z")
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
    oak = oak_polished("gramo_oak", axis="X")
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
          mat=walnut("knob_wood", axis="Z"))


# ------------------------------------------------------------------ 6 ------
@asset(res=2048, view=(-18, 10), pose=(0, 0, 0), pivot="center", kind="weapon", title="Walther P38")
def walther_p38():
    """Walther P38 (1943 production) modelled from real dimensions (mm):
    216 long, 137 high, 125 barrel, slide 29 wide, frame 27, grip 34 over the panels.
    Profile coordinates are in mm with x = 0 at the muzzle, growing to the rear;
    the model is placed with the muzzle towards -X."""
    from shapely.geometry import Polygon
    MM = 0.001

    def P(pts):                       # mm (x from muzzle, z) -> model XZ in metres, muzzle at -X
        return [((x - 108) * MM, z * MM) for x, z in pts]

    def smooth_poly(ctrl, n=160):
        return Polygon(G.curve_pts(P(ctrl), n, closed=True)).buffer(0)

    blue = M.metal("blued_steel", "gunmetal", color=(0.075, 0.077, 0.085), rough=0.32, rough_var=0.03, wear=1.0,
                   dirt=0.55, scratches=0.45, pitting=0.06, rust=0.015, scale=6, edge_radius=0.0012)
    # ---------- barrel (exposed ahead of the slide and through the open-top front)
    bz = 118 * MM
    bar = G.cyl("barrel", 9 * MM, 126 * MM, loc=((0 - 108) * MM, 0, bz), rot=G.rotd(0, 90, 0), segs=48,
                bev=0.0012, mat=blue)
    bore = G.cyl("bore", 4.5 * MM, 0.03, loc=((-5 - 108) * MM, 0, bz), rot=G.rotd(0, 90, 0), segs=24)
    G.boolean(bar, bore)
    G.cyl("muzzle_crown", 9.4 * MM, 3 * MM, loc=((0 - 108) * MM, 0, bz), rot=G.rotd(0, 90, 0), segs=48,
          bev=0.0008, mat=blue)
    # ---------- slide, rear block: lofted rounded section (x 118 -> 207)
    def slide_sec(xm, top, w=14.5, bot=103.0, r=7.0):
        pts = []
        for a in np.linspace(0, 2 * pi, 40, endpoint=False):
            c, s = math.cos(a), math.sin(a)
            y = math.copysign(abs(c) ** 0.35, c) * w
            zc = (top + bot) / 2
            hh = (top - bot) / 2
            zz = zc + math.copysign(abs(s) ** (0.35 if s < 0 else 0.6), s) * hh
            pts.append(((xm - 108) * MM, y * MM, zz * MM))
        return pts
    xs = np.linspace(118, 207, 26)
    secs = []
    for xm in xs:
        t = (xm - 118) / 89
        top = 133.0 - 3.0 * max(0.0, (xm - 200) / 7) ** 2
        secs.append(slide_sec(xm, top, w=14.5 - 1.0 * max(0.0, (xm - 202) / 5)))
    rear = G.loft("slide_rear", secs, blue)
    for k in range(10):                                   # cocking serrations
        g = G.box(f"serr{k}", (1.6 * MM, 0.04, 20 * MM), loc=((166 + k * 3.6 - 108) * MM, 0, 118 * MM))
        G.boolean(rear, g)
    ej = G.box("ejection", (30 * MM, 20 * MM, 14 * MM), loc=((135 - 108) * MM, 12 * MM, 133 * MM), bev=0.002)
    G.boolean(rear, ej)
    # ---------- slide, open-top front: U section extruded along the barrel (x 18 -> 120)
    U = Polygon([(-14.5, 103), (14.5, 103), (14.5, 120), (10.5, 120), (10.5, 108), (-10.5, 108), (-10.5, 120),
                 (-14.5, 120)]).buffer(1.2).buffer(-1.2)
    front = G.extrude("slide_front", G.shape_polys(Polygon([(y * MM, z * MM) for y, z in U.exterior.coords])),
                      102 * MM, bev=0.0012, plane="YZ", mat=blue)
    G.xform(front, ((69 - 108) * MM, 0, 0))
    G.box("front_sight", (4 * MM, 3 * MM, 7 * MM), loc=((24 - 108) * MM, 0, 127.5 * MM), bev=0.0006, mat=blue)
    G.box("rear_sight", (7 * MM, 12 * MM, 5 * MM), loc=((196 - 108) * MM, 0, 135 * MM), bev=0.001, mat=blue)
    # ---------- frame: dust cover + receiver + grip (side profile, well rounded)
    frame = smooth_poly([(28, 103), (208, 103), (216, 97), (215, 84), (213, 60), (216, 30), (217, 8), (210, 1),
                         (152, 1), (145, 8), (143, 40), (136, 76), (124, 91), (60, 92), (40, 94), (30, 97)], 240)
    fr = G.extrude("frame", G.shape_polys(frame), 27 * MM, bev=0.0034, bres=3, plane="XZ", mat=blue)
    G.planar_uv(fr, "Y")
    guard_o = smooth_poly([(122, 93), (124, 74), (112, 60), (86, 58), (66, 64), (60, 80), (62, 93)], 120)
    guard_i = smooth_poly([(115, 92), (117, 76), (108, 66), (87, 64), (71, 69), (67, 82), (69, 92)], 120)
    gd = G.extrude("trigger_guard", G.shape_polys(guard_o.difference(guard_i)), 11 * MM, bev=0.002, bres=3,
                   plane="XZ", mat=blue)
    _ = gd
    trig = smooth_poly([(94, 92), (100, 91), (99, 82), (95, 73), (89, 70), (90, 76), (93, 84)], 60)
    G.extrude("trigger", G.shape_polys(trig), 7 * MM, bev=0.0016, bres=2, plane="XZ", mat=blue)
    ham = smooth_poly([(204, 112), (214, 110), (224, 124), (222, 135), (212, 136), (206, 124)], 80)
    ham = ham.difference(G.circle2d((216 - 108) * MM, 126 * MM, 4 * MM, 24))
    G.extrude("hammer", G.shape_polys(ham), 10 * MM, bev=0.0018, bres=2, plane="XZ", mat=blue)
    # levers and small parts (left side = -Y)
    G.cyl("safety_hub", 7 * MM, 4 * MM, loc=((186 - 108) * MM, -16.5 * MM, 121 * MM), rot=G.rotd(90, 0, 0), segs=28,
          bev=0.001, mat=blue)
    G.box("safety_lever", (6 * MM, 3.5 * MM, 13 * MM), loc=((186 - 108) * MM, -17 * MM, 111 * MM), bev=0.0012,
          mat=blue)
    G.box("slide_stop", (16 * MM, 3.5 * MM, 6 * MM), loc=((128 - 108) * MM, -14.8 * MM, 99 * MM), bev=0.001, mat=blue)
    G.box("takedown", (6 * MM, 3.5 * MM, 12 * MM), loc=((58 - 108) * MM, -14.8 * MM, 97 * MM), bev=0.001, mat=blue)
    G.box("mag_base", (58 * MM, 24 * MM, 5 * MM), loc=((180 - 108) * MM, 0, 0.5 * MM), bev=0.0015, mat=blue)
    G.torus("lanyard", 6 * MM, 1.4 * MM, loc=((213 - 108) * MM, 0, 1 * MM), rot=G.rotd(90, 0, 0), segs=16, rsegs=6,
            mat=blue)
    # ---------- grip panels: bulged bakelite with horizontal grooves
    grooves = D.Canvas(1024)
    for k in range(64):
        grooves.line([(0.04, 0.05 + k * 0.0142), (0.96, 0.05 + k * 0.0142)], 0.0042)
    grooves.circle(0.52, 0.5, 0.075, fill=0)
    gm = grooves.blur(0.6).save("grip_grooves")
    grips = M.plastic("grip_bakelite", color=(0.03, 0.017, 0.01), marble=(0.06, 0.03, 0.016), rough=0.42,
                      wear=0.6, dirt=0.6, layers=[dict(mask=gm, height=-1.0)], bump_strength=0.45)
    gp = smooth_poly([(143, 88), (207, 92), (208, 62), (211, 12), (154, 9), (148, 40)], 100)
    for sgn in (1, -1):
        g = G.extrude(f"grip{sgn}", G.shape_polys(gp), 4 * MM, bev=0.0016, bres=3, plane="XZ", mat=grips)
        G.planar_uv(g, "Y", stretch=True)
        cx, cz = (178 - 108) * MM, 50 * MM
        for v in g.data.vertices:
            d2 = ((v.co.x - cx) / 0.034) ** 2 + ((v.co.z - cz) / 0.046) ** 2
            v.co.y *= 1.0 + 1.1 * max(0.0, 1 - d2)          # domed outer face
        g.data.update()
        G.xform(g, (0, sgn * 15.5 * MM, 0))
        G.cyl(f"screw{sgn}", 3.6 * MM, 2 * MM, loc=((178 - 108) * MM, sgn * 20.6 * MM, 50 * MM), rot=G.rotd(90, 0, 0),
              segs=20, bev=0.0006, mat=blue)


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
@asset(res=2048, view=(-22, 28), kind="device", title="Portable typewriter", max_tris=90000)
def typewriter():
    """1930s portable typewriter (Japy / Remington Portable type). Front faces -Y."""
    deco = D.Canvas(2048)
    deco.text(0.5, 0.2, "JAPY", size=0.05, font="serif_bold")
    for v in (0.06, 0.08):
        deco.line([(0.05, v), (0.95, v)], 0.0015)
    deco_p = deco.blur(0.4).save("typewriter_gold")
    enamel = M.plastic("typewriter_enamel", color=(0.01, 0.009, 0.008), rough=0.22, wear=0.55, dirt=0.5, scale=4,
                       layers=[dict(mask=deco_p, color=(0.85, 0.62, 0.25), metal=1.0, rough=0.3)])
    ch = chrome("typewriter_chrome")
    blk = bakelite("platen_knob")
    W = 0.30
    # body: side profile extruded across the width (sloped keyboard deck, flat top, rounded back)
    prof = G.curve_pts([(-0.15, 0.0), (-0.152, 0.018), (-0.14, 0.03), (-0.02, 0.083), (0.03, 0.092), (0.11, 0.094),
                        (0.135, 0.075), (0.138, 0.0)], 60)
    from shapely.geometry import Polygon
    body = G.extrude("body", G.shape_polys(Polygon(prof).buffer(0)), W, bev=0.012, bres=3, plane="YZ", mat=enamel)
    G.planar_uv(body, "X")
    basket_hole = G.cyl("basket_hole", 0.1, 0.1, loc=(0, 0.075, 0.06), segs=64)
    G.xform(basket_hole, scale=(1.0, 0.45, 1.0))
    G.boolean(body, basket_hole)
    # typebar basket: fan of thin bars converging on the printing point
    for i in range(38):
        a = math.radians(-78 + 156 * i / 37)
        r0 = 0.085
        p0 = (r0 * math.sin(a), 0.07 - 0.035 * math.cos(a), 0.068)
        p1 = (0.35 * r0 * math.sin(a), 0.07 - 0.012 * math.cos(a), 0.086)
        G.tube(f"typebar{i}", [p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.082), p1], 0.0012, n=4, mat=ch)
    seg = G.lathe("segment", [(0.02, 0.078), (0.028, 0.078), (0.028, 0.086), (0.02, 0.086)], segs=48, mat=ch,
                  angle=pi)
    G.xform(seg, (0, 0.075, 0.0))
    # keys: glass-topped caps with chrome rims, four stepped rows (AZERTY)
    rows = ["1234567890", "AZERTYUIOP", "QSDFGHJKLM", "WXCVBN,;:"]
    k_all = [c for r in rows for c in r]
    lg = D.Canvas(4096, 128)
    for i, c in enumerate(k_all):
        lg.text((i + 0.5) / len(k_all), 0.5, c, size=0.55, font="sans_bold")
    legend = lg.save("key_legend")
    keycap = M.plastic("keycap_glass", color=(0.012, 0.012, 0.012), rough=0.08, wear=0.2,
                       layers=[dict(mask=legend, color=(0.75, 0.73, 0.68), rough=0.3)])
    for r, row in enumerate(rows):
        z = 0.034 + 0.017 * (3 - r) * 0 + 0.016 * r
        y = -0.118 + 0.028 * r
        for i, c in enumerate(row):
            x = -0.118 + i * 0.0245 + (r % 2) * 0.006 + (0.012 if r == 3 else 0)
            kidx = k_all.index(c)
            cap = G.cyl(f"key{r}{i}", 0.0072, 0.0035, loc=(x, y, z + 0.012), segs=24, bev=0.0012, mat=keycap)
            lay = cap.data.uv_layers["design"]
            for li, loop in enumerate(cap.data.loops):
                co = cap.data.vertices[loop.vertex_index].co
                lay.data[li].uv = ((kidx + 0.5 + (co.x - x) / 0.016) / len(k_all), 0.5 + (co.y - y) / 0.016)
            G.torus(f"rim{r}{i}", 0.0074, 0.0011, loc=(x, y, z + 0.0145), segs=24, rsegs=6, mat=ch)
            G.tube(f"lever{r}{i}", [(x, y, z + 0.012), (x, y + 0.012, z - 0.002), (x * 0.9, y + 0.05, z - 0.01)],
                   0.0011, n=4, mat=ch)
    G.box("spacebar", (0.15, 0.011, 0.005), loc=(0.0, -0.138, 0.03), bev=0.002, mat=ch)
    for s in (1, -1):
        G.cyl(f"shift{s}", 0.0075, 0.0035, loc=(s * 0.135, -0.105, 0.05), segs=24, bev=0.0012, mat=keycap)
        G.cyl(f"spool{s}", 0.03, 0.009, loc=(s * 0.095, 0.075, 0.093), segs=48, bev=0.003, mat=enamel)
        G.cyl(f"spool_hub{s}", 0.008, 0.012, loc=(s * 0.095, 0.075, 0.095), segs=24, bev=0.002, mat=ch)
    # carriage on top at the back
    G.box("carriage_rail", (W + 0.04, 0.03, 0.012), loc=(0, 0.105, 0.1), bev=0.004, mat=ch)
    rubber = M.plastic("platen_rubber", color=(0.016, 0.016, 0.016), rough=0.65, wear=0.15, dirt=0.3)
    G.cyl("platen", 0.021, W + 0.02, loc=(-(W + 0.02) / 2, 0.1, 0.13), rot=G.rotd(0, 90, 0), segs=48, mat=rubber)
    for s in (1, -1):
        kb = G.lathe(f"knob{s}", G.curve_pts([(0, 0), (0.019, 0.0), (0.021, 0.006), (0.021, 0.014), (0.017, 0.018),
                                              (0, 0.019)], 20), segs=40, mat=blk)
        G.xform(kb, (s * (W / 2 + 0.012), 0.1, 0.13), rot=G.rotd(0, s * 90, 0))
        G.box(f"end_plate{s}", (0.006, 0.05, 0.05), loc=(s * (W / 2 + 0.006), 0.105, 0.125), bev=0.004, mat=enamel)
    G.tube("bail", [(-0.12, 0.078, 0.138), (0.12, 0.078, 0.138)], 0.0018, n=8, mat=ch)
    for x in (-0.05, 0.05):
        G.cyl(f"bail_roller{x}", 0.0045, 0.012, loc=(x - 0.006, 0.078, 0.138), rot=G.rotd(0, 90, 0), segs=16,
              mat=rubber)
    G.tube("return_lever", G.curve_pts([(-W / 2 - 0.01, 0.09, 0.14), (-W / 2 - 0.035, 0.07, 0.15),
                                        (-W / 2 - 0.05, 0.035, 0.152)], 20), 0.0032, n=10, mat=ch)
    G.box("paper_table", (0.2, 0.004, 0.07), loc=(0, 0.126, 0.165), rot=G.rotd(-20, 0, 0), bev=0.002, mat=enamel)
    txt = D.Canvas(1024, 1400)
    lines = ["COMBAT", "", "Organe du Mouvement", "de Libération Française", "", "Paris, le 14 juillet 1943", "",
             "Français ! L'heure approche.", "Tenez-vous prêts.", "Ne collaborez pas.", "", "Vive la France libre."]
    for i, l in enumerate(lines):
        txt.text(0.1, 0.72 - i * 0.045, l, size=0.028 if i else 0.05, font="mono", anchor="lm")
    tp = txt.blur(0.3).save("typed")
    paper = M.paper("typing_paper", color=(0.72, 0.69, 0.6), fibers="rice", stains=0.15, dirt=0.1,
                    layers=[dict(mask=tp, color=(0.03, 0.03, 0.05), opacity=0.9)])
    path = [(0.1 + 0.023 * math.cos(a), 0.13 + 0.023 * math.sin(a)) for a in np.linspace(-2.6, pi / 2, 24)]
    path += [(0.1 + 0.01 * t + 0.03 * t * t, 0.153 + 0.13 * t) for t in np.linspace(0.05, 1, 16)]
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
@asset(res=2048, view=(-28, 16), kind="clothing", title="Felt fedora")
def fedora():
    """Men's felt fedora, c. 1940: teardrop crown with front pinches, snap brim, grosgrain band and bow.
    Front of the hat faces -Y."""
    felt = M.fabric("fur_felt", color=(0.045, 0.04, 0.034), color2=(0.036, 0.032, 0.028), weave=900, rough=0.85,
                    fuzz=0.2, sheen=0.0, wear=0.08, dirt=0.25, bump_strength=0.1)
    band = M.fabric("grosgrain", color=(0.012, 0.011, 0.01), weave=2600, rough=0.5, sheen=0.0, wear=0.0)
    # --- crown: elliptical sections, domed top, then crease + pinches as deformations
    A, B, Hc = 0.098, 0.083, 0.128
    secs = []
    for z in np.r_[np.linspace(0.0, 0.09, 12), np.linspace(0.095, Hc, 10)]:
        k = 1.0 - 0.1 * (z / Hc)
        if z > 0.09:
            k *= math.sqrt(max(1 - ((z - 0.09) / (Hc - 0.09 + 0.004)) ** 2, 0.02))
        secs.append([(A * k * math.sin(a), -B * k * math.cos(a), z) for a in np.linspace(0, 2 * pi, 72, endpoint=False)])
    secs.append([(0.0, 0.0, Hc + 0.002)] * 72)          # pole: closes the top
    crown = G.loft("crown", secs, felt, closed=True, cap=False)
    me = crown.data
    for v in me.vertices:
        x, y, z = v.co
        t = max(0.0, (z - 0.06) / (Hc - 0.06))
        back = 0.5 + 0.5 * (y / B)                       # 0 at front, 1 at back
        crease = 0.03 * math.exp(-(x / 0.03) ** 2) * t ** 2.0 * (0.5 + 0.5 * back)
        v.co.z = z - crease
        for sx in (1, -1):                               # front pinches
            d2 = ((x - sx * 0.045) / 0.028) ** 2 + ((y + 0.055) / 0.03) ** 2 + ((z - 0.095) / 0.03) ** 2
            f = 0.018 * math.exp(-d2)
            v.co.x -= sx * f
            v.co.y += f * 0.4
    me.update()
    G.solidify(crown, 0.0028, offset=-1.0)
    # --- brim: snap brim, down in front, up at back and sides, bound edge
    verts, faces = [], []
    nr, na = 10, 96
    for i in range(nr + 1):
        s = i / nr
        for j in range(na):
            a = 2 * pi * j / na
            ca, sa = math.sin(a), -math.cos(a)            # sa = -1 at front (-Y)
            w = 0.058 + 0.008 * abs(ca)                   # a touch wider at the sides
            r = s * w
            x = (A + r) * ca * 1.0
            y = (B + r) * sa
            up = (0.03 * max(0.0, sa) + 0.016 * abs(ca)) * s ** 2      # back and sides turn up
            down = 0.026 * max(0.0, -sa) ** 1.5 * s ** 1.5              # front snapped down
            verts.append((x, y, up - down))
    for i in range(nr):
        for j in range(na):
            a, b = i * na + j, i * na + (j + 1) % na
            faces.append([a, b, b + na, a + na])
    brim = G.mesh("brim", verts, faces, None, felt)
    G.solidify(brim, 0.0032, offset=0.0)
    edge = [verts[nr * na + j] for j in range(na)] + [verts[nr * na]]
    G.tube("binding", edge, 0.0024, n=10, mat=band)
    # --- band and bow (left side, +X from the wearer's view facing -Y -> bow at +X)
    bnd = G.lathe("band", [(1.0, 0.004), (1.0, 0.038)], segs=96, mat=band, caps=False)
    for v in bnd.data.vertices:
        a = math.atan2(v.co.x, -v.co.y)
        k = 1.0 - 0.1 * (v.co.z / Hc)
        v.co.x, v.co.y = (A * k + 0.0022) * math.sin(a), -(B * k + 0.0022) * math.cos(a)
    bnd.data.update()
    G.solidify(bnd, 0.0012, offset=1.0)
    bx, by = A + 0.004, 0.012
    bow = G.box("bow_knot", (0.008, 0.016, 0.02), loc=(bx, by, 0.021), bev=0.003, mat=band)
    _ = bow
    for s in (1, -1):
        loop = G.box(f"bow_loop{s}", (0.005, 0.026, 0.016), loc=(bx - 0.001, by + s * 0.018, 0.021), bev=0.004,
                     mat=band)
        G.xform(loop, (0, 0, 0), rot=(0, 0, 0))
    G.box("bow_tail", (0.004, 0.012, 0.03), loc=(bx + 0.001, by + 0.006, 0.006), bev=0.002, mat=band)
