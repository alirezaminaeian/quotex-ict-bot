#!/bin/bash
# اسکریپت ساخت سرویس systemd

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER=$(whoami)
SERVICE_FILE="/etc/systemd/system/quotex-ict-bot.service"

echo "🔧 ساخت سرویس systemd..."

# ساخت فایل سرویس
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Quotex ICT Signal Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$SCRIPT_DIR/logs/bot.log
StandardError=append:$SCRIPT_DIR/logs/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

# اطمینان از وجود پوشه logs
mkdir -p "$SCRIPT_DIR/logs"

# Reload systemd
echo "🔄 بارگذاری مجدد systemd..."
sudo systemctl daemon-reload

# فعال‌سازی سرویس
echo "✅ فعال‌سازی سرویس..."
sudo systemctl enable quotex-ict-bot.service

echo ""
echo "✅ سرویس با موفقیت ساخته شد!"
echo ""
echo "📋 دستورات مفید:"
echo "  شروع:     sudo systemctl start quotex-ict-bot.service"
echo "  توقف:     sudo systemctl stop quotex-ict-bot.service"
echo "  ری‌استارت: sudo systemctl restart quotex-ict-bot.service"
echo "  وضعیت:    sudo systemctl status quotex-ict-bot.service"
echo "  لاگ:      sudo journalctl -u quotex-ict-bot.service -f"
echo ""
echo "⚠️  قبل از شروع، مطمئن شو:"
echo "  1. فایل .env با مقادیر واقعی پر شده"
echo "  2. فایل session/quotex_session.pkl موجود است"
echo ""
echo "🚀 برای شروع: sudo systemctl start quotex-ict-bot.service"

