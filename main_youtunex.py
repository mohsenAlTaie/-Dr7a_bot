import os
import subprocess
import logging
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

# إعدادات البوت
TOKEN = "8377439618:AAFOg73PrKhO2I-1SIwt8pxWocV5s1I-l9U"
BOT_USERNAME = "YoutuneX_bot"

# مسار تخزين الملفات
if not os.path.exists("downloads"):
    os.makedirs("downloads")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# رسائل ترحيب غريبة وفخمة للموسيقى
welcome_messages = [
    "🎧✨ أهلاً بك في بعد الموسيقى الموازي! هنا تتحول الروابط إلى نغمات… هل أنت مستعد لاختبار قوة YoutuneX؟",
    "🚀🎶 أنت الآن في قلب موجة الصوت… أرسل رابط أغنيتك ودع YoutuneX يصنع لك موسيقى المستقبل!",
    "🌀🎵 هل سمعت من قبل أغنية سقطت من الفضاء؟ جربها هنا، وأشعر بالرفاهية الموسيقية الخارقة.",
    "🎼💎 حول يوتيوب إلى سيمفونية شخصية بصيغة MP3… مرحباً بك في YoutuneX، معقل الساوند الفاخر!"
]

# زر المطور
DEVELOPER_LINK = "https://t.me/K0_MG"
# زر البوت الثاني
VIDEO_BOT_LINK = "https://t.me/Dr7a_bot"

# دالة البدء
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome = random.choice(welcome_messages)
    keyboard = [
        [InlineKeyboardButton("🎵 حمل MP3 من يوتيوب", callback_data="how_to")],
        [InlineKeyboardButton("🎬 تحميل فيديو من جميع المواقع", url=VIDEO_BOT_LINK)],
        [InlineKeyboardButton("🤝 شارك البوت مع أصدقائك", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("💬 تواصل مع المطور", url=DEVELOPER_LINK)],
    ]
    await update.message.reply_text(
        f"{welcome}\n\n"
        "🎸 *أرسل رابط أغنيتك من يوتيوب فقط، واستمتع بالنقاء!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# رسالة شرح بسيطة تظهر عند الضغط على زر تحميل MP3
async def how_to_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎧 فقط أرسل رابط يوتيوب (فيديو أو أغنية)، وسيصلك ملف MP3 بجودة عالية مباشرة! بدون تعقيد أو خطوات زائدة.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ العودة", callback_data="back_home")]
        ])
    )

async def back_home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await start(update, context)

# دالة تحميل MP3 من يوتيوب
async def download_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    if not any(site in url for site in ["youtube.com", "youtu.be"]):
        await update.message.reply_text("❌ هذا البوت مخصص فقط لتحميل الموسيقى من يوتيوب بصيغة MP3.\nأرسل رابط يوتيوب فقط.")
        return

    # ملف مؤقت
    file_path = f"downloads/{user_id}_audio.mp3"
    await update.message.reply_text("🎼 جاري تحويل الرابط إلى MP3 بجودة عالية… انتظر لحظات السحر!")

    command = [
        "yt-dlp", "-f", "bestaudio", "--extract-audio", "--audio-format", "mp3",
        "-o", file_path, url,
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    try:
        subprocess.run(command, check=True)
        if os.path.exists(file_path):
            await update.message.reply_audio(audio=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على ملف الصوت بعد التحويل. جرب رابط آخر.")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحميل:\n{str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ غير متوقع:\n{str(e)}")

# الربط مع الأزرار والكولباك
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "how_to":
        await how_to_handler(update, context)
    elif query.data == "back_home":
        await back_home_handler(update, context)

# المين الرئيسي
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_mp3))
    app.run_polling()

if __name__ == "__main__":
    main()