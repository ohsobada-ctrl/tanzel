
# نشغل ريفرش واحد بس يخدم لكل المستخدمين
threading.Thread(target=refresh_loop, daemon=True).start()

# ---------------- تشغيل البوت ----------------

while True:
    try:
        bot.polling(non_stop=True, timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"⚠️ Polling error: {e}")
        try: bot.send_message(auth.ADMIN_ID, f"⚠️ البوت توقف بسبب خطأ:\n{e}")
        except: pass
        time.sleep(5)
