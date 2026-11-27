import yfinance as yf
from config import SYMBOLS

active_trades = {}

stats = {
    "win": 0,
    "loss": 0,
    "breakeven": 0,
    "total_pips": 0
}

def add_trade(signal_data):
    asset = signal_data["asset"]
    if asset not in active_trades:
        active_trades[asset] = signal_data
        return True
    return False

def get_current_price(asset_name):
    ticker = SYMBOLS.get(asset_name)
    try:
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not df.empty:
            return float(df['Close'].squeeze().iloc[-1])
    except Exception as e:
        print(f"Narx olishda xato ({asset_name}): {e}")
    return None

def check_active_trades():
    alerts = []
    completed_assets = []

    for asset, trade in list(active_trades.items()):
        price = get_current_price(asset)
        if price is None:
            continue

        direction = trade["direction"]
        tp = trade["tp"]
        sl = trade["sl"]
        entry = trade["entry"]
        be_trigger = trade["be_trigger"]
        pips = trade["pips"]
        sl_pips = trade["sl_pips"]

        if direction == "BUY":
            if not trade["be_moved"] and price >= be_trigger:
                trade["sl"] = entry
                trade["be_moved"] = True
                alerts.append(
                    f"🛡 **BREAKEVEN (ZARARSIZ NUQTA)!**\n"
                    f"📌 Aktiv: **{asset}** (BUY)\n"
                    f"📈 Narx `{round(price, 4)}` ga yetdi.\n"
                    f"🔒 Stop Loss kirish narxiga (`{entry}`) ko'chirildi. Endi bu savdo xavfsiz!"
                )

            if price >= tp:
                stats["win"] += 1
                stats["total_pips"] += pips
                alerts.append(format_exit_msg(asset, "FOYDA (TP) ✅", entry, price, f"+{pips} pips"))
                completed_assets.append(asset)

            elif price <= trade["sl"]:
                if trade["be_moved"]:
                    stats["breakeven"] += 1
                    alerts.append(format_exit_msg(asset, "BREAKEVEN YOPILDI 🛡", entry, price, "0 pips (Zararsiz chiqish)"))
                else:
                    stats["loss"] += 1
                    stats["total_pips"] -= sl_pips
                    alerts.append(format_exit_msg(asset, "STOP LOSS (SL) 🛑", entry, price, f"-{sl_pips} pips"))
                completed_assets.append(asset)

        elif direction == "SELL":
            if not trade["be_moved"] and price <= be_trigger:
                trade["sl"] = entry
                trade["be_moved"] = True
                alerts.append(
                    f"🛡 **BREAKEVEN (ZARARSIZ NUQTA)!**\n"
                    f"📌 Aktiv: **{asset}** (SELL)\n"
                    f"📉 Narx `{round(price, 4)}` ga tushdi.\n"
                    f"🔒 Stop Loss kirish narxiga (`{entry}`) ko'chirildi. Endi bu savdo xavfsiz!"
                )

            if price <= tp:
                stats["win"] += 1
                stats["total_pips"] += pips
                alerts.append(format_exit_msg(asset, "FOYDA (TP) ✅", entry, price, f"+{pips} pips"))
                completed_assets.append(asset)

            elif price >= trade["sl"]:
                if trade["be_moved"]:
                    stats["breakeven"] += 1
                    alerts.append(format_exit_msg(asset, "BREAKEVEN YOPILDI 🛡", entry, price, "0 pips (Zararsiz chiqish)"))
                else:
                    stats["loss"] += 1
                    stats["total_pips"] -= sl_pips
                    alerts.append(format_exit_msg(asset, "STOP LOSS (SL) 🛑", entry, price, f"-{sl_pips} pips"))
                completed_assets.append(asset)

    for asset in completed_assets:
        del active_trades[asset]

    return alerts

def format_exit_msg(asset, status, entry, exit_price, result):
    return (
        f"🚨 **SAVDODAN CHIQING! (YOPISH VAQTI)**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 Aktiv: **{asset}**\n"
        f"🏁 Holat: **{status}**\n"
        f"📥 Kirish narxi: `{entry}`\n"
        f"📤 Chiqish narxi: `{round(exit_price, 4)}`\n"
        f"💰 Natija: **{result}**"
    )

def get_active_list():
    if not active_trades:
        return "📭 Hozircha ochiq (faol) signallar yo'q."
    msg = "📊 **HOZIR KUZATILAYOTGAN SIGNALLAR:**\n\n"
    for asset, t in active_trades.items():
        be_status = "🛡 Breakeven yoqilgan" if t["be_moved"] else "⏳ Oddiy SL"
        msg += f"• **{asset}** ({t['direction']}) | Kirish: `{t['entry']}` | TP: `{t['tp']}` | SL: `{t['sl']}` ({be_status})\n"
    return msg

def get_stats_text():
    total = stats["win"] + stats["loss"]
    accuracy = round((stats["win"] / total) * 100, 1) if total > 0 else 0
    return (
        f"📈 **UMUMIY STATISTIKA**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ Foyda (TP): **{stats['win']} ta**\n"
        f"🛡 Zararsiz (Breakeven): **{stats['breakeven']} ta**\n"
        f"🛑 Stop Loss (SL): **{stats['loss']} ta**\n"
        f"🎯 Aniqlik darajasi: **{accuracy}%**\n"
        f"💵 Sof natija: **{stats['total_pips']} pips**"
    )
