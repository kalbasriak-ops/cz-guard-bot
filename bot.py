import os
import telebot
from telebot import types
import random
import string
import time
import requests
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS

# 🤖 إعداد سيرفر ويب حقيقي لاستقبال إشعارات أمان بصمة العتاد والواجهة
app = Flask('')
CORS(app)  # للسماح بطلب الـ API من المتصفح دون مشاكل CORS

# 1. 🔒 الفحص الذكي والصارم لتوكن البوت ومطابقة متغيرات بيئة Render المتاحة
ENV_TOKEN = os.environ.get("BOT_TOKEN", os.environ.get("TELE_BOT_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))).strip()

if ENV_TOKEN and ":" in ENV_TOKEN:
    BOT_TOKEN = ENV_TOKEN
    print("✅ 🛰️ Success: Connected using Live Render Environment Token.")
else:
    # الفولباك التلقائي المحدث (تأكد دائماً أنك قمت بضبط BOT_TOKEN في إعدادات Render الـ Environment)
    BOT_TOKEN = ENV_TOKEN 
    print("⚠️ Warning: Reading directly from Fallback Chain configuration.")

bot = telebot.TeleBot(BOT_TOKEN)

# 2. بيانات الفايربيز المعرفة مسبقاً ومعرف المدير الثابت
FIREBASE_DB_URL = "https://cinemazone-a11ba-default-rtdb.europe-west1.firebasedatabase.app/"
ADMIN_CHAT_ID = 7861493  # معرف حسابك الإداري الموثق

user_requests = {}

def send_telegram_alert(message):
    """دالة داخلية لإرسال التنبيهات الإدارية الفورية مباشرة للمدير"""
    try:
        bot.send_message(ADMIN_CHAT_ID, message, parse_mode="Markdown")
        print("⚡ [Telegram Alert] Message dispatched successfully to Admin ID.")
    except Exception as e:
        print(f"❌ Failed to send admin telegram alert: {e}")

# ==========================================
# 📡 جسر استقبال الإشعارات الفورية المطوّر (GET + POST API Endpoints)
# ==========================================
@app.route('/')
def home():
    try:
        purge_expired_tokens()
    except Exception as e:
        print(f"Cron automatic purge failed: {e}")
    return "Cinema Zone Guard Engine Status: ACTIVE", 200

@app.route('/api/security/alert', methods=['GET', 'POST'])
def security_alert():
    """مستقبل التنبيهات الذكي يدعم الطريقتين لضمان تخطي جدران حماية المتصفحات والجوالات"""
    
    # استخراج البيانات سواء جاءت على شكل طلب GET (من الرابط) أو POST (JSON)
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args or {}
        
    token = data.get('token', 'غير معروف')
    username = data.get('username', 'عضو مجهول')
    fingerprint = data.get('fingerprint', 'لا يوجد')
    alert_type = data.get('type', 'auth_attempt')
    
    if alert_type == "hardware_block":
        msg = (
            f"🚨 *تنبيه أمان: محاولة اختراق أو جهاز متعدد!*\n\n"
            f"👤 *المستخدم:* {username}\n"
            f"🔑 *التوكن المستخدم:* `{token}`\n"
            f"🛡️ *بصمة العتاد المطرودة:* `{fingerprint}`\n\n"
            f"🔺 _تم تفعيل الحظر التلقائي وطرد الجهاز بنجاح من جدار الحماية!_"
        )
    else:
        msg = (
            f"✨ *دخول فخم جديد للمنصة* ✨\n\n"
            f"👤 *المستخدم:* {username}\n"
            f"🔑 *التوكن:* `{token}`\n"
            f"📱 *بصمة عتاد الجهاز:* `{fingerprint}`\n\n"
            f"🍿 _استعد للمتعة والمغامرة في Cinema Zone!_"
        )
        
    send_telegram_alert(msg)
    
    # إرجاع رد آمن دائماً للمتصفحات لمنع تعليق طلب الصورة المخفية
    return jsonify({"status": "success", "message": "Alert processed."}), 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 🛡️ الدوال المساعدة وفحوصات الأمان
# ==========================================
def is_user_blocked(user_id):
    try:
        url = f"{FIREBASE_DB_URL}cz_blocked_users/{user_id}.json"
        response = requests.get(url, timeout=5)
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
        requests.put(url, json=block_data, timeout=5)
        print(f"🚫 User {user_id} has been blocked due to: {reason}")
    except Exception as e:
        print(f"Error blocking user: {e}")

def purge_expired_tokens():
    current_time_ms = int(time.time() * 1000)
    try:
        active_tokens_url = f"{FIREBASE_DB_URL}cz_active_tokens.json"
        tokens_response = requests.get(active_tokens_url, timeout=5)
        if tokens_response.status_code == 200 and tokens_response.json():
            all_tokens = tokens_response.json()
            for t_code, t_data in all_tokens.items():
                if t_data.get("expiry", 0) < current_time_ms:
                    delete_url = f"{FIREBASE_DB_URL}cz_active_tokens/{t_code}.json"
                    requests.delete(delete_url, timeout=5)
            print("🧹 Database Cleared: Expired tokens purged.")
    except Exception as e:
        print(f"Error purging old tokens: {e}")

def generate_and_save_token(username=None):
    try:
        purge_expired_tokens()
    except Exception:
        pass
        
    current_time_ms = int(time.time() * 1000)
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    token_code = f"cz_{random_suffix}"
    expiry_time = current_time_ms + (10 * 60 * 1000)
    
    formatted_username = f"@{username}" if username else "👤 عضو فخم"
    token_data = {
        "expiry": expiry_time,
        "created": current_time_ms,
        "username": formatted_username
    }
    
    try:
        url = f"{FIREBASE_DB_URL}cz_active_tokens/{token_code}.json"
        response = requests.put(url, json=token_data, timeout=5)
        if response.status_code == 200:
            return token_code
    except Exception as e:
        print(f"Error saving to Firebase: {e}")
    return None

# ==========================================
# 🤖 معالجات التلغرام والأوامر التفاعلية للبوت
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    current_time = time.time()

    try:
        if is_user_blocked(user_id):
            bot.reply_to(message, "❌ تم تقييد وصولك لمنصة سِينِمَا زُونْ نهائياً لمخالفة معايير الأمان الإدارية.")
            return
    except Exception:
        pass

    if user_id not in user_requests:
        user_requests[user_id] = []
    
    user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < 10]
    user_requests[user_id].append(current_time)
    
    if len(user_requests[user_id]) > 5:
        block_user_in_firebase(user_id, username, "Spamming Bot Gateway")
        bot.reply_to(message, "❌ تم حظر حسابك تلقائياً بسبب محاولة إغراق النظام بالطلبات.")
        return

    # 🚨 القائد والمشرف العام
    if user_id == ADMIN_CHAT_ID:
        markup = types.InlineKeyboardMarkup()
        btn_generate = types.InlineKeyboardButton("توليد توكن تجريبي ⚡", callback_data="gen_token")
        markup.add(btn_generate)
        
        bot.reply_to(message, 
            "👑 مرحباً بك يا قائد في لوحة التحكم السرية للحارس!\n\n"
            f"• حالة الجدار الناري للعتاد: 🔒 نشط ويرصد المحاولات.\n"
            "• نظام الـ API المدمج: 🛰️ متصل وجاهز لبث التنبيهات الإدارية الفورية.", 
            reply_markup=markup
        )
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        new_token = generate_and_save_token(username)
        
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
        if call.from_user.id != ADMIN_CHAT_ID:
            bot.answer_callback_query(call.id, text="❌ غير مصرح لك!")
            return
            
        new_token = generate_and_save_token("المدير_العام")
        bot.answer_callback_query(call.id, text="تم التوليد والحفظ بنجاح! 🔥")
        bot.send_message(call.message.chat.id, f"👑 توكن جديد تم حقنه في الفايربيز:\n`{new_token}`", parse_mode="Markdown")

# 🚀 تشغيل سيرفر الويب في مسار منفصل (Thread) قبل تشغيل البوت
server_thread = Thread(target=run_flask)
server_thread.start()

print("🤖 CinemaZone Guard Bot & API Alert System is starting on Web Port...")

try:
    bot.remove_webhook()
except Exception:
    pass

bot.infinity_polling(timeout=10, long_polling_timeout=5)
