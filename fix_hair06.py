"""06番: 左の毛先が、平らに切れている部分を、元の画像の毛先に戻す。

前回までの修正で、元の画像にあった「毛先の細い尖り」が、壁の色で上書きされ、
毛先が平らに切れて、下に白い筋が出ていた。
元の画像(v4_06)のうち、紺の服だった画素だけを、今の画像のまま(壁の色)にして、
それ以外(髪と壁)は、元の画像に戻す。

使い方: python fix_hair06.py 元の画像.png 今の画像.png 出力.png
変更するのは、左の毛先のまわり(x88〜178, y298〜342)だけ。
"""
import sys

import numpy as np
from PIL import Image, ImageFilter

orig_p, cur_p, dst = sys.argv[1], sys.argv[2], sys.argv[3]
o = np.asarray(Image.open(orig_p).convert("RGB"), dtype=np.float64)
c = np.asarray(Image.open(cur_p).convert("RGB"), dtype=np.float64)
H, W, _ = c.shape
X0, X1, Y0, Y1 = 88, 178, 298, 342

box = np.zeros((H, W), bool)
box[Y0:Y1, X0:X1] = True
br = o.mean(axis=2)
# 元の画像で「紺の服」だった画素: 青みが強く(B-R)、あまり明るくない
navy = ((o[:, :, 2] - o[:, :, 0]) > 22) & (br < 110)
# 少し太らせて、紺の縁の混ざった画素も、今の画像(壁)に任せる
nm = Image.fromarray((navy * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
navy = np.asarray(nm) > 0
use_orig = box & ~navy                       # 元の画像に戻す画素
# 下の端(y328〜342)では、元の画像に戻す割合を、なめらかに0にする(貼り合わせの境目を作らない)
yy_ = np.arange(H)[:, None]
fade_y = np.clip((Y1 - yy_) / 14.0, 0, 1)
fade_y = fade_y * fade_y * (3 - 2 * fade_y)
m = Image.fromarray((use_orig * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
alpha = ((np.asarray(m, dtype=np.float64) / 255.0) * fade_y)[:, :, None] * box[:, :, None]
out = c * (1 - alpha) + o * alpha
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
d = np.abs(out - c).max(axis=2) > 0.5
yy, xx = np.nonzero(d)
print("元に戻した画素:", int(d.sum()), "範囲 x%d〜%d y%d〜%d" % (xx.min(), xx.max(), yy.min(), yy.max()))
