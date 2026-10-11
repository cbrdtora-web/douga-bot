"""02番: あごの下の「首が切れて見える」部分を、AIで描き直して、あごと首を自然につなぐ。

あごの輪郭に沿った形の範囲だけを、周囲の絵(256x256の切り抜きを2倍に拡大)を手がかりに描き直し、
範囲の中だけを元の画像に合成する。顔(あごの輪郭より上)と、範囲の外は、1画素も変えない。

使い方: python fix_chin_sd.py 入力.png 出力.png シード
"""
import sys

import numpy as np
import torch
from diffusers import LCMScheduler, StableDiffusionInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter

src, dst, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
torch.set_num_threads(4)
BOX = (150, 190, 406, 446)  # 256x256 の切り抜き
# あごの輪郭の下側から首のつけ根までの範囲(元の画像の座標)
POLY = [(202, 262), (216, 268), (228, 277), (238, 283), (262, 283), (274, 278),
        (283, 271), (294, 265), (294, 300), (202, 300)]

img = Image.open(src).convert("RGB")
crop = img.crop(BOX)
mask = Image.new("L", crop.size, 0)
ImageDraw.Draw(mask).polygon([(x - BOX[0], y - BOX[1]) for x, y in POLY], fill=255)
big = crop.resize((512, 512), Image.LANCZOS)
big_mask = mask.resize((512, 512), Image.LANCZOS).filter(ImageFilter.GaussianBlur(5))

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "SG161222/Realistic_Vision_V5.1_noVAE", torch_dtype=torch.float32, safety_checker=None, use_safetensors=True)
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5", weight_name="pytorch_lora_weights.safetensors")
pipe.fuse_lora()
NEG = ("choker, necklace, black band, ribbon, collar, scarf, nsfw, nude, cleavage, bare shoulders, "
       "text, watermark, deformed, bad anatomy, blurry, low quality, extra fingers")
out = pipe("photo, a woman's smooth neck under the jawline, soft natural shadow under the chin, "
           "long dark hair on both sides, natural skin, sweater collar below",
           image=big, mask_image=big_mask, negative_prompt=NEG, num_inference_steps=10,
           guidance_scale=1.5, strength=0.85, width=512, height=512,
           generator=torch.Generator().manual_seed(seed)).images[0]

small = out.resize((256, 256), Image.LANCZOS)
alpha = mask.filter(ImageFilter.GaussianBlur(1.5))
comp = Image.composite(small, crop, alpha)
res = img.copy()
res.paste(comp, BOX[:2])
res.save(dst)
a = np.asarray(img, dtype=np.int32)
b = np.asarray(res, dtype=np.int32)
d = np.abs(a - b).max(axis=2) > 0
yy, xx = np.nonzero(d)
print("できました: %s 変更した画素 %d 範囲 x%d〜%d y%d〜%d" % (dst, d.sum(), xx.min(), xx.max(), yy.min(), yy.max()))
