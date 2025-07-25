import os
import random
import logging
import time
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import yt_dlp
import subprocess

# إعداد اللوج
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات البوت
TOKEN = "8444492438:AAGH0f5wTCYiie3Vhv9d8rlv1i4LvR6VMW4"
BOT_USERNAME = "Dr7a_bot"
ADMIN_ID = 7249021797

DOWNLOADS_DIR = "downloads"
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# إعداد قاعدة بيانات SQLite
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    daily_downloads INTEGER DEFAULT 0,
    last_download_time INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS vip_users (
    user_id INTEGER PRIMARY KEY,
    vip_expiry TEXT
)
""")
conn.commit()

user_timestamps = {}

WELCOME_MESSAGES = [
    "🔥 نظام التحميل مفتوح... أدخل رابطك وخلي السرعة تشتغل.",
    "👾 دخلت المنطقة المحظورة... أرسل الرابط يا قرصان.",
    "🚀 استعد للتحميل السريع... هيا أرسل الرابط.",
    "🛸 بوت التحميل الفضائي هنا، شاركنا رابط الفيديو.",
    "🕵️‍♂️ الكنز الرقمي بين يديك، أرسل الرابط."
]

VIP_WELCOME_MESSAGES = [
    "✨ أهلاً يا VIP! التحميل عندك بلا حدود ولا انتظار.",
    "👑 مرحباً بالسيد المحترف، سرعة التحميل معك الآن.",
    "⚡ VIP يا غالي، التحميل صاروخي بدون تأخير!",
]

VIP_PRICE = "5,000 دينار عراقي"
SPAM_WAIT_SECONDS = 10
MAX_DAILY_DOWNLOADS = 10

# دوال قاعدة البيانات

def is_vip(user_id: int) -> bool:
    c.execute("SELECT vip_expiry FROM vip_users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        expiry_dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if expiry_dt > datetime.now():
            return True
        else:
            c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
            conn.commit()
    return False

def add_user_if_not_exists(user_id: int):
    c.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def can_download(user_id: int) -> (bool, str):
    add_user_if_not_exists(user_id)
    if is_vip(user_id):
        return True, ""
    c.execute("SELECT daily_downloads, last_download_time FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    daily_downloads, last_time = row
    now_ts = int(time.time())
    if daily_downloads >= MAX_DAILY_DOWNLOADS:
        return False, "❌ وصلت الحد اليومي 10 تحميلات.\nاشترك في VIP لتحميل بلا حدود."
    if now_ts - last_time < SPAM_WAIT_SECONDS:
        remaining = SPAM_WAIT_SECONDS - (now_ts - last_time)
        return False, f"⏱️ انتظر قليلاً، تستطيع التحميل بعد {remaining} ثانية."
    return True, ""

def record_download(user_id: int):
    add_user_if_not_exists(user_id)
    if not is_vip(user_id):
        now_ts = int(time.time())
        c.execute(
            "UPDATE users SET daily_downloads = daily_downloads + 1, last_download_time = ? WHERE user_id = ?",
            (now_ts, user_id)
        )
        conn.commit()

def add_vip(user_id: int, days: int = 30):
    expiry = datetime.now() + timedelta(days=days)
    c.execute("REPLACE INTO vip_users (user_id, vip_expiry) VALUES (?, ?)",
              (user_id, expiry.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def remove_vip(user_id: int):
    c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
    conn.commit()

def list_vip_users():
    c.execute("SELECT user_id, vip_expiry FROM vip_users")
    return c.fetchall()

def main_menu_keyboard(user_id: int):
    buttons = [
        [InlineKeyboardButton("🔢 معرفي (ID)", callback_data="show_id")],
        [InlineKeyboardButton("🎰 اكسب تحميلات مجانية!", callback_data="earn_points")],
        [InlineKeyboardButton("🛡️ مميزات VIP", callback_data="show_vip_features")],
        [InlineKeyboardButton("💳 اشترك الآن", callback_data="subscribe_now")],
    ]
    if is_vip(user_id):
        buttons.append([InlineKeyboardButton("⚡️ تسريع التحميل", callback_data="speed_up")])
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

# أمر /start مع مشاركة البوت وأزرار المطور
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user_if_not_exists(user_id)
    keyboard = [
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_vip(user_id):
        text = random.choice(VIP_WELCOME_MESSAGES) + "\n\n🎉 أنت عضو VIP وتم تفعيل التحميل بلا حدود وسرعة التحميل العالية."
    else:
        text = (
            "👁‍🗨✨ *أهلاً بك في البُعد الآخر من التحميل!*\n\n"
            "هل أنت مستعدّ لاختراق عوالم الفيديوهات من فيسبوك، يوتيوب، إنستغرام، وتيك توك؟ 🚀📥\n"
            "هنا حيث تنصهر الروابط وتولد الملفات! 🌐🔥\n\n"
            "📎 فقط أرسل الرابط، وسأقوم بالباقي... لا حاجة للشرح، فقط الثقة 💼🤖\n\n"
            "🛠️ *تم بناء هذا البوت بعناية بواسطة محسن علي حسين* 🎮💻"
        )

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# معالج الأزرار
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data

    if data == "show_id":
        await query.edit_message_text(f"🔢 معرفك في البوت هو: `{user_id}`", parse_mode="Markdown")

    elif data == "earn_points":
        bot_link = f"https://t.me/{BOT_USERNAME}"
        text = (
            "🎰 اكسب تحميلات مجانية!\n\n"
            "شارك البوت مع 3 أصدقاء لتحصل على 3 نقاط (= 3 تحميلات مجانية).\n"
            "اضغط زر المشاركة بالأسفل."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("شارك البوت", url=bot_link)],
            [InlineKeyboardButton("↩️ العودة", callback_data="back_main")],
        ])
        await query.edit_message_text(text, reply_markup=keyboard)

    elif data == "show_vip_features":
        await query.edit_message_text(
            "مميزات VIP:\n"
            "- تحميل غير محدود\n"
            "- سرعة تحميل أعلى\n"
            f"- السعر: {VIP_PRICE}\n"
            "للاشتراك تواصل مع المطور @K0_MG",
        )

    elif data == "subscribe_now":
        await query.edit_message_text(
            "للاشتراك VIP، اضغط زر الدفع التالي وتواصل مع المطور.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 اشترك VIP الآن", url="https://t.me/K0_MG")]]),
        )

    elif data == "speed_up":
        if is_vip(user_id):
            await query.edit_message_text("⚡️ تم تفعيل تسريع التحميل. عند إرسال الرابط التالي، سيتم تحميل الملف بأقصى سرعة دون انتظار.")
        else:
            await query.edit_message_text("❌ فقط المشتركين VIP يمكنهم استخدام تسريع التحميل.")

    elif data == "admin_panel" and user_id == ADMIN_ID:
        buttons = [
            [InlineKeyboardButton("➕ إضافة VIP", callback_data="admin_add_vip")],
            [InlineKeyboardButton("🗑️ حذف VIP", callback_data="admin_remove_vip")],
            [InlineKeyboardButton("📋 قائمة VIP", callback_data="admin_list_vip")],
            [InlineKeyboardButton("↩️ العودة", callback_data="back_main")],
        ]
        await query.edit_message_text("⚙️ لوحة تحكم الإدارة", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_add_vip" and user_id == ADMIN_ID:
        await query.edit_message_text("📥 أرسل معرف المستخدم الذي تريد إضافة VIP له:")
        context.user_data["admin_action"] = "add_vip"

    elif data == "admin_remove_vip" and user_id == ADMIN_ID:
        await query.edit_message_text("🗑️ أرسل معرف المستخدم الذي تريد حذف VIP له:")
        context.user_data["admin_action"] = "remove_vip"

    elif data == "admin_list_vip" and user_id == ADMIN_ID:
        vips = list_vip_users()
        if not vips:
            await query.edit_message_text("📋 لا يوجد مستخدمين VIP حالياً.")
        else:
            text = "📋 قائمة مستخدمي VIP:\n"
            for uid, expiry in vips:
                text += f"- {uid} | ينتهي: {expiry}\n"
            await query.edit_message_text(text)

    elif data == "back_main":
        await query.edit_message_text(
            random.choice(VIP_WELCOME_MESSAGES) if is_vip(user_id) else random.choice(WELCOME_MESSAGES),
            reply_markup=main_menu_keyboard(user_id),
        )
    else:
        await query.edit_message_text("⚠️ خيار غير معروف.")

# إدارة النص الإداري (إضافة/حذف VIP)
async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    action = context.user_data.get("admin_action")
    if not action:
        return
    text = update.message.text.strip()
    if action == "add_vip":
        if not text.isdigit():
            await update.message.reply_text("❌ المعرف يجب أن يكون رقم فقط.")
            return
        add_vip(int(text))
        await update.message.reply_text(f"✅ تمت إضافة VIP للمستخدم {text} لمدة 30 يوم.")
        context.user_data["admin_action"] = None
    elif action == "remove_vip":
        if not text.isdigit():
            await update.message.reply_text("❌ المعرف يجب أن يكون رقم فقط.")
            return
        remove_vip(int(text))
        await update.message.reply_text(f"✅ تم إزالة VIP من المستخدم {text}.")
        context.user_data["admin_action"] = None

# تحميل الفيديو مع دعم TikTok والتحميل العام
async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    url = update.message.text.strip()

    # حماية سبام 10 ثواني
    if user_id in user_timestamps and now - user_timestamps[user_id] < SPAM_WAIT_SECONDS:
        await update.message.reply_text(f"⏳ الرجاء الانتظار {int(SPAM_WAIT_SECONDS - (now - user_timestamps[user_id]))} ثانية قبل إرسال رابط جديد.")
        return
    user_timestamps[user_id] = now

    # منع تحميل أثناء إدخال إداري
    if context.user_data.get("admin_action"):
        return

    add_user_if_not_exists(user_id)

    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "instagram", "tiktok.com"]):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم. أرسل رابط من YouTube أو Facebook أو Instagram أو TikTok.")
        return

    # TikTok مع رسائل عشوائية
    if "tiktok.com" in url:
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
        loading_msg = random.choice(weird_messages)
        await update.message.reply_text(f"{loading_msg}\n⏳ جاري تحميل الفيديو...")
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOADS_DIR, '%(id)s.%(ext)s'),
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

    # باقي المواقع بالتحميل عبر yt-dlp subprocess
    await update.message.reply_text("📥 جاري تحميل الفيديو، يرجى الانتظار...")

    try:
        file_path = os.path.join(DOWNLOADS_DIR, "video.mp4")
        command = ["yt-dlp", "-f", "mp4", "-o", file_path, url]
        subprocess.run(command, check=True)

        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف بعد التحميل.")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ خطأ أثناء تحميل الفيديو:\n{str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ غير متوقع:\n{str(e)}")

# أمر /help بسيط
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "أرسل رابط فيديو من YouTube أو TikTok أو Facebook أو Instagram لتحميله.\n"
        "المستخدم العادي محدود بـ10 تحميلات يومياً مع انتظار 10 ثوانٍ بين كل تحميل.\n"
        "VIP تحميل غير محدود وتسريع تحميل.\n"
        "/start - لبدء المحادثة\n"
        "/help - لعرض هذه المساعدة\n"
    )
    await update.message.reply_text(help_text)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), admin_text_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
