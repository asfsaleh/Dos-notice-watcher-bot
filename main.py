from __future__ import annotations

import os
import re
import time
from html import unescape
from pathlib import Path
from typing import Any, List, Optional, Tuple, cast

import requests
from bs4 import BeautifulSoup, Tag  # শুধু টাইপ-hintের জন্য, চাইলে মুছতে পারো

# ── CONFIG ──────────────────────────────────────────────────────────
URL_JSON: str = (
    "https://dos.gov.bd/site/view/notices?format=json"  # ← এন্ডপয়েন্ট ঠিক রাখো
)
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "7484576751:AAEUAv5aVb0GT8Sap2LaoGxy5-TgKDmwXPg")
CHAT_ID: str = os.getenv("CHAT_ID", "-1002829016591")
BASE_URL: str = "https://dos.gov.bd"

CHECK_EVERY_SEC: int = 600
STORE_FILE: Path = Path("last_notice.txt")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}
# ────────────────────────────────────────────────────────────────────


import re
from html import unescape
from typing import Any, Optional, Tuple, cast

def get_latest_notice() -> Optional[Tuple[str, str, str, str]]:
    resp = requests.get(JSON_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    j: dict[str, Any] = resp.json()
    rows = cast(list[list[str]], j.get("data", []))
    if not rows:
        print("⚠️ JSON 'data' empty")
        return None

    r0 = rows[0]
    title, date, link_html = r0[1], r0[2], r0[3]

    m = re.search(r'href=["\']([^"\']+\.pdf)', unescape(link_html))
    if not m:
        print("⚠️ PDF link not found")
        return None

    href = m.group(1)
    if href.startswith("//"):
        link = "https:" + href
    elif href.startswith("/"):
        link = BASE_URL.rstrip("/") + href
    else:
        link = href

    key = f"{title}|{date}"
    return (key, title, date, link)




def send_telegram(title: str, date: str, link: str) -> None:
    """
    Push a message to Telegram (channel or personal chat).
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️  BOT_TOKEN / CHAT_ID missing")
        return

    payload = {
        "chat_id": CHAT_ID,
        "text": f"🆕 <b>{title}</b>\n📅 {date}\n📄 {link}",
        "parse_mode": "HTML",
    }
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(api, data=payload, timeout=10)
    print("Telegram:", res.status_code, res.text[:120])


def read_last() -> str:
    return STORE_FILE.read_text().strip() if STORE_FILE.exists() else ""


def write_last(key: str) -> None:
    STORE_FILE.write_text(key)


if __name__ == "__main__":
    print("🔔 Notice-Watcher started …")
    while True:
        try:
            result = get_latest_notice()
            if result is None:
                time.sleep(CHECK_EVERY_SEC)
                continue

            key, title, date, link = result
            if key != read_last():
                send_telegram(title, date, link)
                write_last(key)
                print("✅ new notice sent:", title)
            else:
                print("↻ no new notice")
        except Exception as exc:
            print("⚠️", exc)
        time.sleep(CHECK_EVERY_SEC)
