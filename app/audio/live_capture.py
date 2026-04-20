from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.io.wavfile import write as wav_write

try:
    import sounddevice as sd
except Exception:  # pragma: no cover
    sd = None


@dataclass
class LiveCallRecorder:
    output_dir: Path
    sample_rate: int = 16000
    channels: int = 1
    _q: queue.Queue = field(default_factory=queue.Queue, init=False)
    _frames: list[np.ndarray] = field(default_factory=list, init=False)
    _stream: object | None = field(default=None, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _running: bool = field(default=False, init=False)
    _current_file: Path | None = field(default=None, init=False)

    def start(self, device: int | None = None, loopback: bool = False) -> Path:
        if sd is None:
            raise RuntimeError("Module sounddevice indisponible. Installez les dépendances audio.")
        if self._running:
            raise RuntimeError("Une capture audio est déjà en cours.")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.utcnow().strftime("live_call_%Y%m%d_%H%M%S.wav")
        self._current_file = self.output_dir / filename
        self._frames = []
        self._running = True

        def callback(indata, frames, time, status):
            if status:
                # keep recording; status exposed in logs by caller if needed
                pass
            self._q.put(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            device=device,
            callback=callback,
            blocksize=2048,
            latency="low",
            extra_settings=sd.WasapiSettings(loopback=loopback) if hasattr(sd, "WasapiSettings") else None,
        )
        self._stream.start()

        def collector() -> None:
            while self._running:
                try:
                    frame = self._q.get(timeout=0.2)
                    self._frames.append(frame)
                except queue.Empty:
                    continue

        self._thread = threading.Thread(target=collector, daemon=True)
        self._thread.start()
        return self._current_file

    def stop(self) -> Path:
        if not self._running or self._current_file is None:
            raise RuntimeError("Aucune capture active.")

        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._stream:
            self._stream.stop()
            self._stream.close()

        if not self._frames:
            raise RuntimeError("Aucune donnée audio capturée.")

        audio = np.concatenate(self._frames, axis=0)
        audio_int16 = np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)
        wav_write(self._current_file, self.sample_rate, audio_int16)
        return self._current_file
