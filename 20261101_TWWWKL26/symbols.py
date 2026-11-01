"""Render the visual symbols (400x400, plain white background) used as steering images.
The paper's library has 24 shapes x 12 colors; this file draws a subset of common shapes."""
from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw

SIZE = 400
COLORS = {
    "red": (220, 30, 30), "pink": (255, 105, 180), "blue": (30, 80, 220), "yellow": (240, 200, 0),
    "green": (40, 170, 60), "cyan": (0, 190, 210), "purple": (130, 50, 190), "orange": (250, 140, 20),
    "black": (0, 0, 0), "gray": (128, 128, 128), "brown": (130, 80, 40), "magenta": (220, 30, 200),
}


def _heart(d, c):
    pts = []
    for i in range(400):
        t = 2 * math.pi * i / 400
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((SIZE / 2 + x * 10, SIZE / 2 - y * 10 + 20))
    d.polygon(pts, fill=c)


def _triangle(d, c):
    d.polygon([(SIZE / 2, 60), (60, 340), (340, 340)], fill=c)


def _circle(d, c):
    d.ellipse([70, 70, 330, 330], fill=c)


def _square(d, c):
    d.rectangle([80, 80, 320, 320], fill=c)


def _star(d, c):
    pts = []
    for i in range(10):
        r = 150 if i % 2 == 0 else 60
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((SIZE / 2 + r * math.cos(a), SIZE / 2 + r * math.sin(a) + 10))
    d.polygon(pts, fill=c)


def _plus(d, c):
    d.rectangle([170, 60, 230, 340], fill=c)
    d.rectangle([60, 170, 340, 230], fill=c)


def _checkmark(d, c):
    d.line([(90, 210), (170, 300), (320, 110)], fill=c, width=40, joint="curve")


def _spiral(d, c):
    pts = []
    for i in range(500):
        t = i / 500 * 3 * 2 * math.pi
        r = 8 + 45 * t / (2 * math.pi)
        pts.append((SIZE / 2 + r * math.cos(t), SIZE / 2 + r * math.sin(t)))
    d.line(pts, fill=c, width=22, joint="curve")


def _branching_arrows(d, c):
    d.line([(200, 340), (200, 200)], fill=c, width=22)
    for dx in (-110, 110):
        d.line([(200, 200), (200 + dx, 90)], fill=c, width=22)
        tip = (200 + dx, 70)
        side = 1 if dx > 0 else -1
        d.polygon([tip, (tip[0] - 40 * side, tip[1] + 10), (tip[0] - 5 * side, tip[1] + 45)], fill=c)


def _blob(d, c):
    rnd = random.Random(3)
    pts = []
    for i in range(36):
        a = 2 * math.pi * i / 36
        r = 120 + rnd.uniform(-35, 35)
        pts.append((SIZE / 2 + r * math.cos(a), SIZE / 2 + r * math.sin(a)))
    d.polygon(pts, fill=c)


def _x(d, c):
    d.line([(80, 80), (320, 320)], fill=c, width=40)
    d.line([(320, 80), (80, 320)], fill=c, width=40)


def _arrow_right(d, c):
    d.line([(60, 200), (260, 200)], fill=c, width=36)
    d.polygon([(340, 200), (240, 120), (240, 280)], fill=c)


SHAPES = {"heart": _heart, "triangle": _triangle, "circle": _circle, "square": _square, "star": _star,
          "plus": _plus, "checkmark": _checkmark, "spiral": _spiral, "branching_arrows": _branching_arrows,
          "blob": _blob, "x": _x, "arrow_right": _arrow_right}


def render(shape: str, color: str, path: str) -> str:
    img = Image.new("RGB", (SIZE, SIZE), "white")
    SHAPES[shape](ImageDraw.Draw(img), COLORS[color])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def noise(path: str, seed: int = 0) -> str:
    rnd = random.Random(seed)
    img = Image.new("RGB", (SIZE, SIZE))
    img.putdata([(rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255)) for _ in range(SIZE * SIZE)])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "symbols"
    for s in SHAPES:
        for c in COLORS:
            render(s, c, os.path.join(out, f"{s}_{c}.png"))
    noise(os.path.join(out, "noise.png"))
    print(f"rendered {len(SHAPES) * len(COLORS)} symbols + noise into {out}/")
