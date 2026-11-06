#!/usr/bin/env bash
# Gera o vídeo completo: narração -> quadros -> trilha/efeitos -> MP4 final.
# Requisitos: ffmpeg, python3 com edge-tts, skia-python, numpy, scipy, pillow (RHVoice só para TTS_ENGINE=rhvoice).
# Voz: TTS_VOICE=pt-BR-FranciscaNeural (padrão) ou pt-BR-ThalitaNeural.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build output
python3 src/tts.py                       # narração + tempos por palavra
python3 src/render.py build/video_noaudio.mp4
python3 src/audio.py                     # trilha + efeitos + mixagem (-14 LUFS)
ffmpeg -y -loglevel error -i build/video_noaudio.mp4 -i build/mix.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart output/ciclo_nasal_1080x1920.mp4
ffmpeg -y -loglevel error -i build/narration_raw.wav -af "highpass=f=85,loudnorm=I=-16:TP=-1.5" \
  -ar 48000 output/narracao.wav
cp build/mix.wav output/audio_mixado.wav
python3 src/export_srt.py output/legendas.srt
echo "pronto: output/ciclo_nasal_1080x1920.mp4"
