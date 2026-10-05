<#
.SYNOPSIS
Запускает локальный стенд документации и управляет его сервисом Docker Compose.
.EXAMPLE
.\start.ps1
.EXAMPLE
.\start.ps1 -Action Logs
.EXAMPLE
.\start.ps1 -Action Stop
#>
[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop', 'Restart', 'Logs', 'Status')]
    [string]$Action = 'Start'
)

$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    switch ($Action) {
        'Start'   { & docker compose up --build -d infohelp_egisz }
        'Stop'    { & docker compose stop infohelp_egisz }
        'Restart' { & docker compose restart infohelp_egisz }
        'Logs'    { & docker compose logs --tail 100 -f infohelp_egisz }
        'Status'  { & docker compose ps infohelp_egisz }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose завершился с кодом $LASTEXITCODE."
    }
    if ($Action -in @('Start', 'Restart')) {
        Write-Host 'Стенд запускается: http://localhost:3006/. Дождитесь Compiled successfully в журнале: .\start.ps1 -Action Logs'
    }
}
finally {
    Pop-Location
}
