"""Helpers to paint a livery in 3D: texels know their model-space position/normal/object (baked maps),
decals are drawn in 2D planes (metres) and projected onto the texels."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import map_coordinates

# DINish (SIL Open Font License, https://github.com/playbeing/dinish), a DIN 1451 revival: the lettering of the
# real aircraft is DIN. Point DINISH_DIR to the folder holding DINish-Medium.ttf / DINish-Bold.ttf.
FONTDIR = os.environ.get('DINISH_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'))
CAP_RATIO = 0.69          # DINish cap height / em
SS = 4                    # supersampling when drawing decals


def font(weight='Medium'):
    return os.path.join(FONTDIR, f'DINish-{weight}.ttf')


class Canvas2D:
    """A decal canvas covering [s0,s1] x [t0,t1] metres, drawn with supersampling, RGBA."""
    def __init__(self, s0, s1, t0, t1, res=500.0):
        self.s0, self.s1, self.t0, self.t1, self.res = s0, s1, t0, t1, res
        self.W = int(np.ceil((s1 - s0) * res * SS)); self.H = int(np.ceil((t1 - t0) * res * SS))
        self.img = Image.new('RGBA', (self.W, self.H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def px(self, s, t):
        return ((s - self.s0) * self.res * SS, (self.t1 - t) * self.res * SS)

    def m(self, v):
        return v * self.res * SS

    def text(self, s, t_base, txt, cap, color, weight='Medium', anchor='ls'):
        f = ImageFont.truetype(font(weight), max(1, int(round(self.m(cap) / CAP_RATIO))))
        self.d.text(self.px(s, t_base), txt, font=f, fill=color, anchor=anchor)
        return f

    def glyph(self, s_center, t_base, ch, cap, color, weight='Medium', stretch=1.0):
        """draw one glyph centred horizontally (ink box) at s_center; optional horizontal stretch."""
        f = ImageFont.truetype(font(weight), max(1, int(round(self.m(cap) / CAP_RATIO))))
        bb = f.getbbox(ch, anchor='ls')
        gw = bb[2] - bb[0] + 8; gh = bb[3] - bb[1] + 8
        g = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((4 - bb[0], 4 - bb[1]), ch, font=f, fill=color, anchor='ls')
        if stretch != 1.0:
            g = g.resize((max(1, int(round(gw * stretch))), gh), Image.LANCZOS)
        cx, by = self.px(s_center, t_base)
        # baseline sits at g row (4 - bb[1])
        x0 = int(round(cx - g.width / 2)); y0 = int(round(by - (4 - bb[1])))
        self.img.alpha_composite(g, (max(x0, 0), max(y0, 0)))
        return (g.width - 8 * stretch) / (self.res * SS)

    def text_width(self, txt, cap, weight='Medium', tracking=0.0):
        f = ImageFont.truetype(font(weight), max(1, int(round(self.m(cap) / CAP_RATIO))))
        return f.getlength(txt) / (self.res * SS) + tracking * (len(txt) - 1)

    def tracked_text(self, s, t_base, txt, cap, color, weight='Medium', tracking=0.0):
        f = ImageFont.truetype(font(weight), max(1, int(round(self.m(cap) / CAP_RATIO))))
        x = s
        for ch in txt:
            self.d.text(self.px(x, t_base), ch, font=f, fill=color, anchor='ls')
            x += f.getlength(ch) / (self.res * SS) + tracking
        return x - tracking

    def rect(self, s0, t0, s1, t1, color):
        a = self.px(s0, t1); b = self.px(s1, t0)
        self.d.rectangle([a, b], fill=color)

    def rrect(self, s0, t0, s1, t1, r, color=None, outline=None, width=0.0):
        a = self.px(s0, t1); b = self.px(s1, t0)
        self.d.rounded_rectangle([a, b], radius=self.m(r), fill=color, outline=outline,
                                 width=max(1, int(round(self.m(width)))) if outline else 0)

    def ellipse(self, sc, tc, rs, rt, color=None, outline=None, width=0.0):
        a = self.px(sc - rs, tc + rt); b = self.px(sc + rs, tc - rt)
        self.d.ellipse([a, b], fill=color, outline=outline, width=max(1, int(round(self.m(width)))) if outline else 0)

    def polygon(self, pts, color):
        self.d.polygon([self.px(s, t) for s, t in pts], fill=color)

    def line(self, pts, color, width):
        self.d.line([self.px(s, t) for s, t in pts], fill=color, width=max(1, int(round(self.m(width)))), joint='curve')

    def arc(self, sc, tc, r, a0, a1, color, width, n=64):
        ang = np.radians(np.linspace(a0, a1, n))
        self.line([(sc + r * np.cos(a), tc + r * np.sin(a)) for a in ang], color, width)

    def finish(self):
        im = self.img.resize((max(1, self.W // SS), max(1, self.H // SS)), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32) / 255.0
        return a  # straight alpha RGBA


def project(tex, maps, canvas_arr, cv, origin, d, u, mask):
    """Composite a finished canvas onto tex (float RGB 0..1) for texels in mask.
    origin: model point of (s=0,t=0); d: unit reading direction; u: unit up direction."""
    ii, jj = np.nonzero(mask)
    if len(ii) == 0:
        return 0
    p = maps.pos[ii, jj].astype(np.float64) - np.asarray(origin)
    s = p @ np.asarray(d, float); t = p @ np.asarray(u, float)
    inb = (s >= cv.s0) & (s <= cv.s1) & (t >= cv.t0) & (t <= cv.t1)
    ii, jj, s, t = ii[inb], jj[inb], s[inb], t[inb]
    col = (s - cv.s0) * cv.res - 0.5; row = (cv.t1 - t) * cv.res - 0.5
    rgba = np.stack([map_coordinates(canvas_arr[..., k], [row, col], order=1, mode='constant', cval=0.0) for k in range(4)], -1)
    a = rgba[:, 3:4]
    tex[ii, jj] = tex[ii, jj] * (1 - a) + rgba[:, :3] * a
    return len(ii)


def value_noise(S, cells, seed, octaves=1):
    rng = np.random.default_rng(seed)
    out = np.zeros((S, S), np.float32)
    amp = 1.0; tot = 0
    for o in range(octaves):
        c = cells * (2 ** o)
        g = rng.standard_normal((c + 1, c + 1)).astype(np.float32)
        im = Image.fromarray(g, mode='F').resize((S, S), Image.BICUBIC)
        out += amp * np.asarray(im); tot += amp; amp *= 0.5
    return out / tot


def dilate_fill(tex, used, maxdist=32, fill=None):
    """give unused texels the colour of the nearest used texel (bleed protection for mipmaps)."""
    from scipy.ndimage import distance_transform_edt
    dist, (iy, ix) = distance_transform_edt(~used, return_indices=True)
    out = tex[iy, ix]
    if fill is not None:
        out[dist > maxdist] = fill
    return out
