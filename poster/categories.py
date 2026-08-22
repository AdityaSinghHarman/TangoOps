"""The extensible poster-category registry (Section 4/45 of the spec).

Adding a new category is one new POSTER_TYPES entry — no other file should
need an if/elif per category. UI form logic, the prompt builder, and the
typography layout system all read a category's fields from here.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PosterCategory:
    key: str
    label: str
    min_participants: int
    max_participants: int
    # Field keys the form must collect. "participant_name"/"participant_image"
    # repeat once per participant slot (see min/max_participants) rather than
    # being listed per-index here.
    required_fields: tuple
    optional_fields: tuple
    default_palette: str
    composition_guidance: str
    motifs: tuple
    default_style: str
    layout: str  # which typography.py layout spec to use


POSTER_TYPES = {
    "birthday": PosterCategory(
        key="birthday",
        label="Birthday Celebration",
        min_participants=1,
        max_participants=1,
        required_fields=("event_date", "event_time", "timezone"),
        optional_fields=("tagline", "theme", "reference_poster", "logo"),
        default_palette="gold and champagne, warm complementary accents drawn from the participant photo",
        composition_guidance=(
            "Single hero participant, celebratory but sophisticated composition. "
            "Cinematic portrait lighting on the subject, elegant frame or vignette, "
            "clear title zone above or beside the subject, event-information zone "
            "near the bottom with generous negative space around it."
        ),
        motifs=("premium balloons", "gifts", "ribbons", "confetti", "sparkles", "elegant frames"),
        default_style="auto",
        layout="single_hero",
    ),
    "glam_birthday": PosterCategory(
        key="glam_birthday",
        label="Premium / Glam Birthday",
        min_participants=1,
        max_participants=1,
        required_fields=("event_date", "event_time", "timezone"),
        optional_fields=("tagline", "theme", "reference_poster", "logo"),
        default_palette="black and gold, or burgundy and gold — dark, luxurious base with metallic accents",
        composition_guidance=(
            "Fashion/editorial cinematic portrait of the hero participant, luxury "
            "event-invitation feel. Dark premium background, gold typography zone, "
            "elegant ornaments, champagne particle accents, sophisticated rim "
            "lighting. Avoid childish birthday imagery unless explicitly requested."
        ),
        motifs=("champagne particles", "gold ornaments", "spotlight rim lighting", "editorial framing"),
        default_style="luxury_gold",
        layout="single_hero",
    ),
    "official_battle": PosterCategory(
        key="official_battle",
        label="Official Battle",
        min_participants=2,
        max_participants=2,
        required_fields=("event_date", "event_time", "timezone"),
        optional_fields=("battle_title", "theme", "reference_poster", "logo"),
        default_palette="red vs blue, or championship gold — two-sided complementary contrast",
        composition_guidance=(
            "Two participants with approximately equal visual prominence, opposing "
            "sides of the frame, a central VS emblem, dramatic rim lighting, arena "
            "or energy-streak background. Communicate competition immediately. Do "
            "NOT visually declare a winner — both sides read as evenly matched."
        ),
        motifs=("VS emblem", "arena lighting", "energy streaks", "fire or neon accents"),
        default_style="neon_arena",
        layout="battle_vs",
    ),
    "battle_promotion": PosterCategory(
        key="battle_promotion",
        label="Battle Promotion",
        min_participants=2,
        max_participants=2,
        required_fields=("event_date", "event_time", "timezone"),
        optional_fields=("battle_title", "theme", "reference_poster", "logo"),
        default_palette="red vs blue, high-contrast promotional colors",
        composition_guidance=(
            "Promotional announcement framing for an upcoming battle: both "
            "participants prominent and evenly weighted, bold promotional "
            "typography zone, countdown/anticipation mood rather than in-arena "
            "action. Do NOT visually declare a winner."
        ),
        motifs=("countdown graphics", "spotlight beams", "bold promotional banners"),
        default_style="red_vs_blue",
        layout="battle_vs",
    ),
    "finals": PosterCategory(
        key="finals",
        label="Finals / Competition",
        min_participants=2,
        max_participants=2,
        required_fields=("event_title", "event_date", "event_time", "timezone"),
        optional_fields=("subtitle", "competition_name", "reference_poster", "logo"),
        default_palette="royal gold and deep navy or black — championship prestige palette",
        composition_guidance=(
            "Two hero participants with a central championship treatment — crowns, "
            "trophy-inspired graphics, or a premium VS emblem. Royal spotlighting, "
            "stars, competition-stage atmosphere. Prestige over clutter — do not "
            "overcrowd the composition."
        ),
        motifs=("crowns", "championship frame", "spotlights", "stars", "trophy graphics"),
        default_style="championship",
        layout="finals_dual",
    ),
    "celebration": PosterCategory(
        key="celebration",
        label="Special Celebration",
        min_participants=1,
        max_participants=2,
        required_fields=("event_title", "event_date", "event_time", "timezone"),
        optional_fields=("subtitle", "theme", "reference_poster", "logo"),
        default_palette="festive complementary palette derived from the participant photo(s)",
        composition_guidance=(
            "Warm, festive hero composition celebrating a special occasion. "
            "Dimensional decorative elements, clear foreground/midground/background "
            "separation, generous negative space for the title and event details."
        ),
        motifs=("confetti", "dimensional ribbons", "soft particle light", "festive frame"),
        default_style="auto",
        layout="single_hero",
    ),
    "live_event": PosterCategory(
        key="live_event",
        label="Special Live Event",
        min_participants=1,
        max_participants=2,
        required_fields=("event_title", "event_date", "event_time", "timezone"),
        optional_fields=("subtitle", "theme", "reference_poster", "logo"),
        default_palette="cinematic stage palette — deep base tone with a single vivid accent",
        composition_guidance=(
            "Live-broadcast / on-stage energy: dramatic stage lighting, subtle "
            "motion-suggestive light streaks, clear social-media-ready hierarchy "
            "with the event title reading first."
        ),
        motifs=("stage spotlights", "light streaks", "broadcast framing"),
        default_style="cinematic",
        layout="single_hero",
    ),
    "winner": PosterCategory(
        key="winner",
        label="Winner / Achievement",
        min_participants=1,
        max_participants=1,
        required_fields=("event_title", "event_date", "timezone"),
        optional_fields=("tagline", "theme", "reference_poster", "logo"),
        default_palette="gold and white, victorious high-contrast palette",
        composition_guidance=(
            "Triumphant hero portrait, trophy or achievement-inspired graphical "
            "elements, radiant light rays or gold particle accents, confident and "
            "celebratory but not cluttered."
        ),
        motifs=("trophy graphics", "gold light rays", "achievement badge/emblem"),
        default_style="championship",
        layout="single_hero",
    ),
    "custom": PosterCategory(
        key="custom",
        label="Custom Poster",
        min_participants=0,
        max_participants=6,
        required_fields=("event_title",),
        optional_fields=(
            "event_date", "event_time", "timezone", "tagline", "theme",
            "reference_poster", "logo",
        ),
        default_palette="derived from the participant photo(s) and any custom instruction given",
        composition_guidance=(
            "Follow the additional creative direction and any reference poster "
            "closely, while still holding to the master art-direction quality bar. "
            "No fixed motif set — let the custom instruction and reference lead."
        ),
        motifs=(),
        default_style="custom",
        layout="single_hero",
    ),
}

DEFAULT_CATEGORY_KEY = "birthday"


def get_category(key: str) -> PosterCategory:
    if key not in POSTER_TYPES:
        raise KeyError(f"Unknown poster category: {key!r}")
    return POSTER_TYPES[key]


def category_choices():
    """[(key, label), ...] in the fixed display order from Section 4."""
    order = [
        "birthday", "glam_birthday", "official_battle", "battle_promotion",
        "finals", "celebration", "live_event", "winner", "custom",
    ]
    return [(k, POSTER_TYPES[k].label) for k in order]
