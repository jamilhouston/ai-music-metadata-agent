from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from mutagen import File as MutagenFile

from .models import TechnicalMetadata


KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _estimate_key(chroma: np.ndarray) -> tuple[str, str]:
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    energy = chroma.mean(axis=1)
    candidates: list[tuple[float, str, str]] = []
    for index, name in enumerate(KEY_NAMES):
        candidates.append((float(np.corrcoef(energy, np.roll(major_profile, index))[0, 1]), name, "Major"))
        candidates.append((float(np.corrcoef(energy, np.roll(minor_profile, index))[0, 1]), name, "Minor"))
    _, key, scale = max(candidates, key=lambda item: item[0])
    return key, scale


def analyze_audio(path: str, filename: str) -> TechnicalMetadata:
    technical = TechnicalMetadata(filename=filename, format=Path(filename).suffix.lstrip(".").upper())
    try:
        tags = MutagenFile(path)
        if tags and getattr(tags, "info", None):
            info = tags.info
            technical.duration_seconds = round(float(getattr(info, "length", 0) or 0), 2) or None
            technical.sample_rate_hz = int(getattr(info, "sample_rate", 0) or 0) or None
            technical.channels = int(getattr(info, "channels", 0) or 0) or None
            bitrate = int(getattr(info, "bitrate", 0) or 0)
            technical.bitrate_kbps = round(bitrate / 1000) if bitrate else None
    except Exception:
        pass

    try:
        file_info = sf.info(path)
        technical.duration_seconds = technical.duration_seconds or round(float(file_info.duration), 2)
        technical.sample_rate_hz = technical.sample_rate_hz or int(file_info.samplerate)
        technical.channels = technical.channels or int(file_info.channels)
    except Exception:
        pass

    try:
        samples, sample_rate = librosa.load(path, sr=22050, mono=True, duration=180)
        if samples.size:
            tempo, _ = librosa.beat.beat_track(y=samples, sr=sample_rate)
            estimated_bpm = round(float(np.asarray(tempo).reshape(-1)[0]), 1)
            technical.bpm = estimated_bpm if estimated_bpm > 0 else None
            chroma = librosa.feature.chroma_cqt(y=samples, sr=sample_rate)
            technical.musical_key, technical.scale = _estimate_key(chroma)
            technical.sample_rate_hz = technical.sample_rate_hz or sample_rate
    except Exception:
        pass
    return technical


def make_audio_preview(path: str, seconds: int = 75) -> tuple[str, str]:
    """Create a mono WAV preview for the audio-understanding call."""
    samples, sample_rate = librosa.load(path, sr=16000, mono=True, duration=seconds)
    handle, preview_path = tempfile.mkstemp(suffix=".wav")
    os.close(handle)
    sf.write(preview_path, samples, sample_rate, subtype="PCM_16")
    return preview_path, base64.b64encode(Path(preview_path).read_bytes()).decode("ascii")
