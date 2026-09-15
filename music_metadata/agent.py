from __future__ import annotations

import json
import os

from agents import Agent, ModelSettings, RunConfig, Runner
from openai import OpenAI

from .models import TechnicalMetadata, TrackMetadata
from .taxonomy import taxonomy_prompt


def listen_to_audio(audio_b64: str, known_context: str) -> str:
    client = OpenAI()
    model = os.getenv("OPENAI_AUDIO_MODEL", "gpt-audio-1.5")
    response = client.chat.completions.create(
        model=model,
        modalities=["text"],
        store=False,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Analyze this music preview for catalog metadata. Describe audible genre, mood, "
                        "instrumentation, arrangement, energy, performance style, themes suggested by any "
                        "lyrics, and plausible sync uses. Do not invent ownership, writers, publishers, PRO, "
                        f"IPI, ISRC, UPC, or release facts. Known context: {known_context or 'none'}"
                    ),
                },
                {"type": "input_audio", "input_audio": {"data": audio_b64, "format": "wav"}},
            ],
        }],
    )
    return response.choices[0].message.content or ""


def classify_metadata(
    observations: str,
    technical: TechnicalMetadata,
    link_metadata: dict[str, str],
    known_context: str,
    taxonomy: dict[str, list[str]],
) -> TrackMetadata:
    model = os.getenv("OPENAI_METADATA_MODEL", "gpt-5.6-terra")
    instructions = f"""
You are a music catalog metadata specialist. Map evidence into the supplied controlled vocabulary.
Prefer exact vocabulary terms. Use a small number of discriminating tags rather than every plausible tag.
Never invent rights, ownership, identifiers, release facts, or restrictions. Mark uncertainty clearly.
Confidence values must be between 0 and 1 and should cover genre_primary, moods, instruments, and sync_usage.

CONTROLLED VOCABULARY
{taxonomy_prompt(taxonomy)}
"""
    agent = Agent(
        name="Music metadata classifier",
        instructions=instructions,
        model=model,
        output_type=TrackMetadata,
        model_settings=ModelSettings(store=False),
    )
    payload = {
        "audio_observations": observations,
        "technical_analysis": technical.model_dump(),
        "streaming_link_metadata": link_metadata,
        "user_context": known_context,
    }
    result = Runner.run_sync(
        agent,
        json.dumps(payload, ensure_ascii=False),
        run_config=RunConfig(tracing_disabled=True, trace_include_sensitive_data=False),
    )
    return result.final_output
