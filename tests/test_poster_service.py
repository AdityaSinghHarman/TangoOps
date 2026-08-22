"""poster_service.generate_poster() end-to-end, with the provider mocked out.
Never calls a real (paid) image API — see conftest-less monkeypatch below.
"""
import io

import pytest
from PIL import Image

import poster.poster_service as poster_service
from poster.models import ParticipantImage, PosterRequest


def _png(w=600, h=800, color=(200, 50, 50)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def _fake_generate_poster_image(prompt, participant_images, reference_image, size_key):
    from poster.config import POSTER_SIZES
    spec = POSTER_SIZES[size_key]
    # Return something plausibly poster-shaped so downstream cropping works.
    return _png(spec["width"], spec["height"] + 200)


@pytest.fixture(autouse=True)
def mock_provider(monkeypatch):
    monkeypatch.setattr(poster_service, "generate_poster_image", _fake_generate_poster_image)


def test_generate_poster_birthday_end_to_end():
    request = PosterRequest(
        category_key="birthday",
        participants=[ParticipantImage(name="Riya", image_bytes=_png())],
        event_date="21 August 2026", event_time="7:00 PM", timezone="IST",
        style_key="auto", creative_freedom="balanced", output_size_key="square",
    )
    result = poster_service.generate_poster(request, business_id="biz_1")
    assert result.metadata.success is True
    assert result.metadata.category == "birthday"
    assert result.metadata.participant_names == ["Riya"]
    img = Image.open(io.BytesIO(result.image_bytes))
    assert img.size == (1080, 1080)


def test_generate_poster_official_battle_end_to_end():
    request = PosterRequest(
        category_key="official_battle",
        participants=[
            ParticipantImage(name="Sushmita", image_bytes=_png()),
            ParticipantImage(name="Bhoomika", image_bytes=_png()),
        ],
        event_date="25 August 2026", event_time="10:30 PM", timezone="IST",
        style_key="neon_arena", creative_freedom="balanced", output_size_key="story",
    )
    result = poster_service.generate_poster(request, business_id="biz_1")
    assert result.metadata.participant_names == ["Sushmita", "Bhoomika"]
    img = Image.open(io.BytesIO(result.image_bytes))
    assert img.size == (1080, 1920)


def test_generation_id_is_unique_per_call():
    request = PosterRequest(
        category_key="winner",
        participants=[ParticipantImage(name="Alex", image_bytes=_png())],
        event_title="Top Streamer 2026", timezone="IST",
        style_key="auto", creative_freedom="balanced", output_size_key="square",
    )
    r1 = poster_service.generate_poster(request, business_id="biz_1")
    r2 = poster_service.generate_poster(request, business_id="biz_1")
    assert r1.metadata.generation_id != r2.metadata.generation_id


def test_provider_error_is_translated_to_service_error(monkeypatch):
    from poster.image_generation_service import ImageGenerationError

    def boom(*a, **kw):
        raise ImageGenerationError("The AI image service is temporarily unavailable. Please try again shortly.")

    monkeypatch.setattr(poster_service, "generate_poster_image", boom)

    request = PosterRequest(
        category_key="birthday",
        participants=[ParticipantImage(name="Riya", image_bytes=_png())],
        event_date="21 August 2026", event_time="7:00 PM", timezone="IST",
        style_key="auto", creative_freedom="balanced", output_size_key="square",
    )
    with pytest.raises(poster_service.PosterServiceError):
        poster_service.generate_poster(request, business_id="biz_1")
