# -*- coding: utf-8 -*-
import os
import json
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IN_FILE = os.path.join(BASE_DIR, "session_from_console.json")
OUT_FILE = os.path.join(BASE_DIR, "session", "quotex_session.pkl")


def main() -> None:
    if not os.path.exists(IN_FILE):
        print("❌ فایل session_from_console.json پیدا نشد. اول JSON را از کنسول مرورگر ذخیره کن.")
        return
    with open(IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    cookies = data.get("cookies", [])
    local_storage = data.get("localStorage", {})

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "wb") as f:
        pickle.dump({"cookies": cookies, "localStorage": local_storage}, f)

    print("✅ فایل سشن ساخته شد:", OUT_FILE)


if __name__ == "__main__":
    main()


