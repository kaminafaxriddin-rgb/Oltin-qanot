import os
import time
import threading
import telebot
from telebot import types
from flask import Flask
from config import BOT_TOKEN, ADMIN_ID, SYMBOLS
from analyzer import get_signal
from tracker import add_trade, check_active_trades, get_active_list, get_stats_text

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Oltin Qanot 24/7 Snayper va Kuzatuv Tizimi Faol!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(name) for name in SYMBOLS.keys()]
    markup.add(*buttons)
    markup.add(
        types.KeyboardButton("🔍 Hamma bozorni tekshirish"),
        types.KeyboardButton("📊 Faol Signallar"),
        types.KeyboardButton("📈 Statistika")
    )
    return markup

def is_owner(message):
    return message.from_user.id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not is_owner(message):
        return
    bot.send_message(
        message.chat.id,
        "🦅 **Oltin Qanot — To'liq Nazorat Tizimi**\n\n"
        "✅ Mayda, Snayper va Ultra Snayper signallar\n"
        "✅ Avtomatik Breakeven (zararsiz nuqtaga surish)\n"
        "✅ TP (Foyda) va SL (Stop Loss) urilganda darhol chiqish xabari\n"
        "✅ Siz uxlayotganingizda 24/7 kuzatuv",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_owner(message):
        return

    text = message.text

    if text in SYMBOLS:
        wait_msg = bot.send_message(message.chat.id, f"⏳ {text} tahlil qilinmoqda...")
        sig_data = get_signal(text)
        bot.delete_message(message.chat.id, wait_msg.message_id)
        if sig_data:
            add_trade(sig_data)
            bot.send_message(message.chat.id, sig_data["text"], parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"⚪️ Hozircha **{text}** uchun aniq signal yo'q.", parse_mode="Markdown")

    elif text == "🔍 Hamma bozorni tekshirish":
        bot.send_message(message.chat.id, "📡 Barcha bozorlar tekshirilmoqda...")
        found = 0
        for asset in SYMBOLS.keys():
            sig_data = get_signal(asset)
            if sig_data:
                if add_trade(sig_data):
                    bot.send_message(message.chat.id, sig_data["text"], parse_mode="Markdown")
                    found += 1
            time.sleep(1)
        if found == 0:
            bot.send_message(message.chat.id, "📉 Yangi signallar topilmadi. Faol signallar kuzatuvda.")

    elif text == "📊 Faol Signallar":
        bot.send_message(message.chat.id, get_active_list(), parse_mode="Markdown")

    elif text == "📈 Statistika":
        bot.send_message(message.chat.id, get_stats_text(), parse_mode="Markdown")

def signal_scanner_loop():
    while True:
        for asset in SYMBOLS.keys():
            sig_data = get_signal(asset)
            if sig_data:
                if add_trade(sig_data):
                    try:
                        bot.send_message(ADMIN_ID, f"🔔 **YANGI AVTO-SIGNAL!**\n\n{sig_data['text']}", parse_mode="Markdown")
                    except Exception as e:
                        print(f"Xabar xatosi: {e}")
            time.sleep(4)
        time.sleep(180)

def trade_monitor_loop():
    while True:
        alerts = check_active_trades()
        for alert_msg in alerts:
            try:
                bot.send_message(ADMIN_ID, alert_msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Chiqish xabarida xato: {e}")
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=signal_scanner_loop, daemon=True).start()
    threading.Thread(target=trade_monitor_loop, daemon=True).start()
    bot.infinity_polling(timeout=15, long_polling_timeout=10)
