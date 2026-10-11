"""首元(首の肌・鎖骨あたり)に残ったインペイントの継ぎ目を、生成AIを使わず画像処理だけで直す。

- fix_02: 首の色味(Lab の a/b)をあごの肌に合わせてなだらかに寄せ、顔と同程度の肌のきめ(粒状感)を足す
- fix_06: y≈361 の微細な横筋を縦方向にならし、左の髪の毛先にある黒いしみを周囲の髪の色で埋める
- fix_07: 右肩で髪と肩の肌が水平に切れている境界を、列ごとに深さの違う境界に作り替える(画像処理版。
  結果が「のこぎり状」に見えたため不採用。既定の出力は v7_07_dignified_warp.png)
- fix_08: 首の黒い横線を拡散補間で消し、無地になった長方形にきめを戻し、境界をまたぐ明るさの段差をなだらかな勾配にする

07 の採用版(output/v7_07_dignified_fixed2.png)は fix_seam_sd.py の部分インペイントで作った:
    image=output/v7_07_dignified_fixed.png, rects=[[340, 396, 402, 424]], strength=0.6, seed=23, feather=4,
    steps=10, guidance=1.5,
    prompt="photo of a young japanese woman with long straight dark brown hair, the ends of her long hair
            falling over the shoulder of a dark green ribbed knit sweater, hair tips blending into the sweater,
            soft window light, shallow depth of field, realistic",
    negative="hand, fingers, arm, bare shoulder, skin patch, blurry, deformed, cartoon, painting, text,
              watermark, straight edge"

入力は上書きせず、「元のファイル名_fixed2.png」に保存する。
使い方:
    python fix_neck.py            # 02, 06, 08(07 の画像処理版は既定では実行しない)
    python fix_neck.py 02 08      # 指定したものだけ
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_seam_pixel import dilate, fill_diffusion, rect_mask, soft_blend  # noqa: E402

OUT = Path(__file__).resolve().parent / "output"


# ---------- 基本の道具 ----------
def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)


def save(img, p):
    Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8)).save(p)
    print("保存:", p)


def erode(mask, r):
    return ~dilate(~mask, r)


def gkernel(sigma):
    r = max(1, int(3 * sigma))
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-x * x / (2 * sigma * sigma))
    return k / k.sum()


def gblur(a, sigma, axes=(0, 1)):
    """ガウスぼかし(反射パディング)。a は (H,W) か (H,W,C)。axes で縦だけ・横だけも選べる。"""
    k = gkernel(sigma)
    r = len(k) // 2
    out = a.astype(np.float32)
    for axis in axes:
        pad = [(0, 0)] * out.ndim
        pad[axis] = (r, r)
        p = np.pad(out, pad, mode="reflect")
        acc = np.zeros_like(out)
        for i, w in enumerate(k):
            sl = [slice(None)] * out.ndim
            sl[axis] = slice(i, i + out.shape[axis])
            acc += w * p[tuple(sl)]
        out = acc
    return out


def smooth1d(v, sigma):
    k = gkernel(sigma)
    r = len(k) // 2
    p = np.pad(v.astype(np.float32), (r, r), mode="reflect")
    return np.convolve(p, k, mode="valid")


def masked_blur(img, mask, sigma):
    """mask 内の画素だけを使った正規化ぼかし(髪や服の色を引き込まない)。"""
    m = mask.astype(np.float32)
    num = gblur(img * m[..., None], sigma)
    den = gblur(m, sigma)[..., None]
    return num / np.maximum(den, 1e-3)


def skin_mask(img):
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    lum = img.mean(axis=2)
    return (R - B > 18) & (R > G) & (lum > 60) & (lum < 215)


def rgb2lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ _M.T / _WHITE
    f = np.where(xyz > 0.008856, np.cbrt(np.maximum(xyz, 1e-9)), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def lab2rgb(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200

    def finv(f):
        return np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787)

    xyz = np.stack([finv(fx), finv(fy), finv(fz)], -1) * _WHITE
    c = xyz @ np.linalg.inv(_M).T
    c = np.where(c > 0.0031308, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055, 12.92 * c)
    return np.clip(c * 255, 0, 255)


_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]], dtype=np.float32)
_WHITE = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)


def grain(shape, std, sigma=0.65, seed=0):
    """肌のきめ用のノイズ(少しぼかして粒を丸くする)。標準偏差 std に正規化。"""
    rng = np.random.default_rng(seed)
    n = gblur(rng.normal(0, 1, shape).astype(np.float32), sigma)
    return n / n.std() * std


def band_weight(H, y0, y1, ramp):
    """行 y0..y1 で 1、その外側 ramp 行でなだらかに 0 になる縦方向の重み (H,)。"""
    y = np.arange(H, dtype=np.float32)
    w = np.clip((y - (y0 - ramp)) / ramp, 0, 1) * np.clip(((y1 + ramp) - y) / ramp, 0, 1)
    return w


# ---------- 02: 首の色味を顔に合わせ、肌のきめを足す ----------
def fix_02(src=OUT / "v6_02_classic.png", dst=OUT / "v6_02_classic_fixed2.png", ratio=1.0, dL=3.0, side=4.0, tex_ratio=0.8):
    """ratio: a/b をあごへ寄せる割合。dL: 首の明度に足す量(あご下の影から徐々に)。
    side: 首の左右の端ほど暗くする量(L 単位、中央 0 → 端 -side)で、平らな首に丸みをつける。"""
    img = load(src)
    H, W, _ = img.shape
    m = skin_mask(img) & rect_mask(img.shape, 190, 278, 320, 326)
    m = dilate(erode(m, 1), 1)
    inner = m
    w = np.minimum(gblur(m.astype(np.float32), 2.0), 1.0)
    w = w * np.clip((np.arange(H, dtype=np.float32)[:, None] - 280) / 12.0, 0, 1)  # あご下の影から徐々に
    w = np.where(dilate(inner, 1), w, 0.0)

    lab = rgb2lab(img)
    chin = lab[255:268, 235:285].reshape(-1, 3).mean(0)
    neck = lab[290:318, 215:295].reshape(-1, 3).mean(0)
    shift = (chin - neck) * np.array([0.0, ratio, ratio])  # a/b だけ寄せる
    print(f"02: あご Lab={chin.round(1)} 首 Lab={neck.round(1)} → シフト={shift.round(2)} dL={dL} side={side}")
    lab2 = lab + shift * w[..., None]
    if dL or side:
        # 行ごとの首の中心と半幅から、左右の端ほど暗くする丸み(放物線)をつくる
        shade = np.zeros((H, W), np.float32)
        for y in range(H):
            xs_ = np.where(inner[y])[0]
            if len(xs_) < 8:
                continue
            cx, hw = (xs_.min() + xs_.max()) / 2.0, max((xs_.max() - xs_.min()) / 2.0, 1.0)
            u = np.clip((np.arange(W) - cx) / hw, -1, 1)
            shade[y] = dL - side * u * u
        shade = gblur(shade, 3.0)
        lab2[..., 0] += shade * w
    out = lab2rgb(lab2)

    # 肌のきめ: 顔の肌(頬)の高周波の強さに合わせる
    hp = img - gblur(img, 1.5)
    face_std = min(hp[180:220, 290:325].std(), hp[180:220, 200:232].std())
    neck_std = hp[290:318, 215:295].std()
    g = float(np.sqrt(max((tex_ratio * face_std) ** 2 - neck_std ** 2, 0.0)))
    print(f"02: 頬のきめ={face_std:.2f} 首のきめ={neck_std:.2f} → 追加する粒状感={g:.2f}")
    out = out + (grain((H, W), g, seed=2) * w)[..., None]
    out = np.where(w[..., None] > 0, out, img)
    save(out, dst)
    return w > 0


# ---------- 06: 微細な横筋としみ ----------
def fix_06(src=OUT / "v7_06_intelligent_fixed.png", dst=OUT / "v7_06_intelligent_fixed2.png"):
    img = load(src)
    H, W, _ = img.shape
    lum = img.mean(axis=2)
    # (a) y≈361 の横筋: 肌の列だけ、縦方向にぼかしてならす
    skin = skin_mask(img) & rect_mask(img.shape, 185, 348, 340, 376)
    vb = gblur(img, 2.5, axes=(0,))
    w = band_weight(H, 358, 364, 4)[:, None] * np.minimum(gblur(skin.astype(np.float32), 1.5), 1.0)
    w = np.where(dilate(skin, 2), w, 0.0)
    out = img * (1 - w[..., None]) + vb * w[..., None]
    # (b) 髪の毛先の黒いしみ: 周囲の髪(壁の明るい画素は除く)の中央値で埋める
    blob = rect_mask(img.shape, 155, 361, 170, 371) & (lum < 36)
    blob = dilate(blob, 1)
    ring = dilate(blob, 3) & ~blob & (lum > 36) & (lum < 52)  # 周囲の髪(影の肌や壁は除く)
    fill = np.median(img[ring].reshape(-1, 3), axis=0)
    print(f"06: しみ画素数={int(blob.sum())} 埋める色={fill.round(0)}")
    filled = out.copy()
    filled[blob] = fill * 0.75 + img[blob] * 0.25
    filled = filled + (grain((H, W), 1.5, seed=6) * blob)[..., None]
    out = soft_blend(out, filled, blob, feather=1)
    changed = (w > 0) | dilate(blob, 2)
    out = np.where(changed[..., None], out, img)
    save(out, dst)
    return changed


# ---------- 07: 右肩の髪と肌の水平な切れ目 ----------
def fix_07(src=OUT / "v7_07_dignified_fixed.png", dst=OUT / "v7_07_dignified_warp.png",
           seed=3, amp=3.0, sigma=3.0, amp_hf=4.0, sigma_hf=1.0, x0=326, x1=399, win_in=6, win_out=14):
    """列 x ごとに「肌(明るい)→髪(黒)」の切れ目の行 y_e を見つけ、その近くだけを縦方向に
    乱数量 d(x) だけずらして(局所的な縦ワープ)、まっすぐな切れ目を自然な境界にする。
    d(x) = なめらかな波(σ=sigma, ±amp) + 毛先らしい細かい揺らぎ(σ=sigma_hf, ±amp_hf)。
    切れ目から win_out 行以上離れた画素は変えない。"""
    img = load(src)
    H, W, _ = img.shape
    lum = img.mean(axis=2)
    xs = np.arange(x0, x1)
    ye = np.full(len(xs), np.nan)
    for i, x in enumerate(xs):
        col = lum[:, x]
        for y in range(390, 424):
            if col[y:y + 4].max() < 40 and col[y - 6:y].mean() > 55:
                ye[i] = y
                break
    ok = ~np.isnan(ye)
    print(f"07: 境界を検出した列数={int(ok.sum())}/{len(xs)}  y_edge の範囲={int(np.nanmin(ye))}..{int(np.nanmax(ye))}")
    ye = np.interp(xs, xs[ok], ye[ok])  # 検出できなかった列は隣から補間
    ye = smooth1d(ye, 1.0)
    rng = np.random.default_rng(seed)
    lf = smooth1d(rng.uniform(-1, 1, len(xs) + 40), sigma)[20:-20]
    lf *= amp / (np.abs(lf).max() + 1e-6)
    hf = smooth1d(rng.uniform(-1, 1, len(xs) + 40), sigma_hf)[20:-20]
    hf *= amp_hf / (np.abs(hf).max() + 1e-6)
    d = lf + hf
    out = img.copy()
    changed = np.zeros((H, W), bool)
    for i, x in enumerate(xs):
        c = ye[i]
        for y in range(int(c) - win_out, int(c) + win_out + 1):
            t = abs(y - c)
            win = 1.0 if t <= win_in else max(0.0, (win_out - t) / (win_out - win_in))
            s = d[i] * win
            if abs(s) < 1e-3:
                continue
            sy = y - s  # ここの画素を sy 行から取ってくる(s>0 なら中身が下へ動く=肌が伸びる)
            y0 = int(np.floor(sy))
            f = sy - y0
            y0 = min(max(y0, 0), H - 2)
            out[y, x] = img[y0, x] * (1 - f) + img[y0 + 1, x] * f
            changed[y, x] = True
    # 列どうしの細かい段差をならす(変えた帯の中だけ、ごく小さな横ぼかし)
    sm = gblur(out, 0.7, axes=(1,))
    wsm = np.minimum(gblur(changed.astype(np.float32), 0.8), 1.0)
    region = dilate(changed, 1)
    out = out * (1 - wsm[..., None]) + sm * wsm[..., None]
    out = np.where(region[..., None], out, img)
    save(out, dst)
    return region


def dilate_v(mask, r):
    """縦方向だけに r 画素太らせる(髪の毛先のような縦長の形は保ったまま、横線の穴だけ埋めるのに使う)。"""
    out = mask.copy()
    h = mask.shape[0]
    for dy in range(-r, r + 1):
        ys = slice(max(0, dy), h + min(0, dy))
        yd = slice(max(0, -dy), h + min(0, -dy))
        out[yd] |= mask[ys]
    return out


def erode_v(mask, r):
    return ~dilate_v(~mask, r)


# ---------- 08: 黒い横線、無地の長方形、明るさの段差 ----------
def fix_08(src=OUT / "v7_08_fresh_fixed.png", dst=OUT / "v7_08_fresh_fixed2.png", ya=362, yb=410, line_thr=6.0):
    img = load(src)
    H, W, _ = img.shape
    lum = img.mean(axis=2)
    skin = skin_mask(img) & rect_mask(img.shape, 255, 350, 392, 416)
    skin_c = erode_v(dilate_v(skin, 6), 6)  # 縦方向クロージング: 横線の穴は埋め、縦長の毛先は肌に含めない
    wskin = np.minimum(gblur(skin_c.astype(np.float32), 1.5), 1.0)
    wskin = np.where(dilate(skin_c, 2), wskin, 0.0)

    # (1) 黒い線: 周囲の肌(低周波)より暗い画素だけをマスクにして、拡散補間で埋める
    LFl = masked_blur(lum[..., None], skin_c, 4.0)[..., 0]
    line = rect_mask(img.shape, 276, 380, 338, 393) & skin_c & (lum < LFl - line_thr)
    line = dilate(line, 1) & rect_mask(img.shape, 274, 379, 340, 394) & skin_c
    print(f"08: 線の画素数={int(line.sum())}")
    out = fill_diffusion(img, line)
    # 前回の補間で無地になった長方形(x322-381,y381-392)と、今回埋めた線に、周囲と同じ程度のきめを足す。
    # きめは「細かい粒(σ1.5未満)」と「粗いまだら(σ1.5〜4)」の2段階で、それぞれ周囲の肌の強さに合わせる。
    b1, b4 = gblur(img, 1.5), gblur(img, 4.0)
    ref = skin_c[358:376, 280:340]
    fine_std = float((img - b1)[358:376, 280:340][ref].std())
    coarse_std = float((b1 - b4)[358:376, 280:340][ref].std())
    print(f"08: 周囲の肌のきめ 細={fine_std:.2f} 粗={coarse_std:.2f}")
    flat = (rect_mask(img.shape, 320, 380, 383, 394) & skin_c) | line
    flat_w = np.minimum(gblur(flat.astype(np.float32), 1.0), 1.0) * dilate(flat, 2)
    # 埋めた帯の縁(無地と周囲の境目)をごく弱く縦方向にならす
    out = out * (1 - flat_w[..., None]) + gblur(out, 1.2, axes=(0,)) * flat_w[..., None]
    tex = grain((H, W), fine_std, sigma=0.65, seed=8) + grain((H, W), coarse_std, sigma=2.0, seed=9)
    out = out + (tex * flat_w)[..., None]
    out = np.where(dilate(flat, 2)[..., None], out, img)

    # (2) 明るさの段差: 行 ya..yb の低周波成分を、両端の値を結ぶなだらかな曲線(smoothstep)に置き換える
    LF = masked_blur(out, skin_c, 3.0)
    LFa = gblur(LF[ya], 2.0, axes=(0,))
    LFb = gblur(LF[yb], 2.0, axes=(0,))
    delta = np.zeros_like(out)
    for y in range(ya, yb + 1):
        t = (y - ya) / (yb - ya)
        s = t * t * (3 - 2 * t)
        delta[y] = LFa * (1 - s) + LFb * s - LF[y]
    delta = gblur(delta, 1.5, axes=(1,))
    w2 = band_weight(H, ya + 3, yb - 3, 4)[:, None] * wskin
    out = out + delta * w2[..., None]
    changed = dilate(flat, 2) | (w2 > 0)
    out = np.where(changed[..., None], out, img)
    save(out, dst)
    return changed


if __name__ == "__main__":
    which = sys.argv[1:] or ["02", "06", "08"]
    for k in which:
        {"02": fix_02, "06": fix_06, "07": fix_07, "08": fix_08}[k]()
