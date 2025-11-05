# -*- coding: utf-8 -*-
import os
import time
import pickle
import logging
from datetime import datetime, time as dtime
from typing import Any, Dict, List, Optional, Tuple

import pytz
import pandas as pd
from dotenv import load_dotenv
import base64

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Telegram (python-telegram-bot v13.x - synchronous API)
from telegram import Bot


# -----------------------------
# Configuration and Logging
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "session", "quotex_session.pkl")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "signals.log")

os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# -----------------------------
# Kill Zones (Asia/Tehran)
# -----------------------------

KILL_ZONES: List[Tuple[str, str]] = [
    ("04:30", "07:30"),  # Asia OTC
    ("11:30", "14:30"),  # London OTC
    ("16:30", "19:30"),  # New York OTC (BEST)
]


# -----------------------------
# Utility functions
# -----------------------------

def load_env() -> Dict[str, str]:
    """Load environment variables from .env file placed in project root."""
    load_dotenv()
    env = {
        "QUOTEX_EMAIL": os.getenv("QUOTEX_EMAIL", ""),
        "QUOTEX_PASSWORD": os.getenv("QUOTEX_PASSWORD", ""),
        "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
        "HEADLESS": os.getenv("HEADLESS", "false").lower() == "true",
        "SESSION_B64": os.getenv("SESSION_B64", ""),
    }
    return env


def ensure_session_from_env(session_b64: str) -> None:
    """If SESSION_B64 is provided (base64 of pickled session dict), write to SESSION_FILE."""
    if not session_b64:
        return
    try:
        if not os.path.exists(SESSION_FILE):
            data = base64.b64decode(session_b64)
            os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
            with open(SESSION_FILE, "wb") as f:
                f.write(data)
            logging.info("Session restored from SESSION_B64 env variable")
    except Exception as e:
        logging.error(f"Failed writing session from env: {e}")


def init_driver(headless: bool = False) -> webdriver.Chrome:
    """Initialize Chrome WebDriver.
    Priority:
      1) Use system Chromium + Chromedriver (e.g., Railway/Nixpacks at /usr/bin).
      2) Fallback to webdriver-manager download.
    """
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,900")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Prefer system Chromium/Chromedriver if present (Railway/Nixpacks)
    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    try:
        if os.path.exists(chrome_bin):
            chrome_options.binary_location = chrome_bin
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            return driver
    except Exception:
        pass

    # Fallback: webdriver-manager (downloads matching driver)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


def save_session(driver: webdriver.Chrome) -> None:
    """Persist cookies and localStorage to a pickle file."""
    try:
        cookies = driver.get_cookies()
        local_storage = driver.execute_script(
            "var ls = {}; for (var i = 0; i < localStorage.length; i++){var k = localStorage.key(i); ls[k] = localStorage.getItem(k);} return ls;"
        )
        with open(SESSION_FILE, "wb") as f:
            pickle.dump({"cookies": cookies, "localStorage": local_storage}, f)
        logging.info("Session saved: cookies + localStorage")
    except Exception as e:
        logging.error(f"Failed to save session: {e}")


def load_session(driver: webdriver.Chrome, base_url: str) -> bool:
    """Load cookies and localStorage if session file exists. Return True if dashboard loads."""
    if not os.path.exists(SESSION_FILE):
        return False
    try:
        driver.get(base_url)
        with open(SESSION_FILE, "rb") as f:
            data = pickle.load(f)
        # Load cookies
        for ck in data.get("cookies", []):
            try:
                driver.add_cookie(ck)
            except WebDriverException:
                pass
        # Load localStorage
        ls: Dict[str, str] = data.get("localStorage", {})
        for k, v in ls.items():
            driver.execute_script("localStorage.setItem(arguments[0], arguments[1]);", k, v)
        driver.refresh()
        # Check if dashboard appears
        return is_logged_in(driver)
    except Exception as e:
        logging.error(f"Failed to load session: {e}")
        return False


def is_logged_in(driver: webdriver.Chrome) -> bool:
    """Heuristic: detect a dashboard element that only exists after login."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='balance']"))
        )
        return True
    except TimeoutException:
        return False


def manual_login_with_2fa(driver: webdriver.Chrome, email: str, password: str) -> bool:
    """Perform manual login and handle email 2FA code entered via console input.
    More robust against redirects/iframes and renderer resets.
    """
    sign_in_urls = [
        "https://qxbroker.com/en/sign-in",
        "https://qxbroker.com/en/trade",
    ]

    for url in sign_in_urls:
        try:
            driver.get(url)
            break
        except WebDriverException:
            continue

    def wait_email_field(max_tries: int = 3) -> bool:
        for _ in range(max_tries):
            try:
                driver.switch_to.default_content()
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for fr in iframes:
                    try:
                        driver.switch_to.frame(fr)
                        if driver.find_elements(By.NAME, "email"):
                            return True
                        driver.switch_to.default_content()
                    except WebDriverException:
                        driver.switch_to.default_content()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
                return True
            except (TimeoutException, WebDriverException):
                try:
                    driver.switch_to.default_content()
                    driver.refresh()
                    time.sleep(1)
                except WebDriverException:
                    time.sleep(1)
        return False

    if not wait_email_field():
        return False

    try:
        try:
            driver.switch_to.default_content()
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for fr in iframes:
                try:
                    driver.switch_to.frame(fr)
                    if driver.find_elements(By.NAME, "email"):
                        break
                    driver.switch_to.default_content()
                except WebDriverException:
                    driver.switch_to.default_content()
        except WebDriverException:
            driver.switch_to.default_content()

        email_el = driver.find_element(By.NAME, "email")
        email_el.clear()
        email_el.send_keys(email)
        pwd_el = driver.find_element(By.NAME, "password")
        pwd_el.clear()
        pwd_el.send_keys(password)

        submit_btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button[data-qa='submit'], button")
        if submit_btns:
            try:
                submit_btns[0].click()
            except WebDriverException:
                driver.execute_script("arguments[0].click();", submit_btns[0])

        try:
            driver.switch_to.default_content()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel'], input[name*='code'], input[autocomplete='one-time-code']"))
            )
            print("کد تأیید ایمیل رو وارد کن:")
            code = input().strip()
            code_field = driver.find_element(By.CSS_SELECTOR, "input[type='tel'], input[name*='code'], input[autocomplete='one-time-code']")
            code_field.clear()
            code_field.send_keys(code)
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except NoSuchElementException:
                pass
        except TimeoutException:
            pass

        driver.switch_to.default_content()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='balance']"))
        )
        save_session(driver)
        return True
    except (TimeoutException, WebDriverException):
        return False


def login_with_session(driver: webdriver.Chrome, email: str, password: str) -> bool:
    """Try session login first. If fail, perform manual login and save session."""
    base_trade = "https://qxbroker.com/en/trade"
    if load_session(driver, base_trade):
        return True
    ok = manual_login_with_2fa(driver, email, password)
    return ok


# -----------------------------
# OTC asset handling and chart scraping
# -----------------------------

def open_asset_selector(driver: webdriver.Chrome) -> None:
    """Open asset selector/picker on the platform."""
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-qa='asset-selector']"))
        ).click()
    except TimeoutException:
        driver.find_element(By.CSS_SELECTOR, "button[class*='asset'], [class*='asset']").click()


def get_otc_pairs(driver: webdriver.Chrome) -> List[str]:
    """Detect all OTC pairs visible in the asset selector.
    If detection fails, return a safe fallback list.
    """
    pairs: List[str] = []
    try:
        open_asset_selector(driver)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "[data-qa='asset-item'], li, div[role='option']")
        for it in items:
            name = it.text.strip()
            if name and "OTC" in name.upper():
                pairs.append(name)
    except Exception:
        pass

    if not pairs:
        pairs = [
            "EUR/USD OTC",
            "GBP/USD OTC",
            "AUD/USD OTC",
            "USD/JPY OTC",
            "NZD/CAD OTC",
            "EUR/GBP OTC",
        ]
    try:
        driver.execute_script("document.activeElement && document.activeElement.blur && document.activeElement.blur();")
    except Exception:
        pass
    return pairs


def switch_to_pair(driver: webdriver.Chrome, pair_name: str) -> bool:
    """Switch chart to the given pair name (OTC)."""
    try:
        open_asset_selector(driver)
        time.sleep(0.5)
        items = driver.find_elements(By.CSS_SELECTOR, "[data-qa='asset-item'], li, div[role='option']")
        for it in items:
            if pair_name.strip().lower() in it.text.strip().lower():
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", it)
                it.click()
                time.sleep(1.0)
                return True
    except Exception:
        return False
    return False


def set_timeframe(driver: webdriver.Chrome, tf_label: str) -> None:
    """Set timeframe on the chart, e.g., '1m' or '5m'."""
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-qa='timeframe-selector']"))
        ).click()
        time.sleep(0.2)
        options = driver.find_elements(By.CSS_SELECTOR, "[data-qa='timeframe-option'], button, li")
        for op in options:
            if tf_label.upper() in op.text.upper():
                op.click()
                time.sleep(0.3)
                return
    except Exception:
        pass


def get_candles(driver: webdriver.Chrome, tf_label: str, count: int) -> Optional[pd.DataFrame]:
    """Extract recent candles using injected JavaScript when possible.
    Returns a DataFrame with columns: time, open, high, low, close, color
    """
    set_timeframe(driver, tf_label)
    time.sleep(0.8)

    js_candidates = [
        """
        const out = [];
        try {
          const series = window.__lc_series || window.series || null;
          if (series && series.series && series.series[0] && series.series[0].data) {
            const data = series.series[0].data;
            for (let i = Math.max(0, data.length - arguments[0]); i < data.length; i++) {
              const c = data[i];
              out.push({t: c.time, o: c.open, h: c.high, l: c.low, c: c.close});
            }
          }
        } catch(e) {}
        return out;
        """,
        """
        const out = [];
        try {
          const w = window.tvWidget || window.widget || null;
          if (w && w.activeChart) {
            const c = w.activeChart();
            const bars = c._bars || c._data || [];
            const start = Math.max(0, bars.length - arguments[0]);
            for (let i = start; i < bars.length; i++) {
              const b = bars[i];
              if (!b) continue;
              out.push({t: b.time || b.t, o: b.open||b.o, h: b.high||b.h, l: b.low||b.l, c: b.close||b.cl});
            }
          }
        } catch(e) {}
        return out;
        """,
    ]

    rows: List[Dict[str, Any]] = []
    for script in js_candidates:
        try:
            res = driver.execute_script(script, count)
            if isinstance(res, list) and len(res) >= max(5, int(count/2)):
                for r in res[-count:]:
                    if not r:
                        continue
                    o = float(r.get('o', 0) or 0)
                    h = float(r.get('h', 0) or 0)
                    l = float(r.get('l', 0) or 0)
                    c = float(r.get('c', 0) or 0)
                    t = r.get('t', None)
                    color = 'green' if c >= o else 'red'
                    rows.append({"time": t, "open": o, "high": h, "low": l, "close": c, "color": color})
                break
        except Exception:
            continue

    if not rows:
        return None
    df = pd.DataFrame(rows)
    return df.tail(count).reset_index(drop=True)


# -----------------------------
# ICT Logic
# -----------------------------

def detect_order_block(df: pd.DataFrame) -> bool:
    if df is None or len(df) < 5:
        return False
    last = df.iloc[-2]
    body = abs(last["close"] - last["open"])
    wick = (last["high"] - last["low"]) - body
    return body > wick and body > (df["close"] - df["open"]).abs().rolling(10).mean().iloc[-2]


def detect_fvg(df: pd.DataFrame) -> bool:
    if df is None or len(df) < 3:
        return False
    c1 = df.iloc[-3]
    c2 = df.iloc[-2]
    c3 = df.iloc[-1]
    bullish_gap = c1["high"] < c3["low"]
    bearish_gap = c1["low"] > c3["high"]
    return bool(bullish_gap or bearish_gap)


def detect_liquidity_sweep(df: pd.DataFrame) -> bool:
    if df is None or len(df) < 10:
        return False
    recent = df.tail(10)
    prev_high = recent["high"].iloc[:-1].max()
    prev_low = recent["low"].iloc[:-1].min()
    last = recent.iloc[-1]
    swept_high = last["high"] > prev_high and last["close"] < prev_high
    swept_low = last["low"] < prev_low and last["close"] > prev_low
    return bool(swept_high or swept_low)


def detect_engulfing_m1(df: pd.DataFrame) -> Optional[str]:
    if df is None or len(df) < 2:
        return None
    prev = df.iloc[-2]
    cur = df.iloc[-1]
    bullish = cur["low"] <= prev["low"] and cur["high"] >= prev["high"] and cur["close"] > cur["open"]
    bearish = cur["high"] >= prev["high"] and cur["low"] <= prev["low"] and cur["close"] < cur["open"]
    if bullish:
        return "CALL"
    if bearish:
        return "PUT"
    return None


def detect_bos(df: pd.DataFrame) -> bool:
    if df is None or len(df) < 5:
        return False
    swing_high = df["high"].rolling(3, center=True).max().iloc[-3]
    swing_low = df["low"].rolling(3, center=True).min().iloc[-3]
    last = df.iloc[-1]
    return bool(last["high"] > swing_high or last["low"] < swing_low)


def in_kill_zone(now_tehran: datetime) -> bool:
    t = now_tehran.time()
    for start_str, end_str in KILL_ZONES:
        s_h, s_m = map(int, start_str.split(":"))
        e_h, e_m = map(int, end_str.split(":"))
        if dtime(s_h, s_m) <= t <= dtime(e_h, e_m):
            return True
    return False


def compute_confluence(ob: bool, sweep: bool, engulf_dir: Optional[str], fvg: bool, bos: bool, now_tehran: datetime) -> int:
    score = 0
    if ob and sweep and engulf_dir:
        score = 70
    if score and fvg:
        score = 80
    if score and bos and in_kill_zone(now_tehran):
        score = max(score, 85)
    if score == 0 and (fvg or bos):
        score = 50
    return score


def expiry_decision(score: int, engulf_dir: Optional[str], has_ob: bool, has_fvg: bool, has_bos: bool, now_tehran: datetime) -> int:
    expiry = 1
    hour = now_tehran.hour
    minute = now_tehran.minute
    if score >= 85 and has_ob and has_fvg and has_bos and engulf_dir and (hour == 17 or hour == 18 or (hour == 19 and minute == 0)):
        expiry = 2
    return expiry


def detect_ict_signal(m5: Optional[pd.DataFrame], m1: Optional[pd.DataFrame], pair: str) -> Optional[Dict[str, Any]]:
    tz = pytz.timezone("Asia/Tehran")
    now = datetime.now(tz)
    if m5 is None or m1 is None:
        return None

    ob = detect_order_block(m5)
    fvg = detect_fvg(m5)
    sweep = detect_liquidity_sweep(m5)
    engulf_dir = detect_engulfing_m1(m1)
    bos = detect_bos(m5)

    score = compute_confluence(ob, sweep, engulf_dir, fvg, bos, now)
    if score < 70 or not engulf_dir:
        return None
    expiry = expiry_decision(score, engulf_dir, ob, fvg, bos, now)

    return {
        "pair": pair,
        "direction": engulf_dir,
        "expiry": expiry,
        "score": score,
        "reason": ("OB + " if ob else "") + ("FVG + " if fvg else "") + ("Sweep + " if sweep else "") + ("BOS + " if bos else "") + "Engulfing",
        "time": now.strftime("%H:%M تهران"),
    }


# -----------------------------
# Telegram
# -----------------------------

def send_telegram_signal(token: str, chat_id: str, signal: Dict[str, Any]) -> None:
    bot = Bot(token=token)
    text = (
        "سیگنال قوی ICT\n"
        f"جفت: {signal['pair']}\n"
        f"جهت: {signal['direction']}\n"
        f"انقضا: {signal['expiry']} دقیقه\n"
        f"احتمال: {signal['score']}%\n"
        f"دلیل: {signal['reason']}\n"
        f"زمان: {signal['time']}\n"
        "همین الان وارد شو!"
    )
    try:
        bot.send_message(chat_id=chat_id, text=text)
        logging.info(f"Sent Telegram signal: {text}")
    except Exception as e:
        logging.error(f"Telegram send failed: {e}")


# -----------------------------
# Main loop
# -----------------------------

def main() -> None:
    env = load_env()
    if not env["QUOTEX_EMAIL"] or not env["QUOTEX_PASSWORD"]:
        print("لطفاً فایل .env را با ایمیل و رمز عبور پر کن.")
        return
    if not env["TELEGRAM_TOKEN"] or not env["TELEGRAM_CHAT_ID"]:
        print("لطفاً توکن و چت‌آی‌دی تلگرام را در .env تنظیم کن.")
        return

    # If running on server without filesystem session, allow env-based session injection
    ensure_session_from_env(env.get("SESSION_B64", ""))

    driver = init_driver(headless=env["HEADLESS"])

    logged_in = login_with_session(driver, env["QUOTEX_EMAIL"], env["QUOTEX_PASSWORD"])
    if not logged_in:
        print("ورود ناموفق بود. دوباره تلاش کن.")
        driver.quit()
        return

    otc_pairs = get_otc_pairs(driver)
    print("جفت‌ارزهای OTC شناسایی شده:", otc_pairs)

    tz = pytz.timezone("Asia/Tehran")

    try:
        while True:
            now = datetime.now(tz)
            if in_kill_zone(now):
                if not is_logged_in(driver):
                    logged_in = login_with_session(driver, env["QUOTEX_EMAIL"], env["QUOTEX_PASSWORD"])
                    if not logged_in:
                        time.sleep(30)
                        continue

                strongest: Optional[Dict[str, Any]] = None

                for pair in otc_pairs:
                    if not switch_to_pair(driver, pair):
                        continue
                    m5 = get_candles(driver, "5m", 50)
                    m1 = get_candles(driver, "1m", 30)
                    sig = detect_ict_signal(m5, m1, pair)
                    if sig and sig["score"] >= 85:
                        if strongest is None or sig["score"] > strongest["score"]:
                            strongest = sig

                if strongest:
                    send_telegram_signal(env["TELEGRAM_TOKEN"], env["TELEGRAM_CHAT_ID"], strongest)
                    time.sleep(65)
                else:
                    time.sleep(30)
            else:
                print("خارج از Kill Zone - صبر...")
                time.sleep(60)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
