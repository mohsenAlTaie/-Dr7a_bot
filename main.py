import os
import random
import logging
import time
import subprocess
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد اللوج
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"

# مجلد التحميل
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# قاعدة بيانات VIP
conn = sqlite3.connect("vip_users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY, expires_at TEXT)''')
conn.commit()

def is_vip(user_id: int):
    c.execute("SELECT expires_at FROM vip_users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        if datetime.strptime(row[0], "%Y-%m-%d") >= datetime.utcnow():
            return True
    return False

def get_vip_expiry(user_id: int):
    c.execute("SELECT expires_at FROM vip_users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    return row[0] if row else None

def add_vip(user_id: int, days: int):
    expires_at = datetime.utcnow() + timedelta(days=days)
    c.execute("INSERT OR REPLACE INTO vip_users (user_id, expires_at) VALUES (?, ?)", (user_id, expires_at.date()))
    conn.commit()

def remove_vip(user_id: int):
    c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
    conn.commit()

def list_vips():
    c.execute("SELECT user_id, expires_at FROM vip_users")
    return c.fetchall()

weird_messages = [
    "👽 جاري التواصل مع كائنات TikTok الفضائية...",
    "🔮 فتح بوابة الزمن الرقمي...",
    "🧪 خلط فيديوهات TikTok في المختبر السري...",
    "🐍 استدعاء تنين TikTok لتحميل الفيديو...",
    "📡 التقاط إشارة من سيرفرات الصين...",
    "🚀 تحميل الفيديو بسرعة تتجاوز سرعة الضوء... تقريبًا",
    "🧠 استخدام الذكاء الاصطناعي لفك شيفرة الرابط...",
    "💿 إدخال قرص TikTok داخل مشغل VHS الفضائي...",
    "👾 استدعاء روبوت التحميل من بعد آخر...",
    "🍕 رش جبنة على الرابط للحصول على نكهة أفضل للفيديو...",
    "🎩 تحويل الرابط إلى أرنب وسحبه من القبعة...",
    "🐢 تحميل الفيديو... بسرعة سلحفاة نينجا 🐢 (امزح، هو سريع!)"
]

user_timestamps = {}
daily_limits = {}
DAILY_LIMIT_FREE = 10
DAILY_LIMIT_VIP = 100

def reset_daily_limits():
    current_date = datetime.utcnow().date()
    for user_id in list(daily_limits):
        if daily_limits[user_id]["date"] != current_date:
            daily_limits[user_id] = {"count": 0, "date": current_date}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 معلومات VIP", callback_data="vip_info")],
        [InlineKeyboardButton("🕓 معلومات الاشتراك", callback_data="vip_expiry")],
        [InlineKeyboardButton("🪪 معرفي", callback_data="get_id")],
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "🌌 *مرحباً بك في نُقطة التقاء العوالم الرقمية!*

"
        "هل أنت مستعدّ لاختراق جدران الوقت والبيانات؟ 🧠💾
"
        "🛰️ أرسل الرابط الآن، وسأُحولك إلى بُعد الفيديو الخارق.

"
        "🎯 *تم تطوير هذا النظام من قِبل محسن علي حسين، حيث تلتقي الحرفية بالسحر!*"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def show_vip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "💎 *معلومات اشتراك VIP:*

"
        "✅ تحميل حتى 100 فيديو باليوم
"
        "❌ لا انتظار بين التحميلات
"
        "⚡ أولوية في السرعة
"
        "🔐 دعم الملفات الخاصة

"
        "💰 *طرق الدفع:*
"
        "- آسياسيل
- زين كاش
- ماستر كارد

"
        "📬 للاشتراك، اضغط للتواصل مع المطور"
    )
    keyboard = [[InlineKeyboardButton("💬 تواصل مع المطور", url="https://t.me/K0_MG")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    expiry = get_vip_expiry(user_id)
    if expiry:
        await query.edit_message_text(f"💎 صلاحية اشتراكك تنتهي في: `{expiry}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await query.edit_message_text("❌ ليس لديك اشتراك VIP حاليًا.")

async def handle_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.edit_message_text(f"🪪 معرفك هو: `{user_id}`", parse_mode=ParseMode.MARKDOWN)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_vip_info, pattern="vip_info"))
    app.add_handler(CallbackQueryHandler(show_expiry, pattern="vip_expiry"))
    app.add_handler(CallbackQueryHandler(handle_id, pattern="get_id"))
    app.run_polling()

if __name__ == "__main__":
    main()
