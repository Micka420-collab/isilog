from __future__ import annotations

from dataclasses import dataclass

from app.ai.ticket_analyzer import TicketAnalyzer
from app.ai.transcriber import Transcriber
from app.browser.helpdesk_automator import HelpdeskAutomator
from app.core.models import TicketData
from app.storage.sqlite_store import SQLiteStore


@dataclass
class PipelineService:
    transcriber: Transcriber
    analyzer: TicketAnalyzer
    automator: HelpdeskAutomator
    store: SQLiteStore

    def transcribe(self, audio_path: str) -> str:
        return self.transcriber.transcribe_file(audio_path).text

    def analyze(self, transcript: str) -> TicketData:
        feedback_rows = self.store.get_recent_feedback(limit=150)
        return self.analyzer.analyze(transcript, feedback_rows=feedback_rows)

    def save_draft(self, audio_path: str, transcript: str, ticket: TicketData) -> int:
        return self.store.save_ticket(audio_path=audio_path, transcript=transcript, ticket=ticket, submitted=False)

    def confirm_final(self, transcript: str, ticket: TicketData) -> None:
        self.store.save_feedback(transcript=transcript, final_ticket=ticket)

    def open_helpdesk_ticket_page(self, helpdesk_url: str, browser_channel: str, ticket_type: str) -> str:
        return self.automator.open_ticket_page(
            helpdesk_url=helpdesk_url,
            browser_channel=browser_channel,
            ticket_type=ticket_type,
            headless=False,
        )

    def prefill_helpdesk(self, helpdesk_url: str, ticket: TicketData, browser_channel: str, ticket_type: str) -> str:
        return self.automator.open_and_prefill(
            helpdesk_url=helpdesk_url,
            ticket=ticket,
            browser_channel=browser_channel,
            ticket_type=ticket_type,
            headless=False,
        )
