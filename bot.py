import os
import telebot
from telebot import types
import random
import string
import time
import requests
from threading import Thread
from flask import Flask

# 🌐 إعداد سيرفر ويب وهمي لإرضاء Render ومنع تعليق المنفذ (Port Timeout)
app = Flask('')

@app.route('/')
def home():
    return "CinemaZone Guard is Live!"

def run_flask():
    # Render يمرر المنفذ تلقائياً عبر المتغير البيئي PORT، وإذا لم يجده يستخدم 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 1. 🔒 إخفاء وتأمين توكن البوت
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# 2. بيانات الفايربيز (الـ REST API للـ Realtime Database)
FIREBASE_DB_URL = "https://cinemazone-a11ba-default-rtdb.europe-west1.firebasedatabase.app/"

user_requests = {}

def is_user_blocked(user_id):
    try:
        url = f"{FIREBASE_DB_URL}cz_blocked_users/{user_id}.json"
        response = requests.get(url)
        if response.status_code == 200 and response.json() is not None:
            return True
    except Exception as e:
        print(f"Error checking block list: {e}")
    return False

def block_user_in_firebase(user_id, username, reason):
    try:
        url = f"{FIREBASE_DB_URL}cz_blocked_users/{user_id}.json"
        block_data = {
            "reason": reason,
            "username": username or "Unknown",
            "timestamp": int(time.time() * 1000)
        }
        requests.put(url, json=block_data)
        print(f"🚫 User {user_id} has been blocked due to: {reason}")
    except Exception as e:
        print(f"Error blocking user: {e}")

def generate_and_save_token():
    current_time_ms = int(time.time() * 1000)
    
    # 🧹 [تحديث أمني تلقائي] تنظيف وتطهير قاعدة البيانات من التوكنات القديمة المنتهية أولاً
    try:
        active_tokens_url = f"{FIREBASE_DB_URL}cz_active_tokens.json"
        tokens_response = requests.get(active_tokens_url)
        if tokens_response.status_code == 200 and tokens_response.json():
            all_tokens = tokens_response.json()
            for t_code, t_data in all_tokens.items():
                # إذا انتهت صلاحية التوكن (أقل من الوقت الحالي)، احذفه فوراً
                if t_data.get("expiry", 0) < current_time_ms:
                    delete_url = f"{FIREBASE_DB_URL}cz_active_tokens/{t_code}.json"
                    requests.delete(delete_url)
            print("🧹 Database Cleared: Expired tokens have been successfully purged.")
    except Exception as e:
        print(f"Error purging old tokens: {e}")

    # ⚡ توليد التوكن الجديد
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    token_code = f"cz_{random_suffix}"
    
    expiry_time = current_time_ms + (10 * 60 * 1000) # صلاحية 10 دقائق
    
    token_data = {
        "expiry": expiry_time,
        "created": current_time_ms
    }
    
    try:
        url = f"{FIREBASE_DB_URL}cz_active_tokens/{token_code}.json"
        response = requests.put(url, json=token_data)
        if response.status_code == 200:
            return token_code
    except Exception as e:
        print(f"Error saving to Firebase: {e}")
    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    current_time = time.time()

    if is_user_blocked(user_id):
        bot.reply_to(message, "❌ تم تقييد وصولك لمنصة سِينِمَا زُونْ نهائياً لمخالفة معايير الأمان الإدارية.")
        return

    if user_id not in user_requests:
        user_requests[user_id] = []
    
    user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < 10]
    user_requests[user_id].append(current_time)
    
    if len(user_requests[user_id]) > 5:
        block_user_in_firebase(user_id, username, "محاولة إغراق البوت بالطلبات متكررة (Spamming)")
        bot.reply_to(message, "❌ تم حظر حسابك تلقائياً بسبب محاولة إغراق النظام بالطلبات.")
        return

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

@bot.callback_query_handler(func=lambda call: call.data == "gen_token")
def callback_inline(call):
    if call.message:
        if call.from_user.id != 7861493:
            bot.answer_callback_query(call.id, text="❌ غير مصرح لك!")
            return
            
        new_token = generate_and_save_token()
        bot.answer_callback_query(call.id, text="تم التوليد والحفظ بنجاح! 🔥")
        bot.send_message(call.message.chat.id, f"👑 توكن جديد تم حقنه في الفايربيز:\n`{new_token}`", parse_mode="Markdown")

# 🚀 تشغيل سيرفر الويب في مسار منفصل (Thread) قبل تشغيل البوت
server_thread = Thread(target=run_flask)
server_thread.start()

print("🤖 CinemaZone Guard Bot is starting with Web Port support...")
bot.infinity_polling()
