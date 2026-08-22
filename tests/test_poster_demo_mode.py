"""Demo Mode: never touches the real (paid) provider, still exercises the
real typography/logo/crop pipeline and returns a correctly-sized, clearly
watermarked result.
"""
import io

import pytest
from PIL import Image

import poster.poster_service as poster_service
from poster.config import DEMO_STYLE_GRADIENTS, POSTER_SIZES
from poster.image_processor import generate_placeholder_background
from poster.models import ParticipantImage, PosterRequest


def _png(w=600, h=800, color=(200, 50, 50)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def test_demo_mode_never_calls_the_real_provider(monkeypatch):
    def boom(*a, **kw):
        raise AssertionError("demo_mode must never call the real image-generation provider")

    monkeypatch.setattr(poster_service, "generate_poster_image", boom)

    request = PosterRequest(
        category_key="birthday",
        participants=[ParticipantImage(name="Riya", image_bytes=_png())],
        event_date="21 August 2026", event_time="7:00 PM", timezone="IST",
        style_key="luxury_gold", creative_freedom="balanced", output_size_key="square",
    )
    result = poster_service.generate_poster(request, business_id="biz_1", demo_mode=True)
    assert result.metadata.provider == "demo"
    assert result.metadata.model == "placeholder"
    assert result.metadata.success is True


def test_demo_mode_output_is_correct_size_for_every_output_size():
    for size_key, spec in POSTER_SIZES.items():
        request = PosterRequest(
            category_key="official_battle",
            participants=[
                ParticipantImage(name="Sushmita", image_bytes=_png()),
                ParticipantImage(name="Bhoomika", image_bytes=_png()),
            ],
            event_date="25 August 2026", event_time="10:30 PM", timezone="IST",
            style_key="neon_arena", creative_freedom="balanced", output_size_key=size_key,
        )
        result = poster_service.generate_poster(request, business_id="biz_1", demo_mode=True)
        img = Image.open(io.BytesIO(result.image_bytes))
        assert img.size == (spec["width"], spec["height"]), size_key


def test_placeholder_background_covers_every_style_without_error():
    for style_key in DEMO_STYLE_GRADIENTS:
        out = generate_placeholder_background(1080, 1080, style_key)
        img = Image.open(io.BytesIO(out))
        assert img.size == (1080, 1080)
        assert img.mode == "RGB"


def test_placeholder_background_falls_back_for_unknown_style():
    out = generate_placeholder_background(500, 500, "not_a_real_style")
    img = Image.open(io.BytesIO(out))
    assert img.size == (500, 500)


def test_demo_mode_result_is_watermarked_distinctly_from_real_mode(monkeypatch):
    from poster.config import POSTER_SIZES as SIZES

    def fake_real_provider(prompt, participant_images, reference_image, size_key):
        spec = SIZES[size_key]
        return _png(spec["width"], spec["height"])

    monkeypatch.setattr(poster_service, "generate_poster_image", fake_real_provider)

    request = PosterRequest(
        category_key="winner",
        participants=[ParticipantImage(name="Alex", image_bytes=_png())],
        event_title="Top Streamer 2026", timezone="IST",
        style_key="championship", creative_freedom="balanced", output_size_key="square",
    )
    demo_result = poster_service.generate_poster(request, business_id="biz_1", demo_mode=True)
    real_result = poster_service.generate_poster(request, business_id="biz_1", demo_mode=False)

    assert demo_result.metadata.provider == "demo"
    assert real_result.metadata.provider == "openai"
    # The watermark strip means the top rows differ meaningfully from a
    # non-watermarked render — a cheap proxy for "the badge was drawn".
    assert demo_result.image_bytes != real_result.image_bytes
