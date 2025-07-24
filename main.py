import os
import random
import logging
import time
import subprocess
import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
import yt_dlp

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"
ADMIN_ID = 7249021797

if not os.path.exists("downloads"):
    os.makedirs("downloads")

if not os.path.exists("vip_users.db"):
    conn = sqlite3.connect("vip_users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

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
ADD, REMOVE = range(2)

def add_vip(user_id):
    with sqlite3.connect("vip_users.db") as conn:
        conn.execute("INSERT OR IGNORE INTO vip_users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def remove_vip(user_id):
    with sqlite3.connect("vip_users.db") as conn:
        conn.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
        conn.commit()

def list_vips():
    with sqlite3.connect("vip_users.db") as conn:
        cursor = conn.execute("SELECT user_id FROM vip_users")
        return [str(row[0]) for row in cursor.fetchall()]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "👁‍🗨✨ *أهلاً بك في البُعد الآخر من التحميل!*

"
        "هل أنت مستعدّ لاختراق عوالم الفيديوهات؟ 🚀📥
"
        "📎 فقط أرسل الرابط، وسأقوم بالباقي... 💼🤖

"
        "🛠️ *تم بناء هذا البوت بعناية بواسطة محسن علي حسين* 🎮💻"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول إلى لوحة التحكم.")
        return
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشترك", callback_data="add_user")],
        [InlineKeyboardButton("➖ حذف مشترك", callback_data="remove_user")],
        [InlineKeyboardButton("👁️ عرض المشتركين", callback_data="list_users")]
    ]
    await update.message.reply_text("📋 *لوحة التحكم الإدارية:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def control_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("❌ لا تملك صلاحية استخدام هذه الأزرار.")
        return
    if data == "add_user":
        await query.edit_message_text("🟢 أرسل آيدي المستخدم لإضافته كمشترك.")
        return ADD
    elif data == "remove_user":
        await query.edit_message_text("🔴 أرسل آيدي المستخدم لحذفه من المشتركين.")
        return REMOVE
    elif data == "list_users":
        users = list_vips()
        text = "👁️ قائمة المشتركين:
" + "
".join(users) if users else "❌ لا يوجد مشتركين."
        await query.edit_message_text(text)

async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        add_vip(user_id)
        await update.message.reply_text(f"✅ تم إضافة {user_id} للمشتركين.")
    except:
        await update.message.reply_text("❌ حدث خطأ. تأكد من إدخال آيدي صحيح.")
    return ConversationHandler.END

async def handle_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        remove_vip(user_id)
        await update.message.reply_text(f"🗑️ تم حذف {user_id} من المشتركين.")
    except:
        await update.message.reply_text("❌ حدث خطأ. تأكد من إدخال آيدي صحيح.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    url = update.message.text.strip()
    if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
        await update.message.reply_text("⏳ الرجاء الانتظار قليلاً قبل إرسال رابط جديد.")
        return
    user_timestamps[user_id] = now
    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com"]):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم.")
        return
    if "tiktok.com" in url:
        await update.message.reply_text(random.choice(weird_messages) + "
⏳ جاري تحميل الفيديو...")
        try:
            ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'mp4', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(file_path, 'rb'))
            os.remove(file_path)
        except Exception as e:
            await update.message.reply_text(f"❌ فشل التحميل:
{e}")
        return
    await update.message.reply_text("📥 جاري التحميل...")
    try:
        file_path = "downloads/video.mp4"
        subprocess.run(["yt-dlp", "-f", "mp4", "-o", file_path, url], check=True)
        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ:
{e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(control_callbacks))
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(control_callbacks)],
        states={
            ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add)],
            REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remove)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
