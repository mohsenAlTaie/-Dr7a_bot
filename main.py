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
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("📲 معرفي", callback_data="get_user_id")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "👁‍🗨✨ *أهلاً بك في البُعد الآخر من التحميل!*\n\n"
        "هل أنت مستعدّ لاختراق عوالم الفيديوهات؟ 🚀📅\n"
        "📌 فقط أرسل الرابط، وسأقوم بالباقي...\n\n"
        "🛠️ *تم بناء هذا البوت بعناية بواسطة محسن علي حسين* 🎮💻"
    )
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
        await update.message.reply_text(random.choice(weird_messages) + "\n⏳ جاري تحميل الفيديو...")
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
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ خطأ أثناء التحميل: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ غير متوقع: {str(e)}")

async def add_vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != 7249021797:
        await update.message.reply_text("❌ هذا الأمر مخصص للإدارة فقط.")
        return

    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        add_vip(user_id, days)
        await update.message.reply_text(f"✅ تم إعطاء VIP للمستخدم {user_id} لمدة {days} يومًا")
    except:
        await update.message.reply_text("❌ الاستخدام الصحيح: /addvip [id] [days]")

async def remove_vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != 7249021797:
        await update.message.reply_text("❌ هذا الأمر مخصص للإدارة فقط.")
        return

    try:
        user_id = int(context.args[0])
        remove_vip(user_id)
        await update.message.reply_text(f"❌ تم حذف VIP للمستخدم {user_id}")
    except:
        await update.message.reply_text("❌ الاستخدام الصحيح: /removevip [id]")

async def vip_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != 7249021797:
        await update.message.reply_text("❌ هذا الأمر مخصص للإدارة فقط.")
        return

    vips = list_vips()
    if not vips:
        await update.message.reply_text("❌ لا يوجد مستخدمين VIP")
    else:
        text = "\n".join([f"👤 {uid} - ينتهي بـ {exp}" for uid, exp in vips])
        await update.message.reply_text(text)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get_user_id":
        user = query.from_user
        await query.message.reply_text(f"🪪 معرفك هو: `{user.id}`", parse_mode=ParseMode.MARKDOWN)
        return
    elif query.data == "my_stats":
        user_id = query.from_user.id
        reset_daily_limits()
        limit = DAILY_LIMIT_VIP if is_vip(user_id) else DAILY_LIMIT_FREE
        user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()})
        remaining = limit - user_data["count"]
        await query.message.reply_text(f"📊 عدد تحميلاتك اليوم: {user_data['count']} / {limit}")
        return

        user = query.from_user
        await query.message.reply_text(f"🪪 معرفك هو: `{user.id}`", parse_mode=ParseMode.MARKDOWN)
        return
    elif query.data == "vip_info":
        await show_vip_info(update, context)
    elif query.data == "vip_expiry":
        await show_expiry(update, context)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usage", usage))
    app.add_handler(CommandHandler("addvip", add_vip_cmd))
    app.add_handler(CommandHandler("removevip", remove_vip_cmd))
    app.add_handler(CommandHandler("viplist", vip_list))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
