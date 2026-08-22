"""Deterministic Python-side typography and logo compositing (Sections 22-25).

The AI-generated artwork is the background only. Every piece of exact
information — title, names, date/time, CTA, tagline — is rendered here with
Pillow so it can never contain an AI spelling error, and so it can never
overflow the canvas or sit on top of a face.
"""
import io
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat

from poster.config import FONT_DIR, FONT_VARIABLE_FILE, METALLIC_STYLE_KEYS, POSTER_SIZES

_FONT_PATH = Path(__file__).resolve().parent.parent / FONT_DIR / FONT_VARIABLE_FILE

# opsz/wght variable-font axis order, confirmed against the bundled Inter
# variable font (axes: [Optical size 14-32, Weight 100-900]).
_OPSZ_DEFAULT = 20

SAFE_MARGIN_FRACTION = 0.05  # of the shorter canvas dimension

# Normalized (x0, y0, x1, y1) zones per category layout (Section 24). Kept as
# fractions of canvas size rather than fixed pixels so every output size
# (square/portrait/story) stays correctly proportioned.
LAYOUTS = {
    "single_hero": {
        "title": (0.06, 0.05, 0.94, 0.18),
        "names": (0.06, 0.60, 0.94, 0.70),
        "tagline": (0.06, 0.70, 0.94, 0.78),
        "date_time": (0.10, 0.82, 0.90, 0.90),
        "cta": (0.20, 0.91, 0.80, 0.97),
    },
    "battle_vs": {
        "title": (0.06, 0.04, 0.94, 0.15),
        "name_a": (0.03, 0.76, 0.47, 0.87),
        "name_b": (0.53, 0.76, 0.97, 0.87),
        "date_time": (0.15, 0.89, 0.85, 0.96),
        "cta": (0.25, 0.96, 0.75, 1.00),
    },
    "finals_dual": {
        "title": (0.06, 0.04, 0.94, 0.13),
        "tagline": (0.06, 0.13, 0.94, 0.19),
        "name_a": (0.03, 0.74, 0.47, 0.85),
        "name_b": (0.53, 0.74, 0.97, 0.85),
        "date_time": (0.15, 0.87, 0.85, 0.94),
        "cta": (0.25, 0.94, 0.75, 0.99),
    },
}

def _font(weight: int, size: int, opsz: int = _OPSZ_DEFAULT) -> ImageFont.FreeTypeFont:
    return _load_variable_font(weight, size, opsz)


@lru_cache(maxsize=128)
def _load_variable_font(weight: int, size: int, opsz: int) -> ImageFont.FreeTypeFont:
    try:
        font = ImageFont.truetype(str(_FONT_PATH), size=size)
        font.set_variation_by_axes([opsz, weight])
        return font
    except Exception:
        # Deployment safety net: if the bundled TTF is ever missing, fall
        # back to Pillow's built-in font rather than crashing generation.
        return ImageFont.load_default(size=size)


def _zone_px(zone, canvas_w, canvas_h):
    x0, y0, x1, y1 = zone
    return (round(x0 * canvas_w), round(y0 * canvas_h), round(x1 * canvas_w), round(y1 * canvas_h))


def _region_luminance(img: Image.Image, box) -> float:
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return 0.4
    region = img.crop((x0, y0, x1, y1)).convert("L")
    return ImageStat.Stat(region).mean[0] / 255


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_text(draw, text, box_w, box_h, weight, start_size, min_size, max_lines):
    """Shrinks font size until the wrapped text fits within box_w x box_h,
    never exceeding max_lines and never going below min_size. Names/titles
    are never cropped — they wrap and shrink instead (Section 51).
    """
    size = start_size
    while size >= min_size:
        font = _font(weight, size)
        lines = _wrap_text(draw, text, font, box_w)
        if len(lines) > max_lines:
            size -= 2
            continue
        line_height = font.size * 1.25
        total_h = line_height * len(lines)
        if total_h <= box_h:
            return font, lines, line_height
        size -= 2
    font = _font(weight, min_size)
    lines = _wrap_text(draw, text, font, box_w)[:max_lines]
    return font, lines, font.size * 1.25


def _draw_block(img, draw, text, zone, *, weight=700, start_size=None, min_size=18,
                 align="center", max_lines=2, metallic=False):
    if not text:
        return
    canvas_w, canvas_h = img.size
    x0, y0, x1, y1 = _zone_px(zone, canvas_w, canvas_h)
    box_w, box_h = x1 - x0, y1 - y0
    if box_w <= 0 or box_h <= 0:
        return

    start_size = start_size or round(box_h * 0.6)
    font, lines, line_height = _fit_text(draw, text, box_w, box_h, weight, start_size, min_size, max_lines)

    luminance = _region_luminance(img, (x0, y0, x1, y1))
    if luminance > 0.6:
        fill = (17, 24, 39, 255)       # brand dark text
        stroke = (255, 255, 255, 230)
        shadow = (255, 255, 255, 120)
    else:
        fill = (255, 255, 255, 255)
        shadow = (0, 0, 0, 160)
        stroke = (17, 17, 17, 200)

    total_h = line_height * len(lines)
    start_y = y0 + max(0, (box_h - total_h) / 2)
    stroke_width = max(1, round(font.size * 0.03))

    # Metallic treatment fills the glyph shapes themselves with a gold
    # gradient (masked to the actual text pixels), rather than painting a
    # box behind the text — the dark stroke drawn first stays visible as an
    # outline ring around each gold letter.
    glyph_mask = Image.new("L", img.size, 0) if metallic else None
    mask_draw = ImageDraw.Draw(glyph_mask) if metallic else None

    for i, line in enumerate(lines):
        line_w = draw.textlength(line, font=font)
        if align == "center":
            lx = x0 + (box_w - line_w) / 2
        elif align == "left":
            lx = x0
        else:
            lx = x1 - line_w
        ly = start_y + i * line_height

        draw.text((lx + 2, ly + 3), line, font=font, fill=shadow)
        draw.text(
            (lx, ly), line, font=font, fill=(fill if not metallic else stroke),
            stroke_width=stroke_width, stroke_fill=stroke,
        )
        if metallic:
            mask_draw.text((lx, ly), line, font=font, fill=255)

    if metallic:
        _apply_metallic_overlay(img, (x0, int(start_y), x1, int(start_y + total_h)), glyph_mask)


def _apply_metallic_overlay(img: Image.Image, box, glyph_mask: Image.Image):
    """Gold gradient, masked to the glyph interiors drawn in _draw_block —
    the dark stroke already on img stays visible as an outline ring.
    """
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    grad_row = [int(150 + 90 * (1 - abs((y / max(1, h)) - 0.5) * 2)) for y in range(h)]
    gradient = Image.new("L", (1, h))
    gradient.putdata(grad_row)
    gradient = gradient.resize((img.width, h))

    gold = Image.new("RGBA", (img.width, h), (255, 205, 110, 255))
    gold.putalpha(gradient)

    full_gold = Image.new("RGBA", img.size, (0, 0, 0, 0))
    full_gold.paste(gold, (0, y0))

    img.paste(full_gold, (0, 0), mask=glyph_mask)


def place_logo(img: Image.Image, logo_bytes: bytes, position: str) -> Image.Image:
    """Composites a logo preserving aspect ratio, within safe margins, never
    stretched. position='auto' picks the corner emptiest of foreground
    detail (cheap heuristic: lowest local contrast).
    """
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    canvas_w, canvas_h = img.size
    margin = round(min(canvas_w, canvas_h) * SAFE_MARGIN_FRACTION)
    max_w = round(canvas_w * 0.22)
    max_h = round(canvas_h * 0.12)

    scale = min(max_w / logo.width, max_h / logo.height, 1.0)
    new_size = (max(1, round(logo.width * scale)), max(1, round(logo.height * scale)))
    logo = logo.resize(new_size, Image.LANCZOS)

    corners = {
        "top_left": (margin, margin),
        "top_right": (canvas_w - margin - logo.width, margin),
        "bottom_left": (margin, canvas_h - margin - logo.height),
        "bottom_right": (canvas_w - margin - logo.width, canvas_h - margin - logo.height),
    }

    if position == "auto":
        candidates = ["bottom_right", "bottom_left", "top_right", "top_left"]
        best = min(candidates, key=lambda c: _region_luminance_variance(img, corners[c], logo.size))
        xy = corners[best]
    else:
        xy = corners.get(position, corners["bottom_right"])

    img = img.convert("RGBA")
    img.alpha_composite(logo, dest=xy)
    return img


def _region_luminance_variance(img, xy, size):
    x0, y0 = xy
    x1, y1 = x0 + size[0], y0 + size[1]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return 0
    region = img.crop((x0, y0, x1, y1)).convert("L")
    return ImageStat.Stat(region).stddev[0]


def render_typography(image_bytes: bytes, *, layout_key: str, title: str = "", names: list | None = None,
                       tagline: str = "", date_time_text: str = "", cta: str = "",
                       metallic: bool = False) -> bytes:
    """Composites all deterministic text onto the generated artwork. Returns
    final PNG bytes. `names` is one string for single_hero, or exactly two
    strings ([name_a, name_b]) for battle_vs/finals_dual layouts.
    """
    names = names or []
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    zones = LAYOUTS.get(layout_key, LAYOUTS["single_hero"])

    if title and "title" in zones:
        _draw_block(img, draw, title, zones["title"], weight=800, max_lines=2, metallic=metallic)

    if tagline and "tagline" in zones:
        _draw_block(img, draw, tagline, zones["tagline"], weight=500, min_size=16, max_lines=2)

    if layout_key in ("battle_vs", "finals_dual") and len(names) == 2:
        _draw_block(img, draw, names[0], zones["name_a"], weight=800, max_lines=2, align="center")
        _draw_block(img, draw, names[1], zones["name_b"], weight=800, max_lines=2, align="center")
    elif names and "names" in zones:
        _draw_block(img, draw, " & ".join(names), zones["names"], weight=800, max_lines=2)

    if date_time_text and "date_time" in zones:
        _draw_block(img, draw, date_time_text, zones["date_time"], weight=600, min_size=16, max_lines=1)

    if cta and "cta" in zones:
        _draw_block(img, draw, cta, zones["cta"], weight=600, min_size=14, max_lines=1)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG")
    return out.getvalue()
