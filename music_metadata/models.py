from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TechnicalMetadata(BaseModel):
    filename: str = ""
    format: str = ""
    duration_seconds: float | None = None
    sample_rate_hz: int | None = None
    channels: int | None = None
    bitrate_kbps: int | None = None
    bpm: float | None = None
    musical_key: str = ""
    scale: str = ""


class RightsMetadata(BaseModel):
    artist_name: str = ""
    writers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    pro: str = ""
    ipi_numbers: list[str] = Field(default_factory=list)
    isrc: str = ""
    upc_ean: str = ""
    sync_restrictions: str = ""


class TrackMetadata(BaseModel):
    track_title: str = ""
    version_status: str = ""
    release_status: str = ""
    genre_primary: str = ""
    genre_secondary: list[str] = Field(default_factory=list, max_length=6)
    mood_tags: list[str] = Field(default_factory=list, max_length=8)
    themes_narrative: list[str] = Field(default_factory=list, max_length=6)
    sync_usage: list[str] = Field(default_factory=list, max_length=8)
    instrumentation: list[str] = Field(default_factory=list, max_length=12)
    musical_attributes: list[str] = Field(default_factory=list, max_length=8)
    performance_style: list[str] = Field(default_factory=list, max_length=6)
    description: str = ""
    reference_artists: list[str] = Field(default_factory=list, max_length=5)
    reference_tracks: list[str] = Field(default_factory=list, max_length=5)
    explicit_content: Literal["Yes", "No", "Unknown"] = "Unknown"
    clean_version_available: Literal["Yes", "No", "Unknown"] = "Unknown"
    instrumental_available: Literal["Yes", "No", "Unknown"] = "Unknown"
    confidence: dict[str, float] = Field(default_factory=dict)
    uncertainty_notes: list[str] = Field(default_factory=list)
    metadata_source: list[str] = Field(default_factory=list)
    taxonomy_version: str = "paradrift-v1"


class CatalogRecord(BaseModel):
    metadata: TrackMetadata
    technical: TechnicalMetadata
    rights: RightsMetadata = Field(default_factory=RightsMetadata)
    source_url: str = ""
    review_status: Literal["Draft", "Approved", "Needs review"] = "Draft"
    reviewed_by: str = ""
    reviewed_at: date | None = None
    notes: str = ""

