import io

import pytest
from PIL import Image

from poster.categories import get_category
from poster.validators import (
    PosterValidationError,
    sanitize_filename_component,
    sanitize_text,
    validate_and_normalize_image,
    validate_participant_count,
)


def _png(w=600, h=800, color=(200, 50, 50)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def test_valid_image_is_normalized_to_png():
    out = validate_and_normalize_image(_png(), original_filename="photo.jpg")
    img = Image.open(io.BytesIO(out))
    assert img.format == "PNG"


def test_rejects_unsupported_extension():
    with pytest.raises(PosterValidationError):
        validate_and_normalize_image(_png(), original_filename="photo.gif")


def test_rejects_corrupt_or_unreadable_file():
    with pytest.raises(PosterValidationError):
        validate_and_normalize_image(b"this is not an image", original_filename="photo.png")


def test_rejects_empty_file():
    with pytest.raises(PosterValidationError):
        validate_and_normalize_image(b"", original_filename="photo.png")


def test_rejects_oversized_file():
    huge = b"\x89PNG\r\n\x1a\n" + b"0" * (9_000_000)
    with pytest.raises(PosterValidationError):
        validate_and_normalize_image(huge, original_filename="photo.png")


def test_rejects_too_small_image():
    with pytest.raises(PosterValidationError):
        validate_and_normalize_image(_png(50, 50), original_filename="tiny.png")


def test_missing_participant_below_category_minimum():
    category = get_category("official_battle")
    with pytest.raises(PosterValidationError):
        validate_participant_count(category, 1)  # battle requires exactly 2


def test_missing_participant_zero_for_birthday():
    category = get_category("birthday")
    with pytest.raises(PosterValidationError):
        validate_participant_count(category, 0)


def test_too_many_participants_rejected():
    category = get_category("birthday")
    with pytest.raises(PosterValidationError):
        validate_participant_count(category, 2)  # birthday caps at 1


def test_sanitize_text_strips_control_chars_and_truncates():
    result = sanitize_text("Name\x00 With\x1f Junk" + "x" * 100, max_len=20)
    assert "\x00" not in result
    assert len(result) == 20


def test_sanitize_text_empty_is_safe():
    assert sanitize_text("", 10) == ""
    assert sanitize_text(None, 10) == ""


def test_sanitize_filename_component_strips_unsafe_chars():
    assert sanitize_filename_component("Riya! @2026 <script>") == "Riya_2026_script"


def test_sanitize_filename_component_never_trusts_original_filename():
    # The function only ever receives derived text (a name/category/date),
    # never the raw uploaded filename — this just proves it handles
    # path-traversal-shaped input safely if it ever were passed such a thing.
    assert "/" not in sanitize_filename_component("../../etc/passwd")
    assert ".." not in sanitize_filename_component("../../etc/passwd")


def test_sanitize_filename_component_falls_back_when_empty():
    assert sanitize_filename_component("") == "poster"
    assert sanitize_filename_component("!!!") == "poster"
