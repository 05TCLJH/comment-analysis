"""原始 API 响应落盘。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RawFileRepository:
    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir = raw_dir

    def save_payload(
        self,
        *,
        platform: str,
        job_id: str,
        payload: dict[str, Any],
    ) -> Path:
        target_dir = self.raw_dir / platform.strip().lower()
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / f"{job_id}.json"
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path
