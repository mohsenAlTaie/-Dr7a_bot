import os import random import logging import time import subprocess from datetime import datetime from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton from telegram.constants import ParseMode from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes import yt_dlp

إعداد اللوج

logging.basicConfig( format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO )

توكن البوت

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU" BOT_USERNAME = "Dr7a_bot"

إنشاء مجلد التحميل

if not os.path.exists("downloads"): os.makedirs("downloads")

رسائل غريبة عشوائية للتيك توك

weird_messages = [ "👽 جاري التواصل مع كائنات TikTok الفضائية...", "🔮 فتح بوابة الزمن الرقمي...", "🧪 خلط فيديوهات TikTok في المختبر السري...", "🐍 استدعاء تنين TikTok لتحميل الفيديو...", "📡 التقاط إشارة من سيرفرات الصين...", "🚀 تحميل الفيديو بسرعة تتجاوز سرعة الضوء... تقريبًا", "🧠 استخدام الذكاء الاصطناعي لفك شيفرة الرابط...", "📏 إدخال قرص TikTok داخل مشغل VHS الفضائي...", "👾 استدعاء روبوت التحميل من بعد آخر...", "🍕 رش جبنة على الرابط للحصول على نكهة أفضل للفيديو...", "🎩 تحويل الرابط إلى أرنب وسحبه من القبعة...", "🐢 تحميل الفيديو... بسرعة سلحفاة نينجا 🐢 (امزح، هو سريع!)" ]

نظام حماية من السبام

user_timestamps = {}

عداد التحميلات اليومية

daily_limits = {} DAILY_LIMIT = 10 vip_users_file = "vip_users.txt"

إعادة تعيين الحد اليومي

def reset_daily_limits(): current_date = datetime.utcnow().date() for user_id in list(daily_limits): if daily_limits[user_id]["date"] != current_date: daily_limits[user_id] = {"count": 0, "date": current_date}

التحقق من صلاحية VIP

def is_vip(user_id): if not os.path.exists(vip_users_file): return False with open(vip_users_file, "r") as f: return str(user_id) in f.read()

رسالة /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): keyboard = [ [InlineKeyboardButton("📋 الأوامر", callback_data="commands")], [InlineKeyboardButton("🔑 تفعيل VIP", callback_data="activate_vip")], [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")], [InlineKeyboardButton("👨‍💻 المطور", url="https://t.me/K0_MG")], [InlineKeyboardButton("💳 طرق الدفع", callback_data="vip_info")], ] reply_markup = InlineKeyboardMarkup(keyboard)

welcome_message = (
    "👁‍✨ *أهلاً بك في البُعد الآخر من التحميل!*\n\n"
    "هل أنت مستعدّ لاختراق عوالم الفيديوهات من فيسبوك، يوتيوب، إنستغرام، وتيك توك؟ 🚀📅\n"
    "هنا حيث تنصهر الروابط وتولد الملفات! 🌐🔥"
)
await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

عرض عدد التحميلات المتبقية

async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id reset_daily_limits() user_data = daily_limits.get(user_id, {"count": 0, "date": datetime.utcnow().date()}) remaining = DAILY_LIMIT - user_data["count"] await update.message.reply_text(f"📊 عدد التحميلات المتبقية اليوم: {remaining} من {DAILY_LIMIT}")

الرد على الأزرار

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() data = query.data

if data == "commands":
    await query.edit_message_text(
        "📋 *قائمة الأوامر:*\n"
        "/start - بدء البوت\n"
        "/usage - عرض التحميلات المتبقية\n\n"
        "🗒 أرسل رابط من TikTok, YouTube, Facebook أو Instagram وسنقوم بتحميله لك",
        parse_mode=ParseMode.MARKDOWN
    )
elif data == "vip_info":
    await query.edit_message_text(
        "💳 *معلومات اشتراك VIP:*\n\n"
        "- رفع الحد اليومي إلى عدد غير محدود\n"
        "- سرعة تحميل أفضل\n"
        "- دعم المطور وميزات أضافية\n\n"
        "💳 طرق الدفع:\n- آسياسيل\n- ماستر كارد\n- زين كاش\n\n"
        "✨ للاشتراك اضغط هنا وتواصل مع المطور: @K0_MG",
        parse_mode=ParseMode.MARKDOWN
    )
elif data == "activate_vip":
    user_id = update.effective_user.id
    if is_vip(user_id):
        await query.edit_message_text("✅ تم تفعيل VIP لحسابك. ستحصل على مميزات التحميل غير المحدودة!")
        daily_limits[user_id] = {"count": 0, "date": datetime.utcnow().date()}
    else:
        await query.edit_message_text("❌ لست مشتركًا في VIP. يرجى التواصل مع المطور @K0_MG للاشتراك.")

باقي كود التحميل كما هو (handle_video، وغيرها) بدون تغيير

تشغيل البوت

def main(): app = Application.builder().token(TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("usage", usage)) app.add_handler(CallbackQueryHandler(handle_buttons)) # إضافة باقي الهاندلرات هنا... app.run_polling()

if name == "main": main()

