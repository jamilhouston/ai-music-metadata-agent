---
name: Post-merge Python setup
description: Environment-specific requirement for the imported Python app's merge hook.
---

The post-merge setup script must pass `--break-system-packages` to pip because this Replit Python environment enforces PEP 668 and otherwise rejects non-interactive dependency installation.

**Why:** A first hook run failed before compilation because pip treated the environment as externally managed.

**How to apply:** Keep the hook non-interactive and idempotent, and use the project requirements file with the managed project Python environment.