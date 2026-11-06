# -*- coding: utf-8 -*-
"""Linha do tempo: todos os tempos das cenas derivam da narração (build/timing.json)."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = json.load(open(os.path.join(HERE, "..", "build", "timing.json"), encoding="utf-8"))
WORDS = TIMING["words"]
SEG = {s["id"]: s for s in TIMING["segments"]}
DURATION = TIMING["duration"]


def _norm(s):
    return re.sub(r"[^\wÀ-ÿ]", "", s.lower())


def W(word, seg=None, n=1, end=False):
    """Tempo de início (ou fim) da n-ésima ocorrência de `word` (opcionalmente dentro de `seg`)."""
    k = 0
    for w in WORDS:
        if seg and w["seg"] != seg:
            continue
        if _norm(w["text"]) == _norm(word):
            k += 1
            if k == n:
                return w["end"] if end else w["start"]
    raise KeyError(word)


def S(seg, end=False):
    return SEG[seg]["end"] if end else SEG[seg]["start"]


# ---------------------------------------------------------------- cenas
T = {}
T["hook"] = 0.0
T["narina"] = W("narina")
T["melhor"] = W("melhor")
T["scan"] = W("olha", "hook2")                 # varredura raio-x
T["xray"] = W("dentro", "hook2")               # pele fica transparente
T["lift"] = S("hook2", end=True) - 0.15        # camada de pele se afasta
T["section"] = T["lift"] + 0.9                 # corte totalmente revelado
T["cavidades"] = W("cavidades")
T["septo"] = W("septo")
T["conchas"] = W("conchas")
T["mucosa"] = W("mucosa")
T["vasos"] = W("vasos", "conchas")
T["curioso"] = S("curioso")
T["enchem"] = W("enchem")
T["incha"] = W("incha", "incha")
T["estreita"] = W("estreita")
T["desincha"] = W("desincha", "desincha")
T["facilidade"] = W("facilidade")
T["horas"] = S("horas")
T["inverter"] = W("inverter")
T["ciclo"] = S("ciclo")
T["ciclo_word"] = W("ciclo", "ciclo")
T["sistema"] = W("sistema")
T["compensa_seg"] = S("compensa")
T["compensa"] = W("compensa")
T["resumo"] = S("resumo")
T["r_incha"] = W("incha", "resumo")
T["r_desincha"] = W("desincha", "resumo")
T["r_trocam"] = W("trocam")
T["aviso"] = S("aviso")
T["persistente"] = W("persistente")
T["cta"] = S("cta")
T["percebido"] = W("percebido")
T["comentarios"] = W("comentários")
T["end"] = DURATION

# eventos sonoros (tempo, tipo)
SFX = [
    (T["narina"] - 0.05, "pop"),
    (T["scan"], "scan"),
    (T["lift"] - 0.1, "whoosh"),
    (T["cavidades"], "pop"),
    (T["septo"], "pop"),
    (T["conchas"], "pop"),
    (T["mucosa"], "pop"),
    (T["vasos"] - 0.25, "whoosh_s"),
    (T["enchem"], "swell"),
    (T["estreita"], "pop"),
    (T["desincha"], "deflate"),
    (T["facilidade"], "pop"),
    (T["horas"] - 0.1, "ffwd"),
    (T["ciclo_word"] - 0.05, "ding"),
    (T["sistema"], "zap"),
    (T["compensa"], "pop"),
    (T["resumo"] - 0.05, "rewind"),
    (T["r_incha"], "pop"),
    (T["r_desincha"], "pop"),
    (T["r_trocam"], "pop"),
    (T["aviso"] - 0.15, "whoosh"),
    (T["aviso"] + 0.2, "alert"),
    (T["cta"] - 0.05, "whoosh_s"),
    (T["comentarios"], "pop"),
]

if __name__ == "__main__":
    for k, v in T.items():
        print(f"{k:14s} {v:6.2f}")
