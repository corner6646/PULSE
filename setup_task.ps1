$taskName = "PULSE_Daily"
$batchPath = "$PSScriptRoot\run.bat"

schtasks /delete /tn $taskName /f 2>$null
schtasks /delete /tn ($taskName + "_Logon") /f 2>$null

schtasks /create /tn $taskName /tr $batchPath /sc daily /st 09:00 /rl limited /f

schtasks /create /tn ($taskName + "_Logon") /tr $batchPath /sc onlogon /rl limited /f

Write-Host "SUCCESS - PULSE scheduled tasks registered" -ForegroundColor Green
Write-Host "  PULSE_Daily       : every day at 09:00" -ForegroundColor Cyan
Write-Host "  PULSE_Daily_Logon : on login (catch-up)" -ForegroundColor Cyan
Write-Host "To remove:" -ForegroundColor Yellow
Write-Host "  schtasks /delete /tn PULSE_Daily /f" -ForegroundColor Yellow
Write-Host "  schtasks /delete /tn PULSE_Daily_Logon /f" -ForegroundColor Yellow
