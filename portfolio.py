import os
import json
import time
import config

PORTFOLIO_FILE = os.path.join(config.DATA_DIR, "portfolio.json")

def load_portfolio():
    """
    Memuat status portofolio paper trading dari file JSON.
    Jika file belum ada, diinisialisasi dengan modal awal Rp 100.000.
    """
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    default_portfolio = {
        "cash_idr": 100000.0,
        "initial_capital": 100000.0,
        "positions": {},
        "history": []
    }
    save_portfolio(default_portfolio)
    return default_portfolio

def save_portfolio(data):
    """Menyimpan status portofolio ke file JSON."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=4)

def execute_paper_trade(symbol, action, price, amount_idr):
    """
    Menyimulasikan eksekusi transaksi BUY atau SELL pada portofolio paper trading.
    """
    p = load_portfolio()
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    
    if action == "BUY":
        if p["cash_idr"] < amount_idr:
            return False, "Saldo kas IDR tidak mencukupi untuk melakukan BUY."
            
        qty = amount_idr / price if price > 0 else 0
        p["cash_idr"] -= amount_idr
        
        # Tambah atau gabung posisi
        if symbol in p["positions"]:
            pos = p["positions"][symbol]
            new_qty = pos["qty"] + qty
            new_amount = pos["amount_idr"] + amount_idr
            avg_price = new_amount / new_qty
            p["positions"][symbol] = {
                "entry_price": avg_price,
                "qty": new_qty,
                "amount_idr": new_amount,
                "entry_time": timestamp_str
            }
        else:
            p["positions"][symbol] = {
                "entry_price": price,
                "qty": qty,
                "amount_idr": amount_idr,
                "entry_time": timestamp_str
            }
            
        p["history"].insert(0, {
            "timestamp": timestamp_str,
            "symbol": symbol,
            "action": "BUY",
            "price": price,
            "qty": qty,
            "amount_idr": amount_idr,
            "pnl_idr": 0.0
        })
        save_portfolio(p)
        return True, f"Sukses BUY {qty:.6f} {symbol.split('/')[0]} pada harga Rp {price:,.2f}"

    elif action == "SELL":
        if symbol not in p["positions"]:
            return False, f"Tidak ada posisi terbuka untuk {symbol}."
            
        pos = p["positions"][symbol]
        qty = pos["qty"]
        sell_value = qty * price
        pnl_idr = sell_value - pos["amount_idr"]
        
        p["cash_idr"] += sell_value
        del p["positions"][symbol]
        
        p["history"].insert(0, {
            "timestamp": timestamp_str,
            "symbol": symbol,
            "action": "SELL",
            "price": price,
            "qty": qty,
            "amount_idr": sell_value,
            "pnl_idr": pnl_idr
        })
        save_portfolio(p)
        return True, f"Sukses SELL {qty:.6f} {symbol.split('/')[0]} (PnL: Rp {pnl_idr:,.2f})"

    return False, "Aksi tidak dikenali."
