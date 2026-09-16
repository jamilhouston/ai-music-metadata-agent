from __future__ import annotations

from typing import Any

from .models import CatalogRecord, TrackMetadata


SUGGESTION_GROUPS: tuple[tuple[str, str, str], ...] = (
    ("Primary genre", "genre_primary", "genre_primary"),
    ("Secondary genres", "genre_secondary", "genre_secondary"),
    ("Mood", "mood_tags", "moods"),
    ("Instrumentation", "instrumentation", "instruments"),
    ("Musical attributes & energy", "musical_attributes", "musical_attributes"),
    ("Performance style", "performance_style", "performance_style"),
    ("Themes or narrative", "themes_narrative", "themes_narrative"),
    ("Suggested sync uses", "sync_usage", "sync_usage"),
    ("Description", "description", "description"),
    ("Explicit-content assessment", "explicit_content", "explicit_content"),
    ("Clean-version assessment", "clean_version_available", "clean_version_available"),
    ("Instrumental-version assessment", "instrumental_available", "instrumental_available"),
)

_CONFIDENCE_ALIASES: dict[str, tuple[str, ...]] = {
    "genre_primary": ("genre_primary", "genre"),
    "genre_secondary": ("genre_secondary", "genre"),
    "mood_tags": ("mood_tags", "moods", "mood"),
    "moods": ("moods", "mood_tags", "mood"),
    "instrumentation": ("instrumentation", "instruments", "instrument"),
    "instruments": ("instruments", "instrumentation", "instrument"),
    "musical_attributes": ("musical_attributes", "attributes", "energy"),
    "performance_style": ("performance_style", "performance"),
    "themes_narrative": ("themes_narrative", "themes", "narrative"),
    "sync_usage": ("sync_usage", "sync_uses"),
    "description": ("description",),
    "explicit_content": ("explicit_content", "explicit"),
    "clean_version_available": ("clean_version_available", "clean_version"),
    "instrumental_available": ("instrumental_available", "instrumental_version"),
}


def suggestion_groups(metadata: TrackMetadata) -> list[dict[str, Any]]:
    """Return the AI fields in the order and labels used by the review UI."""
    groups: list[dict[str, Any]] = []
    for label, field, confidence_key in SUGGESTION_GROUPS:
        value = getattr(metadata, field)
        values = [value] if isinstance(value, str) else list(value)
        groups.append(
            {
                "label": label,
                "field": field,
                "values": values,
                "confidence_key": confidence_key,
            }
        )
    return groups


def confidence_value(metadata: TrackMetadata, field: str) -> float | None:
    """Find a model confidence score while tolerating the prompt's field aliases."""
    for key in _CONFIDENCE_ALIASES.get(field, (field,)):
        if key in metadata.confidence:
            return metadata.confidence[key]
    return None


def confidence_text(metadata: TrackMetadata, field: str) -> str:
    score = confidence_value(metadata, field)
    if score is None:
        return "Confidence: not scored"
    return f"Confidence: {round(score * 100)}%"


def analysis_source_label(record: CatalogRecord) -> str:
    if record.source_url and not record.technical.filename:
        return "Link-based metadata estimate — audio was not analyzed."
    return "Audio preview analyzed — tags include the AI listening pass."