"""猫の縦動画(1080x1920, 10秒)を自動作成するプログラム。

使い方:
    python make_video.py                       # 既定の設定で作成
    python make_video.py --text "ここ、最高" --image assets/cat.jpg
    python make_video.py --no-voice            # 音声なし
"""
import argparse
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUT_DIR = Path("output")


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def make_subtitle_png(text, path):
    """漫画ふうの吹き出し(太い縁・だ円・しっぽ)にセリフを入れた透明PNGを作る。"""
    K = 2  # 2倍の大きさで描いて縮小し、縁をなめらかにする
    img = Image.new("RGBA", (W * K, 560 * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    size = 120
    font = ImageFont.truetype(FONT, size * K)
    while d.textlength(text, font=font) > (W - 360) * K and size > 40:
        size -= 6
        font = ImageFont.truetype(FONT, size * K)
    tw = d.textlength(text, font=font) / K
    bw, bh = tw + 200, size + 190  # だ円は文字より大きめに
    x0, y0 = (W - bw) / 2, 50
    x1, y1 = x0 + bw, y0 + bh
    cx = W / 2 - 70  # しっぽの根もと(猫の顔のほうへ)
    tail = [(cx - 55, y1 - 55), (cx + 35, y1 - 45), (cx - 20, y1 + 150)]
    tail_edge = [(cx - 72, y1 - 62), (cx + 52, y1 - 50), (cx - 22, y1 + 178)]
    box = lambda m: tuple(v * K for v in (x0 - m, y0 - m, x1 + m, y1 + m))
    big = lambda pts: [(x * K, y * K) for x, y in pts]
    # 黒い縁 → 白い中身の順に重ねる
    d.ellipse(box(14), fill="black")
    d.polygon(big(tail_edge), fill="black")
    d.ellipse(box(0), fill="white")
    d.polygon(big(tail), fill="white")
    # 文字はふち取りで太く見せる(漫画のセリフ風)
    d.text((W / 2 * K, (y0 + y1) / 2 * K), text, font=font, fill="black", anchor="mm",
           stroke_width=3 * K, stroke_fill="black")
    img.resize((W, 560), Image.LANCZOS).save(path)


def make_bgm(path, seconds):
    """オルゴール風のやさしいBGMを自作する(著作権の心配なし)。"""
    sr = 44100
    t = np.arange(int(sr * seconds)) / sr
    notes = [523.25, 659.25, 783.99, 659.25, 587.33, 698.46, 880.0, 698.46]  # C E G E / D F A F
    step = 0.5
    out = np.zeros_like(t)
    for i in range(int(seconds / step)):
        f = notes[i % len(notes)]
        s = int(i * step * sr)
        n = int(1.2 * sr)
        tt = np.arange(min(n, len(out) - s)) / sr
        tone = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)
        out[s:s + len(tt)] += tone * np.exp(-4 * tt)
    out *= np.minimum(1, t / 0.5) * np.minimum(1, (seconds - t) / 1.5)  # 出だしと終わりをなめらかに
    out = out / np.abs(out).max() * 0.35
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def make_voice(text, path):
    """日本語の読み上げ音声を作る(インターネット不要・無料)。"""
    import pyopenjtalk
    x, sr = pyopenjtalk.tts(text, half_tone=5.0)  # 少し高めの声にする
    x = x / np.abs(x).max() * 0.9
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="assets/cat.jpg")
    ap.add_argument("--text", default="ここ、落ち着くにゃ…")
    ap.add_argument("--seconds", type=int, default=10)
    ap.add_argument("--face-x", type=float, default=0.49, help="猫の顔の位置(横, 0〜1)")
    ap.add_argument("--face-y", type=float, default=0.50, help="猫の顔の位置(縦, 0〜1)")
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--out", default="output/cat_10s.mp4")
    a = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    sub, bgm, voice = OUT_DIR / "sub.png", OUT_DIR / "bgm.wav", OUT_DIR / "voice.wav"
    make_subtitle_png(a.text, sub)
    make_bgm(bgm, a.seconds)

    # 画像を縦長(9:16)に切り出し、猫の顔を中心にゆっくりズーム
    img = Image.open(a.image)
    iw, ih = img.size
    cw = int(ih * 9 / 16)
    cx = min(max(int(iw * a.face_x) - cw // 2, 0), iw - cw)
    crop = OUT_DIR / "crop.png"
    img.crop((cx, 0, cx + cw, ih)).resize((W * 2, H * 2), Image.LANCZOS).save(crop)

    frames = a.seconds * FPS
    zoom = f"1+0.30*on/{frames}"
    zp = (f"zoompan=z='{zoom}':x='iw*0.5-iw/zoom/2':y='ih*{a.face_y}-ih/zoom/2'"
          f":d={frames}:s={W}x{H}:fps={FPS}")
    fade = f"fade=t=out:st={a.seconds - 1}:d=0.8:alpha=1"

    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(crop), "-loop", "1", "-i", str(sub), "-i", str(bgm)]
    audio = "[2:a]volume=0.8[a]"
    if not a.no_voice:
        make_voice(a.text, voice)
        cmd += ["-i", str(voice)]
        audio = "[2:a]volume=0.5[b];[3:a]adelay=1000|1000,volume=1.4[vo];[b][vo]amix=inputs=2:duration=first[a]"
    fc = (f"[0:v]{zp},format=yuv420p[v0];"
          f"[1:v]format=rgba,{fade}[s];"
          f"[v0][s]overlay=x=0:y='60+if(lt(t,1),-800,-70*exp(-7*(t-1))*cos(20*(t-1)))':format=auto[v];{audio}")
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", str(a.seconds),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", a.out]
    run(cmd)
    print("できました:", a.out)


if __name__ == "__main__":
    main()
