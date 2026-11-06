# -*- coding: utf-8 -*-
"""Composição de cada quadro do vídeo (função pura do tempo t)."""
import math
import numpy as np
import skia
from gfx import *
from anatomy import (draw_face, face_outlines, draw_section, draw_air, draw_flow_arrows, flow_factor,
                     CONCHAS, air_bounds)
from timeline import T, WORDS, DURATION

FPS = 30
ANCHOR = (540.0, 820.0)

# ------------------------------------------------------------------ câmera
CAM_KEYS = [
    (0.0, 0, -75, 1.00),
    (0.6, 0, -75, 1.00),
    (2.2, 0, 22, 1.72),
    (T["scan"] - 0.25, 0, 25, 1.90),
    (T["scan"] + 0.55, 0, -30, 1.42),
    (T["lift"] + 0.15, 0, -40, 1.50),
    (T["section"] + 0.5, 0, -60, 1.62),
    (T["septo"] - 0.2, 0, -60, 1.70),
    (T["septo"] + 0.35, 0, -75, 2.05),
    (T["conchas"] - 0.25, 0, -60, 1.92),
    (T["conchas"] + 0.45, -40, -40, 2.02),
    (T["mucosa"] + 0.45, -30, -20, 2.08),
    (T["vasos"] + 0.4, -15, -20, 1.90),
    (T["curioso"] + 0.2, 0, -20, 1.82),
    (T["enchem"] - 0.25, 0, 0, 1.95),
    (T["desincha"], 0, 0, 1.95),
    (T["horas"], 0, 5, 1.80),
    (T["ciclo"], 0, 5, 1.80),
    (T["resumo"] + 0.8, 0, -5, 1.80),
    (T["aviso"] - 0.25, 0, -5, 1.85),
    (T["aviso"] + 0.75, 0, -40, 1.00),
    (T["cta"], 0, -40, 1.02),
    (DURATION, 0, -30, 1.12),
]


class Cam:
    def __init__(self, cx, cy, z):
        self.cx, self.cy, self.z = cx, cy, z

    def s(self, x, y):
        return ANCHOR[0] + (x - self.cx) * self.z, ANCHOR[1] + (y - self.cy) * self.z

    def apply(self, c):
        c.translate(*ANCHOR)
        c.scale(self.z, self.z)
        c.translate(-self.cx, -self.cy)


def camera(t):
    k = CAM_KEYS
    if t <= k[0][0]:
        _, cx, cy, z = k[0]
    elif t >= k[-1][0]:
        _, cx, cy, z = k[-1]
    else:
        for a, b in zip(k, k[1:]):
            if a[0] <= t <= b[0]:
                e = ease(prog(t, a[0], b[0]))
                cx, cy = lerp(a[1], b[1], e), lerp(a[2], b[2], e)
                z = math.exp(lerp(math.log(a[3]), math.log(b[3]), e))
                break
    # leve flutuação de câmera "na mão"
    cx += 3.0 * math.sin(t * 0.7)
    cy += 2.5 * math.sin(t * 0.93 + 1.0)
    z *= 1 + 0.006 * math.sin(t * 0.5)
    return Cam(cx, cy, z)


# ------------------------------------------------------------------ estado do ciclo
def congestion(t):
    """(sL, sR): congestão da mucosa 0..1 em cada lado (tela)."""
    if t >= T["resumo"]:
        sL = 0.35 + 0.65 * sm(t, T["r_incha"], T["r_incha"] + 0.6)
        sR = 0.35 - 0.35 * sm(t, T["r_desincha"], T["r_desincha"] + 0.6)
        sw = sm(t, T["r_trocam"] - 0.1, T["r_trocam"] + 0.8)
        return lerp(sL, 0.0, sw), lerp(sR, 1.0, sw)
    sL = 0.35 + 0.65 * sm(t, T["enchem"], T["incha"] + 0.5)
    sR = 0.35 - 0.35 * sm(t, T["desincha"] - 0.1, T["desincha"] + 0.9)
    sw = sm(t, T["horas"] + 0.5, T["inverter"] + 0.3)
    return lerp(sL, 0.0, sw), lerp(sR, 1.0, sw)


def air_time(t):
    """Tempo das partículas (acelera durante o avanço rápido)."""
    t0, t1 = T["horas"], T["inverter"] + 0.4
    if t < t0:
        return t
    if t < t1:
        return t0 + (t - t0) * 4.0
    return t0 + (t1 - t0) * 4.0 + (t - t1)


# ------------------------------------------------------------------ fundo
_BR = np.random.RandomState(7)
BOKEH = [(_BR.uniform(0, 1080), _BR.uniform(0, 1920), _BR.uniform(30, 130), _BR.uniform(0.06, 0.18),
          _BR.uniform(0, 6.28)) for _ in range(16)]


def draw_bg(c, t, cam):
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [C("#F1F8FC"), C("#DCEBF4"), C("#BFD7E6")],
                                                    [0, 0.5, 1])))
    c.drawCircle(540, 760, 820, P(shader=rad(540, 760, 820, [C("#FFFFFF", 0.65), C("#FFFFFF", 0.0)])))
    px, py = -(cam.cx) * 0.25, -(cam.cy) * 0.25
    for (x, y, r, a, ph) in BOKEH:
        yy = (y - t * 10 + py) % 2100 - 90
        xx = x + 18 * math.sin(t * 0.3 + ph) + px
        c.drawCircle(xx, yy, r * (0.9 + 0.1 * cam.z), P(C("#FFFFFF", a), blur=10))
    # piso sutil
    c.drawRect(skia.Rect.MakeLTRB(0, 1560, W, H), P(shader=lin(0, 1560, 0, H, [C("#A9C6D8", 0.0), C("#A9C6D8", 0.45)])))


def vignette(c):
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(540, 900, 1250, [C("#000000", 0.0), C("#000000", 0.0),
                                                                     C("#0B1E2E", 0.28)], [0, 0.62, 1])))


# ------------------------------------------------------------------ legendas
def _norm_caption(w):
    return w.strip(",.:;!")


def build_caption_groups():
    groups, cur = [], []
    for w in WORDS:
        cur.append(w)
        txt = " ".join(x["text"] for x in cur)
        short = len(_norm_caption(w["text"])) <= 3 and not w["brk"]
        if w["brk"] or len(cur) >= 2 or (len(txt) >= 10 and not short):
            if short and len(cur) < 2 and not w["brk"]:
                continue
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        st = g[0]["start"]
        en = g[-1]["end"] + 0.12
        if i + 1 < len(groups):
            nxt = groups[i + 1][0]["start"]
            if nxt - en < 0.35:
                en = nxt
        out.append((st, en, [(_norm_caption(x["text"]), x["hl"]) for x in g]))
    return out


CAPTIONS = build_caption_groups()


def draw_captions(c, t):
    for st, en, words in CAPTIONS:
        if st - 0.02 <= t < en:
            k = prog(t, st - 0.02, st + 0.12)
            sc = lerp(0.78, 1.0, eback(k))
            a = min(1.0, k * 3)
            parts = [(w, YELLOW if hl else "#FFFFFF") for w, hl in words]
            rich_line(c, parts, 540, 1470, 88, stroke=17, alpha=a, scale=sc)
            break


# ------------------------------------------------------------------ títulos
def title(c, lines, y, size, t, t0, t1, fo=0.25, gap=1.12):
    a = window(t, t0, t1, fi=0.18, fo=fo)
    if a <= 0:
        return
    sc = lerp(0.6, 1.0, eback(prog(t, t0, t0 + 0.3)))
    for i, parts in enumerate(lines):
        rich_line(c, parts, 540, y + i * size * gap, size, alpha=a, scale=sc, stroke=size * 0.19)


def label(c, txt, pos, t, t0, t1, dot=AIR_BLUE, anchor=None, anchors=None, size=34):
    a = window(t, t0, t1, fi=0.2, fo=0.25)
    if a <= 0:
        return
    sc = lerp(0.5, 1.0, eback(prog(t, t0, t0 + 0.28)))
    pill_label(c, txt, pos[0], pos[1], alpha=a, scale=sc, dot=dot, anchor=anchor, anchors=anchors, size=size)


# ------------------------------------------------------------------ partes do quadro
BLINKS = [1.3, 4.3, 49.6, 52.9, 55.6, 58.7]


def blink_amt(t):
    for b in BLINKS:
        if b <= t <= b + 0.18:
            return math.sin(math.pi * (t - b) / 0.18)
    return 0.0


def face_layer(c, t, cam):
    """Rosto com os estados: normal, varredura raio-x, separação da camada e retorno."""
    flare = 1.0 + 0.08 * math.sin(t * 2 * math.pi / 3.6)
    scan_p = prog(t, T["scan"], T["xray"] + 0.3)
    lift = sm(t, T["lift"], T["lift"] + 1.1)
    back = sm(t, T["aviso"] - 0.25, T["aviso"] + 0.55)
    if t >= T["aviso"] - 0.25:
        lift = 1 - back
        ghost = 1 - sm(t, T["aviso"] + 0.3, T["aviso"] + 0.9)
        scan_y = None
    else:
        ghost = 1.0 if scan_p >= 1 else 0.0
        scan_y = lerp(-540, 380, ease(scan_p)) if 0 < scan_p < 1 else None
    if lift >= 0.999:
        return
    blink = blink_amt(t)

    def normal():
        draw_face(c, t, blink=blink, flare=flare)

    def xray(alpha_face):
        c.saveLayer(None, P(alpha=0.32 * alpha_face))
        draw_face(c, t, blink=blink, flare=flare)
        c.restore()
        face_outlines(c, 0.9 * alpha_face)

    c.save()
    # transformação de "afastar a camada de pele"
    c.translate(0, -40)
    c.scale(1 + 0.35 * lift, 1 + 0.35 * lift)
    c.translate(0, 40 - 70 * lift)
    la = 1 - lift
    if scan_y is not None:
        # parte de baixo: normal; parte de cima: raio-x
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(-2000, scan_y, 2000, 3000))
        normal()
        c.restore()
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(-2000, -3000, 2000, scan_y))
        xray(1.0)
        c.restore()
        c.drawRect(skia.Rect.MakeLTRB(-420, scan_y - 4, 420, scan_y + 4), P(C("#7FDBFF", 0.9)))
        c.drawRect(skia.Rect.MakeLTRB(-420, scan_y - 30, 420, scan_y + 2), P(shader=lin(0, scan_y - 60, 0, scan_y,
                   [C("#7FDBFF", 0.0), C("#7FDBFF", 0.45)])))
        c.drawRect(skia.Rect.MakeLTRB(-420, scan_y - 10, 420, scan_y + 10), P(C("#BFF0FF", 0.6), blur=10))
    elif ghost >= 0.999:
        c.saveLayer(None, P(alpha=la))
        xray(1.0)
        c.restore()
    elif ghost <= 0.001:
        c.saveLayer(None, P(alpha=la))
        normal()
        c.restore()
    else:
        c.saveLayer(None, P(alpha=la))
        c.saveLayer(None, P(alpha=1 - ghost))
        normal()
        c.restore()
        xray(ghost)
        c.restore()
    c.restore()


def section_opts(t):
    return dict(
        hl_cav=window(t, T["cavidades"], T["septo"] - 0.4, fi=0.2, fo=0.3) * (0.75 + 0.25 * math.sin(t * 8)),
        hl_septo=window(t, T["septo"] - 0.05, T["conchas"] - 0.4, fi=0.15, fo=0.3),
        hl_conchas=window(t, T["conchas"], T["mucosa"] - 0.35, fi=0.15, fo=0.3),
        hl_mucosa=window(t, T["mucosa"], T["vasos"] + 0.2, fi=0.15, fo=0.3) * (0.6 + 0.4 * math.sin(t * 9)),
        glow=window(t, T["lift"] + 0.5, T["section"] + 0.2, fi=0.3, fo=0.5),
    )


def draw_inset(c, t, cam, sL):
    """Lupa mostrando os vasos (sinusóides venosos) dentro da mucosa da concha inferior."""
    a = window(t, T["vasos"] - 0.25, T["estreita"] - 0.2, fi=0.3, fo=0.3)
    if a <= 0.01:
        return
    sc = lerp(0.3, 1.0, eback(prog(t, T["vasos"] - 0.25, T["vasos"] + 0.2)))
    cx, cy, R = 300.0, 470.0, 165.0
    src = cam.s(-82, 22)
    # conectores da lupa
    dx, dy = cx - src[0], cy - src[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    c.saveLayer(None, P(alpha=a))
    for sgn in (-1, 1):
        x1, y1 = cx + nx * R * sc * sgn, cy + ny * R * sc * sgn
        x0, y0 = src[0] + nx * 26 * sgn, src[1] + ny * 26 * sgn
        c.drawLine(x0, y0, x1, y1, P(C("#1C1C1C", 0.6), stroke=6))
        c.drawLine(x0, y0, x1, y1, P(C("#FFFFFF"), stroke=3))
    c.drawCircle(src[0], src[1], 28, P(C("#1C1C1C"), stroke=7))
    c.drawCircle(src[0], src[1], 28, P(C("#FFFFFF"), stroke=4))
    c.save()
    c.translate(cx, cy)
    c.scale(sc, sc)
    clip = skia.Path()
    clip.addCircle(0, 0, R)
    c.drawCircle(0, 8, R + 6, P(C("#000000", 0.3), blur=12))
    c.save()
    c.clipPath(clip, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(-R, -R, R, R), P(shader=lin(0, -R, 0, R, [C("#F7B9C4"), C("#EE97A8")])))
    # ar (lado da cavidade) + epitélio com cílios
    c.drawRect(skia.Rect.MakeLTRB(-R, -R, R, -R * 0.52), P(shader=lin(0, -R, 0, -R * 0.5, [C("#E9F6FF"), C("#CBE8FF")])))
    for k in range(-8, 9):
        x = k * 21.0
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 9.5, -R * 0.52, x + 9.5, -R * 0.52 + 42), 6, 6),
                    P(C("#FAD1D9")))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 9.5, -R * 0.52, x + 9.5, -R * 0.52 + 42), 6, 6),
                    P(C("#E58FA3"), stroke=2))
        c.drawCircle(x, -R * 0.52 + 26, 4.5, P(C("#B5638A")))
        for j in (-5, 0, 5):
            sway = 3 * math.sin(t * 9 + k * 0.7)
            c.drawLine(x + j, -R * 0.52, x + j + sway, -R * 0.52 - 11, P(C("#E58FA3"), stroke=1.6))
    # sinusóides venosos que se dilatam com a congestão
    k = 0.55 + 0.75 * sL
    vessels = [(-80, 18, 34, 20), (30, 8, 38, 22), (-20, 88, 40, 20), (95, 82, 30, 18), (-110, 100, 24, 15)]
    rng = np.random.RandomState(5)
    for (vx, vy, rx, ry) in vessels:
        rr = oval(vx, vy, rx * k, ry * k)
        c.drawOval(rr, P(C("#8E2340", 0.35), blur=4))
        c.drawOval(rr, P(shader=rad(vx, vy - 4, rx * k, [C("#F07C8E"), C("#D9506B")])))
        c.drawOval(rr, P(C("#A3304C"), stroke=3))
        n = int(4 + 6 * sL)
        for j in range(n):
            ph = rng.uniform(0, 6.28)
            ang = ph + t * 1.4
            px = vx + math.cos(ang) * rx * k * 0.55
            py = vy + math.sin(ang) * ry * k * 0.45
            c.drawOval(oval(px, py, 6, 4.2), P(C("#B3203F")))
            c.drawOval(oval(px - 1, py - 1, 2.6, 1.6), P(C("#E8798C")))
    c.restore()
    c.drawCircle(0, 0, R, P(C("#1C1C1C"), stroke=10))
    c.drawCircle(0, 0, R, P(C("#FFFFFF"), stroke=5))
    c.restore()
    c.restore()
    label(c, "VASOS SANGUÍNEOS", (cx, cy + R + 36), t, T["vasos"], T["estreita"] - 0.2, dot="#D9506B", size=31)


def main_section(c, t, cam, alpha=1.0, extra=True):
    """Corte + ar + setas, desenhado com a câmera aplicada."""
    sL, sR = congestion(t)
    c.saveLayer(None, P(alpha=alpha))
    c.save()
    cam.apply(c)
    draw_section(c, t, sL, sR, section_opts(t))
    ta = air_time(t)
    air_a = sm(t, T["section"] - 0.3, T["section"] + 0.5)
    draw_air(c, ta, -1, sL, alpha=air_a)
    draw_air(c, ta, 1, sR, alpha=air_a)
    arr_a = window(t, T["estreita"] - 0.15, T["ciclo"] - 0.1, fi=0.3, fo=0.3) + \
        window(t, T["r_incha"], T["aviso"] - 0.3, fi=0.3, fo=0.3)
    if arr_a > 0:
        draw_flow_arrows(c, sL, sR, alpha=min(1, arr_a), t=t)
    c.restore()
    c.restore()


def section_labels(c, t, cam):
    sL, sR = congestion(t)
    label(c, "CAVIDADES NASAIS", (540, 300), t, T["cavidades"], T["septo"] - 0.3, dot=AIR_BLUE,
          anchors=[cam.s(-78, -60), cam.s(78, -60)])
    label(c, "SEPTO", (540, 300), t, T["septo"], T["conchas"] - 0.3, dot=YELLOW, anchor=cam.s(0, -150))
    label(c, "CONCHAS NASAIS", (300, 1290), t, T["conchas"], T["mucosa"] - 0.25, dot="#E9849A",
          anchors=[cam.s(-108, 60), cam.s(-74, -60)])
    mL = CONCHAS["inf"]
    label(c, "MUCOSA", (250, 330), t, T["mucosa"], T["vasos"] - 0.3, dot="#E9849A",
          anchors=[cam.s(-90 + 18, -10), cam.s(-16, -120)])
    # MAIS / MENOS AR
    lat, med = air_bounds(60, sL)
    pl = cam.s((lat + med) / 2, 85)
    lat2, med2 = air_bounds(60, sR)
    pr = cam.s(-(lat2 + med2) / 2, 85)
    sw_t = T["inverter"] - 0.2
    label(c, "MENOS AR", (230, 1300), t, T["estreita"], sw_t, dot="#E9849A", anchor=pl)
    label(c, "MAIS AR", (850, 1300), t, T["facilidade"], sw_t, dot=AIR_BLUE, anchor=pr)
    label(c, "MAIS AR", (230, 1300), t, sw_t + 0.35, T["ciclo"] - 0.2, dot=AIR_BLUE, anchor=pl)
    label(c, "MENOS AR", (850, 1300), t, sw_t + 0.35, T["ciclo"] - 0.2, dot="#E9849A", anchor=pr)
    # resumo
    if t >= T["resumo"]:
        label(c, "MENOS AR", (230, 1300), t, T["r_incha"] + 0.3, T["r_trocam"] - 0.05, dot="#E9849A", anchor=pl)
        label(c, "MAIS AR", (850, 1300), t, T["r_desincha"] + 0.3, T["r_trocam"] - 0.05, dot=AIR_BLUE, anchor=pr)
        label(c, "MAIS AR", (230, 1300), t, T["r_trocam"] + 0.45, T["aviso"] - 0.4, dot=AIR_BLUE, anchor=pl)
        label(c, "MENOS AR", (850, 1300), t, T["r_trocam"] + 0.45, T["aviso"] - 0.4, dot="#E9849A", anchor=pr)


def hook_air(c, t, cam):
    """Setas e partículas de ar entrando pelas narinas (rosto)."""
    a_hook = window(t, 0.7, T["scan"] - 0.1, fi=0.35, fo=0.3)
    a_cta = window(t, T["cta"] + 0.2, DURATION + 1, fi=0.4)
    a = max(a_hook, a_cta)
    if a <= 0.01:
        return
    c.save()
    cam.apply(c)
    for s in (-1, 1):
        if a_cta > a_hook:
            ph = 0.5 + 0.5 * math.sin(t * 1.6 + (0 if s < 0 else math.pi))
            f = 0.45 + 0.55 * ph
        else:
            f = 0.12 if s < 0 else 1.0
        n = int(10 + 16 * f)
        rng = np.random.RandomState(11 if s < 0 else 23)
        for i in range(n):
            ph = rng.uniform(0, 1)
            u = rng.uniform(-1, 1)
            p = (ph + t * 0.55) % 1.0
            y = lerp(250, 66, p)
            x = 25 * s + u * 30 * (1 - p) * f
            r = 6.0 * (1.1 - 0.5 * p)
            aa = a * min(1, p / 0.1) * min(1, (1 - p) / 0.2)
            c.drawCircle(x, y, r, P(C(AIR_BLUE, aa)))
            c.drawCircle(x - r * 0.3, y - r * 0.3, r * 0.35, P(C("#FFFFFF", 0.6 * aa)))
        w = lerp(9, 22, f) * lerp(0.3, 1.0, eback(prog(t, 0.7, 1.1)))
        bob = 5 * math.sin(t * 5 + s)
        draw_arrow(c, 25 * s, 215 + bob, 25 * s, 96 + bob, w, AIR_BLUE, ow=2.6, alpha=a)
    c.restore()
    label(c, "NARINA", (250, 1110), t, T["narina"] - 0.05, T["scan"] - 0.1, dot=AIR_BLUE, anchor=cam.s(-25, 64))
    label(c, "FLUXO DE AR", (830, 1150), t, T["melhor"] - 0.05, T["scan"] - 0.1, dot=AIR_BLUE, anchor=cam.s(25, 170))


def cycle_cards(c, t):
    """Cena 'ciclo nasal': dois estados lado a lado + sistema nervoso + fluxo total."""
    t0, t1 = T["ciclo"] - 0.1, T["resumo"] + 0.05
    if not (t0 <= t <= t1 + 0.01):
        return
    ap = eback(prog(t, t0, t0 + 0.45))
    cards = [(280, 820, (1.0, 0.0), "AGORA"), (800, 820, (0.0, 1.0), "HORAS DEPOIS")]
    cw, ch = 440, 560
    for i, (x, y, (sl, sr), head) in enumerate(cards):
        d = prog(t, t0 + 0.12 * i, t0 + 0.12 * i + 0.45)
        sc = lerp(0.4, 1.0, eback(d))
        a = min(1.0, d * 2.5)
        if a <= 0:
            continue
        c.saveLayer(None, P(alpha=a))
        c.save()
        c.translate(x, y)
        c.scale(sc, sc)
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-cw / 2, -ch / 2, cw, ch), 34, 34)
        c.drawRRect(rr, P(C("#0B2238", 0.35), blur=16))
        c.drawRRect(rr, P(shader=lin(0, -ch / 2, 0, ch / 2, [C("#FFFFFF"), C("#E6F1F8")])))
        c.save()
        c.clipRRect(rr, skia.ClipOp.kIntersect, True)
        c.save()
        c.scale(1.32, 1.32)
        c.translate(0, 55)
        draw_section(c, t, sl, sr, {})
        draw_air(c, air_time(t), -1, sl)
        draw_air(c, air_time(t), 1, sr)
        draw_flow_arrows(c, sl, sr, t=t)
        c.restore()
        c.restore()
        c.drawRRect(rr, P(C("#1A1A1A"), stroke=7))
        c.restore()
        c.restore()
        pill_label(c, head, x, y - ch / 2 * sc - 6, alpha=a, scale=sc, dot=YELLOW if i else AIR_BLUE, size=30)
    # ícone de ciclo entre os cards
    icon_cycle(c, 540, 820, 54 * ap, t, alpha=min(1, ap))
    # título
    title(c, [[("CICLO", YELLOW), ("NASAL", YELLOW)]], 300, 92, t, T["ciclo_word"] - 0.05, t1, fo=0.2)
    # sistema nervoso (controle automático)
    a_ns = window(t, T["sistema"] - 0.05, t1, fi=0.3, fo=0.2)
    if a_ns > 0:
        for x in (280, 800):
            path = skia.Path()
            path.moveTo(540, 420)
            path.cubicTo(540, 470, x, 470, x, 525)
            pe = P(C(YELLOW, a_ns), stroke=8)
            pe.setPathEffect(skia.DashPathEffect.Make([22, 16], -t * 90))
            c.drawPath(path, P(C("#3A2A00", 0.6 * a_ns), stroke=13))
            c.drawPath(path, pe)
        label(c, "SISTEMA NERVOSO", (540, 410), t, T["sistema"] - 0.05, t1, dot=YELLOW, size=32)
    # fluxo total semelhante
    a_c = window(t, T["compensa"] - 0.1, t1, fi=0.3, fo=0.2)
    if a_c > 0:
        for i, (x, y, (sl, sr), _) in enumerate(cards):
            fl, fr = 0.25 + 0.75 * flow_factor(sl), 0.25 + 0.75 * flow_factor(sr)
            g = eout(prog(t, T["compensa"] - 0.1 + 0.15 * i, T["compensa"] + 0.5 + 0.15 * i))
            bw, bh = 380, 40
            bx, by = x - bw / 2, 1148
            wl = bw * fl / (fl + fr) * g
            wr = bw * fr / (fl + fr) * g
            c.saveLayer(None, P(alpha=a_c))
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, by, bw, bh), 20, 20)
            c.drawRRect(rr, P(C("#FFFFFF", 0.8)))
            c.save()
            c.clipRRect(rr, skia.ClipOp.kIntersect, True)
            c.drawRect(skia.Rect.MakeXYWH(bx, by, wl, bh), P(C("#2F6FEB")))
            c.drawRect(skia.Rect.MakeXYWH(bx + wl, by, wr, bh), P(C("#8EC1FF")))
            c.drawLine(bx + wl, by, bx + wl, by + bh, P(C("#FFFFFF"), stroke=4))
            c.restore()
            c.drawRRect(rr, P(C("#1A1A1A"), stroke=5))
            c.restore()
        label(c, "FLUXO TOTAL SEMELHANTE", (540, 1252), t, T["compensa"] + 0.15, t1, dot=AIR_BLUE, size=32)


def warning_card(c, t):
    a = window(t, T["aviso"] + 0.2, T["cta"] - 0.25, fi=0.3, fo=0.3)
    if a <= 0:
        return
    sc = lerp(0.5, 1.0, eback(prog(t, T["aviso"] + 0.2, T["aviso"] + 0.55)))
    c.saveLayer(None, P(alpha=a))
    c.save()
    c.translate(540, 300)
    c.scale(sc, sc)
    w, h = 940, 250
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), 36, 36)
    c.drawRRect(rr, P(C("#0B2238", 0.35), blur=16))
    c.drawRRect(rr, P(C("#FFFFFF")))
    c.save()
    c.clipRRect(rr, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, 22, h), P(C("#FFC300")))
    c.restore()
    c.drawRRect(rr, P(C("#1A1A1A"), stroke=6))
    pulse = 1 + 0.06 * math.sin(t * 6)
    icon_warning(c, -w / 2 + 120, 0, 1.25 * pulse)
    fb = font(TF_BLACK, 50)
    fx = font(TF_XB, 38)
    x0 = -w / 2 + 215
    c.drawString("ATENÇÃO", x0, -50, fb, P(C("#E85D04")))
    c.drawString("Entupimento persistente", x0, 8, fx, P(C(INK)))
    c.drawString("ou intenso? Procure um", x0, 56, fx, P(C(INK)))
    c.drawString("profissional de saúde.", x0, 104, fx, P(C(INK)))
    c.restore()
    c.restore()


def rewind_fx(c, t):
    """Efeito de retrocesso: linhas de varredura e ícone."""
    p = prog(t, T["resumo"] - 0.05, T["resumo"] + 0.8)
    if p <= 0 or p >= 1:
        return
    a = math.sin(math.pi * p)
    c.drawRect(skia.Rect.MakeWH(W, H), P(C("#0A1A33", 0.22 * a)))
    rng = np.random.RandomState(int(t * 30))
    for _ in range(9):
        y = rng.uniform(0, H)
        hh = rng.uniform(3, 14)
        c.drawRect(skia.Rect.MakeLTRB(0, y, W, y + hh), P(C("#FFFFFF", 0.18 * a)))
    icon_rewind(c, 500, 830, 1.5 * lerp(0.6, 1.0, eback(prog(t, T["resumo"] - 0.05, T["resumo"] + 0.25))), alpha=a)


def resumo_steps(c, t):
    steps = [(T["r_incha"], "UM LADO INCHA", "#E9849A"),
             (T["r_desincha"], "O OUTRO DESINCHA", AIR_BLUE),
             (T["r_trocam"], "DEPOIS ELES TROCAM", YELLOW)]
    end = T["aviso"] - 0.35
    for i, (st, txt, dot) in enumerate(steps):
        en = steps[i + 1][0] - 0.05 if i + 1 < len(steps) else end
        a = window(t, st - 0.05, en, fi=0.18, fo=0.15)
        if a <= 0:
            continue
        sc = lerp(0.5, 1.0, eback(prog(t, st - 0.05, st + 0.25)))
        # número
        x = 540
        f = font(TF_XB, 40)
        tw = text_w(txt, f)
        c.saveLayer(None, P(alpha=a))
        c.save()
        c.translate(x, 196)
        c.scale(sc, sc)
        wt = tw + 150
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-wt / 2, -40, wt, 80), 40, 40)
        c.drawRRect(rr, P(C("#000000", 0.25), blur=8))
        c.drawRRect(rr, P(C("#FFFFFF")))
        c.drawRRect(rr, P(C("#1A1A1A"), stroke=5))
        c.drawCircle(-wt / 2 + 42, 0, 28, P(C(YELLOW)))
        c.drawCircle(-wt / 2 + 42, 0, 28, P(C("#1A1A1A"), stroke=4))
        fn = font(TF_BLACK, 36)
        n = str(i + 1)
        c.drawString(n, -wt / 2 + 42 - text_w(n, fn) / 2, 13, fn, P(C(INK)))
        c.drawString(txt, -wt / 2 + 90, 14, f, P(C(INK)))
        c.restore()
        c.restore()
    # bolinhas de progresso
    a = window(t, T["r_incha"] - 0.1, end, fi=0.2, fo=0.15)
    if a > 0:
        for i, (st, _, _) in enumerate(steps):
            on = t >= st
            c.drawCircle(500 + i * 40, 262, 9, P(C(YELLOW if on else "#FFFFFF", a)))
            c.drawCircle(500 + i * 40, 262, 9, P(C("#1A1A1A", a), stroke=3))


# ------------------------------------------------------------------ quadro
def compose(c, t):
    cam = camera(t)
    draw_bg(c, t, cam)

    in_cards = T["ciclo"] - 0.1 <= t < T["resumo"] - 0.05
    rewinding = T["resumo"] - 0.05 <= t < T["resumo"] + 0.8

    # ----- corte anatômico (por trás do rosto)
    sec_a = sm(t, T["scan"], T["scan"] + 0.35)
    if t > T["aviso"] + 0.55:
        sec_a *= 1 - sm(t, T["aviso"] + 0.55, T["aviso"] + 0.95)
    if rewinding:
        # reproduz o corte "de trás para frente" (retrocesso real da animação)
        p = ease(prog(t, T["resumo"] - 0.05, T["resumo"] + 0.8))
        tr = lerp(T["inverter"] + 0.5, T["enchem"] - 0.6, p)
        main_section(c, tr, camera(tr), alpha=1.0)
        section_labels(c, tr, camera(tr))
    elif in_cards:
        k = sm(t, T["ciclo"] - 0.1, T["ciclo"] + 0.3)
        if k < 1:
            main_section(c, t, cam, alpha=1 - k)
        cycle_cards(c, t)
    elif sec_a > 0.001:
        main_section(c, t, cam, alpha=sec_a)

    # ----- rosto
    if t < T["lift"] + 1.15 or t >= T["aviso"] - 0.3:
        c.save()
        cam.apply(c)
        face_layer(c, t, cam)
        c.restore()

    # ----- sobreposições
    if T["section"] - 0.2 <= t < T["ciclo"] or T["resumo"] + 0.8 <= t < T["aviso"]:
        section_labels(c, t, cam)
        draw_inset(c, t, cam, congestion(t)[0])
    hook_air(c, t, cam)
    # etiqueta PELE durante a separação das camadas
    lift = sm(t, T["lift"], T["lift"] + 1.1)
    if 0 < lift < 1:
        pill_label(c, "PELE", 800, 560 - 140 * lift, alpha=min(1.0, 2.2 * math.sin(math.pi * lift)),
                   dot="#EDB592", size=36)
    # títulos
    title(c, [[("UMA", "#FFFFFF"), ("NARINA", YELLOW)], [("RESPIRA", "#FFFFFF"), ("MELHOR?", YELLOW)]],
          250, 96, t, 0.15, T["scan"] - 0.25)
    title(c, [[("POR", "#FFFFFF"), ("DENTRO", YELLOW), ("DO", "#FFFFFF"), ("NARIZ", "#FFFFFF")]],
          280, 78, t, T["lift"] + 0.1, T["cavidades"] - 0.3)
    # avanço rápido
    a_ff = window(t, T["horas"] - 0.1, T["ciclo"] - 0.2, fi=0.2, fo=0.25)
    if a_ff > 0:
        sc = lerp(0.4, 1.0, eback(prog(t, T["horas"] - 0.1, T["horas"] + 0.2)))
        blink = 1.0 if t > T["horas"] + 0.4 else 1.0
        icon_ffwd(c, 270, 255, 0.95 * sc * (1 + 0.05 * math.sin(t * 12)), alpha=a_ff * blink)
        rich_line(c, [("HORAS", YELLOW), ("DEPOIS", "#FFFFFF")], 640, 255, 76, alpha=a_ff, scale=sc)
        icon_clock(c, 905, 395, 52 * sc, air_time(t), alpha=a_ff)
    rewind_fx(c, t)
    if t >= T["resumo"] + 0.6:
        resumo_steps(c, t)
    warning_card(c, t)
    # CTA
    title(c, [[("VOCÊ", "#FFFFFF"), ("JÁ", "#FFFFFF")], [("PERCEBEU", YELLOW), ("ISSO?", YELLOW)]],
          250, 104, t, T["cta"] + 0.05, DURATION + 1)
    a_b = window(t, T["comentarios"] - 0.3, DURATION + 1, fi=0.3)
    if a_b > 0:
        icon_bubble(c, 890, 640, lerp(0.3, 1.0, eback(prog(t, T["comentarios"] - 0.3, T["comentarios"] + 0.1))), t,
                    alpha=a_b)
    vignette(c)
    draw_captions(c, t)
    # fade in/out
    if t < 0.25:
        c.drawRect(skia.Rect.MakeWH(W, H), P(C("#000000", 1 - t / 0.25)))


def render_frame(t, arr=None):
    if arr is None:
        arr = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    compose(c, t)
    surf.flushAndSubmit()
    return arr
