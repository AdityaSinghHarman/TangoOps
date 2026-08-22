"""Orchestrates the full pipeline (Section 60):

validation -> category config -> prompt builder -> AI image generation ->
canvas normalization -> Python typography -> logo compositing -> quality
validation -> GenerationResult.

This is the only module the Streamlit UI calls into for generation.
"""
import time
import uuid
from datetime import datetime, timezone as dt_timezone

from PIL import Image
import io

from poster.categories import PosterCategory, get_category
from poster.config import METALLIC_STYLE_KEYS, POSTER_IMAGE_MODEL_DEFAULT, POSTER_PROMPT_VERSION, POSTER_SIZES
from poster.image_generation_service import ImageGenerationError, generate_poster_image
from poster.image_processor import analyze_image, crop_to_size
from poster.models import GenerationMetadata, GenerationResult, PosterRequest
from poster.prompt_builder import build_poster_prompt
from poster.typography import place_logo, render_typography

_DEFAULT_TITLES = {
    "birthday": "HAPPY BIRTHDAY",
    "glam_birthday": "HAPPY BIRTHDAY",
    "official_battle": "OFFICIAL BATTLE",
    "battle_promotion": "COMING SOON",
}


class PosterServiceError(Exception):
    """User-facing failure at any pipeline stage — safe to display as-is."""


def _resolve_title(category: PosterCategory, request: PosterRequest) -> str:
    if request.event_title:
        return request.event_title
    if category.key in ("official_battle", "battle_promotion") and request.battle_title:
        return request.battle_title
    return _DEFAULT_TITLES.get(category.key, category.label.upper())


def _resolve_tagline(request: PosterRequest) -> str:
    return request.tagline or request.subtitle or request.competition_name or ""


def _resolve_date_time_text(request: PosterRequest) -> str:
    parts = [p for p in (request.event_date, request.event_time) if p]
    text = " • ".join(parts)
    if request.timezone and request.event_time:
        text = f"{text} {request.timezone}"
    return text


def generate_poster(request: PosterRequest, *, business_id: str = "", regeneration_seed: str | None = None) -> GenerationResult:
    """Runs one full generation. Raises PosterServiceError on any failure
    that should stop and show the user a message; always returns a
    GenerationResult on success.
    """
    generation_id = str(uuid.uuid4())
    started = time.monotonic()
    category = get_category(request.category_key)

    try:
        participant_bytes = [p.image_bytes for p in request.participants]
        participant_names = [p.name for p in request.participants]

        image_analysis = None
        if participant_bytes:
            try:
                image_analysis = analyze_image(participant_bytes[0])
            except Exception:
                image_analysis = None

        prompt = build_poster_prompt(
            category=category,
            participant_names=participant_names,
            event_title=request.event_title,
            date=request.event_date,
            time=request.event_time,
            timezone=request.timezone,
            style=request.style_key,
            creative_freedom=request.creative_freedom,
            custom_instruction=request.custom_instruction or None,
            has_reference=bool(request.reference_poster_bytes),
            has_logo=bool(request.logo_bytes),
            image_analysis=image_analysis,
        )
        if regeneration_seed:
            prompt += f"\n\n[variation_seed={regeneration_seed}]"

        raw_image = generate_poster_image(
            prompt=prompt,
            participant_images=participant_bytes,
            reference_image=request.reference_poster_bytes,
            size_key=request.output_size_key,
        )

        normalized = crop_to_size(raw_image, request.output_size_key)

        typeset = render_typography(
            normalized,
            layout_key=category.layout,
            title=_resolve_title(category, request),
            names=participant_names,
            tagline=_resolve_tagline(request),
            date_time_text=_resolve_date_time_text(request),
            cta=request.cta,
            metallic=request.style_key in METALLIC_STYLE_KEYS,
        )

        final_bytes = typeset
        if request.logo_bytes:
            img = Image.open(io.BytesIO(typeset))
            img = place_logo(img, request.logo_bytes, request.logo_position)
            out = io.BytesIO()
            img.convert("RGB").save(out, format="PNG")
            final_bytes = out.getvalue()

        _validate_output(final_bytes, request.output_size_key)

        duration = round(time.monotonic() - started, 2)
        metadata = GenerationMetadata(
            generation_id=generation_id,
            category=category.key,
            style=request.style_key,
            creative_freedom=request.creative_freedom,
            participant_names=participant_names,
            event_date=request.event_date,
            event_time=request.event_time,
            timezone=request.timezone,
            output_size=request.output_size_key,
            provider="openai",
            model=POSTER_IMAGE_MODEL_DEFAULT,
            prompt_version=POSTER_PROMPT_VERSION,
            created_at=datetime.now(dt_timezone.utc).isoformat(),
            duration_seconds=duration,
            success=True,
        )
        print(f"poster_studio: generation {generation_id} succeeded in {duration}s (category={category.key})")
        return GenerationResult(image_bytes=final_bytes, metadata=metadata)

    except ImageGenerationError as e:
        _log_failure(generation_id, category.key, started, "provider_error")
        raise PosterServiceError(str(e))
    except PosterServiceError:
        raise
    except Exception as e:
        print(f"poster_studio: generation {generation_id} failed unexpectedly — {type(e).__name__}: {e}")
        _log_failure(generation_id, category.key, started, "internal_error")
        raise PosterServiceError("Something went wrong while creating your poster. Please try again.")


def _log_failure(generation_id, category_key, started, error_type):
    duration = round(time.monotonic() - started, 2)
    print(f"poster_studio: generation {generation_id} failed after {duration}s (category={category_key}, error_type={error_type})")


def _validate_output(image_bytes: bytes, size_key: str) -> None:
    if not image_bytes:
        raise PosterServiceError("The generated poster came back empty. Please try again.")
    spec = POSTER_SIZES[size_key]
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except Exception:
        raise PosterServiceError("The generated poster couldn't be validated. Please try again.")
    img = Image.open(io.BytesIO(image_bytes))
    if img.size != (spec["width"], spec["height"]):
        raise PosterServiceError("The generated poster came back with the wrong dimensions. Please try again.")
