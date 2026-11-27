import yfinance as yf
import pandas as pd
from config import SYMBOLS, PIP_MULTIPLIER

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

def get_signal(asset_name):
    ticker = SYMBOLS.get(asset_name)
    if not ticker:
        return None

    try:
        df_15m = yf.download(ticker, period="5d", interval="15m", progress=False)
        df_1h = yf.download(ticker, period="3mo", interval="1h", progress=False)

        if df_15m.empty or df_1h.empty or len(df_15m) < 55 or len(df_1h) < 100:
            return None

        c_15m = df_15m['Close'].squeeze().dropna()
        c_1h = df_1h['Close'].squeeze().dropna()

        c_4h = c_1h.resample('4h').last().dropna()
        c_1d = c_1h.resample('1D').last().dropna()

        price = float(c_15m.iloc[-1])

        ema20_15m = float(c_15m.ewm(span=20).mean().iloc[-1])
        ema50_15m = float(c_15m.ewm(span=50).mean().iloc[-1])
        rsi_15m = float(calculate_rsi(c_15m).iloc[-1])

        ema20_1h = float(c_1h.ewm(span=20).mean().iloc[-1])
        ema50_1h = float(c_1h.ewm(span=50).mean().iloc[-1])

        ema20_4h = float(c_4h.ewm(span=20).mean().iloc[-1])
        ema50_4h = float(c_4h.ewm(span=50).mean().iloc[-1])
        ema20_1d = float(c_1d.ewm(span=20).mean().iloc[-1])

        mult = PIP_MULTIPLIER[ticker]
        step = 1 / mult

        # 1. ULTRA SNAYPER (500 pips)
        if (price > ema20_15m > ema50_15m and
            price > ema20_1h > ema50_1h and
            price > ema20_4h > ema50_4h and
            price > ema20_1d and 50 <= rsi_15m <= 66):
            tp = round(price + (500 * step), 4)
            sl = round(price - (120 * step), 4)
            be = round(price + (120 * step), 4)
            return build_data("💎 ULTRA SNAYPER", asset_name, "BUY", price, tp, sl, be, 500, 120)

        elif (price < ema20_15m < ema50_15m and
              price < ema20_1h < ema50_1h and
              price < ema20_4h < ema50_4h and
              price < ema20_1d and 34 <= rsi_15m <= 50):
            tp = round(price - (500 * step), 4)
            sl = round(price + (120 * step), 4)
            be = round(price - (120 * step), 4)
            return build_data("💎 ULTRA SNAYPER", asset_name, "SELL", price, tp, sl, be, 500, 120)

        # 2. SNAYPER SIGNAL (350 pips)
        elif price > ema20_15m > ema50_15m and price > ema20_1h > ema50_1h and 48 <= rsi_15m <= 68:
            tp = round(price + (350 * step), 4)
            sl = round(price - (100 * step), 4)
            be = round(price + (100 * step), 4)
            return build_data("🎯 SNAYPER SIGNAL", asset_name, "BUY", price, tp, sl, be, 350, 100)

        elif price < ema20_15m < ema50_15m and price < ema20_1h < ema50_1h and 32 <= rsi_15m <= 52:
            tp = round(price - (350 * step), 4)
            sl = round(price + (100 * step), 4)
            be = round(price - (100 * step), 4)
            return build_data("🎯 SNAYPER SIGNAL", asset_name, "SELL", price, tp, sl, be, 350, 100)

        # 3. MAYDA SIGNAL (150 pips)
        elif price > ema20_15m and rsi_15m < 46:
            tp = round(price + (150 * step), 4)
            sl = round(price - (60 * step), 4)
            be = round(price + (50 * step), 4)
            return build_data("⚡️ MAYDA SIGNAL", asset_name, "BUY", price, tp, sl, be, 150, 60)

        elif price < ema20_15m and rsi_15m > 54:
            tp = round(price - (150 * step), 4)
            sl = round(price + (60 * step), 4)
            be = round(price - (50 * step), 4)
            return build_data("⚡️ MAYDA SIGNAL", asset_name, "SELL", price, tp, sl, be, 150, 60)

        return None
    except Exception as e:
        print(f"Tahlil xatosi ({asset_name}): {e}")
        return None

def build_data(sig_type, asset, direction, entry, tp, sl, be_trigger, target_pips, sl_pips):
    dir_icon = "BUY 🟢" if direction == "BUY" else "SELL 🔴"
    text = (
        f"**{sig_type}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 Aktiv: **{asset}**\n"
        f"📊 Yo'nalish: **{dir_icon}**\n"
        f"🎯 Kirish (Entry): `{round(entry, 4)}`\n"
        f"✅ Foyda (TP): `{tp}` (+{target_pips} pips)\n"
        f"🛑 Stop Loss (SL): `{sl}` (-{sl_pips} pips)\n"
        f"🛡 Breakeven nuqtasi: `{be_trigger}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📡 *Bot narxni kuzatmoqda. Breakeven, TP yoki SL urilganda darhol xabar beraman!*"
    )
    return {
        "asset": asset,
        "type": sig_type,
        "direction": direction,
        "entry": round(entry, 4),
        "tp": tp,
        "sl": sl,
        "be_trigger": be_trigger,
        "be_moved": False,
        "pips": target_pips,
        "sl_pips": sl_pips,
        "text": text
    }
