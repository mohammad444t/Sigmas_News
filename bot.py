import os, time, sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL   = "https://www.steelorbis.com"
NEWS_LIST  = f"{BASE_URL}/steel-news/latest-news/"
INTERVAL   = 30     # seconds between polls

BOT_TOKEN  = os.getenv("BOT_TOKEN")
CHAT_ID    = os.getenv("CHAT_ID")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}

TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def tg_send(text):
    resp = requests.post(TG_URL, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }, timeout=10)
    resp.raise_for_status()

def get_latest_article_url():
    r = requests.get(NEWS_LIST, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    link = soup.select_one("a:has(.article-shell)")
    if not link:
        return None
    return urljoin(BASE_URL, link["href"])

def fetch_article(url):
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    headline = soup.select_one("h1.home-h1").get_text(strip=True)
    body_div = soup.select_one("#contentDiv")
    for a in body_div.find_all("a"):
        a.unwrap()
    body = body_div.get_text("\n", strip=True)
    return f"{headline}\n\n{body}"

def main():
    if not BOT_TOKEN or not CHAT_ID:
        sys.exit("BOT_TOKEN / CHAT_ID env vars missing")

    last_url = None
    tg_send("🤖 SteelOrbis bot started. Polling every 30 s.")

    while True:
        try:
            url = get_latest_article_url()
            if url and url != last_url:
                last_url = url
                tg_send("🆕  New article detected.\nFetching…")
                tg_send(fetch_article(url))
            else:
                print("No new news")
        except Exception as e:
            print("Error:", e)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()