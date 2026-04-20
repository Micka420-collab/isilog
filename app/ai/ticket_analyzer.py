from __future__ import annotations

from pathlib import Path

from app.ai.ollama_client import OllamaClient
from app.ai.learning_service import LearningService
from app.core.category_mapper import CategoryMapper
from app.core.models import TicketData


class TicketAnalyzer:
    def __init__(
        self,
        ollama: OllamaClient,
        model_name: str,
        prompt_path: Path,
        category_mapper: CategoryMapper,
        learning_service: LearningService,
    ):
        self.ollama = ollama
        self.model_name = model_name
        self.system_prompt = prompt_path.read_text(encoding="utf-8")
        self.category_mapper = category_mapper
        self.learning_service = learning_service

    def _build_prompt(self, transcript: str, learning_context: str) -> str:
        allowed = ", ".join(self.category_mapper.allowed_codes())
        return (
            f"Codes catégories autorisés: {allowed}\n\n"
            f"Contexte apprentissage local:\n{learning_context}\n\n"
            f"Transcription:\n{transcript}\n"
        )

    def analyze(self, transcript: str, feedback_rows: list[dict]) -> TicketData:
        learning_context = self.learning_service.build_learning_context(transcript, feedback_rows)
        prompt = self._build_prompt(transcript, learning_context)
        raw = self.ollama.generate_json(self.model_name, prompt=prompt, system=self.system_prompt)
        ticket = TicketData.model_validate(raw)
        ticket.categorie_label = self.category_mapper.resolve_label(ticket.categorie_code)
        return ticket
