
import os
import random
import logging
import time
import subprocess
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)
import yt_dlp

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
BOT_USERNAME = "Dr7a_bot"
OWNER_ID = 7249021797

# قاعدة بيانات VIP
conn = sqlite3.connect("vip_users.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS vip_users (user_id INTEGER PRIMARY KEY, expires_at TEXT)")
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

user_timestamps = {}
daily_limits = {}
DAILY_LIMIT_FREE = 10
DAILY_LIMIT_VIP = 100

def reset_daily_limits():
    current_date = datetime.utcnow().date()
    for user_id in list(daily_limits):
        if daily_limits[user_id]["date"] != current_date:
            daily_limits[user_id] = {"count": 0, "date": current_date}

ADD_VIP_ID, ADD_VIP_DAYS, REMOVE_VIP_ID = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 معلومات VIP", callback_data="vip_info")],
        [InlineKeyboardButton("🕓 معلومات الاشتراك", callback_data="vip_expiry")],
        [InlineKeyboardButton("📲 معرفي", callback_data="get_user_id")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
        [InlineKeyboardButton("➕ مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/K0_MG")]
    ]
    if update.effective_user.id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    await update.message.reply_text("👁✨ مرحباً بك! أرسل رابطاً للتحميل ✨", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "admin_panel" and user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("➕ إضافة VIP", callback_data="cmd_addvip")],
            [InlineKeyboardButton("🗑️ حذف VIP", callback_data="cmd_removevip")],
            [InlineKeyboardButton("📋 قائمة VIP", callback_data="cmd_viplist")],
        ]
        await query.message.reply_text("⚙️ لوحة التحكم الإدارية:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "cmd_addvip" and user_id == OWNER_ID:
        await query.message.reply_text("📥 أرسل ID المستخدم لإعطائه VIP:")
        return ADD_VIP_ID
    elif query.data == "cmd_removevip" and user_id == OWNER_ID:
        await query.message.reply_text("🗑️ أرسل ID المستخدم لحذفه من VIP:")
        return REMOVE_VIP_ID
    elif query.data == "cmd_viplist" and user_id == OWNER_ID:
        vips = list_vips()
        if not vips:
            await query.message.reply_text("❌ لا يوجد مستخدمين VIP")
        else:
            text = "
".join([f"👤 {uid} - ينتهي في: {exp}" for uid, exp in vips])
            await query.message.reply_text(text)
    return ConversationHandler.END

async def receive_vip_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        context.user_data["vip_user_id"] = user_id
        await update.message.reply_text("⏳ أرسل عدد الأيام لإعطاء VIP:")
        return ADD_VIP_DAYS
    except:
        await update.message.reply_text("❌ معرف غير صالح. حاول مرة أخرى.")
        return ConversationHandler.END

async def receive_vip_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        user_id = context.user_data.get("vip_user_id")
        add_vip(user_id, days)
        await update.message.reply_text(f"✅ تم إعطاء VIP للمستخدم {user_id} لمدة {days} يومًا.")
    except:
        await update.message.reply_text("❌ عدد أيام غير صالح.")
    return ConversationHandler.END

async def receive_remove_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        remove_vip(user_id)
        await update.message.reply_text(f"🗑️ تم حذف VIP للمستخدم {user_id}.")
    except:
        await update.message.reply_text("❌ معرف غير صالح.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback)],
        states={
            ADD_VIP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_vip_id)],
            ADD_VIP_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_vip_days)],
            REMOVE_VIP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
