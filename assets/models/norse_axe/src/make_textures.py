"""Procedural PBR textures for the Norse axe (numpy only, deterministic).

Outputs (in ../textures):
  iron_basecolor.jpg  iron_orm.jpg  iron_normal.jpg     2048x2048
  wood_basecolor.jpg  wood_orm.jpg  wood_normal.jpg     512x4096
  leather_basecolor.jpg leather_orm.jpg leather_normal.jpg 1024x1024
ORM = R occlusion, G roughness, B metallic (glTF convention).
Normal maps are OpenGL / glTF style (+Y up).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
import axe_shape as S  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "textures")
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(7)


# ------------------------------------------------------------ helpers -------
def fft_noise(h, w, sig_u, sig_v, rng=RNG):
    """Periodic gaussian-filtered noise, zero mean, unit std.
    sig_u / sig_v are spectral widths in cycles per pixel (small = smooth)."""
    white = rng.standard_normal((h, w))
    fu = np.fft.fftfreq(w)[None, :]
    fv = np.fft.fftfreq(h)[:, None]
    filt = np.exp(-0.5 * ((fu / sig_u) ** 2 + (fv / sig_v) ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * filt))
    n -= n.mean()
    return n / (n.std() + 1e-9)


def fbm(h, w, base, octaves=5, aniso=1.0, gain=0.5, rng=RNG):
    total = np.zeros((h, w))
    amp, s, norm = 1.0, base, 0.0
    for _ in range(octaves):
        total += amp * fft_noise(h, w, s, s * aniso, rng)
        norm += amp
        amp *= gain
        s *= 2.0
    return total / norm


def smooth(a, b, x):
    return S.smoothstep(a, b, x)


def lin2srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def normal_map(h_mm, px_u_mm, px_v_mm, strength=1.0):
    hp = np.pad(h_mm, 1, mode="wrap")
    dhdu = (hp[1:-1, 2:] - hp[1:-1, :-2]) / (2 * px_u_mm)
    dhdv_up = -(hp[2:, 1:-1] - hp[:-2, 1:-1]) / (2 * px_v_mm)
    n = np.stack([-dhdu * strength, -dhdv_up * strength, np.ones_like(h_mm)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, arr, srgb=False):
    a = lin2srgb(arr) if srgb else np.clip(arr, 0, 1)
    img = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
    img.save(os.path.join(OUT, name), quality=93, subsampling=0)
    print("wrote", name, img.size)


def mix(a, b, t):
    """Blend colour arrays (…,3) by a scalar field t (H,W)."""
    t = np.asarray(t)[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def voronoi_f1(h, w, n_pts, rng=RNG, wrap_u=False):
    pts = rng.random((n_pts, 2)) * [h, w]
    if wrap_u:
        pts = np.concatenate([pts, pts + [0, w], pts - [0, w]])
    tree = cKDTree(pts)
    rr, cc = np.mgrid[0:h, 0:w]
    q = np.stack([rr.ravel() + 0.5, cc.ravel() + 0.5], 1)
    d, idx = tree.query(q, k=2, workers=-1)
    return d[:, 0].reshape(h, w), d[:, 1].reshape(h, w), (idx[:, 0] % n_pts).reshape(h, w)


def draw_lines(h, w, lines, width, ss=2):
    img = Image.new("L", (w * ss, h * ss), 0)
    dr = ImageDraw.Draw(img)
    for (p0, p1) in lines:
        dr.line([(p0[0] * ss, p0[1] * ss), (p1[0] * ss, p1[1] * ss)], fill=255, width=max(1, int(width * ss)))
        r = width * ss / 2
        for p in (p0, p1):
            dr.ellipse([p[0] * ss - r, p[1] * ss - r, p[0] * ss + r, p[1] * ss + r], fill=255)
    img = img.resize((w, h), Image.LANCZOS)
    return np.asarray(img, dtype=float) / 255.0


# ================================================================ IRON ======
def make_iron(N=2048):
    px_mm = S.UV_SCALE * 1000.0 / N          # mm per pixel
    rows, cols = np.mgrid[0:N, 0:N]
    U = (cols + 0.5) / N
    V = 1.0 - (rows + 0.5) / N

    # physical coords for the two blade tiles (top half of the atlas)
    top = V >= 0.5
    side_pos = top & (U < 0.5)
    x = np.where(U < 0.5, U, U - 0.5) * S.UV_SCALE - S.UV_X0
    z = (V - 0.5) * S.UV_SCALE - S.UV_Z0

    def to_px(xz, side):
        uu = (xz[:, 0] + S.UV_X0) / S.UV_SCALE + (0.0 if side > 0 else 0.5)
        vv = 0.5 + (xz[:, 1] + S.UV_Z0) / S.UV_SCALE
        return np.stack([uu * N, (1 - vv) * N], 1)

    outline = S.outline_polygon()
    blade_mask_img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(blade_mask_img)
    for side in (1, -1):
        d.polygon([tuple(p) for p in to_px(outline, side)], fill=255)
    blade = np.asarray(blade_mask_img, dtype=float) / 255.0

    # distance to cutting edge (mm) inside the blade tiles
    tree = cKDTree(S.edge_polyline())
    d_edge = np.full((N, N), 1e3)
    sel = top
    dd, _ = tree.query(np.stack([x[sel], z[sel]], 1), workers=-1)
    d_edge[sel] = dd * 1000.0

    # ---- height field (mm)
    f1, f2, cid = voronoi_f1(N, N, 2600)
    R = 22.0
    cell_depth = 0.6 + 0.8 * RNG.random(2600)
    hammer = -0.09 * cell_depth[cid] * (1.0 - np.clip(f1 / R, 0, 1.0) ** 2)
    hammer = ndimage.gaussian_filter(hammer, 1.2)
    wav = 0.10 * fbm(N, N, 1 / 400, 3)

    rust_field = fbm(N, N, 1 / 180, 5)
    rust_mask = smooth(0.9, 1.6, rust_field)
    pits_n = fft_noise(N, N, 1 / 2.5, 1 / 2.5)
    pits = smooth(2.3 - 0.9 * rust_mask, 3.0 - 0.9 * rust_mask, pits_n)
    pits = ndimage.gaussian_filter(pits, 0.7)

    # scratches
    band_w = 7.0 + 1.5 * fbm(N, N, 1 / 60, 3)
    band = 1.0 - smooth(band_w - 1.2, band_w + 1.2, d_edge)
    lines_gen, lines_edge = [], []
    for _ in range(900):
        p = RNG.random(2) * N
        ang = RNG.random() * np.pi
        L = (4 + RNG.random() * 30) / px_mm
        lines_gen.append((p, p + L * np.array([np.cos(ang), np.sin(ang)])))
    for _ in range(2600):
        p = RNG.random(2) * [N, N / 2]
        ang = np.deg2rad(RNG.normal(0, 18))
        L = (3 + RNG.random() * 12) / px_mm
        lines_edge.append((p, p + L * np.array([np.cos(ang), np.sin(ang)])))
    scr_gen = draw_lines(N, N, lines_gen, 0.8) * RNG.random()  # varied strength
    scr_edge = draw_lines(N, N, lines_edge, 0.7)

    # silver inlay: runes ODIN (Elder Futhark) + border grooves on the + face
    inlay = make_inlay(N, to_px, px_mm)

    height = (hammer + wav) * (1 - band * blade) - 0.06 * pits - 0.012 * scr_gen \
        - 0.010 * scr_edge * band * blade - 0.035 * inlay

    # ---- material layers
    # dark forge scale / patina covers most of the head; raised spots are rubbed bright
    patina_n = fbm(N, N, 1 / 160, 6, gain=0.5)
    hp_hammer = hammer - ndimage.gaussian_filter(hammer, 8)
    wear = ndimage.gaussian_filter(smooth(0.01, 0.04, hp_hammer), 2) * 0.2
    scale = np.clip(smooth(-1.9, -0.4, patina_n) - wear, 0, 1)
    rust = np.clip(rust_mask * 0.45 + pits * 0.9, 0, 1) * (1 - band * blade)

    iron_clean = np.array([0.34, 0.34, 0.35])
    rust_col = np.array([0.17, 0.065, 0.026])
    edge_col = np.array([0.63, 0.63, 0.64])
    silver = np.array([0.80, 0.78, 0.74])
    silver_tarn = np.array([0.34, 0.31, 0.27])

    speck = fft_noise(N, N, 1 / 3, 1 / 3)
    tint = (1.0 + 0.08 * fbm(N, N, 1 / 90, 4) + 0.05 * speck)[..., None]
    brown = smooth(-0.8, 1.6, fbm(N, N, 1 / 200, 4)) * 0.7
    iron_scale = mix(np.array([0.062, 0.060, 0.058]), np.array([0.095, 0.070, 0.050]), brown)
    col = iron_clean * tint
    col = mix(col, iron_scale * tint, scale)
    col = mix(col, edge_col * (1 - 0.06 * scr_edge[..., None]), band * blade)
    # scratches cut through the patina and show bright metal
    col = mix(col, iron_clean * 1.1, scr_gen * scale * (1 - band * blade) * 0.35)
    tarn = smooth(-0.2, 1.2, fbm(N, N, 1 / 40, 3))
    col = mix(col, mix(silver, silver_tarn, tarn * 0.6), inlay)
    col = mix(col, rust_col * (0.8 + 0.4 * fbm(N, N, 1 / 8, 2)[..., None]), rust)
    # dirt in pits, scratches and inlay grooves (not in the broad hammer dents)
    fine_h = -0.06 * pits - 0.012 * scr_gen - 0.035 * inlay
    cavity = np.clip(ndimage.gaussian_filter(fine_h, 3) - fine_h, 0, None) * 10
    col = col * (1 - np.clip(cavity, 0, 0.6))[..., None]

    rough = 0.40 + 0.08 * fbm(N, N, 1 / 30, 3)
    rough = rough * (1 - scale) + (0.55 + 0.08 * brown) * scale
    rough = rough * (1 - band * blade) + (0.20 + 0.10 * scr_edge) * band * blade
    rough = rough * (1 - inlay) + 0.28 * inlay
    rough = rough * (1 - rust) + 0.9 * rust
    metal = 1.0 - 0.45 * scale
    metal = metal * (1 - rust) + 0.0 * rust
    metal = np.maximum(metal, inlay)
    occl = np.clip(1 - 0.6 * cavity, 0.4, 1)

    # --- strip regions in the lower half (see build_axe.py for the layout)
    strip_edge = (V > 0.458) & (V < 0.472)
    col[strip_edge] = edge_col
    rough[strip_edge] = 0.22
    metal[strip_edge] = 1.0
    spine = (V > 0.398) & (V < 0.437)
    u_sp = (U - 0.05) / 0.9
    pol = spine & (u_sp > 0.93)
    col[pol] = edge_col
    rough[pol] = 0.24
    metal[pol] = 1.0

    save("iron_basecolor.jpg", col, srgb=True)
    save("iron_orm.jpg", np.stack([occl, np.clip(rough, 0.05, 1), np.clip(metal, 0, 1)], -1))
    save("iron_normal.jpg", normal_map(height, px_mm, px_mm, 1.0))


def rune_strokes():
    """Elder Futhark ODIN (othala, dagaz, isa, naudiz) in unit cells (w,h=1)."""
    return [
        (0.60, [((0.30, 1.0), (0.0, 0.66)), ((0.30, 1.0), (0.60, 0.66)),
                ((0.0, 0.66), (0.60, 0.0)), ((0.60, 0.66), (0.0, 0.0))]),
        (0.80, [((0.0, 0.0), (0.0, 1.0)), ((0.80, 0.0), (0.80, 1.0)),
                ((0.0, 1.0), (0.80, 0.0)), ((0.0, 0.0), (0.80, 1.0))]),
        (0.20, [((0.10, 0.0), (0.10, 1.0))]),
        (0.60, [((0.30, 0.0), (0.30, 1.0)), ((0.0, 0.68), (0.60, 0.40))]),
    ]


def make_inlay(N, to_px, px_mm):
    lines = []
    # runes, 13 mm tall, sitting on the neck/cheek
    h = 0.013
    x0, zc = 0.036, 0.004
    xcur = x0
    for w, strokes in rune_strokes():
        for (a, b) in strokes:
            pa = np.array([[xcur + a[0] * h, zc - h / 2 + a[1] * h]])
            pb = np.array([[xcur + b[0] * h, zc - h / 2 + b[1] * h]])
            lines.append((to_px(pa, 1)[0], to_px(pb, 1)[0]))
        xcur += w * h + 0.0065
    # word separators (two dots) before and after
    dots = [(x0 - 0.006, zc + 0.003), (x0 - 0.006, zc - 0.003),
            (xcur - 0.001, zc + 0.003), (xcur - 0.001, zc - 0.003)]
    for (dx, dz) in dots:
        p = to_px(np.array([[dx, dz]]), 1)[0]
        lines.append((p, p + 0.01))
    # border grooves following the top and lower contour, stopping before the edge
    for off in (0.0045, 0.0065):
        u = np.linspace(0.08, 0.86, 160)
        xt, zt = S.blade_point(u, np.ones_like(u))
        xb, zb = S.blade_point(u, np.zeros_like(u))
        for (xs, zs, sgn) in ((xt, zt - off, 1), (xb, zb, -1)):
            if sgn < 0:
                # offset the lower curve along its inward normal
                dx, dz = np.gradient(xs), np.gradient(zs)
                n = np.stack([-dz, dx], 1)
                n /= np.linalg.norm(n, axis=1, keepdims=True)
                pts = np.stack([xs, zs], 1) + n * off
            else:
                pts = np.stack([xs, zs], 1)
            pp = to_px(pts, 1)
            lines += [(pp[i], pp[i + 1]) for i in range(len(pp) - 1)]
    # vertical groove closing the panel at the neck
    for xo in (0.027, 0.029):
        pa = to_px(np.array([[xo, S.z_bot(0.07) + 0.004]]), 1)[0]
        pb = to_px(np.array([[xo, S.z_top(0.07) - 0.004]]), 1)[0]
        lines.append((pa, pb))
    return draw_lines(N, N, lines, 0.65 / px_mm, ss=3)


# ================================================================ WOOD ======
def make_wood(W=512, H=4096):
    C = 0.105
    L = S.HAFT_Z1 - S.HAFT_Z0
    px_u, px_v = C * 1000 / W, L * 1000 / (H * 0.97)
    rows, cols = np.mgrid[0:H, 0:W]
    U = (cols + 0.5) / W
    V = 1.0 - (rows + 0.5) / H
    zz = S.HAFT_Z0 + (V - 0.03) / 0.97 * L

    warp = fft_noise(H, W, 1 / 90, 1 / 900) * 1.6 + fft_noise(H, W, 1 / 25, 1 / 300) * 0.25
    rings = np.mod(24 * U + warp, 1.0)
    late = smooth(0.62, 0.86, rings) * (1 - smooth(0.93, 1.0, rings))
    streak = fft_noise(H, W, 1 / 1.6, 1 / 30)
    pores = smooth(1.6, 2.4, streak) * (1 - smooth(0.25, 0.45, rings))
    fine = fft_noise(H, W, 1 / 3, 1 / 80)

    early_c = np.array([0.66, 0.52, 0.35])
    late_c = np.array([0.43, 0.29, 0.17])
    col = mix(early_c, late_c, late * 0.85)
    col = col * (1 + 0.05 * fine[..., None])
    col = col * (1 + 0.10 * fbm(H, W, 1 / 300, 3, aniso=0.2)[..., None])
    col = mix(col, np.array([0.30, 0.20, 0.11]), pores * 0.8)
    # aged linseed oil: warmer and darker
    col = col ** 1.25 * np.array([1.0, 0.93, 0.82])
    # handling grime above the grip and near the head
    grime = smooth(0.12, 0.0, np.abs(zz + 0.36)) * 0.6 + smooth(-0.10, -0.02, zz) * 0.35
    grime = grime * (0.7 + 0.3 * fbm(H, W, 1 / 40, 3))
    col = col * (1 - 0.45 * grime[..., None])
    # dings and scratches that show lighter bare wood
    dl = []
    for _ in range(140):
        p = RNG.random(2) * [W, H]
        ang = RNG.normal(np.pi / 2, 0.8)
        Ls = (2 + RNG.random() * 14) / px_u
        dl.append((p, p + Ls * np.array([np.cos(ang), np.sin(ang)])))
    dings = draw_lines(H, W, dl, 1.2)
    col = col * (1 + 0.35 * dings[..., None])

    # end grain caps in V < 0.025 (two discs side by side)
    cap = V < 0.027
    for cu in (0.25, 0.75):
        du = (U - cu) / 0.22
        dv = (V - 0.0135) / 0.0125
        r = np.sqrt(du ** 2 + dv ** 2)
        eg = np.mod(r * 11 + 0.3 * fft_noise(H, W, 1 / 20, 1 / 20), 1.0)
        m = cap & (np.abs(U - cu) < 0.25)
        eg_col = mix(np.array([0.36, 0.25, 0.15]), np.array([0.20, 0.13, 0.07]),
                     smooth(0.7, 0.9, eg) * (1 - smooth(0.95, 1.0, eg)))
        col[m] = eg_col[m]

    rough = 0.58 - 0.08 * late - 0.18 * grime + 0.15 * pores + 0.05 * fine
    height = -0.03 * late - 0.06 * pores + 0.01 * fine - 0.05 * dings
    save("wood_basecolor.jpg", col, srgb=True)
    save("wood_orm.jpg", np.stack([np.ones_like(rough), np.clip(rough, 0.05, 1), np.zeros_like(rough)], -1))
    save("wood_normal.jpg", normal_map(height, px_u, px_v, 1.0))


# ============================================================= LEATHER ======
def make_leather(N=1024):
    C = 0.110
    L = S.GRIP_Z1 - S.GRIP_Z0
    px_u, px_v = C * 1000 / N, L * 1000 / N
    rows, cols = np.mgrid[0:N, 0:N]
    U = (cols + 0.5) / N
    V = 1.0 - (rows + 0.5) / N
    phase = np.mod(U + V * L / S.GRIP_PITCH, 1.0)

    f1, f2, _ = voronoi_f1(N, N, 26000, wrap_u=True)
    pebble = np.clip((f2 - f1) / 3.0, 0, 1)
    pebble = ndimage.gaussian_filter(pebble, 0.6)
    crease = fft_noise(N, N, 1 / 2.0, 1 / 12)

    base = np.array([0.155, 0.075, 0.035])
    col = base * (1 + 0.18 * fbm(N, N, 1 / 60, 4)[..., None])
    polish = smooth(0.70, 0.97, phase) * (1 - smooth(0.975, 1.0, phase))
    polish = polish * (0.6 + 0.4 * fbm(N, N, 1 / 25, 3))
    gap = 1 - smooth(0.0, 0.10, phase)
    col = mix(col, np.array([0.30, 0.18, 0.10]), np.clip(polish * pebble * 1.4, 0, 1) * 0.6)
    col = col * (1 - 0.55 * gap)[..., None] * (0.85 + 0.15 * pebble)[..., None]
    # sweat / dirt darkening towards the middle of the grip
    col = col * (1 - 0.25 * smooth(0.5, 0.0, np.abs(V - 0.5)))[..., None]

    rough = 0.72 - 0.25 * polish - 0.08 * pebble + 0.1 * gap
    height = 0.03 * pebble - 0.015 * smooth(1.2, 2.2, crease)
    occl = 1 - 0.45 * gap
    save("leather_basecolor.jpg", col, srgb=True)
    save("leather_orm.jpg", np.stack([occl, np.clip(rough, 0.05, 1), np.zeros_like(rough)], -1))
    save("leather_normal.jpg", normal_map(height, px_u, px_v, 1.0))


if __name__ == "__main__":
    make_iron()
    make_wood()
    make_leather()
