"""High-detail tileable PBR texture synthesis (numpy), simulating material structure.

Each generator returns / caches three maps in FORGE_TEXCACHE (default /tmp/forge_tex):
  <name>_color.png (sRGB), <name>_rough.png (linear), <name>_height.png (16-bit)
All maps tile seamlessly (periodic noise, wrap-around drawing).

    from forge import texsynth as T
    paths = T.get("oak_weathered")      # dict(color=..., rough=..., height=..., size_m=(w, h))
"""
import hashlib
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

CACHE = os.environ.get("FORGE_TEXCACHE", "/tmp/forge_tex")


# ------------------------------------------------------------------ noise ---
def fft_noise(h, w, sig_u, sig_v, rng):
    """Periodic gaussian-filtered noise (zero mean, unit std). sig_* in cycles/px."""
    white = rng.standard_normal((h, w))
    fu = np.fft.fftfreq(w)[None, :]
    fv = np.fft.fftfreq(h)[:, None]
    filt = np.exp(-0.5 * ((fu / sig_u) ** 2 + (fv / sig_v) ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * filt))
    n -= n.mean()
    return n / (n.std() + 1e-9)


def fbm(h, w, base, rng, octaves=5, gain=0.5, aniso=1.0):
    out, amp, s, norm = np.zeros((h, w)), 1.0, base, 0.0
    for _ in range(octaves):
        out += amp * fft_noise(h, w, s, s * aniso, rng)
        norm += amp
        amp *= gain
        s *= 2
    return out / norm


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def srgb(c):
    """sRGB tuple (0-1) -> linear, for authoring colours by eye."""
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def lerp(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) == 2 else t
    return a + (b - a) * t


def periodic_points(n, h, w, rng):
    return rng.random((n, 2)) * [h, w]


def voronoi(h, w, pts, k=2):
    """Periodic F1/F2 distances + nearest index for points (row, col)."""
    from scipy.spatial import cKDTree
    offs = [(dy, dx) for dy in (-h, 0, h) for dx in (-w, 0, w)]
    allp = np.concatenate([pts + o for o in offs])
    tree = cKDTree(allp)
    rr, cc = np.mgrid[0:h, 0:w]
    d, i = tree.query(np.stack([rr.ravel() + 0.5, cc.ravel() + 0.5], 1), k=k, workers=-1)
    return d[:, 0].reshape(h, w), d[:, 1].reshape(h, w), (i[:, 0] % len(pts)).reshape(h, w)


def wrap_draw(draw_fn, W, H, pts_list):
    """Call draw_fn(pts) for the shape and its wrapped copies near borders."""
    for dx in (-W, 0, W):
        for dy in (-H, 0, H):
            draw_fn([(x + dx, y + dy) for x, y in pts_list])


# ------------------------------------------------------------------ saving --
def _save(name, color_lin, rough, height, size_m):
    """PBR outputs: albedo (clamped to physically plausible 0.012-0.75 linear), roughness,
    16-bit height, and a separate ambient-occlusion map derived from the height field."""
    os.makedirs(CACHE, exist_ok=True)
    color_lin = np.clip(color_lin, 0.012, 0.75)
    c = (lin2srgb(color_lin) * 255 + 0.5).astype(np.uint8)
    hn = (height - height.mean()) / (height.std() + 1e-9)
    cav = np.clip(ndimage.gaussian_filter(hn, 6) - hn, 0, None) + 0.5 * np.clip(ndimage.gaussian_filter(hn, 2) - hn, 0, None)
    ao = np.clip(1 - 0.35 * cav, 0.3, 1)
    Image.fromarray((ao * 255 + 0.5).astype(np.uint8)).save(os.path.join(CACHE, name + "_ao.png"))
    Image.fromarray(c).save(os.path.join(CACHE, name + "_color.png"))
    Image.fromarray((np.clip(rough, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(CACHE, name + "_rough.png"))
    h = height - height.min()
    h = h / (h.max() + 1e-9)
    Image.fromarray((h * 65535).astype(np.uint16)).save(os.path.join(CACHE, name + "_height.png"))
    meta = dict(size_m=size_m, height_range_mm=float((height.max() - height.min())))
    with open(os.path.join(CACHE, name + ".meta"), "w") as f:
        f.write(repr(meta))


def _paths(name):
    return {k: os.path.join(CACHE, f"{name}_{k}.png") for k in ("color", "rough", "height", "ao")}


def get(name, **kw):
    """Return cached texture set, generating it if missing or its generator changed."""
    gen = GENERATORS[name]
    src = open(__file__).read()
    key = hashlib.sha1((src + name + repr(sorted(kw.items()))).encode()).hexdigest()[:10]
    tag = f"{name}_{key}"
    p = _paths(tag)
    if not all(os.path.exists(x) for x in p.values()):
        col, rough, h, size_m = gen(**kw)
        _save(tag, col, rough, h, size_m)
    meta = eval(open(os.path.join(CACHE, tag + ".meta")).read())
    return dict(p, **meta)


# =================================================================== WOOD ===
def _wood(weathered=False, species="oak", W=2048, H=4096, size=(0.5, 1.0), seed=1, cut="flat", aged=False):
    """Board surface. U across the grain, V along it (metres = size).
    cut="flat": flat-sawn (cathedral figure); cut="quarter": radially split / quarter-sawn
    (straight parallel grain with medullary-ray flecks, as Viking-age split oak)."""
    rng = np.random.default_rng(seed)
    su, sv = size
    u = (np.arange(W) + 0.5) / W * su
    v = (np.arange(H) + 0.5) / H * sv
    U, V = np.meshgrid(u, v)
    px_mm = su * 1000 / W
    # log geometry: pith at the board centre line, cut plane distance y0 varies (taper, sweep)
    y0 = 0.11 + 0.012 * np.sin(2 * np.pi * V / sv) + 0.006 * fft_noise(H, W, 1 / 4000, 1 / 1500, rng)
    x = np.abs(U - su / 2)
    x = np.minimum(x, su - x) if False else x
    if cut == "quarter":
        r = 0.04 + U * 0.9 + 0.004 * np.sin(2 * np.pi * V / sv)
    else:
        r = np.sqrt(x ** 2 + y0 ** 2)
    r += 0.0025 * fbm(H, W, 1 / 600, rng, 4, aniso=0.08)          # grain wander, stretched along V
    # knots: deflect rings and add dark cores
    knots = []
    for _ in range((2 if species != "walnut" else 1) if cut == "flat" else 1):
        ku, kv = su * (0.2 + 0.6 * rng.random()), sv * (0.15 + 0.7 * rng.random())
        ks = 0.006 + 0.008 * rng.random()
        d2 = ((U - ku) / (ks * 1.4)) ** 2 + ((V - kv) / (ks * 3.5)) ** 2
        r += 0.004 * np.exp(-d2) * np.sign(U - ku + 1e-6)
        knots.append((ku, kv, ks))
    # ring phase with per-ring width variation
    w0 = {"oak": 0.0026, "walnut": 0.0034, "ash": 0.0030}[species]
    ring_rng = np.random.default_rng(seed + 7)
    knots_r = np.linspace(0, 0.4, 400)
    jitter = np.cumsum(ring_rng.normal(0, 0.18, 400))
    phase = r / w0 + np.interp(r, knots_r, jitter)
    f = phase - np.floor(phase)
    late = ss(0.5, 0.85, f) * (1 - ss(0.96, 1.0, f))
    early = 1 - ss(0.12, 0.35, f)
    # pores (ring-porous oak/ash): short dark dashes in earlywood
    pore_n = fft_noise(H, W, 1 / 2.2, 1 / 30, rng)
    pores = ss(1.6, 2.4, pore_n) * early * (1.0 if species in ("oak", "ash") else 0.35)
    fine = fft_noise(H, W, 1 / 3, 1 / 60, rng)
    # medullary rays (oak silver figure), faint flecks across the grain
    rays = ss(2.3, 3.0, fft_noise(H, W, 1 / 40, 1 / 3, rng)) * (0.6 if species == "oak" else 0.0)
    if cut == "quarter" and species == "oak":
        rays = ss(1.6, 2.6, fft_noise(H, W, 1 / 25, 1 / 6, rng)) * 1.0      # silver figure
    pal = {
        "oak": ((0.55, 0.42, 0.29), (0.35, 0.24, 0.14)),
        "walnut": ((0.36, 0.24, 0.155), (0.24, 0.15, 0.09)),
        "ash": ((0.72, 0.60, 0.44), (0.52, 0.40, 0.26)),
    }[species]
    if aged:          # smoke-darkened interior oak
        pal = ((0.40, 0.30, 0.21), (0.21, 0.145, 0.09))
    ce, cl = srgb(pal[0]), srgb(pal[1])
    col = lerp(ce, cl, np.clip(late * 0.9 + 0.1 * fine, 0, 1))
    col = col * (1 + 0.06 * fbm(H, W, 1 / 300, rng, 3))[..., None]
    col = lerp(col, col * 0.45, pores * 0.8)
    col = lerp(col, col * 1.15, rays * 0.5)
    height = 0.02 * late - 0.06 * pores + 0.005 * fine
    rough = 0.55 + 0.1 * late - 0.05 * rays + 0.08 * pores
    # knot cores
    for (ku, kv, ks) in knots:
        kr = np.sqrt(((U - ku) / (ks * 0.8)) ** 2 + ((V - kv) / (ks * 1.3)) ** 2)
        core = 1 - ss(0.75, 1.0, kr)
        kring = 0.5 + 0.5 * np.cos(kr * 40)
        kc = lerp(srgb((0.30, 0.18, 0.09)), srgb((0.12, 0.07, 0.035)), kring)
        col = lerp(col, kc, core)
        height = height - 0.15 * core * (0.5 + 0.5 * kring)
        crack = core * ss(2.2, 2.8, np.abs(fft_noise(H, W, 1 / 3, 1 / 3, rng)))
        col = lerp(col, col * 0.2, crack)
    # large-scale tone and colour drift (breaks tiling)
    drift = fbm(H, W, 1 / 1500, rng, 3)
    col = col * (1 + 0.1 * drift)[..., None]
    if weathered:
        # sun-greyed surface: earlywood eroded (lower, darker), latewood ridges stand proud and silvery
        grey_l = srgb((0.64, 0.62, 0.58))
        grey_d = srgb((0.38, 0.36, 0.32))
        g = lerp(grey_d, grey_l, np.clip(late * 0.9 + 0.2 * fine + 0.1, 0, 1))
        cover = np.clip(0.75 + 0.25 * fbm(H, W, 1 / 700, rng, 4), 0, 1)
        col = lerp(col * 0.8, g, cover)
        height = height + 0.35 * late - 0.2 * early
        # checking: long thin cracks along the grain
        ck = fft_noise(H, W, 1 / 1.5, 1 / 400, rng)
        cracks = ss(2.6, 3.2, ck)
        cracks = ndimage.maximum_filter(cracks, size=(1, 3))
        col = lerp(col, srgb((0.05, 0.04, 0.03)), cracks * 0.9)
        height = height - 1.0 * cracks
        # grime settles in the eroded earlywood (real material colour, not shading); faint algae
        col = lerp(col, srgb((0.16, 0.14, 0.11)), early * 0.35)
        algae = ss(0.6, 1.2, fbm(H, W, 1 / 250, rng, 4, aniso=0.2)) * 0.35
        col = lerp(col, srgb((0.25, 0.30, 0.18)), algae)
        rough = 0.78 + 0.12 * fine * 0.3 + 0.1 * cracks
    if aged:
        # foot traffic: polished paths, scuffs and grit in the grain
        img = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(img)
        for _ in range(900):
            x0, y0 = rng.random() * W, rng.random() * H
            a = rng.normal(np.pi / 2, 0.6)
            Lp = 15 + 120 * rng.random()
            pts = [(x0, y0), (x0 + np.cos(a) * Lp, y0 + np.sin(a) * Lp)]
            wrap_draw(lambda p: dr.line(p, fill=int(120 + 135 * rng.random()), width=2), W, H, pts)
        sc = ndimage.gaussian_filter(np.asarray(img, dtype=float) / 255, 0.7)
        col = lerp(col, col * 1.35, sc * 0.5)
        height = height - 0.2 * sc
        worn = ss(-0.2, 0.8, fbm(H, W, 1 / 800, rng, 4))
        col = lerp(col, srgb((0.12, 0.09, 0.06)), (1 - worn) * 0.3 * early[..., None].squeeze(-1))
        rough = 0.78 - 0.14 * worn + 0.06 * sc
    return col, rough, height, size


# ================================================================= THATCH ===
def _thatch(W=2048, H=2048, size=(0.5, 0.5), seed=3, n=4200):
    """Long-straw thatch: thousands of overlapping stalks running down the slope (V)."""
    rng = np.random.default_rng(seed)
    idimg = Image.new("I", (W, H), 0)
    colimg = Image.new("RGB", (W, H), (0, 0, 0))
    ordimg = Image.new("I", (W, H), 0)
    di, dc, do = ImageDraw.Draw(idimg), ImageDraw.Draw(colimg), ImageDraw.Draw(ordimg)
    pal = [(0.66, 0.54, 0.30), (0.56, 0.45, 0.26), (0.47, 0.40, 0.30), (0.40, 0.34, 0.26), (0.30, 0.25, 0.17),
           (0.62, 0.58, 0.48)]
    for k in range(1, n + 1):
        x0, y0 = rng.random() * W, rng.random() * H
        L = (0.25 + 0.4 * rng.random()) * H
        ang = np.pi / 2 + rng.normal(0, 0.09)
        bend = rng.normal(0, 0.03)
        wpx = int(9 + 9 * rng.random())
        pts = []
        for t in np.linspace(0, 1, 6):
            a = ang + bend * t
            pts.append((x0 + np.cos(a) * L * t + 6 * np.sin(t * 9 + k), y0 + np.sin(a) * L * t))
        c = np.array(pal[rng.integers(len(pal))]) * (0.8 + 0.35 * rng.random())
        c8 = tuple(int(255 * min(1, x)) for x in c)
        wrap_draw(lambda p: di.line(p, fill=k, width=wpx), W, H, pts)
        wrap_draw(lambda p: dc.line(p, fill=c8, width=wpx), W, H, pts)
        wrap_draw(lambda p: do.line(p, fill=k, width=wpx), W, H, pts)
    ids = np.asarray(idimg, dtype=np.int64)
    col = srgb(np.asarray(colimg, dtype=float) / 255)
    order = np.asarray(ordimg, dtype=float) / n
    # stalk cross-section: distance to the stalk's own boundary -> rounded cylinder profile
    b = np.zeros_like(ids, dtype=bool)
    for ax in (0, 1):
        b |= ids != np.roll(ids, 1, axis=ax)
    dist = ndimage.distance_transform_edt(~b)
    prof = np.sqrt(np.clip(dist / 6.0, 0, 1))
    height = 0.8 * order + 1.2 * prof + 0.05 * fbm(H, W, 1 / 200, rng, 3)
    # stalk nodes and streaks along each stalk
    streak = fft_noise(H, W, 1 / 1.5, 1 / 120, rng)
    col = col * (1 + 0.12 * streak)[..., None]
    deep = 1 - order                                   # lower stalks are older, darker straw (albedo)
    col = lerp(col, col * 0.55, np.clip(deep - 0.4, 0, 1) * 0.6)
    # weathering: greyed top layer, darker deeper layers
    grey = ss(-0.2, 0.8, fbm(H, W, 1 / 500, rng, 4))
    col = lerp(col, np.mean(col, axis=-1, keepdims=True) * np.array(srgb((0.95, 0.93, 0.88))) * 0.9, grey * 0.55)
    rough = 0.72 + 0.2 * (1 - prof) + 0.05 * streak
    return col, rough, height, size


# ================================================================== EARTH ===
def _earth(W=2048, H=2048, size=(1.0, 1.0), seed=5, straw=True):
    """Trampled earth floor: clods, pebbles, chaff, charcoal, damp patches."""
    rng = np.random.default_rng(seed)
    px = size[0] / W
    base = fbm(H, W, 1 / 700, rng, 6)
    lumps = fbm(H, W, 1 / 60, rng, 4, gain=0.55)
    clods = np.minimum(ss(-0.3, 1.2, lumps), 0.6)                 # trampled: tops flattened
    height = 0.6 * base + 0.9 * clods + 0.35 * fbm(H, W, 1 / 12, rng, 3) + 0.25 * fft_noise(H, W, 1 / 2, 1 / 2, rng)
    dry = ss(-0.6, 1.2, ndimage.gaussian_filter(clods, 6) + 0.4 * base)
    soil_d, soil_l = srgb((0.28, 0.22, 0.16)), srgb((0.40, 0.33, 0.25))
    col = lerp(soil_d, soil_l, np.clip(0.6 * dry + 0.4 * (0.5 + 0.3 * fbm(H, W, 1 / 400, rng, 4)), 0, 1))
    grit = fft_noise(H, W, 1 / 1.5, 1 / 1.5, rng)
    col = col * (1 + 0.06 * grit)[..., None]
    img = Image.new("RGB", (W, H))
    hmap = Image.new("L", (W, H), 0)
    d, dh = ImageDraw.Draw(img), ImageDraw.Draw(hmap)
    cm = np.zeros((H, W), dtype=bool)
    peb = Image.new("L", (W, H), 0)
    dp = ImageDraw.Draw(peb)
    for _ in range(220):
        cx, cy = rng.random() * W, rng.random() * H
        rx = (1.0 + 7 * rng.random() ** 3) / (px * 1000)
        ry = rx * (0.55 + 0.4 * rng.random())
        c = [(0.40, 0.37, 0.33), (0.33, 0.28, 0.23), (0.46, 0.43, 0.39), (0.27, 0.24, 0.21)][rng.integers(4)]
        c8 = tuple(int(255 * x * (0.85 + 0.2 * rng.random())) for x in c)
        box = [cx - rx, cy - ry, cx + rx, cy + ry]
        d.ellipse(box, fill=c8)
        dp.ellipse(box, fill=255)
        dh.ellipse(box, fill=int(150 + 100 * rng.random()))
    if straw:
        for _ in range(140):
            x0, y0 = rng.random() * W, rng.random() * H
            a = rng.random() * np.pi
            L = (15 + 70 * rng.random()) / (px * 1000)
            bend = rng.normal(0, 0.25)
            pts = [(x0 + np.cos(a + bend * t) * L * t, y0 + np.sin(a + bend * t) * L * t) for t in np.linspace(0, 1, 5)]
            c8 = tuple(int(255 * x) for x in np.array((0.46, 0.38, 0.22)) * (0.55 + 0.35 * rng.random()))
            wpx = int(4 + 4 * rng.random())
            wrap_draw(lambda p: d.line(p, fill=c8, width=wpx), W, H, pts)
            wrap_draw(lambda p: dp.line(p, fill=255, width=wpx), W, H, pts)
            wrap_draw(lambda p: dh.line(p, fill=90, width=wpx), W, H, pts)
    for _ in range(120):
        cx, cy = rng.random() * W, rng.random() * H
        r = (0.5 + 2.0 * rng.random() ** 2) / (px * 1000)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(8, 7, 6))
        dp.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    pm = np.asarray(peb, dtype=float) / 255
    pm = ndimage.gaussian_filter(pm, 0.7)
    pc = srgb(np.asarray(img, dtype=float) / 255)
    ph = ndimage.gaussian_filter(np.asarray(hmap, dtype=float) / 255, 1.5)
    col = lerp(col, pc, pm)
    height = height + 1.2 * ph
    damp = ss(0.3, 0.9, fbm(H, W, 1 / 900, rng, 4))
    col = col * (1 - 0.25 * damp)[..., None]             # damp soil is genuinely darker
    rough = 0.93 - 0.12 * damp - 0.1 * pm
    return col, rough, height, size


# ======================================================== GRANITE + LICHEN ===
def _granite(W=2048, H=2048, size=(0.6, 0.6), seed=9, lichen=1.0):
    rng = np.random.default_rng(seed)
    px_mm = size[0] * 1000 / W
    pts = periodic_points(int(W * H / (3.0 / px_mm) ** 2 / 1.2), H, W, rng)
    f1, f2, idx = voronoi(H, W, pts)
    kind = rng.random(len(pts))
    mineral = np.where(kind < 0.35, 0, np.where(kind < 0.8, 1, 2))[idx]      # quartz, feldspar, biotite
    tone = (0.85 + 0.3 * rng.random(len(pts)))[idx]
    q, fs, bi = srgb((0.56, 0.55, 0.53)), srgb((0.58, 0.51, 0.47)), srgb((0.24, 0.24, 0.24))
    col = np.where((mineral == 0)[..., None], q, np.where((mineral == 1)[..., None], fs, bi)) * tone[..., None]
    edge = ss(0.0, 2.0, f2 - f1)
    col = col * (0.88 + 0.12 * edge)[..., None]
    weath = fbm(H, W, 1 / 400, rng, 5)
    col = lerp(col, srgb((0.42, 0.41, 0.38)), np.clip(0.72 + 0.2 * weath, 0, 1))
    height = 0.2 * edge + 0.3 * (mineral == 0) - 0.2 * (mineral == 2) + 0.6 * fbm(H, W, 1 / 150, rng, 5)
    rough = 0.72 - 0.15 * (mineral == 0) + 0.1 * weath
    if lichen:
        lim = np.zeros((H, W))
        lic = np.zeros((H, W, 3))
        grain = fft_noise(H, W, 1 / 2.5, 1 / 2.5, rng)
        for c, cov, sc in (((0.60, 0.63, 0.50), 0.72, 1 / 90), ((0.48, 0.52, 0.38), 0.8, 1 / 60),
                           ((0.74, 0.52, 0.17), 0.9, 1 / 45), ((0.22, 0.22, 0.21), 0.9, 1 / 30)):
            n = fbm(H, W, sc, rng, 5, gain=0.6)
            thr = np.quantile(n, cov + (1 - cov) * (1 - lichen))
            m = ss(thr, thr + 0.12, n)
            rim = ss(thr, thr + 0.05, n) * (1 - ss(thr + 0.05, thr + 0.12, n))
            lc = srgb(c) * (0.85 + 0.12 * grain)[..., None]
            lc = lerp(lc, lc * 0.72, rim)
            lic = lerp(lic, lc, m)
            lim = np.maximum(lim, m)
        col = lerp(col, lic, lim * 0.95)
        height = height + 0.2 * lim + 0.05 * grain * lim
        rough = rough * (1 - lim) + 0.9 * lim
    return col, rough, height, size


# =================================================================== DAUB ===
def _daub(W=2048, H=2048, size=(0.8, 0.8), seed=12, limewash=0.6):
    rng = np.random.default_rng(seed)
    base = fbm(H, W, 1 / 500, rng, 6)
    smear = fft_noise(H, W, 1 / 300, 1 / 60, rng)
    f1, f2, idx = voronoi(H, W, periodic_points(40, H, W, rng))
    crack = 1 - ss(0.0, 3.0, f2 - f1)
    crack = crack * ss(0.6, 1.2, fft_noise(H, W, 1 / 250, 1 / 250, rng)) * 0.7
    marks = np.zeros((H, W))
    yy, xx = np.mgrid[0:H, 0:W]
    for _ in range(70):
        cx, cy = rng.random() * W, rng.random() * H
        R = 60 + 160 * rng.random()
        dx = (xx - cx + W / 2) % W - W / 2
        dy = (yy - cy + H / 2) % H - H / 2
        d = np.sqrt(dx ** 2 + dy ** 2)
        a = rng.random() * np.pi
        streaks = np.cos((dx * np.cos(a) + dy * np.sin(a)) / 9.0)
        marks += np.exp(-(d / R) ** 2) * (0.6 + 0.4 * streaks) * (0.5 + rng.random())
    height = 0.8 * base + 0.35 * marks + 0.1 * smear - 1.2 * crack
    tone = np.clip(0.5 + 0.18 * base + 0.08 * marks, 0, 1)
    col = lerp(srgb((0.42, 0.34, 0.25)), srgb((0.55, 0.46, 0.34)), tone)
    height = height + 0.5 * fbm(H, W, 1 / 25, rng, 4)
    img = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    for _ in range(600):
        x0, y0 = rng.random() * W, rng.random() * H
        a = rng.random() * np.pi
        L = 20 + 70 * rng.random()
        pts = [(x0, y0), (x0 + np.cos(a) * L, y0 + np.sin(a) * L)]
        wrap_draw(lambda p: dr.line(p, fill=255, width=3), W, H, pts)
    st = ndimage.gaussian_filter(np.asarray(img, dtype=float) / 255, 0.6)
    col = lerp(col, srgb((0.52, 0.42, 0.24)), st * 0.7)
    height = height + 0.3 * st
    if limewash:
        lw = ss(0.1, 0.8, fbm(H, W, 1 / 350, rng, 5)) * limewash
        lwc = srgb((0.60, 0.57, 0.50)) * (0.88 + 0.12 * fbm(H, W, 1 / 40, rng, 4))[..., None]
        col = lerp(col, lwc, lw * (1 - crack))
    col = lerp(col, srgb((0.10, 0.08, 0.06)), crack * 0.8)
    rough = 0.9 + 0.05 * base
    return col, rough, height, size


GENERATORS = {
    "oak_weathered": lambda: _wood(True, "oak", seed=1, cut="quarter"),
    "oak_fresh": lambda: _wood(False, "oak", seed=2, cut="quarter"),
    "oak_aged": lambda: _wood(False, "oak", seed=6, cut="quarter", aged=True),
    "walnut": lambda: _wood(False, "walnut", seed=3),
    "ash": lambda: _wood(False, "ash", seed=4),
    "thatch": lambda: _thatch(),
    "earth": lambda: _earth(),
    "granite": lambda: _granite(lichen=0.55),
    "daub": lambda: _daub(limewash=0.0),
}
