"""Shared parametric shape of the Norse bearded axe (skeggøx).

Units are metres. Z is up along the haft, X points from the haft towards the
cutting edge, Y is the blade thickness direction. Both the Blender build script
and the texture generator import this module so geometry and UV-space
decorations (runes, polished edge band) line up exactly.
"""
import numpy as np

# ---------------------------------------------------------------- blade -----
X_IN = 0.018          # where the blade starts, hidden inside the eye wall
UV_SCALE = 0.44       # metres covered by one full UV unit on the blade faces
UV_X0 = 0.02          # offset so the blade lands inside its UV tile
UV_Z0 = 0.16


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def z_top(u):
    """Upper contour: almost straight, the toe rises slightly."""
    u = np.asarray(u, dtype=float)
    return 0.028 + 0.026 * u ** 2.4


def z_bot(u):
    """Lower contour: short neck, then the hooked beard sweeping down."""
    u = np.asarray(u, dtype=float)
    return -0.019 - 0.135 * smoothstep(0.28, 1.0, u) ** 2.3 + 0.003 * np.exp(-((u - 0.15) / 0.08) ** 2)


def x_edge(v):
    """Cutting edge: a shallow crescent, the beard tip pulled back."""
    v = np.asarray(v, dtype=float)
    return 0.158 + 0.016 * np.sin(np.pi * v) ** 0.8 - 0.020 * (1.0 - v) ** 3


def blade_point(u, v):
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    x = X_IN + (x_edge(v) - X_IN) * u
    z = z_bot(u) + (z_top(u) - z_bot(u)) * v
    return x, z


def blade_half_thickness(u, v):
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    t = 0.0012 + 0.0100 * (1.0 - u) ** 1.6
    # slightly thinner towards beard tip and toe corners
    t = t * (0.88 + 0.12 * np.sin(np.pi * np.clip(v, 0, 1)) ** 0.5)
    e = smoothstep(0.90, 1.0, u)
    return t * (1.0 - e) + 0.00030 * e


def blade_uv(x, z, side):
    """Planar UVs. side=+1 -> left tile, side=-1 -> right tile (top half)."""
    U = (x + UV_X0) / UV_SCALE * 1.0
    V = 0.5 + (z + UV_Z0) / UV_SCALE
    U = U * 1.0 if side > 0 else 0.5 + U
    return U, V


def edge_polyline(n=4000):
    v = np.linspace(0.0, 1.0, n)
    return np.stack(blade_point(np.ones_like(v), v), axis=1)


def outline_polygon(n=400):
    """Closed blade outline in (x, z), counter-clockwise."""
    u = np.linspace(0.0, 1.0, n)
    v = np.linspace(0.0, 1.0, n)
    bottom = np.stack(blade_point(u, np.zeros_like(u)), 1)
    edge = np.stack(blade_point(np.ones_like(v), v), 1)
    top = np.stack(blade_point(u[::-1], np.ones_like(u)), 1)
    inner = np.stack(blade_point(np.zeros_like(v), v[::-1]), 1)
    return np.concatenate([bottom, edge, top, inner])


# ------------------------------------------------------------------ eye -----
EYE_IN_A = 0.0200     # inner half-size along X (haft fits here)
EYE_IN_B = 0.0135     # inner half-size along Y
EYE_OUT_FRONT = 0.036
EYE_OUT_BACK = 0.025
EYE_OUT_B = 0.0182


def eye_z_range(theta):
    s = np.abs(np.sin(theta)) ** 4
    return -0.037 - 0.014 * s, 0.034 + 0.005 * s


# ----------------------------------------------------------------- haft -----
HAFT_Z0 = -0.660
HAFT_Z1 = 0.041
_HZ = [-0.660, -0.652, -0.640, -0.600, -0.45, -0.25, -0.10, -0.058, -0.040, 0.041]
_HA = [0.0170, 0.0232, 0.0240, 0.0210, 0.0197, 0.0184, 0.0194, 0.0206, 0.0199, 0.0199]


def haft_a(z):
    return np.interp(z, _HZ, _HA)


def haft_b(z):
    return haft_a(z) * 0.68


def haft_xc(z):
    """Slight forward sweep towards the butt."""
    d = np.clip(-np.asarray(z, dtype=float) - 0.06, 0.0, None) / 0.60
    return 0.009 * d ** 2


# ---------------------------------------------------------------- grip ------
GRIP_Z0 = -0.615
GRIP_Z1 = -0.440
GRIP_PITCH = 0.022    # helix pitch of the leather strap
