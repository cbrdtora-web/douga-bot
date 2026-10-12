"""キャラクターごとの声(日本語読み上げ・オフライン)の見本を作る。

使い方:  python scripts/persona_voice.py 07 --style B   # 07番・完全アニメの声 → output/voices/voice_07_B.wav
         python scripts/persona_voice.py 07 --text "好きなセリフ"
声の高さ(half_tone)と速さ(speed)は characters/characters.json の voice に記録してある。
make_video.py の make_voice() と同じ pyopenjtalk を使う。
"""
import argparse
import json
import wave
from pathlib import Path

import numpy as np
import pyopenjtalk

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--text", default="")
    ap.add_argument("--style", choices=["real", "A", "B"], default="real", help="real=実写版、A=実物風アニメ、B=完全アニメ")
    a = ap.parse_args()
    data = json.load(open(ROOT / "characters/characters.json", encoding="utf-8"))
    c = next(c for c in data["characters"] if c["id"] == a.id)
    v = c["voice"] if a.style == "real" else c["voice_anime"][a.style]
    text = a.text or (c["lines"][0] if a.style == "real" else c["lines_anime"][0])
    x, sr = pyopenjtalk.tts(text, speed=v["speed"], half_tone=v["half_tone"])
    x = x / np.abs(x).max() * 0.9
    out = ROOT / "output" / "voices" / f"voice_{c['id']}_{a.style}.wav"
    out.parent.mkdir(exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print("保存:", out, "|", c["name"], "|", v["tone"])


if __name__ == "__main__":
    main()
