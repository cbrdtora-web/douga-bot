"""02番: 首の左の端を、赤い線の位置(x≈203)まで、左へずらす。

新しい色は足さず、首の左側の部分(端から右の約30画素)を、各行ごとに、横にだけ引き伸ばして、
首の左の端がx=203に来るようにする。影や肌の質感は、元のままつながる。
あごの輪郭(y264より上)と、肩(y300より下)には、影響しないよう、上下はなめらかに弱める。

使い方: python fix_neck_shift.py 入力.png 出力.png
"""
import sys

import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(src).convert("RGB"), dtype=np.float64)
g = a.mean(axis=2)
H, W, _ = a.shape
TARGET = 203          # 首の左のライン(ユーザーの赤い線)
XEND = 250            # 引き伸ばす範囲の右端(ここから右は動かさない)
Y0, Y1, FADE_IN, FADE_OUT = 258, 314, 3, 24
RAMP = 9              # 首の縁の、黒から肌へ変わるやわらかい部分の幅(これも一緒に動かす)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


# 行ごとの「首の左の端」: x196以降で、明るさが40を超える位置(となりの画素との間で、小数まで求める)
def find_edge(y):
    x = 196
    while x < XEND and g[y, x] <= 40:
        x += 1
    if x == 196:
        return 196.0
    lo, hi = g[y, x - 1], g[y, x]
    return x - 1 + (40 - lo) / max(hi - lo, 1e-6)


ys = np.arange(Y0 - 6, Y1 + 6)
raw = np.array([find_edge(int(y)) for y in ys])
# ばらつきを消すため、3次の曲線に当てはめてなめらかにする(外れ値は中央値フィルタで先に弱める)
med = np.array([np.median(raw[max(0, i - 4):i + 5]) for i in range(len(raw))])
coef = np.polyfit(ys, med, 3)
edge_s = {int(y): float(np.polyval(coef, y)) for y in ys}

out = a.copy()
for y in range(Y0, Y1):
    w = smooth((y - Y0) / FADE_IN) * smooth((Y1 - y) / FADE_OUT)
    e = edge_s[y]
    shift = (e - TARGET) * w                 # この行で、左へずらす量(画素)
    if shift <= 0.2:
        continue
    A = e - RAMP                             # 元の縁のやわらかい部分の、外側の始まり(まだ黒)
    A2 = A - shift                           # ずらしたあとの、その位置
    for x in range(int(np.floor(A2)), XEND):
        # 出力の x に対応する元の x: [A2, XEND] を [A, XEND] へ、なめらかに対応させる
        s = A + (x - A2) * (XEND - A) / (XEND - A2)
        s = min(max(s, 0), W - 1)
        i = int(np.floor(s)); f = s - i
        j = min(i + 1, W - 1)
        out[y, x] = a[y, i] * (1 - f) + a[y, j] * f

Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
d = np.abs(out - a).max(axis=2) > 0.5
yy, xx = np.nonzero(d)
print("変更した画素:", int(d.sum()), "範囲 x%d〜%d y%d〜%d" % (xx.min(), xx.max(), yy.min(), yy.max()))
