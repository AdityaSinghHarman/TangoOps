from poster.categories import get_category
from poster.prompt_builder import build_poster_prompt


def test_birthday_prompt_includes_master_and_category_rules():
    category = get_category("birthday")
    prompt = build_poster_prompt(
        category, ["Riya"], date="21 August 2026", time="7:00 PM", timezone="IST",
        style="auto", creative_freedom="balanced",
    )
    assert "senior advertising art director" in prompt
    assert "Birthday Celebration" in prompt
    assert "Riya" in prompt
    assert "21 August 2026" in prompt
    assert "[prompt_version=" in prompt
    # AI must not be told to render exact text itself
    assert "leave clean, uncluttered text-safe zones" in prompt


def test_official_battle_prompt_avoids_declaring_a_winner():
    category = get_category("official_battle")
    prompt = build_poster_prompt(
        category, ["Sushmita", "Bhoomika"], date="25 August 2026", time="10:30 PM",
        timezone="IST", style="neon_arena", creative_freedom="balanced",
    )
    assert "Sushmita" in prompt and "Bhoomika" in prompt
    assert "Do NOT visually declare a winner" in prompt
    assert "Neon Arena" in prompt


def test_finals_prompt_uses_finals_composition_guidance():
    category = get_category("finals")
    prompt = build_poster_prompt(
        category, ["Alex", "Sam"], event_title="Grand Finals", date="1 Sept 2026",
        time="9:00 PM", timezone="IST", style="championship", creative_freedom="highly_creative",
    )
    assert "Grand Finals" in prompt
    assert "championship treatment" in prompt
    assert "Highly Creative" in prompt


def test_reference_and_logo_guidance_only_appear_when_supplied():
    category = get_category("birthday")
    without = build_poster_prompt(category, ["Riya"], style="auto", creative_freedom="balanced")
    with_both = build_poster_prompt(
        category, ["Riya"], style="auto", creative_freedom="balanced",
        has_reference=True, has_logo=True,
    )
    assert "REFERENCE GUIDANCE" not in without
    assert "REFERENCE GUIDANCE" in with_both
    assert "brand logo will be composited" in with_both


def test_custom_instruction_is_appended_but_labeled_as_supplemental():
    category = get_category("custom")
    prompt = build_poster_prompt(
        category, [], event_title="Launch Night", style="custom", creative_freedom="balanced",
        custom_instruction="royal black and gold theme with dramatic spotlights",
    )
    assert "royal black and gold theme" in prompt
    assert "supplements, does not override" in prompt


def test_prompt_version_is_stable_and_traceable():
    category = get_category("winner")
    prompt = build_poster_prompt(category, ["Alex"], event_title="Top Streamer 2026", style="auto", creative_freedom="balanced")
    assert "[prompt_version=1.0]" in prompt
