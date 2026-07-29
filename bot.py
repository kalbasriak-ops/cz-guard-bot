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


# ==========================================
# 🛡️ [إضافة الحالة الأمنية الجديدة]: نظام حماية الأجهزة المتعددة والطرد
# ==========================================
@app.route('/api/security/verify-device', methods=['POST'])
def verify_device():
    """التحقق من بصمة العتاد ومنع تشغيل التوكن على أكثر من جهاز"""
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    username = data.get('username', 'عضو مجهول')
    fingerprint = data.get('fingerprint', '')

    if not token or not fingerprint:
        return jsonify({"allowed": False, "message": "⚠️ بيانات الأمان غير مكتملة."}), 400

    # الفحص المبدئي: إذا كانت بصمة هذا الجهاز محظورة مسبقاً بالكامل
    if is_hardware_blocked(fingerprint):
        return jsonify({
            "allowed": False, 
            "message": "🚨 تم حظر جهازك تلقائياً لحماية معايير الأمان."
        }), 403

    try:
        # 1. جلب بيانات التوكن من الفايربيز
        token_url = f"{FIREBASE_DB_URL}cz_active_tokens/{token}.json"
        token_response = requests.get(token_url, timeout=5)
        token_data = token_response.json()

        if not token_data:
            return jsonify({"allowed": False, "message": "❌ التوكن المستخدم غير صحيح أو منتهي الصلاحية."}), 401

        # 2. قفل التوكن على أول جهاز يقوم بتفعيله
        if "fingerprint" not in token_data:
            token_data["fingerprint"] = fingerprint
            requests.put(token_url, json=token_data, timeout=5)
            print(f"🔒 [Lock System] Token {token} locked to Device: {fingerprint}")
            return jsonify({"allowed": True, "message": "✅ تم تفعيل وقفل التوكن على جهازك الحالي بنجاح."}), 200

        # 3. نظام الطرد التلقائي في حال اختلف المعرف (فتح التوكن من جهاز آخر)
        elif token_data["fingerprint"] != fingerprint:
            # حظر حساب التلغرام المرتبط بالتوكن قسرياً
            block_user_in_firebase(token_data.get('chat_id', 'unknown'), username, f"مشاركة توكن مع جهاز آخر: {fingerprint}")
            
            # حظر بصمة العتاد الدخيلة في فرع مستقل للأجهزة وثقنا فيها التوكن والاسم للوحة التحكم والبحث
            safe_fw = fingerprint.replace('.', '_')
            block_hw_url = f"{FIREBASE_DB_URL}cz_blocked_hardware/{safe_fw}.json"
            requests.put(block_hw_url, json={
                "fingerprint": fingerprint,
                "username": username,
                "associated_token": token,
                "timestamp": int(time.time() * 1000),
                "reason": "مشاركة توكن وتعدد أجهزة في الموقع"
            }, timeout=5)

            # بث الإشعار للمدير فوراً
            alert_msg = (
                f"🚨 <b>خرق أمني: محاولة فتح توكن من جهازين!</b>\n\n"
                f"👤 <b>المستخدم:</b> {username}\n"
                f"🔑 <b>التوكن المستهدف:</b> <code>{token}</code>\n"
                f"🔒 <b>العتاد الأصلي:</b> <code>{token_data['fingerprint']}</code>\n"
                f"❌ <b>العتاد الدخيل (المطرود):</b> <code>{fingerprint}</code>\n\n"
                f"🔺 <i>تم حظر العتاد الدخيل وتفعيل الطرد التلقائي بنجاح!</i>"
            )
            send_telegram_alert(alert_msg)

            return jsonify({
                "allowed": False, 
                "message": "🚨 أمن المنصة: لا يمكن استخدام هذا التوكن على أكثر من جهاز! تم طرد المحاولة وحظر الجهاز تلقائياً."
            }), 403

        return jsonify({"allowed": True, "message": "مرحباً بك مجدداً في Cinema Zone."}), 200

    except Exception as e:
        return jsonify({"allowed": False, "message": f"❌ خطأ أمني: {e}"}), 500


def is_hardware_blocked(fingerprint):
    """دالة فحص ما إذا كان العتاد مسجلاً في القائمة السوداء للأجهزة بالفايربيز"""
    try:
        safe_fw = fingerprint.replace('.', '_')
        url = f"{FIREBASE_DB_URL}cz_blocked_hardware/{safe_fw}.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.json() is not None:
            return True
    except Exception:
        pass
    return False


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

def save_bot_subscriber(user_id, username):
    """تحديث الأمان: حفظ معرف المستخدم الفردي وحقن الـ chat_id قسرياً لضمان دقة العدادات والبث"""
    try:
        url = f"{FIREBASE_DB_URL}cz_bot_subscribers/{user_id}.json"
        subscriber_data = {
            "chat_id": user_id,
            "username": f"@{username}" if username else "عضو فخم",
            "last_interaction": int(time.time() * 1000)
        }
        requests.put(url, json=subscriber_data, timeout=3)
    except Exception as e:
        print(f"Error saving bot subscriber: {e}")

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

def generate_and_save_token(username=None, chat_id=None):
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
        "username": formatted_username,
        "chat_id": chat_id  # حفظ الـ chat_id كإجراء أمان إضافي للمساعدة في البث
    }
    
    try:
        url = f"{FIREBASE_DB_URL}cz_active_tokens/{token_code}.json"
        response = requests.put(url, json=token_data, timeout=5)
        if response.status_code == 200:
            return token_code
    except Exception as e:
        print(f"Error save to Firebase: {e}")
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

    save_bot_subscriber(user_id, username)

    if user_id not in user_requests:
        user_requests[user_id] = []
    
    user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < 10]
    user_requests[user_id].append(current_time)
    
    if len(user_requests[user_id]) > 5:
        block_user_in_firebase(user_id, username, "Spamming Bot Gateway")
        bot.reply_to(message, "❌ تم حظر حسابك تلقائياً بسبب محاولة إغراق النظام بالطلبات.")
        return

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
        new_token = generate_and_save_token(username, user_id)
        
        if new_token:
            welcome_text = (
                f"مرحباً بك في سِينِمَا زُونْ 🍿\n\n"
                f"تم توليد كود الدخول الآمن الخاص بك بنجاح:\n\n"
                f"<code>{new_token}</code>\n\n"
                f"⏳ الصلاحية: 10 دقائق فقط (استخدمه الآن قبل انتهاء صلاحيته).\n"
                f"قم بنسخ الكود وضعه في الموقع لتفتح لك المكتبة فوراً! 🎬"
            )
            bot.reply_to(message, welcome_text, parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ عذراً, حدث خطأ أثناء الاتصال بقاعدة البيانات. أعد المحاولة لاحقاً.")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.from_user.id != ADMIN_CHAT_ID:
            bot.answer_callback_query(call.id, text="❌ غير مصرح لك!")
            return
            
        if call.data == "gen_token":
            new_token = generate_and_save_token("المدير_العام", ADMIN_CHAT_ID)
            bot.answer_callback_query(call.id, text="تم التوليد والحفظ بنجاح! 🔥")
            bot.send_message(call.message.chat.id, f"👑 <b>توكن جديد تم حقنه في الفايربيز:</b>\n<code>{new_token}</code>", parse_mode="HTML")
            
        elif call.data == "view_stats":
            bot.answer_callback_query(call.id, text="جاري جلب إحصائيات النظام الفورية...")
            try:
                tokens_res = requests.get(f"{FIREBASE_DB_URL}cz_active_tokens.json", timeout=5).json() or {}
                blocks_res = requests.get(f"{FIREBASE_DB_URL}cz_blocked_users.json", timeout=5).json() or {}
                subs_res = requests.get(f"{FIREBASE_DB_URL}cz_bot_subscribers.json", timeout=5).json() or {}
                hw_blocks_res = requests.get(f"{FIREBASE_DB_URL}cz_blocked_hardware.json", timeout=5).json() or {}
                
                # حساب الطول الفعلي للمفاتيح لمنع مشكلة الـ None والـ List المفرغة نهائياً
                active_count = len(tokens_res.keys()) if isinstance(tokens_res, dict) else (len([x for x in tokens_res if x is not None]) if isinstance(tokens_res, list) else 0)
                blocked_count = len(blocks_res.keys()) if isinstance(blocks_res, dict) else (len([x for x in blocks_res if x is not None]) if isinstance(blocks_res, list) else 0)
                subs_count = len(subs_res.keys()) if isinstance(subs_res, dict) else (len([x for x in subs_res if x is not None]) if isinstance(subs_res, list) else 0)
                hw_blocked_count = len(hw_blocks_res.keys()) if isinstance(hw_blocks_res, dict) else (len([x for x in hw_blocks_res if x is not None]) if isinstance(hw_blocks_res, list) else 0)
                    
            except Exception as e:
                print(f"Error parsing stats metrics: {e}")
                active_count, blocked_count, subs_count, hw_blocked_count = "N/A", "N/A", "N/A", "N/A"
                
            stats_text = (
                "📊 <b>تقرير الإحصائيات الفوري للنظام:</b>\n\n"
                f"• إجمالي المشتركين بالبوت (للبث): 👥 <b>{subs_count} مستخدم</b>\n"
                f"• التوكنات النشطة بالفايربيز حالياً: 🔑 <b>{active_count} توكن</b>\n"
                f"• حسابات المستخدمين المحظورة: 🚫 <b>{blocked_count} حساب</b>\n"
                f"• أجهزة العتاد المحظورة أمنياً: 🛡️ <b>{hw_blocked_count} جهاز</b>\n\n"
                f"• حالة البوت: 🟢 يعمل بأعلى كفاءة"
            )
            bot.send_message(call.message.chat.id, stats_text, parse_mode="HTML")
            
        elif call.data == "how_to_broadcast":
            bot.answer_callback_query(call.id)
            instruction_text = (
                "📢 <b>طريقة بث الإعلانات والأخبار وتثبيتها:</b>\n\n"
                "لبث رسالة أو تنويه فوري وتثبيته في أعلى صفحة البوت لجميع المستخدمين، أرسل الأمر كالتالي:\n"
                "<code>/broadcast اكتب نص الخبر أو الإعلان هنا</code>"
            )
            bot.send_message(call.message.chat.id, instruction_text, parse_mode="HTML")

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
        
    command_text = message.text.replace('/broadcast', '').strip()
    
    if not command_text:
        bot.reply_to(message, "❌ <b>صيغة خاطئة!</b> يرجى كتابة الإعلان بعد الأمر, مثال:\n<code>/broadcast سهرة الليلة فيلم رعب فخم جداً!</code>", parse_mode="HTML")
        return
        
    bot.send_chat_action(message.chat.id, 'typing')
    broadcast_msg = f"📢 <b>تنويه رسمي من إدارة سِينِمَا زُونْ:</b>\n\n{command_text}"
    
    target_chat_ids = set()
    
    try:
        subs_url = f"{FIREBASE_DB_URL}cz_bot_subscribers.json"
        subs_response = requests.get(subs_url, timeout=5)
        subscribers = subs_response.json() or {}
        
        if isinstance(subscribers, dict):
            for uid in subscribers.keys():
                target_chat_ids.add(int(uid))
        elif isinstance(subscribers, list):
            for idx, val in enumerate(subscribers):
                if val is not None:
                    target_chat_ids.add(idx)
    except Exception as e:
        print(f"Error pulling subscribers: {e}")

    try:
        tokens_url = f"{FIREBASE_DB_URL}cz_active_tokens.json"
        tokens_response = requests.get(tokens_url, timeout=5)
        tokens_data = tokens_response.json() or {}
        if isinstance(tokens_data, dict):
            for t_info in tokens_data.values():
                if isinstance(t_info, dict) and t_info.get("chat_id"):
                    target_chat_ids.add(int(t_info.get("chat_id")))
    except Exception as e:
        print(f"Error pulling fallback token chat ids: {e}")

    if not target_chat_ids:
        bot.reply_to(message, "⚠️ لا يوجد مستخدمين مسجلين في قائمة البث حالياً.")
        return

    success_sends = 0
    failed_sends = 0

    for target_chat_id in target_chat_ids:
        try:
            sent = bot.send_message(target_chat_id, broadcast_msg, parse_mode="HTML")
            bot.pin_chat_message(target_chat_id, sent.message_id)
            success_sends += 1
            time.sleep(0.05)
        except Exception:
            failed_sends += 1

    report_text = (
        f"📢 <b>تمت عملية البث والتعليق بنجاح!</b>\n\n"
        f"🟢 تم الإرسال والتثبيت لـ: <b>{success_sends} مستخدم</b>\n"
        f"🔴 فشل الإرسال لـ: <b>{failed_sends} مستخدم</b> (بسبب حظر البوت)"
    )
    bot.reply_to(message, report_text, parse_mode="HTML")

# 🚀 تشغيل سيرفر الويب في مسار منفصل (Thread) قبل تشغيل البوت
server_thread = Thread(target=run_flask)
server_thread.start()

print("🤖 CinemaZone Guard Bot & API Alert System is starting on Web Port...")

try:
    bot.remove_webhook()
except Exception:
    pass

bot.infinity_polling(timeout=10, long_polling_timeout=5)
