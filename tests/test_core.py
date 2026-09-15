from music_metadata.exporters import flatten_record, to_csv, to_docx, to_pdf, to_text, to_xlsx
from music_metadata.models import CatalogRecord, TechnicalMetadata, TrackMetadata
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
