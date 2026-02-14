# rollback.ps1 - Откат Fantasy Dashboard на указанную версию
# Использование: .\rollback.ps1 v1.0.0

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

Write-Host "🔄 Откат на версию: $Version" -ForegroundColor Yellow

# Проверяем что тег существует
$tagExists = git tag -l $Version
if (-not $tagExists) {
    Write-Host "❌ Версия $Version не найдена!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Доступные версии:" -ForegroundColor Cyan
    git tag -l "v*" | Sort-Object -Descending | Select-Object -First 10
    exit 1
}

# Откат локально
Write-Host "📦 Откат локального кода..." -ForegroundColor Cyan
git checkout $Version -- .

# Деплой на VPS
Write-Host "🚀 Деплой на VPS..." -ForegroundColor Cyan
scp static/js/app.js root@188.120.249.151:/var/www/fantasy-telegram/static/js/app.js
scp static/css/main.css root@188.120.249.151:/var/www/fantasy-telegram/static/css/main.css
scp index.html root@188.120.249.151:/var/www/fantasy-telegram/index.html
scp server.py root@188.120.249.151:/var/www/fantasy-telegram/server.py
scp version.json root@188.120.249.151:/var/www/fantasy-telegram/version.json

# Перезапуск сервиса
Write-Host "🔄 Перезапуск сервиса..." -ForegroundColor Cyan
ssh root@188.120.249.151 "systemctl restart fantasy"

# Проверка
Write-Host "✅ Проверка..." -ForegroundColor Cyan
$status = ssh root@188.120.249.151 "systemctl is-active fantasy"
if ($status -eq "active") {
    Write-Host ""
    Write-Host "✅ Откат на $Version выполнен успешно!" -ForegroundColor Green
} else {
    Write-Host "❌ Сервис не запустился!" -ForegroundColor Red
    exit 1
}
