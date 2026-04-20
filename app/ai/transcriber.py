from __future__ import annotations

from faster_whisper import WhisperModel

from app.core.models import TranscriptResult


class Transcriber:
    def __init__(self, model_size: str, device: str, compute_type: str):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe_file(self, audio_path: str) -> TranscriptResult:
        segments, info = self.model.transcribe(audio_path, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return TranscriptResult(
            text=text,
            language=info.language,
            duration_seconds=float(getattr(info, "duration", 0.0) or 0.0),
        )
