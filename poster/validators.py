"""Upload validation, text sanitization, and filename safety for Poster Studio.

Nothing here trusts an uploaded filename or a claimed content-type. Every
image is decoded, verified, and re-encoded to PNG before it's used anywhere
else in the pipeline — re-encoding through Pillow strips anything that
wasn't actual pixel data (metadata payloads, polyglot files, etc.) and
means the app never "executes" an upload, it only ever reads pixels out of
it.
"""
import io
import re
import unicodedata

from PIL import Image

from poster.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_DIM_PX,
    MIN_IMAGE_DIM_PX,
    POSTER_MAX_UPLOAD_BYTES,
    POSTER_MAX_UPLOAD_MB,
)


class PosterValidationError(ValueError):
    """User-facing validation failure — message is safe to show as-is."""


def validate_and_normalize_image(raw_bytes: bytes, *, original_filename: str = "upload") -> bytes:
    """Validate an uploaded image and return re-encoded PNG bytes.

    Raises PosterValidationError with a message safe to show to the user.
    """
    if not raw_bytes:
        raise PosterValidationError("That file is empty.")

    if len(raw_bytes) > POSTER_MAX_UPLOAD_BYTES:
        raise PosterValidationError(f"That image is larger than the {POSTER_MAX_UPLOAD_MB} MB limit.")

    ext = (original_filename.rsplit(".", 1)[-1] if "." in original_filename else "").lower()
    if ext and ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise PosterValidationError("Unsupported file type. Use JPG, PNG, or WEBP.")

    try:
        probe = Image.open(io.BytesIO(raw_bytes))
        probe.verify()  # decodes and checks structure; the file object is unusable after this
    except Exception:
        raise PosterValidationError("That file isn't a readable image, or it's corrupted.")

    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.load()
    except Exception:
        raise PosterValidationError("That file isn't a readable image, or it's corrupted.")

    width, height = img.size
    if width < MIN_IMAGE_DIM_PX or height < MIN_IMAGE_DIM_PX:
        raise PosterValidationError(f"That image is too small. Use at least {MIN_IMAGE_DIM_PX}x{MIN_IMAGE_DIM_PX}px.")
    if width > MAX_IMAGE_DIM_PX or height > MAX_IMAGE_DIM_PX:
        raise PosterValidationError("That image's dimensions are unreasonably large.")

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def validate_participant_count(category, count: int) -> None:
    if count < category.min_participants:
        noun = "participant" if category.min_participants == 1 else "participants"
        raise PosterValidationError(f"{category.label} needs at least {category.min_participants} {noun}.")
    if count > category.max_participants:
        noun = "participant" if category.max_participants == 1 else "participants"
        raise PosterValidationError(f"{category.label} supports at most {category.max_participants} {noun}.")


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_text(value: str, max_len: int) -> str:
    """Strip control characters, collapse whitespace, enforce a max length.

    This is display/prompt text, not SQL or HTML — the point is to keep it
    well-behaved (no embedded control characters, no runaway length going
    into an API prompt), not to escape markup.
    """
    if not value:
        return ""
    value = unicodedata.normalize("NFKC", str(value))
    value = _CONTROL_CHARS_RE.sub("", value)
    value = _WHITESPACE_RE.sub(" ", value).strip()
    return value[:max_len]


_FILENAME_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def sanitize_filename_component(value: str, *, max_len: int = 40, fallback: str = "poster") -> str:
    """Turn arbitrary text (a participant name, event title, ...) into a
    safe filename fragment. Never derived from or reflects the original
    uploaded filename — that's discarded entirely on upload.
    """
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    value = value.strip().replace(" ", "_")
    value = _FILENAME_SAFE_RE.sub("", value)
    value = value.strip("_-")[:max_len]
    return value or fallback
