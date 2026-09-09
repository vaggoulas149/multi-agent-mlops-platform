from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "none")

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "investigations"
