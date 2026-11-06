# -*- coding: utf-8 -*-
"""Trilha sonora sintetizada (sem direitos autorais), efeitos sonoros e mixagem final.

Entrada: build/narration_raw.wav + eventos SFX de timeline.py
Saída:   build/mix.wav (48 kHz estéreo, ~-14 LUFS após loudnorm no ffmpeg)
"""
import os, subprocess, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import SFX, DURATION, TIMING

SR = 48000
BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build")
rng = np.random.RandomState(3)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def env_ad(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def sweep(f0, f1, dur, kind="sin"):
    t = tvec(dur)
    f = np.geomspace(f0, f1, len(t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    return np.sin(ph)


# ------------------------------------------------------------------ efeitos
def sfx(kind):
    if kind == "pop":
        t = tvec(0.14)
        s = sweep(1100, 520, 0.14) * env_ad(len(t), 0.002, 0.035)
        s += 0.3 * bp(rng.randn(len(t)), 2000, 6000) * env_ad(len(t), 0.001, 0.01)
        return 0.5 * s
    if kind in ("whoosh", "whoosh_s"):
        d = 0.75 if kind == "whoosh" else 0.42
        n = int(d * SR)
        noise = rng.randn(n)
        out = np.zeros(n)
        # filtro com frequência variando (blocos)
        blocks = 24
        for b in range(blocks):
            s0, s1 = b * n // blocks, (b + 1) * n // blocks
            fc = 300 * (12 ** (b / blocks))
            out[s0:s1] = bp(noise[max(0, s0 - 2000):s1], fc * 0.6, min(fc * 1.6, 20000))[-(s1 - s0):]
        e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
        return 0.55 * out * e
    if kind == "scan":
        d = 1.3
        t = tvec(d)
        s = 0.25 * sweep(220, 1400, d) + 0.12 * sweep(440, 2800, d)
        s *= 0.5 + 0.5 * np.sin(2 * np.pi * 18 * t) ** 2
        e = np.minimum(1, t / 0.15) * np.minimum(1, (d - t) / 0.3)
        return 0.35 * s * e
    if kind == "swell":
        d = 1.1
        t = tvec(d)
        s = np.sin(2 * np.pi * np.cumsum(np.linspace(90, 150, len(t))) / SR)
        s += 0.4 * lp(rng.randn(len(t)), 500)
        e = np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.25)
        return 0.32 * s * e
    if kind == "deflate":
        d = 0.8
        t = tvec(d)
        s = bp(rng.randn(len(t)), 600, 3500) * np.linspace(1, 0.2, len(t))
        s += 0.5 * sweep(260, 110, d)
        e = np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.4)
        return 0.28 * s * e
    if kind == "ffwd":
        d = 1.0
        t = tvec(d)
        s = np.zeros(len(t))
        for k in range(8):
            st = int(k * 0.11 * SR)
            ch = sweep(500 + 120 * k, 1500 + 200 * k, 0.09)
            ch *= env_ad(len(ch), 0.005, 0.03)
            s[st:st + len(ch)] += ch[: len(s) - st]
        return 0.35 * s
    if kind == "ding":
        d = 1.6
        t = tvec(d)
        s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dd) for f, a, dd in
                ((1046.5, 1.0, 0.6), (1568, 0.5, 0.4), (2093, 0.35, 0.25), (2637, 0.2, 0.18)))
        return 0.3 * s * np.minimum(1, t / 0.003)
    if kind == "zap":
        d = 0.5
        t = tvec(d)
        s = np.sign(np.sin(2 * np.pi * 70 * t)) * 0.3 + sweep(2000, 600, d) * 0.5
        s = bp(s, 200, 5000) * env_ad(len(t), 0.01, 0.12)
        return 0.22 * s
    if kind == "rewind":
        d = 0.85
        t = tvec(d)
        f = 1400 * np.exp(-t * 2.0) * (1 + 0.15 * np.sin(2 * np.pi * 14 * t))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR)
        s = 0.6 * s + 0.4 * bp(rng.randn(len(t)), 1500, 6000)
        e = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.2)
        return 0.3 * s * e
    if kind == "alert":
        out = np.zeros(int(0.7 * SR))
        for k, f in enumerate((880, 660)):
            t = tvec(0.35)
            tone = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * env_ad(len(t), 0.005, 0.12)
            st = int(k * 0.18 * SR)
            out[st:st + len(tone)] += tone
        return 0.22 * out
    raise KeyError(kind)


# ------------------------------------------------------------------ música
def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def music(dur):
    n = int(dur * SR)
    out = np.zeros(n)
    bpm = 100
    beat = 60 / bpm
    bar = beat * 4
    # progressão leve e curiosa: Fmaj7 - G6 - Em7 - Am7 (em MIDI)
    chords = [[53, 57, 60, 64], [55, 59, 62, 64], [52, 55, 59, 62], [57, 60, 64, 67]]
    t_all = np.arange(n) / SR
    nb = int(dur / bar) + 2
    for b in range(nb):
        ch = chords[b % 4]
        s0 = int(b * bar * SR)
        L = int(bar * SR * 1.15)
        if s0 >= n:
            break
        L = min(L, n - s0)
        t = np.arange(L) / SR
        pad = np.zeros(L)
        for m in ch:
            f = note(m)
            for det in (-0.12, 0.12):
                pad += np.sin(2 * np.pi * f * (1 + det / 100) * t + rng.uniform(0, 6))
        e = np.minimum(1, t / 0.6) * np.minimum(1, (L / SR - t) / 0.5)
        out[s0:s0 + L] += 0.035 * lp(pad, 1800) * e
        # baixo
        bass = np.sin(2 * np.pi * note(ch[0] - 12) * t) * np.exp(-t / 1.2)
        out[s0:s0 + L] += 0.06 * bass * np.minimum(1, t / 0.01)
        # arpejo (colcheias)
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 24]
        for k, m in enumerate(arp):
            st = s0 + int(k * beat / 2 * SR)
            ln = int(0.35 * SR)
            if st + ln > n:
                continue
            tt = np.arange(ln) / SR
            f = note(m)
            pl = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt / 0.12)
            out[st:st + ln] += 0.03 * pl * np.minimum(1, tt / 0.004)
        # percussão leve: kick suave nos tempos 1 e 3, shaker nas colcheias
        for k in range(4):
            st = s0 + int(k * beat * SR)
            if k in (0, 2) and st + 6000 < n:
                tt = np.arange(6000) / SR
                kick = np.sin(2 * np.pi * np.cumsum(np.geomspace(120, 45, 6000)) / SR) * np.exp(-tt / 0.08)
                out[st:st + 6000] += 0.10 * kick
            for h in (0, 1):
                sh = st + int(h * beat / 2 * SR)
                if sh + 3000 < n:
                    nz = hp(rng.randn(3000), 6000) * np.exp(-np.arange(3000) / SR / 0.02)
                    out[sh:sh + 3000] += (0.018 if h else 0.010) * nz
    # fade in/out
    fi = int(0.5 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.5 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out


def read_wav(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return a


def main():
    n = int(DURATION * SR)
    voice = read_wav(os.path.join(BUILD, "narration_raw.wav"))
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    # tratamento de voz: passa-alta, leve presença, compressão suave
    v = hp(voice, 85)
    v = v + 0.25 * bp(v, 2500, 5500)
    thr = 0.25
    a = np.abs(v)
    gain = np.where(a > thr, (thr + (a - thr) / 3) / np.maximum(a, 1e-9), 1.0)
    gain = lp(gain, 30, order=1)
    v = v * gain
    v /= np.max(np.abs(v)) + 1e-9
    v *= 0.85

    # ducking da música pela presença de voz
    speak = np.zeros(n)
    for s in TIMING["segments"]:
        speak[int(s["start"] * SR):int(s["end"] * SR)] = 1
    duck = lp(speak, 3, order=1)
    duck = np.clip(duck / (np.max(duck) + 1e-9), 0, 1)
    mus = music(DURATION)[:n]
    v_rms = np.sqrt(np.mean(v[speak > 0] ** 2))
    mus *= 0.42 * v_rms / (np.sqrt(np.mean(mus ** 2)) + 1e-9)   # música ~-7.5 dB sem voz
    mus *= 10 ** (lerp_db(duck) / 20)

    fx = np.zeros(n)
    for t, kind in SFX:
        s = sfx(kind)
        st = int(max(0, t) * SR)
        e = min(n, st + len(s))
        fx[st:e] += s[: e - st]

    mix_l = v + mus + 0.55 * fx
    mix_r = v + mus + 0.55 * fx
    # leve espacialização da música/efeitos
    mix_r = mix_r + 0.08 * np.roll(mus, 240)
    st = np.stack([mix_l, mix_r], 1)
    st /= np.max(np.abs(st)) + 1e-9
    st *= 0.9
    p = os.path.join(BUILD, "mix_pre.wav")
    with wave.open(p, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), os.path.join(BUILD, "mix.wav")], check=True)
    print("ok mix.wav")


def lerp_db(d):
    # -4 dB sem voz, -15 dB durante a fala
    return -1 + (-12 + 1) * d


if __name__ == "__main__":
    main()
