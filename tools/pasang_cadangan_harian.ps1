$ErrorActionPreference = "Stop"

$akar = Split-Path -Parent $PSScriptRoot
$bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
if (-not (Test-Path $bash)) { throw "Git Bash tidak ditemukan di $bash" }

$aksi = New-ScheduledTaskAction `
    -Execute "$env:WINDIR\System32\conhost.exe" `
    -Argument "--headless `"$bash`" tools/cadangan_harian.sh" `
    -WorkingDirectory $akar
$pemicu = New-ScheduledTaskTrigger -Daily -At "21:00"
$setelan = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew
$pelaku = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName "hendrokuswantoro cadangan harian" `
    -Description "Cadangan basis data dan unggahan dashboard, terenkripsi. Catatan di cadangan\harian.log." `
    -Action $aksi -Trigger $pemicu -Settings $setelan -Principal $pelaku -Force | Out-Null

Write-Output "terpasang: tiap hari pukul 21.00, atau sesegera mungkin kalau laptop mati pada jam itu"
