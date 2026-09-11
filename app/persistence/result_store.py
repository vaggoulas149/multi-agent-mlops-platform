"""Local persistence for completed incident investigations.

Investigation results are stored as human-readable JSON artifacts under the
configured artifact directory. Each artifact receives a unique investigation
identifier and a UTC creation timestamp.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from app.config import ARTIFACT_DIR


def save_investigation(
        record: Mapping[str, Any],
) -> str:
    """Persist an investigation record as a local JSON artifact.

    The function creates the artifact directory when necessary, assigns a
    unique investigation identifier, adds a UTC timestamp, and writes the
    resulting payload to disk.

    Args:
        record: Investigation data to include in the persisted artifact.
            Values must be JSON serializable.

    Returns:
        String representation of the path to the saved JSON artifact.
    """
    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    investigation_id = str(uuid4())
    output_path = ARTIFACT_DIR / f"{investigation_id}.json"

    payload: dict[str, Any] = {
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
