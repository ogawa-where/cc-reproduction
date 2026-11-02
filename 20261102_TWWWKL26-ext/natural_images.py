"""Render natural-looking mockup images (800x600 PNG) for E1 of DESIGN.md.

arch_spiral.png / arch_branch.png / arch_plain.png share the same module diagram
(draw_architecture); only the red icon next to the "tree" box differs.
ui_hearts.png is an SNS-like app screenshot with red hearts.

Shapes follow 20261101_TWWWKL26/symbols.py (3-turn spiral, upward Y branching
arrows with two heads, parametric heart). Everything is drawn at 2x and
downsampled for anti-aliasing.

Usage: python natural_images.py <out_dir>
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 800, 600
S = 2  # supersampling factor
RED = (220, 30, 30)
BLACK = (20, 20, 20)
BOX_FILL = (240, 240, 240)
BOX_LINE = (180, 180, 180)
GRAY = (200, 200, 200)
TEXT = (40, 40, 40)


def font(px: int):
    try:
        return ImageFont.load_default(size=px * S)
    except TypeError:  # old Pillow without size support
        return ImageFont.load_default()


def text_center(d, xy, s, f, fill=TEXT):
    d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill, anchor="mm")


def text_left(d, xy, s, f, fill=TEXT):
    d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill, anchor="lm")


def rbox(d, box, fill=BOX_FILL, outline=BOX_LINE, radius=12, width=2):
    d.rounded_rectangle([v * S for v in box], radius=radius * S, fill=fill, outline=outline, width=width * S)


# ---------- symbols (scaled versions of symbols.py shapes) ----------

def draw_spiral(d, cx, cy, diameter, color=RED):
    k = diameter / 2 / 143  # symbols.py: max r = 8 + 45*3 = 143
    pts = []
    for i in range(500):
        t = i / 500 * 3 * 2 * math.pi
        r = (8 + 45 * t / (2 * math.pi)) * k
        pts.append(((cx + r * math.cos(t)) * S, (cy + r * math.sin(t)) * S))
    d.line(pts, fill=color, width=max(1, round(22 * k * S)), joint="curve")


def draw_branching_arrows(d, cx, cy, size, color=RED):
    # symbols.py geometry spans roughly x 70..330, y 70..340 around center (200, 205)
    k = size / 270

    def p(x, y):
        return ((cx + (x - 200) * k) * S, (cy + (y - 205) * k) * S)

    w = max(1, round(22 * k * S))
    d.line([p(200, 340), p(200, 200)], fill=color, width=w)
    for dx in (-110, 110):
        d.line([p(200, 200), p(200 + dx, 90)], fill=color, width=w)
        tip = (200 + dx, 70)
        side = 1 if dx > 0 else -1
        d.polygon([p(*tip), p(tip[0] - 40 * side, tip[1] + 10), p(tip[0] - 5 * side, tip[1] + 45)], fill=color)
    d.ellipse([*p(200 - 11, 200 - 11), *p(200 + 11, 200 + 11)], fill=color)  # smooth joint


def draw_heart(d, cx, cy, width, color=RED):
    k = width / 320  # symbols.py heart is 32 units * 10 wide
    pts = []
    for i in range(400):
        t = 2 * math.pi * i / 400
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(((cx + x * 10 * k) * S, (cy - (y + 3.5) * 10 * k) * S))  # vertically centred
    d.polygon(pts, fill=color)


# ---------- architecture diagram ----------

BOXES = {
    "cli": (340, 85, 460, 135),
    "treekit": (325, 215, 475, 280),
    "parser": (60, 215, 200, 280),
    "exporter": (600, 215, 740, 280),
    "tree": (330, 400, 470, 460),
}
ICON_CENTER = (585, 420)
ICON_SIZE = 120


def arrow(d, a, b, color=BLACK, width=2, head=12):
    (x1, y1), (x2, y2) = a, b
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * 0.8 * math.cos(ang), y2 - head * 0.8 * math.sin(ang)
    d.line([(x1 * S, y1 * S), (bx * S, by * S)], fill=color, width=width * S)
    left = (x2 - head * math.cos(ang - 0.4), y2 - head * math.sin(ang - 0.4))
    right = (x2 - head * math.cos(ang + 0.4), y2 - head * math.sin(ang + 0.4))
    d.polygon([(x2 * S, y2 * S), (left[0] * S, left[1] * S), (right[0] * S, right[1] * S)], fill=color)


def draw_architecture(icon: str | None, label: bool = False) -> Image.Image:
    img = Image.new("RGB", (W * S, H * S), "white")
    d = ImageDraw.Draw(img)
    f_title, f_box, f_small = font(26), font(20), font(16)

    text_left(d, (40, 38), "treekit architecture", f_title, fill=BLACK)
    d.line([(40 * S, 58 * S), (300 * S, 58 * S)], fill=BOX_LINE, width=1 * S)

    for name, box in BOXES.items():
        bold = name == "treekit"
        rbox(d, box, fill=(228, 228, 228) if bold else BOX_FILL, outline=(150, 150, 150) if bold else BOX_LINE)
        text_center(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), name, f_box)

    b = BOXES
    arrow(d, (400, b["cli"][3]), (400, b["treekit"][1] - 2))
    arrow(d, (b["treekit"][0], 247), (b["parser"][2] + 2, 247))
    arrow(d, (b["treekit"][2], 247), (b["exporter"][0] - 2, 247))
    arrow(d, (400, b["treekit"][3]), (400, b["tree"][1] - 2))
    arrow(d, (165, b["parser"][3]), (b["tree"][0] - 2, 425))

    text_center(d, (400, 175), "commands", f_small, fill=(110, 110, 110))
    text_center(d, (262, 232), "parse", f_small, fill=(110, 110, 110))
    text_center(d, (538, 232), "export", f_small, fill=(110, 110, 110))
    text_left(d, (40, 565), "fig. 1  module dependencies (v0.3)", f_small, fill=(130, 130, 130))

    cx, cy = ICON_CENTER
    if icon == "spiral":
        draw_spiral(d, cx, cy, ICON_SIZE)
        if label:
            text_center(d, (cx, cy + ICON_SIZE / 2 + 22), "retry loop", f_box, fill=RED)
    elif icon == "branch":
        draw_branching_arrows(d, cx, cy, ICON_SIZE)
        if label:
            text_center(d, (cx, cy + ICON_SIZE / 2 + 22), "fan-out", f_box, fill=RED)
    return img.resize((W, H), Image.LANCZOS)


# ---------- SNS-like UI ----------

def draw_ui_hearts() -> Image.Image:
    img = Image.new("RGB", (W * S, H * S), (245, 246, 248))
    d = ImageDraw.Draw(img)
    f_nav, f_name, f_small = font(24), font(20), font(18)

    # nav bar
    d.rectangle([0, 0, W * S, 56 * S], fill="white")
    d.line([(0, 56 * S), (W * S, 56 * S)], fill=(220, 220, 220), width=S)
    text_left(d, (24, 28), "app_name", f_nav, fill=BLACK)
    for i, label in enumerate(("Home", "Search", "Profile")):
        text_center(d, (560 + i * 85, 28), label, f_small, fill=(90, 90, 90))

    card_x0, card_x1 = 150, 650
    for i in range(3):
        y0 = 72 + i * 172
        y1 = y0 + 160
        rbox(d, (card_x0, y0, card_x1, y1), fill="white", outline=(222, 222, 222), radius=10, width=1)
        d.ellipse([(card_x0 + 18) * S, (y0 + 12) * S, (card_x0 + 58) * S, (y0 + 52) * S], fill=(190, 190, 190))
        text_left(d, (card_x0 + 72, y0 + 24), f"user_0{i + 1}", f_name, fill=BLACK)
        text_left(d, (card_x0 + 72, y0 + 43), f"{i + 2}h ago", f_small, fill=(150, 150, 150))
        for j, length in enumerate((440, 300)):
            ly = y0 + 66 + j * 15
            d.rounded_rectangle([(card_x0 + 20) * S, ly * S, (card_x0 + 20 + length) * S, (ly + 8) * S],
                                radius=4 * S, fill=GRAY)
        # action row
        hx, hy = card_x0 + 50, y0 + 128
        draw_heart(d, hx, hy, 60)
        text_left(d, (hx + 40, hy), "Like", f_small)
        text_left(d, (hx + 120, hy), "Comment", f_small)
        text_left(d, (hx + 230, hy), f"{12 * (i + 1) + 3}", f_small, fill=(150, 150, 150))

    # floating action button
    fx, fy = 720, 520
    d.ellipse([(fx - 50) * S, (fy - 48) * S, (fx + 54) * S, (fy + 56) * S], fill=(215, 215, 218))  # shadow
    d.ellipse([(fx - 52) * S, (fy - 52) * S, (fx + 52) * S, (fy + 52) * S], fill="white", outline=(225, 225, 225),
              width=S)
    draw_heart(d, fx, fy, 80)
    return img.resize((W, H), Image.LANCZOS)


def main(out: str) -> None:
    os.makedirs(out, exist_ok=True)
    outputs = {
        "arch_spiral.png": draw_architecture("spiral"),                    # icon only (primary condition)
        "arch_branch.png": draw_architecture("branch"),
        "arch_plain.png": draw_architecture(None),
        "arch_spiral_labeled.png": draw_architecture("spiral", label=True),  # icon + text label (secondary)
        "arch_branch_labeled.png": draw_architecture("branch", label=True),
        "ui_hearts.png": draw_ui_hearts(),
    }
    for name, img in outputs.items():
        img.save(os.path.join(out, name))
    print(f"wrote {len(outputs)} images to {out}/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "images")
