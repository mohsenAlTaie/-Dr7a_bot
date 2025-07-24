
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
        [InlineKeyboardButton("📲 معرفي", callback_data="get_user_id")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    if update.effective_user.id == 7249021797:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
    "👁✨ أهلاً بك في البُعد الآخر من التحميل! ✨👁\n"
    "🚀 هل أنت مستعد لاختراق عوالم الفيديوهات؟\n"
    "🔗 فقط أرسل الرابط، وسأقوم بالباقي!\n"
    "🛠 تم بناء هذا البوت بعناية بواسطة محسن علي حسين 🎮💻"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# لاحقاً سأعيد إضافة باقي الدوال هنا، لأنها طويلة وسيتم حفظ الملف بالكامل بعد هذا الجزء

# تشغيل البوت بـ webhook
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=f"https://{os.environ['RAILWAY_STATIC_URL']}/"
    )

if __name__ == "__main__":
    main()

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
        "💎 *معلومات اشتراك VIP:*

"
        "✅ تحميل فيديوهات بلا حدود
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

async def add_vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != "7249021797":
        return
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        add_vip(user_id, days)
        await update.message.reply_text(f"✅ تم إعطاء VIP للمستخدم {user_id} لمدة {days} يومًا")
    except:
        await update.message.reply_text("❌ الاستخدام الصحيح: /addvip [id] [days]")

async def remove_vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != "7249021797":
        return
    try:
        user_id = int(context.args[0])
        remove_vip(user_id)
        await update.message.reply_text(f"❌ تم حذف VIP للمستخدم {user_id}")
    except:
        await update.message.reply_text("❌ الاستخدام الصحيح: /removevip [id]")

async def vip_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != "7249021797":
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
    elif query.data == "my_stats":
        user_id = query.from_user.id
        reset_daily_limits()
        limit = DAILY_LIMIT_VIP if is_vip(user_id) else DAILY_LIMIT_FREE
        user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()})
        await query.message.reply_text(f"📊 عدد تحميلاتك اليوم: {user_data['count']} / {limit}")
    elif query.data == "vip_info":
        await show_vip_info(update, context)
    elif query.data == "vip_expiry":
        await show_expiry(update, context)
    elif query.data == "admin_panel":
        if query.from_user.id != 7249021797:
            await query.message.reply_text("❌ هذا الخيار مخصص فقط للإدارة.")
            return
        keyboard = [
            [InlineKeyboardButton("➕ إضافة VIP", callback_data="cmd_addvip")],
            [InlineKeyboardButton("🗑️ حذف VIP", callback_data="cmd_removevip")],
            [InlineKeyboardButton("📋 قائمة VIP", callback_data="cmd_viplist")]
        ]
        await query.message.reply_text("⚙️ *لوحة التحكم الإدارية:*", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "cmd_addvip":
        await query.message.reply_text("📝 أرسل الأمر بهذا الشكل:
`/addvip user_id days`", parse_mode=ParseMode.MARKDOWN)
    elif query.data == "cmd_removevip":
        await query.message.reply_text("🗑️ أرسل الأمر بهذا الشكل:
`/removevip user_id`", parse_mode=ParseMode.MARKDOWN)
    elif query.data == "cmd_viplist":
        vips = list_vips()
        if not vips:
            await query.message.reply_text("❌ لا يوجد مستخدمين VIP")
        else:
            text = "\n".join([f"👤 {uid} - ينتهي بـ {exp}" for uid, exp in vips])
            await query.message.reply_text(text)

