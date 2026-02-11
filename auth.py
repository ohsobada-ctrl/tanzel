import json, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

ADMIN_ID = 1084115596  # معرف الأدمن
DATA_FILE = "users.json"

# ---------------- تحميل البيانات ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"allowed_users": [], "banned_users": []}
        save_data(data)
    return set(data["allowed_users"]), set(data["banned_users"])

def save_data(data=None):
    if data is None:
        data = {"allowed_users": list(allowed_users), "banned_users": list(banned_users)}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ---------------- القوائم ----------------
allowed_users, banned_users = load_data()

def clean_lists():
    """تنظيف القوائم: أي مستخدم موجود في allowed_users ما يكونش في banned_users"""
    global allowed_users, banned_users
    banned_users -= allowed_users
    save_data()

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def is_allowed(user_id):
    return str(user_id) in allowed_users

def is_banned(user_id):
    return str(user_id) in banned_users

def allow(user_id):
    allowed_users.add(str(user_id))
    if str(user_id) in banned_users:
        banned_users.remove(str(user_id))
    clean_lists()
    save_data()

def ban(user_id):
    banned_users.add(str(user_id))
    if str(user_id) in allowed_users:
        allowed_users.remove(str(user_id))
    clean_lists()
    save_data()

def unban(user_id):
    if str(user_id) in banned_users:
        banned_users.remove(str(user_id))
    save_data()

def list_users():
    return allowed_users, banned_users

# ---------------- طلب إذن ----------------
def request_access(bot, message):
    """إرسال طلب إذن للأدمن مع أزرار سماح/رفض"""
    user = message.from_user
    user_id = user.id
    info = f"""
👤 مستخدم جديد يبي يستعمل البوت:

🆔 ID: {user_id}
👤 الاسم: {user.first_name} {user.last_name or ""}
🔗 يوزر: @{user.username if user.username else "❌ ماعنداش"}
📸 صورة: {"https://t.me/" + user.username if user.username else "❌"}
    """
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ سماح", callback_data=f"allow_{user_id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"ban_{user_id}")
    )

    bot.send_message(ADMIN_ID, info, reply_markup=markup)
    bot.send_message(message.chat.id, "⏳ تم إرسال طلبك للأدمن، استنى الموافقة...")
