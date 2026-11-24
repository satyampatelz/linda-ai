# Linda v0.9 — creates the Desktop shortcut (Windows).
# Easiest way: double-click create-shortcut.bat (this script will
# run by itself). Or in PowerShell: .\create-shortcut.ps1
# A "Linda" icon will appear on the Desktop — click it and the chat opens.
#
# Optional auto-start (server starts when the laptop turns on):
#   .\create-shortcut.ps1 -AutoStart
# or: create-shortcut.bat -AutoStart
param(
    [switch]$AutoStart
)

$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $ProjectRoot "desktop\Linda.bat"
$Icon = Join-Path $ProjectRoot "desktop\linda.ico"

if (-not (Test-Path $Launcher)) {
    Write-Host "Linda.bat not found: $Launcher" -ForegroundColor Red
    Write-Host "This script should be in the linda-ai\desktop\ folder."
    Read-Host "Press Enter to close"
    exit 1
}

$Shell = New-Object -ComObject WScript.Shell
$ShortcutPath = Join-Path $Desktop "Linda.lnk"
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Linda — your personal AI agent"
$Shortcut.WindowStyle = 7  # minimized: no console flash when clicked
if (Test-Path $Icon) { $Shortcut.IconLocation = "$Icon,0" }
$Shortcut.Save()

Write-Host "Done — the 'Linda' icon is on your Desktop." -ForegroundColor Green

if ($AutoStart) {
    $Startup = Join-Path ([Environment]::GetFolderPath("Startup")) "Linda.lnk"
    Copy-Item $ShortcutPath $Startup -Force
    Write-Host "Auto-start is on too — the Linda server will start by itself when the laptop turns on." -ForegroundColor Green
}
Write-Host "Double-click the icon — the chat will open (the first time, the server takes 10-20 seconds to start)."
Read-Host "Press Enter to close"
