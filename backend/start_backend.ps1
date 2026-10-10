<#
.SYNOPSIS
    Script de démarrage rapide du Backend PCD Agent

.DESCRIPTION
    Active l'environnement virtuel et démarre le serveur FastAPI avec uvicorn.
    
.EXAMPLE
    .\start_backend.ps1
    .\start_backend.ps1 -Port 8001
    .\start_backend.ps1 -NoReload
    
.NOTES
    Auteur: Montassar
    Date: 22 Feb 2026
#>

param(
    [int]$Port = 8000,           # Port du serveur (défaut: 8000)
    [switch]$NoReload,           # Désactiver le rechargement automatique
    [string]$Host = "0.0.0.0"    # Adresse d'écoute (défaut: toutes les interfaces)
)

# Couleurs
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-ErrorMsg { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host "  🚀 DÉMARRAGE BACKEND PCD AGENT" -ForegroundColor Magenta
Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host ""

$venvPath = "..\venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

# Vérifier que le venv existe
if (-not (Test-Path $activateScript)) {
    Write-ErrorMsg "Environnement virtuel introuvable: $venvPath"
    Write-Info "Exécutez d'abord: .\install_backend.ps1"
    exit 1
}

# Activer l'environnement
Write-Info "Activation de l'environnement virtuel..."
& $activateScript

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Erreur lors de l'activation du venv"
    exit 1
}

Write-Success "Environnement virtuel activé"

# Vérifier que uvicorn est installé
try {
    $uvicornVersion = python -m uvicorn --version 2>&1
    Write-Success "uvicorn trouvé"
} catch {
    Write-ErrorMsg "uvicorn n'est pas installé"
    Write-Info "Installez les dépendances: .\install_backend.ps1"
    exit 1
}

Write-Host ""
Write-Info "Configuration:"
Write-Host "  - Host: $Host" -ForegroundColor Yellow
Write-Host "  - Port: $Port" -ForegroundColor Yellow
if ($NoReload) {
    Write-Host "  - Reload: Désactivé" -ForegroundColor Yellow
} else {
    Write-Host "  - Reload: Activé (développement)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "  🌐 Serveur démarré sur http://$Host:$Port" -ForegroundColor Green
Write-Host "  📚 Documentation API: http://localhost:$Port/docs" -ForegroundColor Green
Write-Host "  🔧 Arrêt: Ctrl+C" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""

# Construire la commande uvicorn
$uvicornArgs = @(
    "backend.main:app",
    "--host", $Host,
    "--port", $Port
)

if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

# Démarrer le serveur
try {
    python -m uvicorn @uvicornArgs
} catch {
    Write-ErrorMsg "Erreur lors du démarrage du serveur"
    exit 1
}
