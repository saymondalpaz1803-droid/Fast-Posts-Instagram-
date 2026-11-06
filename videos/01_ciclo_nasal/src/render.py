# -*- coding: utf-8 -*-
"""Renderiza todos os quadros em paralelo e codifica o vídeo (sem áudio) com ffmpeg."""
import os, subprocess, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

FPS = 30
W, H = 1080, 1920


def work(i):
    from scene import render_frame
    a = render_frame(i / FPS)
    return a[:, :, :3].tobytes()


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
