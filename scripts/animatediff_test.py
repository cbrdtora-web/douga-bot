"""AnimateDiff で、1枚の絵から短い動画を作る検証(CPU)。 使い方: python scripts/animatediff_test.py 画像.png 出力.mp4 [枚数16] [幅384] [高さ576] [strength0.7] [steps6]"""
import sys
import time

import torch
from diffusers import AnimateDiffVideoToVideoPipeline, LCMScheduler, MotionAdapter
from diffusers.utils import export_to_video
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 16
W = int(sys.argv[4]) if len(sys.argv) > 4 else 384
H = int(sys.argv[5]) if len(sys.argv) > 5 else 576
strength = float(sys.argv[6]) if len(sys.argv) > 6 else 0.7
steps = int(sys.argv[7]) if len(sys.argv) > 7 else 6
torch.set_num_threads(4)
t0 = time.time()
adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-3", torch_dtype=torch.float32, variant="fp16")
pipe = AnimateDiffVideoToVideoPipeline.from_pretrained("Meina/MeinaMix_V11", motion_adapter=adapter, torch_dtype=torch.float32,
                                                        safety_checker=None, use_safetensors=True)
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config, beta_schedule="linear")
pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5", weight_name="pytorch_lora_weights.safetensors")
pipe.fuse_lora()
print("読み込み:", round(time.time() - t0), "秒", flush=True)
img = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
video = [img] * n
t1 = time.time()
out = pipe(video=video, prompt="masterpiece, best quality, anime illustration, 1girl, adult woman, hair blowing gently in the wind, gentle smile, blinking, sparkles floating",
           negative_prompt="lowres, bad anatomy, bad hands, text, watermark, worst quality, low quality, blurry, child",
           num_inference_steps=steps, guidance_scale=1.5, strength=strength, width=W, height=H,
           generator=torch.Generator().manual_seed(1)).frames[0]
print("生成:", round(time.time() - t1), "秒 /", n, "コマ", flush=True)
export_to_video(out, dst, fps=8)
print("保存:", dst, flush=True)
