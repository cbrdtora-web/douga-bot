"""インペイントの継ぎ目を、生成AIを使わず画像処理だけで直すための補助関数集。

- fill_diffusion: マスク部分を周囲の画素から滑らかに補間して埋める(壁などの平坦な背景向け)
- vertical_interp: 指定した帯を、上下の行の間で縦方向に線形補間して置き換える(細い横線の除去向け)
- add_grain: 補間で平坦になった部分に、周囲と同程度の粒状感を足す

使い方(例):
    python fix_seam_pixel.py 06   # 06 の修復を実行して output/v7_06_intelligent_fixed.png に保存
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def dilate(mask, r):
    """2値マスクを r 画素ぶん太らせる(正方形カーネル)。"""
    m = mask.copy()
    out = m.copy()
    h, w = m.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            ys = slice(max(0, dy), h + min(0, dy))
            yd = slice(max(0, -dy), h + min(0, -dy))
            xs = slice(max(0, dx), w + min(0, dx))
            xd = slice(max(0, -dx), w + min(0, -dx))
            out[yd, xd] |= m[ys, xs]
    return out


def fill_diffusion(img, mask, iters=4000):
    """mask==True の画素を、周囲の画素からの拡散(ラプラス補間)で埋める。img は float32 (H,W,3)。"""
    ys, xs = np.where(mask)
    y0, y1 = max(0, ys.min() - 8), min(img.shape[0], ys.max() + 9)
    x0, x1 = max(0, xs.min() - 8), min(img.shape[1], xs.max() + 9)
    sub = img[y0:y1, x0:x1].copy()
    m = mask[y0:y1, x0:x1]
    known = ~m
    # 初期値: 既知画素の平均
    sub[m] = sub[known].mean(axis=0)
    for _ in range(iters):
        nb = (np.roll(sub, 1, 0) + np.roll(sub, -1, 0) + np.roll(sub, 1, 1) + np.roll(sub, -1, 1)) / 4.0
        sub[m] = nb[m]
    out = img.copy()
    out[y0:y1, x0:x1] = sub
    return out


def vertical_interp(img, x0, x1, y0, y1):
    """行 y0..y1-1 (列 x0..x1-1) を、行 y0-1 と行 y1 の間の縦方向線形補間で置き換える。"""
    out = img.copy()
    top = img[y0 - 1, x0:x1].astype(np.float32)
    bot = img[y1, x0:x1].astype(np.float32)
    n = y1 - y0 + 1
    for i, y in enumerate(range(y0, y1)):
        t = (i + 1) / n
        out[y, x0:x1] = top * (1 - t) + bot * t
    return out


def add_grain(img, mask, ref_box, seed=0):
    """mask 部分に、ref_box=(x0,y0,x1,y1) の高周波成分と同程度の標準偏差のノイズを足す。"""
    rx0, ry0, rx1, ry1 = ref_box
    ref = img[ry0:ry1, rx0:rx1]
    blur = (np.roll(ref, 1, 0) + np.roll(ref, -1, 0) + np.roll(ref, 1, 1) + np.roll(ref, -1, 1)) / 4.0
    sd = float((ref - blur).std())
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, sd, img.shape).astype(np.float32)
    out = img.copy()
    out[mask] += noise[mask]
    return out


def soft_blend(orig, fixed, mask, feather=1):
    """mask を少しぼかして、修正画像を元画像に合成する(マスク外は元画像のまま)。"""
    a = mask.astype(np.float32)
    for _ in range(feather):
        a = (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1) + a * 4) / 8.0
    a = np.maximum(a, mask.astype(np.float32))  # マスク内は必ず 1
    return orig * (1 - a[..., None]) + fixed * a[..., None]


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float32)


def save(img, path):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)
    print("保存:", path)


def rect_mask(shape, x0, y0, x1, y1):
    m = np.zeros(shape[:2], bool)
    m[y0:y1, x0:x1] = True
    return m


def fill_plane(img, mask, fit_box, lum_min=140):
    """mask 部分を、fit_box=(x0,y0,x1,y1) 内の明るい(壁の)画素に当てはめた2次曲面の色で埋める。
    周囲の暗い画素(髪など)に引きずられないので、平坦な壁の穴埋めに向く。"""
    x0, y0, x1, y1 = fit_box
    sub = img[y0:y1, x0:x1]
    lum = sub.mean(axis=2)
    ok = (lum > lum_min) & ~mask[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    def design(x, y):
        x = (x - 256) / 256.0; y = (y - 384) / 384.0
        return np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], axis=-1)
    A = design(xx[ok].astype(np.float32), yy[ok].astype(np.float32))
    out = img.copy()
    ys, xs = np.where(mask)
    B = design(xs.astype(np.float32), ys.astype(np.float32))
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A, sub[..., c][ok], rcond=None)
        out[ys, xs, c] = B @ coef
    return out


def extend_hair_down(img, x0, x1, y_top, y_max, bg_lum_max=70, L_min=10, L_max=26, seed=1):
    """髪の毛先が水平に切れている部分を、各列ごとに下へ伸ばして先細りに見せる。
    列 x ごとに、y_top..y_max の範囲で髪(明るさ > bg_lum_max)が終わる行を探し、
    その上の髪の色を鏡写しで下に延ばしつつ、透明度を下げていく。"""
    out = img.copy()
    lum = img.mean(axis=2)
    rng = np.random.default_rng(seed)
    # 列ごとの延長長さ(隣どうし滑らかに)
    L = rng.uniform(L_min, L_max, x1 - x0)
    for _ in range(3):
        L = (np.roll(L, 1) + L + np.roll(L, -1)) / 3.0
    for i, x in enumerate(range(x0, x1)):
        col = lum[y_top:y_max, x]
        hair = np.where(col > bg_lum_max)[0]
        if len(hair) == 0:
            continue
        y_end = y_top + hair.max()  # 最後の髪の行
        n = int(L[i])
        for k in range(1, n + 1):
            y = y_end + k
            if y >= img.shape[0]:
                break
            src_y = max(y_end - k, y_top)  # 鏡写し
            t = k / n
            a = (1 - t) ** 1.6
            # 先細り: 隣の列との平均で細く
            out[y, x] = img[src_y, x] * a + img[y, x] * (1 - a)
    return out


def fix_06(src="output/v7_06_intelligent.png", dst="output/v7_06_intelligent_fixed.png"):
    """左の髪の毛先が「鳥」のような形になっている部分と、その下の灰色の影(x52-150, y347-386)を
    壁の色(2次曲面で近似)で埋める。肌(R-B差が大きい)と首の横の髪(x>150)は触らない。
    仕上げの馴染ませは fix_seam_sd.py(強さ0.45)で行う。"""
    img = load(src)
    lum = img.mean(axis=2)
    rb = img[..., 0] - img[..., 2]
    wall_like = (lum > 150) & (rb < 24)
    skin_like = rb >= 24
    m = rect_mask(img.shape, 52, 347, 151, 394) & ~wall_like & ~skin_like
    m = dilate(m, 1) & rect_mask(img.shape, 50, 346, 151, 395) & ~skin_like
    fixed = fill_plane(img, m, (0, 320, 152, 404), lum_min=150)
    fixed = add_grain(fixed, m, (10, 330, 50, 390))
    out = soft_blend(img, fixed, m, feather=1)
    save(out, dst)
    return m


def fix_04(src="output/v6_04_cute.png", dst="output/v6_04_cute_fixed.png"):
    """左の首の横の灰色のにじみ(x152-182, y321-335)を壁で埋める。"""
    img = load(src)
    lum = img.mean(axis=2)
    m = rect_mask(img.shape, 150, 320, 181, 336) & (lum < 188)
    m = dilate(m, 1) & rect_mask(img.shape, 148, 319, 182, 337)
    fixed = fill_diffusion(img, m)
    fixed = add_grain(fixed, m, (100, 280, 150, 320))
    out = soft_blend(img, fixed, m, feather=1)
    save(out, dst)
    return m


def fix_08(src="output/v7_08_fresh.png", dst="output/v7_08_fresh_fixed.png"):
    """首の下の細い黒い横線(x326-380, y383-391)を周囲から補間して消す。"""
    img = load(src)
    lum = img.mean(axis=2)
    m = rect_mask(img.shape, 322, 381, 381, 392) & (lum < 110)
    m = dilate(m, 1) & rect_mask(img.shape, 320, 380, 381, 393)
    fixed = fill_diffusion(img, m)
    fixed = add_grain(fixed, m, (300, 350, 350, 380))
    out = soft_blend(img, fixed, m, feather=1)
    save(out, dst)
    return m


def fix_09(src="output/v8_09_glam.png", dst="output/v8_09_glam_fixed.png"):
    """右: 髪の中に出た肌色のパッチ(x446-502, y350-363)を、上の髪を鏡写しにして埋める。
    左: 髪の輪郭が y≈358-364 で水平に段になっている部分を、斜めの輪郭になるよう壁で埋める。"""
    img = load(src)
    lum = img.mean(axis=2)
    out = img.copy()
    # 右のパッチ: 周囲の髪の色で滑らかに埋める(質感は後で SD の低強度インペイントで整える)
    m1 = rect_mask(img.shape, 444, 349, 504, 364) & (lum > 95)
    m1 = dilate(m1, 1) & rect_mask(img.shape, 442, 348, 506, 365)
    filled = fill_diffusion(img, m1)
    out = soft_blend(out, filled, m1, feather=1)
    # 左の段差: 行 y=352..380 で、x < 110 - (y-352)*40/28 の髪を壁で埋める
    m2 = np.zeros(img.shape[:2], bool)
    for y in range(352, 381):
        xe = int(round(110 - (y - 352) * 40 / 28))
        m2[y, 30:xe] = lum[y, 30:xe] < 120
    m2 = dilate(m2, 1) & rect_mask(img.shape, 30, 350, 112, 383)
    fixed = fill_plane(img, m2, (0, 300, 110, 420), lum_min=110)
    fixed = add_grain(fixed, m2, (5, 300, 60, 400))
    out = soft_blend(out, fixed, m2, feather=1)
    save(out, dst)
    return m1 | m2


def trim_hair_uneven(img, x0, x1, y_top, y_max, bg_lum_max=70, d_max=18, seed=2, dark_hair=False):
    """髪の毛先が水平に切れている部分を、列ごとに違う深さで削って(下の生地を鏡写しで上に写す)、
    毛先の高さを不揃いにする。dark_hair=True のときは「明るさ < bg_lum_max」を髪とみなす。"""
    out = img.copy()
    lum = img.mean(axis=2)
    rng = np.random.default_rng(seed)
    n = x1 - x0
    d = rng.uniform(0, d_max, n)
    for _ in range(2):
        d = (np.roll(d, 1) + d + np.roll(d, -1)) / 3.0
    for i, x in enumerate(range(x0, x1)):
        col = lum[y_top:y_max, x]
        hair = np.where(col < bg_lum_max)[0] if dark_hair else np.where(col > bg_lum_max)[0]
        if len(hair) == 0:
            continue
        y_end = y_top + hair.max()
        depth = int(d[i])
        for k in range(0, depth + 2):
            y = y_end - k
            src_y = y_end + 2 + k  # 切れ目の下のセーターを鏡写し
            if src_y >= img.shape[0] or y < y_top:
                break
            a = 1.0 if k >= 1 else 0.5
            out[y, x] = img[src_y, x] * a + img[y, x] * (1 - a)
    return out


def fix_07_trim(src="output/v7_07_dignified.png", dst="output/v7_07_dignified_trim.png"):
    """右肩にかかる髪が y≈415 で水平に切れている部分(x332-398)の毛先を不揃いに削る(SD の前処理)。"""
    img = load(src)
    fixed = trim_hair_uneven(img, 332, 400, 400, 420, bg_lum_max=70, d_max=18)
    save(fixed, dst)
    return rect_mask(img.shape, 330, 396, 400, 420)


fix_07 = fix_07_trim


if __name__ == "__main__":
    which = sys.argv[1:] or ["06", "04", "08", "09", "07"]
    for w in which:
        {"06": fix_06, "04": fix_04, "08": fix_08, "09": fix_09, "07": fix_07}[w]()
