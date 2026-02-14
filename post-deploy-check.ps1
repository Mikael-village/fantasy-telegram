# post-deploy-check.ps1 - Диагностика Fantasy Dashboard после деплоя
# Использование: .\post-deploy-check.ps1

$ErrorActionPreference = "Continue"
$baseUrl = "http://188.120.249.151:8000"
$passed = 0
$failed = 0
$results = @()

Write-Host ""
Write-Host "📊 Диагностика Fantasy Dashboard" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# 1. Проверка сервиса
Write-Host "1️⃣ Сервис fantasy..." -NoNewline
$serviceStatus = ssh root@188.120.249.151 "systemctl is-active fantasy" 2>$null
if ($serviceStatus -eq "active") {
    Write-Host " ✅ active" -ForegroundColor Green
    $passed++
    $results += "✅ Сервис: active"
} else {
    Write-Host " ❌ $serviceStatus" -ForegroundColor Red
    $failed++
    $results += "❌ Сервис: $serviceStatus"
}

# 2. Проверка API version
Write-Host "2️⃣ API /api/version..." -NoNewline
try {
    $version = Invoke-RestMethod -Uri "$baseUrl/api/version" -TimeoutSec 5
    Write-Host " ✅ v$($version.version)" -ForegroundColor Green
    $passed++
    $results += "✅ Версия: v$($version.version)"
} catch {
    Write-Host " ❌ недоступен" -ForegroundColor Red
    $failed++
    $results += "❌ API version: недоступен"
}

# 3. Проверка главной страницы
Write-Host "3️⃣ Главная страница..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/" -TimeoutSec 5
    if ($response.StatusCode -eq 200 -and $response.Content -match "Fantasy Dashboard") {
        Write-Host " ✅ OK" -ForegroundColor Green
        $passed++
        $results += "✅ Главная: OK"
    } else {
        Write-Host " ⚠️ загрузилась, но контент странный" -ForegroundColor Yellow
        $passed++
        $results += "⚠️ Главная: загрузилась с предупреждением"
    }
} catch {
    Write-Host " ❌ недоступна" -ForegroundColor Red
    $failed++
    $results += "❌ Главная: недоступна"
}

# 4. Проверка статики (CSS)
Write-Host "4️⃣ Статика CSS..." -NoNewline
try {
    $css = Invoke-WebRequest -Uri "$baseUrl/static/css/main.css" -TimeoutSec 5
    if ($css.StatusCode -eq 200) {
        Write-Host " ✅ OK" -ForegroundColor Green
        $passed++
        $results += "✅ CSS: OK"
    }
} catch {
    Write-Host " ❌ недоступен" -ForegroundColor Red
    $failed++
    $results += "❌ CSS: недоступен"
}

# 5. Проверка статики (JS)
Write-Host "5️⃣ Статика JS..." -NoNewline
try {
    $js = Invoke-WebRequest -Uri "$baseUrl/static/js/app.js" -TimeoutSec 5
    if ($js.StatusCode -eq 200) {
        Write-Host " ✅ OK" -ForegroundColor Green
        $passed++
        $results += "✅ JS: OK"
    }
} catch {
    Write-Host " ❌ недоступен" -ForegroundColor Red
    $failed++
    $results += "❌ JS: недоступен"
}

# 6. Проверка AI status
Write-Host "6️⃣ AI Status..." -NoNewline
try {
    $ai = Invoke-RestMethod -Uri "$baseUrl/api/ai/status" -TimeoutSec 5
    if ($ai.online -eq $true) {
        Write-Host " ✅ online" -ForegroundColor Green
        $passed++
        $results += "✅ AI: online"
    } else {
        Write-Host " ⚠️ offline (ожидаемо без ping)" -ForegroundColor Yellow
        $passed++
        $results += "⚠️ AI: offline"
    }
} catch {
    Write-Host " ⚠️ endpoint недоступен" -ForegroundColor Yellow
    $results += "⚠️ AI status: endpoint недоступен"
}

# 7. Проверка PC Bridge
Write-Host "7️⃣ PC Bridge..." -NoNewline
try {
    $pc = Invoke-RestMethod -Uri "$baseUrl/api/pc/status" -TimeoutSec 5
    if ($pc.connected -eq $true) {
        Write-Host " ✅ connected" -ForegroundColor Green
        $passed++
        $results += "✅ PC Bridge: connected"
    } else {
        Write-Host " ⚠️ offline (ожидаемо если ПК выключен)" -ForegroundColor Yellow
        $results += "⚠️ PC Bridge: offline"
    }
} catch {
    Write-Host " ⚠️ недоступен" -ForegroundColor Yellow
    $results += "⚠️ PC Bridge: недоступен"
}

# Итог
Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
$total = $passed + $failed
Write-Host "Результат: $passed/$total проверок пройдено" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Yellow" })

if ($failed -gt 0) {
    Write-Host ""
    Write-Host "⚠️ Есть проблемы! Рекомендуется откат:" -ForegroundColor Red
    Write-Host "   .\rollback.ps1 [предыдущая версия]" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host ""
    Write-Host "✅ Все критические проверки пройдены!" -ForegroundColor Green
    exit 0
}
