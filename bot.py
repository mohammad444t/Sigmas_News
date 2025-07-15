# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  لازم است «زمانی طولانی» این سلول در حال اجرا بماند
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1) نصب کتابخانه

# 2) کُد ربات
import json, os, random, threading, time
from typing import Set
from telegram import Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

# ───── توکن رباتت را این‌جا بگذار ─────
TOKEN = "8195580337:AAFn5U1KCk4chufiqK3Ikqed2SS96nCEh5g"
# ──────────────────────────────────────

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
