"""AIで作った動くクリップ(mp4)に、声・吹き出しのセリフ・BGM を重ねて、縦動画(1080x1920)に仕上げるプログラム。

使い方: python scripts/compose_video.py クリップ.mp4 03 B 出力.mp4
  クリップ: Colab などで作った、横長でも縦長でもよい動く映像
  03 B     : キャラの番号と、声の種類(real / A / B)。声とセリフは characters/characters.json の設定
- 映像は、行って戻る(ブーメラン)で2倍の長さにして、ゆっくり動き続けるようにする
- 横長の映像は、上下にぼかした同じ映像を敷いて、縦に収める
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import pyopenjtalk

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import make_video as mv  # make_bgm, make_subtitle_png

clip, cid, style, dst = sys.argv[1:5]
data = json.load(open(ROOT / "characters/characters.json", encoding="utf-8"))
c = next(x for x in data["characters"] if x["id"] == cid)
v = c["voice"] if style == "real" else c["voice_anime"][style]
lines = c["lines"] if style == "real" else c["lines_anime"]
work = ROOT / "output" / "compose"
work.mkdir(parents=True, exist_ok=True)

dur_clip = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).decode())
total = round(dur_clip * 2, 2)          # 行って戻る
voices = []
for i, t in enumerate(lines):
    x, sr = pyopenjtalk.tts(t, speed=v["speed"], half_tone=v["half_tone"])
    x = x / np.abs(x).max() * 0.9
    p = work / f"v{i}.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    voices.append((p, len(x) / sr))
    mv.make_subtitle_png(t, work / f"s{i}.png", "#FFE066")
mv.make_bgm(work / "bgm.wav", total)

# セリフの開始時刻: 1つ目は0.6秒、2つ目は1つ目が終わって0.5秒あけて
t0 = 0.6
t1 = t0 + voices[0][1] + 0.5
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", clip,
       "-i", str(voices[0][0]), "-i", str(voices[1][0]), "-i", str(work / "bgm.wav"),
       "-i", str(work / "s0.png"), "-i", str(work / "s1.png"),
       "-filter_complex",
       "[0:v]fps=30,split[x][y];[y]reverse[r];[x][r]concat=n=2:v=1:a=0,split[a][b];"
       "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.15[bg];"
       "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
       f"[4:v]format=rgba[s0];[5:v]format=rgba[s1];"
       f"[base][s0]overlay=0:90:enable='between(t,{t0},{t0 + voices[0][1] + 0.3:.2f})'[o1];"
       f"[o1][s1]overlay=0:90:enable='between(t,{t1:.2f},{min(total - 0.2, t1 + voices[1][1] + 0.4):.2f})',fade=t=out:st={total - 0.7:.2f}:d=0.7[v];"
       f"[3:a]volume=0.4[b];[1:a]adelay={int(t0 * 1000)}|{int(t0 * 1000)},volume=1.4[a1];"
       f"[2:a]adelay={int(t1 * 1000)}|{int(t1 * 1000)},volume=1.4[a2];[b][a1][a2]amix=inputs=3:duration=first,afade=t=out:st={total - 0.7:.2f}:d=0.7[a]",
       "-map", "[v]", "-map", "[a]", "-t", str(total), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-c:a", "aac", "-b:a", "160k", dst]
subprocess.run(cmd, check=True)
print("できました:", dst, "| 長さ", total, "秒 | セリフ:", lines)
