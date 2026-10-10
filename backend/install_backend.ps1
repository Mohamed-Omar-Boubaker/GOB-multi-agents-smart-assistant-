<#
.SYNOPSIS
    Script d'installation automatique du Backend PCD Agent

.DESCRIPTION
    Ce script crée un environnement virtuel Python et installe toutes les dépendances backend.
    
.EXAMPLE
    .\install_backend.ps1
    
.NOTES
    Auteur: Montassar
    Date: 22 Feb 2026
#>

param(
    [switch]$Clean,  # Supprimer l'ancien venv avant de créer le nouveau
    [switch]$SkipVenv  # Installer dans l'environnement actuel sans créer de venv
)

# Couleurs pour les messages
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-ErrorMsg { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host "  🚀 INSTALLATION BACKEND PCD AGENT" -ForegroundColor Magenta
Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host ""

# Vérifier que Python est installé
Write-Info "Vérification de Python..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python trouvé: $pythonVersion"
} catch {
    Write-ErrorMsg "Python n'est pas installé ou n'est pas dans le PATH"
    Write-Info "Téléchargez Python depuis: https://www.python.org/downloads/"
    exit 1
}

# Vérifier que nous sommes dans le bon dossier
$requirementsFile = "requirements.txt"
if (-not (Test-Path $requirementsFile)) {
    Write-ErrorMsg "Fichier $requirementsFile introuvable"
    Write-Info "Assurez-vous d'exécuter ce script depuis le dossier backend/"
    exit 1
}

$venvPath = "..\venv"

# Supprimer l'ancien venv si demandé
if ($Clean -and (Test-Path $venvPath)) {
    Write-Warning "Suppression de l'ancien environnement virtuel..."
    Remove-Item -Path $venvPath -Recurse -Force
    Write-Success "Ancien venv supprimé"
}

# Créer l'environnement virtuel (sauf si --SkipVenv)
if (-not $SkipVenv) {
    if (Test-Path $venvPath) {
        Write-Info "Environnement virtuel existant trouvé: $venvPath"
    } else {
        Write-Info "Création de l'environnement virtuel..."
        python -m venv $venvPath
        
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMsg "Erreur lors de la création du venv"
            exit 1
        }
        
        Write-Success "Environnement virtuel créé: $venvPath"
    }
    
    # Activer l'environnement virtuel
    Write-Info "Activation de l'environnement virtuel..."
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    
    if (-not (Test-Path $activateScript)) {
        Write-ErrorMsg "Script d'activation introuvable: $activateScript"
        exit 1
    }
    
    & $activateScript
    Write-Success "Environnement virtuel activé"
} else {
    Write-Warning "Installation dans l'environnement Python actuel (--SkipVenv)"
}

Write-Host ""
Write-Host "-" * 70 -ForegroundColor Gray

# Mettre à jour pip
Write-Info "Mise à jour de pip..."
python -m pip install --upgrade pip --quiet
Write-Success "pip mis à jour"

# Installer les dépendances
Write-Host ""
Write-Info "Installation des dépendances depuis $requirementsFile..."
Write-Host ""

python -m pip install -r $requirementsFile

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-ErrorMsg "Erreur lors de l'installation des dépendances"
    Write-Info "Vérifiez les messages d'erreur ci-dessus"
    exit 1
}

Write-Host ""
Write-Host "-" * 70 -ForegroundColor Gray
Write-Host ""

# Vérifier quelques packages critiques
Write-Info "Vérification des packages critiques..."
$criticalPackages = @("fastapi", "uvicorn", "openai", "faster-whisper", "httpx", "paho-mqtt")
$allInstalled = $true

foreach ($package in $criticalPackages) {
    $installed = python -m pip show $package 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "$package installé"
    } else {
        Write-ErrorMsg "$package NON installé"
        $allInstalled = $false
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Magenta

if ($allInstalled) {
    Write-Host "  ✅ INSTALLATION TERMINÉE AVEC SUCCÈS!" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Magenta
    Write-Host ""
    Write-Success "Toutes les dépendances ont été installées"
    Write-Host ""
    Write-Info "Pour démarrer le backend:"
    Write-Host "  1. Activez l'environnement: ..\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  2. Lancez le serveur: uvicorn backend.main:app --reload --port 8000" -ForegroundColor Yellow
    Write-Host ""
    Write-Info "Ou utilisez le script de démarrage:"
    Write-Host "  .\start_backend.ps1" -ForegroundColor Yellow
} else {
    Write-Host "  ⚠️  INSTALLATION TERMINÉE AVEC AVERTISSEMENTS" -ForegroundColor Yellow
    Write-Host "=" * 70 -ForegroundColor Magenta
    Write-Host ""
    Write-Warning "Certains packages critiques ne sont pas installés"
    Write-Info "Vérifiez les erreurs ci-dessus et réessayez"
}

Write-Host ""
