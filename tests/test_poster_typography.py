import io

from PIL import Image

from poster.config import POSTER_SIZES
from poster.image_processor import crop_to_size
from poster.typography import place_logo, render_typography


def _bg(w, h, color=(30, 30, 40)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def test_long_participant_name_does_not_overflow_canvas():
    canvas_w, canvas_h = 1080, 1080
    out = render_typography(
        _bg(canvas_w, canvas_h), layout_key="single_hero",
        title="HAPPY BIRTHDAY",
        names=["Alexandra Priyanka Rajeshwari Wentworth-Bhattacharya the Third"],
        date_time_text="21 August 2026 • 7:00 PM IST",
    )
    img = Image.open(io.BytesIO(out))
    assert img.size == (canvas_w, canvas_h)  # never resizes the canvas to fit text


def test_battle_layout_keeps_both_names_readable_and_within_canvas():
    canvas_w, canvas_h = 1080, 1080
    out = render_typography(
        _bg(canvas_w, canvas_h), layout_key="battle_vs", title="OFFICIAL BATTLE",
        names=["Sushmita Devi Extraordinarily Long Display Name", "Bhoomika"],
        date_time_text="25 August 2026 • 10:30 PM IST",
    )
    img = Image.open(io.BytesIO(out))
    assert img.size == (canvas_w, canvas_h)


def test_typography_works_across_all_output_aspect_ratios():
    for size_key, spec in POSTER_SIZES.items():
        out = render_typography(
            _bg(spec["width"], spec["height"]), layout_key="finals_dual",
            title="Grand Finals", names=["Alex", "Sam"],
            date_time_text="1 Sept 2026 • 9:00 PM IST", tagline="Season 3",
        )
        img = Image.open(io.BytesIO(out))
        assert img.size == (spec["width"], spec["height"]), size_key


def test_missing_optional_fields_are_skipped_without_error():
    out = render_typography(_bg(1080, 1080), layout_key="single_hero", title="HAPPY BIRTHDAY")
    img = Image.open(io.BytesIO(out))
    assert img.size == (1080, 1080)


def test_crop_to_size_never_distorts_aspect_ratio():
    # A very wide source cropped down to a square target must not stretch —
    # output must be exactly the target size.
    wide = _bg(2000, 800)
    out = crop_to_size(wide, "square")
    img = Image.open(io.BytesIO(out))
    assert img.size == (1080, 1080)

    tall = _bg(800, 2000)
    out2 = crop_to_size(tall, "story")
    img2 = Image.open(io.BytesIO(out2))
    assert img2.size == (1080, 1920)


def test_logo_placement_preserves_aspect_ratio_and_stays_in_bounds():
    canvas = Image.open(io.BytesIO(_bg(1080, 1080))).convert("RGBA")
    logo_buf = io.BytesIO()
    Image.new("RGBA", (600, 200), (255, 255, 255, 255)).save(logo_buf, format="PNG")

    composited = place_logo(canvas, logo_buf.getvalue(), "bottom_right")
    assert composited.size == (1080, 1080)  # canvas itself is untouched in size


def test_logo_placement_auto_does_not_raise():
    canvas = Image.open(io.BytesIO(_bg(1080, 1350))).convert("RGBA")
    logo_buf = io.BytesIO()
    Image.new("RGBA", (300, 300), (10, 10, 10, 255)).save(logo_buf, format="PNG")
    composited = place_logo(canvas, logo_buf.getvalue(), "auto")
    assert composited.size == (1080, 1350)
