"""動画づくりの検証用プロトタイプ(縦動画 1080x1920・10秒・30fps)。CPUだけ・無料・オフラインで動く構成の確認用。

  人物は(ほぼ)止めたまま、ゆっくり上下にゆれる + 背景のキラキラがまたたく
  + 声(pyopenjtalk、アニメ版の声) + 吹き出しのセリフ + BGM

使い方: python scripts/video_proto.py 03 B output/anime_03_B2_s4.png   # → output/proto_03_B.mp4(3つ目は背景が純黒の元画像)
背景が純黒(0,0,0)のアニメ画像で、背景だけを動かせる。それ以外の絵は全体に重ねる効果だけを使う。
"""
import json
import subprocess
import sys
import time
import wave
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import make_video as mv  # make_bgm, make_subtitle_png, W, H を再利用

ROOT = Path(__file__).resolve().parent.parent
cid, pat = sys.argv[1], sys.argv[2]
W, H, FPS, SEC = 1080, 1920, 30, 10
data = json.load(open(ROOT / "characters/characters.json", encoding="utf-8"))
c = next(x for x in data["characters"] if x["id"] == cid)
src = sys.argv[3] if len(sys.argv) > 3 else f"output/anime_final/anime_{cid}_{pat}.png"
img = Image.open(ROOT / src).convert("RGB")

# 1. 9:16 に拡大(縦いっぱい)して左右を切る
scale = H / img.height
big = img.resize((round(img.width * scale), H), Image.LANCZOS)
x0 = (big.width - W) // 2
big = big.crop((x0, 0, x0 + W, H))
a = np.asarray(big, dtype=np.float32)

# 2. 背景(ふちからつながった純黒)を探す
black = a.max(axis=2) <= 10
bg = np.zeros((H, W), bool)
dq = deque()
for x in range(W):
    for y in (0, H - 1):
        if black[y, x]:
            bg[y, x] = True
            dq.append((y, x))
for y in range(H):
    for x in (0, W - 1):
        if black[y, x] and not bg[y, x]:
            bg[y, x] = True
            dq.append((y, x))
while dq:
    y, x = dq.popleft()
    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
        if 0 <= ny < H and 0 <= nx < W and black[ny, nx] and not bg[ny, nx]:
            bg[ny, nx] = True
            dq.append((ny, nx))
print("背景の割合:", round(float(bg.mean()), 3))

# 3. 声(アニメ版)と BGM
import pyopenjtalk
v = c["voice_anime"][pat]
text = c["lines_anime"][0]
x, sr = pyopenjtalk.tts(text, speed=v["speed"], half_tone=v["half_tone"])
x = x / np.abs(x).max() * 0.9
out = ROOT / "output" / "proto"
out.mkdir(parents=True, exist_ok=True)
vw = out / "voice.wav"
with wave.open(str(vw), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((x * 32767).astype(np.int16).tobytes())
mv.make_bgm(out / "bgm.wav", SEC)
mv.make_subtitle_png(text, out / "sub.png", "#FFE066")

# 4. 背景のキラキラの位置(固定)と、またたきの位相
rng = np.random.default_rng(3)
n = 60
sx = rng.integers(0, W, n); sy = rng.integers(0, H, n)
ph = rng.uniform(0, 6.28, n); sp = rng.uniform(0.8, 2.2, n); rad = rng.choice([4, 6, 9, 13], n, p=[.4, .3, .2, .1])
yy, xx = np.mgrid[0:H, 0:W]
person_mask = ~bg
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", str(vw), "-i", str(out / "bgm.wav"), "-i", str(out / "sub.png"),
       "-filter_complex",
       "[3:v]format=rgba[s];[0:v][s]overlay=x=0:y=60:enable='between(t,1,9)'[v];"
       "[2:a]volume=0.45[b];[1:a]adelay=900|900,volume=1.4[vo];[b][vo]amix=inputs=2:duration=first[a]",
       "-map", "[v]", "-map", "[a]", "-t", str(SEC), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
       "-c:a", "aac", "-b:a", "160k", str(ROOT / "output" / f"proto_{cid}_{pat}.mp4")]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
t0 = time.time()
glow_cache = None
for f in range(FPS * SEC):
    t = f / FPS
    # 人物を、ゆっくり上下に(±7px)ゆらす
    dy = int(round(7 * np.sin(2 * np.pi * t / 3.0)))
    frame = np.roll(a, dy, axis=0)
    mask = np.roll(person_mask, dy, axis=0)
    # 背景: 暗い金色のゆらぎ + またたく星
    bgcol = np.zeros((H, W, 3), np.float32)
    bgcol += (np.array([30, 16, 6], np.float32) * (0.7 + 0.3 * np.sin(t * 1.3)))
    layer = np.zeros((H, W), np.float32)
    for i in range(n):
        b = 0.5 + 0.5 * np.sin(t * sp[i] * 2 + ph[i])
        r = int(rad[i] * (0.6 + 0.8 * b))
        y0, y1, x0_, x1 = max(0, sy[i] - r), min(H, sy[i] + r + 1), max(0, sx[i] - r), min(W, sx[i] + r + 1)
        layer[y0:y1, x0_:x1] = np.maximum(layer[y0:y1, x0_:x1], b * np.clip(1 - np.hypot(yy[y0:y1, x0_:x1] - sy[i], xx[y0:y1, x0_:x1] - sx[i]) / max(r, 1), 0, 1))
    bgcol += layer[..., None] * np.array([255, 230, 160], np.float32)
    # 背景だけを置き換える(人物は frame のまま)。ゆらした人物のぶん、背景がのぞく所は背景色で埋める
    res = np.where(mask[..., None], frame, bgcol)
    p.stdin.write(np.clip(res, 0, 255).astype(np.uint8).tobytes())
p.stdin.close()
p.wait()
print("できました: output/proto_%s_%s.mp4 (%.0f秒かかった)" % (cid, pat, time.time() - t0))
