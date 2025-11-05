# راهنمای آپلود به GitHub

این راهنما برای آپلود کردن پروژه به GitHub است.

---

## مرحله 1: نصب Git

اگر Git نصب نیست:

**ویندوز:**
- دانلود: https://git-scm.com/download/win
- نصب کن و "Add Git to PATH" را تیک بزن

**لینوکس:**
```bash
sudo apt install git -y
```

---

## مرحله 2: ساخت Repository در GitHub

1. وارد GitHub شوید (https://github.com)
2. کلیک روی **"New repository"** (یا + در گوشه بالا)
3. نام repository: `quotex-ict-bot` (یا هر نامی که می‌خواهی)
4. **Public** یا **Private** انتخاب کنید (برای امنیت بهتر Private)
5. **تیک "Add a README file" را بردار** (ما خودشون رو داریم)
6. کلیک **"Create repository"**

---

## مرحله 3: آپلود فایل‌ها به GitHub

### از کامپیوتر خودت (Command Line):

```bash
# 1. برو به پوشه پروژه
cd C:\qt\quotex_ict_bot

# 2. ساخت repository محلی
git init

# 3. اضافه کردن فایل‌ها (مهم: فقط فایل‌های لازم)
git add main.py
git add login_helper.py
git add convert_session.py
git add test_telegram.py
git add requirements.txt
git add env.example
git add .gitignore
git add README.md
git add setup_guide.md
git add SERVER_SETUP.md
git add install_server.sh
git add setup_systemd.sh
git add install_server.ps1
git add GITHUB_SETUP.md

# 4. Commit اولیه
git commit -m "Initial commit: Quotex ICT Bot"

# 5. اضافه کردن remote (آدرس GitHub خودت رو بذار)
git remote add origin https://github.com/YOUR_USERNAME/quotex-ict-bot.git

# 6. Push به GitHub
git branch -M main
git push -u origin main
```

### اگر GitHub Authentication می‌خواهد:

**روش 1: Personal Access Token (توصیه می‌شود)**

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → نام: "Quotex Bot" → تیک `repo` → Generate
3. Token را کپی کن (فقط یکبار نمایش داده می‌شه!)
4. وقتی `git push` می‌زنی، Username: GitHub username، Password: Token

**روش 2: GitHub CLI**

```bash
# نصب GitHub CLI
# ویندوز: https://cli.github.com/
# لینوکس: sudo apt install gh

gh auth login
```

---

## مرحله 4: چک کردن

1. به GitHub برو و repository خودت رو باز کن
2. باید فایل‌های زیر را ببینی:
   - `main.py`
   - `README.md`
   - `requirements.txt`
   - `.gitignore`
   - و بقیه فایل‌های لازم

**⚠️ مهم:** فایل‌های زیر **نباید** در GitHub باشند:
- `.env` (حاوی اطلاعات حساس)
- `session/quotex_session.pkl` (حاوی کوکی‌ها)
- `logs/*.log` (فایل‌های لاگ)

این فایل‌ها در `.gitignore` هستند و commit نمی‌شوند.

---

## مرحله 5: آپدیت بعدی

وقتی تغییری در کد دادی:

```bash
# 1. اضافه کردن تغییرات
git add .

# 2. Commit
git commit -m "توضیح تغییرات"

# 3. Push
git push
```

---

## فایل‌هایی که باید در GitHub باشند:

✅ **باید آپلود بشن:**
- `main.py`
- `login_helper.py`
- `convert_session.py`
- `test_telegram.py`
- `requirements.txt`
- `env.example`
- `.gitignore`
- `README.md`
- `setup_guide.md`
- `SERVER_SETUP.md`
- `GITHUB_SETUP.md`
- `install_server.sh`
- `setup_systemd.sh`
- `install_server.ps1`

❌ **نباید آپلود بشن:**
- `.env` (در `.gitignore` است)
- `session/*.pkl` (در `.gitignore` است)
- `logs/*.log` (در `.gitignore` است)
- `__pycache__/` (در `.gitignore` است)
- `venv/` (در `.gitignore` است)

---

## دستورات Git مفید

```bash
# دیدن وضعیت فایل‌ها
git status

# دیدن تغییرات
git diff

# دیدن تاریخچه
git log

# حذف یک فایل از Git (ولی نگه داشتن در سیستم)
git rm --cached filename

# برگشت به آخرین commit
git reset --hard HEAD
```

---

## اگر خطا گرفتی

### خطا: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/quotex-ict-bot.git
```

### خطا: "Authentication failed"

- Personal Access Token بساز و استفاده کن (مرحله 3 بالا)

### خطا: "refusing to merge unrelated histories"

```bash
git pull origin main --allow-unrelated-histories
```

---

**همه چیز آماده است! 🚀**

اگر سوالی بود، خبر بده.

