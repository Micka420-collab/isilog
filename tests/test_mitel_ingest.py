from pathlib import Path

from app.audio.mitel_ingest import MitelIngestService


def test_latest_recording_returns_most_recent(tmp_path: Path) -> None:
    older = tmp_path / "old.wav"
    newer = tmp_path / "new.wav"
    older.write_text("a", encoding="utf-8")
    newer.write_text("b", encoding="utf-8")

    import os
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    service = MitelIngestService(tmp_path)
    latest = service.latest_recording()
    assert latest.name == "new.wav"
