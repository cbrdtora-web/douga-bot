"""9人のキャラクターを、アニメ画風で新規生成するプログラム(全体を新しく作る。部分修正はしない)。

  パターンA(実物風アニメ): 半実写の陰影・窓の逆光・ぼけた背景の、アニメ絵
  パターンB(完全アニメ)  : 明るい色・大きな目・華やかなアニメの衣装

使い方(リポジトリの直下で):
    python scripts/generate_anime.py                       # 全員・A/B・各3候補(54枚)
    python scripts/generate_anime.py --ids 07 --patterns A B --seeds 1 2 3
    python scripts/generate_anime.py --list

モデル(取得済みの前提。docs/IMAGE_PIPELINE.md 参照): Meina/MeinaMix_V11(ライセンス CreativeML OpenRAIL-M)
全員20代半ばの「大人」。幼い子どもに見える語や制服は使わない。腕は体の横に下ろす(交差は失敗しやすい)。
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "Meina/MeinaMix_V11"

# id: (髪, 目, Aの服, Aの場面, Bの衣装)
SPEC = {
    "01": ("wavy shoulder-length dark brown hair", "soft brown", "beige knit sweater with a shallow V-neck", "warm beige room with sunlight",
           "cozy cream and brown fantasy dress with a big brown ribbon, frills and a flower hair clip"),
    "02": ("long straight black hair with bangs", "dark", "gray knit sweater", "quiet gray room, soft window light",
           "elegant white and navy lolita dress with lace and a ribbon"),
    "03": ("black bob hair with blunt bangs", "bright brown", "white knit sweater", "bright light room, sunny window",
           "cheerful yellow and orange idol stage costume with ribbons and sparkles"),
    "04": ("chin-length black bob hair", "brown", "cream knit sweater", "warm cafe light with bokeh",
           "sweet pink and cream frilly dress with a huge ribbon"),
    "05": ("medium-length soft dark brown hair", "brown", "gray knit turtleneck sweater", "beige room, soft afternoon light",
           "mint and gray cozy fantasy outfit with a big cardigan and a ribbon"),
    "06": ("straight black bob hair with bangs", "dark blue", "cream knit sweater", "beige wall, soft window light",
           "navy cape and white blouse with gold buttons and a ribbon"),
    "07": ("(long straight black hair:1.3) with bangs", "green", "dark green knit turtleneck sweater", "warm golden sunlight through a window",
           "dark green and gold elegant dress with a big ribbon and frills"),
    "08": ("soft medium-long light brown hair", "light blue", "light blue knit sweater with a shallow V-neck", "bright soft green background, daylight",
           "sky blue and white fairy-like dress with ribbons"),
    "09": ("long dark brown hair", "amber", "gray knit sweater", "warm golden light with bokeh",
           "purple and orange halloween witch costume with a big hat, ribbons and pumpkin ornaments"),
}
NEG = ("lowres, bad anatomy, bad hands, extra digits, extra fingers, text, watermark, worst quality, low quality, blurry, "
       "child, childlike, loli, shota, young girl, school uniform, nsfw, cleavage, breasts, bare shoulders, revealing, "
       "see-through, crossed arms, folded arms, hand on arm, hugging herself, ugly, deformed")
NEG_A = NEG + ", photo, photorealistic, 3d render"
NEG_B = NEG + ", realistic, 3d, mature face, serious, complex background"


def prompt(pattern, cid):
    hair, eyes, outfit_a, scene_a, outfit_b = SPEC[cid]
    if pattern == "A":
        return ("masterpiece, best quality, anime illustration, semi-realistic shading, adult woman 25 years old, "
                f"{hair}, {eyes} eyes, gentle smile, {outfit_a}, {scene_a}, strong backlight rim light, soft bokeh background, "
                "smooth soft skin shading, highly detailed, upper body, arms down"), NEG_A
    return ("masterpiece, best quality, 1girl, adult woman 25 years old, tall slender, cute, "
            f"big sparkling {eyes} eyes, happy open smile, {hair}, {outfit_b}, colorful pastel glow background, "
            "sparkles, simple background, upper body, arms down, anime illustration"), NEG_B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=list(SPEC))
    ap.add_argument("--patterns", nargs="*", default=["A", "B"])
    ap.add_argument("--seeds", nargs="*", type=int, default=[1, 2, 3])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for cid in SPEC:
            print(cid, "|", prompt("A", cid)[0][:110], "...")
        return
    env = dict(os.environ, HF_HUB_OFFLINE="1")
    (ROOT / "output").mkdir(exist_ok=True)
    for cid in a.ids:
        for pat in a.patterns:
            p, neg = prompt(pat, cid)
            for s in a.seeds:
                out = ROOT / "output" / f"anime_{cid}_{pat}_s{s}.png"
                if out.exists():
                    continue
                subprocess.run([sys.executable, str(ROOT / "gen_image.py"), p, "--model", MODEL, "--negative", neg,
                                "--guidance", "1.5", "--steps", "8", "--size", "512", "--height", "768",
                                "--seed", str(s), "--out", str(out)], check=True, cwd=ROOT, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"CHAR {cid} done", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
