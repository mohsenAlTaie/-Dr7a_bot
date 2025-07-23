import os import random import logging import time import subprocess import sqlite3 from datetime import datetime from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton from telegram.constants import ParseMode from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes import yt_dlp

إعداد اللوج

logging.basicConfig( format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO )

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU" BOT_USERNAME = "Dr7a_bot"

if not os.path.exists("downloads"): os.makedirs("downloads")

إنشاء قاعدة بيانات VIP

conn = sqlite3.connect("vip.db") c = conn.cursor() c.execute("CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY, activated_at TEXT)") conn.commit() conn.close()

weird_messages = [ "👽 جاري التواصل مع كائنات TikTok الفضائية...", "🔮 فتح بوابة الزمن الرقمي...", "🧪 خلط فيديوهات TikTok في المختبر السري...", "🐍 استدعاء تنين TikTok لتحميل الفيديو...", "📡 التقاط إشارة من سيرفرات الصين...", "🚀 تحميل الفيديو بسرعة تتجاوز سرعة الضوء... تقريبًا", "🧠 استخدام الذكاء الاصطناعي لفك شيفرة الرابط...", "📏 إدخال قرص TikTok داخل مشغل VHS الفضائي...", "👾 استدعاء روبوت التحميل من بعد آخر...", "🍕 رش جبنة على الرابط للحصول على نكهة أفضل للفيديو...", "🎩 تحويل الرابط إلى أرنب وسحبه من القبعة...", "🐢 تحميل الفيديو... بسرعة سلحفاة نينجا 🐢 (امزح، هو سريع!)" ]

user_timestamps = {} daily_limits = {} DAILY_LIMIT_FREE = 10 DAILY_LIMIT_VIP = 100

def is_vip(user_id: int): conn = sqlite3.connect("vip.db") c = conn.cursor() c.execute("SELECT 1 FROM vip_users WHERE user_id = ?", (user_id,)) result = c.fetchone() conn.close() return result is not None

def activate_vip_user(user_id: int): conn = sqlite3.connect("vip.db") c = conn.cursor() c.execute("INSERT OR IGNORE INTO vip_users (user_id, activated_at) VALUES (?, ?)", (user_id, datetime.utcnow().isoformat())) conn.commit() conn.close()

def reset_daily_limits(): current_date = datetime.utcnow().date() for user_id in list(daily_limits): if daily_limits[user_id]["date"] != current_date: daily_limits[user_id] = {"count": 0, "date": current_date}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): keyboard = [ [InlineKeyboardButton("📋 الأوامر", callback_data="commands")], [InlineKeyboardButton("🔹 معلومات VIP", callback_data="vip_info")], [InlineKeyboardButton("✅ تفعيل VIP", callback_data="activate_vip")], [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")], [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")] ] reply_markup = InlineKeyboardMarkup(keyboard)

welcome_message = (
    "👁‍✨ *أهلاً بك في البُعد الآخر من التحميل!*\n\n"
    "هل أنت مستعدّ لاختراق عوالم الفيديوهات من فيسبوك، يوتيوب، إنستغرام، وتيك توك؟ 🚀📅\n"
    "📌 فقط أرسل الرابط، وسأقوم بالباقي... لا حاجة للشرح، فقط الثقة 💼🤖\n\n"
    "🛠️ *تم بناء هذا البوت بعناية بواسطة محسن علي حسين* 🎮💻"
)

await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id reset_daily_limits() limit = DAILY_LIMIT_VIP if is_vip(user_id) else DAILY_LIMIT_FREE user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()}) remaining = limit - user_data["count"] await update.message.reply_text(f"📊 عدد التحميلات المتبقية اليوم: {remaining} من {limit}")

async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() await query.edit_message_text( "📋 قائمة الأوامر المتاحة:\n" "/start - بدء البوت من جديد\n" "/usage - عرض عدد التحميلات المتبقية اليوم\n\n" "📜 أرسل رابط فيديو من TikTok, YouTube, Facebook أو Instagram وسأقوم بتحميله لك 📆", parse_mode=ParseMode.MARKDOWN )

async def show_vip_info(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() text = ( "💎 معلومات اشتراك VIP:\n\n" "✅ تحميل غير محدود حتى 100 فيديو باليوم\n" "❌ لا انتظار بين التحميلات\n" "⚡ أولوية في السرعة\n" "🔐 دعم الملفات الخاصة\n\n" "💰 طرق الدفع:\n" "- آسياسيل\n" "- زين كاش\n" "- ماستر كارد\n\n" "📩 للاشتراك، اضغط على الزر أدناه للتواصل مع المطور" ) keyboard = [[InlineKeyboardButton("💬 تواصل مع المطور", url="https://t.me/K0_MG")]] await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def activate_vip(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query user_id = query.from_user.id activate_vip_user(user_id) await query.answer() await query.edit_message_text("✅ تم تفعيل اشتراك VIP لحسابك بنجاح! استمتع بالمميزات الكاملة 💎")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id now = time.time() url = update.message.text.strip()

if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
    await update.message.reply_text("⏳ الرجاء الانتظار قليلاً قبل إرسال رابط جديد.")
    return
user_timestamps[user_id] = now

reset_daily_limits()
limit = DAILY_LIMIT_VIP if is_vip(user_id) else DAILY_LIMIT_FREE
user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()})
if user_data["count"] >= limit:
    await update.message.reply_text("🚫 وصلت للحد الأقصى من التحميلات اليومية. الرجاء المحاولة غدًا أو الترقية إلى VIP.")
    return
daily_limits[user_id] = {"count": user_data["count"] + 1, "date": datetime.utcnow().date()}

if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com"]):
    await update.message.reply_text("❌ هذا الرابط غير مدعوم.")
    return

if "tiktok.com" in url:
    loading_msg = random.choice(weird_messages)
    await update.message.reply_text(f"{loading_msg}\n⏳ جاري تحميل الفيديو...")
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'mp4',
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ فشل التحميل من TikTok:\n{str(e)}")
    return

await update.message.reply_text("📥 جاري تحميل الفيديو، يرجى الانتظار...")

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
    await update.message.reply_text(f"❌ خطأ أثناء التحميل:\n{str(e)}")
except Exception as e:
    await update.message.reply_text(f"❌ خطأ غير متوقع:\n{str(e)}")

def main(): app = Application.builder().token(TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("usage", usage)) app.add_handler(CallbackQueryHandler(show_commands, pattern="commands")) app.add_handler(CallbackQueryHandler(show_vip_info, pattern="vip_info")) app.add_handler(CallbackQueryHandler(activate_vip, pattern="activate_vip")) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video)) app.run_polling()

if name == "main": main()

