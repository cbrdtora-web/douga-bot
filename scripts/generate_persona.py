"""キャラクター設定(characters/characters.json)から、人物画像を新規生成するプログラム。

使い方(リポジトリの直下で):
    python scripts/generate_persona.py 07 --seeds 701 702 703        # 07番を3パターン
    python scripts/generate_persona.py 02 06 --seeds 1 2 3 4 --out-prefix v30
    python scripts/generate_persona.py 08 --seeds 281 --level relaxed  # 肩出し・浅いVを許可
    python scripts/generate_persona.py --list                         # 一覧

--level strict  : 丸首で首元までしっかり覆う(安全寄り)
--level relaxed : 肩が少し出る・浅いV字まで許可(既定。ユーザーが了承した基準)
--model chillout|rv : chillout=柔らかいアイドル風(既定)、rv=Realistic Vision(服は安全、顔は写真っぽい)

画像全体を新しく作るだけで、部分的な修正はしない(ユーザーの禁止事項)。
できた画像は必ず目で確認すること(docs/IMAGE_PIPELINE.md のチェックリスト)。
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = {"chillout": "stablediffusionapi/chilloutmix", "rv": "SG161222/Realistic_Vision_V5.1_noVAE"}

# 出さないもの(共通)。露出・子どもっぽさ・絵柄ずれ・腕交差などを避ける
NEG_BASE = ("nsfw, nude, naked, cleavage, breasts, plunging, deep neckline, low-cut, revealing, strap, straps, "
            "tank top, camisole, bra, see-through, sheer, transparent, tight clothing, form-fitting, large breasts, "
            "busty, sexy, child, childlike, little girl, baby, teenager, teen, underage, schoolgirl, school uniform, "
            "pink hair, colored hair, green hair, purple hair, monochrome, black and white, "
            "(anime, cartoon, drawing, 3d render:1.3), text, watermark, deformed, bad anatomy, extra fingers, "
            "blurry, low quality, two faces, duplicate, freckles, blotchy skin, "
            "crossed arms, folded arms, hand on arm, hand on shoulder, hugging herself, hands")
NEG_STRICT_EXTRA = ", v-neck, scoop neck, wide neckline, boat neck, bare shoulders, bare collarbone, off-shoulder"

PROMPT_HEAD = ("photo, adult woman in her mid 20s, head and shoulders portrait, arms straight down out of frame, "
               "slim petite build, small bust, natural black or dark brown hair, natural skin tone, glossy smooth skin, "
               "youthful soft face, gentle round eyes, soft rounded cheeks, soft indoor light")
NECK = {"strict": "loose thick opaque knit sweater with a high round crew neckline close to the neck covering the collarbone and shoulders",
        "relaxed": "loose oversized knit sweater, neckline either round or a shallow V, shoulders may be slightly bare"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="キャラ番号(例: 02 06)")
    ap.add_argument("--seeds", nargs="+", type=int, default=[1])
    ap.add_argument("--level", choices=["strict", "relaxed"], default="relaxed")
    ap.add_argument("--model", choices=list(MODELS), default="chillout")
    ap.add_argument("--out-prefix", default="v30")
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    data = json.load(open(ROOT / "characters/characters.json", encoding="utf-8"))
    chars = {c["id"]: c for c in data["characters"]}
    if a.list or not a.ids:
        for c in chars.values():
            print(c["id"], c["name"], c["type"], "|", c["image_style"])
        return

    neg = NEG_BASE + (NEG_STRICT_EXTRA if a.level == "strict" else "")
    env = dict(os.environ, HF_HUB_OFFLINE="1")   # ネットに出ない(モデルは取得済みの前提)
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    for cid in a.ids:
        c = chars[cid]
        for s in a.seeds:
            prompt = f"{PROMPT_HEAD}, {NECK[a.level]}, {c['image_style']}"
            out = out_dir / f"{a.out_prefix}_{cid}_{c['key']}_s{s}.png"
            cmd = [sys.executable, str(ROOT / "gen_image.py"), prompt, "--model", MODELS[a.model], "--negative", neg,
                   "--guidance", "1.5", "--steps", str(a.steps), "--size", "512", "--height", "768",
                   "--seed", str(s), "--out", str(out)]
            print(">>", out.name, flush=True)
            subprocess.run(cmd, check=True, cwd=ROOT, env=env)


if __name__ == "__main__":
    main()
