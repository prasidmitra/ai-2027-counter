#!/usr/bin/env python3
"""Generate the favicon set: a modern white "NAH" wordmark on a black backing."""
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = '/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf'
FALLBACK = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TEXT = 'NAH'
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

S = 512            # master canvas (px)
FILL = 0.78        # fraction of the square the word occupies


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Ubuntu Sans, normal width + extra bold, with fallback."""
    try:
        font = ImageFont.truetype(FONT_PATH, size)
        values = []
        for a in font.get_variation_axes():
            name = a['name']
            if isinstance(name, bytes):
                name = name.decode('ascii', 'replace')
            key = name.lower()
            if 'width' in key or key == 'wdth':
                values.append(100)     # normal width
            elif 'weight' in key or key == 'wght':
                values.append(800)     # extra bold
            else:
                values.append(a['default'])
        font.set_variation_by_axes(values)
        return font
    except Exception:
        return ImageFont.truetype(FALLBACK, size)


def draw_master() -> Image.Image:
    img = Image.new('RGB', (S, S), BLACK)
    d = ImageDraw.Draw(img)

    # Largest font whose "NAH" still fits within FILL of the square.
    target = int(S * FILL)
    font = load_font(S)
    for size in range(S, 40, -1):
        f = load_font(size)
        l, t, r, b = d.textbbox((0, 0), TEXT, font=f)
        if (r - l) <= target:
            font = f
            break

    l, t, r, b = d.textbbox((0, 0), TEXT, font=font)
    w, h = r - l, b - t
    x = (S - w) / 2 - l
    y = (S - h) / 2 - t
    d.text((x, y), TEXT, fill=WHITE, font=font)
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
