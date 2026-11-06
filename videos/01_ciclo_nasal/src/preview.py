# -*- coding: utf-8 -*-
"""Renderiza quadros isolados em PNG para revisão: python3 src/preview.py 1.0 9.5 ..."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from scene import render_frame

out = sys.argv[1] if sys.argv[1].endswith("/") else "build/preview/"
times = [float(x) for x in sys.argv[1:] if not x.endswith("/")]
os.makedirs(out, exist_ok=True)
for t in times:
    t0 = time.time()
    a = render_frame(t)
    Image.fromarray(a[:, :, :3]).resize((540, 960), Image.LANCZOS).save(f"{out}/f_{t:06.2f}.png")
    print(t, round(time.time() - t0, 3), "s")
