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
    filters, ContextTypes
)
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = "7552405839:AAF8Pe8sTJnrr-rnez61HhxnwAVsth2IuaU"
ADMIN_ID = 7249021797
BOT_USERNAME = "Dr7a_bot"

if not os.path.exists("downloads"):
    os.makedirs("downloads")

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

conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    vip_until TEXT DEFAULT NULL,
    daily_downloads INTEGER DEFAULT 0,
    last_download_date TEXT DEFAULT NULL,
    points INTEGER DEFAULT 0,
    daily_vip_minutes INTEGER DEFAULT 0,
    last_vip_date TEXT DEFAULT NULL
)
''')
conn.commit()

def get_user(user_id):
    c.execute("SELECT vip_until, daily_downloads, last_download_date, points, daily_vip_minutes, last_vip_date FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

def add_user_if_not_exists(user_id):
    if not get_user(user_id):
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def is_vip(user_id):
    user = get_user(user_id)
    if user and user[0]:
        vip_until = datetime.strptime(user[0], "%Y-%m-%d %H:%M:%S")
        if vip_until > datetime.now():
            return True
    return False

def update_vip(user_id, minutes=60*24*30):  # 30 يوم
    user = get_user(user_id)
    now_str = datetime.now().strftime("%Y-%m-%d")
    if user:
        new_vip_until = datetime.now() + timedelta(minutes=minutes)
        vip_until_str = new_vip_until.strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET vip_until=?, points=0, daily_vip_minutes=?, last_vip_date=? WHERE user_id=?", (vip_until_str, minutes, now_str, user_id))
        conn.commit()
        return True
    return False

def reset_daily_counts_if_new_day(user_id):
    user = get_user(user_id)
    if not user:
        add_user_if_not_exists(user_id)
        return
    today_str = datetime.now().strftime("%Y-%m-%d")
    if user[2] != today_str:
        c.execute("UPDATE users SET daily_downloads=0, last_download_date=? WHERE user_id=?", (today_str, user_id))
        conn.commit()
    if user[5] != today_str:
        c.execute("UPDATE users SET points=0, daily_vip_minutes=0, last_vip_date=? WHERE user_id=?", (today_str, user_id))
        conn.commit()

def increment_download(user_id):
    reset_daily_counts_if_new_day(user_id)
    c.execute("UPDATE users SET daily_downloads = daily_downloads + 1 WHERE user_id=?", (user_id,))
    conn.commit()

def get_daily_downloads(user_id):
    reset_daily_counts_if_new_day(user_id)
    c.execute("SELECT daily_downloads FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else 0

def add_point(user_id):
    reset_daily_counts_if_new_day(user_id)
    add_user_if_not_exists(user_id)
    c.execute("UPDATE users SET points = points + 1 WHERE user_id=?", (user_id,))
    conn.commit()

def get_points(user_id):
    reset_daily_counts_if_new_day(user_id)
    c.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else 0

user_timestamps = {}
user_share_wait = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user_if_not_exists(user_id)

    keyboard = [
        [InlineKeyboardButton("🆔 معرفي", callback_data="show_id")],
        [InlineKeyboardButton("🤝 شارك البوت واربح VIP", callback_data="share_bot")],
        [InlineKeyboardButton("⭐ مميزات VIP", callback_data="vip_features"),
         InlineKeyboardButton("💳 اشترك الآن", callback_data="subscribe_now")],
        [InlineKeyboardButton("📊 كم تبقى تحميلات اليوم؟", callback_data="remaining_downloads"),
         InlineKeyboardButton("✅ التحقق من الاشتراك", callback_data="check_subscription")],
        [InlineKeyboardButton("🎵 حمل MP3 من اليوتيوب", url="http://t.me/YoutuneX_bot")],  # الزر الجديد هنا
    ]
    if is_vip(user_id):
        keyboard.append([InlineKeyboardButton("⚡️ تسريع التحميل", callback_data="speed_up")])
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "👁‍🗨✨ *أهلاً بك في البُعد الآخر من التحميل!*\n\n"
        "هل أنت مستعدّ لاختراق عوالم الفيديوهات من فيسبوك، يوتيوب، إنستغرام، وتيك توك؟ 🚀📥\n"
        "هنا حيث تنصهر الروابط وتولد الملفات! 🌐🔥\n\n"
        "📎 فقط أرسل الرابط، وسأقوم بالباقي... لا حاجة للشرح، فقط الثقة 💼🤖\n\n"
        "🛠️ *تم تطوير هذه البوت بواسطة: محسن الطائي* 🎮💻"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    add_user_if_not_exists(user_id)

    if query.data == "share_bot":
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT last_vip_date FROM users WHERE user_id=?", (user_id,))
        last_vip_date = c.fetchone()[0]
        if last_vip_date == today:
            await query.edit_message_text("لقد استخدمت ميزة VIP المجانية لهذا اليوم بالفعل!")
            return
        user_share_wait.add(user_id)
        await query.edit_message_text(
            "👥 شارك البوت مع 5 أصدقاء أو أي قناة/مجموعة، ثم أرسل لقطة شاشة هنا.\n\nرابط البوت:\nhttps://t.me/Dr7a_bot"
        )
        return

    if query.data == "show_id":
        await query.edit_message_text(f"🆔 معرفك هو: `{user_id}`", parse_mode=ParseMode.MARKDOWN)

    elif query.data == "vip_features":
        vip_msg = (
            "🔥 لا تفوت الفرصة الذهبية 🔥\n\n"
            "خلّك VIP وعيش الرفاهية التقنية:\n\n"
            "⭐ مميزات VIP:\n"
            "✅ تحميل بلا حدود – نزّل براحتك، ماكو حد\n"
            "✅ تسريع خارق – الفيديو ينزل قبل لا تفكر بيه\n"
            "✅ دعم مباشر من المطور – تحتاج شي؟ موجودين\n"
            "✅ مزايا سرّية بس للمميزين 😏\n\n"
            "💸 السعر: 5,000 دينار عراقي فقط!\n\n"
            "💥 اشترك الآن وخلي البوت يخدمك مثل الملوك 👑\n"
            "الفخامة تبدأ من ضغطة زر!"
        )

        keyboard = [
            [InlineKeyboardButton("💎 اشترك الآن", url="https://t.me/K0_MG")]
        ]
        await query.edit_message_text(vip_msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "subscribe_now":
        subscribe_msg = (
            "💳 للاشتراك VIP، اضغط زر الدفع التالي وتواصل مع المطور:\n"
            "[تواصل مع المطور](https://t.me/K0_MG)"
        )
        await query.edit_message_text(subscribe_msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    elif query.data == "remaining_downloads":
        if is_vip(user_id):
            await query.edit_message_text("📊 أنت مشترك VIP، التحميلات غير محدودة.")
        else:
            downloads = get_daily_downloads(user_id)
            remaining = max(0, 10 - downloads)
            await query.edit_message_text(f"📊 تبقى لك {remaining} تحميلات اليوم (الحد الأقصى 10).")

    elif query.data == "check_subscription":
        user = get_user(user_id)
        if is_vip(user_id) and user[0]:
            await query.edit_message_text(
                f"✅ أنت مشترك VIP حاليًا.\nينتهي الاشتراك في: {user[0]}"
            )
        else:
            await query.edit_message_text("❌ أنت غير مشترك VIP حالياً.")

    elif query.data == "speed_up":
        if is_vip(user_id):
            await query.answer("تم تفعيل تسريع التحميل لأنك مشترك VIP ✅", show_alert=True)
            await query.edit_message_text("⚡️ تم تفعيل تسريع التحميل بأقصى سرعة! استمتع 💎")
        else:
            await query.edit_message_text("❌ هذه الميزة متاحة فقط للمشتركين VIP.")

    elif query.data == "admin_panel":
        if user_id == ADMIN_ID:
            admin_keyboard = [
                [InlineKeyboardButton("➕ إضافة VIP", callback_data="add_vip")],
                [InlineKeyboardButton("🗑️ حذف VIP", callback_data="remove_vip")],
                [InlineKeyboardButton("📋 قائمة VIP", callback_data="list_vip")],
                [InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main")],
            ]
            await query.edit_message_text("⚙️ لوحة التحكم الإدارية:", reply_markup=InlineKeyboardMarkup(admin_keyboard))
        else:
            await query.edit_message_text("❌ أنت غير مصرح بالدخول إلى لوحة التحكم.")

    elif query.data == "back_to_main":
        await start(update, context)

    elif query.data == "add_vip":
        if user_id == ADMIN_ID:
            await query.message.reply_text("📝 أرسل معرف المستخدم لإضافة اشتراك VIP له:")
            context.user_data["vip_action"] = "add"
        else:
            await query.edit_message_text("❌ ليس لديك صلاحية.")

    elif query.data == "remove_vip":
        if user_id == ADMIN_ID:
            await query.message.reply_text("📝 أرسل معرف المستخدم لحذف اشتراك VIP له:")
            context.user_data["vip_action"] = "remove"
        else:
            await query.edit_message_text("❌ ليس لديك صلاحية.")

    elif query.data == "list_vip":
        if user_id == ADMIN_ID:
            c.execute("SELECT user_id, vip_until FROM users WHERE vip_until > ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
            rows = c.fetchall()
            if not rows:
                await query.edit_message_text("📋 لا يوجد مشتركين VIP حالياً.")
            else:
                msg = "📋 قائمة المشتركين VIP:\n"
                for uid, vip_until in rows:
                    msg += f"- {uid} حتى {vip_until}\n"
                await query.edit_message_text(msg)
        else:
            await query.edit_message_text("❌ ليس لديك صلاحية.")
    else:
        await query.edit_message_text("❌ خيار غير معروف.")

def get_cookies_path(url):
    if "instagram.com/stories/" in url:
        return "cookies_instagram_story.txt"
    elif ("facebook.com/stories/" in url or "fb.watch" in url and "story" in url):
        return "cookies_facebook_story.txt"
    elif "instagram.com" in url:
        return "cookies_instagram.txt"
    elif "facebook.com" in url or "fb.watch" in url:
        return "cookies_facebook.txt"
    elif "youtube.com" in url or "youtu.be" in url:
        return "cookies_youtube.txt"
    else:
        return None

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()
    cookies_file = get_cookies_path(url)

    if "tiktok.com" in url:
        loading_msg = random.choice(weird_messages)
        await update.message.reply_text(f"{loading_msg}\n⏳ جاري تحميل الفيديو...")
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'format': 'mp4',
            'quiet': True,
        }
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(file_path, 'rb'))
            os.remove(file_path)
            increment_download(user_id)
        except Exception as e:
            await update.message.reply_text(f"❌ فشل التحميل من TikTok:\n{str(e)}")
        return

    await update.message.reply_text("📥 جاري تحميل الفيديو، يرجى الانتظار...")
    try:
        file_path = "downloads/video.mp4"
        command = ["yt-dlp", "-f", "mp4", "-o", file_path, url]
        if cookies_file and os.path.exists(cookies_file):
            command = ["yt-dlp", "--cookies", cookies_file, "-f", "mp4", "-o", file_path, url]
        subprocess.run(command, check=True)
        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"))
            increment_download(user_id)
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف بعد التحميل.")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ خطأ أثناء تحميل الفيديو:\n{str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ غير متوقع:\n{str(e)}")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    add_user_if_not_exists(user_id)
    reset_daily_counts_if_new_day(user_id)
    now = time.time()

    # الجزء المهم لإضافة أو حذف VIP
    if "vip_action" in context.user_data:
        action = context.user_data["vip_action"]
        try:
            target_id = int(text)
        except:
            await update.message.reply_text("❌ المعرف غير صالح. حاول مرة أخرى.")
            context.user_data.pop("vip_action")
            return
        if action == "add":
            update_vip(target_id, minutes=60*24*30)
            await update.message.reply_text(f"✅ تم إضافة VIP للمستخدم {target_id} لمدة 30 يوم.")
        elif action == "remove":
            c.execute("UPDATE users SET vip_until=NULL WHERE user_id=?", (target_id,))
            conn.commit()
            await update.message.reply_text(f"✅ تم إزالة VIP للمستخدم {target_id}.")
        context.user_data.pop("vip_action")
        return

    if any(site in text for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "instagram", "tiktok.com"]):
        if not is_vip(user_id):
            downloads = get_daily_downloads(user_id)
            if downloads >= 10:
                await update.message.reply_text("❌ وصلت الحد اليومي للتحميلات. اشترك VIP لتحميل بلا حدود.")
                return
            if user_id in user_timestamps and now - user_timestamps[user_id] < 60:
                wait_sec = int(60 - (now - user_timestamps[user_id]))
                await update.message.reply_text(f"⏳ الرجاء الانتظار {wait_sec} ثانية قبل إرسال رابط جديد.")
                return
            user_timestamps[user_id] = now
        await download_video(update, context)
    else:
        if is_vip(user_id):
            vip_funny_replies = [
                "😂 مشترك VIP وتحچي؟ كاعد بعرش الذهب وتكتبلي؟ 😎",
                "🤣 لك مشترك VIP وتريد تشتكي؟ راحة البال مضمونة!",
                "👑 شتريد بعد؟ أنت VIP يعني فوق القانون 😂",
                "🤑 راح أنفذ لك الطلب حتى لو تريد فيديو من المريخ!",
                "😂 رجاءً لا تطلب شي غريب... مثل تحميل دموع حزنك 😢",
            ]
            await update.message.reply_text(random.choice(vip_funny_replies))
        else:
            await update.message.reply_text("❌ أرسل رابط فيديو صالح من YouTube أو Facebook أو Instagram أو TikTok.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_share_wait:
        user_share_wait.remove(user_id)
        update_vip(user_id, minutes=3)
        await update.message.reply_text("🎉 مبروك لقد ربحت VIP لمدة 3 دقائق!")
    else:
        await update.message.reply_text("هذه الخدمة مخصصة فقط بعد مشاركة البوت.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
