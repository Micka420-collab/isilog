param(
  [string]$PythonExe = "py -3.11",
  [string]$OllamaModel = "gemma3:4b"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "[1/6] Création environnement virtuel..."
if (-not (Test-Path ".venv")) {
  & py -3.11 -m venv .venv
}

Write-Host "[2/6] Installation dépendances Python..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "[3/6] Installation Playwright Chromium..."
& .\.venv\Scripts\python.exe -m playwright install chromium

Write-Host "[4/6] Vérification Ollama..."
$ollamaExists = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaExists) {
  Write-Host "Ollama non trouvé. Tentative d'installation via winget..."
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
  } else {
    throw "winget introuvable. Installez Ollama manuellement: https://ollama.com/download/windows"
  }
}

Write-Host "[5/6] Démarrage service Ollama si nécessaire..."
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

Write-Host "[6/6] Téléchargement modèle Gemma local ($OllamaModel)..."
ollama pull $OllamaModel

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Fichier .env créé depuis .env.example"
}

Write-Host "Installation terminée. Lancez: .\\scripts\\run_dev.bat"
