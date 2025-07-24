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

# إعداد قاعدة بيانات VIP
conn = sqlite3.connect("vip_users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY, expires_at TEXT)''')
conn.commit()

def add_vip(user_id: int, days: int):
    expires_at = datetime.utcnow() + timedelta(days=days)
    c.execute("INSERT OR REPLACE INTO vip_users (user_id, expires_at) VALUES (?, ?)", (user_id, expires_at.strftime('%Y-%m-%d')))
    conn.commit()

def remove_vip(user_id: int):
    c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
    conn.commit()

def list_vips():
    c.execute("SELECT user_id, expires_at FROM vip_users")
    return c.fetchall()

def is_vip(user_id: int):
    c.execute("SELECT expires_at FROM vip_users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row and datetime.strptime(row[0], "%Y-%m-%d") >= datetime.utcnow():
        return True
    return False

def get_vip_expiry(user_id: int):
    c.execute("SELECT expires_at FROM vip_users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    return row[0] if row else None

ADMIN_ID = 7249021797

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🪪 معرفي", callback_data="get_user_id")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    await update.message.reply_text("👋 أهلاً بك! استخدم الأزرار أدناه:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_user_id":
        user = query.from_user
        await query.message.reply_text(f"🪪 معرفك هو: `{user.id}`", parse_mode=ParseMode.MARKDOWN)

    elif query.data == "admin_panel" and query.from_user.id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("➕ إضافة VIP", callback_data="cmd_addvip")],
            [InlineKeyboardButton("🗑️ حذف VIP", callback_data="cmd_removevip")],
            [InlineKeyboardButton("📋 قائمة VIP", callback_data="cmd_viplist")],
            [InlineKeyboardButton("🪪 معرف المستخدم", callback_data="get_user_id")]
        ]
        await query.message.reply_text("⚙️ *لوحة التحكم الإدارية:*", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "cmd_addvip":
        await query.message.reply_text("📥 أرسل الأمر بهذا الشكل:
/addvip [id] [days]")

    elif query.data == "cmd_removevip":
        await query.message.reply_text("🗑️ أرسل الأمر بهذا الشكل:
/removevip [id]")

    elif query.data == "cmd_viplist":
        vips = list_vips()
        if not vips:
            await query.message.reply_text("❌ لا يوجد مستخدمين VIP")
        else:
            text = "\n".join([f"👤 {uid} - ينتهي بـ {exp}" for uid, exp in vips])
            await query.message.reply_text(text)

async def addvip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        add_vip(user_id, days)
        await update.message.reply_text(f"✅ تم إعطاء VIP للمستخدم {user_id} لمدة {days} يومًا.")
    except:
        await update.message.reply_text("❌ الاستخدام الصحيح:
/addvip [id] [days]")

async def removevip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        remove_vip(user_id)
        await update.message.reply_text(f"🗑️ تم إزالة VIP من المستخدم {user_id}.")
    except:
        await update.message.reply_text("❌ الاستخدام الصحيح:
/removevip [id]")

def main():
    app = Application.builder().token("YOUR_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addvip", addvip_command))
    app.add_handler(CommandHandler("removevip", removevip_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    logging.info("✅ البوت يعمل الآن.")
    app.run_polling()

if __name__ == "__main__":
    main()
