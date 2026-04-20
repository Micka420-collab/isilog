from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.core.models import TicketData


class HelpdeskAutomator:
    def __init__(self, selectors_path: Path, timeout_ms: int = 30000):
        self.selectors = json.loads(selectors_path.read_text(encoding="utf-8"))
        self.timeout_ms = timeout_ms

    def _resolve_ticket_url(self, fallback_helpdesk_url: str, ticket_type: str) -> str:
        typed = self.selectors.get("ticket_page_urls", {}).get(ticket_type)
        if typed:
            return typed
        return self.selectors.get("ticket_page_url") or fallback_helpdesk_url

    def open_ticket_page(
        self,
        helpdesk_url: str,
        ticket_type: str,
        browser_channel: str = "msedge",
        headless: bool = False,
    ) -> str:
        url = self._resolve_ticket_url(helpdesk_url, ticket_type)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=browser_channel, headless=headless)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            page.bring_to_front()
            return f"Formulaire {ticket_type} ouvert: {url}"

    def open_and_prefill(
        self,
        helpdesk_url: str,
        ticket: TicketData,
        ticket_type: str,
        browser_channel: str = "msedge",
        headless: bool = False,
    ) -> str:
        s = self.selectors
        url = self._resolve_ticket_url(helpdesk_url, ticket_type)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=browser_channel, headless=headless)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")

            try:
                page.wait_for_selector(s["fields"]["objet"], timeout=self.timeout_ms)
            except PlaywrightTimeoutError as exc:
                browser.close()
                raise RuntimeError(
                    "Impossible de trouver les champs ticket. Vérifiez selectors/isilog_selectors.json"
                ) from exc

            self._fill_text_fields(page, ticket)
            self._fill_select_fields(page, ticket)

            page.bring_to_front()
            return "Formulaire prérempli. Vérifiez puis cliquez sur Enregistrer manuellement."

    def _fill_text_fields(self, page, ticket: TicketData) -> None:
        mapping = {
            "demandeur": ticket.demandeur,
            "beneficiaire": ticket.beneficiaire,
            "site": ticket.site,
            "objet": ticket.objet,
            "description": ticket.description,
            "actions_deja_realisees": ticket.actions_deja_realisees,
            "resolution_proposee": ticket.resolution_proposee,
            "resume_interne": ticket.resume_interne,
        }
        for key, value in mapping.items():
            selector = self.selectors["fields"].get(key)
            if selector and value:
                page.fill(selector, value)

    def _fill_select_fields(self, page, ticket: TicketData) -> None:
        select_map = {
            "categorie_label": ticket.categorie_label,
            "urgence": ticket.urgence,
            "impact": ticket.impact,
        }
        for key, value in select_map.items():
            selector = self.selectors["fields"].get(key)
            if selector and value:
                try:
                    page.select_option(selector, label=value)
                except Exception:
                    try:
                        page.fill(selector, value)
                    except Exception:
                        continue
