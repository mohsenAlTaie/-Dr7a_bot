import os
import sqlite3
import logging
import random
import time
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import yt_dlp

BOT_TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
ADMIN_ID = 7249021797

DOWNLOADS_DIR = "downloads"
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

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
SPAM_WAIT_SECONDS = 60
MAX_DAILY_DOWNLOADS = 10

def is_vip(user_id: int) -> bool:
    c.execute("SELECT vip_expiry FROM vip_users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        expiry_str = row[0]
        expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
        if expiry_dt > datetime.now():
            return True
        else:
            c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
            conn.commit()
            return False
    return False

def add_user_if_not_exists(user_id: int):
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
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
        c.execute("UPDATE users SET daily_downloads = daily_downloads + 1, last_download_time = ? WHERE user_id = ?", (now_ts, user_id))
        conn.commit()

def add_points(user_id: int, pts: int):
    add_user_if_not_exists(user_id)
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (pts, user_id))
    conn.commit()

def get_user_points(user_id: int) -> int:
    add_user_if_not_exists(user_id)
    c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    return row[0] if row else 0

def use_points(user_id: int, pts: int) -> bool:
    current = get_user_points(user_id)
    if current >= pts:
        c.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (pts, user_id))
        conn.commit()
        return True
    return False

def list_vip_users():
    c.execute("SELECT user_id, vip_expiry FROM vip_users")
    return c.fetchall()

def add_vip(user_id: int, days: int = 30):
    expiry = datetime.now() + timedelta(days=days)
    c.execute(
        "REPLACE INTO vip_users (user_id, vip_expiry) VALUES (?, ?)",
        (user_id, expiry.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()

def remove_vip(user_id: int):
    c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
    conn.commit()

def download_media(url: str, format_code: str = None) -> str:
    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOADS_DIR, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "format": format_code or "best",
        "noplaylist": True,
        "retries": 3,
        "cachedir": False,
        "nooverwrites": True,
    }

    if "facebook.com" in url:
        cookie_path = "facebook_cookies.txt"
    elif "instagram.com" in url:
        cookie_path = "instagram_cookies.txt"
    elif "youtube.com" in url or "youtu.be" in url:
        cookie_path = "youtube_cookies.txt"
    else:
        cookie_path = None

    if cookie_path and os.path.isfile(cookie_path):
        ydl_opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"خطأ في تحميل الفيديو: {e}")
        return None

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

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data

    if data == "show_id":
        await query.edit_message_text(f"🔢 معرفك في البوت هو: `{user_id}`", parse_mode="Markdown")

    elif data == "earn_points":
        bot_username = context.bot.username
        bot_link = f"https://t.me/{bot_username}"
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

async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_action"):
        # نمنع التحميل إذا نحن بانتظار إدخال إداري (مثل إضافة VIP)
        return

    url = update.message.text.strip()
    user_id = update.effective_user.id

    add_user_if_not_exists(user_id)

    can_dl, msg = can_download(user_id)
    if not can_dl:
        await update.message.reply_text(msg)
        return

    await update.message.reply_text("⏳ جارٍ تحميل الفيديو... انتظر قليلاً.")
    filepath = download_media(url)
    if filepath and os.path.isfile(filepath):
        with open(filepath, "rb") as video_file:
            await update.message.reply_document(document=video_file)
        record_download(user_id)
        os.remove(filepath)
    else:
        await update.message.reply_text("❌ حدث خطأ أثناء التحميل.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user_if_not_exists(user_id)
    if is_vip(user_id):
        text = random.choice(VIP_WELCOME_MESSAGES) + "\n\n🎉 أنت عضو VIP وتم تفعيل التحميل بلا حدود وسرعة التحميل العالية."
    else:
        text = random.choice(WELCOME_MESSAGES)
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(user_id))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "أرسل رابط فيديو من YouTube أو TikTok أو Facebook أو Instagram لتحميله.\n"
        "لـ YouTube يمكنك اختيار صيغة التحميل (صوت فقط، فيديو، أو شورت).\n"
        "يمكنك الضغط على الأزرار للتحكم في حسابك أو الاشتراك في VIP.\n"
        "المستخدم العادي محدود بـ10 تحميلات يومياً مع انتظار 60 ثانية بين كل تحميل.\n"
        "VIP تحميل غير محدود وتسريع تحميل.\n"
        "/start - لبدء المحادثة\n"
        "/help - لعرض هذه المساعدة\n"
    )
    await update.message.reply_text(help_text)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), admin_text_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
