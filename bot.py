import time
import os
import ccxt
import pandas as pd
import joblib

import config
from features import generate_features
from screener import get_potential_tokens, create_exchange
from portfolio import load_portfolio, execute_paper_trade

# Breakout scanner: pengganti screener lama kalau use_breakout=True.
# Import-nya dibuat opsional supaya bot lama tetap jalan walau file
# breakout_scanner.py belum ada di folder yang sama.
try:
    from breakout_scanner import scan_explosive, enrich_with_coingecko
    _BREAKOUT_AVAILABLE = True
except Exception:
    scan_explosive = None
    enrich_with_coingecko = None
    _BREAKOUT_AVAILABLE = False


def pick_breakout_target():
    """Scan breakout sekali, kembalikan (symbol, info_dict).

    Kalau scan gagal atau tidak ada kandidat, fallback ke config.SYMBOL
    (BTC/IDR) supaya bot tidak berhenti. Fungsi ini sengaja dipanggil
    sekali di awal dan tiap BREAKOUT_RESCAN_HOURS, BUKAN tiap loop,
    karena satu scan butuh puluhan request OHLCV + CoinGecko.
    """
    if not _BREAKOUT_AVAILABLE:
        print("[BREAKOUT] breakout_scanner.py tidak ditemukan, fallback ke BTC/IDR.")
        return config.SYMBOL, None
    try:
        results = scan_explosive(
            exchange_name=getattr(config, "BREAKOUT_EXCHANGE", "tokocrypto"),
            quote=getattr(config, "BREAKOUT_QUOTE", "IDR"),
            min_volume=getattr(config, "BREAKOUT_MIN_VOLUME", 500_000_000),
            top_n=getattr(config, "BREAKOUT_TOP_N", 3),
            min_score=getattr(config, "BREAKOUT_MIN_SCORE", 60),
        )
        if getattr(config, "BREAKOUT_ENRICH", False) and results:
            try:
                results = enrich_with_coingecko(results)
            except Exception as e:
                print(f"[BREAKOUT] CoinGecko gagal, lanjut tanpa enrichment: {e}")
        if not results:
            print("[BREAKOUT] Tidak ada kandidat breakout, fallback ke BTC/IDR.")
            return config.SYMBOL, None
        top = results[0]
        print(f"[BREAKOUT] Kandidat teratas: {top['symbol']} skor {top['score']}/100 "
              f"(volume {top['volume_ratio']}x, breakout {top['breakout_pct']:+.1f}%)")
        if top.get("reasons"):
            print(f"[BREAKOUT] Alasan: {'; '.join(top['reasons'])}")
        if top.get("market_cap_usd"):
            print(f"[BREAKOUT] Market cap: ${top['market_cap_usd']:,.0f} "
                  f"(#{top.get('market_cap_rank')})")
        return top["symbol"], top
    except Exception as e:
        print(f"[BREAKOUT WARNING] Scan gagal ({e}), fallback ke BTC/IDR.")
        return config.SYMBOL, None

def fetch_latest_ohlcv(symbol, timeframe=config.TIMEFRAME, limit=100):
    exchange = create_exchange()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def run_bot(single_run=False, use_screener=False, use_breakout=False, interval_seconds=15):
    print("=" * 65)
    print(" VibeTrade AI - Automated Real-Time Paper Trading Bot")
    print("=" * 65)

    breakout_info = None
    last_scan_time = 0
    if use_breakout:
        # Mode breakout menggantikan screener lama. Scan sekali di awal,
        # lalu scan ulang tiap BREAKOUT_RESCAN_HOURS di dalam loop.
        # Peringatan: model dilatih di BTC/IDR, jadi prediksi ML untuk
        # koin lain bersifat eksperimen. Tetap paper trading saja.
        print("[BREAKOUT] Mode breakout aktif. Model dilatih di BTC/IDR, jadi")
        print("[BREAKOUT] prediksi ML untuk koin lain bersifat eksperimen, paper trading saja.")
        target_symbol, breakout_info = pick_breakout_target()
        last_scan_time = time.time()
    elif use_screener:
        potential_tokens = get_potential_tokens()
        target_symbol = potential_tokens[0] if potential_tokens else config.SYMBOL
    else:
        target_symbol = config.SYMBOL
        
    print(f"[AUTOPILOT BOT] Simbol Target Trading: {target_symbol}")
    
    if not os.path.exists(config.MODEL_PATH):
        print(f"[BOT ERROR] File model tidak ditemukan di {config.MODEL_PATH}.")
        print("Silakan jalankan `python train.py` terlebih dahulu!")
        return

    print(f"[BOT] Memuat model AI dari {config.MODEL_PATH}...")
    model = joblib.load(config.MODEL_PATH)
    
    feature_cols = ['RSI_14', 'SMA_20', 'SMA_50', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']
    
    iteration = 0
    while True:
        iteration += 1
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n--- [AUTOPILOT ITERASI {iteration}] {current_time} ---")
        try:
            # Scan ulang breakout kalau sudah waktunya (default 4 jam).
            if use_breakout and time.time() - last_scan_time >= getattr(config, "BREAKOUT_RESCAN_HOURS", 4) * 3600:
                new_symbol, breakout_info = pick_breakout_target()
                if new_symbol != target_symbol:
                    print(f"[BREAKOUT] Target berubah: {target_symbol} -> {new_symbol}")
                    target_symbol = new_symbol
                last_scan_time = time.time()

            # 1. Fetch 100 candle real-time terbaru
            df_raw = fetch_latest_ohlcv(symbol=target_symbol)
            df_features = generate_features(df_raw)
            
            if df_features.empty:
                print("[BOT WARNING] Data fitur kosong.")
                if single_run: break
                time.sleep(interval_seconds)
                continue
                
            available_features = [col for col in feature_cols if col in df_features.columns]
            latest_row = df_features.iloc[[-1]][available_features]
            latest_close = df_features.iloc[-1]['close']
            
            # 2. Prediksi ML
            prediction = model.predict(latest_row)[0]
            prob = model.predict_proba(latest_row)[0]
            
            # 3. Load Portofolio saat ini
            port = load_portfolio()
            has_position = target_symbol in port["positions"]
            
            print(f"[MARKET LIVE] {target_symbol} Price: Rp {latest_close:,.2f}")
            print(f"[AI PREDICTION] Sinyal: {'BUY (1)' if prediction == 1 else 'HOLD/SELL (0)'} | Prob: Naik={prob[1]*100:.1f}%, Turun={prob[0]*100:.1f}%")
            
            # 4. Eksekusi Otomatis Paper Trading
            if prediction == 1 and not has_position:
                print(f"[AUTOPILOT EXECUTION] >> Memicu Otomatis BUY Rp {config.TRADE_SIZE_IDR:,.2f} <<")
                success, msg = execute_paper_trade(target_symbol, "BUY", latest_close, config.TRADE_SIZE_IDR)
                print(f"[PORTFOLIO LOG] {msg}")
            elif prediction == 0 and has_position:
                print(f"[AUTOPILOT EXECUTION] >> Memicu Otomatis SELL (Tutup Posisi) <<")
                success, msg = execute_paper_trade(target_symbol, "SELL", latest_close, config.TRADE_SIZE_IDR)
                print(f"[PORTFOLIO LOG] {msg}")
            else:
                if has_position:
                    pos = port["positions"][target_symbol]
                    unrealized_pnl = (latest_close * pos["qty"]) - pos["amount_idr"]
                    print(f"[AUTOPILOT STATUS] Posisi Terbuka Dipertahankan. Floating PnL: Rp {unrealized_pnl:,.2f}")
                else:
                    print(f"[AUTOPILOT STATUS] Tidak ada posisi. Menunggu sinyal BUY dari AI...")
                
        except Exception as e:
            print(f"[BOT ERROR] Terjadi kesalahan dalam perulangan bot: {e}")
            
        if single_run:
            print("[BOT] Single run selesai.")
            break
            
        print(f"[BOT] Menunggu {interval_seconds} detik sebelum pemindaian berikutnya...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Default tetap seperti dulu (BTC/IDR, tanpa screener).
    # Untuk memakai breakout scanner: run_bot(use_breakout=True)
    run_bot(single_run=False, use_screener=False, use_breakout=False, interval_seconds=15)
