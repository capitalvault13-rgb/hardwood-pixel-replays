#!/usr/bin/env bash
# Renders Pixel Replay #003 to renders/pixel-replay-003-wembanyama-50.mp4
set -euo pipefail
cd "$(dirname "$0")"
python3 audio.py
ffmpeg -v error -y -i audio.wav -af loudnorm=I=-14:TP=-1.5 -ar 48000 audio_norm.wav
python3 replay.py render | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - \
  -i audio_norm.wav -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k \
  -shortest -movflags +faststart ../../renders/pixel-replay-003-wembanyama-50.mp4
rm -f audio.wav audio_norm.wav
echo "done -> renders/pixel-replay-003-wembanyama-50.mp4"
