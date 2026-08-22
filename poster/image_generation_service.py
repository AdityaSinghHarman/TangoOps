"""Image-generation provider abstraction (Section 13).

poster_service.py (and nothing else) calls generate_poster_image(). Adding
or swapping a provider means adding a class here and updating get_provider()
— the rest of the pipeline never talks to an external API directly.
"""
import io
import time as time_module

import streamlit as st

from poster.config import (
    POSTER_GENERATION_TIMEOUT_SECONDS,
    POSTER_IMAGE_MODEL_DEFAULT,
    POSTER_MAX_RETRIES,
    POSTER_SIZES,
)


class ImageGenerationError(Exception):
    """User-facing generation failure — message is safe to show as-is."""


class ImageGenerationProvider:
    def generate(self, prompt: str, participant_images: list, reference_image: bytes | None, size_key: str) -> bytes:
        raise NotImplementedError


class OpenAIImageProvider(ImageGenerationProvider):
    def __init__(self, api_key: str, model: str, timeout: int):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key, timeout=timeout)
        self._model = model

    def generate(self, prompt: str, participant_images: list, reference_image: bytes | None, size_key: str) -> bytes:
        from openai import (
            APIConnectionError,
            APITimeoutError,
            AuthenticationError,
            BadRequestError,
            InternalServerError,
            PermissionDeniedError,
            RateLimitError,
        )

        provider_size = POSTER_SIZES[size_key]["provider_size"]

        images = [
            (f"participant_{i}.png", io.BytesIO(b), "image/png")
            for i, b in enumerate(participant_images)
        ]
        if reference_image:
            images.append(("reference.png", io.BytesIO(reference_image), "image/png"))

        last_error = None
        for attempt in range(POSTER_MAX_RETRIES + 1):
            try:
                response = self._client.images.edit(
                    model=self._model,
                    image=images,
                    prompt=prompt[:32000],
                    size=provider_size,
                    quality="high",
                    n=1,
                )
                item = response.data[0]
                b64 = getattr(item, "b64_json", None)
                if not b64:
                    raise ImageGenerationError("The image provider returned no image data.")
                import base64
                return base64.b64decode(b64)

            except (AuthenticationError, PermissionDeniedError):
                print("poster_studio: OpenAI auth/permission error — check OPENAI_API_KEY")
                raise ImageGenerationError("The AI image service isn't configured correctly. Please contact support.")

            except BadRequestError as e:
                print(f"poster_studio: OpenAI bad request — {type(e).__name__}: {e}")
                raise ImageGenerationError("The AI image service rejected this request. Try different photos or wording.")

            except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError) as e:
                last_error = e
                if attempt < POSTER_MAX_RETRIES:
                    print(f"poster_studio: transient provider error (attempt {attempt + 1}), retrying — {type(e).__name__}")
                    time_module.sleep(min(2 ** attempt, 8))
                    continue
                print(f"poster_studio: provider unavailable after retries — {type(e).__name__}: {e}")
                raise ImageGenerationError("The AI image service is temporarily unavailable. Please try again shortly.")

            except Exception as e:
                print(f"poster_studio: unexpected provider error — {type(e).__name__}: {e}")
                raise ImageGenerationError("Something went wrong generating the poster. Please try again.")

        raise ImageGenerationError("The AI image service is temporarily unavailable. Please try again shortly.") from last_error


def _get_openai_config():
    try:
        cfg = st.secrets.get("openai", {})
    except Exception:
        cfg = {}
    api_key = cfg.get("api_key") if cfg else None
    if not api_key:
        return None, None, None
    model = cfg.get("model", POSTER_IMAGE_MODEL_DEFAULT)
    timeout = int(cfg.get("timeout", POSTER_GENERATION_TIMEOUT_SECONDS))
    return api_key, model, timeout


def get_provider() -> ImageGenerationProvider:
    api_key, model, timeout = _get_openai_config()
    if not api_key:
        raise ImageGenerationError("AI Poster Studio isn't configured yet — an OpenAI API key is required.")
    return OpenAIImageProvider(api_key=api_key, model=model, timeout=timeout)


def generate_poster_image(prompt: str, participant_images: list, reference_image: bytes | None, size_key: str) -> bytes:
    """Returns raw generated image bytes (PNG). Raises ImageGenerationError
    with a message that's already safe to show to the end user.
    """
    provider = get_provider()
    return provider.generate(prompt, participant_images, reference_image, size_key)
