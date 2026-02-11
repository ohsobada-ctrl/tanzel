from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import auth

def show_admin_panel(bot, message):
    """تعرض لوحة الأدمن بأزرار"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("👥 عرض المستخدمين"),
        KeyboardButton("✅ السماح"),
        KeyboardButton("🚫 الحظر"),
        KeyboardButton("🔓 إلغاء الحظر"),
        KeyboardButton("📣 إرسال رسالة لجميع المستخدمين")  # الزر الجديد هنا
    )
    bot.send_message(message.chat.id, "⚙️ اختار الأمر:", reply_markup=markup)




def handle_admin_buttons(bot, message):
    """معالجة أزرار الأدمن بعد اختيارها"""
    if not auth.is_admin(message.from_user.id):
        return bot.send_message(message.chat.id, "🚫 هذا الأمر للأدمن فقط.")

    text = message.text
    if text == "👥 عرض المستخدمين":
        allowed, banned = auth.list_users()
        text_msg = "👥 **المستخدمين المسموح لهم:**\n"
        text_msg += "\n".join([str(u) for u in allowed]) if allowed else "لا يوجد"
        text_msg += "\n\n🚫 **المحظورين:**\n"
        text_msg += "\n".join([str(u) for u in banned]) if banned else "لا يوجد"
        bot.send_message(message.chat.id, text_msg, parse_mode="Markdown")
    elif text == "✅ السماح":
        bot.send_message(message.chat.id, "📌 اكتب ID المستخدم للسماح:")
        bot.register_next_step_handler(message, lambda m: allow_user(bot, m))
    elif text == "🚫 الحظر":
        bot.send_message(message.chat.id, "📌 اكتب ID المستخدم للحظر:")
        bot.register_next_step_handler(message, lambda m: ban_user(bot, m))
    elif text == "🔓 إلغاء الحظر":
        bot.send_message(message.chat.id, "📌 اكتب ID المستخدم لإلغاء الحظر:")
        bot.register_next_step_handler(message, lambda m: unban_user(bot, m))
    elif text == "📣 إرسال رسالة لجميع المستخدمين":
         bot.send_message(message.chat.id, "📌 اكتب النص الذي تريد إرساله لجميع المستخدمين:")
         bot.register_next_step_handler(message, lambda m: broadcast_message(bot, m))



def allow_user(bot, message):
    try:
        user_id = int(message.text.strip())
        auth.allow(user_id)
        bot.send_message(message.chat.id, f"✅ تم السماح للمستخدم {user_id}")
    except:
        bot.send_message(message.chat.id, "❌ ID غير صالح.")


def ban_user(bot, message):
    try:
        user_id = int(message.text.strip())
        auth.ban(user_id)
        bot.send_message(message.chat.id, f"🚫 تم حظر المستخدم {user_id}")
    except:
        bot.send_message(message.chat.id, "❌ ID غير صالح.")


def unban_user(bot, message):
    try:
        user_id = int(message.text.strip())
        auth.unban(user_id)
        bot.send_message(message.chat.id, f"🔓 تم إلغاء الحظر عن {user_id}")
    except:
        bot.send_message(message.chat.id, "❌ ID غير صالح.")

def broadcast_message(bot, message):
    """إرسال رسالة لجميع المستخدمين المسموح لهم"""
    text = message.text.strip()
    if not text:
        return bot.send_message(message.chat.id, "❌ لا يمكن إرسال رسالة فارغة.")
    
    # نجمع كل المستخدمين المسموح لهم
    users = list(auth.allowed_users)
    success = 0
    failed = 0
    for user_id in users:
        try:
            bot.send_message(user_id, text)
            success += 1
        except:
            failed += 1
    bot.send_message(message.chat.id, f"📣 تم إرسال الرسالة بنجاح إلى {success} مستخدمين، وفشل في {failed}.")
