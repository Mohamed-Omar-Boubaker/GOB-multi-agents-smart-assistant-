# create_shortcut.ps1
# Run this ONCE to create a clickable desktop icon for GOB Edge AI.
# Usage: Right-click this file → "Run with PowerShell"

param(
    [string]$ProjectRoot = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [string]$LauncherScript = ""
)

# Auto-detect launcher path
if (-not $LauncherScript) {
    $LauncherScript = Join-Path $ProjectRoot "start_project.bat"
}

if (-not (Test-Path $LauncherScript)) {
    Write-Host "[ERROR] Launcher not found at: $LauncherScript" -ForegroundColor Red
    Write-Host "        Make sure start_project.bat is in the project root." -ForegroundColor Yellow
    pause
    exit 1
}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "GOB Edge AI.lnk"

# Check for logo icon (optional)
$IconPath = Join-Path $ProjectRoot "logoapp.png"
# Windows shortcuts need .ico — we'll use cmd.exe icon as fallback
$ShellIconPath = "%SystemRoot%\system32\cmd.exe"

try {
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $LauncherScript
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.WindowStyle = 1   # Normal window
    $Shortcut.Description = "Start GOB Edge AI (Backend + Frontend)"
    $Shortcut.IconLocation = "$ShellIconPath,0"
    $Shortcut.Save()

    Write-Host "" 
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host "  Desktop shortcut created!" -ForegroundColor Green
    Write-Host "  Location: $ShortcutPath" -ForegroundColor Cyan
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Double-click 'GOB Edge AI' on your desktop to launch the project." -ForegroundColor Yellow
    Write-Host ""
}
catch {
    Write-Host "[ERROR] Failed to create shortcut: $_" -ForegroundColor Red
}

# Tip: to use the actual app logo as icon, convert logoapp.png to .ico first:
# Install ImageMagick then run:
#   magick convert logoapp.png -resize 256x256 gob_icon.ico
# Then set $Shortcut.IconLocation = (Join-Path $ProjectRoot "gob_icon.ico") + ",0"

pause
