"""2D masks for painted / inlaid / engraved designs (drawn with PIL in design-UV
space). White = design, black = background. Saved into the per-asset work dir."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "hiero": os.path.join(HERE, "fonts", "NotoSansEgyptianHieroglyphs.ttf"),
    "runic": os.path.join(HERE, "fonts", "NotoSansRunic.ttf"),
    "linearb": os.path.join(HERE, "fonts", "NotoSansLinearB.ttf"),
    "cjk": "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "serif_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "sans_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
}


def workdir():
    d = os.environ.get("FORGE_WORK", "/tmp/forge")
    os.makedirs(d, exist_ok=True)
    return d


class Canvas:
    """Coordinates are in UV units (0..1, v up) unless noted."""

    def __init__(self, w=2048, h=None, ss=2):
        self.W, self.H, self.ss = w, h or w, ss
        self.im = Image.new("L", (self.W * ss, self.H * ss), 0)
        self.d = ImageDraw.Draw(self.im)

    def px(self, u, v):
        return (u * self.W * self.ss, (1 - v) * self.H * self.ss)

    def pw(self, w):
        return max(1, int(w * self.W * self.ss))

    def line(self, pts, width=0.004, fill=255, closed=False):
        p = [self.px(*q) for q in pts]
        if closed:
            p.append(p[0])
        self.d.line(p, fill=fill, width=self.pw(width), joint="curve")
        r = self.pw(width) / 2
        for q in (p[0], p[-1]):
            self.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=fill)
        return self

    def poly(self, pts, fill=255):
        self.d.polygon([self.px(*q) for q in pts], fill=fill)
        return self

    def circle(self, u, v, r, fill=255, outline=None, width=0.003):
        x, y = self.px(u, v)
        R = r * self.W * self.ss
        if outline is None:
            self.d.ellipse([x - R, y - R, x + R, y + R], fill=fill)
        else:
            self.d.ellipse([x - R, y - R, x + R, y + R], outline=outline, width=self.pw(width))
        return self

    def rect(self, u0, v0, u1, v1, fill=255):
        a, b = self.px(u0, v1), self.px(u1, v0)
        self.d.rectangle([a, b], fill=fill)
        return self

    def text(self, u, v, s, size=0.05, font="serif", fill=255, anchor="mm", angle=0):
        f = ImageFont.truetype(FONTS.get(font, font), int(size * self.H * self.ss))
        if angle:
            tmp = Image.new("L", self.im.size, 0)
            ImageDraw.Draw(tmp).text(self.px(u, v), s, font=f, fill=fill, anchor=anchor)
            tmp = tmp.rotate(angle, center=self.px(u, v), resample=Image.BICUBIC)
            self.im = Image.fromarray(np.maximum(np.asarray(self.im), np.asarray(tmp)))
            self.d = ImageDraw.Draw(self.im)
        else:
            self.d.text(self.px(u, v), s, font=f, fill=fill, anchor=anchor)
        return self

    # ---- ornamental bands (u0..u1 horizontally, v0..v1 band)
    def meander(self, v0, v1, u0=0.0, u1=1.0, n=24, width=None):
        h = v1 - v0
        w = width or h * 0.12
        step = (u1 - u0) / n
        for i in range(n):
            x = u0 + i * step
            a = step
            pts = [(x, v0 + 0.1 * h), (x, v1 - 0.1 * h), (x + 0.8 * a, v1 - 0.1 * h), (x + 0.8 * a, v0 + 0.35 * h),
                   (x + 0.3 * a, v0 + 0.35 * h), (x + 0.3 * a, v0 + 0.6 * h), (x + 0.55 * a, v0 + 0.6 * h)]
            self.line(pts, w)
            self.line([(x, v0 + 0.1 * h), (x + a, v0 + 0.1 * h)], w)
        return self

    def zigzag(self, v0, v1, u0=0.0, u1=1.0, n=30, width=0.004):
        pts = [(u0 + (u1 - u0) * i / n, v0 if i % 2 == 0 else v1) for i in range(n + 1)]
        return self.line(pts, width)

    def dots(self, v, u0=0.0, u1=1.0, n=40, r=0.004):
        for i in range(n):
            self.circle(u0 + (u1 - u0) * (i + 0.5) / n, v, r)
        return self

    def hband(self, v0, v1, u0=0.0, u1=1.0):
        return self.rect(u0, v0, u1, v1)

    def step_fret(self, v0, v1, u0=0.0, u1=1.0, n=10, width=None):
        """Mesoamerican xicalcoliuhqui (stepped spiral) band."""
        h = v1 - v0
        w = width or h * 0.09
        step = (u1 - u0) / n
        for i in range(n):
            x = u0 + i * step
            s = step
            spiral = [(x + 0.5 * s, v0 + 0.5 * h), (x + 0.5 * s, v0 + 0.72 * h), (x + 0.28 * s, v0 + 0.72 * h),
                      (x + 0.28 * s, v0 + 0.28 * h), (x + 0.72 * s, v0 + 0.28 * h), (x + 0.72 * s, v1 - 0.08 * h)]
            self.line(spiral, w)
            steps = [(x + 0.72 * s, v1 - 0.08 * h), (x + 0.86 * s, v1 - 0.08 * h), (x + 0.86 * s, v0 + 0.5 * h),
                     (x + 1.0 * s, v0 + 0.5 * h), (x + 1.0 * s, v0 + 0.08 * h), (x + 1.28 * s, v0 + 0.08 * h)]
            self.line(steps, w)
        return self

    def cloud_scroll(self, cu, cv, r, turns=1.6, width=0.004, flip=False):
        pts = []
        for t in np.linspace(0, turns * 2 * math.pi, 80):
            rr = r * (1 - t / (turns * 2 * math.pi) * 0.85)
            a = t if not flip else -t
            pts.append((cu + rr * math.cos(a), cv + rr * math.sin(a)))
        return self.line(pts, width)

    def blur(self, px=1.0):
        self.im = self.im.filter(ImageFilter.GaussianBlur(px * self.ss))
        self.d = ImageDraw.Draw(self.im)
        return self

    def grow(self, px=1):
        self.im = self.im.filter(ImageFilter.MaxFilter(int(px * self.ss) * 2 + 1))
        self.d = ImageDraw.Draw(self.im)
        return self

    def invert(self):
        self.im = Image.eval(self.im, lambda x: 255 - x)
        self.d = ImageDraw.Draw(self.im)
        return self

    def paste_mask(self, other, mode="max"):
        a, b = np.asarray(self.im), np.asarray(other.im.resize(self.im.size))
        self.im = Image.fromarray(np.maximum(a, b) if mode == "max" else np.minimum(a, 255 - b))
        self.d = ImageDraw.Draw(self.im)
        return self

    def save(self, name):
        path = os.path.join(workdir(), name + ".png")
        self.im.resize((self.W, self.H), Image.LANCZOS).save(path)
        return path


def hieroglyphs(seed=0, n=12, pool=None):
    """Pick n real hieroglyph code points (Gardiner signs) for cartouches/columns."""
    rng = np.random.default_rng(seed)
    pool = pool or [0x13000, 0x1300B, 0x13050, 0x13062, 0x13080, 0x1309D, 0x130A7, 0x130B8, 0x130C0,
                    0x130D1, 0x130ED, 0x13103, 0x13117, 0x13121, 0x13153, 0x13171, 0x13177, 0x1318B,
                    0x13191, 0x131A3, 0x131B1, 0x131CB, 0x131DD, 0x131E0, 0x131F3, 0x13216, 0x13254,
                    0x1327F, 0x1328F, 0x132AA, 0x132F4, 0x13319, 0x1333C, 0x1336F, 0x13399, 0x133CF, 0x13402]
    return "".join(chr(pool[i]) for i in rng.integers(0, len(pool), n))
