"""顔と髪はそのまま残し、指定した位置より下(首から下)だけを描き直すプログラム(インペイント)。

使い方:
    python gen_inpaint.py 元画像.png "首から下の指示文(英語)" --top 0.40 --out output/new.png
--top は、画像の上から何割の位置より下を描き直すか(0〜1)。あごの少し下に合わせる。
"""
import argparse
import time
from pathlib import Path

import torch
from diffusers import LCMScheduler, StableDiffusionInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter

LCM = "latent-consistency/lcm-lora-sdv1-5"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("prompt")
    ap.add_argument("--top", type=float, required=True)
    ap.add_argument("--out", default="output/inpaint.png")
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
    mask = Image.new("L", init.size, 0)
    ImageDraw.Draw(mask).rectangle((0, int(768 * a.top), 512, 768), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(6))

    t = time.time()
    img = pipe(a.prompt, image=init, mask_image=mask, negative_prompt=a.negative or None,
               num_inference_steps=a.steps, guidance_scale=a.guidance, strength=1.0,
               width=512, height=768, generator=torch.Generator().manual_seed(a.seed)).images[0]
    Path(a.out).parent.mkdir(exist_ok=True)
    img.save(a.out)
    print(f"できました: {a.out} ({time.time() - t:.0f}秒)")


if __name__ == "__main__":
    main()
