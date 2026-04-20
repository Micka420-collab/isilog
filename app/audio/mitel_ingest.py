from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg"}


@dataclass
class MitelIngestService:
    recordings_dir: Path

    def latest_recording(self) -> Path:
        if not self.recordings_dir.exists() or not self.recordings_dir.is_dir():
            raise FileNotFoundError(
                f"Dossier Mitel introuvable: {self.recordings_dir}. Configurez MITEL_RECORDINGS_DIR dans .env"
            )

        candidates = [
            p
            for p in self.recordings_dir.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ]
        if not candidates:
            raise FileNotFoundError(
                f"Aucun fichier audio trouvé dans {self.recordings_dir} (extensions: {sorted(SUPPORTED_AUDIO_EXTENSIONS)})"
            )
        return max(candidates, key=lambda p: p.stat().st_mtime)
