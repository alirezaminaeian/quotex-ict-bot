# راهنمای کامل نصب و اجرای ربات روی سرور (VPS)

این راهنما برای اجرای ربات روی سرور ویندوز یا لینوکس (مثل Oracle Cloud، AWS، DigitalOcean) است.

---

## گزینه 1: سرور ویندوز

### مرحله 1: آماده‌سازی سرور

1. **نصب Python 3.12:**
   - دانلود: https://www.python.org/downloads/
   - موقع نصب تیک "Add Python to PATH" را بزن
   - تیک "Install for all users" را بزن

2. **نصب Google Chrome:**
   - دانلود: https://www.google.com/chrome/
   - نصب کن

3. **انتقال فایل‌های پروژه:**
   - پوشه `quotex_ict_bot` را به سرور ببر (مثلاً `C:\quotex_bot\`)
   - فایل `.env` را با مقادیر واقعی پر کن
   - فایل `session/quotex_session.pkl` را هم ببر (اگر از قبل ساخته شده)

### مرحله 2: نصب کتابخانه‌ها

```powershell
cd C:\quotex_bot\quotex_ict_bot
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### مرحله 3: اجرای خودکار با Windows Task Scheduler

1. **ساخت Task جدید:**
   - Task Scheduler را باز کن
   - Create Basic Task → نام: "Quotex ICT Bot" → Next
   - Trigger: Daily → Next
   - Start time: هر ساعت (مثلاً 00:00) → Next
   - Action: Start a program → Next
   - Program: `C:\Python312\python.exe` (یا مسیر Python)
   - Arguments: `C:\quotex_bot\quotex_ict_bot\main.py`
   - Start in: `C:\quotex_bot\quotex_ict_bot`
   - Finish

2. **تنظیمات پیشرفته:**
   - Right-click روی Task → Properties
   - General tab: تیک "Run whether user is logged on or not"
   - Actions tab: مطمئن شو مسیر درست است
   - Conditions tab: تیک "Wake the computer to run this task" را بردار
   - Settings tab: تیک "Run task as soon as possible after a scheduled start is missed"

3. **اجرای دستی (برای تست):**
   - Right-click روی Task → Run
   - برای چک کردن لاگ: `C:\quotex_bot\quotex_ict_bot\logs\signals.log`

---

## گزینه 2: سرور لینوکس (Ubuntu/Debian)

### مرحله 1: آماده‌سازی سرور

```bash
# آپدیت سیستم
sudo apt update && sudo apt upgrade -y

# نصب Python 3.12
sudo apt install python3.12 python3.12-venv python3-pip -y

# نصب Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb -y

# نصب وابستگی‌های Selenium
sudo apt install -y chromium-chromedriver || sudo apt install -y chromium-driver
```

### مرحله 2: انتقال فایل‌ها

```bash
# ساخت پوشه پروژه
mkdir -p ~/quotex_bot
cd ~/quotex_bot

# انتقال فایل‌ها (از طریق FTP/SFTP یا git clone)
# یا از طریق FileZilla/SCP تمام پوشه quotex_ict_bot را ببر
```

### مرحله 3: نصب کتابخانه‌ها

```bash
cd ~/quotex_bot/quotex_ict_bot
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### مرحله 4: اجرای خودکار با systemd (بهترین روش)

1. **ساخت سرویس systemd:**

```bash
sudo nano /etc/systemd/system/quotex-ict-bot.service
```

2. **محتوای فایل:**

```ini
[Unit]
Description=Quotex ICT Signal Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/quotex_bot/quotex_ict_bot
Environment="PATH=/home/YOUR_USERNAME/quotex_bot/quotex_ict_bot/venv/bin"
ExecStart=/home/YOUR_USERNAME/quotex_bot/quotex_ict_bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/YOUR_USERNAME/quotex_bot/quotex_ict_bot/logs/bot.log
StandardError=append:/home/YOUR_USERNAME/quotex_bot/quotex_ict_bot/logs/bot_error.log

[Install]
WantedBy=multi-user.target
```

3. **جایگزینی مسیرها:**
   - `YOUR_USERNAME` را با نام کاربری خودت عوض کن
   - اگر مسیر متفاوته، اون رو هم عوض کن

4. **فعال‌سازی و اجرای سرویس:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# فعال‌سازی (اجرا بعد از ری‌استارت)
sudo systemctl enable quotex-ict-bot.service

# شروع سرویس
sudo systemctl start quotex-ict-bot.service

# چک کردن وضعیت
sudo systemctl status quotex-ict-bot.service

# دیدن لاگ‌های زنده
sudo journalctl -u quotex-ict-bot.service -f
```

### گزینه جایگزین: اجرا با screen یا tmux

```bash
# نصب screen
sudo apt install screen -y

# اجرا در screen
screen -S quotex_bot
cd ~/quotex_bot/quotex_ict_bot
source venv/bin/activate
python main.py

# جدا شدن از screen: Ctrl+A سپس D
# برگشت به screen: screen -r quotex_bot
# لیست session‌ها: screen -ls
```

---

## تنظیمات مهم برای سرور

### 1) تنظیم فایل `.env`:

```bash
QUOTEX_EMAIL=your_email@gmail.com
QUOTEX_PASSWORD=your_password
TELEGRAM_TOKEN=12345:ABCDEF
TELEGRAM_CHAT_ID=123456789
HEADLESS=true
```

**نکته:** روی سرور `HEADLESS=true` بذار تا مرورگر در پس‌زمینه اجرا بشه.

### 2) اطمینان از وجود سشن:

- فایل `session/quotex_session.pkl` باید موجود باشه
- اگر نیست، از روش قبلی (Console مرورگر) سشن بگیر و بذار

### 3) فایروال و اتصال:

- مطمئن شو سرور به اینترنت وصل هست
- اگر فایروال فعاله، پورت‌های لازم رو باز کن

---

## مدیریت و مانیتورینگ

### چک کردن لاگ‌ها:

**Windows:**
```powershell
# لاگ سیگنال‌ها
Get-Content C:\quotex_bot\quotex_ict_bot\logs\signals.log -Tail 50

# لاگ خطاها (اگر با Task Scheduler اجرا شده)
# Event Viewer → Windows Logs → Application
```

**Linux:**
```bash
# لاگ سیگنال‌ها
tail -f ~/quotex_bot/quotex_ict_bot/logs/signals.log

# لاگ سرویس (systemd)
sudo journalctl -u quotex-ict-bot.service -f
```

### ری‌استارت سرویس:

**Windows:**
- Task Scheduler → Right-click روی Task → End → سپس Run

**Linux:**
```bash
sudo systemctl restart quotex-ict-bot.service
```

### توقف سرویس:

**Windows:**
- Task Scheduler → Right-click روی Task → Disable

**Linux:**
```bash
sudo systemctl stop quotex-ict-bot.service
```

---

## عیب‌یابی

### مشکل: ربات شروع نمی‌شود

- چک کن فایل `.env` درست پر شده
- چک کن سشن موجود است (`session/quotex_session.pkl`)
- چک کن اینترنت وصل است
- لاگ‌ها رو ببین (خطاها معمولاً داخل لاگ‌ها هست)

### مشکل: مرورگر باز نمی‌شود (Linux)

```bash
# نصب وابستگی‌های Chrome
sudo apt install -y libxss1 libappindicator1 libindicator7
sudo apt install -y libgconf-2-4 libxrandr2 libasound2
```

### مشکل: سشن منقضی شده

- اگر پیام "ورود ناموفق" می‌بینی، سشن منقضی شده
- از روش Console دوباره سشن بگیر و فایل `session/quotex_session.pkl` رو جایگزین کن

### مشکل: سیگنال نمی‌فرستد

- چک کن `TELEGRAM_TOKEN` و `TELEGRAM_CHAT_ID` درست است
- چک کن ربات در Kill Zone است (04:30–07:30، 11:30–14:30، 16:30–19:30 تهران)
- چک کن کندل‌ها از چارت خوانده می‌شوند (ممکنه UI تغییر کرده باشه)

---

## Oracle Cloud (رایگان)

### ایجاد VM:

1. Oracle Cloud → Create Instance
2. OS: Ubuntu 22.04
3. Shape: Always Free (AMD) - 1 OCPU, 1GB RAM
4. Networking: Public IP enabled
5. SSH Key: اضافه کن

### اتصال:

```bash
ssh -i your_key.pem ubuntu@YOUR_IP
```

### نصب و اجرا:

طبق "گزینه 2: سرور لینوکس" بالا عمل کن.

---

## نکات امنیتی

1. **فایل `.env` را محافظت کن:**
   ```bash
   chmod 600 .env  # Linux
   ```

2. **فایل سشن را محافظت کن:**
   ```bash
   chmod 600 session/quotex_session.pkl  # Linux
   ```

3. **فایروال:**
   - فقط پورت‌های لازم (SSH: 22) را باز کن
   - بقیه پورت‌ها را ببند

---

**ربات آماده اجرا روی سرور است!** 🚀

اگر سوالی یا مشکلی بود، لاگ‌ها را چک کن یا بهم خبر بده.

