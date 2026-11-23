# Satyam v0.9 — Desktop shortcut banata hai (Windows).
# Aasan tareeqa: create-shortcut.bat pe double-click karo (ye script
# khud chal jayegi). Ya PowerShell me: .\create-shortcut.ps1
# Desktop pe "Satyam" icon ban jayega — click karte hi chat khul jayega.
#
# Optional auto-start (laptop on hote hi server bhi start ho):
#   .\create-shortcut.ps1 -AutoStart
# ya: create-shortcut.bat -AutoStart
param(
    [switch]$AutoStart
)

$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $ProjectRoot "desktop\Satyam.bat"
$Icon = Join-Path $ProjectRoot "desktop\satyam.ico"

if (-not (Test-Path $Launcher)) {
    Write-Host "Satyam.bat nahi mila: $Launcher" -ForegroundColor Red
    Write-Host "Ye script satyam-ai\desktop\ folder me honi chahiye."
    Read-Host "Band karne ke liye Enter dabao"
    exit 1
}

$Shell = New-Object -ComObject WScript.Shell
$ShortcutPath = Join-Path $Desktop "Satyam.lnk"
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Satyam — your personal AI agent"
$Shortcut.WindowStyle = 7  # minimized: click karne pe console flash nahi hoga
if (Test-Path $Icon) { $Shortcut.IconLocation = "$Icon,0" }
$Shortcut.Save()

Write-Host "Ho gaya — Desktop pe 'Satyam' icon ban gaya." -ForegroundColor Green

if ($AutoStart) {
    $Startup = Join-Path ([Environment]::GetFolderPath("Startup")) "Satyam.lnk"
    Copy-Item $ShortcutPath $Startup -Force
    Write-Host "Auto-start bhi on hai — laptop on hote hi Satyam server khud chalega." -ForegroundColor Green
}
Write-Host "Icon pe double-click karo — chat khul jayega (pehli baar server start hone me 10-20 second lagenge)."
Read-Host "Band karne ke liye Enter dabao"
