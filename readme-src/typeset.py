"""Tiny typesetter: shapes text with HarfBuzz and emits glyph outlines as SVG
<use> references, so the README renders identically on every machine."""
import io, re
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

FONTS = ""  # Face() takes a full path

def _num(v):
    s = ("%.1f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

class Face:
    _n = 0
    def __init__(self, file, axes=None):
        tt = TTFont(FONTS + file)
        if "fvar" in tt:
            full = {a.axisTag: a.defaultValue for a in tt["fvar"].axes}
            full.update(axes or {})
            tt = instantiateVariableFont(tt, full)
        b = io.BytesIO(); tt.save(b); self.data = b.getvalue()
        self.tt = TTFont(io.BytesIO(self.data))
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upm = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(self.data))
        Face._n += 1
        self.key = "f%d_" % Face._n
        os2 = self.tt["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0) or 0.7 * self.upm
        self.xh = getattr(os2, "sxHeight", 0) or 0.5 * self.upm

    def shape(self, text, features=None):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hb, buf, features or {"kern": True, "liga": True})
        return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def outline(self, gid):
        pen = SVGPathPen(self.gs, ntos=_num)
        self.gs[self.order[gid]].draw(pen)
        return pen.getCommands()

    def width(self, text, size, tracking=0.0, features=None):
        g = self.shape(text, features)
        return (sum(a for _, a, _, _ in g) + tracking * self.upm * max(len(g) - 1, 0)) * size / self.upm


class SVG:
    def __init__(self, w, h, title=""):
        self.w, self.h, self.title = w, h, title
        self.defs, self.glyphs, self.body, self.style = [], {}, [], []

    def _ref(self, face, gid):
        rid = face.key + str(gid)
        if rid not in self.glyphs:
            d = face.outline(gid)
            self.glyphs[rid] = d
        return rid if self.glyphs[rid] else None

    def text(self, face, s, x, y, size, color, op=1.0, tracking=0.0,
             features=None, anchor="start", extra=""):
        g = face.shape(s, features)
        k = size / face.upm
        tr = tracking * face.upm
        total = sum(a for _, a, _, _ in g) + tr * max(len(g) - 1, 0)
        if anchor == "end": x -= total * k
        elif anchor == "middle": x -= total * k / 2
        pen, uses = 0.0, []
        for gid, adv, xo, yo in g:
            rid = self._ref(face, gid)
            if rid:
                uses.append('<use xlink:href="#%s" x="%s"%s/>' % (
                    rid, _num(pen + xo), (' y="%s"' % _num(yo)) if yo else ""))
            pen += adv + tr
        self.body.append(
            '<g transform="translate(%s %s) scale(%.5f %.5f)" fill="%s"%s%s>%s</g>' % (
                _num(x), _num(y), k, -k, color,
                (' opacity="%s"' % op) if op != 1 else "", extra, "".join(uses)))
        return total * k

    def wrap(self, face, s, size, maxw, tracking=0.0, features=None):
        words, lines, cur = s.split(" "), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if cur and face.width(t, size, tracking, features) > maxw:
                lines.append(cur); cur = w
            else:
                cur = t
        if cur: lines.append(cur)
        return lines

    def raw(self, s): self.body.append(s)

    def render(self):
        defs = "".join('<path id="%s" d="%s"/>' % (k, v) for k, v in self.glyphs.items() if v)
        style = ("<style>%s</style>" % "".join(self.style)) if self.style else ""
        t = ("<title>%s</title>" % self.title) if self.title else ""
        return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                'width="%s" height="%s" viewBox="0 0 %s %s" fill="none" role="img">%s%s<defs>%s%s</defs>%s</svg>'
                % (self.w, self.h, self.w, self.h, t, style, defs, "".join(self.defs), "".join(self.body)))

def balanced(svg, face, s, size, maxw, tracking=0.0, features=None):
    """Wrap to the fewest lines that fit maxw, then narrow the measure until
    just before it would add a line, so no line ends up as a lonely orphan."""
    lines = svg.wrap(face, s, size, maxw, tracking, features)
    n, lo, hi = len(lines), maxw * 0.5, maxw
    for _ in range(30):
        mid = (lo + hi) / 2
        if len(svg.wrap(face, s, size, mid, tracking, features)) > n: lo = mid
        else: hi = mid
    return svg.wrap(face, s, size, hi, tracking, features)


def para(svg, face, s, size, measure, features=None):
    """Wrap at the measure; if that strands a short last line, rebalance."""
    lines = svg.wrap(face, s, size, measure, features=features)
    if len(lines) > 1 and face.width(lines[-1], size, features=features) < 0.4 * measure:
        return balanced(svg, face, s, size, measure, features=features)
    return lines
