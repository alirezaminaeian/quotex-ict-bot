#!/bin/bash
# اسکریپت نصب خودکار برای سرور لینوکس

set -e

echo "🚀 شروع نصب ربات Quotex ICT Bot..."

# آپدیت سیستم
echo "📦 آپدیت سیستم..."
sudo apt update && sudo apt upgrade -y

# نصب Python 3.12
echo "🐍 نصب Python..."
sudo apt install python3.12 python3.12-venv python3-pip -y

# نصب Google Chrome
echo "🌐 نصب Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt install ./google-chrome-stable_current_amd64.deb -y
    rm google-chrome-stable_current_amd64.deb
fi

# نصب وابستگی‌های Chrome
echo "📚 نصب وابستگی‌های Chrome..."
sudo apt install -y libxss1 libappindicator1 libindicator7 libgconf-2-4 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 libcairo-gobject2 libgtk-3-0 libgdk-pixbuf2.0-0

# ساخت virtual environment
echo "📦 ساخت virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# نصب کتابخانه‌ها
echo "📚 نصب کتابخانه‌های Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ نصب با موفقیت انجام شد!"
echo ""
echo "📝 مراحل بعدی:"
echo "1. فایل .env را با مقادیر واقعی پر کن"
echo "2. فایل session/quotex_session.pkl را بذار"
echo "3. برای اجرا با systemd: sudo bash setup_systemd.sh"
echo "4. یا برای اجرا با screen: screen -S quotex_bot && source venv/bin/activate && python main.py"

