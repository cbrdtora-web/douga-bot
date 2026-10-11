"""猫の4コマ漫画をゼロから描いて、1枚の縦長画像にするプログラム。

使い方:
    python make_manga.py                 # output/manga_4koma.png ができる
    python make_manga.py --color "#FFB3C7"   # 吹き出しの色を変える
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
K = 2                       # 2倍で描いて縮小(なめらかにする)
PW, PH = 1000, 430          # 1コマの大きさ
FUR, FUR_D, LINE = "#F4A64E", "#D9822B", "#3B2A20"
BOX, BOX_D, FLAP = "#D2A36A", "#B5834A", "#C8453F"


def font(size):
    return ImageFont.truetype(FONT, size * K)


def S(*v):
    return [x * K for x in v]


def poly(d, pts, fill, outline=LINE, w=5):
    d.polygon([(x * K, y * K) for x, y in pts], fill=fill, outline=outline, width=w * K)


def oval(d, x, y, rx, ry, fill, w=5):
    d.ellipse(S(x - rx, y - ry, x + rx, y + ry), fill=fill, outline=LINE, width=w * K)


def line(d, pts, w=5):
    d.line([(x * K, y * K) for x, y in pts], fill=LINE, width=w * K, joint="curve")


def eyes(d, x, y, mood, gap=62):
    for sx in (-1, 1):
        ex = x + sx * gap
        if mood == "happy":      # にっこり目 ^ ^
            line(d, [(ex - 20, y + 8), (ex, y - 12), (ex + 20, y + 8)], 8)
        elif mood == "sleepy":   # とろんとした目
            line(d, [(ex - 20, y), (ex + 20, y)], 8)
        elif mood == "wow":      # びっくり目
            oval(d, ex, y, 24, 28, "white", 5)
            oval(d, ex, y, 9, 11, LINE, 1)
        else:                    # ふつうの目
            oval(d, ex, y, 15, 20, LINE, 1)
            oval(d, ex + 4, y - 6, 5, 6, "white", 1)


def cat_head(d, x, y, mood="normal", r=125):
    # 折れ耳(スコティッシュフォールド風)
    poly(d, [(x - r * .85, y - r * .55), (x - r * .55, y - r * 1.0), (x - r * .15, y - r * .8)], FUR)
    poly(d, [(x + r * .85, y - r * .55), (x + r * .55, y - r * 1.0), (x + r * .15, y - r * .8)], FUR)
    oval(d, x, y, r * 1.1, r, FUR)
    for i in (-1, 0, 1):         # おでこのしま模様
        line(d, [(x + i * 30, y - r * .98), (x + i * 30, y - r * .68)], 6)
    eyes(d, x, y - 8, mood)
    poly(d, [(x - 13, y + 24), (x + 13, y + 24), (x, y + 38)], "#E8798A", w=3)
    mouth = {"happy": 22, "wow": 0}.get(mood, 10)
    if mood == "wow":
        oval(d, x, y + 58, 11, 14, "#8A2E3A", 4)
    else:
        line(d, [(x, y + 38), (x, y + 48)], 4)
        line(d, [(x - mouth * 1.3, y + 50 + (mouth / 3 if mood == "happy" else 0)), (x, y + 48),
                 (x + mouth * 1.3, y + 50 + (mouth / 3 if mood == "happy" else 0))], 4)
    for sx in (-1, 1):           # ひげ
        for dy in (-6, 8):
            line(d, [(x + sx * 78, y + 34 + dy), (x + sx * 150, y + 24 + dy * 2.2)], 3)
    if mood == "happy":          # ほっぺ
        oval(d, x - 92, y + 36, 20, 12, "#F8A8A8", 1)
        oval(d, x + 92, y + 36, 20, 12, "#F8A8A8", 1)


HX, HY = 400, 260  # 猫の部品(スプライト)の中での頭の中心


def cat_sprite(mood="normal", body=True, r=125):
    """猫1匹ぶんを透明な画像に描く。あとで好きな大きさ・位置に貼れる。"""
    img = Image.new("RGBA", (1000 * K, 700 * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if body:
        tail = [(HX + 120, HY + 190), (HX + 240, HY + 170), (HX + 290, HY + 90), (HX + 260, HY + 20)]
        line(d, tail, 30)
        d.line([(x * K, y * K) for x, y in tail], fill=FUR, width=18 * K, joint="curve")
        oval(d, HX, HY + 150, 150, 105, FUR)
        oval(d, HX - 60, HY + 235, 40, 22, FUR)
        oval(d, HX + 60, HY + 235, 40, 22, FUR)
    cat_head(d, HX, HY, mood, r)
    return img


def put_cat(img, hx, hy, s, **kw):
    sp = cat_sprite(**kw)
    sp = sp.resize((int(sp.width * s), int(sp.height * s)), Image.LANCZOS)
    img.alpha_composite(sp, (int((hx - HX * s) * K), int((hy - HY * s) * K)))


def box(d, x, y, w=330, h=200, open_front=True):
    poly(d, [(x - w / 2, y), (x + w / 2, y), (x + w / 2 - 15, y + h), (x - w / 2 + 15, y + h)], BOX)
    poly(d, [(x - w / 2 - 20, y - 50), (x - w / 2 + 40, y - 6), (x - w / 2, y)], FLAP, w=4)
    poly(d, [(x + w / 2 + 20, y - 50), (x + w / 2 - 40, y - 6), (x + w / 2, y)], FLAP, w=4)
    line(d, [(x - w / 2, y), (x + w / 2, y)], 6)


def sfx(d, text, x, y, size, color="#E8453C", rot=0):
    """効果音の文字(ふち取りで太く)"""
    f = font(size)
    tmp = Image.new("RGBA", (int(size * K * (len(text) + 1)), int(size * K * 1.6)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((tmp.width / 2, tmp.height / 2), text, font=f, fill=color, anchor="mm",
            stroke_width=7 * K, stroke_fill="white")
    td.text((tmp.width / 2, tmp.height / 2), text, font=f, fill=color, anchor="mm",
            stroke_width=2 * K, stroke_fill=LINE)
    tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=True)
    d._image.alpha_composite(tmp, (int(x * K - tmp.width / 2), int(y * K - tmp.height / 2)))


def bubble(d, text, cx, cy, tail_to, size=44, color="#FFE066"):
    f = font(size)
    tw = d.textlength(text, font=f) / K
    rx, ry = tw / 2 + 50, size * 0.5 + 32
    tx, ty = tail_to
    ang = math.atan2(ty - cy, tx - cx)
    bx, by = cx + math.cos(ang) * rx * .6, cy + math.sin(ang) * ry * .6
    px, py = -math.sin(ang) * 28, math.cos(ang) * 28
    tail = [(bx + px, by + py), (bx - px, by - py), (tx, ty)]
    d.ellipse(S(cx - rx - 6, cy - ry - 6, cx + rx + 6, cy + ry + 6), fill=LINE)
    d.polygon([(x * K, y * K) for x, y in
               [(bx + px * 1.25, by + py * 1.25), (bx - px * 1.25, by - py * 1.25),
                (tx + math.cos(ang) * 8, ty + math.sin(ang) * 8)]], fill=LINE)
    d.ellipse(S(cx - rx, cy - ry, cx + rx, cy + ry), fill=color)
    d.polygon([(x * K, y * K) for x, y in tail], fill=color)
    d.text((cx * K, cy * K), text, font=f, fill=LINE, anchor="mm", stroke_width=1 * K, stroke_fill=LINE)


def speed_lines(d, cx, cy, r0, r1, n=28):
    for i in range(n):
        a = 2 * math.pi * i / n
        line(d, [(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                 (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], 3)


def panel(bg):
    img = Image.new("RGBA", (PW * K, PH * K), bg)
    d = ImageDraw.Draw(img)
    d._image = img
    return img, d


def build(color):
    panels = []
    # ① 箱を発見
    img, d = panel("#FFF6E5")
    d.rectangle(S(0, 345, PW, PH), fill="#E9D3B0")
    box(d, 760, 215, 300, 150)
    put_cat(img, 260, 190, 0.62, mood="wow")
    speed_lines(d, 260, 200, 120, 190, 18)
    sfx(d, "！", 440, 150, 90, rot=10)
    bubble(d, "あっ、箱だ！", 330, 52, (290, 120), 40, color)
    panels.append(img)
    # ② くんくん
    img, d = panel("#FFF6E5")
    d.rectangle(S(0, 345, PW, PH), fill="#E9D3B0")
    box(d, 720, 215, 300, 150)
    put_cat(img, 430, 190, 0.62, mood="normal")
    sfx(d, "くんくん", 640, 150, 56, "#3A8DDE", -8)
    bubble(d, "ふむ…いいにおい", 250, 52, (380, 125), 38, color)
    panels.append(img)
    # ③ ジャンプ
    img, d = panel("#FFF1D6")
    speed_lines(d, 500, 215, 250, 520, 40)
    box(d, 500, 300, 340, 140)
    put_cat(img, 500, 140, 0.6, mood="happy")
    sfx(d, "ぴょん！", 800, 100, 72, "#E8453C", 12)
    panels.append(img)
    # ④ オチ
    img, d = panel("#FFF6E5")
    d.rectangle(S(0, 345, PW, PH), fill="#E9D3B0")
    put_cat(img, 500, 225, 0.78, mood="happy", body=False)
    box(d, 500, 265, 440, 165)
    sfx(d, "ニャー", 820, 130, 62, "#E8453C", 8)
    bubble(d, "ここ、落ち着くにゃ…", 290, 55, (430, 160), 40, color)
    panels.append(img)

    margin, gap, head = 40, 24, 120
    W = PW + margin * 2
    H = head + (PH + gap) * 4 + margin
    sheet = Image.new("RGBA", (W * K, H * K), "white")
    sd = ImageDraw.Draw(sheet)
    sd.text((W / 2 * K, head / 2 * K + 5 * K), "はこねこ日記", font=font(64), fill=LINE,
            anchor="mm", stroke_width=2 * K, stroke_fill=LINE)
    for i, p in enumerate(panels):
        y = head + i * (PH + gap)
        sheet.alpha_composite(p, (margin * K, y * K))
        sd.rectangle(S(margin, y, margin + PW, y + PH), outline=LINE, width=8 * K)
    return sheet.resize((W, H), Image.LANCZOS).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--color", default="#FFE066", help="吹き出しの色")
    ap.add_argument("--out", default="output/manga_4koma.png")
    a = ap.parse_args()
    Path(a.out).parent.mkdir(exist_ok=True)
    build(a.color).save(a.out)
    print("できました:", a.out)


if __name__ == "__main__":
    main()
