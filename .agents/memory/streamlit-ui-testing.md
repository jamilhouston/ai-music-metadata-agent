---
name: Streamlit UI testing
description: Constraints for running local Streamlit interaction tests in this project.
---

Use an explicit project-root path when creating `AppTest` from a test module because Streamlit resolves relative script paths from the caller file's directory.

**Why:** `AppTest.from_file("app.py")` called from `tests/` resolves to the wrong directory.

**How to apply:** Build the app path from the test file's parent directory and isolate live-service variables in fixture-only tests. The user requested a password-free demo, so access-gate environment cleanup is no longer required.