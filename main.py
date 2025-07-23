
import os
import random
import logging
import time
import subprocess
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"
ADMIN_ID = 7249021797

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

if not os.path.exists("downloads"):
    os.makedirs("downloads")

conn = sqlite3.connect("vip_users.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY, expires_at TEXT)")
conn.commit()

user_timestamps = {}
daily_limits = {}
DAILY_LIMIT_FREE = 10
DAILY_LIMIT_VIP = 100

weird_messages = [
    "👽 جاري التواصل مع كائنات TikTok الفضائية...",
    "🧠 استخدام الذكاء الاصطناعي لفك شيفرة الرابط...",
]

def is_vip(user_id: int):
    c.execute("SELECT expires_at FROM vip_users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    return bool(row and datetime.strptime(row[0], "%Y-%m-%d") >= datetime.utcnow())

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 VIP", callback_data="vip_info")],
        [InlineKeyboardButton("📋 لوحة التحكم", callback_data="admin_panel")] if update.effective_user.id == ADMIN_ID else []
    ]
    await update.message.reply_text("مرحبا بك!", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "admin_panel" and query.from_user.id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("➕ إضافة VIP", callback_data="cmd_addvip")],
            [InlineKeyboardButton("🗑️ حذف VIP", callback_data="cmd_removevip")],
            [InlineKeyboardButton("📋 قائمة VIP", callback_data="cmd_viplist")],
            [InlineKeyboardButton("📢 إرسال تنبيه", callback_data="cmd_broadcast")]
        ]
        await query.message.reply_text("⚙️ لوحة التحكم:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "cmd_addvip":
        await query.message.reply_text("أرسل ID وعدد الأيام (مثال: 12345 30)")
        return 1
    elif query.data == "cmd_removevip":
        await query.message.reply_text("أرسل ID الذي تريد حذفه")
        return 2
    elif query.data == "cmd_viplist":
        vips = list_vips()
        if not vips:
            await query.message.reply_text("لا يوجد VIP")
        else:
            await query.message.reply_text("\n".join([f"{uid} - {exp}" for uid, exp in vips]))
    elif query.data == "cmd_broadcast":
        await query.message.reply_text("أرسل الآن الرسالة التي تريد إرسالها لكل المستخدمين")
        return 3

async def add_vip_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id, days = map(int, update.message.text.strip().split())
        add_vip(user_id, days)
        await update.message.reply_text(f"تم تفعيل VIP لـ {user_id} لمدة {days} يومًا")
    except:
        await update.message.reply_text("❌ خطأ، تحقق من الصيغة")
    return ConversationHandler.END

async def remove_vip_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        remove_vip(user_id)
        await update.message.reply_text(f"تم حذف VIP للمستخدم {user_id}")
    except:
        await update.message.reply_text("❌ خطأ، تحقق من ID")
    return ConversationHandler.END

async def broadcast_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    c.execute("SELECT user_id FROM vip_users")
    users = [row[0] for row in c.fetchall()]
    count = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, message)
            count += 1
        except:
            continue
    await update.message.reply_text(f"✅ تم إرسال التنبيه إلى {count} مستخدم.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_vip_step)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_vip_step)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
