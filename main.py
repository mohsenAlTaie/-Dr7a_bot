
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
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# توكن البوت الموحد
TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"  # استبدله إذا تغيّر
ADMIN_ID = 7249021797

# قاعدة بيانات VIP
conn = sqlite3.connect("vip_users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY, expiry TEXT)")
conn.commit()

def add_vip(user_id: int, days: int = 30):
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute("REPLACE INTO vip_users (user_id, expiry) VALUES (?, ?)", (user_id, expiry))
    conn.commit()

def remove_vip(user_id: int):
    cursor.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
    conn.commit()

def list_vips():
    cursor.execute("SELECT user_id, expiry FROM vip_users")
    return cursor.fetchall()

def get_vip_expiry(user_id: int):
    cursor.execute("SELECT expiry FROM vip_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def is_vip(user_id: int):
    expiry = get_vip_expiry(user_id)
    if expiry:
        return datetime.strptime(expiry, "%Y-%m-%d") >= datetime.now()
    return False

# إنشاء مجلد التحميل
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# رسائل غريبة عشوائية للتيك توك
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

# نظام حماية من السبام
user_timestamps = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin")] if update.effective_user.id == ADMIN_ID else [],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "👁‍🗨✨ *أهلاً بك في البُعد الآخر من التحميل!*

"
        "📎 فقط أرسل الرابط، وسأقوم بالباقي... لا حاجة للشرح، فقط الثقة 💼🤖

"
        "🛠️ *تم بناء هذا البوت بعناية بواسطة محسن علي حسين* 🎮💻"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# الإدارة
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        return await query.answer("❌ غير مصرح لك")
    keyboard = [
        [InlineKeyboardButton("➕ إضافة VIP", callback_data="add_vip")],
        [InlineKeyboardButton("🗑️ حذف VIP", callback_data="remove_vip")],
        [InlineKeyboardButton("📋 قائمة VIP", callback_data="list_vips")],
        [InlineKeyboardButton("🪪 معرف المستخدم", callback_data="get_user_id")]
    ]
    await query.message.edit_text("🎛️ *لوحة التحكم:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        return await query.answer("❌ غير مصرح لك")
    
    if query.data == "add_vip":
        context.user_data["admin_action"] = "add"
        await query.message.edit_text("🆔 أرسل رقم معرف المستخدم الذي تريد إضافته كـ VIP")
    elif query.data == "remove_vip":
        context.user_data["admin_action"] = "remove"
        await query.message.edit_text("🆔 أرسل رقم معرف المستخدم الذي تريد حذفه من VIP")
    elif query.data == "list_vips":
        vips = list_vips()
        text = "\n".join([f"🆔 {uid} - ⏳ {expiry}" for uid, expiry in vips]) or "لا يوجد أعضاء VIP"
        await query.message.edit_text(f"📋 قائمة VIP:
{text}")
    elif query.data == "get_user_id":
        await query.message.edit_text(f"🪪 معرفك: `{user_id}`", parse_mode=ParseMode.MARKDOWN)

# استقبال المعرف من الأدمن
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    action = context.user_data.get("admin_action")
    if not action:
        return

    try:
        target_id = int(update.message.text.strip())
    except:
        return await update.message.reply_text("❌ المعرف غير صحيح")

    if action == "add":
        add_vip(target_id)
        await update.message.reply_text(f"✅ تم إضافة {target_id} إلى VIP")
    elif action == "remove":
        remove_vip(target_id)
        await update.message.reply_text(f"🗑️ تم حذف {target_id} من VIP")

    context.user_data["admin_action"] = None

# تحميل الفيديوهات
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    url = update.message.text.strip()

    if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
        await update.message.reply_text("⏳ الرجاء الانتظار قليلاً قبل إرسال رابط جديد.")
        return
    user_timestamps[user_id] = now

    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "instagram", "tiktok.com"]):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم.")
        return

    if "tiktok.com" in url:
        loading_msg = random.choice(weird_messages)
        await update.message.reply_text(f"{loading_msg}
⏳ جاري تحميل الفيديو...")
        ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s','format': 'mp4','quiet': True}
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

    await update.message.reply_text("📥 جاري تحميل الفيديو، يرجى الانتظار...")
    try:
        file_path = "downloads/video.mp4"
        command = ["yt-dlp", "-f", "mp4", "-o", file_path, url]
        subprocess.run(command, check=True)
        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ:
{str(e)}")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="admin"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), handle_admin_input))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
