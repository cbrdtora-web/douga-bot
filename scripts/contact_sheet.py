"""画像を並べた一覧画像を作る。  使い方: python scripts/contact_sheet.py 出力.jpg 画像1 画像2 ... [--cols 3]"""
import sys

from PIL import Image


def main():
    args = sys.argv[1:]
    cols = 3
    if "--cols" in args:
        i = args.index("--cols")
        cols = int(args[i + 1])
        del args[i:i + 2]
    out, files = args[0], args[1:]
    w, h, pad = 512, 768, 6
    rows = -(-len(files) // cols)
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad) + pad), "white")
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB").resize((w, h))
        sheet.paste(im, (pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad)))
    sheet.save(out, quality=90)
    print("保存:", out)


if __name__ == "__main__":
    main()
