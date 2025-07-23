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
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("💎 معلومات VIP", callback_data="vip_info")],
        [InlineKeyboardButton("🕓 معلومات الاشتراك", callback_data="vip_expiry")],
        [InlineKeyboardButton("📮 إرسال معرفي لتفعيل VIP", callback_data="send_id")],
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")],
        [InlineKeyboardButton("📊 حالتي", callback_data="my_status")]
    ]
    if user_id == 7249021797:
        keyboard.insert(0, [InlineKeyboardButton("📜 الأوامر", callback_data="show_commands")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = "⚡️ مرحباً بك في مختبر الظلال الرقمية 💠🚀\nحيث تبدأ الفيديوهات رحلتها عبر الزمن!"
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reset_daily_limits()
    limit = DAILY_LIMIT_VIP if is_vip(user_id) else DAILY_LIMIT_FREE
    user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()})
    remaining = limit - user_data["count"]
    await update.message.reply_text(f"📊 عدد التحميلات المتبقية اليوم: {remaining} من {limit}")

async def show_vip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "💎 *معلومات اشتراك VIP:*\n\n"
        "✅ تحميل فيديوهات بلا حدود\n"
        "❌ لا انتظار بين التحميلات\n"
        "⚡ أولوية في السرعة\n"
        "🔐 دعم الملفات الخاصة\n\n"
        "💰 *طرق الدفع:*\n"
        "- آسياسيل\n- زين كاش\n- ماستر كارد\n\n"
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

async def my_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    reset_daily_limits()
    limit = DAILY_LIMIT_VIP if is_vip(user_id) else DAILY_LIMIT_FREE
    user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()})
    remaining = limit - user_data["count"]
    
    next_reset = datetime.combine(datetime.utcnow().date() + timedelta(days=1), datetime.min.time())

    text = (
        f"📊 *حالتك الحالية:*\n\n"
        f"🔄 المتبقي من التحميل اليوم: `{remaining}` من `{limit}`\n"
        f"⏳ يمكنك إعادة التحميل بعد: `{next_reset.strftime('%Y-%m-%d %H:%M')} UTC`\n"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    url = update.message.text.strip()

    if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
        await update.message.reply_text("⏳ الرجاء الانتظار قليلاً قبل إرسال رابط جديد.")
        return
    user_timestamps[user_id] = now

    reset_daily_limits()
    limit = DAILY_LIMIT_VIP if is_vip(user_id) else DAILY_LIMIT_FREE
    user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()})
    if user_data["count"] >= limit:
        await update.message.reply_text("🚫 وصلت للحد الأقصى. الرجاء المحاولة غدًا أو الترقية إلى VIP.")
        return
    daily_limits[user_id] = {"count": user_data["count"] + 1, "date": datetime.utcnow().date()}

    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com"]):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم.")
        return

    if "tiktok.com" in url:
        await update.message.reply_text("⏳ جاري تحميل الفيديو...")
        ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'mp4', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(file_path, 'rb'))
            os.remove(file_path)
        except Exception as e:
            await update.message.reply_text(f"❌ فشل التحميل: {str(e)}")
        return

    await update.message.reply_text("📥 جاري تحميل الفيديو...")
    try:
        file_path = "downloads/video.mp4"
        command = ["yt-dlp", "-f", "mp4"]

        if "facebook.com" in url or "fb.watch" in url:
            command += ["--cookies", "facebook_cookies.txt"]
        elif "youtube.com" in url or "youtu.be" in url:
            command += ["--cookies", "youtube_cookies.txt"]
        elif "instagram.com" in url:
            command += ["--cookies", "instagram_cookies.txt"]

        command += ["-o", file_path, url]
        subprocess.run(command, check=True)

        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف بعد التحميل.")
    except subprocess
