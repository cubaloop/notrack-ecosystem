$ErrorActionPreference = "Continue"
Set-Location "C:\Users\Yo\notrack-ecosystem"

Write-Host "Inicializando Ecosistema NoTrack..."
$p1 = Start-Process -FilePath "python" -ArgumentList "-u", "scripts/orchestrator.py" -WorkingDirectory "C:\Users\Yo\notrack-ecosystem" -RedirectStandardOutput "C:\Users\Yo\notrack-ecosystem\logs\orchestrator.log" -RedirectStandardError "C:\Users\Yo\notrack-ecosystem\logs\orchestrator_err.log" -WindowStyle Hidden -PassThru
$p2 = Start-Process -FilePath "python" -ArgumentList "-u", "scripts/web_interface.py" -WorkingDirectory "C:\Users\Yo\notrack-ecosystem" -RedirectStandardOutput "C:\Users\Yo\notrack-ecosystem\logs\web.log" -RedirectStandardError "C:\Users\Yo\notrack-ecosystem\logs\web_err.log" -WindowStyle Hidden -PassThru
$p3 = Start-Process -FilePath "python" -ArgumentList "-u", "scripts/github_bridge_daemon.py" -WorkingDirectory "C:\Users\Yo\notrack-ecosystem" -RedirectStandardOutput "C:\Users\Yo\notrack-ecosystem\logs\github_bridge.log" -RedirectStandardError "C:\Users\Yo\notrack-ecosystem\logs\github_bridge_err.log" -WindowStyle Hidden -PassThru

Write-Host "[System] Orchestrator PID: $($p1.Id)"
Write-Host "[System] Web Interface PID: $($p2.Id)"
Write-Host "[System] GitHub Bridge Daemon PID: $($p3.Id)"
Write-Host "Ecosistema activo en http://127.0.0.1:5000"

while ($true) {
    Start-Sleep -Seconds 10
    if ($p1.HasExited) {
        $p1 = Start-Process -FilePath "python" -ArgumentList "-u", "scripts/orchestrator.py" -WorkingDirectory "C:\Users\Yo\notrack-ecosystem" -RedirectStandardOutput "C:\Users\Yo\notrack-ecosystem\logs\orchestrator.log" -RedirectStandardError "C:\Users\Yo\notrack-ecosystem\logs\orchestrator_err.log" -WindowStyle Hidden -PassThru
    }
    if ($p2.HasExited) {
        $p2 = Start-Process -FilePath "python" -ArgumentList "-u", "scripts/web_interface.py" -WorkingDirectory "C:\Users\Yo\notrack-ecosystem" -RedirectStandardOutput "C:\Users\Yo\notrack-ecosystem\logs\web.log" -RedirectStandardError "C:\Users\Yo\notrack-ecosystem\logs\web_err.log" -WindowStyle Hidden -PassThru
    }
    if ($p3.HasExited) {
        $p3 = Start-Process -FilePath "python" -ArgumentList "-u", "scripts/github_bridge_daemon.py" -WorkingDirectory "C:\Users\Yo\notrack-ecosystem" -RedirectStandardOutput "C:\Users\Yo\notrack-ecosystem\logs\github_bridge.log" -RedirectStandardError "C:\Users\Yo\notrack-ecosystem\logs\github_bridge_err.log" -WindowStyle Hidden -PassThru
    }
}
