
import os
import random
import logging
import time
import subprocess
import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"

if not os.path.exists("downloads"):
    os.makedirs("downloads")

DB_FILE = "vip_users.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY, expiry TIMESTAMP)")
        conn.commit()

def add_vip(user_id, days=30):
    expiry = time.time() + days * 86400
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO vip_users (user_id, expiry) VALUES (?, ?)", (user_id, expiry))
        conn.commit()

def remove_vip(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
        conn.commit()

def list_vips():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, expiry FROM vip_users")
        return c.fetchall()

def get_vip_expiry(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT expiry FROM vip_users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return result[0] if result else None

def is_vip(user_id):
    expiry = get_vip_expiry(user_id)
    return expiry and expiry > time.time()

ADMIN_ID = 7249021797
user_timestamps = {}
weird_messages = [
    "🚀 جاري التواصل مع كائنات TikTok الفضائية...",
    "🔮 فتح بوابة الزمن الرقمي...",
    "🧪 خلط فيديوهات TikTok في المختبر السري...",
    "🐉 استدعاء تنين TikTok لتحميل الفيديو...",
    "📡 التقاط إشارة من سيرفرات الصين...",
    "⚡ تحميل الفيديو بسرعة تتجاوز سرعة الضوء... تقريبًا"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("👨‍💻 المطور", url="https://t.me/K0_MG")],
        [InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")] if update.effective_user.id == ADMIN_ID else []
    ]
    text = "👋 مرحباً بك في بوت تحميل الفيديوهات المدعوم للمشتركين بنظام VIP.

📥 أرسل رابط من TikTok أو YouTube أو Facebook أو Instagram.
"

    if is_vip(update.effective_user.id):
        expiry = get_vip_expiry(update.effective_user.id)
        date_str = time.strftime("%Y-%m-%d", time.localtime(expiry))
        text += f"
✅ اشتراكك مفعل حتى: {date_str} 🎫"
    else:
        text += "
❌ حسابك غير مفعل. يرجى الاشتراك عبر المطور."

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([row for row in keyboard if row]), parse_mode=ParseMode.HTML)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if user_id != ADMIN_ID:
        return

    data = query.data
    if data == "admin_panel":
        keyboard = [
            [InlineKeyboardButton("➕ إضافة VIP", callback_data="add_vip")],
            [InlineKeyboardButton("🗑️ حذف VIP", callback_data="remove_vip")],
            [InlineKeyboardButton("📋 قائمة VIP", callback_data="list_vip")],
            [InlineKeyboardButton("🪪 معرف المستخدم", callback_data="show_userid")]
        ]
        await query.edit_message_text("⚙️ لوحة تحكم الأدمن:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "add_vip":
        context.user_data["action"] = "add_vip"
        await query.edit_message_text("✍️ أرسل معرف المستخدم لإضافته كـ VIP.")
    elif data == "remove_vip":
        context.user_data["action"] = "remove_vip"
        await query.edit_message_text("✍️ أرسل معرف المستخدم لحذفه من VIP.")
    elif data == "list_vip":
        vips = list_vips()
        text = "\n".join([f"{uid} - ينتهي: {time.strftime('%Y-%m-%d', time.localtime(exp))}" for uid, exp in vips]) or "❌ لا يوجد مشتركين حالياً."
        await query.edit_message_text(f"📋 قائمة VIP:
{text}")
    elif data == "show_userid":
        await query.edit_message_text(f"🪪 معرفك: `{user_id}`", parse_mode=ParseMode.MARKDOWN)

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    action = context.user_data.get("action")
    if not action:
        return

    try:
        target_id = int(update.message.text.strip())
        if action == "add_vip":
            add_vip(target_id)
            await update.message.reply_text("✅ تم إضافة المستخدم بنجاح إلى VIP.")
        elif action == "remove_vip":
            remove_vip(target_id)
            await update.message.reply_text("🗑️ تم حذف المستخدم من VIP.")
    except:
        await update.message.reply_text("⚠️ تأكد من كتابة المعرف بشكل صحيح.")
    context.user_data["action"] = None

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_vip(user_id) and user_id != ADMIN_ID:
        await update.message.reply_text("🔒 هذا البوت مخصص للمشتركين فقط. راسل المطور للاشتراك.")
        return

    now = time.time()
    url = update.message.text.strip()
    if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
        await update.message.reply_text("⏳ يرجى الانتظار قليلاً قبل إرسال رابط جديد.")
        return
    user_timestamps[user_id] = now

    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com"]):
        await update.message.reply_text("❌ الرابط غير مدعوم حالياً.")
        return

    if "tiktok.com" in url:
        await update.message.reply_text(f"{random.choice(weird_messages)}
⏳ جاري التحميل...")
        ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'mp4', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(file_path, 'rb'))
            os.remove(file_path)
        except Exception as e:
            await update.message.reply_text(f"❌ فشل التحميل:
{str(e)}")
        return

    await update.message.reply_text("📥 جاري تحميل الفيديو...")
    try:
        file_path = "downloads/video.mp4"
        subprocess.run(["yt-dlp", "-f", "mp4", "-o", file_path, url], check=True)
        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ:
{str(e)}")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_input))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
