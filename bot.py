import time
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import auth
from admin_panel import show_admin_panel, handle_admin_buttons
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import threading


TOKEN = '7824420284:AAHoy-cVGPJQg_ltuUpZA7q4DT5tuMPkUAE'
bot = telebot.TeleBot(TOKEN)
user_data = {}  # لكل مستخدم بياناته

# ---------------- /start ----------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if auth.is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 تم حظرك من استخدام البوت.")
        return

    # لو المستخدم غير أدمن وغير مسموح له
    if not auth.is_admin(user_id) and not auth.is_allowed(user_id):
        auth.request_access(bot, message)  # ترسل طلب للأدمن
        return

    # لو المستخدم الأدمن أو تم السماح له
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔑 تسجيل الدخول", callback_data="start_login"))
    bot.send_message(
        message.chat.id,
        "👋 أهلاً بيك!\n"
        "هذا البوت يسمح لك بمتابعة تسجيل المقررات في جامعة التقنية.\n"
        "اضغط الزر لتسجيل الدخول.",
        reply_markup=markup
    )


# ---------------- زر تسجيل الدخول ----------------
@bot.callback_query_handler(func=lambda call: call.data == "start_login")
def start_login(call):
    user_id = call.from_user.id

    if auth.is_banned(user_id):
        bot.send_message(call.message.chat.id, "🚫 تم حظرك من استخدام البوت.")
        return

    if not auth.is_admin(user_id) and not auth.is_allowed(user_id):
        auth.request_access(bot, call.message)
        return

    # تهيئة بيانات المستخدم
    user_data[user_id] = {"awaiting_username": True, "awaiting_password": False}
    bot.send_message(call.message.chat.id, "👤 دخل اسم المستخدم:")

# ---------------- التعامل مع الرسائل ----------------
# ---------------- أوامر الأدمن ----------------
@bot.message_handler(func=lambda m: m.text in ["اوامر", "/admin"])
def admin_commands(message):
    if not auth.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 هذا الأمر للأدمن فقط.")
        return
    show_admin_panel(bot, message)

@bot.message_handler(func=lambda m: m.text in ["📣 إرسال رسالة لجميع المستخدمين","👥 عرض المستخدمين", "✅ السماح", "🚫 الحظر", "🔓 إلغاء الحظر"])
def admin_buttons(message):
    handle_admin_buttons(bot, message)


# ---------------- الهاندلر العام ----------------
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id

    # تجاهل رسائل الأدمن للأزرار
    if auth.is_admin(user_id) and message.text in ["اوامر", "/admin","📣 إرسال رسالة لجميع المستخدمين", "👥 عرض المستخدمين", "✅ السماح", "🚫 الحظر", "🔓 إلغاء الحظر"]:
        return  # ما يعمل شيء، الهاندلر الخاص بلوحة الأدمن يتعامل معها

    if auth.is_banned(user_id):
        return

    if user_id not in user_data:
        bot.send_message(message.chat.id, "📌 استخدم /start لبدء العملية.")
        return

    

    

    if user_data[user_id].get("awaiting_username", False):
        user_data[user_id]['username'] = message.text
        user_data[user_id]['awaiting_username'] = False
        user_data[user_id]['awaiting_password'] = True
        bot.send_message(message.chat.id, "🔑 دخل كلمة المرور:")
        return
    elif user_data[user_id].get("awaiting_password", False):
        user_data[user_id]['password'] = message.text
        user_data[user_id]['awaiting_password'] = False
        bot.send_message(message.chat.id, "✅ جاري تسجيل الدخول... ⏳")
        threading.Thread(target=enroll_flow, args=(message, user_id)).start()
        return

    if message.text.startswith("/"):
        return
    bot.send_message(message.chat.id, "📌 استخدم /start لبدء العملية.")


# أوامر الأدمن
@bot.message_handler(func=lambda m: m.text in ["اوامر", "/admin"])
def admin_commands(message):
    if not auth.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 هذا الأمر للأدمن فقط.")
        return
    show_admin_panel(bot, message)
@bot.message_handler(func=lambda m: m.text in ["👥 عرض المستخدمين", "✅ السماح", "🚫 الحظر", "🔓 إلغاء الحظر"])
def admin_buttons(message):
    handle_admin_buttons(bot, message)


# ---------------- تسجيل الدخول والمتابعة ----------------
def enroll_flow(message, user_id):
    chat_id = message.chat.id
    username = user_data[user_id]['username']
    password = user_data[user_id]['password']

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://sms.uot.edu.ly/eng/login_ing.php")

       # اختيار الكلية بشكل صحيح
        fac_dropdown = wait.until(EC.presence_of_element_located((By.ID, "fac")))
        select = Select(fac_dropdown)
        select.select_by_visible_text("تقنية المعلومات")


        # إدخال اسم المستخدم وكلمة المرور
        email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_field.send_keys(username)
        pw_field = driver.find_element(By.ID, "login-password")
        pw_field.send_keys(password)
        driver.find_element(By.NAME, "btnlogin").click()

       # التحقق من وجود رسالة خطأ
        time.sleep(2)
        try:
                error_msg = driver.find_element(By.XPATH, "//h1[contains(text(),'رقم القيد الذي ادخلته غير صحيح')]")
                if error_msg:
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("🔑 تسجيل الدخول", callback_data="start_loginAG"))

                    bot.send_message(
                        message.chat.id,
                        "❌ رقم القيد أو كلمة المرور غير صحيحة. حاول مرة أخرى.",
                        reply_markup=markup
                    )

                    driver.quit()
                    return  # نوقف العملية هنا
        except NoSuchElementException:
                pass
    

    
        # تأكيد الدخول
        wait.until(EC.url_contains("student"))


        # تجاوز أي إعلان أو نافذة منبثقة
        try:
            time.sleep(1)
            driver.execute_script("document.querySelectorAll('.modal.show').forEach(m => m.style.display='none');")
        except: pass

        # الدخول للسجل الدراسي
        record_menu = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nav-link.nav-record")))
        driver.execute_script("arguments[0].click();", record_menu)

        show_semester = wait.until(EC.element_to_be_clickable((By.XPATH, "//p[text()='عرض الفصول']")))
        driver.execute_script("arguments[0].click();", show_semester)

        time.sleep(2)
        table = driver.find_element(By.ID, "example2")
        rows = table.find_elements(By.TAG_NAME, "tr")
        last_row = None
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 7 and "تسجيل المقررات" in cells[6].text:
                last_row = row

        if not last_row:
            bot.send_message(chat_id, "❌ لا يوجد فصل لتسجيل المقررات")
            driver.quit()
            return

        enroll_btn = last_row.find_element(By.NAME, "signsub")
        driver.execute_script("arguments[0].click();", enroll_btn)

        # قراءة المواد
        time.sleep(2)
        table_courses = driver.find_element(By.CLASS_NAME, "table")
        courses = table_courses.find_elements(By.TAG_NAME, "tr")

        markup = InlineKeyboardMarkup(row_width=1)
        course_map = {}
        for i, course in enumerate(courses[1:], start=1):
            cells = course.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 7:
                code = cells[1].text.strip()
                name = cells[2].text.strip()
                statu = cells[4].text.strip()
                status = cells[5].text.strip()               
                groups = [g.text.strip() for g in cells[6].find_elements(By.TAG_NAME, "option") if g.text.strip()]
                if not groups: groups = ["1","2","3"]
                btn_text = f"{code} - {name} | {status}"
                markup.add(InlineKeyboardButton(btn_text, callback_data=f"course_{i}"))
                course_map[f"course_{i}"] = (code, name, status, groups)

        user_data[user_id]['course_map'] = course_map
        user_data[user_id]['driver'] = driver
        bot.send_message(chat_id, "📋 اختر المادة لمتابعتها:", reply_markup=markup)
       

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء تسجيل الدخول: {str(e)}")
        driver.quit()

# ---------------- إعادة تسجيل الدخول بعد الفشل ----------------
@bot.callback_query_handler(func=lambda call: call.data == "start_loginAG")
def restart_login(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    user_data[user_id] = {"awaiting_username": True, "awaiting_password": False}
    bot.send_message(chat_id, "👤 دخل اسم المستخدم:")

# ---------------- اختيار المادة ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
def choose_group(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    course_info = user_data[user_id]['course_map'][call.data]
    code, name, status, groups = course_info

    markup = InlineKeyboardMarkup(row_width=3)
    for g in ["1","2","3"]:
        markup.add(InlineKeyboardButton(f"المجموعة {g}", callback_data=f"group_{code}_{g}"))

    user_data[user_id]['selected_course'] = (code, name)
    bot.send_message(chat_id, f"📌 اختر المجموعة لمتابعة مادة: {name}", reply_markup=markup)
    
#  ---------------- متابعة المادة ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("group_"))
def monitor_course(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    _, code, group = call.data.split("_")
    name = user_data[user_id]['selected_course'][1]
    driver = user_data[user_id]['driver']

    cancel_markup = InlineKeyboardMarkup(row_width=1)
    cancel_markup.add(InlineKeyboardButton("❌ إلغاء المتابعة", callback_data="cancel_monitor"))

    bot.send_message(chat_id, f"🔍 جاري متابعة {name} - المجموعة {group}", reply_markup=cancel_markup)
    user_data[user_id]['monitoring'] = True

    def monitor_loop():
        while user_data[user_id].get('monitoring', False):
            try:
                table_courses = driver.find_element(By.CLASS_NAME, "table")
                courses = table_courses.find_elements(By.TAG_NAME, "tr")
                found = False
                for course in courses[1:]:
                    cells = course.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 7 and code in cells[1].text:
                        status = cells[5].text.strip()
                        available_groups = [g.text.strip() for g in cells[6].find_elements(By.TAG_NAME, "option") if g.text.strip()]
                        if "متاحة" in status and group in available_groups:
                            bot.send_message(chat_id, f"✅ المادة {name} - المجموعة {group} متاحة الآن!")
                            user_data[user_id]['monitoring'] = False
                            found = True
                            break
                if found: break
                time.sleep(10)
                driver.refresh()
            except: break

    threading.Thread(target=monitor_loop).start()
@bot.callback_query_handler(func=lambda call: call.data == "cancel_monitor")
def cancel_monitor(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_data[user_id]['monitoring'] = False
    bot.send_message(chat_id, "❌ تم إلغاء متابعة المادة.")

# ---------------- أزرار السماح/رفض ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith(("allow_", "ban_")))
def handle_access_buttons(call):
    if not auth.is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 فقط الأدمن يقدر يضغط هالزر")
        return

    action, user_id = call.data.split("_")
    if action == "allow":
        auth.allowed_users.add(user_id)
        bot.send_message(auth.ADMIN_ID, f"✅ تم السماح للمستخدم {user_id}")
        bot.send_message(user_id, "🎉 تم السماح لك باستخدام البوت، يمكنك الآن متابعة المقررات.")
    elif action == "ban":
        auth.banned_users.add(user_id)
        if user_id in auth.allowed_users:
            auth.allowed_users.remove(user_id)
        bot.send_message(auth.ADMIN_ID, f"🚫 تم رفض المستخدم {user_id}")
        bot.send_message(user_id, "❌ تم رفض طلبك لاستخدام البوت.")



# استدعاء لوحة الأدمن عند كلمة "اوامر" أو "/admin"
@bot.message_handler(func=lambda m: m.text in ["اوامر", "/admin"])
def admin_commands(message):
    show_admin_panel(bot, message)


# ---------------- تشغيل البوت ----------------
while True:
    try:
        bot.polling(non_stop=True, timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"⚠️ Polling error: {e}")
        try: bot.send_message(auth.ADMIN_ID, f"⚠️ البوت توقف بسبب خطأ:\n{e}")
        except: pass
        time.sleep(5)