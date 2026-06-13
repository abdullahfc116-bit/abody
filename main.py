import telebot
import os
import requests
from flask import Flask
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def get_tiktok_data(url):
    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        response = requests.get(api_url).json()
        if response.get('code') == 0:
            return response['data']
    except:
        pass
    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 مرحباً بك في بوت تحميل من تيك توك الخاص بك! 📱✨\n\nأرسل رابط الفيديو وسأقوم بتحميله لك فوراً. 🚀")

@bot.message_handler(func=lambda message: message.text and "tiktok.com" in message.text)
def handle_tiktok(message):
    url = message.text
    msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو...")
    data = get_tiktok_data(url)
    if data:
        bot.send_video(message.chat.id, data['play'], caption="🎬 تم التحميل بنجاح ✅")
        bot.delete_message(message.chat.id, msg.message_id)
    else:
        bot.edit_message_text("❌ فشل التحميل، يرجى التأكد من الرابط.", message.chat.id, msg.message_id)

if __name__ == '__main__':
    Thread(target=run).start()
    bot.infinity_polling()
