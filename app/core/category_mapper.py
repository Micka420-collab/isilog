from __future__ import annotations

import json
from pathlib import Path


class CategoryMapper:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._map = self._load_map(config_path)

    @staticmethod
    def _load_map(config_path: Path) -> dict[str, str]:
        with config_path.open("r", encoding="utf-8") as f:
            content = json.load(f)
        return content.get("code_to_helpdesk", {})

    def resolve_label(self, category_code: str) -> str:
        return self._map.get(category_code, self._map.get("autre_incident", "support_2i"))

    def allowed_codes(self) -> list[str]:
        return sorted(self._map.keys())
