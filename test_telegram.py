# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from telegram import Bot


def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("اول داخل فایل .env مقدار TELEGRAM_TOKEN و TELEGRAM_CHAT_ID را پر کن.")
        return

    bot = Bot(token=token)
    bot.send_message(chat_id=chat_id, text="✅ تست موفق: ربات تلگرام وصل است.")
    print("پیام تستی با موفقیت ارسال شد.")


if __name__ == "__main__":
    main()


