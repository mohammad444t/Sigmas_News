# 2) کُد ربات
import json, os, random, threading, time
from typing import Set
from telegram import Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

# ───── توکن رباتت را این‌جا بگذار ─────
TOKEN = "8195580337:AAFn5U1KCk4chufiqK3Ikqed2SS96nCEh5g"
# ──────────────────────────────────────


# 3) نمونه‌سازی
bot = SigmasNewsBot(TOKEN)

# 4) تابع تولید خبر
TITLES = [
    "رونمایی از محصول جدید", "گزارش مالی فصل سوم", "همکاری راهبردی",
    "به‌روزرسانی بزرگ نرم‌افزار", "موفقیت تازهٔ استارتاپ"
]
BODIES = [
    "این همکاری فرصت‌های تازه‌ای در بازار جهانی ایجاد می‌کند.",
    "میزان فروش نسبت به سال گذشته ۳۰٪ افزایش یافته است.",
    "کاربران می‌توانند از قابلیت‌های جدید بهره‌مند شوند.",
    "این سرمایه‌گذاری به توسعه زیرساخت‌ها کمک خواهد کرد.",
    "هدف ما افزایش بهره‌وری و رضایت مشتریان است."
]
def random_news() -> str:
    return f"<b>{random.choice(TITLES)}</b>\n\n{random.choice(BODIES)}"

# 5) تردِ ارسال دوره‌ای
def periodic_sender():
    while True:
        if bot.subscribers:
            bot.send_to_subscribers(random_news())
        time.sleep(30)

threading.Thread(target=periodic_sender, daemon=True).start()

# 6) اجرای ربات (گوش دادن دستورات)
bot.run()
