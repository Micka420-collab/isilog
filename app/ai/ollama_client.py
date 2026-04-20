from __future__ import annotations

import json
from typing import Any

import requests


class OllamaClient:
    def __init__(self, base_url: str, timeout_seconds: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def generate_json(self, model: str, prompt: str, system: str) -> dict[str, Any]:
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        raw = data.get("response", "{}")
        return json.loads(raw)
