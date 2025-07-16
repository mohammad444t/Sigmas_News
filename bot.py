from __future__ import annotations
from typing import List, Dict, Any
from together import Together
import time
import sys
import json, os, random, threading
from typing import Set
from telegram import Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# ───── توکن رباتت را این‌جا بگذار ─────
TOKEN = "8195580337:AAFn5U1KCk4chufiqK3Ikqed2SS96nCEh5g"
# ──────────────────────────────────────



class DeepSeekV3Client:
    """
    Thin wrapper around Together.ai's chat/completions endpoint
    for the model 'deepseek-ai/DeepSeek-V3'.

    Example
    -------
    >>> client = DeepSeekV3Client()
    >>> response = client.ask("Explain transformers in one paragraph.")
    >>> print(response)
    """

    MODEL = "deepseek-ai/DeepSeek-V3"
    _API_KEY = "e48afbc7b0bf0034d704014fd69ccf778c95535b22b70f5dc85e1ccd8aaa49ef"

    def __init__(self, temperature: float = 0.7, top_p: float = 0.9, max_new_tokens: int = 512):
        self.client = Together(api_key=self._API_KEY)
        self.temperature = temperature
        self.top_p = top_p
        self.max_new_tokens = max_new_tokens

    def _format_messages(self, prompt: str, history: List[Dict[str, str]] | None = None) -> List[Dict[str, str]]:
        """
        Combines an optional `history` list with the new user prompt.

        Each item in `history` must look like:
            {"role": "user", "content": "..."}  or
            {"role": "assistant", "content": "..."}
        """
        messages = history[:] if history else []
        messages.append({"role": "user", "content": prompt})
        return messages

    def ask(
        self,
        prompt: str,
        history: List[Dict[str, str]] | None = None,
        **gen_kwargs: Any,
    ) -> str:
        """
        Send the prompt (plus optional message history) and
        return the assistant's text.

        Extra Together parameters can be passed via **gen_kwargs.
        """
        messages = self._format_messages(prompt, history)

        params = {
            "model": self.MODEL,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_new_tokens,
            **gen_kwargs,
        }

        completion = self.client.chat.completions.create(**params)
        return completion.choices[0].message.content


class NewsPromptBuilder:
    """
    سازندهٔ پرامپت برای خبرنویسی به زبان فارسی.
    """

    TEMPLATE = (
        "در نقش یک خبرنویس حرفه‌ای عمل کن. پس از دریافت ورودی من (که شامل یک «عنوان» و سپس «متن خبر» اصلی است)،"
        " دقیقاً خروجی زیر را تولید کن:\n\n"
        "در سطر اول، «عنوان» ورودی را عیناً به‌عنوان عنوان خبر بنویس.\n"
        "از سطر دوم، بدنهٔ خبر را با عبارت دقیق «به گزارش SteelOrbis» آغاز کن و سپس در حداکثر ۱۵۰ کلمه،"
        " طی دو پاراگراف پشت سر هم، خلاصه‌ای روان و منسجم از متن خبر ورودی ارائه بده.\n"
        "هیچ متنی را پررنگ، مورب، فهرست‌وار یا در قالب نشانه‌گذاری (bullet) ننویس؛ همه چیز باید متن ساده باشد.\n"
        "از اضافه کردن هر توضیح یا اطلاعات اضافی خودداری کن؛ فقط عنوان و بدنهٔ مورد نیاز را طبق دستور بالا برگردان.\n"
    )

    def __init__(self, title: str, body: str):
        self.title = title.strip()
        self.body = body.strip()

    def build(self) -> str:
        """
        خروجی نهایی (prompt) را برمی‌گرداند.
        """
        prompt = (
            f"{self.TEMPLATE}\n"
            f"{self.title}\n\n"
            f"{self.body}"
        )
        return prompt



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  لازم است «زمانی طولانی» این سلول در حال اجرا بماند
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class SigmasNewsBot:
    def __init__(self, token: str, data_file: str = "subscribers.json"):
        self.token, self.data_file = token, data_file
        self.subscribers: Set[int] = self._load_subscribers()

        self.updater = Updater(token=self.token, use_context=True)
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self._start))
        dp.add_handler(CommandHandler("subscribe", self._subscribe))
        dp.add_handler(CommandHandler("unsubscribe", self._unsubscribe))

    # ---------- فایل JSON ----------
    def _load_subscribers(self) -> Set[int]:
        if os.path.isfile(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                try:  return set(json.load(f))
                except json.JSONDecodeError: pass
        return set()

    def _save_subscribers(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(list(self.subscribers), f, ensure_ascii=False)

    # ---------- هندلرها ----------
    def _start(self, update: Update, _: CallbackContext):
        txt = ("به ربات تلگرام اخبار سیگماس خوش آمدید، جهت مشترک شدن، "
               "از فرمان /subscribe استفاده کنید و جدیدترین اخبار را دریافت نمایید. "
               "در صورت نیاز به لغو اشتراک، از فرمان /unsubscribe استفاده کنید.")
        kb = [["/subscribe", "/unsubscribe"]]
        update.message.reply_text(txt, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    def _subscribe(self, update: Update, _: CallbackContext):
        uid = update.effective_user.id
        if uid in self.subscribers:
            update.message.reply_text("شما قبلا مشترک شده اید ❗️"); return
        self.subscribers.add(uid); self._save_subscribers()
        update.message.reply_text("✅ شما با موفقیت مشترک شدید.")

    def _unsubscribe(self, update: Update, _: CallbackContext):
        uid = update.effective_user.id
        if uid not in self.subscribers:
            update.message.reply_text("شما مشترک نیستید ❗️"); return
        self.subscribers.remove(uid); self._save_subscribers()
        update.message.reply_text("❌ اشتراک شما لغو شد.")

    # ---------- API ارسال پیام ----------
    def send_to_subscribers(self, text: str, parse_mode=ParseMode.HTML):
        failed = []
        for uid in list(self.subscribers):
            try:
                self.updater.bot.send_message(uid, text, parse_mode=parse_mode)
            except Exception as e:
                print(f"⚠️  cannot send to {uid}: {e}")
                failed.append(uid)
        if failed:
            self.subscribers.difference_update(failed); self._save_subscribers()

    # ---------- اجرا ----------
    def run(self):
        print("Bot is running...  (Ctrl+C to stop cell)")
        self.updater.start_polling()
        self.updater.idle()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SteelOrbisWatcher  – stateless, call-on-demand scraper
=====================================================

• Call .poll() whenever you like (cron, schedule, Celery, …).
• .poll() now returns a **triple** → (is_new, title, body)
      is_new  : bool   – True  → a fresh article was processed
                          False → nothing new
      title   : str    – headline text  (empty when is_new is False)
      body    : str    – cleaned article text (empty when is_new is False)
• Still persists the last seen URL and offers .get_last_article().

Example
-------
from steelorbis_watcher import SteelOrbisWatcher
import time

w = SteelOrbisWatcher()

while True:
    is_new, title, body = w.poll()
    if is_new:
        # do something with title/body
        pass
    time.sleep(60)
"""




class SteelOrbisWatcher:
    # ───────────────────── class-level constants ───────────────────── #
    BASE_URL  = "https://www.steelorbis.com"
    NEWS_LIST = f"{BASE_URL}/steel-news/latest-news/"

    HEADERS = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
    }

    # ───────────────────────── constructor ────────────────────────── #
    def __init__(self, state_file: str | Path = "state.json") -> None:
        """
        state_file – JSON file used to remember the last processed URL.
        """
        self.state_file    = Path(state_file)
        self._last_url     = self._load_last_url()
        self._last_article: Dict[str, str] = {}   # {'url', 'headline', 'body'}

    # ─────────────────────── state helpers ────────────────────────── #
    def _load_last_url(self) -> str:
        try:
            return json.loads(self.state_file.read_text())["last_url"]
        except Exception:
            return ""

    def _save_last_url(self, url: str) -> None:
        self.state_file.write_text(json.dumps({"last_url": url}), encoding="utf-8")

    # ───────────────────── scraping helpers ───────────────────────── #
    @staticmethod
    def _soup(url: str) -> BeautifulSoup:
        resp = requests.get(url, headers=SteelOrbisWatcher.HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")

    def _latest_link(self) -> Tuple[Optional[str], Optional[str]]:
        soup = self._soup(self.NEWS_LIST)
        link = soup.select_one("a:has(.article-shell)")
        if link is None:
            return None, None
        url   = urljoin(self.BASE_URL, link["href"])
        title = link.select_one("h3.article-lead").get_text(strip=True)
        return url, title

    def _fetch_article(self, url: str) -> Tuple[str, str]:
        soup = self._soup(url)
        headline_tag = soup.select_one("h1.home-h1")
        body_tag     = soup.select_one("#contentDiv")
        headline     = headline_tag.get_text(strip=True) if headline_tag else ""

        # unwrap hyperlinks, keep their text
        for a in body_tag.find_all("a"):
            a.unwrap()

        parts = [blk.get_text(" ", strip=True) for blk in body_tag.find_all(["h2", "p"])]
        body  = "\n".join(parts)
        return headline, body

    # ───────────────────── event callback ─────────────────────────── #
    def on_new_article(self, headline: str, body: str, url: str) -> None:
        """
        Override for custom side-effects.
        Default: pretty-print the article.
        """
        bar = "=" * 80
        print(f"\n{bar}\n{headline}\n{bar}\n{body}\n")

    # ───────────────────── public interface ───────────────────────── #
    def poll(self) -> Tuple[bool, str, str]:
        """
        One-shot check.
        Returns (is_new, title, body)  as described at top.
        """
        url, _ = self._latest_link()

        if url and url != self._last_url:
            # new article detected
            title, body = self._fetch_article(url)

            # cache and persist
            self._last_url     = url
            self._last_article = {"url": url, "headline": title, "body": body}
            self._save_last_url(url)

            # user hook
            self.on_new_article(title, body, url)
            return True, title, body

        # nothing new
        print("No new news")
        return False, "", ""

    def get_last_article(self) -> Dict[str, str]:
        """
        Return a copy of the cached article dict or {} if none fetched yet.
        """
        return self._last_article.copy()


# ─────────────────────── main ────────────────────────── #

watcher = SteelOrbisWatcher()

bot = SigmasNewsBot(TOKEN)

llm_bot = DeepSeekV3Client()


# 5) تردِ ارسال دوره‌ای
def periodic_sender():
    while True:
        isnew, news_title, news_body = watcher.poll()
        if isnew:
            if bot.subscribers:
                builder = NewsPromptBuilder(
                    title = news_title,
                    body = news_body
                )
                prompt = builder.build()
                reply = llm_bot.ask(prompt)
                bot.send_to_subscribers(reply)
        time.sleep(60)

threading.Thread(target=periodic_sender, daemon=True).start()

# 6) اجرای ربات (گوش دادن دستورات)
bot.run()
