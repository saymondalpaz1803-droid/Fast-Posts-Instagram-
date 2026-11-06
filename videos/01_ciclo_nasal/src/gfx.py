# -*- coding: utf-8 -*-
"""Primitivas gráficas (skia): cores, easing, caminhos suaves, setas, etiquetas, textos."""
import math
import skia

W, H = 1080, 1920
FONT_DIR = "/usr/share/fonts/opentype/inter/"
TF_BLACK = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-Black.otf")
TF_XB = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-ExtraBold.otf")
TF_B = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-Bold.otf")

YELLOW = "#FFD60A"
AIR_BLUE = "#2F6FEB"
INK = "#151515"


# ------------------------------------------------------------------ math / easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def prog(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease(x):
    x = clamp(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eback(x):
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def sm(t, t0, t1):
    return ease(prog(t, t0, t1))


def window(t, t0, t1, fi=0.25, fo=0.25):
    """1 dentro de [t0,t1], com rampas de entrada/saída."""
    if t < t0 or t > t1 + fo:
        return 0.0
    a = eout(prog(t, t0, t0 + fi))
    if t > t1:
        a *= 1 - ease(prog(t, t1, t1 + fo))
    return a


# ------------------------------------------------------------------ cores
def rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def C(h, a=1.0):
    r, g, b = rgb(h)
    return skia.Color(r, g, b, int(round(255 * clamp(a))))


def mixc(h1, h2, t, a=1.0):
    r1, g1, b1 = rgb(h1)
    r2, g2, b2 = rgb(h2)
    t = clamp(t)
    return skia.Color(int(lerp(r1, r2, t)), int(lerp(g1, g2, t)), int(lerp(b1, b2, t)), int(round(255 * clamp(a))))


def mixhex(h1, h2, t):
    r1, g1, b1 = rgb(h1)
    r2, g2, b2 = rgb(h2)
    t = clamp(t)
    return "#%02X%02X%02X" % (int(lerp(r1, r2, t)), int(lerp(g1, g2, t)), int(lerp(b1, b2, t)))


def P(color=None, stroke=0, shader=None, blur=0, cap_round=True, alpha=None):
    p = skia.Paint(AntiAlias=True)
    if color is not None:
        p.setColor(color)
    if alpha is not None:
        p.setAlphaf(alpha)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap_round:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    if shader is not None:
        p.setShader(shader)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, pos)


def rad(x, y, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(x, y), r, cols, pos)


# ------------------------------------------------------------------ caminhos
def catmull(pts, closed=True, k=1.0):
    p = skia.Path()
    n = len(pts)
    if n < 2:
        return p
    p.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[(i + 1) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        p.close()
    return p


def mirror(pts):
    return [(-x, y) for x, y in pts]


def sym(half):
    """half: pontos do lado direito de cima p/ baixo (x>=0); retorna contorno fechado simétrico."""
    left = [(-x, y) for x, y in reversed(half) if x != 0]
    return half + left


def oval(cx, cy, rx, ry):
    return skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)


def poly(pts, closed=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


# ------------------------------------------------------------------ setas
def arrow_path(x0, y0, x1, y1, w, head=None):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    hl = head if head else w * 1.7
    hw = w * 1.15
    bx, by = x1 - ux * hl, y1 - uy * hl
    p = skia.Path()
    p.moveTo(x0 + nx * w / 2, y0 + ny * w / 2)
    p.lineTo(bx + nx * w / 2, by + ny * w / 2)
    p.lineTo(bx + nx * hw, by + ny * hw)
    p.lineTo(x1, y1)
    p.lineTo(bx - nx * hw, by - ny * hw)
    p.lineTo(bx - nx * w / 2, by - ny * w / 2)
    p.lineTo(x0 - nx * w / 2, y0 - ny * w / 2)
    p.arcTo(skia.Rect.MakeLTRB(x0 - w / 2, y0 - w / 2, x0 + w / 2, y0 + w / 2), 0, 0, False)
    p.close()
    return p


def draw_arrow(c, x0, y0, x1, y1, w, color, outline="#10264F", ow=None, alpha=1.0, glow=True):
    if alpha <= 0.01 or w <= 0.5:
        return
    p = arrow_path(x0, y0, x1, y1, w)
    ow = ow if ow is not None else max(2.0, w * 0.16)
    if glow:
        c.drawPath(p, P(C("#FFFFFF", 0.55 * alpha), stroke=ow * 3.2, blur=ow * 1.5))
    c.drawPath(p, P(C(outline, alpha), stroke=ow * 2))
    r, g, b = rgb(color)
    light = "#%02X%02X%02X" % (min(255, r + 70), min(255, g + 70), min(255, b + 70))
    c.drawPath(p, P(shader=lin(x0, y0, x1, y1, [C(color, alpha), C(light, alpha)])))


# ------------------------------------------------------------------ texto
def font(tf, size):
    f = skia.Font(tf, size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def text_w(txt, f):
    return f.measureText(txt)


def outlined_text(c, txt, x, y, f, fill="#FFFFFF", stroke=14, scolor="#000000", alpha=1.0, shadow=True):
    """Desenha texto com contorno (x = esquerda, y = baseline)."""
    if shadow:
        c.drawString(txt, x, y + stroke * 0.45, f, P(C("#000000", 0.45 * alpha), stroke=stroke * 1.1, blur=stroke * 0.5))
    c.drawString(txt, x, y, f, P(C(scolor, alpha), stroke=stroke))
    c.drawString(txt, x, y, f, P(C(fill, alpha)))


def rich_line(c, parts, cx, cy, size, tf=None, stroke=None, alpha=1.0, scale=1.0, max_w=980):
    """parts: [(texto, cor_hex)], centralizado em (cx, cy=centro vertical)."""
    tf = tf or TF_BLACK
    f = font(tf, size)
    sp = text_w(" ", f)
    widths = [text_w(t, f) for t, _ in parts]
    total = sum(widths) + sp * (len(parts) - 1)
    s = scale * min(1.0, max_w / max(total, 1))
    stroke = stroke if stroke is not None else size * 0.17
    c.save()
    c.translate(cx, cy)
    c.scale(s, s)
    x = -total / 2
    base = size * 0.36
    for (t, col), w in zip(parts, widths):
        outlined_text(c, t, x, base, f, fill=col, stroke=stroke, alpha=alpha)
        x += w + sp
    c.restore()


def pill_label(c, txt, x, y, alpha=1.0, scale=1.0, dot="#2F6FEB", size=34, anchor=None, anchors=None):
    """Etiqueta em cápsula branca com letras pretas (estilo das referências)."""
    if alpha <= 0.01:
        return
    f = font(TF_XB, size)
    tw = text_w(txt, f)
    pad = size * 0.62
    dot_r = size * 0.2
    wtot = tw + pad * 2 + dot_r * 2 + size * 0.3
    h = size * 1.55
    pts = []
    if anchor:
        pts.append(anchor)
    if anchors:
        pts += anchors
    for ax, ay in pts:  # linha guia até a estrutura
        c.drawLine(x, y, ax, ay, P(C("#1C1C1C", 0.9 * alpha), stroke=7))
        c.drawLine(x, y, ax, ay, P(C("#FFFFFF", alpha), stroke=3.5))
        c.drawCircle(ax, ay, 11, P(C("#1C1C1C", alpha)))
        c.drawCircle(ax, ay, 7, P(C("#FFFFFF", alpha)))
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-wtot / 2, -h / 2, wtot, h), h / 2, h / 2)
    c.save()
    c.translate(0, 5)
    c.drawRRect(r, P(C("#000000", 0.25 * alpha), blur=6))
    c.restore()
    c.drawRRect(r, P(C("#FFFFFF", alpha)))
    c.drawRRect(r, P(C("#3A2A20", alpha), stroke=3.5))
    dx = -wtot / 2 + pad * 0.75 + dot_r
    c.drawCircle(dx, 0, dot_r, P(C(dot, alpha)))
    c.drawString(txt, dx + dot_r + size * 0.3, size * 0.36, f, P(C(INK, alpha)))
    c.restore()


# ------------------------------------------------------------------ ícones
def icon_ffwd(c, x, y, s=1.0, alpha=1.0, color=YELLOW):
    """Ícone de avanço rápido: duas setas amarelas."""
    if alpha <= 0.01:
        return
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for ox in (-34, 30):
        tri = poly([(ox - 30, -38), (ox + 34, 0), (ox - 30, 38)])
        c.drawPath(tri, P(C("#000000", 0.3 * alpha), blur=6))
        c.drawPath(tri, P(C("#3A2A00", alpha), stroke=9))
        c.drawPath(tri, P(shader=lin(0, -38, 0, 38, [C("#FFE45C", alpha), C(color, alpha)])))
    c.restore()


def icon_rewind(c, x, y, s=1.0, alpha=1.0):
    """Ícone de retrocesso: duas setas brancas + linhas horizontais."""
    if alpha <= 0.01:
        return
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for i, (ly, lw) in enumerate([(-24, 70), (0, 95), (24, 70)]):
        c.drawLine(70, ly, 70 + lw, ly, P(C("#1A1A1A", alpha), stroke=13))
        c.drawLine(70, ly, 70 + lw, ly, P(C("#FFFFFF", alpha), stroke=7))
    for ox in (34, -30):
        tri = poly([(ox + 30, -40), (ox - 34, 0), (ox + 30, 40)])
        c.drawPath(tri, P(C("#000000", 0.3 * alpha), blur=6))
        c.drawPath(tri, P(C("#1A1A1A", alpha), stroke=9))
        c.drawPath(tri, P(C("#FFFFFF", alpha)))
    c.restore()


def icon_clock(c, x, y, r, t, alpha=1.0, speed=6.0):
    if alpha <= 0.01:
        return
    c.drawCircle(x, y + 4, r, P(C("#000000", 0.25 * alpha), blur=5))
    c.drawCircle(x, y, r, P(C("#FFFFFF", alpha)))
    c.drawCircle(x, y, r, P(C("#1A1A1A", alpha), stroke=6))
    for k in range(12):
        a = k * math.pi / 6
        c.drawLine(x + math.cos(a) * r * 0.78, y + math.sin(a) * r * 0.78,
                   x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9, P(C("#1A1A1A", alpha), stroke=3))
    am = t * speed
    ah = t * speed / 12
    c.drawLine(x, y, x + math.sin(ah) * r * 0.45, y - math.cos(ah) * r * 0.45, P(C("#1A1A1A", alpha), stroke=7))
    c.drawLine(x, y, x + math.sin(am) * r * 0.72, y - math.cos(am) * r * 0.72, P(C("#E63946", alpha), stroke=5))
    c.drawCircle(x, y, 5, P(C("#1A1A1A", alpha)))


def icon_cycle(c, x, y, r, t, alpha=1.0):
    """Duas setas curvas formando um ciclo (alternância)."""
    if alpha <= 0.01:
        return
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(t * 0.9))
    for k in range(2):
        c.save()
        c.rotate(180 * k)
        path = skia.Path()
        path.addArc(oval(0, 0, r, r), 200, 120)
        c.drawPath(path, P(C("#3A2A00", alpha), stroke=26))
        c.drawPath(path, P(C(YELLOW, alpha), stroke=15))
        a = math.radians(320)
        hx, hy = math.cos(a) * r, math.sin(a) * r
        tx, ty = -math.sin(a), math.cos(a)
        nx, ny = math.cos(a), math.sin(a)
        tri = poly([(hx + tx * 26, hy + ty * 26), (hx + nx * 22, hy + ny * 22), (hx - nx * 22, hy - ny * 22)])
        c.drawPath(tri, P(C("#3A2A00", alpha), stroke=8))
        c.drawPath(tri, P(C(YELLOW, alpha)))
        c.restore()
    c.restore()


def icon_warning(c, x, y, s, alpha=1.0):
    tri = catmull([(0, -52), (52, 40), (-52, 40)], closed=True, k=0.25)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawPath(tri, P(C("#000000", 0.25 * alpha), blur=5))
    c.drawPath(tri, P(C("#2A1A00", alpha), stroke=10))
    c.drawPath(tri, P(C("#FFC300", alpha)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-6, -22, 6, 14), 5, 5), P(C("#2A1A00", alpha)))
    c.drawCircle(0, 27, 7, P(C("#2A1A00", alpha)))
    c.restore()


def icon_bubble(c, x, y, s, t, alpha=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Path()
    body.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-90, -62, 90, 50), 40, 40))
    tail = poly([(-50, 40), (-78, 92), (-8, 46)])
    body.addPath(tail)
    c.drawPath(body, P(C("#000000", 0.3 * alpha), blur=8))
    c.drawPath(body, P(C("#1A1A1A", alpha), stroke=10))
    c.drawPath(body, P(C("#FFFFFF", alpha)))
    for k in range(3):
        b = 0.5 + 0.5 * math.sin(t * 7 - k * 0.9)
        c.drawCircle(-44 + k * 44, -6 - 8 * b, 13, P(C("#1A1A1A", alpha)))
    c.restore()
