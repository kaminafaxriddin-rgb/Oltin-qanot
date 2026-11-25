import os
import time
import json
import math
import threading
import requests
from flask import Flask

TOKEN = "9073466221:AAGQpv2_6_6UNTg7sRGdPNPln9xgLDFXREs"
MENING_ID = "771626113"
OXIRGI_UPDATE_ID = 0

BOT_FAOL = True
DEPOZIT = 1000.0
STATISTIKA = {"tp": 0, "sl": 0}

app = Flask(__name__)

@app.route("/")
def home():
    return "Oltin Qanot V11.0 MODULAR PRO 24/7 ishlamoqda!"

AKTIVLAR = {
    "GOLD": {"ticker": "GC=F", "nomi": "🥇 OLTIN (XAU/USD)", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 2, "p100": 1.0, "sl75": 0.75, "p200": 2.0, "sl150": 1.5, "pip_qiymat": 10.0},
    "SILVER": {"ticker": "SI=F", "nomi": "🥈 KUMUSH (XAG/USD)", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 3, "p100": 0.100, "sl75": 0.075, "p200": 0.200, "sl150": 0.150, "pip_qiymat": 5.0},
    "BTC": {"ticker": "BTC-USD", "nomi": "₿ BITCOIN (BTC/USD)", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 2, "p100": 100.0, "sl75": 75.0, "p200": 200.0, "sl150": 150.0, "pip_qiymat": 1.0},
    "ETH": {"ticker": "ETH-USD", "nomi": "🔷 ETHEREUM (ETH/USD)", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 2, "p100": 10.0, "sl75": 7.5, "p200": 20.0, "sl150": 15.0, "pip_qiymat": 1.0},
    "SOL": {"ticker": "SOL-USD", "nomi": "🟣 SOLANA (SOL/USD)", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 2, "p100": 1.0, "sl75": 0.75, "p200": 2.0, "sl150": 1.5, "pip_qiymat": 1.0},
    "EUR": {"ticker": "EURUSD=X", "nomi": "💶 EUR/USD", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 4, "p100": 0.0010, "sl75": 0.0008, "p200": 0.0020, "sl150": 0.0015, "pip_qiymat": 10.0},
    "GBP": {"ticker": "GBPUSD=X", "nomi": "💷 GBP/USD", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 4, "p100": 0.0010, "sl75": 0.0008, "p200": 0.0020, "sl150": 0.0015, "pip_qiymat": 10.0},
    "OIL": {"ticker": "BZ=F", "nomi": "🛢 BRENT NEFTI", "savdo": None, "skalp": None, "mikro": None, "aniqlik": 2, "p100": 0.10, "sl75": 0.08, "p200": 0.20, "sl150": 0.15, "pip_qiymat": 10.0}
}

def asosiy_klaviatura():
    holat_tugma = "⏸ Pauza" if BOT_FAOL else "▶️ Davom etish"
    return {
        "keyboard": [
            [{"text": "🥇 Oltin"}, {"text": "🥈 Kumush"}, {"text": "🛢 Neft"}],
            [{"text": "₿ BTC"}, {"text": "🔷 ETH"}, {"text": "🟣 SOL"}],
            [{"text": "💶 EUR/USD"}, {"text": "💷 GBP/USD"}, {"text": "📝 So'zli Analiz"}],
            [{"text": "⚡ 100 Pips"}, {"text": "🔥 200 Pips"}, {"text": "🌡 Bozor Kayfiyati"}],
            [{"text": "💰 Barcha Narxlar"}, {"text": "📊 Faol Signallar"}, {"text": "🧮 Lot Hisoblash"}],
            [{"text": "📈 Statistika"}, {"text": holat_tugma}, {"text": "🗑 Tozalash"}]
        ],
        "resize_keyboard": True
    }

def analiz_klaviaturasi():
    return {
        "keyboard": [
            [{"text": "📝 Oltin Analizi"}, {"text": "📝 Kumush Analizi"}, {"text": "📝 Neft Analizi"}],
            [{"text": "📝 BTC Analizi"}, {"text": "📝 ETH Analizi"}, {"text": "📝 SOL Analizi"}],
            [{"text": "📝 EUR/USD Analizi"}, {"text": "📝 GBP/USD Analizi"}],
            [{"text": "🔙 Orqaga"}]
        ],
        "resize_keyboard": True
    }

def telegramga_yuborish(xabar, menyu="asosiy"):
    dom = "api.telegram" + ".org/bot"
    url = "https://" + dom + TOKEN + "/sendMessage"
    klaviatura = analiz_klaviaturasi() if menyu == "analiz" else asosiy_klaviatura()
    data = {"chat_id": MENING_ID, "text": xabar, "reply_markup": json.dumps(klaviatura)}
    requests.post(url, data=data, timeout=15)

def ema_hisoblash(narxlar, davr):
    k = 2 / (davr + 1)
    birinchi = next(iter(narxlar))
    ema = [birinchi]
    for narx in narxlar[1:]:
        ema.append(narx * k + ema[-1] * (1 - k))
    return ema

def macd_hisoblash(narxlar):
    ema12 = ema_hisoblash(narxlar, 12)
    ema26 = ema_hisoblash(narxlar, 26)
    macd_chiziq = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
    signal_chiziq = ema_hisoblash(macd_chiziq, 9)
    return macd_chiziq, signal_chiziq

def bollinger_hisoblash(narxlar, davr=20):
    oxirgi_qism = narxlar[-davr:]
    ortacha = sum(oxirgi_qism) / davr
    dispersiya = sum((x - ortacha) ** 2 for x in oxirgi_qism) / davr
    ogish = math.sqrt(dispersiya)
    return ortacha + (2 * ogish), ortacha, ortacha - (2 * ogish)

def rsi_hisoblash(narxlar, davr=14):
    farqlar = [narxlar[i] - narxlar[i - 1] for i in range(1, len(narxlar))]
    osish = [f if f > 0 else 0 for f in farqlar[-davr:]]
    tushish = [-f if f < 0 else 0 for f in farqlar[-davr:]]
    ortacha_osish = sum(osish) / davr
    ortacha_tushish = sum(tushish) / davr
    if ortacha_tushish == 0:
        return 100
    rs = ortacha_osish / ortacha_tushish
    return 100 - (100 / (1 + rs))

def malumot_olish(ticker, interval, range_val):
    y_dom = "query1.finance.yahoo" + ".com/v8/finance/chart/"
    url = f"https://{y_dom}{ticker}?interval={interval}&range={range_val}"
    headers = {"User-Agent": "Mozilla/5.0"}
    javob = requests.get(url, headers=headers, timeout=15).json()
    natija = next(iter(javob["chart"]["result"]))
    quote = next(iter(natija["indicators"]["quote"]))
    close = [n for n in quote["close"] if n is not None]
    high = [n for n in quote["high"] if n is not None]
    low = [n for n in quote["low"] if n is not None]
    return close, high, low

def atr_hisoblash(high, low, close, davr=14):
    tr_list = []
    for i in range(1, len(close)):
        tr = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        tr_list.append(tr)
    return sum(tr_list[-davr:]) / davr

def lot_tavsiya(kalit):
    risk_summa = DEPOZIT * 0.02
    lot = round(risk_summa / (15 * AKTIVLAR[kalit]["pip_qiymat"]), 2)
    return max(0.01, lot)

def katta_trend_olish(ticker):
    c1h, _, _ = malumot_olish(ticker, "1h", "5d")
    ema50 = ema_hisoblash(c1h, 50)
    return "BUY" if c1h[-1] > ema50[-1] else "SELL"

def sozli_analiz_tayyorla(kalit):
    ticker = AKTIVLAR[kalit]["ticker"]
    nomi = AKTIVLAR[kalit]["nomi"]
    anq = AKTIVLAR[kalit]["aniqlik"]
    c15, h15, l15 = malumot_olish(ticker, "15m", "5d")
    c1h, _, _ = malumot_olish(ticker, "1h", "1mo")
    c4h, _, _ = malumot_olish(ticker, "4h", "3mo")
    narx = round(c15[-1], anq)
    ema9 = ema_hisoblash(c15, 9)
    ema21 = ema_hisoblash(c15, 21)
    ema50_1h = ema_hisoblash(c1h, 50)
    ema50_4h = ema_hisoblash(c4h, 50)
    macd_l, sig_l = macd_hisoblash(c15)
    rsi = round(rsi_hisoblash(c15, 14), 1)
    max_24h = round(max(h15[-96:]), anq)
    min_24h = round(min(l15[-96:]), anq)
    t4 = "yuqoriga" if narx > ema50_4h[-1] else "pastga"
    t1 = "yuqoriga" if narx > ema50_1h[-1] else "pastga"
    qisqa = "xaridorlar qo'lida (EMA9 > EMA21)" if ema9[-1] > ema21[-1] else "sotuvchilar qo'lida (EMA9 < EMA21)"
    impuls = "o'sish impulsi kuchaymoqda" if macd_l[-1] > sig_l[-1] else "pasayish bosimi ortmoqda"
    if rsi > 70:
        rsi_izoh = f"RSI ({rsi}) haddan tashqari qizib ketgan — orqaga qaytish xavfi bor, shoshilib BUY ochmang."
    elif rsi < 30:
        rsi_izoh = f"RSI ({rsi}) haddan tashqari sotilgan — pastdan yuqoriga sakrash ehtimoli yuqori, shoshilib SELL ochmang."
    else:
        rsi_izoh = f"RSI ({rsi}) me'yoriy zonada — narx tanlangan yo'nalishda davom etishi uchun yetarli zaxira bor."
    if t4 == "yuqoriga" and t1 == "yuqoriga":
        xulosa = "4H va 1H katta trendlar bir ovozdan YUQORIGA qaragan. Faqat narx tayanchga tekkanda BUY izlash eng to'g'ri strategiya."
    elif t4 == "pastga" and t1 == "pastga":
        xulosa = "4H va 1H katta trendlar bir ovozdan PASTGA qaragan. Narx tepaga ko'tarilib qarshilikka urilganda SELL izlash eng xavfsiz yo'l."
    else:
        xulosa = f"4H trend {t4}, 1H trend esa {t1} yo'nalgan. Faqat kichik (100/200 pips) skalping bilan ishlash tavsiya etiladi."
    matn = f"📝 {nomi} — SO'Z BILAN BATAFSIL ANALIZ\n\n💰 Joriy narx: {narx} (Max: {max_24h} | Min: {min_24h})\n\n1️⃣ Trend: 4H {t4}, 1H {t1}. Qisqa ustunlik {qisqa} va {impuls}.\n\n2️⃣ Kuch: {rsi_izoh}\n\n3️⃣ Xulosa: {xulosa}"
    telegramga_yuborish(matn, menyu="analiz")

def savdoni_kuzatish(kalit, joriy_narx):
    nomi = AKTIVLAR[kalit]["nomi"]
    savdo = AKTIVLAR[kalit]["savdo"]
    if savdo is not None:
        if savdo["turi"] == "BUY":
            if not savdo["tp1_yetdi"] and joriy_narx >= savdo["tp1"]:
                savdo["tp1_yetdi"] = True
                STATISTIKA["tp"] += 1
                telegramga_yuborish(f"✅ {nomi} (SNAYPER): TP1 FOYDA! ({savdo['tp1']}) | SL ni {savdo['kirish']} ga suring.")
            elif joriy_narx >= savdo["tp2"]:
                STATISTIKA["tp"] += 1
                telegramga_yuborish(f"🏆 {nomi} (SNAYPER): TP2 YOPILDI! ({savdo['tp2']})")
                AKTIVLAR[kalit]["savdo"] = None
            elif joriy_narx <= savdo["sl"]:
                STATISTIKA["sl"] += 1
                telegramga_yuborish(f"🛑 {nomi} (SNAYPER): STOP LOSS ({savdo['sl']}).")
                AKTIVLAR[kalit]["savdo"] = None
        elif savdo["turi"] == "SELL":
            if not savdo["tp1_yetdi"] and joriy_narx <= savdo["tp1"]:
                savdo["tp1_yetdi"] = True
                STATISTIKA["tp"] += 1
                telegramga_yuborish(f"✅ {nomi} (SNAYPER): TP1 FOYDA! ({savdo['tp1']}) | SL ni {savdo['kirish']} ga suring.")
            elif joriy_narx <= savdo["tp2"]:
                STATISTIKA["tp"] += 1
                telegramga_yuborish(f"🏆 {nomi} (SNAYPER): TP2 YOPILDI! ({savdo['tp2']})")
                AKTIVLAR[kalit]["savdo"] = None
            elif joriy_narx >= savdo["sl"]:
                STATISTIKA["sl"] += 1
                telegramga_yuborish(f"🛑 {nomi} (SNAYPER): STOP LOSS ({savdo['sl']}).")
                AKTIVLAR[kalit]["savdo"] = None
    skalp = AKTIVLAR[kalit]["skalp"]
    if skalp is not None:
        if skalp["turi"] == "BUY":
            if joriy_narx >= skalp["tp"]:
                STATISTIKA["tp"] += 1
                telegramga_yuborish(f"🔥✅ {nomi} (200 PIPS): FOYDA YOPILDI! ({skalp['tp']})")
                AKTIVLAR[kalit]["skalp"] = None
