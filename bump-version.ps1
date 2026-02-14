# bump-version.ps1 - Обновление версии Fantasy Dashboard
# Использование: .\bump-version.ps1 patch|minor|major

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("patch", "minor", "major")]
    [string]$Type
)

$versionFile = Join-Path $PSScriptRoot "version.json"

if (-not (Test-Path $versionFile)) {
    Write-Host "❌ version.json не найден" -ForegroundColor Red
    exit 1
}

$json = Get-Content $versionFile -Raw | ConvertFrom-Json
$currentVersion = $json.version
$parts = $currentVersion.Split('.')

$major = [int]$parts[0]
$minor = [int]$parts[1]
$patch = [int]$parts[2]

switch ($Type) {
    "patch" { $patch++ }
    "minor" { $minor++; $patch = 0 }
    "major" { $major++; $minor = 0; $patch = 0 }
}

$newVersion = "$major.$minor.$patch"
$json.version = $newVersion
$json | Add-Member -NotePropertyName "lastUpdate" -NotePropertyValue (Get-Date -Format "yyyy-MM-ddTHH:mm:ss") -Force

# Сохраняем без BOM (UTF8NoBOM)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($versionFile, ($json | ConvertTo-Json -Depth 10), $utf8NoBom)

Write-Host ""
Write-Host "✅ Версия обновлена: " -NoNewline
Write-Host "v$currentVersion" -ForegroundColor Yellow -NoNewline
Write-Host " → " -NoNewline
Write-Host "v$newVersion" -ForegroundColor Green
Write-Host ""
Write-Host "Тип изменения: $Type" -ForegroundColor Cyan
Write-Host ""
