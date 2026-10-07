# Music Metadata Agent

A Replit-ready Streamlit prototype for logging music metadata from uploaded audio. It combines deterministic audio analysis with an AI listening pass and controlled-vocabulary classification.

## What it does

- Accepts MP3, WAV, FLAC, M4A, AAC, and OGG uploads.
- Extracts technical properties and estimates BPM, key, and scale.
- Uses GPT-Audio-1.5 to describe the track.
- Uses GPT-5.6 Terra to return validated catalog metadata.
- Accepts a Spotify or Apple Music track link as enrichment or as a link-only alternative input.
- Requires human review before export.
- Exports text, Excel, PDF, Word, and a CSV formatted for Google Sheets.
- Accepts an exported copy of the category workbook to load its complete vocabulary.

## Replit setup

1. Import this folder into a Replit Python App.
2. Add `OPENAI_API_KEY` in Replit Secrets.
3. Run the app. Replit uses the command in `.replit`. The demo is open without a password.

Optional settings:

- `OPENAI_METADATA_MODEL` defaults to `gpt-5.6-terra`.
- `OPENAI_AUDIO_MODEL` defaults to `gpt-audio-1.5`.
- `DAILY_ANALYSIS_LIMIT` defaults to `10` analyses per day across the demo instance.
- `MAX_UPLOAD_MB` defaults to `25` MB.
- `MAX_TRACK_SECONDS` defaults to `600` seconds (10 minutes).

## Public-demo safeguards

- The demo is open without an access code; anyone who reaches it shares the daily analysis allowance.
- Audio uploaders must confirm they own the audio or have permission to process it.
- Temporary audio and preview files are deleted after each analysis.
- The demo does not create user accounts, request contact information, or save catalog records.
- Model response storage is disabled, and OpenAI Agents SDK tracing is disabled.
- Direct Google Sheets sharing was replaced with a downloadable CSV so the app never asks for a consumer email address.
- The built-in daily counter is appropriate for a small demonstration. Use a managed rate limiter and database before supporting significant public traffic.
- Keep all credentials in Replit Secrets. Never place them in this repository.

Read [PRIVACY.md](PRIVACY.md) for the consumer-facing data flow, third-party processing disclosure, and security boundaries.

## Taxonomy

The bundled vocabulary follows the structure of the supplied Paradrift catalog: genre/subgenre, mood, style, instruments, tempo, references, and sync usage. Upload an `.xlsx` export of the category workbook in the sidebar to use the full current vocabulary without bundling private catalog and rights data into the application.

## Important limitations

- BPM and key detection are estimates and require review.
- Model-generated genre, mood, and sync tags are suggestions.
- Rights and ownership identifiers are never inferred.
- The SQLite usage counter stores only a calendar date and aggregate analysis count. It does not store names, IP addresses, audio, links, or metadata.
