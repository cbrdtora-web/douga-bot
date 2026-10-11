"""インペイントの継ぎ目を、Stable Diffusion の部分インペイント(低い強さ)で直すプログラム。

- 指定した小さな長方形だけをマスクにして描き直し、マスクの外は元画像の画素をそのまま使う(合成)。
- モデルは1回だけ読み込み、ジョブ(JSON)を順に処理する。

使い方:
    HF_HUB_OFFLINE=1 python fix_seam_sd.py jobs.json
jobs.json の形式(リスト):
    [{"image": "output/a.png", "out": "output/a_fixed.png",
      "rects": [[x0, y0, x1, y1], ...], "prompt": "...", "negative": "...",
      "strength": 0.5, "seed": 0, "feather": 4, "steps": 10, "guidance": 1.5,
      "raw": "任意: 合成前の生成画像の保存先"}]
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
    init = Image.open(job["image"]).convert("RGB")
    assert init.size == (512, 768), init.size
    feather = job.get("feather", 4)
    mask = make_mask(init.size, job["rects"], feather)
    t = time.time()
    gen = pipe(job["prompt"], image=init, mask_image=mask,
               negative_prompt=job.get("negative") or None,
               num_inference_steps=job.get("steps", 10), guidance_scale=job.get("guidance", 1.5),
               strength=job.get("strength", 0.5), width=512, height=768,
               generator=torch.Generator().manual_seed(job.get("seed", 0))).images[0]
    if job.get("raw"):
        gen.save(job["raw"])
    # マスク内だけを合成(マスクの外は元画像のまま)
    a = np.asarray(mask).astype(np.float32)[..., None] / 255.0
    o = np.asarray(init).astype(np.float32)
    g = np.asarray(gen.resize(init.size)).astype(np.float32)
    out = o * (1 - a) + g * a
    Path(job["out"]).parent.mkdir(exist_ok=True)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(job["out"])
    print(f"できました: {job['out']} strength={job.get('strength', 0.5)} ({time.time() - t:.0f}秒)", flush=True)


def main():
    jobs = json.load(open(sys.argv[1]))
    t = time.time()
    pipe = load_pipe()
    print(f"モデル読み込み {time.time() - t:.0f}秒", flush=True)
    for job in jobs:
        run_job(pipe, job)


if __name__ == "__main__":
    main()
