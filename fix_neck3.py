"""3回目の修復(入力: *_fixed2.png → 出力: *_fixed3.png)。生成AIは使わず、画像処理だけで直す。

- fix_02: 首の肌の明るさと色味(Lab の L/a/b)を、あご(唇の下の影を除く)の肌に寄せる。あご下の影は残す。
- fix_06: (a) 髪の後ろの白い羽のような部分を、壁の色(左側の壁に当てはめた平面)に落とす。
         (b) 初回修正のマスク(x<151)の打ち切りで残った、首の影の「四角」の外側を、曲線の首の輪郭で壁に置き換える。
         (c) 毛先を軽くシャープにする。
- fix_07: 初回・前回の SD 修正がぼかした右肩の髪と襟元を原画に戻し、肩にかかる半透明の髪の筋を黒髪に近づけ、
         袖の折り目の真っ黒な部分にリブの質感を続ける。
- fix_08: 初回の SD 修正が描いた襟の上の細い線と、髪の先の茶色いにじみを原画に戻し、残りを拡散補間で馴染ませ、
         首の肌の明るさの段差(y≈394)を直線の勾配に置き換える。

07 の採用版(output/v7_07_dignified_fixed3.png)は、fix_07 の出力(画像処理版)を入力に、fix_seam_sd2x.py
(2 倍に拡大した切り抜きの部分インペイント)で襟元の切れ目だけを描き直したもの:
    crop=[256, 288, 512, 544], rects=[[336, 404, 406, 430]], strength=0.5, seed=1, feather=3, steps=10, guidance=1.5,
    prompt="close-up photo of a young japanese woman's shoulder, tips of her long dark black hair falling over the
            neckline of a dark green ribbed knit sweater, hair ends lying across the knit fabric, soft window light,
            shallow depth of field, realistic",
    negative="hand, fingers, arm, bare shoulder, skin patch, blurry, deformed, cartoon, painting, text, watermark,
              straight edge, blonde hair, pale hair, gray hair"
    (seed 2 は右側に灰色のにじみ、seed 3 は左側に暗いにじみが出たため不採用)

06 の採用版(output/v7_06_intelligent_fixed3.png)も同様に、fix_06 の出力(画像処理版)を入力に、首の影の「四角」
(壁ポケットの右下の角)だけを、髪を含まないマスクで弱く描き直したもの:
    crop=[48, 240, 304, 496], rects=[[146, 350, 180, 382]], strength=0.4, seed=4, feather=3, steps=10, guidance=1.5,
    prompt="photo of a young japanese woman with a dark bob haircut, the side of her neck in soft shadow meeting her
            bare shoulder, plain beige wall behind her, smooth natural skin, soft light, realistic",
    negative="hair, hair strands, extra hair, long hair, blurry, deformed, cartoon, painting, text, watermark,
              bright white, halo, stain, square, hard edge"
    (髪を含むマスク [[146,346,196,382]]・強さ 0.45 の seed 1〜3 は、毛先を肩まで伸ばして描いたため不採用)

入力は上書きせず、「元のファイル名から _fixed2 を除いた名前 + _fixed3.png」に保存する。
使い方:
    python fix_neck3.py            # 02, 06, 07, 08 すべて
    python fix_neck3.py 02 08      # 指定したものだけ
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_seam_pixel import dilate, fill_diffusion, rect_mask, soft_blend  # noqa: E402
from fix_neck import (load, save, erode, gblur, masked_blur, skin_mask, rgb2lab, lab2rgb,  # noqa: E402
                      grain, band_weight, dilate_v, erode_v, smooth1d)

OUT = Path(__file__).resolve().parent / "output"


# ---------- 道具 ----------
def feather_mask(mask, sigma):
    """mask(bool) をぼかした 0..1 の重み。mask の内側は 1 のまま。"""
    a = gblur(mask.astype(np.float32), sigma)
    return np.maximum(np.minimum(a, 1.0), mask.astype(np.float32))


def inner_feather(mask, r, sigma):
    """mask の内側 r 画素だけを使って縁をなだらかにした重み(mask の外は 0)。"""
    return feather_mask(erode(mask, r), sigma) * mask


def fit_plane_color(img, ok, xs, ys):
    """ok==True の画素に、色ごとに平面 (1, x, y) を当てはめ、(xs, ys) の位置の色を返す。"""
    yy, xx = np.where(ok)
    A = np.stack([np.ones(len(xx), np.float32), xx.astype(np.float32), yy.astype(np.float32)], 1)
    B = np.stack([np.ones(len(xs), np.float32), xs.astype(np.float32), ys.astype(np.float32)], 1)
    out = np.zeros((len(xs), 3), np.float32)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A, img[..., c][ok], rcond=None)
        out[:, c] = B @ coef
    return out


def hp_std(img, mask, sigma=1.5):
    """mask 内の高周波(きめ)の標準偏差。"""
    hp = img - gblur(img, sigma)
    return float(hp[mask].std())


def max_filter(a, r):
    out = a.copy()
    h, w = a.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            ys = slice(max(0, dy), h + min(0, dy))
            yd = slice(max(0, -dy), h + min(0, -dy))
            xs = slice(max(0, dx), w + min(0, dx))
            xd = slice(max(0, -dx), w + min(0, -dx))
            out[yd, xd] = np.maximum(out[yd, xd], a[ys, xs])
    return out


# ---------- 02: 首の明るさと色味をあごに寄せる ----------
def fix_02(src=OUT / "v6_02_classic_fixed2.png", dst=OUT / "v6_02_classic_fixed3.png",
           l_ratio=0.85, y_ramp=(282, 300)):
    """首の肌(y>=278)の Lab を、あご(唇の下の影を除いた y263-275)の肌の平均に寄せる。
    L の補正は、あご下の影(y_ramp[0])から y_ramp[1] にかけて徐々に効かせ、暗い縁(髪の影)には効かせない。"""
    img = load(src)
    H, W, _ = img.shape
    m = skin_mask(img) & rect_mask(img.shape, 190, 278, 320, 330)
    m = dilate(erode(m, 1), 1)
    w = np.minimum(gblur(m.astype(np.float32), 2.0), 1.0)
    y = np.arange(H, dtype=np.float32)[:, None]
    w = w * np.clip((y - y_ramp[0]) / float(y_ramp[1] - y_ramp[0]), 0, 1)
    w = np.where(m, w, 0.0)  # 肌の画素だけ(セーターの襟や髪には触れない)

    lab = rgb2lab(img)
    chin_m = skin_mask(img) & rect_mask(img.shape, 228, 263, 262, 275) & (lab[..., 0] > 62)
    neck_m = m & rect_mask(img.shape, 230, 300, 282, 322)
    chin = lab[chin_m].mean(0)
    neck = lab[neck_m].mean(0)
    shift = chin - neck
    shift[0] *= l_ratio
    print(f"02: あご Lab={chin.round(1)} 首 Lab={neck.round(1)} → シフト={shift.round(2)}")
    s = np.clip((lab[..., 0] - 35.0) / 30.0, 0, 1)  # 暗い縁(髪の影)は明るくしない
    lab2 = lab.copy()
    lab2[..., 0] += shift[0] * s * w
    lab2[..., 1] += shift[1] * w
    lab2[..., 2] += shift[2] * w
    out = lab2rgb(lab2)
    out = np.where(w[..., None] > 0, out, img)
    save(out, dst)
    return w > 0


# ---------- 06: 白い羽、首の影の四角、毛先 ----------
def fix_06(src=OUT / "v7_06_intelligent_fixed2.png", dst=OUT / "v7_06_intelligent_fixed3.png",
           sharpen=0.6):
    img = load(src)
    H, W, _ = img.shape
    lum = img.mean(2)
    rb = img[..., 0] - img[..., 2]
    out = img.copy()
    changed = np.zeros((H, W), bool)

    # 壁の色: 毛先と肩の間に見える壁(ポケット x122-152, y350-372)の実測の平均色。
    # 壁は右に向かって少し明るくなる(左端≈180、右端≈220)ので、ごく弱い横方向の勾配を付ける。
    pocket = rect_mask(img.shape, 122, 350, 152, 372) & (lum > 150) & (np.abs(rb) < 24)
    wall_c = img[pocket].mean(0)
    xx = np.arange(W, dtype=np.float32)[None, :]
    wall_img = wall_c[None, None, :] + (0.08 * (xx - 137.0))[..., None] * np.ones((H, 1, 1), np.float32)
    g_std = min(hp_std(img, pocket), 2.2)  # ポケットは縁の画素を含むので、広い壁の実測(≈2.1)で上限
    g = grain((H, W), g_std, sigma=0.7, seed=61)
    print(f"06: 壁の色={wall_c.round(1)} 壁のきめ={g_std:.2f}")

    # (a) 白い羽: 明るくて冷たい白(R-B が小さい)画素を、壁の色(暖色)に置き換える。髪の暗い画素はそのまま。
    reg = rect_mask(img.shape, 170, 296, 218, 332)
    wa = np.clip((lum - 120.0) / 40.0, 0, 1) * np.clip((16.0 - rb) / 8.0, 0, 1) * reg
    print(f"06(a): 置き換える画素数={int((wa > 0.5).sum())} 羽の色={img[wa > 0.5].mean(0).round(0)}"
          f" → 壁の色={wall_img[wa > 0.5].mean(0).round(0)}")
    out = out * (1 - wa[..., None]) + (wall_img + g[..., None]) * wa[..., None]
    changed |= wa > 0

    # (b) 首の影の四角: 正体は「壁ポケット(毛先と肩の間に見える壁)の右下の角」。x>=155 の暗い影は y344→386 まで
    #     連続しており、肩の上端のエッジはポケットの下(x<152)にしかない。光は右から来ている(壁は右ほど明るい)ので、
    #     ポケットの右側(x146〜首の輪郭)を「頭の影が落ちた壁」(壁色×shade、左へ向かって半影の勾配)にし、
    #     首の輪郭 x_sil は x≈181 から肩(150,371)へ丸く広げる。髪(暗くて R-B が小さい)は残し、境界は 3 画素でなだらかに。
    #     → 壁を明るい形で食い込ませる案(くさび・影の壁・丸み)はどれも「切り抜き」に見えるか効かないため不採用。
    #     10 倍で見ると「四角」に見える要因は (i) ポケット右辺の縦の直線的なエッジ(x154-160)、
    #     (ii) 影の矩形(明度≈42)が下の肩の影(≈56)より一段暗く y368-372 で段になること、
    #     (iii) ポケットの角 (156-166, 367-372) にある赤みの少ない暗い筋、の 3 つなので、それぞれ直接直す。
    yy = np.arange(H, dtype=np.float32)[:, None]
    blob_m = rect_mask(img.shape, 160, 352, 176, 366)
    blob_c = img[blob_m].mean(0)
    # (iii) 暗い筋: 影の色(周囲の行の中央値)で埋める
    streak = rect_mask(img.shape, 154, 366, 168, 373) & (lum < 52) & (rb < 22)
    streak = dilate(streak, 1) & rect_mask(img.shape, 153, 365, 169, 374) & (lum < 70)
    ring = dilate(streak, 3) & ~streak & (lum < 75) & (rb > 20)
    fill = np.median(out[ring].reshape(-1, 3), axis=0)
    filled = out.copy()
    filled[streak] = fill
    filled = filled + (grain((H, W), hp_std(img, blob_m), sigma=0.7, seed=62) * streak)[..., None]
    out = soft_blend(out, filled, streak, feather=1)
    print(f"06(b): 筋の画素数={int(streak.sum())} 埋める色={fill.round(0)}")
    changed |= dilate(streak, 2)
    # (ii) 影を下(肩)へ向かってなだらかに明るくし、肩の影(≈56)につなげる(x158-178, y356-372, 肌の画素だけ)
    grad_zone = rect_mask(img.shape, 158, 356, 179, 373) & (rb > 18) & (lum < 70)
    wg = inner_feather(grad_zone, 1, 1.5) * np.clip((yy - 356.0) / 14.0, 0, 1)
    out = out + (wg * 9.0)[..., None] * (blob_c / blob_c.mean())[None, None, :]
    changed |= wg > 0.02
    # (i) 縦のエッジ(x152-162, y350-369)を横方向にぼかして、縁を 4 画素から 6 画素程度に
    edge = rect_mask(img.shape, 151, 350, 163, 370)
    we = inner_feather(edge, 1, 1.5)
    out = out * (1 - we[..., None]) + gblur(out, 1.3, axes=(1,)) * we[..., None]
    changed |= we > 0.02

    # (c) 毛先を軽くシャープに(髪の画素だけ)
    if sharpen > 0:
        hz = rect_mask(img.shape, 117, 318, 186, 352) & (lum < 130)
        hz &= ~dilate(streak | grad_zone | edge, 1)
        wz = feather_mask(erode(hz, 1), 1.5) * (dilate(hz, 1) & rect_mask(img.shape, 117, 287, 285, 405))
        sharp = out + sharpen * (out - gblur(out, 1.2))
        out = out * (1 - wz[..., None]) + sharp * wz[..., None]
        changed |= wz > 0

    out = np.where(changed[..., None], out, img)
    save(out, dst)
    return changed


def warp_edge(img, x0, x1, y_lo, y_hi, amp, sigma, win_in, win_out, seed, edge_thr=40.0):
    """列 x ごとに、y_lo..y_hi の間で「明るい→暗い(lum<edge_thr が 4 行続く)」になる行 y_e を見つけ、
    その近く(±win_out 行)を、なめらかな乱数 d(x)(±amp)だけ縦にずらして、まっすぐな縁をゆるやかに揺らす。
    最後に縁の近くを縦方向に 1 画素だけやわらげる。変えた範囲(bool)も返す。"""
    H, W, _ = img.shape
    lum = img.mean(2)
    xs = np.arange(x0, x1)
    ye = np.full(len(xs), np.nan)
    for i, x in enumerate(xs):
        col = lum[:, x]
        for yv in range(y_lo, y_hi):
            if col[yv:yv + 4].max() < edge_thr and col[yv - 4:yv].mean() > edge_thr + 15:
                ye[i] = yv
                break
    ok = ~np.isnan(ye)
    if ok.sum() < 4:
        return img, np.zeros((H, W), bool)
    ye = np.interp(xs, xs[ok], ye[ok])
    ye = smooth1d(ye, 1.5)
    rng = np.random.default_rng(seed)
    d = smooth1d(rng.uniform(-1, 1, len(xs) + 40), sigma)[20:-20]
    d *= amp / (np.abs(d).max() + 1e-6)
    out = img.copy()
    changed = np.zeros((H, W), bool)
    for i, x in enumerate(xs):
        c = ye[i]
        for yv in range(int(c) - win_out, int(c) + win_out + 1):
            t = abs(yv - c)
            win = 1.0 if t <= win_in else max(0.0, (win_out - t) / float(win_out - win_in))
            s = d[i] * win
            if abs(s) < 1e-3:
                continue
            sy = yv - s
            yb = int(np.floor(sy))
            f = sy - yb
            yb = min(max(yb, 0), H - 2)
            out[yv, x] = img[yb, x] * (1 - f) + img[yb + 1, x] * f
            changed[yv, x] = True
    # 縁の近く(±2 行)だけ、縦方向にごく弱くやわらげる
    near = np.zeros((H, W), bool)
    for i, x in enumerate(xs):
        c = int(round(ye[i]))
        near[max(c - 2, 0):c + 3, x] = True
    sm = gblur(out, 0.7, axes=(0,))
    wn = np.minimum(gblur(near.astype(np.float32), 0.8), 1.0)
    out = out * (1 - wn[..., None]) + sm * wn[..., None]
    changed |= wn > 0.02
    print(f"07: 縁を検出した列数={int(ok.sum())}/{len(xs)} y_e の範囲={int(np.nanmin(ye))}..{int(np.nanmax(ye))}")
    return out, changed


# ---------- 07: 右肩の髪・襟元・袖の折り目 ----------
def fix_07(src=OUT / "v7_07_dignified_fixed2.png", org=OUT / "v7_07_dignified.png",
           dst=OUT / "v7_07_dignified_fixed3.png", k_dark=1.3, rib_gain=1.5, rib_amp=2.5):
    img = load(src)
    o = load(org)
    H, W, _ = img.shape
    changed = np.zeros((H, W), bool)

    # 1) SD でぼけた部分(肩の髪の筋・襟元・袖の上端)を原画に戻す
    r1 = rect_mask(img.shape, 326, 387, 414, 446)
    a = inner_feather(r1, 3, 2.0)
    out = img * (1 - a[..., None]) + o * a[..., None]
    changed |= r1

    # 2) 肩にかかる半透明の髪の筋を暗く(肌の明るさ S に対して、暗い画素ほどさらに暗く)。
    #    斑点が出ないよう、明るさは少しぼかしたものから計算し、比率を画素に掛ける。
    lum = out.mean(2)
    lum_b = gblur(lum, 0.8)
    S = gblur(max_filter(lum_b, 3), 2.0)
    zone = rect_mask(img.shape, 330, 387, 404, 417)
    y = np.arange(H, dtype=np.float32)[:, None]
    ramp = np.clip((y - 387) / 11.0, 0, 1)  # y=387 で 0 → y=398 で 1(上の筋と急に変わらないように)
    notgreen = (out[..., 0] >= out[..., 1] - 2) & (lum_b > 25)
    depth = np.clip((S - lum_b - 15.0) / 15.0, 0, 1)  # 肌より 15 以上暗い画素から効き始める
    new_lum = np.maximum(S - k_dark * (S - lum_b), 12.0)
    ratio = np.where(zone & notgreen, new_lum / np.maximum(lum_b, 1.0), 1.0)
    wz = inner_feather(zone, 2, 1.5) * ramp * depth
    ratio = 1.0 + (ratio - 1.0) * wz
    out = out * ratio[..., None]
    changed |= wz > 0

    # 3) 襟元の水平な切れ目: 肌→セーターの縁を、列ごとに ±amp 画素のゆるやかな揺らぎで上下にずらし、1 画素やわらげる
    out, wwarp = warp_edge(out, 340, 394, 404, 424, amp=2.0, sigma=5.0, win_in=3, win_out=8, seed=7)
    changed |= wwarp

    # 4) 袖の折り目の真っ黒な部分: 明るさは持ち上げず(持ち上げると範囲の縁に帯が出る)、
    #    リブ(横方向の帯域成分)を増幅し、真っ黒な所には右のリブと位相を合わせた弱いリブを合成する
    lum = out.mean(2)
    fz = rect_mask(img.shape, 350, 398, 408, 486)
    wf = inner_feather(fz, 7, 4.0)
    bp = gblur(lum, 1.0, axes=(1,)) - gblur(lum, 4.0, axes=(1,))
    dark = np.clip((60.0 - lum) / 40.0, 0, 1)
    P = 10.0
    xs_ref = np.arange(380, 410, dtype=np.float32)
    xx = np.arange(W, dtype=np.float32)[None, :]
    phase = np.zeros(H, np.float32)
    for yv in range(398, 482):
        v = bp[yv, 380:410]
        c = (v * np.cos(2 * np.pi * xs_ref / P)).sum()
        s_ = (v * np.sin(2 * np.pi * xs_ref / P)).sum()
        phase[yv] = np.arctan2(s_, c)
    phase = gblur(phase[:, None], 2.0, axes=(0,))[:, 0]
    rib = np.cos(2 * np.pi * xx / P - phase[:, None])
    black = np.clip((8.0 - lum) / 6.0, 0, 1)  # lum<2 で 1、lum>8 で 0
    sleeve = np.clip((xx - 368.0) / 8.0, 0, 1) * np.ones((H, 1), np.float32)  # 袖側(x>=376)だけ。体側には合成しない
    new_lum = lum + wf * sleeve * (rib_gain * dark * bp + rib_amp * black * rib)
    new_lum = np.maximum(new_lum, 1.0)
    shade = out[fz & (lum > 6) & (lum < 16)].mean(0)  # 折り目の暗い緑の色味
    shade = shade / shade.mean()
    delta = (new_lum - lum)
    out = out + delta[..., None] * shade[None, None, :]
    print(f"07: 折り目の色味={shade.round(2)} リブの振幅(最大)={float(np.abs(delta * (wf > 0)).max()):.1f}")
    changed |= wf > 0

    out = np.where(changed[..., None], out, img)
    save(out, dst)
    return changed


# ---------- 08: 襟の上の線、髪の先のにじみ、首の帯 ----------
def fix_08(src=OUT / "v7_08_fresh_fixed2.png", org=OUT / "v7_08_fresh.png",
           dst=OUT / "v7_08_fresh_fixed3.png", ya=376, yb=406):
    img = load(src)
    o = load(org)
    H, W, _ = img.shape
    changed = np.zeros((H, W), bool)

    # 1) 原画の復元: 襟の上の細い線(x>=383, 初回の SD 修正が襟を上に広げて描いたもの)と、
    #    髪の先の左下(x374-383, y<391: 原画では黒い髪の先端)。
    #    髪の先の左下は、角が四角く出ないよう (374,383)→(384,389) の斜めで切る。
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    r2 = rect_mask(img.shape, 374, 366, 384, 391) & (xx >= 374.0 + np.clip(yy - 383.0, 0, None) * 1.7)
    r = rect_mask(img.shape, 383, 366, 466, 406) | r2
    a = inner_feather(r, 2, 1.5)
    a = np.where(r2, np.minimum(a, inner_feather(r, 3, 2.5)), a)  # 髪の左の縁はさらになだらかに
    out = img * (1 - a[..., None]) + o * a[..., None]
    changed |= r

    # 2) にじみ(x360-378, y366-392): 髪の左の縁は原画でも 10 画素ほどのやわらかい縁なので、形(明るさ)はそのまま、
    #    オレンジがかった色だけを「その行の肌の色と髪の黒の線形混合」(明るさを保つ)に置き換える。
    #    髪の下端(x>=386, y>=384)の下は襟なので、そこは「襟の色と髪の黒の線形混合」にする。
    zone = rect_mask(img.shape, 360, 366, 388, 394)
    zone2 = rect_mask(img.shape, 386, 384, 440, 395)
    lum = out.mean(2)
    hair_c = out[rect_mask(img.shape, 388, 368, 398, 380)].mean(0)
    hair_l = float(hair_c.mean())
    recol = out.copy()
    for yv in range(366, 395):
        skin_c = out[yv, 346:358].mean(0)
        skin_l = float(skin_c.mean())
        alpha = np.clip((skin_l - lum[yv]) / max(skin_l - hair_l, 1.0), 0, 1)
        recol[yv, :388] = skin_c[None, :] * (1 - alpha[:388])[:, None] + hair_c[None, :] * alpha[:388][:, None]
        collar_c = out[398:402, 410:440].reshape(-1, 3).mean(0)
        collar_l = float(collar_c.mean())
        alpha2 = np.clip((collar_l - lum[yv]) / max(collar_l - hair_l, 1.0), 0, 1)
        recol[yv, 386:] = collar_c[None, :] * (1 - alpha2[386:])[:, None] + hair_c[None, :] * alpha2[386:][:, None]
    rb = out[..., 0] - out[..., 2]
    wz = np.maximum(inner_feather(zone, 1, 1.0), inner_feather(zone2, 1, 1.0))
    wz = wz * np.clip((rb - 12.0) / 10.0, 0, 1) * np.clip((85.0 - lum) / 15.0, 0, 1)
    skin_ref = skin_mask(out) & rect_mask(img.shape, 300, 366, 350, 392)
    tex = grain((H, W), hp_std(out, skin_ref), seed=81)
    recol = recol + (tex * np.clip((recol.mean(2) - 40.0) / 40.0, 0, 1))[..., None]
    out = out * (1 - wz[..., None]) + recol * wz[..., None]
    print(f"08: にじみの色を置き換えた画素数={int((wz > 0.3).sum())} 髪の色={hair_c.round(0)}")
    changed |= wz > 0.02
    # 髪の先端の左下の角(斜めの切り口が 8 倍で小さな段に見える)を、ごく弱くぼかしてなめらかに
    corner = rect_mask(img.shape, 372, 378, 392, 393)
    wc = inner_feather(corner, 2, 1.5)
    out = out * (1 - wc[..., None]) + gblur(out, 1.0) * wc[..., None]
    changed |= wc > 0.02

    # 3) 帯: 行 ya..yb の低周波成分を、両端を結ぶ直線の勾配に置き換える(肌だけ)
    skin = skin_mask(out) & rect_mask(img.shape, 296, 368, 378, 412)
    skin_c = erode_v(dilate_v(skin, 6), 6)
    wskin = np.minimum(gblur(skin_c.astype(np.float32), 1.5), 1.0)
    wskin = np.where(dilate(skin_c, 2), wskin, 0.0)
    LF = masked_blur(out, skin_c, 2.5)
    LFa = gblur(LF[ya], 2.0, axes=(0,))
    LFb = gblur(LF[yb], 2.0, axes=(0,))
    delta = np.zeros_like(out)
    for yv in range(ya, yb + 1):
        t = (yv - ya) / float(yb - ya)
        delta[yv] = LFa * (1 - t) + LFb * t - LF[yv]
    delta = gblur(delta, 1.5, axes=(1,))
    w2 = band_weight(H, ya + 3, yb - 3, 4)[:, None] * wskin
    w2 = np.where(rect_mask(img.shape, 296, ya - 4, 378, yb + 5), w2, 0.0)
    out = out + delta * w2[..., None]
    print(f"08: 帯の補正量 最大={float(np.abs(delta.mean(2) * w2).max()):.1f}")
    changed |= w2 > 0

    out = np.where(changed[..., None], out, img)
    save(out, dst)
    return changed


if __name__ == "__main__":
    which = sys.argv[1:] or ["02", "06", "07", "08"]
    for k in which:
        {"02": fix_02, "06": fix_06, "07": fix_07, "08": fix_08}[k]()
