#!/usr/bin/env bash
# 新しいセッションで、人物画像を作れる状態にするためのスクリプト。
# 使い方:  bash scripts/setup_env.sh          (ライブラリを入れる)
#          bash scripts/setup_env.sh --models (モデルも取りに行く。事前にネット許可が必要)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1. ライブラリ =="
pip install -q -r requirements.txt
pip install -q torch diffusers transformers accelerate peft safetensors huggingface_hub

if [ "${1:-}" != "--models" ]; then
  echo "モデルの確認だけ行います(取りに行くときは --models)"
  python3 - <<'PY'
from pathlib import Path
hub = Path.home() / ".cache/huggingface/hub"
for m in ["stablediffusionapi--chilloutmix", "SG161222--Realistic_Vision_V5.1_noVAE",
          "latent-consistency--lcm-lora-sdv1-5", "stable-diffusion-v1-5--stable-diffusion-v1-5"]:
    print(("あり  " if (hub / f"models--{m}").exists() else "なし  ") + m)
PY
  exit 0
fi

echo "== 2. モデル取得(初回だけ。許可ドメインが必要: docs/IMAGE_PIPELINE.md の「許可」参照) =="
python3 - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("stablediffusionapi/chilloutmix")               # 柔らかいアイドル風の顔。服の指定を守らないことがある
snapshot_download("SG161222/Realistic_Vision_V5.1_noVAE")         # 服は安全に作れる。写真っぽい顔
snapshot_download("latent-consistency/lcm-lora-sdv1-5")           # 高速化(LCM-LoRA)
PY
echo "完了。以後は HF_HUB_OFFLINE=1 で動かせます。ネット許可(huggingface関連ドメイン)は外してOK。"
