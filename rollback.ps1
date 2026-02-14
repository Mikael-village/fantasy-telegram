# rollback.ps1 - Откат Fantasy Dashboard на указанную версию
# Использование: .\rollback.ps1 1.0.0

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$VPS = "root@188.120.249.151"
$RemotePath = "/var/www/fantasy-telegram"

Write-Host ""
Write-Host "🔄 Откат Fantasy Dashboard на версию v$Version" -ForegroundColor Yellow
Write-Host ""

# Проверяем что тег существует
Write-Host "Проверяю наличие тега v$Version..." -ForegroundColor Cyan
$tagCheck = git tag -l "v$Version" 2>&1
if (-not $tagCheck) {
    Write-Host "❌ Тег v$Version не найден!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Доступные версии:" -ForegroundColor Yellow
    git tag -l "v*" | ForEach-Object { Write-Host "  $_" }
    exit 1
}

Write-Host "✅ Тег найден" -ForegroundColor Green

# Создаём бэкап текущей версии на VPS
Write-Host ""
Write-Host "Создаю бэкап текущей версии на VPS..." -ForegroundColor Cyan
ssh $VPS "cd $RemotePath && git stash"

# Откатываем на VPS
Write-Host "Откатываю на v$Version..." -ForegroundColor Cyan
$result = ssh $VPS "cd $RemotePath && git fetch --tags && git checkout v$Version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при откате!" -ForegroundColor Red
    exit 1
}

# Перезапускаем сервис
Write-Host "Перезапускаю сервис..." -ForegroundColor Cyan
ssh $VPS "systemctl restart fantasy"

# Проверяем
Write-Host ""
Write-Host "Проверяю статус..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$health = ssh $VPS "curl -s http://localhost:8000/api/version"
Write-Host ""
Write-Host "✅ Откат завершён!" -ForegroundColor Green
Write-Host "Текущая версия на сервере: $health" -ForegroundColor Cyan
Write-Host ""
