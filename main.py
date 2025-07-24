
import os
import random
import logging
import time
import subprocess
import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# إعداد اللوج
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# معلومات البوت والإدارة
TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"
ADMIN_ID = 7249021797

# قاعدة بيانات VIP
DB_NAME = "vip_users.db"
if not os.path.exists(DB_NAME):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("CREATE TABLE vip (user_id INTEGER PRIMARY KEY)")
        conn.commit()

# إنشاء مجلد التحميل
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# رسائل غريبة عشوائية للتيك توك
weird_messages = [
    "👽 جاري التواصل مع كائنات TikTok الفضائية...",
    "🔮 فتح بوابة الزمن الرقمي...",
    "🧪 خلط فيديوهات TikTok في المختبر السري...",
    "🚀 تحميل الفيديو بسرعة تتجاوز سرعة الضوء... تقريبًا",
]

user_timestamps = {}

def is_vip(user_id: int) -> bool:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute("SELECT 1 FROM vip WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")],
        [InlineKeyboardButton("فحص الاشتراك", callback_data="check_vip")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """👁‍🗨✨ *أهلاً بك في البُعد الآخر من التحميل!*

أرسل الرابط الآن لتحميل الفيديو، أو استخدم الخيارات أدناه.""",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()
    now = time.time()

    if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
        await update.message.reply_text("⏳ الرجاء الانتظار قليلاً قبل إرسال رابط جديد.")
        return
    user_timestamps[user_id] = now

    if not is_vip(user_id):
        await update.message.reply_text("❌ هذه الميزة مخصصة للمشتركين VIP فقط.")
        return

    await update.message.reply_text(random.choice(weird_messages))
    try:
        file_path = "downloads/video.mp4"
        command = ["yt-dlp", "-f", "mp4", "-o", file_path, url]
        subprocess.run(command, check=True)
        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف بعد التحميل.")
    except Exception as e:
        await update.message.reply_text(f"""❌ خطأ:
{str(e)}""")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check_vip":
        if is_vip(user_id):
            await query.edit_message_text("✅ أنت مشترك VIP.")
        else:
            await query.edit_message_text("❌ أنت لست مشترك VIP.")
    elif query.data == "admin_panel" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("➕ إضافة VIP", callback_data="add_vip")],
            [InlineKeyboardButton("🗑️ حذف VIP", callback_data="remove_vip")],
            [InlineKeyboardButton("📋 قائمة VIP", callback_data="list_vip")],
            [InlineKeyboardButton("🪪 معرف المستخدم", callback_data="get_user_id")],
        ]
        await query.edit_message_text("⚙️ لوحة التحكم:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "add_vip" and user_id == ADMIN_ID:
        context.user_data["admin_action"] = "add"
        await query.edit_message_text("🔢 أرسل الآن معرف المستخدم لإضافته VIP.")
    elif query.data == "remove_vip" and user_id == ADMIN_ID:
        context.user_data["admin_action"] = "remove"
        await query.edit_message_text("🔢 أرسل معرف المستخدم لحذفه من VIP.")
    elif query.data == "list_vip" and user_id == ADMIN_ID:
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("SELECT user_id FROM vip").fetchall()
        vip_list = "\n".join(str(row[0]) for row in rows) or "🚫 لا يوجد مشتركين VIP."
        await query.edit_message_text(f"📋 قائمة VIP:\n{vip_list}")
    elif query.data == "get_user_id":
        await query.edit_message_text(f"🪪 معرفك: {user_id}")

async def admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    action = context.user_data.get("admin_action")
    if not action:
        return

    try:
        user_id = int(update.message.text.strip())
        with sqlite3.connect(DB_NAME) as conn:
            if action == "add":
                conn.execute("INSERT OR IGNORE INTO vip(user_id) VALUES(?)", (user_id,))
                await update.message.reply_text(f"✅ تم إضافة {user_id} إلى VIP.")
            elif action == "remove":
                conn.execute("DELETE FROM vip WHERE user_id = ?", (user_id,))
                await update.message.reply_text(f"🗑️ تم حذف {user_id} من VIP.")
            conn.commit()
    except ValueError:
        await update.message.reply_text("❌ يجب أن ترسل رقم معرف صحيح.")
    context.user_data["admin_action"] = None

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & filters.USER(user_id=ADMIN_ID), admin_id_input))
    app.run_polling()

if __name__ == "__main__":
    main()
