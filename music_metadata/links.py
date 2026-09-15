from __future__ import annotations

import re
from urllib.parse import urlparse

import requests


def resolve_music_link(url: str) -> dict[str, str]:
    if not url:
        return {}
    host = urlparse(url).netloc.casefold()
    if "spotify.com" in host:
        response = requests.get("https://open.spotify.com/oembed", params={"url": url}, timeout=12)
        response.raise_for_status()
        data = response.json()
        return {
            "provider": "Spotify",
            "title": data.get("title", ""),
            "creator": data.get("author_name", ""),
            "source_url": url,
        }
    if "music.apple.com" in host:
        match = re.search(r"[?&]i=(\d+)", url) or re.search(r"/(\d+)(?:\?|$)", url)
        if not match:
            return {"provider": "Apple Music", "source_url": url}
        response = requests.get("https://itunes.apple.com/lookup", params={"id": match.group(1)}, timeout=12)
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return {"provider": "Apple Music", "source_url": url}
        data = results[-1]
        return {
            "provider": "Apple Music",
            "title": data.get("trackName", ""),
            "creator": data.get("artistName", ""),
            "album": data.get("collectionName", ""),
            "genre": data.get("primaryGenreName", ""),
            "release_date": data.get("releaseDate", ""),
            "source_url": url,
        }
    raise ValueError("Enter a Spotify or Apple Music track link.")

