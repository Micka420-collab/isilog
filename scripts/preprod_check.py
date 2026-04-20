from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_check(name: str, fn) -> tuple[bool, str]:
    try:
        detail = fn()
        return True, detail or "OK"
    except Exception as exc:
        return False, str(exc)


def check_files() -> str:
    required = [
        ROOT / "config" / "categories.json",
        ROOT / "config" / "isilog_selectors.json",
        ROOT / "app" / "prompts" / "helpdesk_extraction_system_prompt.txt",
        ROOT / ".env.example",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Fichiers manquants: " + ", ".join(missing))
    return "Fichiers de configuration présents"


def check_json_config() -> str:
    json.loads((ROOT / "config" / "categories.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "config" / "isilog_selectors.json").read_text(encoding="utf-8"))
    return "JSON de configuration valide"


def check_settings_and_db() -> str:
    from app.core.settings import load_settings
    from app.storage.sqlite_store import SQLiteStore

    settings = load_settings(str(ROOT / ".env" if (ROOT / ".env").exists() else ROOT / ".env.example"))
    store = SQLiteStore(settings.db_path)
    _ = store.get_recent_feedback(limit=1)
    return f"Settings OK, SQLite OK ({settings.db_path})"


def check_categories() -> str:
    from app.core.category_mapper import CategoryMapper

    mapper = CategoryMapper(ROOT / "config" / "categories.json")
    if not mapper.allowed_codes():
        raise ValueError("Aucun code catégorie disponible")
    _ = mapper.resolve_label("autre_incident")
    return f"{len(mapper.allowed_codes())} codes catégories chargés"


def check_local_services() -> str:
    from app.core.settings import load_settings
    from app.core.healthcheck import LocalHealthChecker

    settings = load_settings(str(ROOT / ".env" if (ROOT / ".env").exists() else ROOT / ".env.example"))
    checker = LocalHealthChecker(settings.ollama_url, settings.ollama_model, timeout_seconds=3)
    statuses = checker.run()
    ko = [f"{s.name}: {s.detail}" for s in statuses if not s.ok]
    if ko:
        return "AVERTISSEMENT -> " + " | ".join(ko)
    return "Ollama, modèle Gemma et Edge détectés"


def main() -> int:
    checks = [
        ("Présence fichiers", check_files),
        ("Validité JSON", check_json_config),
        ("Settings + SQLite", check_settings_and_db),
        ("Catégories", check_categories),
        ("Services locaux", check_local_services),
    ]

    has_error = False
    print("=== Pré-check production Isilog Local Assistant ===")
    for name, fn in checks:
        ok, detail = run_check(name, fn)
        icon = "✅" if ok else "❌"
        print(f"{icon} {name}: {detail}")
        if not ok:
            has_error = True

    print("=== Fin pré-check ===")
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
