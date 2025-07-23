import os
import random
import logging
import time
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد اللوج
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# توكن البوت الموحد
TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"

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

# رسالة /start موحدة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = (
        "👁‍🗨✨ *أهلاً بك في البُعد الآخر من التحميل!*\n\n"
        "هل أنت مستعدّ لاختراق عوالم الفيديوهات من فيسبوك، يوتيوب، إنستغرام، وتيك توك؟ 🚀📥\n"
        "هنا حيث تنصهر الروابط وتولد الملفات! 🌐🔥\n\n"
        "📎 فقط أرسل الرابط، وسأقوم بالباقي... لا حاجة للشرح، فقط الثقة 💼🤖\n\n"
        "🛠️ *تم بناء هذا البوت بعناية بواسطة محسن علي حسين* 🎮💻"
    )

    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# الدالة الأساسية لتحليل وتحميل الفيديو
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    url = update.message.text.strip()

    # حماية من السبام
    if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
        await update.message.reply_text("⏳ الرجاء الانتظار قليلاً قبل إرسال رابط جديد.")
        return
    user_timestamps[user_id] = now

    # التحقق من الرابط
    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "instagram", "tiktok.com"]):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم. أرسل رابط من YouTube أو Facebook أو Instagram أو TikTok.")
        return

    # TikTok برسالة خاصة
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

    # باقي المواقع
    await update.message.reply_text("📥 جاري تحميل الفيديو، يرجى الانتظار...")

    try:
        file_path = "downloads/video.mp4"
        command = ["yt-dlp", "-f", "mp4"]

        # كوكيز المواقع
        if "facebook.com" in url or "fb.watch" in url:
            command += ["--cookies", "cookies_facebook.txt"]
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
        await update.message.reply_text(f"❌ خطأ أثناء تحميل الفيديو:\n{str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ غير متوقع:\n{str(e)}")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
