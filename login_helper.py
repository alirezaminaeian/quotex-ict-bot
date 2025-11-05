# -*- coding: utf-8 -*-
import os
import time
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "session", "quotex_session.pkl")
os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)


def init_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,900")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    chrome_options.add_experimental_option('useAutomationExtension', False)
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Fallback: use Chrome without webdriver-manager if offline
        driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


def save_session(driver: webdriver.Chrome) -> None:
    cookies = driver.get_cookies()
    local_storage = driver.execute_script(
        "var ls = {}; for (var i = 0; i < localStorage.length; i++){var k = localStorage.key(i); ls[k] = localStorage.getItem(k);} return ls;"
    )
    with open(SESSION_FILE, "wb") as f:
        pickle.dump({"cookies": cookies, "localStorage": local_storage}, f)
    print("✅ سشن ذخیره شد: session/quotex_session.pkl")


def main():
    driver = init_driver()
    driver.get("https://qxbroker.com/en/trade")
    print("مرورگر باز شد. لطفاً به کواتکس لاگین کن. بعد از ورود کامل به داشبورد، این پنجره ترمینال رو برگرد و Enter بزن.")
    try:
        input()
    except KeyboardInterrupt:
        pass
    save_session(driver)
    driver.quit()


if __name__ == "__main__":
    main()


