import os
import telebot
from telebot import types
import random
import string
import time
import requests

# 1. 🔒 إخفاء وتأمين توكن البوت (يقرأ تلقائياً من إعدادات سيرفر Render المخفية)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# 2. بيانات الفايربيز (الـ REST API للـ Realtime Database)
FIREBASE_DB_URL = "https://cinemazone-a11ba-default-rtdb.europe-west1.firebasedatabase.app/"

# مخزن مؤقت لعدّاد الحماية من الإغراق (Anti-Spam Tracking)
user_requests = {}

# 🛡️ دالة للتحقق هل المستخدم محظور في الفايربيز أم لا
def is_user_blocked(user_id):
    try:
        url = f"{FIREBASE_DB_URL}cz_blocked_users/{user_id}.json"
        response = requests.get(url)
        if response.status_code == 200 and response.json() is not None:
            return True
    except Exception as e:
        print(f"Error checking block list: {e}")
    return False

# 🚫 دالة لحظر المخرب تلقائياً في الفايربيز
def block_user_in_firebase(user_id, username, reason):
    try:
        url = f"{FIREBASE_DB_URL}cz_blocked_users/{user_id}.json"
        block_data = {
            "reason": reason,
            "username": username or "Unknown",
            "timestamp": int(time.time() * 1000)
        }
        requests.put(url, json=block_data)
        print(f"🚫 User {user_id} has been blocked automatically due to: {reason}")
    except Exception as e:
        print(f"Error blocking user: {e}")

# دالة لتوليد توكن عشوائي فريد وحفظه في الفايربيز للموقع
def generate_and_save_token():
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    token_code = f"cz_{random_suffix}"
    
    expiry_time = int((time.time() + (10 * 60)) * 1000)  # 10 دقائق صلاحية
    created_time = int(time.time() * 1000)
    
    token_data = {
        "expiry": expiry_time,
        "created": created_time
    }
    
    try:
        url = f"{FIREBASE_DB_URL}cz_active_tokens/{token_code}.json"
        response = requests.put(url, json=token_data)
        if response.status_code == 200:
            return token_code
    except Exception as e:
        print(f"Error saving to Firebase: {e}")
    return None

# التعامل مع أمر /start لجميع الحسابات مع تفعيل الفخاخ الأمنية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    current_time = time.time()

    # 🛑 1. فحص هل المستخدم في قائمة الحظر الأساسية؟
    if is_user_blocked(user_id):
        bot.reply_to(message, "❌ تم تقييد وصولك لمنصة سِينِمَا زُونْ نهائياً لمخالفة معايير الأمان الإدارية.")
        return

    # 🛑 2. نظام مصيدة الإغراق (Anti-Spam) - حظر تلقائي للمخربين
    if user_id not in user_requests:
        user_requests[user_id] = []
    
    # تنظيف الطلبات القديمة التي مرت عليها أكثر من 10 ثوانٍ
    user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < 10]
    
    # إضافة الطلب الحالي
    user_requests[user_id].append(current_time)
    
    # إذا أرسل أكثر من 5 طلبات في أقل من 10 ثوانٍ (سلوك تخريبي)
    if len(user_requests[user_id]) > 5:
        block_user_in_firebase(user_id, username, "محاولة إغراق البوت بالطلبات متكررة (Spamming)")
        bot.reply_to(message, "❌ تم حظر حسابك تلقائياً بسبب محاولة إغراق النظام بالطلبات.")
        return

    # 👑 إذا كان الحساب هو حسابك الأساسي (القائد والمسؤول)
    if user_id == 7861493:
        markup = types.InlineKeyboardMarkup()
        btn_generate = types.InlineKeyboardButton("توليد توكن تجريبي ⚡", callback_data="gen_token")
        markup.add(btn_generate)
        
        bot.reply_to(message, 
            "👑 مرحباً بك يا قائد في لوحة التحكم السرية للحارس!\n\n"
            "• حالة الجدار الناري: 🔒 نشط ومؤمن 100%.\n"
            "• نظام الأمن المزدوج: 🛡️ مفعّل ويرصد المخربين تلقائياً.", 
            reply_markup=markup
        )
    else:
        # لجميع الحسابات الأخرى - توليد توكن تلقائي فوراً
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
        # تأكيد إضافي لحماية زر القائد
        if call.from_user.id != 7861493:
            bot.answer_callback_query(call.id, text="❌ غير مصرح لك!")
            return
            
        new_token = generate_and_save_token()
        bot.answer_callback_query(call.id, text="تم التوليد والحفظ بنجاح! 🔥")
        bot.send_message(call.message.chat.id, f"👑 توكن جديد تم حقنه في الفايربيز:\n`{new_token}`", parse_mode="Markdown")

# تشغيل البوت المستمر
print("🤖 CinemaZone Muted Bot is now running securely with Double-Layer Shielding...")
bot.infinity_polling()
