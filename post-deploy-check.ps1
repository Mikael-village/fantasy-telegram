# post-deploy-check.ps1 - Диагностика после деплоя
# Использование: .\post-deploy-check.ps1

$VPS = "root@188.120.249.151"
$ApiUrl = "http://localhost:8000"

Write-Host ""
Write-Host "📊 Диагностика Fantasy Dashboard" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Получаем результаты диагностики
$result = ssh $VPS "curl -s $ApiUrl/api/health/full" | ConvertFrom-Json

if (-not $result) {
    Write-Host "❌ Не удалось получить данные диагностики!" -ForegroundColor Red
    exit 1
}

# Версия
Write-Host "Версия: " -NoNewline
Write-Host "v$($result.version)" -ForegroundColor Yellow
Write-Host ""

# Проверки
Write-Host "Проверки:" -ForegroundColor White

foreach ($check in $result.checks.PSObject.Properties) {
    $name = $check.Name
    $data = $check.Value
    $status = $data.status
    
    $icon = switch ($status) {
        "ok" { "✅" }
        "warning" { "⚠️" }
        "error" { "❌" }
        default { "❓" }
    }
    
    $color = switch ($status) {
        "ok" { "Green" }
        "warning" { "Yellow" }
        "error" { "Red" }
        default { "White" }
    }
    
    $details = ""
    if ($data.message) { $details = " - $($data.message)" }
    elseif ($data.ms) { $details = " - $($data.ms)ms" }
    elseif ($data.connected -ne $null) { $details = " - $(if ($data.connected) {'connected'} else {'offline'})" }
    elseif ($data.online -ne $null) { $details = " - $(if ($data.online) {'online'} else {'offline'})" }
    
    Write-Host "  $icon " -NoNewline
    Write-Host "$name" -NoNewline -ForegroundColor $color
    Write-Host "$details"
}

Write-Host ""

# Итог
$summary = $result.summary
Write-Host "Итог: " -NoNewline
Write-Host "$($summary.passed) passed" -NoNewline -ForegroundColor Green
Write-Host ", " -NoNewline
Write-Host "$($summary.warnings) warnings" -NoNewline -ForegroundColor Yellow
Write-Host ", " -NoNewline
Write-Host "$($summary.failed) failed" -ForegroundColor Red

Write-Host ""

# Общий статус
$overall = $result.overall
$overallIcon = switch ($overall) {
    "ok" { "✅" }
    "warning" { "⚠️" }
    "error" { "❌" }
}
$overallColor = switch ($overall) {
    "ok" { "Green" }
    "warning" { "Yellow" }
    "error" { "Red" }
}

Write-Host "$overallIcon Общий статус: " -NoNewline
Write-Host $overall.ToUpper() -ForegroundColor $overallColor
Write-Host ""

# Возвращаем код ошибки если есть проблемы
if ($overall -eq "error") {
    Write-Host "⚠️ Обнаружены критические проблемы! Рекомендуется откат." -ForegroundColor Red
    exit 1
}
