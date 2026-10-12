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

# 2. 後光: 人物(背景でない所)のまわりがやわらかく金色に光る
person = Image.fromarray(((~bg) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20))
halo = np.asarray(person, float)[..., None] / 255.0
halo = np.clip(halo * 2.0, 0, 1) * 0.95

# 3. 放射状の光線(頭のうしろから)
rays = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(rays)
n = 22
for k in range(n):
    ang = 2 * math.pi * k / n + 0.07
    half = math.pi / n * 0.28
    R = 1200
    pts = [(cx, cy), (cx + R * math.cos(ang - half), cy + R * math.sin(ang - half)),
           (cx + R * math.cos(ang + half), cy + R * math.sin(ang + half))]
    d.polygon(pts, fill=255)
rays = np.asarray(rays.filter(ImageFilter.GaussianBlur(2)), float)[..., None] / 255.0 * 0.55

# 4. キラキラ(大小の4つ星と光の粒)。背景だけに置く
rng = np.random.default_rng(7)
star = Image.new("L", (W, H), 0)
dot = Image.new("L", (W, H), 0)
sd, dd = ImageDraw.Draw(star), ImageDraw.Draw(dot)


def free(x, y, r):
    y0, y1, x0, x1 = max(0, y - r - 4), min(H, y + r + 5), max(0, x - r - 4), min(W, x + r + 5)
    return bg[y0:y1, x0:x1].mean() > 0.97


placed = 0
tries = 0
while placed < 38 and tries < 4000:
    tries += 1
    x, y = int(rng.integers(8, W - 8)), int(rng.integers(8, H - 8))
    r = int(rng.choice([5, 7, 9, 12, 16, 20], p=[0.25, 0.25, 0.2, 0.15, 0.1, 0.05]))
    if not free(x, y, r):
        continue
    k = r * 0.2
    sd.polygon([(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)], fill=255)
    placed += 1
for _ in range(700):
    x, y = int(rng.integers(5, W - 5)), int(rng.integers(5, H - 5))
    r = int(rng.choice([1, 2, 3]))
    if free(x, y, r):
        dd.ellipse((x - r, y - r, x + r, y + r), fill=255)
star_core = np.asarray(star, float)[..., None] / 255.0
dot_core = np.asarray(dot, float)[..., None] / 255.0
glow = np.asarray(Image.fromarray(np.maximum(np.asarray(star), np.asarray(dot))).filter(ImageFilter.GaussianBlur(6)), float)[..., None] / 255.0

# 5. 合成。背景の画素だけを変える
base = a.astype(float)
bgm = bg[..., None].astype(float)
light = np.clip(halo + rays, 0, 0.95)
out = base * (1 - light * bgm) + GOLD * (light * bgm)
g = np.clip(glow * 0.9, 0, 1) * bgm
out = out * (1 - g) + GOLD * g
core = np.clip(star_core + dot_core, 0, 1) * bgm
out = out * (1 - core) + WHITE * core
out = np.where(bgm > 0, out, base)
res = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(res).save(dst)
changed = np.abs(res.astype(int) - a).max(axis=2) > 0
print("保存:", dst, "| 変わった画素:", int(changed.sum()), "| うち背景以外:", int((changed & ~bg).sum()))
