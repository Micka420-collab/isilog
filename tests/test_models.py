import pytest
from pydantic import ValidationError

from app.core.models import TicketData


def test_ticket_data_valid() -> None:
    ticket = TicketData(categorie_code="vpn", niveau_confiance=0.8)
    assert ticket.categorie_code == "vpn"


def test_ticket_data_invalid_category() -> None:
    with pytest.raises(ValidationError):
        TicketData(categorie_code="invalid")
