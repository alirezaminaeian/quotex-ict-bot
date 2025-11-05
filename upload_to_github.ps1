# اسکریپت آپلود خودکار به GitHub

Write-Host "🚀 شروع آپلود به GitHub..." -ForegroundColor Green

# چک کردن Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git نصب نیست!" -ForegroundColor Red
    Write-Host "لطفاً Git را نصب کن: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "بعد از نصب، PowerShell را restart کن و دوباره این اسکریپت را اجرا کن." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Git پیدا شد" -ForegroundColor Green

# گرفتن اطلاعات GitHub
$repoUrl = Read-Host "آدرس GitHub repository را وارد کن (مثلاً: https://github.com/USERNAME/quotex-ict-bot.git)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "❌ آدرس repository خالی است!" -ForegroundColor Red
    exit 1
}

# فایل‌های لازم برای commit
$filesToAdd = @(
    "main.py",
    "login_helper.py",
    "convert_session.py",
    "test_telegram.py",
    "requirements.txt",
    "env.example",
    ".gitignore",
    "README.md",
    "setup_guide.md",
    "SERVER_SETUP.md",
    "GITHUB_SETUP.md",
    "install_server.sh",
    "setup_systemd.sh",
    "install_server.ps1",
    "upload_to_github.ps1"
)

Write-Host ""
Write-Host "📦 آماده‌سازی repository..." -ForegroundColor Yellow

# Initialize git (اگر نیست)
if (-not (Test-Path ".git")) {
    git init
    Write-Host "✅ Repository محلی ساخته شد" -ForegroundColor Green
}

# اضافه کردن remote
git remote remove origin 2>$null
git remote add origin $repoUrl
Write-Host "✅ Remote اضافه شد" -ForegroundColor Green

# اضافه کردن فایل‌ها
Write-Host ""
Write-Host "📁 اضافه کردن فایل‌ها..." -ForegroundColor Yellow
foreach ($file in $filesToAdd) {
    if (Test-Path $file) {
        git add $file
        Write-Host "  ✅ $file" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  $file پیدا نشد" -ForegroundColor Yellow
    }
}

# Commit
Write-Host ""
Write-Host "💾 Commit کردن..." -ForegroundColor Yellow
git commit -m "Initial commit: Quotex ICT Bot - Complete setup with all necessary files" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Commit موفق بود" -ForegroundColor Green
} else {
    Write-Host "⚠️  Commit انجام نشد (ممکن است فایل‌ها قبلاً commit شده باشند)" -ForegroundColor Yellow
}

# Push
Write-Host ""
Write-Host "⬆️  Push به GitHub..." -ForegroundColor Yellow
Write-Host "⚠️  اگر Authentication خواست:" -ForegroundColor Yellow
Write-Host "   - Username: GitHub username خودت" -ForegroundColor Cyan
Write-Host "   - Password: Personal Access Token (نه رمز GitHub)" -ForegroundColor Cyan
Write-Host ""

git branch -M main 2>&1 | Out-Null
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ آپلود با موفقیت انجام شد!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Repository: $repoUrl" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Push ناموفق بود!" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 راه حل:" -ForegroundColor Yellow
    Write-Host "1. Personal Access Token بساز: GitHub → Settings → Developer settings → Personal access tokens" -ForegroundColor Cyan
    Write-Host "2. یا دستی push کن: git push -u origin main" -ForegroundColor Cyan
}

