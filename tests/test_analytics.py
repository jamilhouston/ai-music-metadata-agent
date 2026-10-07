from music_metadata import analytics


def test_event_uses_existing_tracker_without_injecting_one(monkeypatch):
    rendered = []
    monkeypatch.setattr(analytics.components, "html", lambda content, **kwargs: rendered.append(content))

    analytics.track_event("export_downloaded", {"format": "pdf"})

    assert len(rendered) == 1
    assert "window.parent?.umami?.track" in rendered[0]
    assert '"export_downloaded"' in rendered[0]
    assert '"format":"pdf"' in rendered[0]
    assert "<script src=" not in rendered[0]


def test_invalid_event_names_are_ignored(monkeypatch):
    rendered = []
    monkeypatch.setattr(analytics.components, "html", lambda content, **kwargs: rendered.append(content))
    analytics.track_event("invalid event")
    assert rendered == []


def test_render_failure_does_not_break_application(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("Tracker unavailable")

    monkeypatch.setattr(analytics.components, "html", fail)
    analytics.track_event("metadata_approved", {"link_only": True})


def test_payload_cannot_close_script():
    assert "<" not in analytics._script_json({"format": "</script>"})
