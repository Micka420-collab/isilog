from __future__ import annotations

import shutil
from dataclasses import dataclass

import requests


@dataclass
class HealthStatus:
    name: str
    ok: bool
    detail: str


class LocalHealthChecker:
    def __init__(self, ollama_url: str, ollama_model: str, timeout_seconds: int = 5):
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model
        self.timeout_seconds = timeout_seconds

    def run(self) -> list[HealthStatus]:
        results = [
            self._check_playwright_prereq(),
            self._check_ollama_service(),
            self._check_ollama_model(),
        ]
        return results

    def _check_playwright_prereq(self) -> HealthStatus:
        msedge = shutil.which("msedge") or shutil.which("msedge.exe")
        return HealthStatus(
            name="Browser MS Edge",
            ok=bool(msedge),
            detail="OK" if msedge else "MS Edge introuvable dans le PATH",
        )

    def _check_ollama_service(self) -> HealthStatus:
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=self.timeout_seconds)
            response.raise_for_status()
            return HealthStatus(name="Service Ollama", ok=True, detail="OK")
        except Exception as exc:
            return HealthStatus(name="Service Ollama", ok=False, detail=f"Inaccessible: {exc}")

    def _check_ollama_model(self) -> HealthStatus:
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=self.timeout_seconds)
            response.raise_for_status()
            models = response.json().get("models", [])
            names = [m.get("name", "") for m in models]
            ok = any(name.startswith(self.ollama_model) or name == self.ollama_model for name in names)
            detail = "OK" if ok else f"Modèle manquant: {self.ollama_model}"
            return HealthStatus(name="Modèle Gemma", ok=ok, detail=detail)
        except Exception as exc:
            return HealthStatus(name="Modèle Gemma", ok=False, detail=f"Vérification impossible: {exc}")
