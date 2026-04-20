from app.ai.learning_service import LearningService


def test_build_learning_context_contains_examples() -> None:
    service = LearningService()
    rows = [
        {
            "transcript": "probleme vpn site paris",
            "category_code": "vpn",
            "ticket": {"objet": "VPN KO", "resume_interne": "Impossible de se connecter"},
        }
    ]
    context = service.build_learning_context("vpn ne marche plus", rows)
    assert "Exemple 1" in context
    assert "vpn" in context
