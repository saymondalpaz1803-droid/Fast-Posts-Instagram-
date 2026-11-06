# -*- coding: utf-8 -*-
"""Modelos anatômicos em coordenadas de "mundo" (origem ≈ ponta do nariz).

- draw_face(): rosto frontal estilizado com sombreamento volumétrico.
- draw_section(): corte frontal (coronal) da face na altura das conchas nasais,
  como uma maquete em placa: pele > gordura > músculo > osso, órbitas, células
  etmoidais, seios maxilares, cavidades nasais, septo e conchas (sup., média, inf.)
  revestidas por mucosa. A mucosa das conchas inferiores (e o "swell body" do septo)
  aumenta de espessura com a congestão — base do ciclo nasal.
"""
import math
import numpy as np
import skia
from gfx import *

# ======================================================================== ROSTO
SKIN_L, SKIN_M, SKIN_D = "#FBD9BE", "#F2BE97", "#DDA07A"
HAIR_D, HAIR_L = "#3B271E", "#6A4836"

HEAD = sym([(0, -440), (170, -418), (272, -322), (300, -172), (293, -22), (262, 112),
            (202, 232), (112, 316), (0, 346)])
HAIR = [(-306, -150), (-322, -330), (-236, -472), (0, -520), (236, -472), (322, -330), (306, -150),
        (282, -228), (196, -300), (60, -318), (-70, -300), (-190, -322), (-268, -262), (-292, -205)]


def head_path():
    return catmull(HEAD)


def _eye(c, s, blink, look=0.0):
    cx, cy = 120 * s, -150
    alm = skia.Path()
    alm.moveTo(cx - 50, cy)
    alm.cubicTo(cx - 30, cy - 32, cx + 30, cy - 32, cx + 50, cy)
    alm.cubicTo(cx + 30, cy + 25, cx - 30, cy + 25, cx - 50, cy)
    alm.close()
    # sombra da órbita
    c.drawOval(oval(cx, cy - 12, 78, 44), P(C("#B9805F", 0.16), blur=16))
    c.drawPath(alm, P(shader=lin(0, cy - 26, 0, cy + 22, [C("#E7E2DE"), C("#FFFFFF"), C("#F3EFEC")], [0, 0.45, 1])))
    c.save()
    c.clipPath(alm, skia.ClipOp.kIntersect, True)
    ix = cx + look * 8
    c.drawCircle(ix, cy, 26, P(shader=rad(ix, cy, 26, [C("#8A5A3A"), C("#5B3A26"), C("#2E1C12")], [0, 0.6, 1])))
    c.drawCircle(ix, cy, 11.5, P(C("#0E0A08")))
    c.drawCircle(ix - 9, cy - 9, 6.5, P(C("#FFFFFF", 0.95)))
    c.drawCircle(ix + 8, cy + 7, 3, P(C("#FFFFFF", 0.7)))
    c.drawRect(skia.Rect.MakeLTRB(cx - 55, cy - 30, cx + 55, cy - 18), P(C("#000000", 0.12), blur=5))
    if blink > 0:
        c.drawRect(skia.Rect.MakeLTRB(cx - 60, cy - 35, cx + 60, cy - 35 + 62 * blink),
                   P(shader=lin(0, cy - 35, 0, cy + 25, [C("#F3C3A0"), C("#E9AE88")])))
    c.restore()
    lid = skia.Path()
    top_y = lerp(-32, 18, blink)
    lid.moveTo(cx - 52, cy + 1)
    lid.cubicTo(cx - 30, cy + top_y, cx + 30, cy + top_y, cx + 52, cy + 1)
    c.drawPath(lid, P(C("#2E1C14"), stroke=6.5))
    low = skia.Path()
    low.moveTo(cx - 44, cy + 6)
    low.cubicTo(cx - 25, cy + 24, cx + 25, cy + 24, cx + 44, cy + 6)
    c.drawPath(low, P(C("#B97A5A", 0.45), stroke=3))
    # sobrancelha
    br = skia.Path()
    br.moveTo(cx - 62 * s, -212)          # ponta interna
    br.quadTo(cx - 2 * s, -250, cx + 66 * s, -222)
    c.drawPath(br, P(C(HAIR_D), stroke=17))


def draw_face(c, t, blink=0.0, flare=1.0, outline_only=False):
    # ---- ombros / camiseta
    sh = skia.Path()
    sh.moveTo(-470, 1500)
    sh.lineTo(-430, 540)
    sh.cubicTo(-405, 440, -250, 402, -118, 376)
    sh.lineTo(118, 376)
    sh.cubicTo(250, 402, 405, 440, 430, 540)
    sh.lineTo(470, 1500)
    sh.close()
    c.drawPath(sh, P(shader=lin(-300, 380, 300, 700, [C("#5CC2B4"), C("#2A9D8F"), C("#1F7A70")], [0, 0.55, 1])))
    # ---- pescoço
    nk = skia.Path()
    nk.moveTo(-96, 220)
    nk.cubicTo(-90, 300, -100, 350, -116, 392)
    nk.cubicTo(-40, 420, 40, 420, 116, 392)
    nk.cubicTo(100, 350, 90, 300, 96, 220)
    nk.close()
    c.drawPath(nk, P(shader=lin(0, 230, 0, 400, [C("#C48463"), C("#E3A983"), C("#E8B18D")], [0, 0.45, 1])))
    col = skia.Path()
    col.moveTo(-125, 384)
    col.cubicTo(-50, 430, 50, 430, 125, 384)
    c.drawPath(col, P(C("#1C6E65"), stroke=16))
    # ---- orelhas
    for s in (-1, 1):
        c.drawOval(oval(292 * s, -100, 44, 72), P(shader=rad(292 * s, -110, 75, [C(SKIN_M), C(SKIN_D)])))
        c.drawOval(oval(296 * s, -96, 22, 44), P(C("#C9875F", 0.55), blur=4))
    # ---- cabeça
    hp = head_path()
    c.drawPath(hp, P(C("#000000", 0.18), blur=22))
    c.drawPath(hp, P(shader=rad(-70, -170, 560, [C(SKIN_L), C(SKIN_M), C(SKIN_D)], [0, 0.55, 1])))
    c.save()
    c.clipPath(hp, skia.ClipOp.kIntersect, True)
    # sombra do lado direito (luz vindo da esquerda)
    c.drawOval(oval(330, 0, 120, 420), P(C("#B9724F", 0.28), blur=50))
    # bochechas
    for s in (-1, 1):
        c.drawCircle(178 * s, 42, 62, P(C("#F29A86", 0.30), blur=26))
    # oclusão sob o cabelo
    hp2 = catmull(HAIR)
    hp2.offset(0, 22)
    c.drawPath(hp2, P(C("#8A4E33", 0.35), blur=16))
    # brilho na testa e queixo
    c.drawOval(oval(-50, -330, 120, 50), P(C("#FFFFFF", 0.18), blur=24))
    c.drawOval(oval(0, 292, 52, 22), P(C("#FFFFFF", 0.14), blur=10))
    # sombra sob o queixo/mandíbula
    c.restore()
    # luz de recorte azulada (rim light)
    c.save()
    c.clipPath(hp, skia.ClipOp.kIntersect, True)
    c.drawPath(hp, P(C("#BFE6FF", 0.35), stroke=14, blur=6))
    c.restore()
    # ---- cabelo
    hpath = catmull(HAIR)
    c.drawPath(hpath, P(C("#000000", 0.2), blur=10))
    c.drawPath(hpath, P(shader=lin(-200, -520, 200, -150, [C(HAIR_L), C(HAIR_D)])))
    hl = skia.Path()
    hl.moveTo(-200, -430)
    hl.cubicTo(-120, -490, 40, -500, 140, -460)
    c.drawPath(hl, P(C("#FFFFFF", 0.18), stroke=18, blur=6))
    # ---- olhos
    for s in (-1, 1):
        _eye(c, s, blink)
    # ---- nariz
    _nose(c, flare)
    # ---- boca
    _mouth(c)


def _nose(c, flare=1.0):
    # sombras laterais do dorso (luz da esquerda: lado direito mais escuro)
    for s, a in ((-1, 0.22), (1, 0.42)):
        pth = skia.Path()
        pth.moveTo(30 * s, -172)
        pth.cubicTo(38 * s, -100, 48 * s, -40, 64 * s, 8)
        c.drawPath(pth, P(C("#B8744F", a), stroke=20, blur=9))
    c.drawOval(oval(-4, -85, 14, 92), P(C("#FFFFFF", 0.30), blur=8))
    # asas do nariz
    for s in (-1, 1):
        c.drawOval(oval(52 * s, 40, 31, 28), P(shader=rad(46 * s - 6, 30, 34, [C("#F8CBA8"), C("#E4A783")])))
        cr = skia.Path()
        cr.moveTo(66 * s, 8)
        cr.cubicTo(84 * s, 28, 80 * s, 58, 50 * s, 68)
        c.drawPath(cr, P(C("#A9633F", 0.55), stroke=5, blur=1.2))
    # ponta
    c.drawOval(oval(0, 26, 48, 26), P(C("#B9724F", 0.25), blur=10))
    c.drawCircle(0, 20, 41, P(shader=rad(-9, 8, 44, [C("#FCDCC2"), C("#F2BC97"), C("#E6A982")], [0, 0.6, 1])))
    c.drawOval(oval(-7, 4, 13, 9), P(C("#FFFFFF", 0.55), blur=4))
    # narinas (com leve dilatação na respiração)
    for s in (-1, 1):
        c.save()
        c.translate(25 * s, 59)
        c.rotate(18 * s)
        c.drawOval(oval(0, 0, 14.5 * flare, 8.2 * (0.9 + 0.1 * flare)),
                   P(shader=rad(0, 2, 15, [C("#3A1B15"), C("#6B372C")])))
        c.restore()
    c.drawOval(oval(0, 80, 56, 12), P(C("#A8673F", 0.32), blur=7))


def _mouth(c):
    c.drawOval(oval(0, 128, 18, 22), P(C("#B8744F", 0.22), blur=8))  # filtro labial
    up = skia.Path()
    up.moveTo(-72, 162)
    up.cubicTo(-40, 146, -15, 140, 0, 148)
    up.cubicTo(15, 140, 40, 146, 72, 162)
    up.cubicTo(40, 171, -40, 171, -72, 162)
    up.close()
    c.drawPath(up, P(shader=lin(0, 140, 0, 170, [C("#D67A6C"), C("#B95F55")])))
    lo = skia.Path()
    lo.moveTo(-64, 165)
    lo.cubicTo(-36, 203, 36, 203, 64, 165)
    lo.cubicTo(30, 173, -30, 173, -64, 165)
    lo.close()
    c.drawPath(lo, P(shader=lin(0, 166, 0, 200, [C("#E08C80"), C("#CB7266")])))
    c.drawOval(oval(-10, 182, 20, 6), P(C("#FFFFFF", 0.35), blur=3))
    ln = skia.Path()
    ln.moveTo(-74, 160)
    ln.quadTo(0, 175, 74, 160)
    c.drawPath(ln, P(C("#7E352E"), stroke=4.5))
    for s in (-1, 1):
        c.drawCircle(78 * s, 157, 4, P(C("#A65A4A", 0.6), blur=2))
    c.drawOval(oval(0, 214, 40, 10), P(C("#B9724F", 0.22), blur=8))


def face_outlines(c, alpha, color="#8FDBFF"):
    """Contornos tipo raio-x do rosto."""
    if alpha <= 0.01:
        return
    pp = P(C(color, alpha), stroke=4)
    glow = P(C(color, alpha * 0.5), stroke=12, blur=6)
    paths = [head_path(), catmull(HAIR)]
    for s in (-1, 1):
        e = skia.Path()
        cx = 120 * s
        e.moveTo(cx - 50, -150)
        e.cubicTo(cx - 30, -182, cx + 30, -182, cx + 50, -150)
        e.cubicTo(cx + 30, -125, cx - 30, -125, cx - 50, -150)
        paths.append(e)
        n = skia.Path()
        n.moveTo(30 * s, -172)
        n.cubicTo(38 * s, -100, 48 * s, -40, 66 * s, 8)
        n.cubicTo(84 * s, 28, 80 * s, 58, 50 * s, 68)
        paths.append(n)
        paths.append(skia.Path().addOval(oval(25 * s, 59, 14, 8)))
    m = skia.Path()
    m.moveTo(-74, 160)
    m.quadTo(0, 175, 74, 160)
    paths.append(m)
    for p in paths:
        c.drawPath(p, glow)
        c.drawPath(p, pp)


# ======================================================================== CORTE
SLAB = sym([(0, -308), (120, -308), (255, -305), (283, -200), (296, -60), (292, 60), (268, 160),
            (215, 240), (120, 262), (0, 268)])
BONE = sym([(0, -300), (250, -300), (264, -200), (270, -90), (257, 0), (234, 88), (192, 140),
            (150, 152), (0, 152)])
CAV_LAT = [(-30, -268), (-42, -215), (-66, -150), (-96, -80), (-122, -20), (-142, 35), (-146, 85), (-132, 110)]
CAV_L = [(-4, -268)] + CAV_LAT + [(-4, 110)]
SINUS_L = [(-166, -72), (-210, -88), (-252, -70), (-268, -10), (-258, 60), (-224, 100), (-176, 104), (-160, 62), (-158, 0)]
ORBIT = (185, -180, 82)
ETHMOID = [(-68, -248, 12), (-90, -228, 12), (-72, -214, 9), (-93, -196, 10), (-80, -172, 8)]
SEPT_HALF = 9.0

# conchas (lado esquerdo da tela): cx, cy, rx, ry, m_min, m_max
CONCHAS = {
    "sup": (-49, -192, 10, 19, 4.0, 5.0),
    "mid": (-70, -92, 18, 40, 6.0, 11.0),
    "inf": (-108, 30, 30, 50, 7.0, 24.0),
}

# cores
AIR_A, AIR_B = "#E9F6FF", "#C6E6FF"
MUC_A, MUC_B, MUC_SW = "#F6A9B8", "#E9849A", "#DC5B7B"
BONE_A, BONE_B = "#F6EDDD", "#E3D2B5"
MUSCLE = "#D9837A"
FAT = "#F4DA9A"
SKINC = "#EDB592"


def wall_x(y):
    """x (negativo) da parede lateral da cavidade esquerda na altura y."""
    pts = CAV_LAT
    if y <= pts[0][1]:
        return pts[0][0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return lerp(x0, x1, (y - y0) / (y1 - y0))
    return pts[-1][0]


def conc_m(name, s):
    cx, cy, rx, ry, m0, m1 = CONCHAS[name]
    return lerp(m0, m1, s)


def sept_m(y, s):
    base = lerp(5.0, 8.0, s)
    bulge = lerp(4.0, 9.0, s) * math.exp(-((y + 30) / 42) ** 2)  # "swell body" septal
    return base + bulge


def air_bounds(y, s):
    """(lateral, medial) do canal de ar comum do lado esquerdo, para congestão s."""
    lat = wall_x(y) + 4
    for name in ("sup", "mid", "inf"):
        cx, cy, rx, ry, m0, m1 = CONCHAS[name]
        m = lerp(m0, m1, s)
        R = ry + m
        if abs(y - cy) < R:
            lat = max(lat, cx + (rx + m) * math.sqrt(1 - ((y - cy) / R) ** 2))
    med = -(SEPT_HALF + sept_m(y, s))
    return lat, med


def flow_factor(s):
    lat, med = air_bounds(30, s)
    gap = med - lat
    lat0, med0 = air_bounds(30, 0.0)
    return clamp(gap / (med0 - lat0))


def _layer_bands(c, path):
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    c.drawPath(path, P(shader=lin(0, -300, 0, 270, [C("#E59389"), C(MUSCLE), C("#C9726A")])))
    c.drawPath(path, P(C(FAT), stroke=56))
    c.drawPath(path, P(C("#F0C9A0"), stroke=26))
    c.drawPath(path, P(C(SKINC), stroke=18))
    c.restore()


def draw_concha(c, side, name, s, t, hl=0.0, muc_glow=0.0):
    cx, cy, rx, ry, m0, m1 = CONCHAS[name]
    m = lerp(m0, m1, s)
    cx *= -side          # CONCHAS está definido para o lado esquerdo (side = -1)
    # pedículo ósseo até a parede lateral
    ay = cy - ry * 0.55
    ax = wall_x(ay) * -side
    c.drawLine(ax, ay, cx + side * rx * 0.1, cy - ry * 0.45, P(C(mixhex(MUC_B, MUC_SW, s)), stroke=9 + 2 * m * 0.7))
    # mucosa
    col_in = mixhex(MUC_A, "#F08AA2", s)
    col_out = mixhex(MUC_B, MUC_SW, s)
    c.drawOval(oval(cx, cy + 3, rx + m, ry + m), P(C("#9C3B55", 0.18), blur=6))
    c.drawOval(oval(cx, cy, rx + m, ry + m), P(shader=rad(cx - side * 4, cy - ry * 0.3, ry + m,
                                                           [C(col_in), C(col_out)])))
    # vasos (sinusóides venosos) dentro da mucosa
    n = int(12 + 16 * s) if name == "inf" else int(6 + 6 * s)
    rng = np.random.RandomState({"sup": 1, "mid": 2, "inf": 3}[name] * 10 + (7 if side > 0 else 3))
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.15, 0.15)
        f = rng.uniform(0.45, 0.85)
        vx = cx + math.cos(a) * (rx + m) * f
        vy = cy + math.sin(a) * (ry + m) * f
        vr = (1.2 + 2.4 * s + rng.uniform(0, 0.8)) * (1.0 if name == "inf" else 0.7)
        c.drawOval(oval(vx, vy, vr * 1.25, vr), P(C("#B8324F", 0.30 + 0.5 * s)))
    # lâmina óssea curva (concha = osso enrolado coberto de mucosa)
    md = -side  # direção medial
    bp = skia.Path()
    bp.moveTo(cx - md * rx * 0.75, cy - ry * 0.78)
    bp.cubicTo(cx + md * rx * 0.55, cy - ry * 0.55, cx + md * rx * 0.45, cy + ry * 0.35,
               cx + md * rx * 0.05, cy + ry * 0.62)
    bp.quadTo(cx - md * rx * 0.3, cy + ry * 0.8, cx - md * rx * 0.45, cy + ry * 0.55)
    bw = max(3.0, rx * 0.26)
    c.drawPath(bp, P(C(BONE_B), stroke=bw + 3))
    c.drawPath(bp, P(C(BONE_A), stroke=bw))
    if muc_glow > 0:
        c.drawOval(oval(cx, cy, rx + m, ry + m), P(C("#FFFFFF", muc_glow), stroke=4))
    if hl > 0:
        c.drawOval(oval(cx, cy, rx + m + 4, ry + m + 4), P(C(YELLOW, hl * 0.6), stroke=14, blur=5))
        c.drawOval(oval(cx, cy, rx + m + 4, ry + m + 4), P(C(YELLOW, hl), stroke=5))


def septum_path(side, s):
    pts = []
    for y in np.linspace(-262, 106, 40):
        pts.append((side * (SEPT_HALF + sept_m(y, s)), y))
    pts += [(0, 106), (0, -262)]
    return catmull(pts, closed=True, k=0.6)


def draw_section(c, t, sL, sR, opts=None):
    """Desenha o corte. opts: dict com destaques (hl_septo, hl_conchas, hl_mucosa, hl_cav, glow)."""
    o = opts or {}
    slab = catmull(SLAB)
    # sombra no "chão"
    c.drawOval(oval(0, 318, 300, 30), P(C("#2B4A63", 0.25), blur=22))
    # espessura da maquete (extrusão)
    depth = int(34 * o.get("depth", 1.0))
    for k in range(depth, 0, -3):
        sp = skia.Path(slab)
        sp.offset(0, k)
        c.drawPath(sp, P(C(mixhex("#B8796E", "#D59A8C", 1 - k / max(depth, 1)))))
    # face de corte: camadas de tecido
    _layer_bands(c, slab)
    # ossos da face
    bone = catmull(BONE)
    c.drawPath(bone, P(shader=lin(0, -300, 0, 150, [C(BONE_A), C(BONE_B)])))
    # cavidade oral + língua (abaixo do palato)
    oral = catmull(sym([(0, 132), (150, 134), (176, 180), (152, 226), (0, 228)]))
    c.drawPath(oral, P(C("#F2B3B3")))
    tg = skia.Path()
    tg.moveTo(-146, 230)
    tg.cubicTo(-136, 150, 136, 150, 146, 230)
    tg.close()
    c.drawPath(tg, P(shader=lin(0, 160, 0, 230, [C("#EA9393"), C("#D1707A")])))
    c.drawOval(oval(-30, 178, 60, 10), P(C("#FFFFFF", 0.25), blur=6))
    # órbitas (gordura + globo + músculos)
    ox, oy, orr = ORBIT
    for s in (-1, 1):
        x = ox * s
        c.drawCircle(x, oy, orr + 5, P(C(BONE_B)))
        c.drawCircle(x, oy, orr, P(shader=rad(x, oy, orr, [C("#FBE7B4"), C(FAT)])))
        for a in (0, 90, 180, 270):
            ar = math.radians(a)
            c.drawOval(oval(x + math.cos(ar) * 60, oy + math.sin(ar) * 60, 12 if a in (90, 270) else 9,
                            9 if a in (90, 270) else 12), P(C("#D9877F")))
        c.drawCircle(x, oy, 48, P(shader=rad(x - 14, oy - 16, 60, [C("#FFFFFF"), C("#E6ECF1")])))
        c.drawCircle(x, oy, 48, P(C("#C9D3DB"), stroke=2.5))
    # células etmoidais
    for s in (-1, 1):
        for (x, y, r) in ETHMOID:
            c.drawCircle(x * s, y, r, P(C(MUC_A)))
            c.drawCircle(x * s, y, r - 2.5, P(C(AIR_A)))
    # seios maxilares
    for s in (-1, 1):
        sp = catmull(SINUS_L if s < 0 else mirror(SINUS_L))
        c.drawPath(sp, P(shader=lin(0, -90, 0, 100, [C(AIR_A), C(AIR_B)])))
        c.save()
        c.clipPath(sp, skia.ClipOp.kIntersect, True)
        c.drawPath(sp, P(C(MUC_A), stroke=8))
        c.restore()
    # cavidades nasais (ar) com revestimento de mucosa
    hl_cav = o.get("hl_cav", 0.0)
    for s, sv in ((-1, sL), (1, sR)):
        cp = catmull(CAV_L if s < 0 else mirror(CAV_L), k=0.8)
        c.drawPath(cp, P(shader=lin(0, -268, 0, 110, [C(AIR_A), C(AIR_B)])))
        if hl_cav > 0:
            c.drawPath(cp, P(C("#7CC4FF", 0.45 * hl_cav)))
        c.save()
        c.clipPath(cp, skia.ClipOp.kIntersect, True)
        c.drawPath(cp, P(C(mixhex(MUC_A, MUC_B, sv)), stroke=10))
        c.restore()
        if hl_cav > 0:
            c.drawPath(cp, P(C(YELLOW, hl_cav), stroke=5))
    # palato duro (assoalho)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-150, 108, 150, 132), 8, 8), P(C(BONE_B)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-150, 113, 150, 127), 6, 6), P(C(BONE_A)))
    # conchas
    hlc = o.get("hl_conchas", 0.0)
    mg = o.get("hl_mucosa", 0.0)
    for s, sv in ((-1, sL), (1, sR)):
        for name in ("sup", "mid", "inf"):
            draw_concha(c, s, name, sv, t, hl=hlc, muc_glow=mg)
    # septo: mucosa (cada lado) + núcleo de osso/cartilagem
    for s, sv in ((-1, sL), (1, sR)):
        spp = septum_path(s, sv)
        c.drawPath(spp, P(shader=lin(-20 * s, 0, 0, 0, [C(mixhex(MUC_B, MUC_SW, sv)), C(MUC_A)])))
        if mg > 0:
            c.drawPath(spp, P(C("#FFFFFF", mg), stroke=3.5))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-SEPT_HALF, -268, SEPT_HALF, 110), 6, 6),
                P(shader=lin(-9, 0, 9, 0, [C(BONE_B), C(BONE_A), C(BONE_B)])))
    hs = o.get("hl_septo", 0.0)
    if hs > 0:
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-SEPT_HALF - 14, -270, SEPT_HALF + 14, 112), 12, 12)
        c.drawRRect(r, P(C(YELLOW, 0.5 * hs), stroke=16, blur=6))
        c.drawRRect(r, P(C(YELLOW, hs), stroke=5))
    # contorno da placa (realce "maquete")
    gl = o.get("glow", 0.0)
    c.drawPath(slab, P(C("#FFFFFF", 0.35 + 0.5 * gl), stroke=3))
    if gl > 0:
        c.drawPath(slab, P(C("#FFFFFF", 0.5 * gl), stroke=16, blur=8))


# ------------------------------------------------------------------ partículas de ar
_RNG = np.random.RandomState(42)
NP = 38
PARTS = {side: dict(u=_RNG.uniform(-1, 1, NP), ph=_RNG.uniform(0, 1, NP), sp=_RNG.uniform(0.8, 1.25, NP),
                    th=_RNG.uniform(0, 1, NP)) for side in (-1, 1)}


def draw_air(c, t_air, side, s, alpha=1.0, density=1.0, y0=104, y1=-175):
    """Partículas azuis subindo pelo meato comum (entre conchas e septo)."""
    if alpha <= 0.01:
        return
    d = PARTS[side]
    f = flow_factor(s)
    vis = 0.25 + 0.75 * f  # o lado congestionado ainda deixa passar ar (nunca zero)
    for i in range(len(d["u"])):
        if d["th"][i] > vis * density:
            continue
        p = (d["ph"][i] + t_air * 0.32 * d["sp"][i] * (0.75 + 0.5 * f)) % 1.0
        y = lerp(y0, y1, p)
        lat, med = air_bounds(y, s)
        r = 5.6 * (1.15 - 0.45 * p)
        half = (med - lat) / 2 - r - 1.5
        if half <= 0:
            continue
        x = (lat + med) / 2 + d["u"][i] * half
        if side > 0:
            x = -x
        a = alpha * min(1, p / 0.08) * min(1, (1 - p) / 0.15)
        c.drawCircle(x, y + 1.5, r, P(C("#0B2E73", 0.35 * a)))
        c.drawCircle(x, y, r, P(C(AIR_BLUE, a)))
        c.drawCircle(x - r * 0.3, y - r * 0.3, r * 0.35, P(C("#FFFFFF", 0.6 * a)))


def draw_flow_arrows(c, sL, sR, alpha=1.0, t=0.0):
    for side, s in ((-1, sL), (1, sR)):
        f = flow_factor(s)
        lat, med = air_bounds(40, s)
        x = (lat + med) / 2 * (1 if side < 0 else -1)
        w = lerp(9, 22, f)
        bob = 4 * math.sin(t * 4 + side)
        draw_arrow(c, x, 100 + bob, x, lerp(30, -40, f) + bob, w, AIR_BLUE, ow=2.5, alpha=alpha)


# ======================================================================== CAMADA INTERMEDIÁRIA
CART_A, CART_B, CART_LINE = "#E4F2F8", "#BCD9E6", "#8FB4C4"


def draw_bone_plate(c, t, blink=0.0):
    """Camada abaixo da pele, no estilo maquete: ossos da face (creme) e cartilagens
    do nariz (azul-claras), olhos mantidos para não ficar assustador."""
    hp = head_path()
    c.drawPath(hp, P(C("#000000", 0.18), blur=18))
    c.drawPath(hp, P(shader=rad(-60, -170, 560, [C("#FBF5EA"), C(BONE_A), C(BONE_B)], [0, 0.5, 1])))
    c.save()
    c.clipPath(hp, skia.ClipOp.kIntersect, True)
    c.drawOval(oval(330, 0, 120, 420), P(C("#A88B62", 0.25), blur=50))
    # músculos visíveis em volta da boca e nas bochechas (tons suaves, sem sangue)
    c.drawOval(oval(0, 165, 96, 58), P(shader=rad(0, 165, 96, [C("#E79A90"), C("#D07A72")])))
    for k in range(18):
        a = 2 * math.pi * k / 18
        c.drawLine(math.cos(a) * 40, 165 + math.sin(a) * 24, math.cos(a) * 92, 165 + math.sin(a) * 54,
                   P(C("#B9625C", 0.45), stroke=2))
    c.drawOval(oval(0, 165, 42, 14), P(C("#C46B66")))
    for s in (-1, 1):
        mp = skia.Path()
        mp.moveTo(200 * s, -60)
        mp.cubicTo(170 * s, 20, 120 * s, 80, 80 * s, 130)
        c.drawPath(mp, P(C("#E3A096", 0.55), stroke=24, blur=2))
        c.drawPath(mp, P(C("#C9746D", 0.25), stroke=2))
    c.restore()
    # maçãs do rosto (zigomático) e arco das sobrancelhas
    for s in (-1, 1):
        c.drawOval(oval(190 * s, -40, 70, 40), P(C("#FFFFFF", 0.35), blur=18))
        br = skia.Path()
        br.moveTo(50 * s, -228)
        br.quadTo(120 * s, -258, 200 * s, -215)
        c.drawPath(br, P(C("#FFFFFF", 0.4), stroke=16, blur=6))
    # órbitas com os olhos
    for s in (-1, 1):
        x, y = 120 * s, -150
        c.drawCircle(x, y, 70, P(shader=rad(x, y, 70, [C("#B89A73"), C("#D9C3A0")], [0.6, 1])))
        c.drawCircle(x, y, 70, P(C("#C2A67E"), stroke=3))
        c.drawCircle(x, y + 2, 47, P(C("#000000", 0.25), blur=6))
        c.drawCircle(x, y, 46, P(shader=rad(x - 14, y - 16, 62, [C("#FFFFFF"), C("#E3E9EE")])))
        c.drawCircle(x, y, 25, P(shader=rad(x, y, 25, [C("#8A5A3A"), C("#5B3A26"), C("#2E1C12")], [0, 0.6, 1])))
        c.drawCircle(x, y, 11, P(C("#0E0A08")))
        c.drawCircle(x - 9, y - 9, 6, P(C("#FFFFFF", 0.95)))
        if blink > 0:
            c.drawRect(skia.Rect.MakeLTRB(x - 48, y - 48, x + 48, y - 48 + 96 * blink), P(C(BONE_B)))
    # abertura piriforme (atrás das cartilagens)
    pir = catmull(sym([(0, -70), (40, -64), (66, -10), (72, 50), (48, 86), (0, 92)]))
    c.drawPath(pir, P(shader=rad(0, 20, 90, [C("#8E5F5A"), C("#B78079")])))
    # ossos nasais
    for s in (-1, 1):
        nb = catmull([(3 * s, -200), (22 * s, -196), (44 * s, -80), (36 * s, -62), (3 * s, -66)], k=0.7)
        c.drawPath(nb, P(shader=lin(0, -200, 0, -60, [C("#F7EFE2"), C(BONE_B)])))
        c.drawPath(nb, P(C("#C2A67E"), stroke=2.5))
    # cartilagens: septal (centro), laterais e alares
    sept = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-8, -66, 8, 52), 6, 6)
    c.drawRRect(sept, P(C(CART_B)))
    for s in (-1, 1):
        lat = catmull([(6 * s, -64), (38 * s, -70), (58 * s, -12), (46 * s, 10), (8 * s, 6)], k=0.7)
        c.drawPath(lat, P(shader=lin(0, -70, 0, 10, [C(CART_A), C(CART_B)])))
        c.drawPath(lat, P(C(CART_LINE), stroke=2.5))
        c.drawOval(oval(34 * s, 38, 34, 28), P(shader=rad(28 * s, 28, 36, [C(CART_A), C(CART_B)])))
        c.drawOval(oval(34 * s, 38, 34, 28), P(C(CART_LINE), stroke=2.5))
    c.drawCircle(0, 18, 26, P(shader=rad(-6, 10, 28, [C("#F2FAFD"), C(CART_B)])))
    c.drawCircle(0, 18, 26, P(C(CART_LINE), stroke=2.5))
    for s in (-1, 1):
        c.save()
        c.translate(25 * s, 59)
        c.rotate(18 * s)
        c.drawOval(oval(0, 0, 14, 8), P(C("#6B3B36")))
        c.restore()
    c.drawPath(hp, P(C("#FFFFFF", 0.5), stroke=4))
