"""Shared, machine-independent paths for AEC demo scripts."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


REPO_ROOT = Path(
    os.environ.get("AEC_DEMO_ROOT", Path(__file__).resolve().parents[1])
).expanduser().resolve()
RENDER_ROOT = Path(
    os.environ.get("AEC_RENDER_ROOT", REPO_ROOT / "renders" / "ocean_view")
).expanduser().resolve()
HDRI_PATH = Path(os.environ.get("AEC_HDRI_PATH", "")).expanduser()
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
FFMPEG_BIN = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or "ffmpeg"


def require_file(path: Path, variable: str) -> Path:
    """Return a configured file or fail with a useful configuration message."""
    if path and path.is_file():
        return path
    raise FileNotFoundError(
        f"Set {variable} to an existing file (current value: {path or '<empty>'})."
    )
