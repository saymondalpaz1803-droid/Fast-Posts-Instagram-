# -*- coding: utf-8 -*-
"""Gera a narração (RHVoice pt-BR, offline) e o mapa de tempo palavra a palavra.

Saídas em build/: narration.wav (48 kHz mono) e timing.json
"""
import json, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, GAPS, LEAD_IN, TAIL

BUILD = os.path.join(HERE, "..", "build")
SR = 48000
ENGINE = os.environ.get("TTS_ENGINE", "edge")            # "edge" (neural, natural) ou "rhvoice" (offline)
EDGE_VOICE = os.environ.get("TTS_VOICE", "pt-BR-FranciscaNeural")
EDGE_RATE = os.environ.get("TTS_RATE", "+0%")
EDGE_PITCH = os.environ.get("TTS_PITCH", "-2Hz")
VOICE = os.environ.get("RH_VOICE", "leticia-f123")
RATE = os.environ.get("RH_RATE", "110")
PITCH = os.environ.get("RH_PITCH", "100")


def synth(text, path):
    subprocess.run(["RHVoice-test", "-p", VOICE, "-r", RATE, "-t", PITCH,
                    "-R", "24000", "-o", path], input=text.encode("utf-8"), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = path.replace(".wav", "_48k.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ar", str(SR), "-ac", "1",
                    "-sample_fmt", "s16", out], check=True)
    with wave.open(out) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a


def synth_edge(text, path):
    """Voz neural (Microsoft Edge TTS). Retorna (áudio 48 kHz, [(palavra, início_s, fim_s)])."""
    import asyncio, edge_tts

    async def run():
        com = edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE, pitch=EDGE_PITCH, boundary="WordBoundary",
                                   proxy=os.environ.get("HTTPS_PROXY") or None)
        audio, words = bytearray(), []
        async for ch in com.stream():
            if ch["type"] == "audio":
                audio += ch["data"]
            elif ch["type"] == "WordBoundary":
                words.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
        return bytes(audio), words

    for attempt in range(4):
        try:
            data, words = asyncio.run(run())
            break
        except Exception:
            if attempt == 3:
                raise
            import time
            time.sleep(2 ** (attempt + 1))
    mp3 = path.replace(".wav", ".mp3")
    open(mp3, "wb").write(data)
    out = path.replace(".wav", "_48k.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1",
                    "-sample_fmt", "s16", out], check=True)
    with wave.open(out) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a, words


def trim_bounds(a, thr=0.006):
    env = np.convolve(np.abs(a), np.ones(240) / 240, mode="same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return 0, len(a)
    return max(0, idx[0] - 960), min(len(a), idx[-1] + 2400)


def align_edge(toks, words, offset):
    """Usa as fronteiras de palavra do serviço; tokens sem par recebem tempo interpolado."""
    def norm(x):
        return re.sub(r"[^\wÀ-ÿ]", "", x.lower())
    out, j = [], 0
    for k, t in enumerate(toks):
        nt = norm(t["text"])
        hit = None
        for jj in range(j, min(j + 3, len(words))):
            if norm(words[jj][0]) == nt or nt.startswith(norm(words[jj][0])) or norm(words[jj][0]).startswith(nt):
                hit = jj
                break
        if hit is not None:
            st, en = words[hit][1] - offset, words[hit][2] - offset
            j = hit + 1
        else:
            st = out[-1]["end"] if out else 0.0
            en = st + 0.25
        out.append({"text": t["text"], "hl": t["hl"], "start": max(0.0, st), "end": max(st + 0.05, en),
                    "brk": t["brk"]})
    return out


def trim(a, thr=0.012):
    env = np.convolve(np.abs(a), np.ones(240) / 240, mode="same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return a
    s, e = max(0, idx[0] - 480), min(len(a), idx[-1] + 960)
    return a[s:e]


def syllables(word):
    w = word.lower()
    groups = re.findall(r"[aeiouáéíóúâêôãõàü]+", w)
    n = 0
    for g in groups:
        # ditongos contam 1; hiatos simples (ex.: "ia" em "sanguíneos") ~ aproximação
        n += 1 if len(g) <= 2 else 2
    return max(1, n)


def pauses(a, min_len=0.07, thr=0.010):
    """Retorna lista de (inicio, fim) de silêncios internos (em segundos)."""
    env = np.convolve(np.abs(a), np.ones(480) / 480, mode="same")
    quiet = env < thr
    out, i, n = [], 0, len(a)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) / SR >= min_len and i > SR * 0.1 and j < n - SR * 0.1:
                out.append((i / SR, j / SR))
            i = j
        else:
            i += 1
    return out


def tokenize(text):
    toks = []
    for raw in text.split():
        hl = "*" in raw
        clean = raw.replace("*", "")
        toks.append({"text": clean, "hl": hl,
                     "brk": bool(re.search(r"[,.!?:;]$", clean)),
                     "syl": syllables(re.sub(r"[^\wÀ-ÿ]", "", clean))})
    return toks


def align(toks, dur, ps):
    """Divide a fala em frases pelas pausas detectadas e distribui por sílabas."""
    # grupos de palavras separados por pontuação
    groups, cur = [], []
    for t in toks:
        cur.append(t)
        if t["brk"]:
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    # escolher as pausas mais longas para as fronteiras entre grupos
    need = len(groups) - 1
    ps_sorted = sorted(ps, key=lambda p: p[1] - p[0], reverse=True)[:need]
    ps_sorted = sorted(ps_sorted)
    total_syl = sum(t["syl"] for t in toks)
    if len(ps_sorted) == need:
        bounds = [0.0] + [x for p in ps_sorted for x in p] + [dur]
        spans = [(bounds[2 * i], bounds[2 * i + 1]) for i in range(len(groups))]
    else:  # fallback: proporcional
        spans, t0 = [], 0.0
        for g in groups:
            d = dur * sum(t["syl"] for t in g) / total_syl
            spans.append((t0, t0 + d)); t0 += d
    out = []
    for g, (s, e) in zip(groups, spans):
        gs = sum(t["syl"] + 0.6 for t in g)
        t0 = s
        for t in g:
            d = (e - s) * (t["syl"] + 0.6) / gs
            out.append({"text": t["text"], "hl": t["hl"], "start": t0, "end": t0 + d, "brk": t["brk"]})
            t0 += d
    return out


def main():
    os.makedirs(BUILD, exist_ok=True)
    tmp = os.path.join(BUILD, "tts_tmp"); os.makedirs(tmp, exist_ok=True)
    parts = [np.zeros(int(LEAD_IN * SR), np.float32)]
    t = LEAD_IN
    timing = {"segments": [], "words": []}
    for sid, text in SEGMENTS:
        plain = text.replace("*", "")
        if ENGINE == "edge":
            a, bwords = synth_edge(plain, os.path.join(tmp, f"{sid}.wav"))
            s0, s1 = trim_bounds(a)
            a = a[s0:s1]
            words = align_edge(tokenize(text), bwords, s0 / SR)
        else:
            a = trim(synth(plain, os.path.join(tmp, f"{sid}.wav")))
            words = align(tokenize(text), len(a) / SR, pauses(a))
        dur = len(a) / SR
        for w in words:
            w["start"] += t; w["end"] += t; w["seg"] = sid
        timing["words"] += words
        timing["segments"].append({"id": sid, "start": t, "end": t + dur, "text": plain})
        parts.append(a)
        g = GAPS.get(sid, 0.3)
        parts.append(np.zeros(int(g * SR), np.float32))
        t += dur + g
    parts.append(np.zeros(int(TAIL * SR), np.float32))
    audio = np.concatenate(parts)
    peak = np.max(np.abs(audio)) or 1
    audio = audio / peak * 0.89
    timing["duration"] = len(audio) / SR
    with wave.open(os.path.join(BUILD, "narration_raw.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    with open(os.path.join(BUILD, "timing.json"), "w", encoding="utf-8") as f:
        json.dump(timing, f, ensure_ascii=False, indent=1)
    for s in timing["segments"]:
        print(f'{s["start"]:6.2f}-{s["end"]:6.2f}  {s["id"]}')
    print("TOTAL", round(timing["duration"], 2))


if __name__ == "__main__":
    main()
