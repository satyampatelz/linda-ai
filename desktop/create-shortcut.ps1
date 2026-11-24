# Linda v0.9 — Desktop shortcut banata hai (Windows).
# Aasan tareeqa: create-shortcut.bat pe double-click karo (ye script
# khud chal jayegi). Ya PowerShell me: .\create-shortcut.ps1
# Desktop pe "Linda" icon ban jayega — click karte hi chat khul jayega.
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
$Launcher = Join-Path $ProjectRoot "desktop\Linda.bat"
$Icon = Join-Path $ProjectRoot "desktop\linda.ico"

if (-not (Test-Path $Launcher)) {
    Write-Host "Linda.bat nahi mila: $Launcher" -ForegroundColor Red
    Write-Host "Ye script linda-ai\desktop\ folder me honi chahiye."
    Read-Host "Band karne ke liye Enter dabao"
    exit 1
}

$Shell = New-Object -ComObject WScript.Shell
$ShortcutPath = Join-Path $Desktop "Linda.lnk"
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Linda — your personal AI agent"
$Shortcut.WindowStyle = 7  # minimized: click karne pe console flash nahi hoga
if (Test-Path $Icon) { $Shortcut.IconLocation = "$Icon,0" }
$Shortcut.Save()

Write-Host "Ho gaya — Desktop pe 'Linda' icon ban gaya." -ForegroundColor Green

if ($AutoStart) {
    $Startup = Join-Path ([Environment]::GetFolderPath("Startup")) "Linda.lnk"
    Copy-Item $ShortcutPath $Startup -Force
    Write-Host "Auto-start bhi on hai — laptop on hote hi Linda server khud chalega." -ForegroundColor Green
}
Write-Host "Icon pe double-click karo — chat khul jayega (pehli baar server start hone me 10-20 second lagenge)."
Read-Host "Band karne ke liye Enter dabao"
