"""Build the GitHub social-preview card.

Recomposes the source artwork (3:2, lockup in the left third) onto GitHub's
1280x640 social-preview ratio, centred, with the paper texture carried across
the full frame so there is no seam.

Run from this folder:  python build-og.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
SRC = HERE / "source-artwork.png"
OUT = HERE / "janus-og.png"
W, H = 1280, 640                      # GitHub social-preview size

im = Image.open(SRC).convert("RGB")

# ---- 1. canvas: real paper texture from his own empty right side, mirrored to 2:1
tex = im.crop((896, 192, 1536, 832))                  # 640x640 of pure background
canvas = Image.new("RGB", (W, H))
canvas.paste(tex, (0, 0))
canvas.paste(tex.transpose(Image.FLIP_LEFT_RIGHT), (640, 0))

# ---- 2. his lockup, with bleed so the feather has texture to fade into
BLEED = 40
box = (134 - BLEED, 175 - BLEED, 577 + BLEED, 843 + BLEED)
block = im.crop(box)

CONTENT_H = 520                                        # target height of the artwork itself
scale = CONTENT_H / (843 - 175)
bw, bh = (round(block.width * scale), round(block.height * scale))
block = block.resize((bw, bh), Image.LANCZOS)

# ---- 3. feathered alpha so the two textures meet invisibly
f = round(BLEED * scale)
mask = Image.new("L", (bw, bh), 0)
ImageDraw.Draw(mask).rectangle([f, f, bw - f, bh - f], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(f * 0.55))

canvas.paste(block, ((W - bw) // 2, (H - bh) // 2), mask)
canvas.save(OUT, optimize=True)
print("wrote", OUT, canvas.size)
