"""文章(プロンプト)から画像を作るプログラム。GPUなし(CPUのみ)で動く。

事前に必要なこと:
    環境の設定「Network access」の許可ドメインに huggingface.co を追加する
    (モデルを最初の1回だけダウンロードするため)

使い方:
    python gen_image.py "a realistic photo of a ginger scottish fold cat sitting in a cardboard box, cozy room, soft light"
    python gen_image.py "プロンプト" --out output/cat1.png --seed 3
"""
import argparse
import time
from pathlib import Path

import torch
from diffusers import DiffusionPipeline, LCMScheduler

# 商用利用できるライセンス(CreativeML OpenRAIL-M)のモデル + 高速化用のLCM-LoRA
BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
LCM = "latent-consistency/lcm-lora-sdv1-5"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--out", default="output/gen.png")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=6)
    ap.add_argument("--size", type=int, default=512)
    a = ap.parse_args()

    torch.set_num_threads(4)
    pipe = DiffusionPipeline.from_pretrained(BASE, torch_dtype=torch.float32, safety_checker=None)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LCM, weight_name="pytorch_lora_weights.safetensors")
    pipe.fuse_lora()

    t = time.time()
    img = pipe(a.prompt, num_inference_steps=a.steps, guidance_scale=1.0,
               width=a.size, height=a.size,
               generator=torch.Generator().manual_seed(a.seed)).images[0]
    Path(a.out).parent.mkdir(exist_ok=True)
    img.save(a.out)
    print(f"できました: {a.out} ({time.time() - t:.0f}秒)")


if __name__ == "__main__":
    main()
