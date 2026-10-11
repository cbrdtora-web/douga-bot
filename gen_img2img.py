"""元の画像の顔の雰囲気を残して、服や体形だけを描き直すプログラム(img2img)。

使い方:
    python gen_img2img.py 元画像.png "新しい指示文(英語)" --strength 0.6 --out output/new.png
strength が小さいほど元の画像に近く、大きいほど大きく変わる。
"""
import argparse
import time
from pathlib import Path

import torch
from diffusers import LCMScheduler, StableDiffusionImg2ImgPipeline
from PIL import Image

LCM = "latent-consistency/lcm-lora-sdv1-5"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("prompt")
    ap.add_argument("--out", default="output/img2img.png")
    ap.add_argument("--model", default="SG161222/Realistic_Vision_V5.1_noVAE")
    ap.add_argument("--negative", default="")
    ap.add_argument("--strength", type=float, default=0.6)
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--guidance", type=float, default=1.5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    torch.set_num_threads(4)
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        a.model, torch_dtype=torch.float32, safety_checker=None, use_safetensors=True)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LCM, weight_name="pytorch_lora_weights.safetensors")
    pipe.fuse_lora()

    init = Image.open(a.image).convert("RGB").resize((512, 768))
    t = time.time()
    img = pipe(a.prompt, image=init, negative_prompt=a.negative or None, strength=a.strength,
               num_inference_steps=a.steps, guidance_scale=a.guidance,
               generator=torch.Generator().manual_seed(a.seed)).images[0]
    Path(a.out).parent.mkdir(exist_ok=True)
    img.save(a.out)
    print(f"できました: {a.out} ({time.time() - t:.0f}秒)")


if __name__ == "__main__":
    main()
