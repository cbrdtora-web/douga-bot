"""黒い背景に、金色の後光・放射状の光線・たくさんのキラキラを足すプログラム。人物には一切触れない。

人物のまわりの「ふちが黒(0,0,0)でつながった背景」だけを見つけて、その上にだけ光を重ねる。
背景以外の画素(人物・服・オレンジのうねり)は、1画素も変わらない。
使い方: python scripts/add_sparkles.py 元画像.png 出力.png [--center 200 170]
(ユーザーの個別の依頼で、アニメB・03番に使った。部分修正の一種なので、依頼があるときだけ使うこと。)
"""
import math
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

args = sys.argv[1:]
cx, cy = 200, 170
if "--center" in args:
    i = args.index("--center")
    cx, cy = int(args[i + 1]), int(args[i + 2])
    del args[i:i + 3]
src, dst = args[0], args[1]
img = Image.open(src).convert("RGB")
W, H = img.size
a = np.asarray(img, dtype=np.int32)

# 1. 背景 = 画像のふちから続く純黒の領域(帯・ベルトなど人物の中の黒は含めない)
black = a.max(axis=2) <= 8
bg = np.zeros((H, W), bool)
dq = deque()
for x in range(W):
    for y in (0, H - 1):
        if black[y, x] and not bg[y, x]:
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
# ふち1画素は人物の輪郭になじませるため背景から外す
bg_img = Image.fromarray((bg * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))
bg = np.asarray(bg_img) > 0

GOLD = np.array([255, 214, 120], float)
WHITE = np.array([255, 250, 225], float)

# 2. 後光: 人物のまわりが、なめらかに金色に光る(近いほど明るく、遠いほど深いあめ色)
person = Image.fromarray(((~bg) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))
halo = np.asarray(person, float)[..., None] / 255.0
halo = np.clip(halo * 1.4, 0, 1) ** 2.2 * 0.7
COL_NEAR = np.array([255, 236, 190], float)
COL_FAR = np.array([232, 150, 40], float)

# 3. 放射状の光線: ごく淡く、ふんわり
rays = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(rays)
n = 14
for k in range(n):
    ang = 2 * math.pi * k / n + 0.11
    half = math.pi / n * 0.35
    R = 1200
    d.polygon([(cx, cy), (cx + R * math.cos(ang - half), cy + R * math.sin(ang - half)),
               (cx + R * math.cos(ang + half), cy + R * math.sin(ang + half))], fill=255)
rays = np.asarray(rays.filter(ImageFilter.GaussianBlur(9)), float)[..., None] / 255.0 * 0.0

# 4. 光のボケ(やわらかい円)と、細く長い上品な星
rng = np.random.default_rng(11)


def free(x, y, r, frac=0.93):
    y0, y1, x0, x1 = max(0, y - r - 3), min(H, y + r + 4), max(0, x - r - 3), min(W, x + r + 4)
    return bg[y0:y1, x0:x1].mean() > frac


bokeh = np.zeros((H, W), float)
placed, tries = 0, 0
while placed < 0 and tries < 6000:
    tries += 1
    x, y = int(rng.integers(10, W - 10)), int(rng.integers(10, H - 10))
    r = int(rng.choice([6, 9, 13, 18, 26], p=[0.3, 0.3, 0.2, 0.14, 0.06]))
    if not free(x, y, r):
        continue
    layer = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(layer)
    ld.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.uniform(110, 200)))
    bokeh = np.maximum(bokeh, np.asarray(layer.filter(ImageFilter.GaussianBlur(max(2.0, r / 2.2))), float) / 255.0)

star = Image.new("L", (W, H), 0)
sd = ImageDraw.Draw(star)
placed, tries = 0, 0
while placed < 14 and tries < 6000:
    tries += 1
    x, y = int(rng.integers(14, W - 14)), int(rng.integers(14, H - 14))
    r = int(rng.choice([10, 16, 24, 34], p=[0.4, 0.3, 0.2, 0.1]))
    if not free(x, y, r, 0.97):
        continue
    k = r * 0.07
    sd.polygon([(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)], fill=255)
    rr = r * 0.45
    k2 = rr * 0.12
    sd.polygon([(x, y - rr), (x + k2, y - k2), (x + rr, y), (x + k2, y + k2), (x, y + rr), (x - k2, y + k2), (x - rr, y), (x - k2, y - k2)], fill=255)
    placed += 1
dots = 0
tries = 0
dd = ImageDraw.Draw(star)
while dots < 34 and tries < 4000:
    tries += 1
    x, y = int(rng.integers(8, W - 8)), int(rng.integers(8, H - 8))
    r = int(rng.choice([1, 2], p=[0.6, 0.4]))
    if free(x, y, r, 0.97):
        dd.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.uniform(140, 255)))
        dots += 1
star_a = np.asarray(star, float) / 255.0
star_glow = np.asarray(star.filter(ImageFilter.GaussianBlur(7)), float) / 255.0
bokeh_a = bokeh[..., None] * 0.6
star_core = star_a[..., None]
star_gl = np.clip(star_glow * 1.8, 0, 1)[..., None] * 0.7

# 5. 合成。背景の画素だけを変える(黒の背景を、あめ色→金色のなめらかなグラデーションに置き換える)
base = a.astype(float)
bgm = bg[..., None].astype(float)
t = np.clip(halo / 0.7, 0, 1) ** 0.85
FAR, MID, NEAR = np.array([0, 0, 0], float), np.array([96, 52, 14], float), np.array([236, 190, 100], float)
grad = np.where(t < 0.5, FAR + (MID - FAR) * (t / 0.5), MID + (NEAR - MID) * ((t - 0.5) / 0.5))
out = grad
out = out * (1 - rays * 0.8) + np.array([255, 226, 150], float) * (rays * 0.8)
out = out * (1 - bokeh_a * 0.8) + np.array([255, 236, 180], float) * (bokeh_a * 0.8)
out = out * (1 - star_gl) + np.array([255, 226, 150], float) * star_gl
out = out * (1 - star_core) + np.array([255, 253, 240], float) * star_core
out = np.where(bgm > 0, out, base)
res = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(res).save(dst)
changed = np.abs(res.astype(int) - a).max(axis=2) > 0
print("保存:", dst, "| 変わった画素:", int(changed.sum()), "| うち背景以外:", int((changed & ~bg).sum()))
