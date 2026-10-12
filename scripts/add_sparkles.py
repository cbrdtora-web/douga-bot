"""背景にキラキラ(4つの尖った星と小さな光の粒)を足すプログラム。人物には触れない(位置を手で指定)。

使い方: python scripts/add_sparkles.py 元画像.png 出力.png
(ユーザーの個別の依頼で、03番のBに使った。部分修正の一種なので、依頼があるときだけ使うこと。)
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
W, H = im.size
# (x, y, 半径): 背景(黒・オレンジのうねり)の上だけに置く。髪・服の上には置かない
STARS = [(34, 92, 11), (40, 190, 15), (24, 262, 9), (105, 432, 16), (152, 520, 12), (66, 566, 10), (128, 604, 9),
         (436, 20, 10), (470, 130, 12), (492, 214, 9), (30, 330, 12), (60, 650, 11)]
DOTS = [(70, 140, 3), (20, 140, 2), (90, 400, 3), (170, 470, 2), (40, 460, 3), (180, 600, 2), (480, 60, 3), (455, 180, 2),
        (500, 90, 2), (14, 520, 3), (100, 520, 2), (30, 610, 2), (330, 16, 3)]


def star_layer(sx, r):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y, rad in sx:
        k = rad * 0.22
        pts = [(x, y - rad), (x + k, y - k), (x + rad, y), (x + k, y + k), (x, y + rad), (x - k, y + k), (x - rad, y), (x - k, y - k)]
        d.polygon(pts, fill=(255, 250, 220, 255))
    return layer


sparkle = star_layer(STARS, 1)
dots = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dd = ImageDraw.Draw(dots)
for x, y, r in DOTS:
    dd.ellipse((x - r, y - r, x + r, y + r), fill=(255, 245, 200, 255))
glow = Image.alpha_composite(sparkle, dots).filter(ImageFilter.GaussianBlur(5))
a_glow = np.asarray(glow)[..., 3:4] / 255.0 * 0.85
base = np.asarray(im, dtype=np.float64)
out = base * (1 - a_glow) + np.array([255, 215, 120]) * a_glow           # やわらかい光
core = Image.alpha_composite(sparkle, dots)
a_core = np.asarray(core)[..., 3:4] / 255.0
out = out * (1 - a_core) + np.asarray(core)[..., :3] * a_core            # 白い芯
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
print("保存:", dst)
