from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import ARTIFACT_DIR


def save_investigation(record: dict) -> str:
    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    investigation_id = str(uuid4())
    output_path = ARTIFACT_DIR / f"{investigation_id}.json"

    payload = {
        "investigation_id": investigation_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **record,
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return str(output_path)
