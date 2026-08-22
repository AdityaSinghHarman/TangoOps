"""Builds the single structured instruction sent to the image-generation
provider. This is the ONLY place prompt text gets assembled — nothing else
in the pipeline or UI constructs prompt strings (Section 15).
"""
from poster.categories import PosterCategory
from poster.config import POSTER_PROMPT_VERSION

MASTER_DESIGN_RULES = """\
You are a senior advertising art director and promotional poster designer \
working for a premium live-streaming platform. Produce a professional \
commercial event-poster composition with:
- strong visual hierarchy and intentional negative space
- cinematic, premium lighting with controlled highlights and appropriate contrast
- sharp subject rendering with clean, realistic skin texture (no plastic/over-smoothed skin)
- clean subject extraction with no extraction halos or matte fringing
- clear foreground/midground/background separation and visual depth
- dimensional, sophisticated decorative elements used with restraint, not clutter
- a professional, social-media-ready advertising aesthetic

Avoid: cheap clip-art appearance, malformed anatomy, duplicate people, \
distorted faces, unnecessary facial alteration, excessive skin smoothing, \
low-resolution or muddy textures, inconsistent lighting, visual clutter, \
stretched or distorted logos, random unrelated graphical objects, bad \
perspective, and unreadable visual hierarchy.

CRITICAL — leave clean, uncluttered text-safe zones (areas of simple \
background, not busy detail) roughly matching where a title, participant \
name(s), and event date/time would sit for this poster's layout. Do NOT \
render any of your own readable title, name, date, or time text into the \
image — all of that text is added afterward with exact, deterministic \
typography. Any decorative lettering you do include must be abstract/\
illegible, never real words.

IDENTITY PRESERVATION — every uploaded participant photo is an identity \
reference, not a generic model. Preserve each person's face, facial \
structure, recognizable appearance, skin tone, hairstyle where practical, \
and general body proportions. You may enhance lighting, sharpness, tonal \
balance, and integration with the poster's lighting, but the resulting \
person must remain clearly recognizable as the uploaded individual — do \
not beautify them into a different-looking person."""


STYLE_RULES = {
    "auto": "Visual style: choose a sophisticated palette and lighting direction that best complements the participant photo(s) and the category — do not default to the same look every time.",
    "luxury_gold": "Visual style: Luxury Gold — warm gold and champagne tones, metallic highlights, elegant premium lighting.",
    "black_gold": "Visual style: Black & Gold — deep black base with gold accents, high-contrast, editorial luxury feel.",
    "glam_red": "Visual style: Glam Red — rich red and gold/black accents, glamorous cinematic lighting.",
    "elegant_pink": "Visual style: Elegant Pink — soft pink and gold, refined and elegant, not childish.",
    "royal_purple": "Visual style: Royal Purple — deep purple and gold, regal and premium.",
    "neon_arena": "Visual style: Neon Arena — dark arena background, vivid neon rim lighting, high-energy competitive mood.",
    "red_vs_blue": "Visual style: Red vs Blue — two-sided complementary red/blue palette split across the frame, high contrast.",
    "championship": "Visual style: Championship — gold and deep navy/black, trophy-grade prestige lighting.",
    "floral_premium": "Visual style: Floral Premium — tasteful dimensional floral accents, soft premium lighting, not busy.",
    "cinematic": "Visual style: Cinematic — filmic lighting and color grade, dramatic but clean composition.",
    "minimal_premium": "Visual style: Minimal Premium — restrained palette, large negative space, quiet luxury.",
    "festival": "Visual style: Festival — vibrant celebratory palette with dimensional light and particle accents.",
    "custom": "Visual style: follow the additional creative direction below closely for palette and mood.",
}

CREATIVE_FREEDOM_RULES = {
    "reference_focused": "Creative freedom: Reference Focused — stay relatively close to the reference poster's composition and style where one is supplied.",
    "balanced": "Creative freedom: Balanced — use any reference poster as inspiration for composition/palette/mood while introducing original ideas; do not copy it.",
    "highly_creative": "Creative freedom: Highly Creative — treat the event/category/reference only as loose direction and create a substantially new, original premium concept.",
}


def build_poster_prompt(
    category: PosterCategory,
    participant_names: list,
    event_title: str = "",
    date: str = "",
    time: str = "",
    timezone: str = "",
    style: str = "auto",
    creative_freedom: str = "balanced",
    custom_instruction: str | None = None,
    has_reference: bool = False,
    has_logo: bool = False,
    image_analysis: dict | None = None,
) -> str:
    """Combine MASTER / CATEGORY / STYLE / USER EVENT DATA / REFERENCE
    GUIDANCE into one structured prompt string. Pure function — no I/O.
    """
    sections = [MASTER_DESIGN_RULES]

    category_lines = [
        f"CATEGORY: {category.label}",
        f"Composition guidance: {category.composition_guidance}",
    ]
    if category.motifs:
        category_lines.append("Motifs to draw from selectively (do not use all of them at once): " + ", ".join(category.motifs) + ".")
    category_lines.append(f"Suggested palette direction: {category.default_palette}.")
    sections.append("\n".join(category_lines))

    sections.append(STYLE_RULES.get(style, STYLE_RULES["auto"]))
    sections.append(CREATIVE_FREEDOM_RULES.get(creative_freedom, CREATIVE_FREEDOM_RULES["balanced"]))

    event_lines = ["EVENT DATA (for context only — do not render this text into the image):"]
    if event_title:
        event_lines.append(f"- Event title: {event_title}")
    if participant_names:
        if len(participant_names) == 1:
            event_lines.append(f"- Participant: {participant_names[0]}")
        else:
            event_lines.append(f"- Participants: {', '.join(participant_names)}")
    if date:
        event_lines.append(f"- Date: {date}")
    if time:
        event_lines.append(f"- Time: {time}" + (f" {timezone}" if timezone else ""))
    sections.append("\n".join(event_lines))

    if has_reference:
        sections.append(
            "REFERENCE GUIDANCE: a reference poster is supplied for composition, "
            "palette, hierarchy, lighting, decorative language, framing, and "
            "overall mood inspiration only. Do not reproduce it, and do not "
            "carry over any people who appear in it — the uploaded participant "
            "photo(s) are the only identity references that matter."
        )

    if has_logo:
        sections.append(
            "A brand logo will be composited on top of the finished image "
            "afterward — leave a clear, uncluttered corner or edge area free "
            "for it; do not place your own logo-like graphics there."
        )

    if style == "auto" and image_analysis:
        sections.append(
            "AUTO PALETTE SIGNAL: choose a complementary palette informed by the "
            f"participant photo (dominant tone ~{image_analysis.get('dominant_color', '#808080')}, "
            f"overall brightness {'high' if image_analysis.get('brightness', 0.5) > 0.6 else 'low' if image_analysis.get('brightness', 0.5) < 0.35 else 'medium'}, "
            f"background reads as {image_analysis.get('background_complexity', 'simple')}) rather than "
            "reusing the same palette on every poster."
        )

    if custom_instruction:
        sections.append(f"ADDITIONAL CREATIVE DIRECTION (supplements, does not override, the rules above): {custom_instruction}")

    sections.append(f"[prompt_version={POSTER_PROMPT_VERSION}]")
    return "\n\n".join(sections)
