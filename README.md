# Isilog Local Ticket Assistant (MVP Windows)

Application **100 % locale** pour assister la création de tickets helpdesk Isilog depuis un appel utilisateur.

## Pourquoi cette stack (compromis MVP entreprise Windows)
- **Python 3.11 + Tkinter**: GUI native simple, stable, sans dépendance lourde côté poste, facile à empaqueter en `.exe`.
- **faster-whisper local**: transcription offline rapide.
- **Ollama + Gemma local**: IA locale sans cloud.
- **Playwright**: pilotage navigateur robuste sans modifier le site Isilog.
- **Pydantic + SQLite**: validation de données et persistance locale simple.
- **Logs JSON structurés**: exploitables en support/diagnostic.

## Intégration Mitel (clarification)
- Le MVP **ne se connecte pas à une API Mitel propriétaire** (souvent indisponible en poste agent).
- Il propose 3 modes locaux robustes: lecture d'un fichier audio manuel, chargement du **dernier enregistrement Mitel** (`MITEL_RECORDINGS_DIR`), et **écoute directe de l'appel** via capture audio loopback Windows.
- Cela permet d'avoir la transcription dans l'app sans cloud ni modification de Mitel.

## Décrocher/Raccrocher automatique (dans l'app)
- Bouton **Décrocher (auto)**: démarre l'écoute directe + ouvre automatiquement un ticket web (type `incident` ou `demande`).
- Bouton **Raccrocher (auto)**: stoppe l'écoute, lance transcription + analyse, puis préremplit le ticket helpdesk web.
- Important: sans API officielle Mitel, ce déclenchement est piloté par les boutons de cette app (pas par interception native du bouton Mitel).

## Fonctionnalités MVP
### Priorité 1 (implémentée)
- Import audio local.
- Transcription locale.
- Analyse locale Gemma via Ollama.
- Ticket structuré éditable.
- Export JSON.
- Copie du résumé interne.

### Priorité 2 (implémentée, prête à adapter)
- Ouverture/contrôle navigateur vers Isilog.
- Préremplissage des champs.
- **Aucun clic automatique sur Enregistrer**.
- Couche de sélecteurs configurable dans `config/isilog_selectors.json`.

### Priorité 3 (bases implémentées)
- SQLite local pour tickets + feedback validé.
- Logs applicatifs structurés.
- Scripts build `.exe`.
- Structure modulaire extensible.

## Auto-amélioration locale (sans cloud)
Le système ne réentraîne pas le modèle, mais s'améliore localement via:
1. stockage des tickets **corrigés/validés**,
2. injection des exemples proches dans le prompt (few-shot dynamique),
3. statistiques de catégories validées pour guider la prédiction.

Concrètement: bouton **"Valider ticket final"** enregistre un feedback local, utilisé pour les analyses suivantes.

## Arborescence
```text
app/
  ai/
    learning_service.py
    ollama_client.py
    ticket_analyzer.py
    transcriber.py
  browser/
    helpdesk_automator.py
  core/
    category_mapper.py
    models.py
    pipeline.py
    settings.py
  prompts/
    helpdesk_extraction_system_prompt.txt
  storage/
    sqlite_store.py
  ui/
    main_window.py
  utils/
    logging_utils.py
  __init__.py
  main.py
config/
  categories.json
  isilog_selectors.json
examples/
  sample_transcript.txt
scripts/
  run_dev.bat
  build_exe.bat
tests/
  test_category_mapper.py
  test_learning_service.py
  test_models.py
.env.example
requirements.txt
README.md
```

## Installation automatique Windows (recommandée)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install_windows.ps1 -OllamaModel gemma3:4b
```
Ce script installe:
- environnement Python + dépendances,
- navigateur Playwright,
- Ollama (via winget si absent),
- modèle Gemma local.

## Prérequis Windows
1. Windows 10/11
2. Python 3.11+
3. [Ollama Windows](https://ollama.com/download)
4. Modèle Gemma local téléchargé (exemple):
   ```powershell
   ollama pull gemma3:4b
   ```
5. Dépendances Python:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

## Lancement pas à pas (mode dev)
```powershell
copy .env.example .env
.\.venv\Scripts\activate
python -m app.main
```

Ou script Windows:
```powershell
scripts\run_dev.bat
```

## Usage quotidien agent support
1. Ouvrir l’application.
2. Choisir le type de ticket (**incident** ou **demande**).
3. Utiliser soit les boutons manuels, soit **Décrocher (auto)** / **Raccrocher (auto)**.
3. Si mode manuel/Mitel: cliquer **Transcrire** puis **Analyser**.
4. Vérifier et corriger le ticket.
5. Corriger le ticket dans le formulaire.
6. **Exporter JSON** (optionnel).
7. **Ouvrir / Remplir le helpdesk**.
8. Vérifier dans le navigateur.
9. Cliquer manuellement sur **Enregistrer** dans Isilog.
10. Cliquer **Valider ticket final** dans l’app pour apprentissage local.

## Configuration
### `.env`
- `OLLAMA_URL`, `OLLAMA_MODEL`
- `HELPDESK_URL` (par défaut: `https://helpdesk.brgm.fr/IsilogWebSystem/Pages/HelpDesk/HELP005.aspx?Type=PROPERTY&Action=C&IwsId=1`)
- `BROWSER_CHANNEL=msedge`
- `MITEL_RECORDINGS_DIR` (dossier local des enregistrements Mitel, défaut: `C:/Users/hotline6/AppData/Roaming/Mitel/MitelDialer`)
- `LIVE_RECORDINGS_DIR` (sortie des captures en direct)
- `LIVE_SAMPLE_RATE`, `LIVE_CHANNELS`
- `DEBUG=false`

### Catégories
Éditer `config/categories.json` pour mapper `categorie_code` -> libellé helpdesk autorisé.

### Sélecteurs Isilog
Éditer `config/isilog_selectors.json` selon votre UI réelle Isilog. URL préconfigurée: `https://helpdesk.brgm.fr/IsilogWebSystem/Pages/HelpDesk/HELP005.aspx?Type=PROPERTY&Action=C&IwsId=1`.

## Build exécutable Windows
```powershell
.\.venv\Scripts\activate
scripts\build_exe.bat
```
Sortie:
- `dist\IsilogLocalAssistant\IsilogLocalAssistant.exe`

## Sécurité / conformité
- Full local, aucun appel cloud.
- Données dans SQLite locale.
- Logs JSON locaux.
- Debug désactivable via `.env`.
- Pas d'autosubmit final côté helpdesk.

## Extension future (prévue architecture)
- Capture audio direct depuis softphone/système.
- Historique riche et filtres.
- Contrôles qualité ticket.
- Base de connaissance locale.
- Indicateurs de performance et analytics internes.
