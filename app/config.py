"""Application configuration loaded from environment variables.

This module centralizes runtime configuration used across the project,
including OpenAI model settings, retry limits, artifact storage paths,
and environment-file loading.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
ENV_PATH: Path = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

OPENAI_MODEL: str = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna",
)

OPENAI_REASONING_EFFORT: str = os.getenv(
    "OPENAI_REASONING_EFFORT",
    "none",
)

MAX_RETRIES: int = int(
    os.getenv(
        "MAX_RETRIES",
        "2",
    )
)

ARTIFACT_DIR: Path = (
        PROJECT_ROOT
        / "artifacts"
        / "investigations"
)
