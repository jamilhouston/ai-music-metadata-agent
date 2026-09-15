from __future__ import annotations

import os
import hmac
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from music_metadata.agent import classify_metadata, listen_to_audio
from music_metadata.audio import analyze_audio, make_audio_preview
from music_metadata.exporters import to_csv, to_docx, to_pdf, to_text, to_xlsx
from music_metadata.links import resolve_music_link
from music_metadata.models import CatalogRecord, RightsMetadata, TechnicalMetadata
from music_metadata.storage import reserve_daily_analysis
from music_metadata.taxonomy import BASE_TAXONOMY, taxonomy_from_workbook


st.set_page_config(page_title="Music Metadata Agent", page_icon="🎵", layout="wide")
st.title("Music Metadata Agent")
st.caption("Upload a track, review suggested tags, and export approved metadata.")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
MAX_TRACK_SECONDS = int(os.getenv("MAX_TRACK_SECONDS", "600"))
DAILY_ANALYSIS_LIMIT = int(os.getenv("DAILY_ANALYSIS_LIMIT", "10"))


def require_access() -> bool:
    """Require a shared tester code in production; allow a restricted local preview."""
    expected = os.getenv("APP_ACCESS_CODE", "")
    if not expected:
        if os.getenv("REPLIT_DEPLOYMENT"):
            st.error("This deployment is waiting for its APP_ACCESS_CODE secret.")
            st.stop()
        st.warning("Developer preview: no access code is configured.")
        return False
    if st.session_state.get("authenticated"):
        return True
    st.subheader("Private preview")
    st.write("Enter the tester access code to use this prototype.")
    with st.form("access_form"):
        entered = st.text_input("Access code", type="password")
        submitted = st.form_submit_button("Continue")
    if submitted:
        if hmac.compare_digest(entered, expected):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("That access code is not correct.")
    st.stop()
    return False


authenticated = require_access()

if "record" not in st.session_state:
    st.session_state.record = None

with st.sidebar:
    st.header("Taxonomy")
    taxonomy_file = st.file_uploader("Optional category workbook", type=["xlsx"], help="Upload an exported copy of your category spreadsheet to use its full vocabulary.")
    if taxonomy_file:
        try:
            taxonomy = taxonomy_from_workbook(taxonomy_file.getvalue())
            st.success("Category workbook loaded")
        except Exception as exc:
            taxonomy = BASE_TAXONOMY
            st.error(f"Could not read the taxonomy workbook: {exc}")
    else:
        taxonomy = BASE_TAXONOMY
    st.caption(f"Metadata model: {os.getenv('OPENAI_METADATA_MODEL', 'gpt-5.6-terra')}")
    st.caption(f"Audio model: {os.getenv('OPENAI_AUDIO_MODEL', 'gpt-audio-1.5')}")
    st.caption(f"Daily demo limit: {DAILY_ANALYSIS_LIMIT} analyses")

audio_file = st.file_uploader(
    f"Audio file (maximum {MAX_UPLOAD_MB} MB and {MAX_TRACK_SECONDS // 60} minutes)",
    type=["mp3", "wav", "flac", "m4a", "aac", "ogg"],
)
streaming_url = st.text_input("Spotify or Apple Music track link (optional)")
known_context = st.text_area("Known context", placeholder="Track title, artist, intended use, lyric summary, or anything the agent should know")

with st.expander("Privacy and upload permission", expanded=True):
    st.write(
        "This demo does not create consumer accounts, request contact details, or permanently save uploaded "
        "audio or generated metadata. The original audio is analyzed temporarily on the app server; only a "
        "short mono preview, the context you enter, and relevant link metadata are sent to OpenAI. Temporary "
        "audio files are deleted after analysis. OpenAI API data is not used for model training unless the "
        "account owner opts in, but standard API abuse-monitoring logs may be retained for up to 30 days. "
        "Downloaded exports are saved only where you choose. Do not enter personal information or upload "
        "confidential music or music you do not own or have permission to process."
    )
upload_permission = st.checkbox(
    "I own this audio or have permission to upload and analyze it.",
    disabled=audio_file is None,
)

left, right = st.columns(2)
with left:
    title_override = st.text_input("Track title (optional)")
    artist_name = st.text_input("Artist name (optional)")
with right:
    version_status = st.text_input("Version status", placeholder="Master, instrumental, clean, alt mix…")
    release_status = st.text_input("Release status", placeholder="Unreleased, released, pending…")

if st.button(
    "Analyze metadata",
    type="primary",
    disabled=not (audio_file or streaming_url) or (audio_file is not None and not upload_permission),
):
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Add OPENAI_API_KEY to Replit Secrets or your local environment.")
    elif audio_file and audio_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.error(f"That file is larger than the {MAX_UPLOAD_MB} MB limit.")
    else:
        audio_path = ""
        preview_path = ""
        try:
            with st.status("Analyzing track…", expanded=True) as status:
                link_metadata = resolve_music_link(streaming_url) if streaming_url else {}
                if link_metadata:
                    st.write(f"Loaded {link_metadata.get('provider')} reference metadata")
                if audio_file:
                    suffix = Path(audio_file.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                        handle.write(audio_file.getvalue())
                        audio_path = handle.name
                    technical = analyze_audio(audio_path, audio_file.name)
                    if technical.duration_seconds and technical.duration_seconds > MAX_TRACK_SECONDS:
                        raise ValueError(
                            f"This track is longer than the {MAX_TRACK_SECONDS // 60}-minute demo limit."
                        )
                    st.write("Technical audio analysis complete")
                    allowed, used = reserve_daily_analysis(DAILY_ANALYSIS_LIMIT)
                    if not allowed:
                        raise RuntimeError("Today's demo analysis limit has been reached. Please try again tomorrow.")
                    st.write(f"Daily demo use: {used} of {DAILY_ANALYSIS_LIMIT}")
                    preview_path, audio_b64 = make_audio_preview(audio_path)
                    observations = listen_to_audio(audio_b64, known_context)
                    st.write("Audio listening pass complete")
                else:
                    technical = TechnicalMetadata()
                    allowed, used = reserve_daily_analysis(DAILY_ANALYSIS_LIMIT)
                    if not allowed:
                        raise RuntimeError("Today's demo analysis limit has been reached. Please try again tomorrow.")
                    st.write(f"Daily demo use: {used} of {DAILY_ANALYSIS_LIMIT}")
                    observations = (
                        "No audio was uploaded. Use only the streaming-link metadata, the user's context, "
                        "and verified public web information. Mark subjective tags as uncertain when evidence is weak."
                    )
                    st.write("Link-only research pass ready")
                metadata = classify_metadata(observations, technical, link_metadata, known_context, taxonomy)
                uploaded_stem = Path(audio_file.name).stem if audio_file else ""
                metadata.track_title = title_override or metadata.track_title or link_metadata.get("title", "") or uploaded_stem
                metadata.version_status = version_status or metadata.version_status
                metadata.release_status = release_status or metadata.release_status
                metadata.metadata_source = (["Uploaded audio"] if audio_file else []) + ([link_metadata.get("provider", "Streaming link")] if link_metadata else [])
                record = CatalogRecord(
                    metadata=metadata,
                    technical=technical,
                    rights=RightsMetadata(artist_name=artist_name or link_metadata.get("creator", "")),
                    source_url=streaming_url,
                    review_status="Needs review" if metadata.uncertainty_notes else "Draft",
                )
                st.session_state.record = record
                status.update(label="Draft metadata ready for review", state="complete")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
        finally:
            if audio_path:
                Path(audio_path).unlink(missing_ok=True)
            if preview_path:
                Path(preview_path).unlink(missing_ok=True)

record = st.session_state.record
if record:
    st.divider()
    st.subheader("Review metadata")
    metadata = record.metadata
    metadata.track_title = st.text_input("Title", metadata.track_title, key="review_title")
    metadata.genre_primary = st.selectbox(
        "Primary genre",
        options=[""] + taxonomy.get("genre_families", []),
        index=([""] + taxonomy.get("genre_families", [])).index(metadata.genre_primary) if metadata.genre_primary in taxonomy.get("genre_families", []) else 0,
    )
    metadata.genre_secondary = st.multiselect("Secondary genres", taxonomy.get("subgenres", []), default=[v for v in metadata.genre_secondary if v in taxonomy.get("subgenres", [])])
    metadata.mood_tags = st.multiselect("Mood tags", taxonomy.get("moods", []), default=[v for v in metadata.mood_tags if v in taxonomy.get("moods", [])])
    metadata.sync_usage = st.multiselect("Sync uses", taxonomy.get("sync_uses", []), default=[v for v in metadata.sync_usage if v in taxonomy.get("sync_uses", [])])
    metadata.instrumentation = st.text_input("Instrumentation (comma-separated)", ", ".join(metadata.instrumentation)).split(",")
    metadata.instrumentation = [value.strip() for value in metadata.instrumentation if value.strip()]
    metadata.themes_narrative = [value.strip() for value in st.text_input("Themes (comma-separated)", ", ".join(metadata.themes_narrative)).split(",") if value.strip()]
    metadata.description = st.text_area("Description", metadata.description)
    st.json({"technical": record.technical.model_dump(), "confidence": metadata.confidence, "uncertainty_notes": metadata.uncertainty_notes})

    approve = st.checkbox("I reviewed these fields and approve this metadata")
    if approve:
        record.review_status = "Approved"
        record.reviewed_at = date.today()
        st.success("Approved for export. Nothing was saved on the app server.")

    st.subheader("Export")
    text_export = to_text(record)
    st.code(text_export, language=None)
    st.caption("Use the copy button in the text box, or download a formatted file.")
    col1, col2, col3, col4 = st.columns(4)
    col1.download_button("Download Excel", to_xlsx(record), file_name="music-metadata.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    col2.download_button("For Google Sheets", to_csv(record), file_name="music-metadata-google-sheets.csv", mime="text/csv")
    col3.download_button("Download PDF", to_pdf(record), file_name="music-metadata.pdf", mime="application/pdf")
    col4.download_button("Download document", to_docx(record), file_name="music-metadata.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.caption("To use Google Sheets, download the Google Sheets CSV and import it into a sheet you control.")
