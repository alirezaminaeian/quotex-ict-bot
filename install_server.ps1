# اسکریپت نصب خودکار برای سرور ویندوز

Write-Host "🚀 شروع نصب ربات Quotex ICT Bot..." -ForegroundColor Green

# چک کردن Python
Write-Host "🐍 چک کردن Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python نصب نیست. لطفاً Python 3.12 را نصب کن." -ForegroundColor Red
    exit 1
}

# چک کردن Chrome
Write-Host "🌐 چک کردن Google Chrome..." -ForegroundColor Yellow
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chromePath)) {
    Write-Host "⚠️  Google Chrome پیدا نشد. لطفاً Chrome را نصب کن." -ForegroundColor Yellow
}

# ساخت virtual environment (اختیاری)
Write-Host "📦 ساخت virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
}

# نصب کتابخانه‌ها
Write-Host "📚 نصب کتابخانه‌های Python..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "✅ نصب با موفقیت انجام شد!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 مراحل بعدی:" -ForegroundColor Cyan
Write-Host "1. فایل .env را با مقادیر واقعی پر کن"
Write-Host "2. فایل session/quotex_session.pkl را بذار"
Write-Host "3. برای اجرا: python main.py"
Write-Host "4. یا با Task Scheduler اجرا کن (راهنما: SERVER_SETUP.md)"

