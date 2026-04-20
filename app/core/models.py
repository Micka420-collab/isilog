from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


CategoryCode = Literal[
    "vpn",
    "mot_de_passe",
    "outlook",
    "teams",
    "bdd_droits_acces",
    "bdd_dump",
    "bdd_migration",
    "application_autre",
    "installation_logiciel",
    "station_accueil",
    "reseau",
    "authentification",
    "autre_incident",
]


class TicketData(BaseModel):
    demandeur: str = ""
    beneficiaire: str = ""
    site: str = ""
    objet: str = ""
    description: str = ""
    categorie_code: CategoryCode = "autre_incident"
    categorie_label: str = ""
    urgence: str = ""
    impact: str = ""
    actions_deja_realisees: str = ""
    resolution_proposee: str = ""
    informations_manquantes: str = ""
    niveau_confiance: float = Field(default=0.0, ge=0.0, le=1.0)
    resume_interne: str = ""

    @field_validator("niveau_confiance", mode="before")
    @classmethod
    def coerce_confidence(cls, value: float | str) -> float:
        if value in (None, ""):
            return 0.0
        return float(value)


class TranscriptResult(BaseModel):
    text: str
    language: str
    duration_seconds: float = 0.0


class TicketRecord(BaseModel):
    id: int | None = None
    created_at: datetime
    audio_path: str = ""
    transcript: str
    ticket_json: str
    submitted: bool = False
