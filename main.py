import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import asyncio

# تسجيل اللوج
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# التوكن الجديد
BOT_TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "video_vip_bot"  # غيّره إذا اختلف اسم البوت

# رسالة ترحيب فخمة وغريبة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 معلومات VIP", callback_data="vip_info")],
        [InlineKeyboardButton("🕓 معلومات الاشتراك", callback_data="vip_expiry")],
        [InlineKeyboardButton("🆔 معرفة الـ ID", callback_data="get_id")],
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👁‍🗨 مرحباً بك في البوت الغريب من المستقبل...\nاضغط الزر المناسب لتبدأ الرحلة 🔮",
        reply_markup=reply_markup
    )

# معالجة الضغط على الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "vip_info":
        await query.message.reply_text("💎 معلومات VIP:\nالباقة: ذهبية\nالميزات: تحميل سريع، عدد غير محدود.")
    elif query.data == "vip_expiry":
        await query.message.reply_text("🕓 اشتراكك ينتهي بعد: 30 يومًا.")
    elif query.data == "get_id":
        user_id = query.from_user.id
        await query.message.reply_text(f"🆔 معرفك هو:\n<code>{user_id}</code>", parse_mode="HTML")

# تشغيل البوت
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 البوت يعمل الآن...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
