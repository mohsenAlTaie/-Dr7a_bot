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

TOKEN = "8444492438:AAGH0f5wTCYiie3Vhv9d8rlv1i4LvR6VMW4"
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

def update_vip(user_id, minutes=30):
    user = get_user(user_id)
    now_str = datetime.now().strftime("%Y-%m-%d")
    if user:
        last_vip_date = user[5]
        daily_vip_minutes = user[4] or 0
        if last_vip_date == now_str and daily_vip_minutes >= 30:
            return False
        remain = 30 - daily_vip_minutes
        add_min = min(minutes, remain)
        new_vip_until = datetime.now() + timedelta(minutes=add_min)
        vip_until_str = new_vip_until.strftime("%Y-%m-%d %H:%M:%S")
        new_daily_vip = daily_vip_minutes + add_min
        c.execute("UPDATE users SET vip_until=?, points=0, daily_vip_minutes=?, last_vip_date=? WHERE user_id=?",
                  (vip_until_str, new_daily_vip, now_str, user_id))
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user_if_not_exists(user_id)

    keyboard = [
        [InlineKeyboardButton("🆔 معرفي", callback_data="show_id")],
    ]

    if get_points(user_id) < 5:
        keyboard[0].append(InlineKeyboardButton("🎁 اكسب تحميلات مجانية", callback_data="free_downloads"))
    else:
        keyboard[0].append(InlineKeyboardButton("🎉 نقاط كافية! تفعيل VIP تلقائي", callback_data="auto_vip"))

    keyboard.append([
        InlineKeyboardButton("⭐ مميزات VIP", callback_data="vip_features"),
        InlineKeyboardButton("💳 اشترك الآن", callback_data="subscribe_now")
    ])

    keyboard.append([
        InlineKeyboardButton("📊 كم تبقى تحميلات اليوم؟", callback_data="remaining_downloads"),
        InlineKeyboardButton("✅ التحقق من الاشتراك", callback_data="check_subscription")
    ])

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
        "🛠️ *تم بناء هذا البوت بعناية بواسطة محسن علي حسين* 🎮💻"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    add_user_if_not_exists(user_id)

    if query.data == "show_id":
        await query.edit_message_text(f"🆔 معرفك هو: `{user_id}`", parse_mode=ParseMode.MARKDOWN)

    elif query.data == "free_downloads":
        share_url = f"https://t.me/{BOT_USERNAME}"
        keyboard = [
            [InlineKeyboardButton("📤 شارك البوت الآن", url=f"https://t.me/share/url?url={share_url}&text=جرب_هذا_البوت_الخاص_بالتحميل!")],
            [InlineKeyboardButton("✅ تأكيد المشاركة", callback_data="confirm_share")],
            [InlineKeyboardButton("❓ كم عدد نقاطك؟", callback_data="show_points")]
        ]
        text = (
            "🎁 شارك البوت مع أصدقائك! \n"
            "اضغط على زر 'شارك البوت الآن' لتسهيل المشاركة.\n\n"
            "بعد مشاركة البوت، اضغط 'تأكيد المشاركة' لأحسب لك نقطة.\n"
            "⚠️ *تنبيه:* لا يمكنك الحصول على أكثر من 30 دقيقة VIP من نقاط المشاركة في اليوم الواحد.\n"
            "يرجى الصدق والضغط على تأكيد المشاركة فقط بعد المشاركة الفعلية.\n"
            "كل 5 نقاط تحصل على VIP نصف ساعة!"
        )
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    elif query.data == "confirm_share":
        if is_vip(user_id):
            await query.answer("⚠️ أنت مشترك VIP بالفعل، لا يمكن إضافة نقاط VIP إضافية الآن.", show_alert=True)
            return

        user = get_user(user_id)
        now_str = datetime.now().strftime("%Y-%m-%d")
        daily_vip = user[4] if user else 0

        if user and user[5] != now_str:
            c.execute("UPDATE users SET daily_vip_minutes=0, last_vip_date=? WHERE user_id=?", (now_str, user_id))
            conn.commit()
            daily_vip = 0

        if daily_vip >= 30:
            await query.answer("⚠️ لقد وصلت الحد اليومي (30 دقيقة VIP). حاول غداً.", show_alert=True)
            return

        added = update_vip(user_id, minutes=30)
        if added:
            points = get_points(user_id)
            await query.answer(f"✅ تم تفعيل VIP نصف ساعة وأضيفت نقطة. نقاطك الحالية: {points}", show_alert=True)
        else:
            await query.answer("⚠️ لم تتم إضافة دقائق VIP، ربما وصلت الحد اليومي.", show_alert=True)

    elif query.data == "show_points":
        points = get_points(user_id)
        await query.answer(f"نقاطك الحالية: {points}", show_alert=True)

    elif query.data == "auto_vip":
        points = get_points(user_id)
        if points >= 5:
            added = update_vip(user_id, minutes=30)
            if added:
                await query.edit_message_text(
                    "🎉 تم تفعيل اشتراك VIP لمدة 30 دقيقة بنجاح! استمتع بالتسريع والتحميل بلا حدود."
                )
            else:
                await query.edit_message_text(
                    "⚠️ لقد وصلت الحد اليومي (30 دقيقة VIP) من نقاط المشاركة."
                )
        else:
            await query.edit_message_text(
                "❌ نقاطك غير كافية لتفعيل VIP. استمر في مشاركة روابط أصدقائك."
            )

    elif query.data == "vip_features":
        vip_msg = (
            "⭐ مميزات VIP:\n"
            "- تحميل غير محدود\n"
            "- تسريع التحميل\n"
            "- دعم مباشر\n"
            "- وغيرها الكثير..."
        )
        await query.edit_message_text(vip_msg)

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
        if is_vip(user_id):
            await query.edit_message_text("✅ أنت مشترك VIP حاليًا.")
        else:
            await query.edit_message_text("❌ أنت غير مشترك VIP حالياً.")

    elif query.data == "speed_up":
        if is_vip(user_id):
            await query.edit_message_text("⚡️ تسريع التحميل مفعّل فقط للمشتركين VIP.")
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
            await update.message.reply_text("📝 أرسل معرف المستخدم لإضافة اشتراك VIP له:")
            context.user_data["vip_action"] = "add"
        else:
            await query.edit_message_text("❌ ليس لديك صلاحية.")

    elif query.data == "remove_vip":
        if user_id == ADMIN_ID:
            await update.message.reply_text("📝 أرسل معرف المستخدم لحذف اشتراك VIP له:")
            context.user_data["vip_action"] = "remove"
        else:
            await update.message.reply_text("❌ ليس لديك صلاحية.")

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
    # انستغرام ستوري
    if "instagram.com/stories/" in url:
        return "cookies_instagram_story.txt"
    # فيسبوك ستوري
    elif ("facebook.com/stories/" in url or "fb.watch" in url and "story" in url):
        return "cookies_facebook_story.txt"
    # انستغرام عادي
    elif "instagram.com" in url:
        return "cookies_instagram.txt"
    # فيسبوك عادي
    elif "facebook.com" in url or "fb.watch" in url:
        return "cookies_facebook.txt"
    # يوتيوب
    elif "youtube.com" in url or "youtu.be" in url:
        return "cookies_youtube.txt"
    else:
        return None

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    add_user_if_not_exists(user_id)
    reset_daily_counts_if_new_day(user_id)

    if "vip_action" in context.user_data:
        action = context.user_data["vip_action"]
        try:
            target_id = int(text)
        except:
            await update.message.reply_text("❌ المعرف غير صالح. حاول مرة أخرى.")
            return

        if action == "add":
            update_vip(target_id, minutes=60*24*7)
            await update.message.reply_text(f"✅ تم إضافة VIP للمستخدم {target_id} لمدة 7 أيام.")
        elif action == "remove":
            c.execute("UPDATE users SET vip_until=NULL WHERE user_id=?", (target_id,))
            conn.commit()
            await update.message.reply_text(f"✅ تم إزالة VIP للمستخدم {target_id}.")

        context.user_data.pop("vip_action")
        return

    if any(site in text for site in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "instagram", "tiktok.com"]):
        now = time.time()
        if not is_vip(user_id):
            downloads = get_daily_downloads(user_id)
            if downloads >= 10:
                await update.message.reply_text("❌ وصلت الحد اليومي للتحميلات. اشترك VIP لتحميل بلا حدود.")
                return
            if user_id in user_timestamps and now - user_timestamps[user_id] < 10:
                await update.message.reply_text("⏳ الرجاء الانتظار قليلاً قبل إرسال رابط جديد.")
                return
            user_timestamps[user_id] = now

        if not is_vip(user_id):
            add_point(user_id)
            points = get_points(user_id)
            if points >= 5:
                await update.message.reply_text(
                    "🎉 مبروك! لديك 5 نقاط. اضغط زر 'تفعيل VIP تلقائي' في الواجهة الرئيسية لتحصل على VIP نصف ساعة."
                )
            else:
                await update.message.reply_text(f"✅ تم احتساب نقطة لك. نقاطك الحالية: {points}.")

        await download_video(update, context)
    else:
        await update.message.reply_text("❌ أرسل رابط فيديو صالح من YouTube أو Facebook أو Instagram أو TikTok.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    # دعم ملفات الكوكيز تلقائياً
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
        # دعم الكوكيز للمنصات الأخرى (يوتيوب/فيسبوك/انستا)
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

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
