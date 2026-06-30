import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types
import random
import string
import time
import requests

# --- خدعة المنفذ لموقع Render ---
app = Flask(__name__)
@app.route('/')
def home(): return "CinemaZone Guard is Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run).start()
# ------------------------------

BOT_TOKEN = "8891273359:AAEnUSaKQrz7TYMUuGmNIXyKNgMbuNqtlHg"
bot = telebot.TeleBot(BOT_TOKEN)
FIREBASE_DB_URL = "https://cinemazone-a11ba-default-rtdb.europe-west1.firebasedatabase.app/"

def generate_and_save_token():
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    token_code = f"cz_{random_suffix}"
    expiry_time = int((time.time() + (10 * 60)) * 1000)
    created_time = int(time.time() * 1000)
    token_data = {"expiry": expiry_time, "created": created_time}
    try:
        url = f"{FIREBASE_DB_URL}cz_active_tokens/{token_code}.json"
        response = requests.put(url, json=token_data)
        if response.status_code == 200: return token_code
    except: pass
    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id == 7861493:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("توليد توكن ⚡", callback_data="gen_token"))
        bot.reply_to(message, "👑 أهلاً بك يا قائد، الحارس نشط!", reply_markup=markup)
    else:
        new_token = generate_and_save_token()
        if new_token:
            bot.reply_to(message, f"مرحباً في سِينِمَا زُونْ 🍿\nكود دخولك: `{new_token}`\n⏳ صلاحية: 10 دقائق.", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "gen_token")
def callback_inline(call):
    new_token = generate_and_save_token()
    bot.answer_callback_query(call.id, text="تم التوليد!")
    bot.send_message(call.message.chat.id, f"`{new_token}`", parse_mode="Markdown")

bot.infinity_polling()
