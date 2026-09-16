---
name: Streamlit UI testing
description: Constraints for running local Streamlit interaction tests in this project.
---

Use an explicit project-root path when creating `AppTest` from a test module because Streamlit resolves relative script paths from the caller file's directory. Clear deployment-only access-gate variables in local UI tests so the fixture reaches the application flow instead of the login screen.

**Why:** The test runner environment can expose the app's access-code secret, and `AppTest.from_file("app.py")` called from `tests/` resolves to the wrong directory.

**How to apply:** Build the app path from the test file's parent directory and remove `APP_ACCESS_CODE`, `REPLIT_DEPLOYMENT`, and any other live-service variables before running a fixture-only interaction test.