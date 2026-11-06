# -*- coding: utf-8 -*-
"""Renderiza todos os quadros em paralelo e codifica o vídeo (sem áudio) com ffmpeg."""
import os, subprocess, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

FPS = 30
W, H = 1080, 1920


SUB = int(os.environ.get("MB_SAMPLES", "3"))  # amostras de desfoque de movimento por quadro
SHUTTER = 0.5                                   # obturador de 180°


def work(i):
    """Renderiza o quadro i com desfoque de movimento (média de sub-quadros)."""
    from scene import render_frame
    t = i / FPS
    if SUB <= 1:
        return render_frame(t)[:, :, :3].tobytes()
    acc = np.zeros((H, W, 3), np.float32)
    for k in range(SUB):
        off = ((k + 0.5) / SUB - 0.5) * SHUTTER / FPS
        acc += render_frame(max(0.0, t + off))[:, :, :3]
    return np.clip(acc / SUB + 0.5, 0, 255).astype(np.uint8).tobytes()


def main():
    from timeline import DURATION
    out = sys.argv[1] if len(sys.argv) > 1 else "build/video_noaudio.mp4"
    n = int(round(DURATION * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(work, range(n), chunksize=6)):
            enc.stdin.write(buf)
            if k % 150 == 0:
                print(f"{k}/{n} quadros  {time.time() - t0:.0f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    print("ok", out, n, "quadros", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
