"""Shared dataclasses passed between poster/ pipeline stages."""
from dataclasses import dataclass, field


@dataclass
class ParticipantImage:
    """A validated, already-decoded participant photo."""
    name: str
    image_bytes: bytes  # re-encoded PNG bytes, never the raw upload as-is


@dataclass
class PosterRequest:
    category_key: str
    participants: list  # list[ParticipantImage], ordered
    event_title: str = ""
    event_date: str = ""      # already-formatted display string (exact, deterministic)
    event_time: str = ""      # already-formatted display string
    timezone: str = ""
    tagline: str = ""
    subtitle: str = ""
    competition_name: str = ""
    battle_title: str = ""
    theme: str = ""
    style_key: str = "auto"
    creative_freedom: str = "balanced"
    custom_instruction: str = ""
    reference_poster_bytes: bytes | None = None
    logo_bytes: bytes | None = None
    logo_position: str = "auto"
    output_size_key: str = "square"
    cta: str = ""


@dataclass
class GenerationMetadata:
    generation_id: str
    category: str
    style: str
    creative_freedom: str
    participant_names: list
    event_date: str
    event_time: str
    timezone: str
    output_size: str
    provider: str
    model: str
    prompt_version: str
    created_at: str
    duration_seconds: float = 0.0
    success: bool = False
    error_type: str | None = None


@dataclass
class GenerationResult:
    image_bytes: bytes
    metadata: GenerationMetadata
