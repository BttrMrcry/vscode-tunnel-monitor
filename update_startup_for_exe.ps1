# Update startup shortcut to use the standalone .exe
$WshShell = New-Object -ComObject WScript.Shell
$StartupPath = [System.Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupPath "Tunnel Monitor.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $PSScriptRoot "dist\TunnelMonitor.exe"
$Shortcut.WorkingDirectory = Join-Path $PSScriptRoot "dist"
$Shortcut.Description = "VS Code Tunnel Monitor"
$Shortcut.Save()

Write-Host "Startup shortcut updated to use TunnelMonitor.exe" -ForegroundColor Green
Write-Host "Location: $ShortcutPath" -ForegroundColor Cyan
