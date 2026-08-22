"""The AI Poster Studio Streamlit page (Section 40).

app.py calls poster.ui.render(...) from one page block — no other file
renders any part of this feature. Session-state keys are all prefixed
"poster_" to avoid colliding with the rest of the dashboard.
"""
import io

import streamlit as st
from PIL import Image

from poster.categories import POSTER_TYPES, category_choices, get_category
from poster.config import (
    CREATIVE_FREEDOM_LEVELS,
    DEFAULT_CATEGORY_KEY,
    DEFAULT_CREATIVE_FREEDOM,
    DEFAULT_LOGO_POSITION,
    DEFAULT_POSTER_SIZE_KEY,
    DEFAULT_STYLE_KEY,
    LOGO_POSITIONS,
    MAX_CUSTOM_INSTRUCTION_CHARS,
    MAX_EVENT_TITLE_CHARS,
    MAX_PARTICIPANT_NAME_CHARS,
    MAX_TAGLINE_CHARS,
    POSTER_MAX_UPLOAD_MB,
    POSTER_SIZES,
    STYLE_PRESETS,
    can_generate_poster,
)
from poster.models import ParticipantImage, PosterRequest
from poster.poster_service import PosterServiceError, generate_poster
from poster.validators import (
    PosterValidationError,
    sanitize_filename_component,
    sanitize_text,
    validate_and_normalize_image,
    validate_participant_count,
)

_TIMEZONES = [
    "IST (UTC+5:30)", "GMT (UTC+0:00)", "EST (UTC-5:00)", "PST (UTC-8:00)",
    "CET (UTC+1:00)", "SGT (UTC+8:00)", "AEST (UTC+10:00)",
]

_STATE_DEFAULTS = {
    "poster_category": DEFAULT_CATEGORY_KEY,
    "poster_style": DEFAULT_STYLE_KEY,
    "poster_creative_freedom": DEFAULT_CREATIVE_FREEDOM,
    "poster_output_size": DEFAULT_POSTER_SIZE_KEY,
    "poster_logo_position": DEFAULT_LOGO_POSITION,
    "poster_result": None,
    "poster_last_error": None,
    "poster_variation_counter": 0,
}


def _init_state():
    for key, default in _STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _field_label(field_key: str) -> str:
    return {
        "event_date": "Event Date", "event_time": "Event Time", "timezone": "Timezone",
        "tagline": "Tagline", "theme": "Theme", "reference_poster": "Reference Poster",
        "logo": "Brand Logo", "battle_title": "Battle Title", "subtitle": "Subtitle",
        "competition_name": "Competition Name", "event_title": "Event Title",
    }.get(field_key, field_key.replace("_", " ").title())


def _read_uploaded_image(uploaded_file, *, max_mb=POSTER_MAX_UPLOAD_MB):
    raw = uploaded_file.getvalue()
    return validate_and_normalize_image(raw, original_filename=uploaded_file.name)


def render(*, username: str, user_role: str, business_id: str, business_name: str = "") -> None:
    _init_state()

    st.markdown("## 🎨 AI Poster Studio")
    st.caption("Create a professional event poster from participant photos in a few steps.")

    if not can_generate_poster(business_id):
        st.warning("AI Poster Studio isn't available on your current plan yet.")
        return

    category_key = st.session_state["poster_category"]
    category = get_category(category_key)

    # ------------------------------------------------------------ STEP 1 --
    st.markdown("#### Step 1 · Poster Type")
    choices = category_choices()
    labels = [label for _, label in choices]
    keys = [key for key, _ in choices]
    idx = keys.index(category_key) if category_key in keys else 0
    selected_label = st.selectbox("Choose a poster type", labels, index=idx, key="poster_category_select")
    new_category_key = keys[labels.index(selected_label)]
    if new_category_key != category_key:
        st.session_state["poster_category"] = new_category_key
        st.session_state["poster_result"] = None
        st.rerun()
    category = get_category(category_key)

    # ------------------------------------------------------------ STEP 2 --
    st.markdown("#### Step 2 · Participants")
    max_slots = category.max_participants
    participants = []
    if max_slots == 0:
        st.caption("This poster type doesn't require a participant photo.")
    else:
        cols = st.columns(min(max_slots, 2)) if max_slots > 1 else [st.container()]
        for i in range(max_slots):
            required = i < category.min_participants
            col = cols[i % len(cols)]
            with col:
                label_suffix = f" {i + 1}" if max_slots > 1 else ""
                name = st.text_input(
                    f"Participant{label_suffix} name" + (" *" if required else " (optional)"),
                    key=f"poster_participant_name_{i}", max_chars=MAX_PARTICIPANT_NAME_CHARS,
                )
                pic = st.file_uploader(
                    f"Participant{label_suffix} photo" + (" *" if required else " (optional)"),
                    type=["png", "jpg", "jpeg", "webp"], key=f"poster_participant_pic_{i}",
                )
                if pic is not None:
                    st.image(pic, width=140)
                if pic is not None and name.strip():
                    participants.append((sanitize_text(name, MAX_PARTICIPANT_NAME_CHARS), pic))
                elif pic is not None or name.strip():
                    if required:
                        st.caption("Add both a name and a photo for this participant.")

    # ------------------------------------------------------------ STEP 3 --
    st.markdown("#### Step 3 · Event Information")
    event_title = ""
    event_date = event_time = timezone_choice = ""
    tagline = subtitle = competition_name = battle_title = theme = ""

    all_fields = set(category.required_fields) | set(category.optional_fields)
    if "event_title" in all_fields:
        event_title = st.text_input(
            _field_label("event_title") + (" *" if "event_title" in category.required_fields else " (optional)"),
            key="poster_event_title", max_chars=MAX_EVENT_TITLE_CHARS,
        )
    date_col, time_col, tz_col = st.columns(3)
    if "event_date" in all_fields:
        with date_col:
            d = st.date_input("Event Date" + (" *" if "event_date" in category.required_fields else ""), key="poster_event_date", value=None)
            event_date = d.strftime("%d %B %Y") if d else ""
    if "event_time" in all_fields:
        with time_col:
            t = st.time_input("Event Time" + (" *" if "event_time" in category.required_fields else ""), key="poster_event_time", value=None)
            event_time = t.strftime("%I:%M %p").lstrip("0") if t else ""
    if "timezone" in all_fields:
        with tz_col:
            timezone_choice = st.selectbox("Timezone", _TIMEZONES, index=0, key="poster_timezone")

    if "battle_title" in all_fields:
        battle_title = sanitize_text(st.text_input(_field_label("battle_title") + " (optional)", key="poster_battle_title"), MAX_EVENT_TITLE_CHARS)
    if "competition_name" in all_fields:
        competition_name = sanitize_text(st.text_input(_field_label("competition_name") + " (optional)", key="poster_competition_name"), MAX_EVENT_TITLE_CHARS)
    if "subtitle" in all_fields:
        subtitle = sanitize_text(st.text_input(_field_label("subtitle") + " (optional)", key="poster_subtitle"), MAX_TAGLINE_CHARS)
    if "tagline" in all_fields:
        tagline = sanitize_text(st.text_input(_field_label("tagline") + " (optional)", key="poster_tagline"), MAX_TAGLINE_CHARS)
    if "theme" in all_fields:
        theme = sanitize_text(st.text_input(_field_label("theme") + " (optional)", key="poster_theme"), MAX_TAGLINE_CHARS)

    # ------------------------------------------------------------ STEP 4 --
    st.markdown("#### Step 4 · Creative Style")
    style_labels = [label for _, label in STYLE_PRESETS]
    style_keys = [key for key, _ in STYLE_PRESETS]
    style_idx = style_keys.index(st.session_state["poster_style"]) if st.session_state["poster_style"] in style_keys else 0
    style_label = st.selectbox("Visual Style", style_labels, index=style_idx, key="poster_style_select")
    style_key = style_keys[style_labels.index(style_label)]

    # ------------------------------------------------------------ STEP 5 --
    st.markdown("#### Step 5 · Branding & Reference (Optional)")
    ref_col, logo_col = st.columns(2)
    reference_file = None
    logo_file = None
    with ref_col:
        st.caption("Upload a poster whose overall visual direction you like. AI will use it for composition/style inspiration while creating an original design.")
        reference_file = st.file_uploader("Reference Poster", type=["png", "jpg", "jpeg", "webp"], key="poster_reference_upload")
        if reference_file is not None:
            st.image(reference_file, width=140)
    with logo_col:
        st.caption("Transparent PNG preferred. Never stretched — placed within safe margins.")
        logo_file = st.file_uploader("Brand Logo", type=["png", "jpg", "jpeg", "webp"], key="poster_logo_upload")
        if logo_file is not None:
            st.image(logo_file, width=140)
            logo_pos_labels = [label for _, label in LOGO_POSITIONS]
            logo_pos_keys = [key for key, _ in LOGO_POSITIONS]
            pos_label = st.selectbox("Logo Placement", logo_pos_labels, index=0, key="poster_logo_position_select")
            st.session_state["poster_logo_position"] = logo_pos_keys[logo_pos_labels.index(pos_label)]

    # -------------------------------------------------------- ADVANCED ----
    with st.expander("Advanced Options"):
        size_labels = [spec["label"] for spec in POSTER_SIZES.values()]
        size_keys = list(POSTER_SIZES.keys())
        size_idx = size_keys.index(st.session_state["poster_output_size"])
        size_label = st.selectbox("Poster Size", size_labels, index=size_idx, key="poster_size_select")
        output_size_key = size_keys[size_labels.index(size_label)]

        cf_labels = [label for _, label in CREATIVE_FREEDOM_LEVELS]
        cf_keys = [key for key, _ in CREATIVE_FREEDOM_LEVELS]
        cf_idx = cf_keys.index(st.session_state["poster_creative_freedom"])
        cf_label = st.selectbox("Creative Freedom", cf_labels, index=cf_idx, key="poster_cf_select")
        creative_freedom = cf_keys[cf_labels.index(cf_label)]

        custom_instruction = st.text_area(
            "Additional Creative Direction (Optional)",
            placeholder="Example: royal black and gold theme with dramatic spotlights and minimal balloons.",
            max_chars=MAX_CUSTOM_INSTRUCTION_CHARS, key="poster_custom_instruction",
        )
        cta = sanitize_text(st.text_input("Call to Action (Optional)", key="poster_cta", max_chars=40), 40)

    st.session_state["poster_output_size"] = output_size_key
    st.session_state["poster_style"] = style_key
    st.session_state["poster_creative_freedom"] = creative_freedom

    # -------------------------------------------------------- VALIDATION --
    validation_errors = []
    if len(participants) < category.min_participants:
        validation_errors.append(f"{category.label} needs at least {category.min_participants} participant photo(s) with names.")
    for field in category.required_fields:
        value = {"event_title": event_title, "event_date": event_date, "event_time": event_time, "timezone": timezone_choice}.get(field, "")
        if not value:
            validation_errors.append(f"{_field_label(field)} is required.")

    # ------------------------------------------------------- STEP 6 -------
    st.markdown("#### Step 6 · Generate")
    if not validation_errors:
        with st.container(border=True):
            st.markdown(f"**POSTER**  \n{category.label}")
            if participants:
                st.markdown("**PARTICIPANTS**  \n" + "  vs  ".join(n for n, _ in participants))
            if event_date or event_time:
                st.markdown(f"**DATE / TIME**  \n{event_date}  {event_time} {timezone_choice if event_time else ''}".strip())
            st.markdown(f"**STYLE**  \n{style_label}")
    else:
        for err in validation_errors:
            st.warning(err)

    provider_configured = _is_provider_configured()
    demo_mode = st.checkbox(
        "Preview UI with placeholder art (free — skips AI, no cost)",
        value=not provider_configured, key="poster_demo_mode",
        help="Runs the real typography, layout, and logo compositing on a "
             "placeholder background instead of calling OpenAI — lets you "
             "see and download a realistic-looking preview for free.",
    )
    if not provider_configured and not demo_mode:
        st.caption("No OpenAI key is configured here, so a real generation will show a configuration error.")

    generate_clicked = st.button("Generate Poster", type="primary", disabled=bool(validation_errors))

    if generate_clicked:
        _run_generation(
            category, participants, event_title, event_date, event_time, timezone_choice,
            tagline, subtitle, competition_name, battle_title, theme,
            style_key, creative_freedom, custom_instruction, cta,
            reference_file, logo_file, output_size_key, business_id,
            demo_mode=demo_mode,
        )

    result = st.session_state.get("poster_result")
    if result is not None:
        st.markdown("---")
        st.markdown("#### Preview")
        is_demo_result = result.metadata.provider == "demo"
        if is_demo_result:
            st.info("This is a Demo Mode preview — placeholder background, real layout/typography/logo. No AI was called and nothing was charged.")
        st.image(result.image_bytes, width='stretch')

        regen_col, variation_col, download_col = st.columns(3)
        with regen_col:
            if st.button("Regenerate"):
                _run_generation(
                    category, participants, event_title, event_date, event_time, timezone_choice,
                    tagline, subtitle, competition_name, battle_title, theme,
                    style_key, creative_freedom, custom_instruction, cta,
                    reference_file, logo_file, output_size_key, business_id,
                    variation=False, demo_mode=demo_mode,
                )
        with variation_col:
            if st.button("Create Variation"):
                _run_generation(
                    category, participants, event_title, event_date, event_time, timezone_choice,
                    tagline, subtitle, competition_name, battle_title, theme,
                    style_key, creative_freedom, custom_instruction, cta,
                    reference_file, logo_file, output_size_key, business_id,
                    variation=True, demo_mode=demo_mode,
                )
        with download_col:
            filename = _build_filename(category, [n for n, _ in participants], event_date, demo=is_demo_result)
            st.download_button(
                "Download Demo Preview" if is_demo_result else "Download HQ Poster",
                data=result.image_bytes, file_name=filename,
                mime="image/png", type="primary",
            )

        if user_role in ("platform_admin",) or st.session_state.get("poster_debug"):
            with st.expander("Generation details"):
                m = result.metadata
                st.caption(
                    f"generation_id={m.generation_id} · prompt_version={m.prompt_version} · "
                    f"model={m.model} · duration={m.duration_seconds}s"
                )


def _build_filename(category, names, event_date, demo=False) -> str:
    safe_names = [sanitize_filename_component(n) for n in names] or ["poster"]
    date_part = sanitize_filename_component(event_date, max_len=16, fallback="")
    parts = [sanitize_filename_component(category.key)] + safe_names
    if date_part:
        parts.append(date_part)
    if demo:
        parts.append("demo")
    return "_".join(p for p in parts if p) + ".png"


def _is_provider_configured() -> bool:
    try:
        return bool(st.secrets.get("openai", {}).get("api_key"))
    except Exception:
        return False


def _run_generation(
    category, participants, event_title, event_date, event_time, timezone_choice,
    tagline, subtitle, competition_name, battle_title, theme,
    style_key, creative_freedom, custom_instruction, cta,
    reference_file, logo_file, output_size_key, business_id,
    variation=False, demo_mode=False,
):
    try:
        with st.spinner("Validating your photos…"):
            validate_participant_count(category, len(participants))
            participant_images = []
            for name, pic in participants:
                normalized = _read_uploaded_image(pic)
                participant_images.append(ParticipantImage(name=name, image_bytes=normalized))

            reference_bytes = _read_uploaded_image(reference_file) if reference_file is not None else None
            logo_bytes = _read_uploaded_image(logo_file) if logo_file is not None else None

        request = PosterRequest(
            category_key=category.key,
            participants=participant_images,
            event_title=sanitize_text(event_title, MAX_EVENT_TITLE_CHARS),
            event_date=event_date,
            event_time=event_time,
            timezone=timezone_choice,
            tagline=tagline,
            subtitle=subtitle,
            competition_name=competition_name,
            battle_title=battle_title,
            theme=theme,
            style_key=style_key,
            creative_freedom=creative_freedom,
            custom_instruction=sanitize_text(custom_instruction, MAX_CUSTOM_INSTRUCTION_CHARS),
            reference_poster_bytes=reference_bytes,
            logo_bytes=logo_bytes,
            logo_position=st.session_state.get("poster_logo_position", DEFAULT_LOGO_POSITION),
            output_size_key=output_size_key,
            cta=cta,
        )

        seed = None
        if variation:
            st.session_state["poster_variation_counter"] += 1
            seed = f"variation-{st.session_state['poster_variation_counter']}"

        status_label = "Building a placeholder preview…" if demo_mode else "Generating your poster…"
        with st.status(status_label, expanded=False) as status:
            if not demo_mode:
                status.write("Building the design brief…")
            result = generate_poster(request, business_id=business_id, regeneration_seed=seed, demo_mode=demo_mode)
            status.update(label="Preview ready." if demo_mode else "Poster ready.", state="complete")

        st.session_state["poster_result"] = result
        st.session_state["poster_last_error"] = None
        st.toast("Demo preview ready." if demo_mode else "Poster generated.", icon="🎨")
        st.rerun()

    except PosterValidationError as e:
        st.session_state["poster_last_error"] = str(e)
        st.error(str(e))
    except PosterServiceError as e:
        st.session_state["poster_last_error"] = str(e)
        st.error(str(e))
    except Exception as e:
        print(f"poster_studio: unhandled UI-layer error — {type(e).__name__}: {e}")
        st.error("Something went wrong while creating your poster. Please try again.")
