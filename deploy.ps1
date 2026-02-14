# deploy.ps1 - Full deploy Fantasy Dashboard
# Usage: .\deploy.ps1 patch|minor|major

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("patch", "minor", "major")]
    [string]$Type
)

$ErrorActionPreference = "Continue"
$VPS = "root@188.120.249.151"
$RemotePath = "/var/www/fantasy-telegram"

Write-Host ""
Write-Host "DEPLOY FANTASY DASHBOARD" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# 1. Bump version
Write-Host "1. Version bump ($Type)..." -ForegroundColor Yellow
& "$PSScriptRoot\bump-version.ps1" $Type
$versionJson = Get-Content "$PSScriptRoot\version.json" | ConvertFrom-Json
$version = $versionJson.version
Write-Host "   Version: v$version" -ForegroundColor Green

# 2. Git commit + tag
Write-Host ""
Write-Host "2. Git commit + tag..." -ForegroundColor Yellow
git add -A
$commitMsg = "v$version deploy"
git commit -m $commitMsg 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Commit: $commitMsg" -ForegroundColor Green
} else {
    Write-Host "   No changes to commit" -ForegroundColor Gray
}

$tagExists = git tag -l "v$version"
if (-not $tagExists) {
    git tag "v$version"
    Write-Host "   Tag: v$version" -ForegroundColor Green
} else {
    Write-Host "   Tag v$version exists" -ForegroundColor Gray
}

# 3. SCP files
Write-Host ""
Write-Host "3. Copy files to VPS..." -ForegroundColor Yellow
$files = @(
    "index.html",
    "server.py",
    "version.json",
    "static/js/app.js",
    "static/css/main.css"
)

foreach ($file in $files) {
    $localPath = Join-Path $PSScriptRoot $file
    if (Test-Path $localPath) {
        $remoteDest = "$RemotePath/$file"
        scp $localPath "${VPS}:$remoteDest" 2>$null
        Write-Host "   + $file" -ForegroundColor Green
    }
}

# 4. Restart service
Write-Host ""
Write-Host "4. Restart service..." -ForegroundColor Yellow
ssh $VPS "systemctl restart fantasy"
Start-Sleep -Seconds 2
$status = ssh $VPS "systemctl is-active fantasy"
if ($status -eq "active") {
    Write-Host "   Service: active" -ForegroundColor Green
} else {
    Write-Host "   Service: $status" -ForegroundColor Red
}

# 5. Diagnostics
Write-Host ""
Write-Host "5. Diagnostics..." -ForegroundColor Yellow
Write-Host ""

$passed = 0
$failed = 0
$warnings = 0
$results = @()

# Service check
$svcStatus = ssh $VPS "systemctl is-active fantasy"
if ($svcStatus -eq "active") {
    Write-Host "   [OK] Service" -ForegroundColor Green
    $passed++
} else {
    Write-Host "   [FAIL] Service: $svcStatus" -ForegroundColor Red
    $failed++
}

# API version
$apiVersion = ssh $VPS "curl -s http://localhost:8000/api/version"
if ($apiVersion -match "version") {
    Write-Host "   [OK] API version" -ForegroundColor Green
    $passed++
} else {
    Write-Host "   [FAIL] API version" -ForegroundColor Red
    $failed++
}

# Main page
$mainPage = ssh $VPS "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/"
if ($mainPage -eq "200") {
    Write-Host "   [OK] Main page" -ForegroundColor Green
    $passed++
} else {
    Write-Host "   [FAIL] Main page: $mainPage" -ForegroundColor Red
    $failed++
}

# CSS
$cssCheck = ssh $VPS "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/static/css/main.css"
if ($cssCheck -eq "200") {
    Write-Host "   [OK] CSS" -ForegroundColor Green
    $passed++
} else {
    Write-Host "   [FAIL] CSS: $cssCheck" -ForegroundColor Red
    $failed++
}

# JS
$jsCheck = ssh $VPS "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/static/js/app.js"
if ($jsCheck -eq "200") {
    Write-Host "   [OK] JS" -ForegroundColor Green
    $passed++
} else {
    Write-Host "   [FAIL] JS: $jsCheck" -ForegroundColor Red
    $failed++
}

# AI Status (optional)
$aiStatus = ssh $VPS "curl -s http://localhost:8000/api/ai/status"
if ($aiStatus -match '"online":true') {
    Write-Host "   [OK] AI Online" -ForegroundColor Green
} else {
    Write-Host "   [WARN] AI Offline" -ForegroundColor Yellow
    $warnings++
}

# PC Bridge (optional)
$pcStatus = ssh $VPS "curl -s http://localhost:8000/api/pc/status"
if ($pcStatus -match '"connected":true') {
    Write-Host "   [OK] PC Bridge" -ForegroundColor Green
} else {
    Write-Host "   [WARN] PC Bridge offline" -ForegroundColor Yellow
    $warnings++
}

# Summary
Write-Host ""
Write-Host "========================" -ForegroundColor Cyan
$total = $passed + $failed

if ($failed -eq 0) {
    Write-Host "DEPLOY OK: v$version" -ForegroundColor Green
    Write-Host "Checks: $passed/$total passed" -ForegroundColor Green
    if ($warnings -gt 0) {
        Write-Host "Warnings: $warnings" -ForegroundColor Yellow
    }
} else {
    Write-Host "DEPLOY PROBLEMS: v$version" -ForegroundColor Red
    Write-Host "Checks: $passed/$total passed" -ForegroundColor Red
    Write-Host "Failed: $failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Rollback: .\rollback.ps1 [version]" -ForegroundColor Yellow
}

Write-Host ""
