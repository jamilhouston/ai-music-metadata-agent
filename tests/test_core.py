from pathlib import Path

from streamlit.testing.v1 import AppTest

from music_metadata.exporters import flatten_record, to_csv, to_docx, to_pdf, to_text, to_xlsx
from music_metadata.models import CatalogRecord, TechnicalMetadata, TrackMetadata
from music_metadata.presentation import analysis_source_label, confidence_text, suggestion_groups
from music_metadata.storage import reserve_daily_analysis
from music_metadata.taxonomy import clean_term, unique_terms


def sample_record() -> CatalogRecord:
    return CatalogRecord(
        metadata=TrackMetadata(
            track_title="Example",
            genre_primary="R&B",
            mood_tags=["Warm", "Relaxed"],
            confidence={"genre_primary": 0.91},
        ),
        technical=TechnicalMetadata(filename="example.wav", duration_seconds=123.4, bpm=98),
    )


def test_taxonomy_normalization():
    assert clean_term("  Folk\u00a0 Rock  ") == "Folk Rock"
    assert unique_terms(["Rock", " rock ", "Pop"]) == ["Rock", "Pop"]


def test_exports_are_created():
    record = sample_record()
    assert flatten_record(record)["track_title"] == "Example"
    assert "Genre Primary: R&B" in to_text(record)
    assert to_xlsx(record).startswith(b"PK")
    assert to_csv(record).startswith(b"\xef\xbb\xbf")
    assert to_docx(record).startswith(b"PK")
    assert to_pdf(record).startswith(b"%PDF")


def test_daily_analysis_limit(tmp_path):
    database = tmp_path / "usage.db"
    assert reserve_daily_analysis(2, str(database)) == (True, 1)
    assert reserve_daily_analysis(2, str(database)) == (True, 2)
    assert reserve_daily_analysis(2, str(database)) == (False, 2)


def test_ai_auto_tag_display_groups_and_confidence():
    metadata = TrackMetadata(
        genre_primary="Electronic",
        genre_secondary=["House"],
        mood_tags=["Energetic"],
        instrumentation=["Synth"],
        musical_attributes=["Driving"],
        performance_style=["Polished"],
        themes_narrative=["Nightlife"],
        sync_usage=["Advertising"],
        description="A bright, driving electronic track.",
        explicit_content="No",
        clean_version_available="Yes",
        instrumental_available="Unknown",
        confidence={"genre_primary": 0.9, "moods": 0.75},
    )

    groups = {group["label"]: group for group in suggestion_groups(metadata)}

    assert groups["Primary genre"]["values"] == ["Electronic"]
    assert groups["Musical attributes & energy"]["values"] == ["Driving"]
    assert groups["Explicit-content assessment"]["values"] == ["No"]
    assert confidence_text(metadata, "genre_primary") == "Confidence: 90%"
    assert confidence_text(metadata, "mood_tags") == "Confidence: 75%"


def test_link_only_results_are_explicitly_labeled():
    record = CatalogRecord(
        metadata=TrackMetadata(),
        technical=TechnicalMetadata(),
        source_url="https://open.spotify.com/track/example",
    )

    assert analysis_source_label(record) == "Link-based metadata estimate — audio was not analyzed."


def test_exports_unlock_after_human_approval(monkeypatch):
    monkeypatch.delenv("APP_ACCESS_CODE", raising=False)
    monkeypatch.delenv("REPLIT_DEPLOYMENT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    record = CatalogRecord(
        metadata=TrackMetadata(track_title="Fixture"),
        technical=TechnicalMetadata(),
        review_status="Draft",
    )
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py")
    app.session_state.record = record

    app.run(timeout=30)

    assert app.checkbox(key="approve_metadata").value is False
    assert len(app.download_button) == 0
    assert any("Exports unlock after human review and approval." in info.value for info in app.info)

    app.checkbox(key="approve_metadata").set_value(True).run(timeout=30)

    assert app.session_state.record.review_status == "Approved"
    assert app.checkbox(key="approve_metadata").value is True
    assert [button.label for button in app.download_button] == [
        "Download Excel",
        "For Google Sheets",
        "Download PDF",
        "Download document",
    ]
