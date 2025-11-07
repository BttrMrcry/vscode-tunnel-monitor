# Create startup shortcut for Tunnel Monitor
$WshShell = New-Object -ComObject WScript.Shell
$StartupPath = [System.Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupPath "Tunnel Monitor.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $PSScriptRoot "start_tunnel_monitor.bat"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "VS Code Tunnel Monitor"
$Shortcut.Save()

Write-Host "Startup shortcut created at: $ShortcutPath" -ForegroundColor Green
