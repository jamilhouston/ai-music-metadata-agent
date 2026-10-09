# Privacy and Security Notes

Last reviewed: October 9, 2026

This portfolio prototype is designed around data minimization. It demonstrates a useful AI workflow without building a consumer database.

## Information the demo does not collect

- No consumer account, name, email address, phone number, or mailing address.
- No user account or advertising profile is maintained by the application. The deployment includes Replit-injected Umami analytics instrumentation and custom events for analysis, approval and export activity. Exact browser tracking behavior, host logs, identifiers and retention require separate verification with the hosting provider.
- The application is designed not to retain a permanent copy of uploaded audio. Hosting logs, temporary storage failure cases, and third-party provider retention are separate considerations.
- No permanent server-side copy of generated metadata.
- No rights or ownership information inferred by AI.

## What is processed

When a consumer uploads audio, the original file is temporarily available to the application for technical analysis. The application creates a short mono preview and sends that preview, any context the consumer entered, technical measurements, and relevant streaming-link metadata to the OpenAI API for metadata suggestions. The application attempts to delete temporary audio and preview files after processing. An error occurring *during preview creation* can leave an intermediate file; deletion is not guaranteed on every error path. Do not upload sensitive or irreplaceable recordings until this is fixed and independently tested.

Spotify and Apple Music links are sent to the applicable provider's public metadata endpoint. Direct Google account sharing is not used. Consumers can download a CSV and import it into a Google Sheet they control.

Exports are generated in memory and downloaded only at the consumer's request. The application keeps the current result in temporary session memory so it can be reviewed and exported; it is not written to the catalog database.

## Operational usage measurement

The demo maintains one aggregate counter containing only the date and total number of analyses performed that day. It does not contain a consumer identifier, IP address, audio filename, streaming link, or metadata. The counter exists only to limit API spending and abuse. It is separate from the deployment's analytics instrumentation and any technical logging performed by the host.

## OpenAI processing

The application sets model response storage to false and disables Agents SDK tracing. According to OpenAI's API data-control documentation, API inputs and outputs are not used to train OpenAI models unless the API account owner explicitly opts in. Standard Chat Completions and Responses requests may still be retained in abuse-monitoring logs for up to 30 days. Eligible organizations can separately apply for additional retention controls such as Zero Data Retention.

Reference: https://developers.openai.com/api/docs/guides/your-data

## Security controls

- The current deployed demo is available without a shared access code; visitors share the daily analysis allowance. Authentication and user-specific quotas are not implemented.
- The OpenAI key remains in the host's encrypted secret store and is never delivered to a browser or committed to source control.
- A project-specific, restricted, rotated API key is recommended. Key scoping, expiration and host configuration have not been independently audited.
- Audio uploads are restricted by file type, size, and duration.
- Consumers must confirm that they own or have permission to process uploaded audio.
- The demo has a daily analysis ceiling.
- The app initially requires approval before export. This control is incomplete: approval is not currently invalidated automatically after metadata edits or a new analysis. Users should explicitly re-review each result before exporting.
- Exceptions are handled without intentionally displaying API keys or credentials.

## Honest limitations

This is a portfolio demonstration, not a compliance certification or a substitute for legal advice. Hosting providers and third-party API providers may maintain their own security and operational logs under their respective policies. The password-free portfolio demo should not be treated as a substitute for individual authentication, managed rate limiting, verified analytics/privacy disclosures, monitoring, and a formal privacy review before broad commercial use.
