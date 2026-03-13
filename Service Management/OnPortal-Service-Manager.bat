<# : Batch Wrapper
@echo off
title OnPortal Service Manager

:: --- ADMIN ELEVATION ---
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo [!] Requesting Admin Permissions...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B
)
if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
cd /d "%~dp0"

:: --- EXECUTE POWERSHELL ---
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression (Get-Content '%~f0' -Encoding UTF8 -Raw)"
exit /B
#>

# ==============================================================================
# --- POWERSHELL SCRIPT STARTS HERE ---
# ==============================================================================

function Restart-OnityService {
    param (
        [string]$ServiceName,
        [string]$DisplayName
    )
    
    Write-Host "`n  [*] Checking $DisplayName ($ServiceName)..." -ForegroundColor Cyan
    
    if (-not (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue)) {
        Write-Host "  [!] Skipped: '$ServiceName' is not installed on this machine." -ForegroundColor DarkGray
        return
    }

    Write-Host "  [*] Stopping $ServiceName..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force
    Start-Sleep -Seconds 2

    Write-Host "  [*] Starting $ServiceName..." -ForegroundColor Yellow
    Start-Service -Name $ServiceName
    Start-Sleep -Seconds 1

    Write-Host "  [+] $DisplayName restarted successfully!" -ForegroundColor Green
}

# Main Menu Loop
do {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                ONPORTAL SERVICE MANAGER                ║" -ForegroundColor White -BackgroundColor DarkCyan
    Write-Host "  ╠════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "  ║                                                        ║" -ForegroundColor Cyan
    Write-Host "  ║  Select a service to restart:                          ║" -ForegroundColor White
    Write-Host "  ║                                                        ║" -ForegroundColor Cyan
    Write-Host "  ║  [1] OnPortal Node Service                             ║" -ForegroundColor Yellow
    Write-Host "  ║      (Standard OnPortal PMS communication)             ║" -ForegroundColor DarkGray
    Write-Host "  ║                                                        ║" -ForegroundColor Cyan
    Write-Host "  ║  [2] OnPortal IoT Service                              ║" -ForegroundColor Yellow
    Write-Host "  ║      (Only used if property has EMS like InnComm)      ║" -ForegroundColor DarkGray
    Write-Host "  ║                                                        ║" -ForegroundColor Cyan
    Write-Host "  ║  [3] Restart Both Services                             ║" -ForegroundColor Green
    Write-Host "  ║                                                        ║" -ForegroundColor Cyan
    Write-Host "  ║  [Q] Quit                                              ║" -ForegroundColor Red
    Write-Host "  ║                                                        ║" -ForegroundColor Cyan
    Write-Host "  ╠════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "  ║  Special thanks to Kernwuzhere1979 for assisting! :)   ║" -ForegroundColor Gray
    Write-Host "  ╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    $choice = Read-Host "  Enter your choice (1/2/3/Q)"

    switch ($choice) {
        '1' { Restart-OnityService -ServiceName "OnPortalNodeService" -DisplayName "OnPortal Node Service" }
        '2' { Restart-OnityService -ServiceName "OnPortalIoTService" -DisplayName "OnPortal IoT Service" }
        '3' { 
            Restart-OnityService -ServiceName "OnPortalNodeService" -DisplayName "OnPortal Node Service"
            Restart-OnityService -ServiceName "OnPortalIoTService" -DisplayName "OnPortal IoT Service"
        }
        'Q' { exit }
        'q' { exit }
        default { Write-Host "  Invalid selection, please try again." -ForegroundColor Red }
    }
    
    Write-Host "`n  --------------------------------------------------------" -ForegroundColor Cyan
    $pause = Read-Host "  Press Enter to return to menu or type 'Q' to quit"
    if ($pause -eq 'q' -or $pause -eq 'Q') { exit }

} while ($true)