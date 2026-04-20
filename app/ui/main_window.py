from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from pydantic import ValidationError

from app.ai.learning_service import LearningService
from app.audio.live_capture import LiveCallRecorder
from app.audio.mitel_ingest import MitelIngestService
from app.ai.ollama_client import OllamaClient
from app.ai.ticket_analyzer import TicketAnalyzer
from app.ai.transcriber import Transcriber
from app.browser.helpdesk_automator import HelpdeskAutomator
from app.core.category_mapper import CategoryMapper
from app.core.models import TicketData
from app.core.pipeline import PipelineService
from app.core.settings import load_settings
from app.storage.sqlite_store import SQLiteStore
from app.utils.logging_utils import configure_logging


TICKET_FIELDS = [
    "demandeur",
    "beneficiaire",
    "site",
    "objet",
    "description",
    "categorie_code",
    "categorie_label",
    "urgence",
    "impact",
    "actions_deja_realisees",
    "resolution_proposee",
    "informations_manquantes",
    "niveau_confiance",
    "resume_interne",
]


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.settings = load_settings()
        self.logger = configure_logging(self.settings.log_path, self.settings.debug)

        self.store = SQLiteStore(self.settings.db_path)
        mapper = CategoryMapper(Path("config/categories.json"))
        analyzer = TicketAnalyzer(
            ollama=OllamaClient(self.settings.ollama_url, self.settings.timeout_seconds),
            model_name=self.settings.ollama_model,
            prompt_path=Path("app/prompts/helpdesk_extraction_system_prompt.txt"),
            category_mapper=mapper,
            learning_service=LearningService(),
        )
        self.pipeline = PipelineService(
            transcriber=Transcriber(
                self.settings.whisper_model_size,
                self.settings.whisper_device,
                self.settings.whisper_compute_type,
            ),
            analyzer=analyzer,
            automator=HelpdeskAutomator(Path("config/isilog_selectors.json")),
            store=self.store,
        )

        self.mitel_ingest = MitelIngestService(self.settings.mitel_recordings_dir)
        self.live_recorder = LiveCallRecorder(
            output_dir=self.settings.live_recordings_dir,
            sample_rate=self.settings.live_sample_rate,
            channels=self.settings.live_channels,
        )
        self.audio_path = ""
        self.transcript_text = ""
        self.ticket = TicketData()
        self.ticket_vars: dict[str, tk.StringVar] = {}
        self.ticket_type_var = tk.StringVar(value="incident")

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.root.title(self.settings.app_name)
        self.root.geometry("1200x820")

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Type ticket").pack(side=tk.LEFT, padx=4)
        ttk.Combobox(top, textvariable=self.ticket_type_var, values=["incident", "demande"], width=12, state="readonly").pack(side=tk.LEFT, padx=4)

        ttk.Button(top, text="Charger un audio", command=self.load_audio).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Charger dernier audio Mitel", command=self.load_latest_mitel_audio).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Décrocher (auto)", command=self.decrocher_auto).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Raccrocher (auto)", command=self.raccrocher_auto).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Démarrer écoute appel", command=self.start_live_capture).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Stop écoute + traiter", command=self.stop_live_capture).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Transcrire", command=self.transcribe_audio).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Analyser", command=self.analyze_transcript).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Copier le résumé", command=self.copy_summary).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Exporter JSON", command=self.export_json).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Ouvrir / Remplir le helpdesk", command=self.prefill_helpdesk).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Valider ticket final", command=self.validate_final_ticket).pack(side=tk.LEFT, padx=4)

        main = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=1)
        main.add(right, weight=1)

        ttk.Label(left, text="Transcription").pack(anchor=tk.W)
        self.transcript_widget = tk.Text(left, height=18, wrap=tk.WORD)
        self.transcript_widget.pack(fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(right, text="Ticket éditable")
        form.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(form)
        scrollbar = ttk.Scrollbar(form, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for idx, field in enumerate(TICKET_FIELDS):
            ttk.Label(scroll_frame, text=field).grid(row=idx, column=0, sticky=tk.W, padx=6, pady=4)
            var = tk.StringVar(value="")
            self.ticket_vars[field] = var
            ttk.Entry(scroll_frame, textvariable=var, width=70).grid(row=idx, column=1, sticky=tk.EW, padx=6, pady=4)

        status = ttk.LabelFrame(self.root, text="Logs / Statut")
        status.pack(fill=tk.BOTH, padx=10, pady=8)
        self.status_widget = tk.Text(status, height=8, wrap=tk.WORD)
        self.status_widget.pack(fill=tk.BOTH, expand=True)

        self._status("Application prête.")

    def _status(self, msg: str) -> None:
        self.status_widget.insert(tk.END, msg + "\n")
        self.status_widget.see(tk.END)
        self.logger.info(msg)

    def _sync_form_from_ticket(self) -> None:
        data = self.ticket.model_dump()
        for field in TICKET_FIELDS:
            self.ticket_vars[field].set(str(data.get(field, "")))

    def _sync_ticket_from_form(self) -> TicketData:
        payload = {k: v.get().strip() for k, v in self.ticket_vars.items()}
        return TicketData.model_validate(payload)

    def load_audio(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir un fichier audio",
            filetypes=[("Audio", "*.wav *.mp3 *.m4a *.ogg"), ("Tous", "*.*")],
        )
        if not path:
            return
        self.audio_path = path
        self._status(f"Audio chargé: {path}")

    def load_latest_mitel_audio(self) -> None:
        try:
            latest = self.mitel_ingest.latest_recording()
            self.audio_path = str(latest)
            self._status(f"Audio Mitel détecté: {latest}")
        except Exception as exc:
            self._status(f"Erreur import Mitel: {exc}")
            messagebox.showerror("Import Mitel", str(exc))

    def decrocher_auto(self) -> None:
        """Workflow demandé: décrocher => écoute directe + ouverture ticket web."""
        try:
            self.start_live_capture()
            msg = self.pipeline.open_helpdesk_ticket_page(
                helpdesk_url=self.settings.helpdesk_url,
                browser_channel=self.settings.browser_channel,
                ticket_type=self.ticket_type_var.get(),
            )
            self._status(msg)
        except Exception as exc:
            self._status(f"Erreur workflow décrocher: {exc}")
            messagebox.showerror("Décrocher auto", str(exc))

    def raccrocher_auto(self) -> None:
        """Workflow demandé: raccrocher => stop capture + analyse + préremplissage."""
        try:
            self.stop_live_capture()
            self.prefill_helpdesk()
        except Exception as exc:
            self._status(f"Erreur workflow raccrocher: {exc}")
            messagebox.showerror("Raccrocher auto", str(exc))

    def start_live_capture(self) -> None:
        try:
            file_path = self.live_recorder.start(loopback=True)
            self._status(f"Écoute appel démarrée (loopback Windows). Fichier cible: {file_path}")
        except Exception as exc:
            self._status(f"Erreur démarrage écoute: {exc}")
            messagebox.showerror("Écoute directe", str(exc))

    def stop_live_capture(self) -> None:
        try:
            captured = self.live_recorder.stop()
            self.audio_path = str(captured)
            self._status(f"Capture arrêtée: {captured}")
            self.transcribe_audio()
            self.analyze_transcript()
        except Exception as exc:
            self._status(f"Erreur arrêt écoute: {exc}")
            messagebox.showerror("Écoute directe", str(exc))

    def transcribe_audio(self) -> None:
        if not self.audio_path:
            messagebox.showwarning("Audio requis", "Chargez un fichier audio avant la transcription.")
            return
        try:
            self._status("Transcription en cours...")
            self.transcript_text = self.pipeline.transcribe(self.audio_path)
            self.transcript_widget.delete("1.0", tk.END)
            self.transcript_widget.insert("1.0", self.transcript_text)
            self._status("Transcription terminée.")
        except Exception as exc:
            self._status(f"Erreur transcription: {exc}")
            messagebox.showerror("Erreur", str(exc))

    def analyze_transcript(self) -> None:
        transcript = self.transcript_widget.get("1.0", tk.END).strip()
        if not transcript:
            messagebox.showwarning("Transcription requise", "La zone transcription est vide.")
            return
        try:
            self._status("Analyse Gemma/Ollama en cours...")
            self.ticket = self.pipeline.analyze(transcript)
            self._sync_form_from_ticket()
            self.pipeline.save_draft(self.audio_path, transcript, self.ticket)
            self._status("Analyse terminée, ticket généré.")
        except ValidationError as exc:
            self._status(f"Réponse IA invalide: {exc}")
            messagebox.showerror("Erreur validation", str(exc))
        except Exception as exc:
            self._status(f"Erreur analyse: {exc}")
            messagebox.showerror("Erreur", str(exc))

    def copy_summary(self) -> None:
        resume = self.ticket_vars["resume_interne"].get().strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(resume)
        self._status("Résumé copié.")

    def export_json(self) -> None:
        try:
            ticket = self._sync_ticket_from_form()
            path = filedialog.asksaveasfilename(
                title="Exporter le ticket JSON",
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
            )
            if not path:
                return
            Path(path).write_text(ticket.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
            self._status(f"Ticket exporté: {path}")
        except Exception as exc:
            self._status(f"Erreur export: {exc}")
            messagebox.showerror("Erreur", str(exc))

    def prefill_helpdesk(self) -> None:
        try:
            ticket = self._sync_ticket_from_form()
            message = self.pipeline.prefill_helpdesk(
                helpdesk_url=self.settings.helpdesk_url,
                ticket=ticket,
                browser_channel=self.settings.browser_channel,
                ticket_type=self.ticket_type_var.get(),
            )
            self._status(message)
        except Exception as exc:
            self._status(f"Erreur navigateur: {exc}")
            messagebox.showerror("Erreur navigateur", str(exc))

    def validate_final_ticket(self) -> None:
        transcript = self.transcript_widget.get("1.0", tk.END).strip()
        if not transcript:
            messagebox.showwarning("Transcription requise", "Impossible de valider sans transcription.")
            return
        try:
            ticket = self._sync_ticket_from_form()
            self.pipeline.confirm_final(transcript, ticket)
            self._status("Ticket final validé et appris localement.")
        except Exception as exc:
            self._status(f"Erreur validation finale: {exc}")
            messagebox.showerror("Erreur", str(exc))


def run_app() -> None:
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
