"""Procedural PBR materials (Cycles node trees) that the pipeline bakes to
textures. All presets feed a single Principled BSDF so the baker can read
Base Color / Roughness / Metallic / Normal straight from its inputs.

Coordinates default to Object space, so noise is continuous across UV seams.
Decals and painted patterns use the "design" UV layer via image masks.
"""
import os

import bpy

OBJ, UV, GEN = "Object", "UV", "Generated"


def rgba(c):
    if isinstance(c, (int, float)):
        return (c, c, c, 1.0)
    return tuple(c) + (1.0,) * (4 - len(c))


def hexc(h, lin=True):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    if lin:
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return tuple(c)


class NB:
    """Tiny node-tree builder. Methods return output sockets."""

    def __init__(self, name):
        self.m = bpy.data.materials.new(name)
        self.nt = self.m.node_tree
        self.nt.nodes.clear()
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.bsdf = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.nt.links.new(self.bsdf.outputs[0], self.out.inputs["Surface"])
        self._coord = None
        self._cache = {}

    # ---- plumbing
    def node(self, kind, **kw):
        n = self.nt.nodes.new(kind)
        for k, v in kw.items():
            if k in n.inputs.keys():
                self.set(n.inputs[k], v)
            else:
                setattr(n, k, v)
        return n

    def set(self, sock, v):
        if v is None:
            return
        if hasattr(v, "is_output") or hasattr(v, "links"):
            self.nt.links.new(v, sock)
        elif sock.type in ("RGBA",):
            sock.default_value = rgba(v)
        elif sock.type == "VECTOR" and isinstance(v, (int, float)):
            sock.default_value = (v, v, v)
        else:
            sock.default_value = v

    # ---- coordinates
    def co(self, kind=OBJ, uv="design"):
        if kind == UV:
            return self.node("ShaderNodeUVMap", uv_map=uv).outputs["UV"]
        if self._coord is None:
            self._coord = self.nt.nodes.new("ShaderNodeTexCoord")
        return self._coord.outputs[kind]

    def mapv(self, vec=None, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0)):
        n = self.node("ShaderNodeMapping")
        self.set(n.inputs["Vector"], vec if vec is not None else self.co())
        n.inputs["Scale"].default_value = scale if hasattr(scale, "__len__") else (scale,) * 3
        n.inputs["Location"].default_value = loc
        n.inputs["Rotation"].default_value = rot
        return n.outputs["Vector"]

    # ---- textures
    def noise(self, scale=5.0, detail=6.0, rough=0.55, vec=None, distort=0.0, kind="FBM", out="Fac",
              lac=2.0, dim="3D", w=0.0):
        n = self.node("ShaderNodeTexNoise", noise_dimensions=dim, noise_type=kind)
        self.set(n.inputs["Vector"], vec if vec is not None else self.co())
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Lacunarity"].default_value = lac
        n.inputs["Distortion"].default_value = distort
        if dim == "4D":
            n.inputs["W"].default_value = w
        return n.outputs[out]

    def voronoi(self, scale=5.0, vec=None, feature="F1", out="Distance", rand=1.0, metric="EUCLIDEAN",
                detail=0.0):
        n = self.node("ShaderNodeTexVoronoi", feature=feature, distance=metric)
        self.set(n.inputs["Vector"], vec if vec is not None else self.co())
        n.inputs["Scale"].default_value = scale
        n.inputs["Randomness"].default_value = rand
        if "Detail" in n.inputs:
            n.inputs["Detail"].default_value = detail
        return n.outputs[out]

    def wave(self, scale=5.0, vec=None, kind="BANDS", axis="Z", distort=4.0, detail=3.0, profile="SIN",
             dscale=1.0):
        n = self.node("ShaderNodeTexWave", wave_type=kind, wave_profile=profile)
        if kind == "BANDS":
            n.bands_direction = axis
        else:
            n.rings_direction = axis
        self.set(n.inputs["Vector"], vec if vec is not None else self.co())
        n.inputs["Scale"].default_value = scale
        n.inputs["Distortion"].default_value = distort
        n.inputs["Detail"].default_value = detail
        n.inputs["Detail Scale"].default_value = dscale
        return n.outputs["Fac"]

    def img(self, path, vec=None, cs="Non-Color", out="Color", interp="Cubic", ext="REPEAT"):
        n = self.node("ShaderNodeTexImage", interpolation=interp, extension=ext)
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = cs
        self.set(n.inputs["Vector"], vec if vec is not None else self.co(UV))
        return n.outputs[out]

    # ---- math / colour
    def math(self, op, a, b=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.set(n.inputs[0], a)
        if b is not None:
            self.set(n.inputs[1], b)
        return n.outputs[0]

    def add(self, a, b):
        return self.math("ADD", a, b)

    def mul(self, a, b, clamp=False):
        return self.math("MULTIPLY", a, b, clamp)

    def sub(self, a, b):
        return self.math("SUBTRACT", a, b)

    def mr(self, v, a=0.0, b=1.0, c=0.0, d=1.0, clamp=True, interp="LINEAR"):
        n = self.node("ShaderNodeMapRange", interpolation_type=interp, clamp=clamp)
        self.set(n.inputs["Value"], v)
        for k, val in zip(("From Min", "From Max", "To Min", "To Max"), (a, b, c, d)):
            n.inputs[k].default_value = val
        return n.outputs["Result"]

    def ss(self, v, a, b):
        """Smoothstep-style mask."""
        return self.mr(v, a, b, 0, 1, interp="SMOOTHSTEP")

    def ramp(self, fac, stops, interp="LINEAR"):
        n = self.node("ShaderNodeValToRGB")
        cr = n.color_ramp
        cr.interpolation = interp
        self.set(n.inputs["Fac"], fac)
        els = cr.elements
        while len(els) < len(stops):
            els.new(0.5)
        for e, (pos, col) in zip(els, sorted(stops, key=lambda s: s[0])):
            e.position = pos
            e.color = rgba(col)
        return n.outputs["Color"]

    def mix(self, a, b, fac, blend="MIX", clamp=True):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend, clamp_result=clamp)
        self.set(n.inputs[0], fac)
        self.set(n.inputs[6], a)
        self.set(n.inputs[7], b)
        return n.outputs[2]

    def mixf(self, a, b, fac):
        n = self.node("ShaderNodeMix", data_type="FLOAT")
        self.set(n.inputs[0], fac)
        self.set(n.inputs[2], a)
        self.set(n.inputs[3], b)
        return n.outputs[0]

    def hsv(self, col, h=0.5, s=1.0, v=1.0):
        n = self.node("ShaderNodeHueSaturation")
        self.set(n.inputs["Color"], col)
        self.set(n.inputs["Hue"], h)
        self.set(n.inputs["Saturation"], s)
        self.set(n.inputs["Value"], v)
        return n.outputs["Color"]

    def gray(self, col):
        n = self.node("ShaderNodeRGBToBW")
        self.set(n.inputs[0], col)
        return n.outputs[0]

    def sep(self, vec):
        n = self.node("ShaderNodeSeparateXYZ")
        self.set(n.inputs[0], vec)
        return n.outputs

    # ---- geometry-aware masks (Cycles only, baked into textures)
    def edges(self, radius=0.003, lo=0.02, hi=0.25):
        """Convex-edge mask from the Bevel-node normal trick."""
        key = ("edge", round(radius, 5))
        if key not in self._cache:
            bev = self.node("ShaderNodeBevel", samples=4)
            bev.inputs["Radius"].default_value = radius
            geo = self.node("ShaderNodeNewGeometry")
            dot = self.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
            self.nt.links.new(bev.outputs[0], dot.inputs[0])
            self.nt.links.new(geo.outputs["Normal"], dot.inputs[1])
            self._cache[key] = self.sub(1.0, dot.outputs["Value"])
        return self.mr(self._cache[key], lo, hi, 0, 1)

    def cavity(self, dist=0.02, lo=0.3, hi=1.0):
        """1 in crevices, 0 on open surfaces (ambient-occlusion based)."""
        key = ("ao", round(dist, 5))
        if key not in self._cache:
            n = self.node("ShaderNodeAmbientOcclusion", samples=4, only_local=True)
            n.inputs["Distance"].default_value = dist
            self._cache[key] = n.outputs["AO"]
        return self.mr(self._cache[key], lo, hi, 1, 0)

    def chips(self, amount=0.5, scale=8.0, edge=1.2):
        """Chipped-paint mask (1 = paint gone): noisy patches concentrated on edges."""
        n = self.add(self.mul(self.noise(scale, 12, 0.72), 0.9), self.mul(self.edges(0.004), edge))
        lo = 0.78 - 0.22 * amount
        return self.ss(n, lo, lo + 0.04)

    def scratches(self, scale=30.0, amount=0.5):
        sc = 0.0
        for rot, st in (((0, 0, 0.4), (1, 1, 30)), ((0.7, 0, -0.8), (30, 1, 1)), ((0.2, 0.5, 1.3), (1, 25, 1))):
            v = self.voronoi(scale, self.mapv(scale=st, rot=rot), feature="DISTANCE_TO_EDGE")
            sc = self.add(sc, self.mr(v, 0.0, 0.01, 1, 0))
        return self.mul(self.mul(sc, self.ss(self.noise(5, 2, 0.5), 0.4, 0.62)), amount, clamp=True)

    def bump(self, height, strength=0.3, dist=0.002, normal=None):
        n = self.node("ShaderNodeBump")
        self.set(n.inputs["Height"], height)
        n.inputs["Strength"].default_value = strength
        n.inputs["Distance"].default_value = dist
        if normal is not None:
            self.set(n.inputs["Normal"], normal)
        return n.outputs["Normal"]

    # ---- output
    def done(self, color, rough, metal=0.0, normal=None, **extra):
        b = self.bsdf
        self.set(b.inputs["Base Color"], color)
        self.set(b.inputs["Roughness"], rough)
        self.set(b.inputs["Metallic"], metal)
        if normal is not None:
            self.set(b.inputs["Normal"], normal)
        for k, v in extra.items():
            self.set(b.inputs[k], v)
        return self.m


# =============================================================== layers ====
def apply_layers(nb, col, rough, metal, height, layers):
    """Paint/inlay/engrave layers driven by design-UV image masks.

    layer = dict(mask=path | socket, color=, rough=, metal=, height=, channel="R",
                 invert=False, uv="design", opacity=1)
    """
    for L in layers or []:
        m = L["mask"]
        if callable(m):
            m = m(nb)
        elif isinstance(m, str):
            m = nb.gray(nb.img(m, nb.co(UV, L.get("uv", "design")), out="Color", ext=L.get("ext", "CLIP")))
        if L.get("invert"):
            m = nb.sub(1.0, m)
        if L.get("opacity", 1) != 1:
            m = nb.mul(m, L["opacity"])
        if L.get("chip"):
            m = nb.mul(m, nb.sub(1.0, nb.chips(L["chip"], L.get("chip_scale", 8.0))))
            m = nb.mul(m, nb.sub(1.0, nb.scratches(35, L["chip"])))
        if "color" in L:
            c = L["color"]
            if L.get("vary", 0):
                v = nb.noise(L.get("vary_scale", 40), 4, 0.6)
                c = nb.mix(c, nb.hsv(c, 0.5, 1.0, 1.0 - L["vary"]), v)
            col = nb.mix(col, c, m)
        if "rough" in L:
            rough = nb.mixf(rough, L["rough"], m)
        if "metal" in L:
            metal = nb.mixf(metal, L["metal"], m)
        if "height" in L:
            height = nb.add(height, nb.mul(m, L["height"]))
    return col, rough, metal, height


def _finish(nb, col, rough, metal, height, bump_strength, bump_dist, layers, **extra):
    col, rough, metal, height = apply_layers(nb, col, rough, metal, height, layers)
    normal = nb.bump(height, bump_strength, bump_dist)
    return nb.done(col, rough, metal, normal, **extra)


# ============================================================== presets ====
METALS = {
    "iron": (0.33, 0.32, 0.31), "steel": (0.56, 0.57, 0.58), "gold": (1.0, 0.72, 0.30),
    "silver": (0.95, 0.93, 0.88), "bronze": (0.78, 0.50, 0.26), "brass": (0.89, 0.70, 0.38),
    "copper": (0.95, 0.60, 0.45), "chrome": (0.55, 0.56, 0.57), "pewter": (0.52, 0.52, 0.50),
    "gunmetal": (0.16, 0.16, 0.17),
}


def metal(name, kind="iron", color=None, rough=0.32, rough_var=0.06, wear=0.6, dirt=0.5,
          dirt_color=(0.03, 0.025, 0.02), patina=None, patina_amt=0.0, patina_scale=6.0,
          scratches=0.4, hammer=0.0, pitting=0.0, rust=0.0, scale=1.0, layers=None,
          bump_strength=0.25, edge_radius=0.003):
    nb = NB(name)
    base = color or METALS[kind]
    s = scale
    var = nb.noise(18 * s, 8, 0.6)
    col = nb.mix(base, nb.hsv(base, 0.5, 1.05, 0.82), var)
    r = nb.mr(nb.noise(40 * s, 6, 0.55), 0.3, 0.7, rough - rough_var, rough + rough_var)
    height = nb.mul(nb.noise(120 * s, 4, 0.5), 0.05)
    # scratches: thin stretched voronoi edges in two directions
    if scratches:
        sc = 0.0
        for rot, st in (((0, 0, 0.4), (1, 1, 30)), ((0.7, 0, -0.8), (30, 1, 1))):
            v = nb.voronoi(35 * s, nb.mapv(scale=st, rot=rot), feature="DISTANCE_TO_EDGE")
            sc = nb.add(sc, nb.mr(v, 0.0, 0.012, 1, 0))
        sc = nb.mul(nb.mul(sc, nb.ss(nb.noise(6 * s, 2, 0.5), 0.45, 0.65)), scratches, clamp=True)
        col = nb.mix(col, nb.hsv(base, 0.5, 0.9, 1.25), nb.mul(sc, 0.5))
        r = nb.mixf(r, rough * 0.6, sc)
        height = nb.sub(height, nb.mul(sc, 0.2))
    if hammer:
        hv = nb.voronoi(22 * s * hammer, feature="F1")
        height = nb.add(height, nb.mul(nb.math("POWER", hv, 2.0), 1.2))
    if pitting:
        p = nb.ss(nb.noise(260 * s, 3, 0.6), 0.66 - 0.05 * pitting, 0.72)
        height = nb.sub(height, nb.mul(p, 0.6 * pitting))
        col = nb.mix(col, nb.hsv(base, 0.5, 0.8, 0.4), nb.mul(p, 0.7))
    if patina is not None and patina_amt:
        pm = nb.ss(nb.noise(patina_scale * s, 8, 0.65), 0.62 - 0.25 * patina_amt, 0.70 - 0.2 * patina_amt)
        pm = nb.math("MAXIMUM", pm, nb.mul(nb.cavity(0.02 * s ** -1), patina_amt))
        pc = nb.mix(patina, nb.hsv(patina, 0.5, 1.0, 0.7), nb.noise(60 * s, 4))
        col = nb.mix(col, pc, pm)
        r = nb.mixf(r, 0.75, pm)
        metal_v = nb.mixf(1.0, 0.0, pm)
        height = nb.add(height, nb.mul(pm, 0.15))
    else:
        metal_v = 1.0
    if rust:
        rm = nb.ss(nb.noise(9 * s, 10, 0.7), 0.66 - 0.2 * rust, 0.74 - 0.2 * rust)
        rm = nb.math("MAXIMUM", rm, nb.mul(nb.cavity(0.015), rust * 0.8))
        rc = nb.ramp(nb.noise(80 * s, 6, 0.7), [(0.3, (0.16, 0.05, 0.015)), (0.7, (0.33, 0.12, 0.03))])
        col = nb.mix(col, rc, rm)
        r = nb.mixf(r, 0.9, rm)
        metal_v = nb.mixf(metal_v, 0.0, rm)
        height = nb.add(height, nb.mul(nb.mul(rm, nb.noise(200 * s, 4)), 0.4))
    if dirt:
        d = nb.mul(nb.cavity(0.03), dirt, clamp=True)
        col = nb.mix(col, dirt_color, d)
        r = nb.mixf(r, 0.8, d)
    if wear:
        e = nb.mul(nb.edges(edge_radius), wear, clamp=True)
        col = nb.mix(col, nb.hsv(base, 0.5, 0.9, 1.3), e)
        r = nb.mixf(r, rough * 0.5, e)
        metal_v = nb.mixf(metal_v, 1.0, e)
    return _finish(nb, col, r, metal_v, height, bump_strength, 0.002, layers)


def wood(name, light=(0.30, 0.19, 0.095), dark=(0.11, 0.065, 0.03), rough=0.55, axis="Z", ring_scale=55.0,
         grain_stretch=12.0, varnish=0.0, dirt=0.4, wear=0.3, scale=1.0, layers=None, paint=None,
         paint_wear=0.5, pores=0.5, bump_strength=0.2):
    nb = NB(name)
    st = {"X": (1 / grain_stretch, 1, 1), "Y": (1, 1 / grain_stretch, 1), "Z": (1, 1, 1 / grain_stretch)}[axis]
    v = nb.mapv(scale=tuple(x * scale for x in st))
    rings = nb.wave(ring_scale, v, kind="RINGS", axis=axis, distort=8, detail=5, dscale=0.08, profile="SAW")
    fine = nb.noise(90, 8, 0.6, nb.mapv(scale=tuple(x * scale * 4 for x in st)))
    g = nb.add(nb.mul(rings, 0.75), nb.mul(fine, 0.35))
    col = nb.ramp(g, [(0.2, light), (0.5, nb_lerp(light, dark, 0.3)), (0.8, dark)])
    col = nb.mix(col, nb.hsv(col, 0.5, 0.9, 0.7), nb.ss(nb.noise(8 * scale, 4, 0.6), 0.5, 0.75))
    col = nb.mix(col, nb.hsv(col, 0.5, 1.1, 0.8), nb.noise(3 * scale, 3))
    pore = nb.ss(nb.noise(300, 2, 0.5, nb.mapv(scale=tuple(x * scale * 8 for x in st))), 0.62, 0.7)
    col = nb.mix(col, dark, nb.mul(pore, pores))
    height = nb.add(nb.mul(g, 0.2), nb.mul(pore, -0.3 * pores))
    r = nb.mixf(rough, rough + 0.1, g)
    metal_v = 0.0
    if varnish:
        r = nb.mixf(r, 0.18, varnish)
    if paint is not None:
        pw = nb.math("MAXIMUM", nb.chips(paint_wear, 7 * scale), nb.scratches(30 * scale, paint_wear))
        fade = nb.noise(2.5 * scale, 6, 0.6)
        pc = nb.mix(paint, nb.hsv(paint, 0.47, 0.8, 0.72), nb.ss(fade, 0.35, 0.75))
        pc = nb.mix(pc, nb.hsv(pc, 0.5, 1.0, 0.82), nb.mul(g, 0.6))
        col = nb.mix(pc, col, pw)
        r = nb.mixf(nb.mr(fade, 0, 1, 0.55, 0.8), r, pw)
        height = nb.add(nb.mul(height, 0.35), nb.mul(pw, -0.6))
    grime = nb.ss(nb.noise(3 * scale, 8, 0.65), 0.45, 0.8)
    col = nb.mix(col, nb.hsv(col, 0.5, 0.9, 0.6), nb.mul(grime, 0.5))
    if dirt:
        d = nb.mul(nb.cavity(0.03), dirt, clamp=True)
        col = nb.mix(col, (0.035, 0.025, 0.015), d)
    if wear:
        e = nb.mul(nb.edges(0.004), wear, clamp=True)
        col = nb.mix(col, nb.hsv(col, 0.5, 0.9, 1.25), e)
    return _finish(nb, col, r, metal_v, height, bump_strength, 0.002, layers)


def nb_lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def stone(name, c1=(0.6, 0.58, 0.55), c2=(0.35, 0.33, 0.3), kind="limestone", rough=0.7, veins=None,
          vein_amt=0.5, scale=1.0, dirt=0.5, wear=0.3, polish=0.0, layers=None, bump_strength=0.35,
          chips=0.3):
    nb = NB(name)
    s = scale
    if kind == "marble":
        warp = nb.noise(1.2 * s, 10, 0.6, distort=3.0, out="Color")
        vn = nb.wave(2.0 * s, warp, kind="BANDS", axis="X", distort=12, detail=8, dscale=2)
        vm = nb.ss(nb.math("ABSOLUTE", nb.sub(vn, 0.5)), 0.03, 0.0)
        col = nb.mix(c1, c2, nb.noise(4 * s, 6, 0.6))
        col = nb.mix(col, veins or (0.25, 0.25, 0.25), nb.mul(vm, vein_amt))
        height = nb.mul(nb.noise(80 * s, 4), 0.05)
    elif kind == "granite":
        v = nb.voronoi(180 * s, feature="F1", out="Color")
        col = nb.mix(c1, c2, nb.gray(v))
        col = nb.mix(col, (0.02, 0.02, 0.02), nb.ss(nb.noise(250 * s, 2), 0.6, 0.66))
        height = nb.mul(nb.noise(200 * s, 3), 0.1)
    else:  # limestone / sandstone / basalt / clay-ish
        n1 = nb.noise(6 * s, 12, 0.7)
        col = nb.ramp(n1, [(0.3, c2), (0.7, c1)])
        grit = nb.noise(400 * s, 2, 0.5)
        col = nb.mix(col, nb.hsv(col, 0.5, 1.0, 0.75), nb.ss(grit, 0.55, 0.7))
        pits = nb.ss(nb.voronoi(60 * s, feature="F1"), 0.12, 0.0)
        height = nb.add(nb.mul(nb.noise(30 * s, 10, 0.7), 0.6), nb.mul(pits, -0.5))
        height = nb.add(height, nb.mul(grit, 0.2))
    r = nb.mixf(rough, rough * 0.4, polish) if polish else rough
    r = nb.mr(nb.noise(20 * s, 4), 0.3, 0.7, r - 0.08, r + 0.08) if not polish else r
    if chips:
        ch = nb.mul(nb.edges(0.006, 0.05, 0.3), nb.ss(nb.noise(25 * s, 6, 0.7), 0.5, 0.62))
        ch = nb.mul(ch, chips)
        height = nb.sub(height, nb.mul(ch, 0.8))
        col = nb.mix(col, nb.hsv(col, 0.5, 0.8, 1.2), ch)
    if dirt:
        d = nb.mul(nb.cavity(0.04), dirt, clamp=True)
        col = nb.mix(col, (0.05, 0.04, 0.03), d)
    if wear:
        e = nb.mul(nb.edges(0.005), wear, clamp=True)
        col = nb.mix(col, nb.hsv(col, 0.5, 0.9, 1.2), e)
    return _finish(nb, col, r, 0.0, height, bump_strength, 0.003, layers)


def ceramic(name, color=(0.5, 0.2, 0.08), rough=0.55, glaze=False, crackle=0.0, speckle=0.3,
            dirt=0.5, wear=0.4, chips=0.2, body=(0.45, 0.22, 0.1), scale=1.0, layers=None,
            bump_strength=0.2, drips=0.0):
    """Terracotta (glaze=False) or glazed ceramic/porcelain."""
    nb = NB(name)
    s = scale
    col = nb.mix(color, nb.hsv(color, 0.5, 1.05, 0.85), nb.noise(8 * s, 6, 0.6))
    height = nb.mul(nb.noise(90 * s, 4, 0.5), 0.1 if not glaze else 0.02)
    r = rough if glaze else nb.mr(nb.noise(30 * s, 4), 0.3, 0.7, rough - 0.08, rough + 0.08)
    if speckle:
        sp = nb.ss(nb.noise(500 * s, 2, 0.5), 0.68, 0.72)
        col = nb.mix(col, nb.hsv(color, 0.5, 1.0, 0.5), nb.mul(sp, speckle))
    if crackle:
        cr = nb.voronoi(40 * s, feature="DISTANCE_TO_EDGE", vec=nb.mapv(scale=1.0))
        crm = nb.mul(nb.mr(cr, 0.0, 0.015, 1, 0), crackle)
        col = nb.mix(col, (0.12, 0.1, 0.07), crm)
        height = nb.sub(height, nb.mul(crm, 0.1))
    if drips:
        dm = nb.ss(nb.noise(5 * s, 4, 0.5, nb.mapv(scale=(1, 1, 0.15))), 0.55, 0.6)
        col = nb.mix(col, nb.hsv(color, 0.5, 1.2, 0.6), nb.mul(dm, drips))
    col, r, metal, height = apply_layers(nb, col, r, 0.0, height, layers)
    if chips:
        ch = nb.mul(nb.mul(nb.edges(0.004, 0.05, 0.3), nb.ss(nb.noise(20 * s, 6, 0.7), 0.52, 0.6)), chips)
        col = nb.mix(col, body, ch)
        r = nb.mixf(r, 0.85, ch)
        height = nb.sub(height, nb.mul(ch, 0.5))
    if dirt:
        d = nb.mul(nb.cavity(0.03), dirt, clamp=True)
        col = nb.mix(col, (0.05, 0.035, 0.02), d)
        r = nb.mixf(r, 0.8, nb.mul(d, 0.5))
    if wear:
        e = nb.mul(nb.edges(0.003), wear, clamp=True)
        col = nb.mix(col, nb.hsv(col, 0.5, 0.85, 1.15), e)
    normal = nb.bump(height, bump_strength, 0.002)
    return nb.done(col, r, metal, normal)


def fabric(name, color=(0.3, 0.05, 0.04), color2=None, weave=400.0, rough=0.85, fuzz=0.3, dirt=0.4,
           wear=0.3, layers=None, sheen=0.3, uv=False, bump_strength=0.3):
    nb = NB(name)
    vec = nb.co(UV) if uv else nb.co()
    a = nb.wave(weave, vec, kind="BANDS", axis="X", distort=0.4, detail=1, profile="SIN")
    b = nb.wave(weave, vec, kind="BANDS", axis="Y" if uv else "Z", distort=0.4, detail=1, profile="SIN")
    w = nb.math("MAXIMUM", a, b)
    col = nb.mix(color, nb.hsv(color, 0.5, 1.0, 0.75), nb.mul(w, 0.5))
    if color2 is not None:
        col = nb.mix(col, color2, nb.ss(nb.noise(3, 6, 0.6), 0.45, 0.6))
    col = nb.mix(col, nb.hsv(color, 0.5, 0.9, 1.2), nb.mul(nb.noise(200, 3, 0.8), fuzz))
    height = nb.add(nb.mul(w, 0.4), nb.mul(nb.noise(30, 6), 0.3))
    if dirt:
        col = nb.mix(col, (0.04, 0.03, 0.02), nb.mul(nb.cavity(0.03), dirt, clamp=True))
    if wear:
        col = nb.mix(col, nb.hsv(col, 0.5, 0.7, 1.25), nb.mul(nb.edges(0.005), wear, clamp=True))
    return _finish(nb, col, rough, 0.0, height, bump_strength, 0.001, layers, **{"Sheen Weight": sheen})


def leather(name, color=(0.12, 0.05, 0.02), rough=0.6, wear=0.6, dirt=0.5, scale=1.0, layers=None,
            bump_strength=0.3):
    nb = NB(name)
    s = scale
    pebble = nb.voronoi(220 * s, feature="SMOOTH_F1", out="Distance")
    crease = nb.noise(35 * s, 10, 0.7, distort=0.5, kind="RIDGED_MULTIFRACTAL")
    col = nb.mix(color, nb.hsv(color, 0.5, 1.1, 0.7), nb.noise(6 * s, 6, 0.65))
    height = nb.add(nb.mul(pebble, 0.4), nb.mul(crease, -0.2))
    r = nb.mr(nb.noise(12 * s, 4), 0.3, 0.7, rough - 0.12, rough + 0.12)
    if wear:
        e = nb.mul(nb.edges(0.004), wear, clamp=True)
        col = nb.mix(col, nb.hsv(color, 0.5, 0.9, 1.7), e)
        r = nb.mixf(r, rough * 0.6, e)
    if dirt:
        col = nb.mix(col, (0.02, 0.012, 0.006), nb.mul(nb.cavity(0.02), dirt, clamp=True))
    return _finish(nb, col, r, 0.0, height, bump_strength, 0.001, layers)


def plastic(name, color=(0.02, 0.012, 0.008), rough=0.25, marble=None, wear=0.3, dirt=0.4,
            layers=None, scale=1.0, bump_strength=0.1):
    """Bakelite / lacquer / enamel."""
    nb = NB(name)
    col = color
    if marble is not None:
        w = nb.noise(4 * scale, 8, 0.6, distort=2.0)
        col = nb.mix(color, marble, nb.ss(w, 0.45, 0.65))
    height = nb.mul(nb.noise(150 * scale, 3), 0.03)
    r = nb.mr(nb.noise(20 * scale, 4), 0.3, 0.7, rough * 0.8, rough * 1.4)
    if wear:
        e = nb.mul(nb.edges(0.003), wear, clamp=True)
        col = nb.mix(col, nb.hsv(color, 0.5, 0.9, 1.6), e)
        r = nb.mixf(r, rough * 2.0, e)
    if dirt:
        col = nb.mix(col, (0.02, 0.015, 0.01), nb.mul(nb.cavity(0.02), dirt, clamp=True))
    return _finish(nb, col, r, 0.0, height, bump_strength, 0.001, layers)


def gem(name, color=(0.05, 0.35, 0.18), color2=None, rough=0.12, veins=0.4, scale=1.0, layers=None,
        dirt=0.2, bump_strength=0.05, cloud=0.5):
    """Jade, lapis, turquoise, obsidian... (opaque stone with polish)."""
    nb = NB(name)
    c2 = color2 or nb_lerp(color, (0.9, 0.95, 0.85), 0.35)
    cl = nb.noise(3 * scale, 10, 0.65, distort=1.5)
    col = nb.mix(color, c2, nb.mul(nb.ss(cl, 0.4, 0.75), cloud))
    if veins:
        v = nb.voronoi(4 * scale, nb.mapv(nb.noise(2 * scale, 4, out="Color")), feature="DISTANCE_TO_EDGE")
        col = nb.mix(col, nb.hsv(color, 0.5, 1.2, 0.5), nb.mul(nb.mr(v, 0, 0.02, 1, 0), veins))
    height = nb.mul(nb.noise(60 * scale, 3), 0.02)
    if dirt:
        col = nb.mix(col, (0.02, 0.02, 0.015), nb.mul(nb.cavity(0.015), dirt, clamp=True))
    return _finish(nb, col, rough, 0.0, height, bump_strength, 0.001, layers, **{"Coat Weight": 0.3})


def paper(name, color=(0.62, 0.52, 0.34), rough=0.85, fibers="papyrus", layers=None, dirt=0.4,
          stains=0.4, bump_strength=0.25):
    nb = NB(name)
    uvv = nb.co(UV)
    if fibers == "papyrus":
        h = nb.wave(60, uvv, kind="BANDS", axis="X", distort=6, detail=6, profile="SIN")
        v = nb.wave(60, uvv, kind="BANDS", axis="Y", distort=6, detail=6, profile="SIN")
        f = nb.mixf(h, v, 0.5)
    else:
        f = nb.noise(300, 8, 0.7, uvv)
    col = nb.mix(color, nb.hsv(color, 0.5, 1.1, 0.8), nb.mul(f, 0.6))
    if stains:
        st = nb.ss(nb.noise(4, 8, 0.7, uvv), 0.55, 0.75)
        col = nb.mix(col, nb.hsv(color, 0.5, 1.3, 0.55), nb.mul(st, stains))
    col = nb.mix(col, nb.hsv(color, 0.5, 1.2, 0.5), nb.mul(nb.edges(0.004), 0.6, clamp=True))
    height = nb.mul(f, 0.4)
    if dirt:
        col = nb.mix(col, (0.08, 0.05, 0.02), nb.mul(nb.cavity(0.02), dirt, clamp=True))
    return _finish(nb, col, rough, 0.0, height, bump_strength, 0.001, layers)


def feather(name, c1=(0.0, 0.25, 0.08), c2=(0.01, 0.05, 0.12), tip=None, rough=0.4, sheen=0.6):
    """Feathers: iridescent-ish gradient along design-UV v, barbs across."""
    nb = NB(name)
    uvv = nb.co(UV)
    x, y, _ = nb.sep(uvv)
    barbs = nb.wave(160, nb.mapv(uvv, rot=(0, 0, 0.6)), kind="BANDS", axis="X", distort=1.5, detail=2)
    col = nb.mix(c1, c2, nb.ss(y, 0.2, 0.9))
    if tip is not None:
        col = nb.mix(col, tip, nb.ss(y, 0.85, 0.95))
    col = nb.mix(col, nb.hsv(col, 0.5, 1.0, 0.6), nb.mul(barbs, 0.5))
    height = nb.mul(barbs, 0.5)
    return _finish(nb, col, rough, 0.0, height, 0.3, 0.001, None, **{"Sheen Weight": sheen})


def glass(name, color=(0.9, 0.95, 0.92), rough=0.02, ior=1.5, tint_strength=1.0):
    """Transmissive glass (not baked; exported via KHR_materials_transmission)."""
    nb = NB(name)
    nb.m["nobake"] = True
    return nb.done(color, rough, 0.0, None, **{"Transmission Weight": 1.0, "IOR": ior})


def liquid(name, color=(0.25, 0.01, 0.02), rough=0.05):
    nb = NB(name)
    nb.m["nobake"] = True
    return nb.done(color, rough, 0.0, None, **{"Transmission Weight": 0.9, "IOR": 1.34})


def emissive(name, color=(1.0, 0.6, 0.25), strength=3.0, base=(0.8, 0.7, 0.5)):
    nb = NB(name)
    nb.m["nobake"] = True
    return nb.done(base, 0.5, 0.0, None, **{"Emission Color": color, "Emission Strength": strength})


def asset_dir():
    return os.environ.get("FORGE_WORK", "/tmp/forge")


def axis_mask(axis, lo, hi, noise=0.0, nscale=20.0):
    """Layer mask factory: smooth ramp along an object-space axis (lo -> hi)."""
    def f(nb):
        v = nb.sep(nb.co())["XYZ".index(axis)]
        if noise:
            v = nb.add(v, nb.mul(nb.sub(nb.noise(nscale, 6, 0.6), 0.5), noise))
        return nb.ss(v, lo, hi)
    return f


def noise_mask(scale=10.0, lo=0.5, hi=0.6, detail=8):
    return lambda nb: nb.ss(nb.noise(scale, detail, 0.65), lo, hi)


def radial_mask(r0, r1, axes="XY"):
    """1 inside r0, fading to 0 at r1 (distance from the object-space axis)."""
    def f(nb):
        s = nb.sep(nb.co())
        a, b = s["XYZ".index(axes[0])], s["XYZ".index(axes[1])]
        d = nb.math("SQRT", nb.add(nb.mul(a, a), nb.mul(b, b)))
        return nb.ss(d, r1, r0)
    return f
