"""Canvas normalization and lightweight image analysis (Sections 11, 26, 27).

Deliberately dependency-light: Pillow only, no OpenCV/face-detection. If a
genuine need for smarter subject-aware cropping comes up later, this is the
one place that would change.
"""
import io

from PIL import Image, ImageDraw, ImageFilter, ImageStat

from poster.config import DEMO_STYLE_GRADIENTS, POSTER_SIZES


def _hex_to_rgb(value: str) -> tuple:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def generate_placeholder_background(width: int, height: int, style_key: str = "auto") -> bytes:
    """A Pillow-only diagonal gradient with a soft vignette, standing in for
    the AI artwork in Demo Mode. No external calls, no cost — lets the rest
    of the pipeline (crop, typography, logo) be exercised for free.
    """
    c1, c2 = DEMO_STYLE_GRADIENTS.get(style_key, DEMO_STYLE_GRADIENTS["auto"])
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)

    diag = max(1, width + height)
    row = []
    for i in range(diag):
        t = i / diag
        row.append((round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t), round(b1 + (b2 - b1) * t)))
    gradient_strip = Image.new("RGB", (diag, 1))
    gradient_strip.putdata(row)
    gradient_strip = gradient_strip.resize((diag, diag))
    img = gradient_strip.rotate(45, expand=True)
    left = (img.width - width) // 2
    top = (img.height - height) // 2
    img = img.crop((left, top, left + width, top + height))

    # Soft vignette so it reads as a poster background, not a flat swatch.
    # Darkens toward the palette's own darker endpoint rather than pure
    # black, so light styles (e.g. Minimal Premium) don't get harsh black
    # corners.
    vignette = Image.new("L", (width, height), 255)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse((-width * 0.2, -height * 0.2, width * 1.2, height * 1.2), fill=140)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=min(width, height) * 0.08))
    darker = tuple(round(c * 0.55) for c in (min(r1, r2), min(g1, g2), min(b1, b2)))
    dark_layer = Image.new("RGB", (width, height), darker)
    img = Image.composite(img, dark_layer, vignette)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def crop_to_size(image_bytes: bytes, size_key: str) -> bytes:
    """Center-crop (never stretch) the generated image down to the exact
    target pixel dimensions for the requested output size.
    """
    spec = POSTER_SIZES[size_key]
    target_w, target_h = spec["width"], spec["height"]
    target_ratio = target_w / target_h

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # source is wider than target: crop width, keep full height
        new_w = round(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    elif src_ratio < target_ratio:
        # source is taller than target: crop height, bias slightly upward
        # since portrait/hero subjects usually sit in the upper-to-center
        # band rather than dead center.
        new_h = round(src_w / target_ratio)
        remaining = src_h - new_h
        top = max(0, round(remaining * 0.35))
        img = img.crop((0, top, src_w, top + new_h))

    img = img.resize((target_w, target_h), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def analyze_image(image_bytes: bytes) -> dict:
    """Cheap heuristics used to inform auto style/palette choices — not a
    substitute for real computer vision, just enough signal to avoid always
    picking the same palette.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = img.size

    small = img.resize((64, 64))
    stat = ImageStat.Stat(small)
    r, g, b = (round(c) for c in stat.mean)
    brightness = round((0.299 * r + 0.587 * g + 0.114 * b) / 255, 3)

    quantized = small.quantize(colors=5, method=Image.MEDIANCUT)
    palette = quantized.getpalette()
    color_counts = sorted(quantized.getcolors(), reverse=True)
    dominant_idx = color_counts[0][1]
    dr, dg, db = palette[dominant_idx * 3: dominant_idx * 3 + 3]
    dominant_hex = f"#{dr:02x}{dg:02x}{db:02x}"

    # background complexity: standard deviation of a small grayscale
    # version — a low-variance image reads as a simple/plain background,
    # a high-variance one as busy/detailed.
    gray_stat = ImageStat.Stat(small.convert("L"))
    complexity = "simple" if gray_stat.stddev[0] < 35 else "busy"

    return {
        "width": width,
        "height": height,
        "orientation": "portrait" if height > width else ("landscape" if width > height else "square"),
        "brightness": brightness,
        "dominant_color": dominant_hex,
        "background_complexity": complexity,
    }
