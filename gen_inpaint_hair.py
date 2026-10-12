"""顔と髪はそのまま残し、首から下(髪の毛は除く)だけを描き直すプログラム。

使い方:
    python gen_inpaint_hair.py 元画像.png "首から下の指示文(英語)" --top 0.50 --out output/new.png
--top: 画像の上から何割より下を描き直すか。髪の毛(暗い部分)はその位置より下でも残す。
"""
import argparse
import time
from pathlib import Path

import numpy as np
import torch
from diffusers import LCMScheduler, StableDiffusionInpaintPipeline
from PIL import Image, ImageFilter

LCM = "latent-consistency/lcm-lora-sdv1-5"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("prompt")
    ap.add_argument("--top", type=float, required=True)
    ap.add_argument("--hair-until", type=float, default=0.62, help="この割合より上では暗い部分(髪)を残す")
    ap.add_argument("--out", default="output/inpaint_hair.png")
    ap.add_argument("--model", default="SG161222/Realistic_Vision_V5.1_noVAE")
    ap.add_argument("--negative", default="")
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--guidance", type=float, default=1.5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    torch.set_num_threads(4)
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        a.model, torch_dtype=torch.float32, safety_checker=None, use_safetensors=True)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LCM, weight_name="pytorch_lora_weights.safetensors")
    pipe.fuse_lora()

    init = Image.open(a.image).convert("RGB").resize((512, 768))
    arr = np.asarray(init, dtype=np.float64)
    br = arr.mean(axis=2)
    yy = np.arange(768)[:, None] * np.ones((1, 512))
    redo = yy >= 768 * a.top
    # 髪(暗い画素)は、hair_until より上なら残す
    dark = Image.fromarray(((br < 70) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    hair = (np.asarray(dark) > 0) & (yy < 768 * a.hair_until)
    mask = Image.fromarray(((redo & ~hair) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))

    t = time.time()
    img = pipe(a.prompt, image=init, mask_image=mask, negative_prompt=a.negative or None,
               num_inference_steps=a.steps, guidance_scale=a.guidance, strength=1.0,
               width=512, height=768, generator=torch.Generator().manual_seed(a.seed)).images[0]
    Path(a.out).parent.mkdir(exist_ok=True)
    img.save(a.out)
    print(f"できました: {a.out} ({time.time() - t:.0f}秒)")


if __name__ == "__main__":
    main()
