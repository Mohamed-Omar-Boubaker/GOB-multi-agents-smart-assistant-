#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reset complet du système GOB Agent
    
.DESCRIPTION
    1. Supprime agent_memory.db (SQLite)
    2. Tue le serveur backend (pour vider la RAM)
    3. Redémarre le backend
    
.NOTES
    Le problème: LLMClient garde self.conversations{} en RAM
    Solution: Kill + Restart pour vider la mémoire
#>

param(
    [switch]$ConfirmAll
)

$ErrorActionPreference = "Stop"
$BaseDir = "C:\Users\lapte\OneDrive - ensi-uma.tn\Bureau\GOB agint\pcd-ai-embedded-agent"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           🔄 RESET COMPLET GOB AGENT                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Confirmation si pas de flag
if (-not $ConfirmAll) {
    Write-Host "⚠️  ATTENTION: Ceci va:" -ForegroundColor Yellow
    Write-Host "   1. Supprimer toute la mémoire (agent_memory.db)" -ForegroundColor Yellow
    Write-Host "   2. Tuer le serveur backend (vider RAM)" -ForegroundColor Yellow
    Write-Host "   3. Redémarrer le backend" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Continuer? (O/N)"
    if ($response -ne "O" -and $response -ne "o") {
        Write-Host "❌ Annulé" -ForegroundColor Red
        exit 0
    }
}

Write-Host ""
Write-Host "📍 Dossier de travail: $BaseDir" -ForegroundColor Gray
Write-Host ""

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1: Supprimer agent_memory.db
# ═══════════════════════════════════════════════════════════════
Write-Host "📂 ÉTAPE 1: Suppression de la base de données" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray

$DbPath = Join-Path $BaseDir "data\agent_memory.db"

if (Test-Path $DbPath) {
    try {
        Remove-Item $DbPath -Force
        Write-Host "   ✅ agent_memory.db supprimé" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Erreur lors de la suppression: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ℹ️  agent_memory.db n'existe pas (déjà vide)" -ForegroundColor Yellow
}

Write-Host ""

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2: Tuer le processus uvicorn
# ═══════════════════════════════════════════════════════════════
Write-Host "🔪 ÉTAPE 2: Arrêt du serveur backend" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray

$UvicornProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*backend.main:app*" }

if ($UvicornProcesses) {
    foreach ($proc in $UvicornProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force
            Write-Host "   ✅ Processus uvicorn (PID: $($proc.Id)) tué" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Impossible de tuer PID $($proc.Id): $_" -ForegroundColor Yellow
        }
    }
    
    # Attendre que les processus se terminent
    Start-Sleep -Seconds 2
} else {
    Write-Host "   ℹ️  Aucun processus uvicorn trouvé" -ForegroundColor Yellow
}

# Fallback: tuer tous les python uvicorn
$AllPythonUvicorn = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -match "uvicorn.*backend\.main" 
}

if ($AllPythonUvicorn) {
    Write-Host "   🔍 Processus Python uvicorn détectés, nettoyage..." -ForegroundColor Yellow
    $AllPythonUvicorn | ForEach-Object { 
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        Write-Host "   ✅ PID $($_.Id) tué" -ForegroundColor Green
    }
}

Write-Host ""

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3: Redémarrer le backend
# ═══════════════════════════════════════════════════════════════
Write-Host "🚀 ÉTAPE 3: Redémarrage du backend" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray

# Activer venv
$VenvActivate = Join-Path $BaseDir "venv\Scripts\Activate.ps1"

if (-not (Test-Path $VenvActivate)) {
    Write-Host "   ❌ venv non trouvé: $VenvActivate" -ForegroundColor Red
    exit 1
}

Write-Host "   🔧 Activation venv..." -ForegroundColor Gray
& $VenvActivate

Write-Host "   🌐 Lancement uvicorn sur port 8000..." -ForegroundColor Gray
Write-Host ""
Write-Host "   ➡️  Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "   ➡️  Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

# Changer de répertoire et lancer
Set-Location $BaseDir

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ RESET COMPLET TERMINÉ!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧠 Mémoire RAM vidée (conversations en mémoire supprimées)" -ForegroundColor Yellow
Write-Host "💾 Base de données supprimée" -ForegroundColor Yellow
Write-Host ""
Write-Host "Lancement du backend..." -ForegroundColor Cyan
Write-Host ""

# Lancer uvicorn (bloquant)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
