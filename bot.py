import json, os, random, time, threading
from typing import Set
from telegram import Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN      = os.getenv("BOT_TOKEN")           # از محیط می‌خوانیم
APP_URL    = os.getenv("APP_URL")             # مثل https://sigma-bot.up.railway.app
DATA_FILE  = "subscribers.json"

class SigmasNewsBot:
    def __init__(self):
        self.subscribers: Set[int] = self._load()
        self.updater = Updater(token=TOKEN, use_context=True)
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self._start))
        dp.add_handler(CommandHandler("subscribe", self._sub))
        dp.add_handler(CommandHandler("unsubscribe", self._unsub))

    # ---------- JSON ----------
    def _load(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except: return set()
    def _save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self.subscribers), f, ensure_ascii=False)

    # ---------- Handlers ----------
    def _start(self, upd: Update, _: CallbackContext):
        txt=("به ربات تلگرام اخبار سیگماس خوش آمدید، جهت مشترک شدن، "
             "از فرمان /subscribe استفاده کنید ...")
        kbd=[["/subscribe","/unsubscribe"]]
        upd.message.reply_text(txt, reply_markup=ReplyKeyboardMarkup(kbd, resize_keyboard=True))
    def _sub(self, upd: Update, _: CallbackContext):
        uid=upd.effective_user.id
        if uid in self.subscribers:
            upd.message.reply_text("شما قبلا مشترک شده اید ❗️"); return
        self.subscribers.add(uid); self._save()
        upd.message.reply_text("✅ شما با موفقیت مشترک شدید.")
    def _unsub(self, upd: Update, _: CallbackContext):
        uid=upd.effective_user.id
        if uid not in self.subscribers:
            upd.message.reply_text("شما مشترک نیستید ❗️"); return
        self.subscribers.remove(uid); self._save()
        upd.message.reply_text("❌ اشتراک شما لغو شد.")

    # ---------- ارسال بیرونی ----------
    def send(self, text: str, mode=ParseMode.HTML):
        for uid in list(self.subscribers):
            try: self.updater.bot.send_message(uid, text, parse_mode=mode)
            except: pass

    # ---------- Webhook ----------
    def run_webhook(self):
        port = int(os.getenv("PORT", 8080))
        self.updater.start_webhook(
            listen="0.0.0.0", port=port, url_path=TOKEN
        )
        self.updater.bot.setWebhook(f"{APP_URL}/{TOKEN}")
        print("Webhook set -->", APP_URL)
        self.updater.idle()

bot = SigmasNewsBot()

# خبر تصادفی هر 30 ثانیه (می‌توانید حذف کنید)
def ticker():
    titles=["خبر فوری","گزارش مالی","محصول جدید","آپدیت نرم‌افزار"]
    bodies=["جزئیات به زودی اعلام می‌شود.","فروش رشد چشمگیری داشت.","تجربه کاربری بهتر شد."]
    while True:
        if bot.subscribers:
            import random
            txt=f"<b>{random.choice(titles)}</b>\n\n{random.choice(bodies)}"
            bot.send(txt)
        time.sleep(30)
threading.Thread(target=ticker, daemon=True).start()

if __name__ == "__main__":
    bot.run_webhook()
