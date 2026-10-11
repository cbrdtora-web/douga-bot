"""小さな継ぎ目を、2倍に拡大した切り抜きで Stable Diffusion の部分インペイント(低い強さ)にかけ、
縮小して元画像に合成するプログラム(fix_seam_sd.py の高解像度版)。

- 256x256 の切り抜きを 512x512 に拡大して描き直すので、細い髪の筋などの細部が崩れにくい。
- マスクの外は元画像の画素をそのまま使う(合成はマスクをぼかして行う)。
- 種(seed)を複数指定すると、候補を seed ごとに別ファイルに保存する。

使い方:
    HF_HUB_OFFLINE=1 python fix_seam_sd2x.py jobs.json
jobs.json の形式(リスト):
    [{"image": "output/a.png", "out": "scratch/a_sd",           # 出力は out + f"_s{seed}.png"
      "crop": [x0, y0, x1, y1],                                # 256x256 の切り抜き(元画像の座標)
      "rects": [[x0, y0, x1, y1], ...],                        # 描き直す長方形(元画像の座標)
      "prompt": "...", "negative": "...",
      "strength": 0.5, "seeds": [1, 2, 3], "feather": 3, "steps": 10, "guidance": 1.5}]
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from diffusers import LCMScheduler, StableDiffusionInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter

LCM = "latent-consistency/lcm-lora-sdv1-5"
MODEL = "SG161222/Realistic_Vision_V5.1_noVAE"
SCALE = 2


def load_pipe():
    torch.set_num_threads(4)
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        MODEL, torch_dtype=torch.float32, safety_checker=None, use_safetensors=True)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LCM, weight_name="pytorch_lora_weights.safetensors")
    pipe.fuse_lora()
    pipe.set_progress_bar_config(disable=True)
    return pipe


def make_mask(size, rects, feather):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in rects:
        d.rectangle((x0, y0, x1, y1), fill=255)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    return mask


def run_job(pipe, job):
    full = Image.open(job["image"]).convert("RGB")
    cx0, cy0, cx1, cy1 = job["crop"]
    assert cx1 - cx0 == 256 and cy1 - cy0 == 256, job["crop"]
    crop = full.crop((cx0, cy0, cx1, cy1))
    init = crop.resize((256 * SCALE, 256 * SCALE), Image.LANCZOS)
    feather = job.get("feather", 3)
    rects_c = [[(x0 - cx0) * SCALE, (y0 - cy0) * SCALE, (x1 - cx0) * SCALE, (y1 - cy0) * SCALE]
               for x0, y0, x1, y1 in job["rects"]]
    mask_hi = make_mask(init.size, rects_c, feather * SCALE)
    # 合成用のマスク(元解像度)
    rects_full = [[x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0] for x0, y0, x1, y1 in job["rects"]]
    mask_lo = np.asarray(make_mask(crop.size, rects_full, feather)).astype(np.float32)[..., None] / 255.0
    for seed in job.get("seeds", [0]):
        t = time.time()
        gen = pipe(job["prompt"], image=init, mask_image=mask_hi,
                   negative_prompt=job.get("negative") or None,
                   num_inference_steps=job.get("steps", 10), guidance_scale=job.get("guidance", 1.5),
                   strength=job.get("strength", 0.5), width=init.size[0], height=init.size[1],
                   generator=torch.Generator().manual_seed(seed)).images[0]
        gen.save(f"{job['out']}_s{seed}_raw512.png")
        g = np.asarray(gen.resize(crop.size, Image.LANCZOS)).astype(np.float32)
        o = np.asarray(crop).astype(np.float32)
        merged = o * (1 - mask_lo) + g * mask_lo
        out = np.asarray(full).astype(np.float32).copy()
        out[cy0:cy1, cx0:cx1] = merged
        Path(job["out"]).parent.mkdir(parents=True, exist_ok=True)
        dst = f"{job['out']}_s{seed}.png"
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
        print(f"できました: {dst} strength={job.get('strength', 0.5)} seed={seed} ({time.time() - t:.0f}秒)", flush=True)


def main():
    jobs = json.load(open(sys.argv[1]))
    t = time.time()
    pipe = load_pipe()
    print(f"モデル読み込み {time.time() - t:.0f}秒", flush=True)
    for job in jobs:
        run_job(pipe, job)


if __name__ == "__main__":
    main()
