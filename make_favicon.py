#!/usr/bin/env python3
"""Generate the favicon set: a thick, block-letter "NAH" stretched to fill the square."""
import math
from PIL import Image, ImageDraw

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

S = 512            # master canvas (px)
M = 16             # thin white border (px on the master)
STEM = 52          # stroke thickness


def thick_segment(p, q, t):
    """Four corners of a `t`-thick segment from p to q (a parallelogram)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    hx, hy = nx * t / 2, ny * t / 2
    return [
        (p[0] + hx, p[1] + hy),
        (p[0] - hx, p[1] - hy),
        (q[0] - hx, q[1] - hy),
        (q[0] + hx, q[1] + hy),
    ]


def draw_master() -> Image.Image:
    img = Image.new('RGB', (S, S), WHITE)
    d = ImageDraw.Draw(img)

    top, bottom = M, S - M       # 16, 496
    H = bottom - top             # 480
    W = H // 3                   # 160 per letter — letters touch at their edges
    t = STEM
    mid = top + H // 2           # vertical center

    x0 = M

    # N — two stems + a top-left -> bottom-right diagonal.
    nx0 = x0
    d.polygon(thick_segment((nx0 + t, top), (nx0 + W - t, bottom), t), fill=BLACK)
    d.rectangle([nx0, top, nx0 + t, bottom], fill=BLACK)
    d.rectangle([nx0 + W - t, top, nx0 + W, bottom], fill=BLACK)

    # A — vertical legs, a flat top bar, and a crossbar (squared "A").
    ax0 = x0 + W
    d.rectangle([ax0, top, ax0 + t, bottom], fill=BLACK)
    d.rectangle([ax0 + W - t, top, ax0 + W, bottom], fill=BLACK)
    d.rectangle([ax0, top, ax0 + W, top + t], fill=BLACK)
    d.rectangle([ax0, mid - t // 2, ax0 + W, mid + t // 2], fill=BLACK)

    # H — two stems + a crossbar.
    hx0 = x0 + 2 * W
    d.rectangle([hx0, top, hx0 + t, bottom], fill=BLACK)
    d.rectangle([hx0 + W - t, top, hx0 + W, bottom], fill=BLACK)
    d.rectangle([hx0, mid - t // 2, hx0 + W, mid + t // 2], fill=BLACK)

    return img


master = draw_master()

# PNG favicons (LANCZOS-downsampled from the 512px master for crisp edges).
master.resize((192, 192), Image.LANCZOS).save('apple-touch-icon.png')
master.resize((32, 32), Image.LANCZOS).save('favicon-32x32.png')
master.resize((16, 16), Image.LANCZOS).save('favicon-16x16.png')

# Multi-size .ico for legacy browsers.
master.save('favicon.ico', format='ICO',
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

print('wrote favicon.ico, favicon-16x16.png, favicon-32x32.png, apple-touch-icon.png')
