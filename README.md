# AI Music Metadata Agent

**Creative technology · Applied generative AI · Human-reviewed music cataloging**

[Live Replit demo](https://music-metadata-agent--jamilhouston.replit.app) · [Presentation (PDF)](Music%20Metadata%20Agent.pdf) · [Privacy and security notes](PRIVACY.md) · [Portfolio](https://jamilhouston.com/labs)

## The problem

Music creators and catalog owners repeatedly describe tracks using genre, mood, instruments, tempo, themes, and potential sync uses. Manual tagging takes time, and descriptions can vary between collaborators and catalogs.

**Goal:** produce a consistent, editable *first draft* of metadata while keeping the human responsible for accuracy, context, and approval.

## How it works

1. **Provide audio or a link.** Upload MP3, WAV, FLAC, M4A, AAC, or OGG, or supply a supported Spotify/Apple Music link.
2. **Analyze.** Extract measurable audio properties and estimated BPM/key; an AI listening pass suggests descriptive attributes. A link-only submission is labeled accordingly and should not be mistaken for listening analysis.
3. **Review.** Inspect and edit suggestions for genre, mood, instrumentation, energy, tempo, themes, and sync use.
4. **Export.** Copy approved text or download Excel, PDF, Word, or Google Sheets-compatible CSV. Google Sheets is **not** directly connected.

The app does not infer ownership, rights identifiers, or clearance status.

## Technology and implementation

- **Interface:** Python 3.11 and Streamlit.
- **Audio analysis:** Librosa, NumPy, Mutagen, and SoundFile.
- **AI and structured output:** OpenAI Python/Agents SDKs, Pydantic; configurable audio and metadata models.
- **Integrations:** Spotify oEmbed / Apple music metadata lookup.
- **Exports:** OpenPyXL, python-docx, ReportLab, and CSV.
- **Operations:** Replit deployment, aggregate daily usage counting in local SQLite, and custom analytics events.

**My role:** I identified the cataloging problem, defined the desired workflow and safeguards, developed and iterated the prototype with Replit and AI-assisted tooling, diagnosed a structured-output schema issue, tested the user journey, and prepared the presentation and deployment. This is a working portfolio prototype, not a certified commercial service.

## Project evidence

- [Nine-slide case study](Music%20Metadata%20Agent.pdf): opportunity, product flow, architecture, privacy and security decisions, schema debugging, deployment, and next steps.
- [Automated tests](tests/): 11 tests passed in the October 2026 source audit. That result does not verify all live model calls or production behavior.
- [Privacy documentation](PRIVACY.md): data flow, third-party processing, retention limitations, analytics, and known gaps.

## Run your own development copy

Install the dependencies in a Python/Replit environment using `requirements.txt`, set `OPENAI_API_KEY` as an environment secret (never commit its value), and run the Streamlit app through the project's `.replit` configuration or `streamlit run app.py`.

Selected settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_METADATA_MODEL` | `gpt-5.6-terra` | Metadata generation model |
| `OPENAI_AUDIO_MODEL` | `gpt-audio-1.5` | Audio interpretation model |
| `DAILY_ANALYSIS_LIMIT` | `10` | Shared daily demo usage cap |
| `MAX_UPLOAD_MB` | `25` | Upload size boundary |
| `MAX_TRACK_SECONDS` | `600` | Track duration boundary |

Model availability and cost depend on your API account. For local development, run tests with `python -m pytest`. Optional category vocabulary can be loaded from a local `.xlsx` export; don't commit private catalog workbooks or recordings.

## Important limitations

- **Human approval has a known state bug:** approval does not always reset after edits or a new analysis. Users must re-review each result; this requires a code fix before broad public use.
- **Temporary audio cleanup has an edge case:** an error during preview creation can leave an intermediate file. Do not upload sensitive recordings until the failure path is fixed and retested.
- **Demo access is password-free.** The SQLite daily counter is local to an instance, not a robust global rate limiter.
- Generated tags and estimated BPM/key require human validation. A valid JSON schema does not guarantee factually correct metadata.
- Analytics instrumentation exists; its live delivery, host telemetry, and retention were not comprehensively verified. See [PRIVACY.md](PRIVACY.md).
- Historical commits contain an original imported ZIP; maintained code is in the current source tree, not the archive.

**Status:** research and portfolio demo. Use synthetic or appropriately licensed audio for demonstrations; this repository is not an authoritative catalog or rights-management system.

**License:** [MIT](LICENSE), for the source under that license.
