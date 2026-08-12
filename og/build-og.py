"""Build the GitHub social-preview card.

Recomposes the source artwork (3:2, lockup in the left third) onto GitHub's
1280x640 social-preview ratio. The lockup stays LEFT, where the artwork puts it,
and the empty right side carries copy explaining the skill. That space is the
reason the artwork is left-weighted; it is not padding.

The paper texture is carried across the full frame and the lockup is pasted
through a feathered mask with bleed, so the two textures meet invisibly.

Canonical implementation. The copy in each skill repo must stay identical; if you
change one, change the other.

Run from this folder:
    python build-og.py --config peitho
    python build-og.py --config janus
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
W, H = 1280, 640                       # GitHub social-preview size

FONTS = Path("C:/Windows/Fonts")
F_DISPLAY = FONTS / "GARA.TTF"         # Garamond, for kicker and headline
F_TEXT = FONTS / "corbell.ttf"         # Corbel Light, for the bullets
F_MONOISH = FONTS / "calibril.ttf"     # Calibri Light: lining figures, so a URL sits on the baseline

GOLD, CREAM, MUTED, RULE = "#C9A96A", "#EFE6D4", "#9C9081", "#8A7449"

# Per-skill config. box is the lockup's trimmed bounding box in the source
# artwork, as (x0, y0, x1, y1). Find it with:
#   magick source-artwork.png -fuzz 15% -trim -format '%wx%h+%X+%Y' info:
CONFIGS = {
    "peitho": dict(
        out="peitho-og.png",
        box=(107, 105, 729, 920),
        kicker="PULL IS PARTICIPATION",
        headline="A reader keeps reading because you gave them something to do.",
        bullets=[
            "Visible gaps, not withheld endings",
            "Openings that earn the next paragraph",
            "Every claim sourced. No invented detail.",
        ],
        footer="github.com/Pr1m4lc0d3/peitho",
    ),
    "janus": dict(
        out="janus-og.png",
        box=(134, 175, 577, 843),
        kicker="CONTRADICTION IS THE POSITION",
        headline="Every other framework dissolves a contradiction. This one refuses.",
        # Straight from janus/SKILL.md steps 1, 2 and 4. Do NOT write "what a
        # rival must give up" here: that is Idea Forge Pro's moat gate, a
        # different thing, and Janus is explicitly not a pipeline stage.
        bullets=[
            "Name the pair that must both be true",
            "Ban the three exits: compromise, sequence, segment",
            "Harvest a mechanism, not a slogan. Neither pole weakens.",
        ],
        footer="github.com/Pr1m4lc0d3/janus",
    ),
}


def tracked(draw, xy, text, font, fill, tracking=0.0):
    """Draw text with letterspacing. Returns the advance width."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x - xy[0]


def wrap(text, font, max_w):
    lines, words, line = [], text.split(), ""
    for word in words:
        trial = f"{line} {word}".strip()
        if font.getlength(trial) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def build(cfg, src_path):
    im = Image.open(src_path).convert("RGB")

    # 1. Canvas: real paper texture from the artwork's own empty right side,
    #    mirrored to fill 2:1 without repeating a visible edge.
    tex = im.crop((896, 192, 1536, 832))
    canvas = Image.new("RGB", (W, H))
    canvas.paste(tex, (0, 0))
    canvas.paste(tex.transpose(Image.FLIP_LEFT_RIGHT), (640, 0))

    # 2. The lockup, cropped with bleed so the feather has texture to fade into.
    BLEED, CONTENT_H = 40, 520
    x0, y0, x1, y1 = cfg["box"]
    block = im.crop((x0 - BLEED, y0 - BLEED, x1 + BLEED, y1 + BLEED))
    scale = CONTENT_H / (y1 - y0)
    bw, bh = round(block.width * scale), round(block.height * scale)
    block = block.resize((bw, bh), Image.LANCZOS)

    # 3. Feathered alpha so the two textures meet invisibly.
    f = round(BLEED * scale)
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rectangle([f, f, bw - f, bh - f], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(f * 0.55))

    lock_x, lock_y = 84 - f, (H - bh) // 2
    canvas.paste(block, (lock_x, lock_y), mask)

    # 4. Right column, clear of the lockup's visible edge.
    col_x = 84 + (bw - 2 * f) + 96
    col_w = W - col_x - 84
    if col_w < 260:
        raise SystemExit(f"Right column is only {col_w}px. Narrow the lockup.")

    d = ImageDraw.Draw(canvas)
    y = 148

    tracked(d, (col_x, y), cfg["kicker"], ImageFont.truetype(str(F_DISPLAY), 25), GOLD, 5.5)
    y += 44

    head_font = ImageFont.truetype(str(F_DISPLAY), 45)
    for line in wrap(cfg["headline"], head_font, col_w):
        d.text((col_x, y), line, font=head_font, fill=CREAM)
        y += 50
    y += 20

    d.line([(col_x, y), (col_x + 96, y)], fill=RULE, width=1)
    y += 32

    bullet_font = ImageFont.truetype(str(F_TEXT), 25)
    for b in cfg["bullets"]:
        d.text((col_x, y), "\u00b7", font=bullet_font, fill=GOLD)
        d.text((col_x + 22, y), b, font=bullet_font, fill=MUTED)
        y += 40

    tracked(d, (col_x, H - 140), cfg["footer"], ImageFont.truetype(str(F_MONOISH), 22), GOLD, 2.2)

    out = HERE / cfg["out"]
    canvas.save(out, optimize=True)
    print(f"wrote {out} {canvas.size} right column {col_w}px")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, choices=sorted(CONFIGS))
    ap.add_argument("--source", default=str(HERE / "source-artwork.png"))
    a = ap.parse_args()
    build(CONFIGS[a.config], a.source)
