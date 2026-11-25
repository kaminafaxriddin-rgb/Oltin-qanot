import os, time, json, math, threading, requests
from flask import Flask

TOKEN = "9073466221:AAGQpv2_6_6UNTg7sRGdPNPln9xgLDFXREs"
MENING_ID = "771626113"
OXIRGI_UPDATE_ID = 0
BOT_FAOL = True
DEPOZIT = 1000.0
STAT = {"tp": 0, "sl": 0}

app = Flask(__name__)

@app.route("/")
def home():
    return "Oltin Qanot V11.0 24/7 Live!"

AKTIVLAR = {
    "GOLD": {"t": "GC=F", "n": "🥇 OLTIN", "s": None, "sk": None, "mk": None, "a": 2, "p1": 1.0, "sl1": 0.75, "p2": 2.0, "sl2": 1.5, "pq": 10.0},
    "SILVER": {"t": "SI=F", "n": "🥈 KUMUSH", "s": None, "sk": None, "mk": None, "a": 3, "p1": 0.1, "sl1": 0.075, "p2": 0.2, "sl2": 0.15, "pq": 5.0},
    "BTC": {"t": "BTC-USD", "n": "₿ BTC", "s": None, "sk": None, "mk": None, "a": 2, "p1": 100.0, "sl1": 75.0, "p2": 200.0, "sl2": 150.0, "pq": 1.0},
    "ETH": {"t": "ETH-USD", "n": "🔷 ETH", "s": None, "sk": None, "mk": None, "a": 2, "p1": 10.0, "sl1": 7.5, "p2": 20.0, "sl2": 15.0, "pq": 1.0},
    "SOL": {"t": "SOL-USD", "n": "🟣 SOL", "s": None, "sk": None, "mk": None, "a": 2, "p1": 1.0, "sl1": 0.75, "p2": 2.0, "sl2": 1.5, "pq": 1.0},
    "EUR": {"t": "EURUSD=X", "n": "💶 EUR/USD", "s": None, "sk": None, "mk": None, "a": 4, "p1": 0.001, "sl1": 0.0008, "p2": 0.002, "sl2": 0.0015, "pq": 10.0},
    "GBP": {"t": "GBPUSD=X", "n": "💷 GBP/USD", "s": None, "sk": None, "mk": None, "a": 4, "p1": 0.001, "sl1": 0.0008, "p2": 0.002, "sl2": 0.0015, "pq": 10.0},
    "OIL": {"t": "BZ=F", "n": "🛢 NEFT", "s": None, "sk": None, "mk": None, "a": 2, "p1": 0.1, "sl1": 0.08, "p2": 0.2, "sl2": 0.15, "pq": 10.0}
}

def yubor(xabar, menyu="asosiy"):
    baza = "https://api." + "telegram.org/b" + "ot"
    url = baza + TOKEN + "/sendMessage"


    p_btn = "⏸ Pauza" if BOT_FAOL else "▶️ Davom etish"
    kb = {
        "keyboard": [
            [{"text": "🥇 Oltin"}, {"text": "🥈 Kumush"}, {"text": "🛢 Neft"}],
            [{"text": "₿ BTC"}, {"text": "🔷 ETH"}, {"text": "🟣 SOL"}],
            [{"text": "💶 EUR/USD"}, {"text": "💷 GBP/USD"}, {"text": "📝 So'zli Analiz"}],
            [{"text": "⚡ 100 Pips"}, {"text": "🔥 200 Pips"}, {"text": "🌡 Bozor Kayfiyati"}],
            [{"text": "💰 Barcha Narxlar"}, {"text": "📊 Faol Signallar"}, {"text": "🧮 Lot Hisoblash"}],
            [{"text": "📈 Statistika"}, {"text": p_btn}, {"text": "🗑 Tozalash"}]
        ], "resize_keyboard": True
    }
    if menyu == "analiz":
        kb = {
            "keyboard": [
                [{"text": "📝 Oltin Analizi"}, {"text": "📝 Kumush Analizi"}, {"text": "📝 Neft Analizi"}],
                [{"text": "📝 BTC Analizi"}, {"text": "📝 ETH Analizi"}, {"text": "📝 SOL Analizi"}],
                [{"text": "📝 EUR/USD Analizi"}, {"text": "📝 GBP/USD Analizi"}, {"text": "🔙 Orqaga"}]
            ], "resize_keyboard": True
        }
    requests.post(url, data={"chat_id": MENING_ID, "text": xabar, "reply_markup": json.dumps(kb)}, timeout=15)

def ema(arr, d):
    k = 2 / (d + 1)
    res = [arr[0]]
    for x in arr[1:]:
        res.append(x * k + res[-1] * (1 - k))
    return res

def rsi(arr, d=14):
    dif = [arr[i] - arr[i - 1] for i in range(1, len(arr))]
    up = sum(x if x > 0 else 0 for x in dif[-d:]) / d
    dn = sum(-x if x < 0 else 0 for x in dif[-d:]) / d
    return 100 if dn == 0 else 100 - (100 / (1 + up / dn))

def get_data(t, iv, rg):
    url = f"https://yahoo.com{t}?interval={iv}&range={rg}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).json()["chart"]["result"][0]["indicators"]["quote"][0]
    return [x for x in r["close"] if x], [x for x in r["high"] if x], [x for x in r["low"] if x]

def lot_calc(k):
    return max(0.01, round((DEPOZIT * 0.02) / (15 * AKTIVLAR[k]["pq"]), 2))

def analiz_yoz(k):
    a = AKTIVLAR[k]
    c15, h15, l15 = get_data(a["t"], "15m", "5d")
    c1h, _, _ = get_data(a["t"], "1h", "1mo")
    c4h, _, _ = get_data(a["t"], "4h", "3mo")
    p = round(c15[-1], a["a"])
    e9, e21, e1h, e4h = ema(c15, 9), ema(c15, 21), ema(c1h, 50), ema(c4h, 50)
    r = round(rsi(c15), 1)
    t4 = "yuqoriga" if p > e4h[-1] else "pastga"
    t1 = "yuqoriga" if p > e1h[-1] else "pastga"
    q = "xaridorlar qo'lida" if e9[-1] > e21[-1] else "sotuvchilar qo'lida"
    izoh = "RSI qizib ketgan, korreksiya xavfi bor." if r > 70 else ("RSI sotilgan zonada, sakrash kutilmoqda." if r < 30 else "RSI me'yoriy, trend davom etishi mumkin.")
    xul = "4H va 1H YUQORIGA — tayanchdan BUY qulay." if t4 == "yuqoriga" and t1 == "yuqoriga" else ("4H va 1H PASTGA — qarshilikdan SELL qulay." if t4 == "pastga" and t1 == "pastga" else "Trendlar aralash — faqat 100/200 pips skalping qiling.")
    yubor(f"📝 {a['n']} — SO'ZLI ANALIZ\n\n💰 Narx: {p} (Max: {round(max(h15[-96:]), a['a'])} | Min: {round(min(l15[-96:]), a['a'])})\n1️⃣ Trend: 4H {t4}, 1H {t1}. Qisqa ustunlik {q}.\n2️⃣ RSI ({r}): {izoh}\n3️⃣ Xulosa: {xul}", "analiz")

def kuzat(k, p):
    a = AKTIVLAR[k]
    for key, label in [("s", "SNAYPER"), ("sk", "200 PIPS"), ("mk", "100 PIPS")]:
        st = a[key]
        if not st:
            continue
        if st["t"] == "BUY":
            if p >= st["tp"]:
                STAT["tp"] += 1
                yubor(f"✅ {a['n']} ({label}): FOYDA YOPILDI! ({st['tp']})")
                a[key] = None
            elif p <= st["sl"]:
                STAT["sl"] += 1
                yubor(f"🛑 {a['n']} ({label}): STOP LOSS ({st['sl']})")
                a[key] = None
        else:
            if p <= st["tp"]:
                STAT["tp"] += 1
                yubor(f"✅ {a['n']} ({label}): FOYDA YOPILDI! ({st['tp']})")
                a[key] = None
            elif p >= st["sl"]:
                STAT["sl"] += 1
                yubor(f"🛑 {a['n']} ({label}): STOP LOSS ({st['sl']})")
                a[key] = None

def tekshir(k, rejim="avto"):
    a = AKTIVLAR[k]
    c15, h15, l15 = get_data(a["t"], "15m", "5d")
    p = round(c15[-1], a["a"])
    kuzat(k, p)
    if rejim == "narx":
        return f"{a['n']}: {p}"
    c1h, _, _ = get_data(a["t"], "1h", "1mo")
    c4h, _, _ = get_data(a["t"], "4h", "3mo")
    e9, e21, e1h, e4h = ema(c15, 9), ema(c15, 21), ema(c1h, 50), ema(c4h, 50)
    r = round(rsi(c15), 1)
    buy = (30 if p > e4h[-1] else 0) + (30 if p > e1h[-1] else 0) + (25 if e9[-1] > e21[-1] else 0) + (15 if 50 < r < 72 else 0)
    sell = (30 if p < e4h[-1] else 0) + (30 if p < e1h[-1] else 0) + (25 if e9[-1] < e21[-1] else 0) + (15 if 28 < r < 50 else 0)
    if rejim == "kayfiyat":
        return f"{a['n']}: {'🟢 BUY ' + str(buy) + '%' if buy >= sell else '🔴 SELL ' + str(sell) + '%'}"
    if rejim == "tahlil":
        yubor(f"🎯 {a['n']} — QISQA TAHLIL\n\n💰 Narx: {p}\n📈 RSI: {r} | 🧮 Lot: {lot_calc(k)}\n🟢 BUY: {buy}% | 🔴 SELL: {sell}%")
        return
    if not BOT_FAOL:
        return
    tr = "BUY" if p > e1h[-1] else "SELL"
    c1, _, _ = get_data(a["t"], "1m", "1d")
    p1 = round(c1[-1], a["a"])
    if a["mk"] is None:
        m3, m8 = ema(c1, 3), ema(c1, 8)
        if tr == "BUY" and m3[-2] <= m8[-2] and m3[-1] > m8[-1]:
            a["mk"] = {"t": "BUY", "in": p1, "tp": round(p1 + a["p1"], a["a"]), "sl": round(p1 - a["sl1"], a["a"])}
            yubor(f"⚡ 100 PIPS BUY — {a['n']}\n💰 Kirish: {p1}\n🎯 TP: {a['mk']['tp']}\n🛑 SL: {a['mk']['sl']}\n🧮 Lot: {lot_calc(k)}")
        elif tr == "SELL" and m3[-2] >= m8[-2] and m3[-1] < m8[-1]:
            a["mk"] = {"t": "SELL", "in": p1, "tp": round(p1 - a["p1"], a["a"]), "sl": round(p1 + a["sl1"], a["a"])}
            yubor(f"⚡ 100 PIPS SELL — {a['n']}\n💰 Kirish: {p1}\n🎯 TP: {a['mk']['tp']}\n🛑 SL: {a['mk']['sl']}\n🧮 Lot: {lot_calc(k)}")
    c5, _, _ = get_data(a["t"], "5m", "1d")
    p5 = round(c5[-1], a["a"])
    if a["sk"] is None:
        s5, s13 = ema(c5, 5), ema(c5, 13)
        if tr == "BUY" and s5[-2] <= s13[-2] and s5[-1] > s13[-1]:
            a["sk"] = {"t": "BUY", "in": p5, "tp": round(p5 + a["p2"], a["a"]), "sl": round(p5 - a["sl2"], a["a"])}
            yubor(f"🔥 200 PIPS BUY — {a['n']}\n💰 Kirish: {p5}\n🎯 TP: {a['sk']['tp']}\n🛑 SL: {a['sk']['sl']}\n🧮 Lot: {lot_calc(k)}")
        elif tr == "SELL" and s5[-2] >= s13[-2] and s5[-1] < s13[-1]:
            a["sk"] = {"t": "SELL", "in": p5, "tp": round(p5 - a["p2"], a["a"]), "sl": round(p5 + a["sl2"], a["a"])}
            yubor(f"🔥 200 PIPS SELL — {a['n']}\n💰 Kirish: {p5}\n🎯 TP: {a['sk']['tp']}\n🛑 SL: {a['sk']['sl']}\n🧮 Lot: {lot_calc(k)}")
    if a["s"] is None:
        atr = sum(h15[i] - l15[i] for i in range(-14, 0)) / 14
        if e9[-2] < e21[-2] and e9[-1] > e21[-1] and buy >= 85:
            a["s"] = {"t": "BUY", "in": p, "tp": round(p + atr * 3, a["a"]), "sl": round(p - atr * 1.5, a["a"])}
            yubor(f"🎯 SNAYPER BUY — {a['n']}\n💰 Kirish: {p}\n🎯 TP: {a['s']['tp']}\n🛑 SL: {a['s']['sl']}\n🧮 Lot: {lot_calc(k)}")
        elif e9[-2] > e21[-2] and e9[-1] < e21[-1] and sell >= 85:
            a["s"] = {"t": "SELL", "in": p, "tp": round(p - atr * 3, a["a"]), "sl": round(p + atr * 1.5, a["a"])}
            yubor(f"🎯 SNAYPER SELL — {a['n']}\n💰 Kirish: {p}\n🎯 TP: {a['s']['tp']}\n🛑 SL: {a['s']['sl']}\n🧮 Lot: {lot_calc(k)}")

def loop_bot():
    global OXIRGI_UPDATE_ID, BOT_FAOL, DEPOZIT
    yubor("🚀 Oltin Qanot V11.0 24/7 ishga tushdi!")
    last_scan = 0
    btns = {"/start": "GOLD", "🥇 Oltin": "GOLD", "🥈 Kumush": "SILVER", "🛢 Neft": "OIL", "₿ BTC": "BTC", "🔷 ETH": "ETH", "🟣 SOL": "SOL", "💶 EUR/USD": "EUR", "💷 GBP/USD": "GBP"}
    abtn = {"📝 Oltin Analizi": "GOLD", "📝 Kumush Analizi": "SILVER", "📝 Neft Analizi": "OIL", "📝 BTC Analizi": "BTC", "📝 ETH Analizi": "ETH", "📝 SOL Analizi": "SOL", "📝 EUR/USD Analizi": "EUR", "📝 GBP/USD Analizi": "GBP"}
    while True:
        try:
            baza = "https://api." + "telegram.org/b" + "ot"
            res = requests.get(baza + TOKEN + "/getUpdates?offset=" + str(OXIRGI_UPDATE_ID + 1) + "&timeout=10", timeout=15).json().get("result", [])

            for it in res:
                OXIRGI_UPDATE_ID = it["update_id"]
                msg = it.get("message", {})
                
                if str(msg.get("from", {}).get("id", "")) != MENING_ID:
                    continue
                txt = msg.get("text", "")
                if txt in btns:
                    tekshir(btns[txt], "tahlil")
                elif txt in abtn:
                    analiz_yoz(abtn[txt])
                elif txt == "📝 So'zli Analiz":
                    yubor("📝 Qaysi aktivning so'zli analizini o'qiysiz?", "analiz")
                elif txt == "🔙 Orqaga":
                    yubor("🔙 Asosiy menyu", "asosiy")
                elif txt == "🌡 Bozor Kayfiyati":
                    yubor("🌡 KAYFIYAT:\n\n" + "\n".join(tekshir(k, "kayfiyat") for k in AKTIVLAR))
                elif txt == "💰 Barcha Narxlar":
                    yubor("💰 NARXLAR:\n\n" + "\n".join(tekshir(k, "narx") for k in AKTIVLAR))
                elif txt == "🧮 Lot Hisoblash":
                    yubor(f"🧮 LOT (${int(DEPOZIT)}):\n\n" + "\n".join(f"{AKTIVLAR[k]['n']}: {lot_calc(k)}" for k in AKTIVLAR) + "\n\nO'zgartirish: lot 500")
                elif txt.lower().startswith("lot "):
                    DEPOZIT = float(txt.split()[1])
                    yubor(f"✅ Depozit ${int(DEPOZIT)} bo'ldi!")
                elif txt == "⏸ Pauza":
                    BOT_FAOL = False
                    yubor("⏸ Pauza yoqildi.")
                elif txt == "▶️ Davom etish":
                    BOT_FAOL = True
                    yubor("▶️ Bot davom etmoqda!")
                elif txt == "🗑 Tozalash":
                    for k in AKTIVLAR:
                        AKTIVLAR[k]["s"] = AKTIVLAR[k]["sk"] = AKTIVLAR[k]["mk"] = None
                    yubor("🗑 Signallar tozalandi.")
                elif txt == "📊 Faol Signallar":
                    out = [f"{AKTIVLAR[k]['n']}: {AKTIVLAR[k][x]['t']} @ {AKTIVLAR[k][x]['in']}" for k in AKTIVLAR for x in ["s", "sk", "mk"] if AKTIVLAR[k][x]]
                    yubor("\n".join(out) if out else "📭 Faol signallar yo'q.")
                elif txt == "📈 Statistika":
                    j = STAT["tp"] + STAT["sl"]
                    yubor(f"📈 Foyda: {STAT['tp']} | Zarar: {STAT['sl']} | Aniqlik: {round(STAT['tp']/j*100,1) if j else 0}%")
                elif txt in ["⚡ 100 Pips", "🔥 200 Pips"]:
                    for k in AKTIVLAR:
                        tekshir(k, "avto")
                    yubor("✅ Bozorlar tekshirildi!")
            if time.time() - last_scan >= 60:
                for k in AKTIVLAR:
                    try:
                        tekshir(k, "avto")
                    except Exception:
                        pass
                last_scan = time.time()
        except Exception as e:
            print(e)
            time.sleep(5)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=loop_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
