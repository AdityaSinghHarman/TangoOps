"""Centralized configuration for AI Poster Studio.

No Streamlit import here on purpose — kept pure/constants-only so it can be
imported by tests and by any part of the pipeline without pulling in a
running app. Secrets (API keys) are read where they're used
(image_generation_service.py), not here.
"""

POSTER_PROMPT_VERSION = "1.0"

# ---------------------------------------------------------------- uploads --
POSTER_MAX_UPLOAD_MB = 8
POSTER_MAX_UPLOAD_BYTES = POSTER_MAX_UPLOAD_MB * 1_000_000
POSTER_MAX_PARTICIPANT_IMAGES = 6  # headroom beyond today's 1-2 per category
MIN_IMAGE_DIM_PX = 200
MAX_IMAGE_DIM_PX = 8000  # guards against decompression-bomb style uploads
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

MAX_EVENT_TITLE_CHARS = 80
MAX_PARTICIPANT_NAME_CHARS = 40
MAX_TAGLINE_CHARS = 100
MAX_CUSTOM_INSTRUCTION_CHARS = 300

# ------------------------------------------------------------- generation --
POSTER_IMAGE_PROVIDER = "openai"
POSTER_IMAGE_MODEL_DEFAULT = "gpt-image-1"
POSTER_GENERATION_TIMEOUT_SECONDS = 90
POSTER_MAX_RETRIES = 2  # bounded retries on top of the first attempt

# Final output sizes offered in the UI, mapped to the nearest size the
# provider natively supports. image_processor.py crops/letterboxes from the
# generated image down to the exact final dimensions — never stretches.
POSTER_SIZES = {
    "square": {"label": "Square Social", "width": 1080, "height": 1080, "provider_size": "1024x1024"},
    "portrait": {"label": "Portrait Social", "width": 1080, "height": 1350, "provider_size": "1024x1536"},
    "story": {"label": "Story / Reel", "width": 1080, "height": 1920, "provider_size": "1024x1536"},
}
DEFAULT_POSTER_SIZE_KEY = "square"

STYLE_PRESETS = [
    ("auto", "Auto / Surprise Me"),
    ("luxury_gold", "Luxury Gold"),
    ("black_gold", "Black & Gold"),
    ("glam_red", "Glam Red"),
    ("elegant_pink", "Elegant Pink"),
    ("royal_purple", "Royal Purple"),
    ("neon_arena", "Neon Arena"),
    ("red_vs_blue", "Red vs Blue"),
    ("championship", "Championship"),
    ("floral_premium", "Floral Premium"),
    ("cinematic", "Cinematic"),
    ("minimal_premium", "Minimal Premium"),
    ("festival", "Festival"),
    ("custom", "Custom"),
]
DEFAULT_STYLE_KEY = "auto"
METALLIC_STYLE_KEYS = {"luxury_gold", "black_gold", "championship", "glam_red"}

CREATIVE_FREEDOM_LEVELS = [
    ("reference_focused", "Reference Focused"),
    ("balanced", "Balanced"),
    ("highly_creative", "Highly Creative"),
]
DEFAULT_CREATIVE_FREEDOM = "balanced"

LOGO_POSITIONS = [
    ("auto", "Auto"),
    ("top_left", "Top Left"),
    ("top_right", "Top Right"),
    ("bottom_left", "Bottom Left"),
    ("bottom_right", "Bottom Right"),
]
DEFAULT_LOGO_POSITION = "auto"

FONT_DIR = "assets/fonts"
FONT_VARIABLE_FILE = "Inter-Variable.ttf"

# ---------------------------------------------------------------- demo mode --
# Demo Mode skips the paid AI call entirely and runs a Pillow-generated
# placeholder gradient through the same real typography/logo pipeline —
# lets the whole UI and the deterministic-text output be exercised for
# free. Two gradient endpoint colors per style, used only by
# image_processor.generate_placeholder_background().
DEMO_STYLE_GRADIENTS = {
    "auto": ("#2b2440", "#6b5b95"),
    "luxury_gold": ("#231a0f", "#caa15d"),
    "black_gold": ("#0b0b0b", "#b8902f"),
    "glam_red": ("#2a0a0a", "#b5273b"),
    "elegant_pink": ("#3a1f2e", "#e8a0c4"),
    "royal_purple": ("#1f1240", "#7c3aed"),
    "neon_arena": ("#05050f", "#22d3ee"),
    "red_vs_blue": ("#7a1f2b", "#1f3f9e"),
    "championship": ("#151515", "#d4af37"),
    "floral_premium": ("#2e1f2a", "#e8b4c8"),
    "cinematic": ("#10131a", "#3a4a63"),
    "minimal_premium": ("#e9e6df", "#b9b3a6"),
    "festival": ("#3a1050", "#f2994a"),
    "custom": ("#211a4a", "#7c3aed"),
}
DEMO_WATERMARK_TEXT = "DEMO PREVIEW — placeholder artwork, not AI-generated"


# ---------------------------------------------------- cost-control stubs --
# Deliberately trivial today (no billing/quota system exists yet for this
# feature). Kept as real call sites so a future quota system plugs in here
# without touching poster_service.py or ui.py.
def can_generate_poster(business_id, plan_code=None) -> bool:
    return True


def get_poster_generation_allowance(business_id, plan_code=None):
    """Returns None for unlimited, else an int remaining-generations count."""
    return None
