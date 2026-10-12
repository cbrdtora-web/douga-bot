"""キャラクターごとの声(日本語読み上げ・オフライン)の見本を作る。

使い方:  python scripts/persona_voice.py 07            # 07番のセリフ例を output/voice_07.wav に
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
    a = ap.parse_args()
    data = json.load(open(ROOT / "characters/characters.json", encoding="utf-8"))
    c = next(c for c in data["characters"] if c["id"] == a.id)
    text = a.text or c["lines"][0]
    x, sr = pyopenjtalk.tts(text, speed=c["voice"]["speed"], half_tone=c["voice"]["half_tone"])
    x = x / np.abs(x).max() * 0.9
    out = ROOT / "output" / f"voice_{c['id']}.wav"
    out.parent.mkdir(exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print("保存:", out, "|", c["name"], "|", c["voice"]["tone"])


if __name__ == "__main__":
    main()
