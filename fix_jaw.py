"""02番: あごの左右にある「切れ」を、周囲の肌の色でなめらかに埋めて直す。

- 左: あごの輪郭の内側に、途中で終わる細い黒い筋(傷のような線)がある → 周囲より暗い画素を肌で埋める
- 右: あごの下の黒い細長い影が、尖った形で途中で切れている → 黒い先端を、肌から髪へ向かうなだらかな影にする

使い方: python fix_jaw.py 入力.png 出力.png
変更するのは、あごの左右の狭い範囲(左 x203〜232,y258〜284 / 右 x266〜288,y262〜286)だけ。
"""
import sys

import numpy as np

from fix_seam_pixel import add_grain, dilate, fill_diffusion, load, save, soft_blend

src, dst = sys.argv[1], sys.argv[2]
img = load(src)
g = img.mean(axis=2)
H, W = g.shape
orig = img.copy()

# ---- 左: 細い黒い筋 ----
x0, x1, y0, y1 = 203, 233, 258, 285
med = np.zeros((H, W))
for y in range(y0, y1):
    for x in range(x0, x1):
        med[y, x] = np.median(g[y - 4:y + 5, x - 4:x + 5])
box = np.zeros((H, W), bool)
box[y0:y1, x0:x1] = True
streak = box & (g < med - 14) & (g > 50)
streak = dilate(streak, 1) & box
print("左: 埋める画素", int(streak.sum()))
if streak.any():
    img = fill_diffusion(img, streak, iters=1500)
    img = add_grain(img, streak, (236, 268, 262, 282), seed=5)

# ---- 右: 黒い影の尖った先端 ----
rx0, rx1, ry0, ry1 = 266, 288, 262, 287
rbox = np.zeros((H, W), bool)
rbox[ry0:ry1, rx0:rx1] = True
tip = rbox & (g < 80)
tip = dilate(tip, 1) & rbox
print("右: 埋める画素", int(tip.sum()))
if tip.any():
    img = fill_diffusion(img, tip, iters=2500)
    img = add_grain(img, tip, (236, 268, 262, 282), seed=6)

mask = (streak | tip)
out = soft_blend(orig, img, mask, feather=1)
save(out, dst)
d = np.abs(out - orig).max(axis=2) > 0.5
yy, xx = np.nonzero(d)
print("変更した画素:", int(d.sum()), "範囲 x%d〜%d y%d〜%d" % (xx.min(), xx.max(), yy.min(), yy.max()))
