import telebot
from telebot import types
import random
import string
import time
import requests

# 1. إعداد توكن البوت الجديد الخاص بك
BOT_TOKEN = "8891273359:AAEnUSaKQrz7TYMUuGmNIXyKNgMbuNqtlHg"
bot = telebot.TeleBot(BOT_TOKEN)

# 2. بيانات الفايربيز (الـ REST API للـ Realtime Database)
FIREBASE_DB_URL = "https://cinemazone-a11ba-default-rtdb.europe-west1.firebasedatabase.app/"

# دالة لتوليد توكن عشوائي فريد وحفظه في الفايربيز
def generate_and_save_token():
    # توليد كود مثل: cz_A1B2C3D4
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    token_code = f"cz_{random_suffix}"
    
    # 🔥 حساب وقت الانتهاء (10 دقائق من الآن بالملي ثانية لضمان أمان حديدي)
    expiry_time = int((time.time() + (10 * 60)) * 1000)
    created_time = int(time.time() * 1000)
    
    # تجهيز البيانات للفايربيز
    token_data = {
        "expiry": expiry_time,
        "created": created_time
    }
    
    # حفظ التوكن مباشرة في جدول cz_active_tokens عبر حزمة requests
    try:
        url = f"{FIREBASE_DB_URL}cz_active_tokens/{token_code}.json"
        response = requests.put(url, json=token_data)
        if response.status_code == 200:
            return token_code
    except Exception as e:
        print(f"Error saving to Firebase: {e}")
    return None

# التعامل مع أمر /start لجميع الحسابات بدون أي تجمد
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # إذا كان الحساب هو حسابك الأساسي (القائد والمسؤول)
    if user_id == 7861493:
        markup = types.InlineKeyboardMarkup()
        btn_generate = types.InlineKeyboardButton("توليد توكن تجريبي ⚡", callback_data="gen_token")
        markup.add(btn_generate)
        
        bot.reply_to(message, 
            "👑 مرحباً بك يا قائد في لوحة التحكم السرية للحارس!\n\n"
            "• حالة الجدار الناري: 🔒 نشط ومؤمن 100%.\n"
            "• تنبيه: حسابك معفي تماماً من فحص فترات الصلاحية.", 
            reply_markup=markup
        )
    else:
        # لجميع الحسابات الأخرى (الاحتياطي والمتابعين) - توليد توكن تلقائي فوراً!
        bot.send_chat_action(message.chat.id, 'typing')
        new_token = generate_and_save_token()
        
        if new_token:
            welcome_text = (
                "مرحباً بك في سِينِمَا زُونْ 🍿\n\n"
                "تم توليد كود الدخول الآمن الخاص بك بنجاح:\n"
                f"`{new_token}`\n\n"
                "⏳ الصلاحية: 10 دقائق فقط (استخدمه الآن قبل انتهاء صلاحيته).\n"
                "قم بنسخ الكود وضعه في الموقع لتفتح لك المكتبة فوراً! 🎬"
            )
            bot.reply_to(message, welcome_text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ عذراً، حدث خطأ أثناء الاتصال بقاعدة البيانات. أعد المحاولة لاحقاً.")

# التعامل مع الضغط على الزر بداخل حساب الإدارة
@bot.callback_query_handler(func=lambda call: call.data == "gen_token")
def callback_inline(call):
    if call.message:
        new_token = generate_and_save_token()
        bot.answer_callback_query(call.id, text="تم التوليد والحفظ بنجاح! 🔥")
        bot.send_message(call.message.chat.id, f"👑 توكن جديد تم حقنه في الفايربيز:\n`{new_token}`", parse_mode="Markdown")

# تشغيل البوت المستمر
print("🤖 CinemaZone Guard Bot is now running perfectly with 10-min expiry...")
bot.infinity_polling()
