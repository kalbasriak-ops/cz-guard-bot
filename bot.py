import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types
import random
import string
import time
import requests

# --- خدعة المنفذ المجاني لموقع Render ---
app = Flask(__name__)
@app.route('/')
def home(): 
    return "CinemaZone Guard is Active"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run).start()
# -------------------------------------

# 🔐 مفاتيح الربط الأساسية المحدثة
BOT_TOKEN = "8891273359:AAGX87IasRFVYuaksMDVSgKZWbz_TQ94jbA"
FIREBASE_DB_URL = "https://cinemazone-a11ba-default-rtdb.europe-west1.firebasedatabase.app/"
ADMIN_ID = 7861493  # معرف حسابك الأساسي كمدير

bot = telebot.TeleBot(BOT_TOKEN)

def generate_and_save_token():
    """دالة توليد التوكن العشوائي وحفظه مباشرة في الفايربيز مع وقت الصلاحية"""
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    token_code = f"cz_{random_suffix}"
    
    expiry_time = int((time.time() + (10 * 60)) * 1000)
    created_time = int(time.time() * 1000)
    
    token_data = {
        "expiry": expiry_time,
        "created": created_time
    }
    
    try:
        base_url = FIREBASE_DB_URL.rstrip('/')
        url = f"{base_url}/cz_active_tokens/{token_code}.json"
        response = requests.put(url, json=token_data, timeout=10)
        if response.status_code == 200:
            return token_code
    except Exception as e:
        print(f"Firebase Error: {e}")
    
    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # 1. إذا كان المرسل هو القائد (الحساب الأساسي)
    if user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("توليد توكن ⚡", callback_data="gen_token"))
        bot.reply_to(message, "👑 أهلاً بك يا قائد، الحارس نشط وجاهز لخدمتك!", reply_markup=markup)
    
    # 2. إذا كان المرسل مستخدم عادي أو حسابك الاحتياطي
    else:
        new_token = generate_and_save_token()
        if new_token:
            response_text = f"مرحباً بك في سِينِمَا زُونْ 🍿\n\nكود دخولك الآمن هو:\n`{new_token}`\n\n⏳ هذا الكود صالح للاستخدام لمدة 10 دقائق فقط."
            bot.reply_to(message, response_text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ عذراً، حدث خطأ أثناء الاتصال بقاعدة البيانات لتوليد الكود. يرجى المحاولة مجدداً لاحقاً.")

@bot.callback_query_handler(func=lambda call: call.data == "gen_token")
def callback_inline(call):
    """التعامل مع ضغطة زر التوليد من الحساب الأساسي"""
    new_token = generate_and_save_token()
    
    if new_token:
        bot.answer_callback_query(call.id, text="تم توليد التوكن بنجاح! ✅")
        bot.send_message(call.message.chat.id, f"🔑 التوكن الجديد الخاص بك:\n`{new_token}`", parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, text="❌ فشل حفظ التوكن في فايربيز")
        bot.send_message(call.message.chat.id, "❌ خطأ: لم يتمكن البوت من حفظ التوكن في قاعدة البيانات.")

# تشغيل البوت بشكل مستمر
bot.infinity_polling(timeout=10, long_polling_timeout=5)
