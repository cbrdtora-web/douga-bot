"""採用した画像(02・06・07・08)を、同じ指示文・同じ seed で作り直して、元の画像と同じか確かめる。

使い方:  python scripts/reproduce_adopted.py 08        → output/repro_08.png ができ、元画像との差を表示
レシピは characters/exact_recipes.json。モデルは取得済みであること(scripts/setup_env.sh)。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def main():
    cid = sys.argv[1]
    rec = next(r for r in json.load(open(ROOT / "characters/exact_recipes.json", encoding="utf-8"))["recipes"] if r["id"] == cid)
    out = ROOT / "output" / f"repro_{cid}.png"
    cmd = [sys.executable, str(ROOT / "gen_image.py"), rec["prompt"], "--model", rec["model"], "--negative", rec["negative"],
           "--guidance", str(rec["guidance"]), "--steps", str(rec["steps"]), "--size", str(rec["size"][0]),
           "--height", str(rec["size"][1]), "--seed", str(rec["seed"]), "--out", str(out)]
    subprocess.run(cmd, check=True, cwd=ROOT, env=dict(os.environ, HF_HUB_OFFLINE="1"))
    a = np.asarray(Image.open(out).convert("RGB"), dtype=float)
    b = np.asarray(Image.open(ROOT / rec["file"]).convert("RGB"), dtype=float)
    print("元画像との平均差(0なら完全一致):", round(float(np.abs(a - b).mean()), 3))


if __name__ == "__main__":
    main()
