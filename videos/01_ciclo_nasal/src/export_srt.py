# -*- coding: utf-8 -*-
"""Exporta as legendas (mesmos grupos de palavras do vídeo) em SRT."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene import CAPTIONS


def ts(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


out = sys.argv[1] if len(sys.argv) > 1 else "legendas.srt"
with open(out, "w", encoding="utf-8") as f:
    for i, (st, en, words) in enumerate(CAPTIONS, 1):
        f.write(f"{i}\n{ts(st)} --> {ts(en)}\n{' '.join(w for w, _ in words)}\n\n")
print("ok", out, len(CAPTIONS))
