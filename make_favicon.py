#!/usr/bin/env python3
"""Generate the favicon set: bold, narrow "NAH" in black on a white square."""
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = '/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf'
FALLBACK = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TEXT = 'NAH'
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Square the text must fit inside (as a fraction of the canvas side).
FILL = 0.78


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Ubuntu Sans, condensed (wdth=75) + extra bold (wght=800), with fallbacks."""
    try:
        font = ImageFont.truetype(FONT_PATH, size)
        axes = font.get_variation_axes()
        values = []
        for a in axes:
            name = a['name']
            if isinstance(name, bytes):
                name = name.decode('ascii', 'replace')
            key = name.lower()
            if 'width' in key or key == 'wdth':
                values.append(75)      # condensed
            elif 'weight' in key or key == 'wght':
                values.append(800)     # extra bold
            else:
                values.append(a['default'])
        font.set_variation_by_axes(values)
        return font
    except Exception:
        return ImageFont.truetype(FALLBACK, size)


def render(size: int) -> Image.Image:
    img = Image.new('RGB', (size, size), WHITE)
    draw = ImageDraw.Draw(img)

    # Pick the largest font size whose glyphs still fit within FILL of the square.
    font = None
    for candidate in range(size, 20, -1):
        f = load_font(candidate)
        l, t, r, b = draw.textbbox((0, 0), TEXT, font=f)
        if (r - l) <= FILL * size and (b - t) <= FILL * size:
            font = f
            break

    l, t, r, b = draw.textbbox((0, 0), TEXT, font=font)
    w, h = r - l, b - t
    x = (size - w) / 2 - l
    y = (size - h) / 2 - t
    draw.text((x, y), TEXT, fill=BLACK, font=font)
    return img


master = render(512)

# PNG favicons (LANCZOS-downsampled from the 512px master for crisp edges).
master.resize((192, 192), Image.LANCZOS).save('apple-touch-icon.png')
master.resize((32, 32), Image.LANCZOS).save('favicon-32x32.png')
master.resize((16, 16), Image.LANCZOS).save('favicon-16x16.png')

# Multi-size .ico for legacy browsers.
master.save('favicon.ico', format='ICO',
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

print('wrote favicon.ico, favicon-16x16.png, favicon-32x32.png, apple-touch-icon.png')
