import os
import sqlite3
import logging
import random
import time
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

import yt_dlp

# إعداد اللوج لسهولة تتبع الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# توكن البوت والمعرف الأدمن
TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
ADMIN_ID = 7249021797

# إنشاء مجلد للتحميلات إن لم يكن موجوداً
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# اتصال بقاعدة بيانات SQLite (ملف bot_data.db)
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول لو غير موجودة
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    downloads_today INTEGER DEFAULT 0,
    last_download_time INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    free_downloads INTEGER DEFAULT 0,
    last_reset TEXT DEFAULT ''
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vip_users (
    user_id INTEGER PRIMARY KEY,
    vip_expiry TEXT
)
""")
conn.commit()

WELCOME_MESSAGES = [
    "🔥 نظام التحميل مفتوح... أدخل رابطك وخلي السرعة تشتغل.",
    "👾 دخلت المنطقة المحظورة... أرسل الرابط يا قرصان.",
    "⚡️ سرعة الصاروخ جاهزة، أرسل رابط الفيديو!",
    "🎮 حان وقت تحميل الفيديوهات، شارك الرابط!",
    "🌪️ العاصفة الرقمية بدأت، رابطك بعد؟"
]

DAILY_LIMIT = 10
SPAM_DELAY = 60


def is_vip(user_id: int) -> bool:
    cursor.execute("SELECT vip_expiry FROM vip_users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row:
        expiry_str = row[0]
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)
                if expiry > datetime.now():
                    return True
                else:
                    cursor.execute("DELETE FROM vip_users WHERE user_id=?", (user_id,))
                    conn.commit()
            except:
                # إذا شكل التاريخ غير صحيح، نحذفه كإجراء أمان
                cursor.execute("DELETE FROM vip_users WHERE user_id=?", (user_id,))
                conn.commit()
    return False


def get_user(user_id: int):
    cursor.execute("SELECT downloads_today, last_download_time, points, free_downloads, last_reset FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row:
        downloads_today, last_download_time, points, free_downloads, last_reset = row
        return {
            "downloads_today": downloads_today,
            "last_download_time": last_download_time,
            "points": points,
            "free_downloads": free_downloads,
            "last_reset": last_reset
        }
    else:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return {
            "downloads_today": 0,
            "last_download_time": 0,
            "points": 0,
            "free_downloads": 0,
            "last_reset": ''
        }


def update_user(user_id: int, **kwargs):
    fields = []
    values = []
    for key, val in kwargs.items():
        fields.append(f"{key}=?")
        values.append(val)
    values.append(user_id)
    sql = f"UPDATE users SET {', '.join(fields)} WHERE user_id=?"
    cursor.execute(sql, values)
    conn.commit()


def reset_daily_counts():
    now_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT user_id, last_reset FROM users")
    users = cursor.fetchall()
    for user_id, last_reset in users:
        if last_reset != now_str:
            cursor.execute(
                "UPDATE users SET downloads_today=0, last_reset=? WHERE user_id=?",
                (now_str, user_id),
            )
    conn.commit()


def can_download(user_id: int, is_vip_user: bool) -> (bool, str):
    user = get_user(user_id)
    now_ts = int(time.time())
    if not is_vip_user:
        last_time = user["last_download_time"]
        if now_ts - last_time < SPAM_DELAY:
            wait_time = SPAM_DELAY - (now_ts - last_time)
            return False, f"⏱️ انتظر شوي حبي، تقدر تحمل بعد {wait_time} ثانية."
    return True, ""


def can_download_limit(user_id: int, is_vip_user: bool) -> (bool, str):
    user = get_user(user_id)
    reset_daily_counts()
    if not is_vip_user:
        total_allowed = DAILY_LIMIT + user["free_downloads"]
        if user["downloads_today"] >= total_allowed:
            return False, "❌ وصلت الحد اليومي. اشترك في VIP للتحميل بلا حدود."
    return True, ""


def after_download_success(user_id: int):
    user = get_user(user_id)
    now_ts = int(time.time())
    new_downloads = user["downloads_today"] + 1
    new_free_downloads = max(0, user["free_downloads"] - 1) if user["free_downloads"] > 0 else 0
    update_user(
        user_id,
        downloads_today=new_downloads,
        last_download_time=now_ts,
        free_downloads=new_free_downloads
    )


def add_points(user_id: int, points_to_add: int):
    user = get_user(user_id)
    new_points = user["points"] + points_to_add
    update_user(user_id, points=new_points)


def use_point_for_free_download(user_id: int) -> bool:
    user = get_user(user_id)
    if user["points"] >= 3:
        new_points = user["points"] - 3
        new_free_downloads = user["free_downloads"] + 3
        update_user(user_id, points=new_points, free_downloads=new_free_downloads)
        return True
    return False


def random_welcome():
    return random.choice(WELCOME_MESSAGES)


def main_keyboard(is_vip_user: bool):
    buttons = [
        [InlineKeyboardButton("🔹 معرفي (ID)", callback_data="show_id")],
        [InlineKeyboardButton("🎰 اكسب تحميلات مجانية!", callback_data="earn_points")],
        [InlineKeyboardButton("⭐️ مميزات VIP", callback_data="vip_features")],
        [InlineKeyboardButton("🛒 اشترك الآن (5 ألف عراقي)", url="https://t.me/K0_MG")],
    ]
    if is_vip_user:
        buttons.append([InlineKeyboardButton("⏩ تسريع التحميل", callback_data="speed_up")])
    if ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)


def admin_keyboard():
    buttons = [
        [InlineKeyboardButton("➕ إضافة VIP", callback_data="admin_add_vip")],
        [InlineKeyboardButton("🗑️ حذف VIP", callback_data="admin_remove_vip")],
        [InlineKeyboardButton("📋 قائمة المشتركين", callback_data="admin_list_users")],
    ]
    return InlineKeyboardMarkup(buttons)


async def download_media(url: str, download_type: str = "video") -> str:
    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
    }

    if download_type == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "outtmpl": "downloads/%(id)s.mp3",
        })
    elif download_type == "shorts":
        ydl_opts.update({
            "format": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "noplaylist": True,
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logging.error(f"Download error: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    vip_status = is_vip(user_id)
    text = random_welcome()
    if vip_status:
        text += "\n\n🎉 أنت مشترك VIP! استمتع بالتحميل بدون حدود وبسرعة عالية."
    else:
        text += f"\n\n🚦 الحد اليومي للمستخدم العادي هو {DAILY_LIMIT} تحميلات."
    keyboard = main_keyboard(vip_status)
    await update.message.reply_text(text, reply_markup=keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    vip_status = is_vip(user_id)

    if query.data == "show_id":
        await query.answer()
        await query.edit_message_text(f"🆔 معرفك في تيليجرام هو: <code>{user_id}</code>", parse_mode=ParseMode.HTML)

    elif query.data == "earn_points":
        await query.answer()
        text = ("🎯 شارك البوت مع 3 أصدقاء لتحصل على 3 نقاط = 3 تحميلات مجانية!\n\n"
                "✅ بعد المشاركة، أرسل لي رابط فيديو لتحميله مجاناً!")
        await query.edit_message_text(text, reply_markup=main_keyboard(vip_status))

    elif query.data == "vip_features":
        await query.answer()
        text = ("🌟 مميزات VIP:\n"
                "- تحميل غير محدود.\n"
                "- سرعة تحميل أعلى مع زر تسريع التحميل.\n"
                "- لا قيود زمنية بين التحميلات.\n"
                "- دعم خاص من المطور.\n\n"
                "اشترك الآن للاستفادة من المميزات!")
        await query.edit_message_text(text, reply_markup=main_keyboard(vip_status))

    elif query.data == "speed_up":
        await query.answer("✅ تم تفعيل تسريع التحميل!")
        context.user_data["speed_up"] = True
        await query.edit_message_text("⏩ تم تفعيل تسريع التحميل! أرسل رابط الفيديو لتحميله بسرعة عالية.")

    elif query.data == "admin_panel":
        if user_id == ADMIN_ID:
            await query.answer()
            await query.edit_message_text("⚙️ لوحة تحكم الإدارة:", reply_markup=admin_keyboard())
        else:
            await query.answer("❌ أنت لست الأدمن.", show_alert=True)

    elif query.data == "admin_add_vip":
        if user_id == ADMIN_ID:
            context.user_data["admin_action"] = "add_vip"
            await query.answer()
            await query.edit_message_text("أرسل معرف المستخدم الذي تريد إضافته VIP:")
        else:
            await query.answer("❌ أنت لست الأدمن.", show_alert=True)

    elif query.data == "admin_remove_vip":
        if user_id == ADMIN_ID:
            context.user_data["admin_action"] = "remove_vip"
            await query.answer()
            await query.edit_message_text("أرسل معرف المستخدم الذي تريد إزالة VIP عنه:")
        else:
            await query.answer("❌ أنت لست الأدمن.", show_alert=True)

    elif query.data == "admin_list_users":
        if user_id == ADMIN_ID:
            await query.answer()
            cursor.execute("SELECT user_id FROM vip_users")
            vip_rows = cursor.fetchall()
            vip_list = "\n".join(str(row[0]) for row in vip_rows) or "لا يوجد مشتركين VIP حالياً."
            await query.edit_message_text(f"قائمة المشتركين VIP:\n{vip_list}")
        else:
            await query.answer("❌ أنت لست الأدمن.", show_alert=True)

    else:
        await query.answer()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    vip_status = is_vip(user_id)

    allowed, msg_limit = can_download_limit(user_id, vip_status)
    if not allowed:
        await update.message.reply_text(msg_limit)
        return

    allowed, msg_spam = can_download(user_id, vip_status)
    if not allowed:
        await update.message.reply_text(msg_spam)
        return

    speed_up = context.user_data.get("speed_up", False)

    if not any(domain in text.lower() for domain in ("youtube.com", "youtu.be", "facebook.com", "fb.watch", "tiktok.com", "instagram.com")):
        await update.message.reply_text("❌ الرابط غير مدعوم. الرجاء إرسال رابط من YouTube، Facebook، TikTok، أو Instagram.")
        return

    # خاص باليوتيوب: نطلب نوع التحميل
    if "youtube.com" in text.lower() or "youtu.be" in text.lower():
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎧 صوت فقط", callback_data=f"download_audio|{text}"),
                InlineKeyboardButton("🎥 فيديو كامل", callback_data=f"download_video|{text}"),
                InlineKeyboardButton("📱 شورتس", callback_data=f"download_shorts|{text}"),
            ]
        ])
        await update.message.reply_text("اختر نوع التحميل:", reply_markup=keyboard)
        return
    else:
        await update.message.reply_text(random.choice(WELCOME_MESSAGES))

        filename = await download_media(text, "video")
        if not filename:
            await update.message.reply_text("❌ حدث خطأ أثناء التحميل. حاول لاحقاً.")
            return

        try:
            if speed_up:
                await update.message.reply_video(open(filename, "rb"))
            else:
                with open(filename, "rb") as video_file:
                    await update.message.reply_video(video_file)
        except Exception as e:
            logging.error(f"Error sending file: {e}")
            await update.message.reply_text("❌ حدث خطأ أثناء إرسال الملف.")
            return

        after_download_success(user_id)
        context.user_data["speed_up"] = False

        try:
            os.remove(filename)
        except:
            pass


async def download_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("|")
    action = data[0]
    url = data[1]

    vip_status = is_vip(user_id)
    speed_up = context.user_data.get("speed_up", False)

    allowed, msg_limit = can_download_limit(user_id, vip_status)
    if not allowed:
        await query.answer()
        await query.edit_message_text(msg_limit)
        return

    allowed, msg_spam = can_download(user_id, vip_status)
    if not allowed:
        await query.answer()
        await query.edit_message_text(msg_spam)
        return

    await query.answer()
    await query.edit_message_text("⏳ جاري التحميل... انتظر لحظة من فضلك.")

    download_type_map = {
        "download_audio": "audio",
        "download_video": "video",
        "download_shorts": "shorts"
    }

    download_type = download_type_map.get(action, "video")

    filename = await download_media(url, download_type)
    if not filename:
        await query.edit_message_text("❌ حدث خطأ أثناء التحميل. حاول لاحقاً.")
        return

    try:
        if download_type == "audio":
            await query.message.reply_audio(open(filename, "rb"))
        else:
            await query.message.reply_video(open(filename, "rb"))
    except Exception as e:
        logging.error(f"Error sending file: {e}")
        await query.edit_message_text("❌ حدث خطأ أثناء إرسال الملف.")
        return

    after_download_success(user_id)
    context.user_data["speed_up"] = False

    try:
        os.remove(filename)
    except:
        pass


async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if user_id != ADMIN_ID:
        return

    action = context.user_data.get("admin_action")
    if action == "add_vip":
        try:
            new_vip_id = int(text)
            expiry_date = (datetime.now() + timedelta(days=30)).isoformat()
            cursor.execute("INSERT OR REPLACE INTO vip_users (user_id, vip_expiry) VALUES (?, ?)", (new_vip_id, expiry_date))
            conn.commit()
            await update.message.reply_text(f"تمت إضافة المستخدم {new_vip_id} كمشترك VIP حتى {expiry_date}.")
        except Exception as e:
            await update.message.reply_text("خطأ: الرجاء إرسال معرف مستخدم صحيح.")
        context.user_data["admin_action"] = None

    elif action == "remove_vip":
        try:
            remove_vip_id = int(text)
            cursor.execute("DELETE FROM vip_users WHERE user_id=?", (remove_vip_id,))
            conn.commit()
            await update.message.reply_text(f"تم حذف الاشتراك VIP للمستخدم {remove_vip_id}.")
        except Exception as e:
            await update.message.reply_text("خطأ: الرجاء إرسال معرف مستخدم صحيح.")
        context.user_data["admin_action"] = None


async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(download_choice_handler, pattern="^download_"))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), admin_text_handler))

    print("البوت بدأ بنجاح...")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
