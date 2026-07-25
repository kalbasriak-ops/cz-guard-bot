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

# ==========================================
# 🔒 إعداد التوكن الفعلي والمطابق للوحة تحكم Render بشكل مباشر وثابت
# ==========================================
BOT_TOKEN = "8891273359:AAGX87IasRFVYuaksMDVSgKZWbz_TQ94jbA"
bot = telebot.TeleBot(BOT_TOKEN)

print("✅ 🛰️ Success: Connected using hardcoded Master Token (8891273359).")

# 2. بيانات الفايربيز المعرفة مسبقاً ومعرف المدير الثابت
FIREBASE_DB_URL = "https://cinemazone-a11ba-default-rtdb.europe-west1.firebasedatabase.app/"
ADMIN_CHAT_ID = 7861493  # معرف حسابك الإداري الموثق

user_requests = {}

def send_telegram_alert(html_message):
    """دالة داخلية لإرسال التنبيهات الإدارية الفورية باستخدام الـ HTML لمنع سقوط الرسائل"""
    try:
        bot.send_message(ADMIN_CHAT_ID, html_message, parse_mode="HTML")
        print("⚡ [Telegram Alert] Message dispatched successfully to Admin ID using HTML.")
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
    """مستقبل التنبيهات الذكي والمعدل بالكامل ليعمل بنظام HTML لمنع مشاكل الصياغة"""
    
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args or {}
        
    token = data.get('token', 'غير معروف')
    username = data.get('username', 'عضو مجهول')
    fingerprint = data.get('fingerprint', 'لا يوجد')
    alert_type = data.get('type', 'auth_attempt')
    
    # تنسيق الرسائل الملكي الآمن بصيغة HTML لتجنب السقوط
    if alert_type == "hardware_block":
        msg = (
            f"🚨 <b>تنبيه أمان: محاولة اختراق أو جهاز متعدد!</b>\n\n"
            f"👤 <b>المستخدم:</b> {username}\n"
            f"🔑 <b>التوكن المستخدم:</b> <code>{token}</code>\n"
            f"🛡️ <b>بصمة العتاد المطرودة:</b> <code>{fingerprint}</code>\n\n"
            f"🔺 <i>تم تفعيل الحظر التلقائي وطرد الجهاز بنجاح من جدار الحماية!</i>"
        )
    elif token == "cz103659_master_token" or "👑" in username:
        msg = (
            f"👑 <b>دخول ملكي استثنائي للمنصة</b> 👑\n\n"
            f"👤 <b>القائد المشرف:</b> {username}\n"
            f"🔑 <b>التوكن:</b> <code>{token}</code>\n"
            f"📱 <b>بصمة عتاد الجهاز:</b> <code>{fingerprint}</code>\n\n"
            f"🍿 <i>نظام الرادار الأمني تحت أمرك يا فندم! السهرة منورة بوجودك.</i>"
        )
    else:
        msg = (
            f"✨ <b>دخول فخم جديد للمنصة</b> ✨\n\n"
            f"👤 <b>المستخدم:</b> {username}\n"
            f"🔑 <b>التوكن:</b> <code>{token}</code>\n"
            f"📱 <b>بصمة عتاد الجهاز:</b> <code>{fingerprint}</code>\n\n"
            f"🍿 <i>استعد للمتعة والمغامرة في Cinema Zone!</i>"
        )
        
    send_telegram_alert(msg)
    return jsonify({"status": "success", "message": "Alert processed successfully."}), 200

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
# 🤖 معالجات التلغرام والأوامر التفاعلية المتطورة للبوت
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

    # 🚨 القائد والمشرف العام ولوحة التحكم المتطورة لمواكبة أرقى البوتات
    if user_id == ADMIN_CHAT_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_generate = types.InlineKeyboardButton("توليد توكن تجريبي ⚡", callback_data="gen_token")
        btn_stats = types.InlineKeyboardButton("الإحصائيات العامة 📊", callback_data="view_stats")
        btn_help_info = types.InlineKeyboardButton("إعلان وبث فوري 📢", callback_data="how_to_broadcast")
        
        markup.add(btn_generate, btn_stats)
        markup.add(btn_help_info)
        
        bot.reply_to(message, 
            "👑 <b>مرحباً بك يا قائد في لوحة التحكم التفاعلية المتقدمة للحارس!</b>\n\n"
            "• حالة الجدار الناري للعتاد: 🔒 <b>نشط ويرصد المحاولات.</b>\n"
            "• نظام الـ API المطور: 🛰️ <b>متصل ويبث التنبيهات فورا عبر الـ HTML.</b>\n\n"
            "اختر من القائمة الإعداد الذي تريد تعديله أو توليده مباشرة:", 
            parse_mode="HTML",
            reply_markup=markup
        )
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        new_token = generate_and_save_token(username)
        
        if new_token:
            welcome_text = (
                "مرحباً بك في سِينِمَا زُونْ 🍿\n\n"
                "تم توليد كود الدخول الآمن الخاص بك بنجاح:\n"
                f"<code>{new_token}</code>\n\n"
                "⏳ الصلاحية: 10 دقائق فقط (استخدمه الآن قبل انتهاء صلاحيته).\n"
                "قم بنسخ الكود وضعه في الموقع لتفتح لك المكتبة فوراً! 🎬"
            )
            bot.reply_to(message, welcome_text, parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ عذراً, حدث خطأ أثناء الاتصال بقاعدة البيانات. أعد المحاولة لاحقاً.")

# معالجة الأزرار التفاعلية (Inline Keyboard Callback Engine)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.from_user.id != ADMIN_CHAT_ID:
            bot.answer_callback_query(call.id, text="❌ غير مصرح لك!")
            return
            
        if call.data == "gen_token":
            new_token = generate_and_save_token("المدير_العام")
            bot.answer_callback_query(call.id, text="تم التوليد والحفظ بنجاح! 🔥")
            bot.send_message(call.message.chat.id, f"👑 <b>توكن جديد تم حقنه في الفايربيز:</b>\n<code>{new_token}</code>", parse_mode="HTML")
            
        elif call.data == "view_stats":
            bot.answer_callback_query(call.id, text="جاري جلب إحصائيات النظام...")
            try:
                tokens_res = requests.get(f"{FIREBASE_DB_URL}cz_active_tokens.json", timeout=5).json() or {}
                blocks_res = requests.get(f"{FIREBASE_DB_URL}cz_blocked_users.json", timeout=5).json() or {}
                active_count = len(tokens_res)
                blocked_count = len(blocks_res)
            except Exception:
                active_count, blocked_count = "N/A", "N/A"
                
            stats_text = (
                "📊 <b>تقرير الإحصائيات الفوري للنظام:</b>\n\n"
                f"• التوكنات النشطة بالفايربيز حالياً: 🔑 <b>{active_count} توكن</b>\n"
                f"• الأجهزة المحظورة نهائياً: 🚫 <b>{blocked_count} جهاز</b>\n"
                "• حالة البوت: 🟢 يعمل بأعلى كفاءة"
            )
            bot.send_message(call.message.chat.id, stats_text, parse_mode="HTML")
            
        elif call.data == "how_to_broadcast":
            bot.answer_callback_query(call.id)
            instruction_text = (
                "📢 <b>طريقة بث الإعلانات والأخبار وتثبيتها:</b>\n\n"
                "لبث رسالة أو تنويه فوري وتثبيته في أعلى صفحة البوت، أرسل الأمر كالتالي:\n"
                "<code>/broadcast اكتب نص الخبر أو الإعلان هنا</code>"
            )
            bot.send_message(call.message.chat.id, instruction_text, parse_mode="HTML")

# ==========================================
# 📢 دالة البث التلقائي وتثبيت الرسائل (Broadcast & Auto-Pin Feature)
# ==========================================
@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
        
    # استخراج نص البث بعد الأمر
    command_text = message.text.replace('/broadcast', '').strip()
    
    if not command_text:
        bot.reply_to(message, "❌ <b>صيغة خاطئة!</b> يرجى كتابة الإعلان بعد الأمر، مثال:\n<code>/broadcast سهرة الليلة فيلم رعب فخم جداً!</code>", parse_mode="HTML")
        return
        
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        # بث التنويه للمدير وتثبيته تلقائياً ليكون ظاهراً ومعلقاً في الشات كإعلان رسمي فخم
        broadcast_msg = f"📢 <b>تنويه رسمي من إدارة سِينِمَا زُونْ:</b>\n\n{command_text}"
        sent_msg = bot.send_message(message.chat.id, broadcast_msg, parse_mode="HTML")
        bot.pin_chat_message(message.chat.id, sent_msg.message_id)
        
        bot.reply_to(message, "✅ <b>تم بث الإعلان بنجاح وتثبيته في أعلى المحادثة كرسالة معلقة!</b>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء معالجة البث والتثبيت المباشر: {e}")

# 🚀 تشغيل سيرفر الويب في مسار منفصل (Thread) قبل تشغيل البوت
server_thread = Thread(target=run_flask)
server_thread.start()

print("🤖 CinemaZone Guard Bot & API Alert System is starting on Web Port...")

try:
    bot.remove_webhook()
except Exception:
    pass

bot.infinity_polling(timeout=10, long_polling_timeout=5)
