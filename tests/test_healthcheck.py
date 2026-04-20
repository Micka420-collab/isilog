from app.core.healthcheck import LocalHealthChecker


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_healthcheck_model_present(monkeypatch) -> None:
    checker = LocalHealthChecker("http://localhost:11434", "gemma3:4b")

    def fake_get(*args, **kwargs):
        return DummyResponse({"models": [{"name": "gemma3:4b"}]})

    monkeypatch.setattr("app.core.healthcheck.requests.get", fake_get)
    statuses = checker.run()
    model_status = [s for s in statuses if s.name == "Modèle Gemma"][0]
    assert model_status.ok is True
