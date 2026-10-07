from __future__ import annotations

import os
import hmac
import html
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from music_metadata.agent import classify_metadata, listen_to_audio
from music_metadata.analytics import track_event
from music_metadata.audio import analyze_audio, make_audio_preview
from music_metadata.exporters import to_csv, to_docx, to_pdf, to_text, to_xlsx
from music_metadata.links import resolve_music_link
from music_metadata.models import CatalogRecord, RightsMetadata, TechnicalMetadata
from music_metadata.presentation import analysis_source_label, confidence_text, suggestion_groups
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
st.info(
    "AI Auto-Tagger will suggest categories after analysis. You do not need to choose categories before you start; "
    "review and correct the suggestions afterward."
)

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
    "Analyze & Auto-Tag",
    type="primary",
    disabled=not (audio_file or streaming_url) or (audio_file is not None and not upload_permission),
):
    input_mode = "audio_and_link" if audio_file and streaming_url else "audio" if audio_file else "link_only"
    track_event("analysis_started", {"input_mode": input_mode})
    if not os.getenv("OPENAI_API_KEY"):
        track_event("analysis_failed", {"input_mode": input_mode, "failure_stage": "configuration"})
        st.error("Add OPENAI_API_KEY to Replit Secrets or your local environment.")
    elif audio_file and audio_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        track_event("analysis_failed", {"input_mode": input_mode, "failure_stage": "upload_limit"})
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
                # These fields are user/verified-source facts, never AI inferences.
                metadata.version_status = version_status
                metadata.release_status = release_status
                metadata.metadata_source = (["Uploaded audio"] if audio_file else []) + ([link_metadata.get("provider", "Streaming link")] if link_metadata else [])
                record = CatalogRecord(
                    metadata=metadata,
                    technical=technical,
                    rights=RightsMetadata(artist_name=artist_name or link_metadata.get("creator", "")),
                    source_url=streaming_url,
                    review_status="Needs review" if metadata.uncertainty_notes else "Draft",
                )
                st.session_state.record = record
                track_event(
                    "analysis_completed",
                    {
                        "input_mode": input_mode,
                        "link_only": not bool(audio_file),
                        "has_uncertainty": bool(metadata.uncertainty_notes),
                    },
                )
                status.update(label="Draft metadata ready for review", state="complete")
        except Exception as exc:
            track_event("analysis_failed", {"input_mode": input_mode, "failure_stage": "analysis"})
            st.error(f"Analysis failed: {exc}")
        finally:
            if audio_path:
                Path(audio_path).unlink(missing_ok=True)
            if preview_path:
                Path(preview_path).unlink(missing_ok=True)

record = st.session_state.record
if record:
    st.divider()
    metadata = record.metadata
    st.subheader("AI-Suggested Tags")
    source_label = analysis_source_label(record)
    if "Link-based" in source_label:
        st.warning(source_label)
    else:
        st.success(source_label)
    st.caption(
        "These are AI suggestions from the selected taxonomy. Read the confidence levels and uncertainty notes "
        "before approving anything for export."
    )

    for group in suggestion_groups(metadata):
        field = group["field"]
        values = group["values"]
        with st.container(border=True):
            st.markdown(f"**{group['label']}**")
            if field == "description":
                st.write(values[0] if values and values[0] else "No suggestion")
            elif values:
                chips = " ".join(
                    f'<span style="display:inline-block;padding:.25rem .6rem;margin:.15rem .2rem .15rem 0;'
                    f'border:1px solid #d7dbe2;border-radius:999px;background:#f5f7fa;">'
                    f"{html.escape(str(value))}</span>"
                    for value in values
                )
                st.markdown(chips, unsafe_allow_html=True)
            else:
                st.caption("No suggestion")
            st.caption(confidence_text(metadata, group["confidence_key"]))

    if metadata.uncertainty_notes:
        st.warning("Uncertainty notes")
        for note in metadata.uncertainty_notes:
            st.markdown(f"- {note}")
    else:
        st.success("No uncertainty notes were returned.")

    def options_with_current(values: list[str], current: list[str] | str) -> list[str]:
        selected = [current] if isinstance(current, str) and current else list(current)
        return list(dict.fromkeys([value for value in selected if value] + list(values)))

    with st.expander("Edit suggestions"):
        st.caption("Optional: correct any AI suggestion before requesting approval.")
        metadata.track_title = st.text_input("Title", metadata.track_title, key="review_title")
        genre_options = options_with_current(taxonomy.get("genre_families", []), metadata.genre_primary)
        metadata.genre_primary = st.selectbox(
            "Primary genre",
            options=[""] + genre_options,
            index=([""] + genre_options).index(metadata.genre_primary) if metadata.genre_primary in genre_options else 0,
            key="edit_genre_primary",
        )
        metadata.genre_secondary = st.multiselect(
            "Secondary genres",
            options_with_current(taxonomy.get("subgenres", []), metadata.genre_secondary),
            default=metadata.genre_secondary,
            key="edit_genre_secondary",
        )
        metadata.mood_tags = st.multiselect(
            "Mood",
            options_with_current(taxonomy.get("moods", []), metadata.mood_tags),
            default=metadata.mood_tags,
            key="edit_mood_tags",
        )
        metadata.sync_usage = st.multiselect(
            "Suggested sync uses",
            options_with_current(taxonomy.get("sync_uses", []), metadata.sync_usage),
            default=metadata.sync_usage,
            key="edit_sync_usage",
        )
        metadata.instrumentation = [
            value.strip()
            for value in st.text_input(
                "Instrumentation (comma-separated)",
                ", ".join(metadata.instrumentation),
                key="edit_instrumentation",
            ).split(",")
            if value.strip()
        ]
        metadata.musical_attributes = [
            value.strip()
            for value in st.text_input(
                "Musical attributes & energy (comma-separated)",
                ", ".join(metadata.musical_attributes),
                key="edit_musical_attributes",
            ).split(",")
            if value.strip()
        ]
        metadata.performance_style = [
            value.strip()
            for value in st.text_input(
                "Performance style (comma-separated)",
                ", ".join(metadata.performance_style),
                key="edit_performance_style",
            ).split(",")
            if value.strip()
        ]
        metadata.themes_narrative = [
            value.strip()
            for value in st.text_input(
                "Themes or narrative (comma-separated)",
                ", ".join(metadata.themes_narrative),
                key="edit_themes_narrative",
            ).split(",")
            if value.strip()
        ]
        metadata.description = st.text_area("Description", metadata.description, key="edit_description")
        metadata.explicit_content = st.selectbox(
            "Explicit-content assessment",
            ["Unknown", "Yes", "No"],
            index=["Unknown", "Yes", "No"].index(metadata.explicit_content),
            key="edit_explicit_content",
        )
        metadata.clean_version_available = st.selectbox(
            "Clean-version assessment",
            ["Unknown", "Yes", "No"],
            index=["Unknown", "Yes", "No"].index(metadata.clean_version_available),
            key="edit_clean_version",
        )
        metadata.instrumental_available = st.selectbox(
            "Instrumental-version assessment",
            ["Unknown", "Yes", "No"],
            index=["Unknown", "Yes", "No"].index(metadata.instrumental_available),
            key="edit_instrumental_version",
        )
        st.info(
            "Ownership and rights fields are not inferred. Artist, writers, publishers, PRO, IPI, ISRC, UPC, "
            "licensing rights, and release status must come from you or a verified source."
        )
        st.json({"technical": record.technical.model_dump(), "confidence": metadata.confidence})

    was_approved = record.review_status == "Approved"
    approve = st.checkbox(
        "I reviewed these fields and approve this metadata",
        value=record.review_status == "Approved",
        key="approve_metadata",
    )
    if approve:
        record.review_status = "Approved"
        record.reviewed_at = date.today()
        if not was_approved:
            track_event(
                "metadata_approved",
                {
                    "link_only": not bool(record.technical.filename),
                    "has_uncertainty": bool(metadata.uncertainty_notes),
                },
            )
        st.success("Approved for export. Nothing was saved on the app server.")
    else:
        if record.review_status == "Approved":
            record.review_status = "Needs review"
            record.reviewed_at = None
        st.warning("Review and approve the suggested tags before exporting.")

    st.subheader("Export")
    if record.review_status == "Approved":
        text_export = to_text(record)
        st.code(text_export, language=None)
        st.caption("Use the copy button in the text box, or download a formatted file.")
        col1, col2, col3, col4 = st.columns(4)
        if col1.download_button("Download Excel", to_xlsx(record), file_name="music-metadata.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
            track_event("export_downloaded", {"format": "xlsx"})
        if col2.download_button("For Google Sheets", to_csv(record), file_name="music-metadata-google-sheets.csv", mime="text/csv"):
            track_event("export_downloaded", {"format": "csv"})
        if col3.download_button("Download PDF", to_pdf(record), file_name="music-metadata.pdf", mime="application/pdf"):
            track_event("export_downloaded", {"format": "pdf"})
        if col4.download_button("Download document", to_docx(record), file_name="music-metadata.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
            track_event("export_downloaded", {"format": "docx"})
        st.caption("To use Google Sheets, download the Google Sheets CSV and import it into a sheet you control.")
    else:
        st.info("Exports unlock after human review and approval.")
