from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

import streamlit.components.v1 as components


_EVENT_NAME = re.compile(r"^[a-z0-9_]{1,49}$")


def _script_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":")).replace("<", "\\u003c")


def _safe_data(data: Mapping[str, str | int | float | bool] | None) -> dict[str, str | int | float | bool]:
    if not data:
        return {}
    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str) and isinstance(value, (str, int, float, bool))
    }


def track_event(name: str, data: Mapping[str, str | int | float | bool] | None = None) -> None:
    """Send a safe no-op-able event to Replit's injected Umami tracker."""
    if not _EVENT_NAME.fullmatch(name):
        return
    components.html(
        f"""
        <script>
        (() => {{
          try {{
            window.parent?.umami?.track({_script_json(name)}, {_script_json(_safe_data(data))});
          }} catch (_) {{}}
        }})();
        </script>
        """,
        height=0,
    )