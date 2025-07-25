import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

# إنشاء جدول users مع كل الأعمدة المطلوبة
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    vip_until TEXT DEFAULT NULL,
    daily_downloads INTEGER DEFAULT 0,
    last_download_date TEXT DEFAULT NULL,
    points INTEGER DEFAULT 0,
    daily_vip_minutes INTEGER DEFAULT 0,
    last_vip_date TEXT DEFAULT NULL
)
""")

conn.commit()
conn.close()

print("تم إنشاءها بنجاح users.db قاعدة البيانات.")