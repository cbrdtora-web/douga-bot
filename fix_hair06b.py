"""06番: 左の毛先のまわりを、元の画像の「髪と壁」に戻す(範囲を広げた版)。

前回(fix_hair06.py)は範囲が狭く、毛先の下に、前の修正の跡(ぼやけた灰色のにじみ)が残っていた。
範囲を広げ、元の画像のうち「髪と壁」だけを戻す。紺の服だった所と、肌の所は、今の画像のまま。

使い方: python fix_hair06b.py 元の画像.png 今の画像.png 出力.png
変更するのは、x88〜215, y298〜366 のなか。
"""
import sys

import numpy as np
from PIL import Image, ImageFilter

orig_p, cur_p, dst = sys.argv[1], sys.argv[2], sys.argv[3]
o = np.asarray(Image.open(orig_p).convert("RGB"), dtype=np.float64)
c = np.asarray(Image.open(cur_p).convert("RGB"), dtype=np.float64)
H, W, _ = c.shape
X0, X1, Y0, Y1 = 60, 215, 290, 372

R, G, B = o[:, :, 0], o[:, :, 1], o[:, :, 2]
br = o.mean(axis=2)
navy = ((B - R) > 22) & (br < 110)                                  # 元の画像の紺の服
skin = ((R - B) > 25) & ((R - G) > 8) & (br > 55) & (br < 200)      # 元の画像の肌(茶色)


def grow(mask, n):
    im = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * n + 1))
    return np.asarray(im) > 0


# 紺の服の上の縁は、ほぼ水平な直線(y = -0.121*x + 363.1、x80〜125あたり)。その1画素上より下は、今の画像のまま。
yy0, xx0 = np.mgrid[0:H, 0:W]
navy_geo = (yy0 >= (-0.121 * xx0 + 363.1 - 1.0)) & (xx0 <= 135)
keep_cur = grow(navy_geo, 1) | (grow(navy, 2) & (xx0 <= 140))               # 今の画像のままにする画素(紺の服の位置・肌)
box = np.zeros((H, W), bool)
box[Y0:Y1, X0:X1] = True
use_orig = box & ~keep_cur

m = Image.fromarray((use_orig * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
alpha = np.asarray(m, dtype=np.float64) / 255.0

# 範囲の右と下の端では、なめらかに0へ(貼り合わせの境目を作らない)
xx = np.arange(W)[None, :]
yy = np.arange(H)[:, None]
sm = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
alpha = alpha * sm((X1 - xx) / 14.0) * sm((Y1 - yy) / 22.0) * sm((xx - X0 + 1) / 28.0) * sm((yy - Y0 + 1) / 8.0)
alpha = alpha[:, :, None]

out = c * (1 - alpha) + o * alpha
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
d = np.abs(out - c).max(axis=2) > 0.5
ys, xs = np.nonzero(d)
print("元に戻した画素:", int(d.sum()), "範囲 x%d〜%d y%d〜%d" % (xs.min(), xs.max(), ys.min(), ys.max()))
