import os
import time
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import joblib

import config
from features import generate_features
from screener import create_exchange
from portfolio import load_portfolio, execute_paper_trade
from explain import explain_signal

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="VibeTrade AI - Live Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("VibeTrade AI - Real-Time Paper Trading Dashboard")
st.caption("Micro Capital Algorithmic Trading Bot (Tokocrypto via CCXT)")

# Sidebar Konfigurasi
st.sidebar.header("Pengaturan Bot & Pasar")
symbol = st.sidebar.selectbox("Pilih Pasangan Aset:", ["BTC/IDR", "ETH/IDR", "SOL/IDR", "DOGE/IDR"], index=0)
trade_size = st.sidebar.number_input("Nominal Transaksi (IDR):", value=config.TRADE_SIZE_IDR, step=1000)
auto_refresh = st.sidebar.checkbox("Auto Refresh Data AI (15 Detik)", value=False)

# Fungsi Cache Data OHLCV
def load_ohlcv_data(target_symbol):
    exchange = create_exchange()
    ohlcv = exchange.fetch_ohlcv(target_symbol, timeframe=config.TIMEFRAME, limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# Main Panel Execution
try:
    with st.spinner(f"Menarik data real-time {symbol} dari Tokocrypto..."):
        df_raw = load_ohlcv_data(symbol)
        df_features = generate_features(df_raw)
        
    latest_close = df_features.iloc[-1]['close']
    latest_row = df_features.iloc[[-1]]
    
    # Load Status Portofolio Paper Trading
    port = load_portfolio()
    cash_idr = port["cash_idr"]
    initial_cap = port["initial_capital"]
    
    # Hitung Nilai Aset Kripto & Posisi Terbuka
    crypto_val = 0.0
    open_pos_list = []
    for pos_sym, pos_data in port["positions"].items():
        val = pos_data["qty"] * latest_close if pos_sym == symbol else pos_data["amount_idr"]
        crypto_val += val
        pnl_rp = val - pos_data["amount_idr"]
        pnl_pct = (pnl_rp / pos_data["amount_idr"]) * 100 if pos_data["amount_idr"] > 0 else 0
        open_pos_list.append({
            "Simbol": pos_sym,
            "Harga Masuk": f"Rp {pos_data['entry_price']:,.2f}",
            "Jumlah Koin": f"{pos_data['qty']:.6f}",
            "Modal (IDR)": f"Rp {pos_data['amount_idr']:,.2f}",
            "Nilai Saat Ini": f"Rp {val:,.2f}",
            "PnL (Rp)": f"Rp {pnl_rp:,.2f}",
            "PnL (%)": f"{pnl_pct:+.2f}%",
            "Waktu Masuk": pos_data["entry_time"]
        })
        
    total_portfolio_val = cash_idr + crypto_val
    total_pnl_rp = total_portfolio_val - initial_cap
    total_pnl_pct = (total_pnl_rp / initial_cap) * 100 if initial_cap > 0 else 0
    
    # Section 1: Saldo & Portfolio Status
    st.subheader("Ringkasan Saldo & Portofolio (Paper Trading)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Saldo Kas IDR", f"Rp {cash_idr:,.2f}")
    m2.metric("Nilai Aset Kripto", f"Rp {crypto_val:,.2f}")
    m3.metric("Total Portofolio", f"Rp {total_portfolio_val:,.2f}")
    m4.metric("Total Profit / Loss", f"Rp {total_pnl_rp:,.2f}", f"{total_pnl_pct:+.2f}%")
    
    st.markdown("---")
    
    # Pemuatan Model ML & Prediksi Sinyal
    model = None
    if os.path.exists(config.MODEL_PATH):
        model = joblib.load(config.MODEL_PATH)
        feature_cols = ['RSI_14', 'SMA_20', 'SMA_50', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']
        available_features = [col for col in feature_cols if col in df_features.columns]
        
        prediction = model.predict(latest_row[available_features])[0]
        prob = model.predict_proba(latest_row[available_features])[0]
    else:
        prediction = 0
        prob = [0.5, 0.5]
        st.warning("Model AI belum dilatih. Jalankan `python train.py`!")
        
    # Grid Metrik Sinyal Live
    c1, c2, c3 = st.columns(3)
    c1.metric("Harga Terakhir", f"Rp {latest_close:,.2f}")
    
    if prediction == 1:
        c2.metric("Sinyal AI Terbaru", "BUY (BELI)", delta=f"{prob[1]*100:.1f}% Probabilitas Naik")
    else:
        c2.metric("Sinyal AI Terbaru", "HOLD / SELL", delta=f"-{prob[0]*100:.1f}% Probabilitas Turun", delta_color="inverse")
        
    qty_est = trade_size / latest_close if latest_close > 0 else 0
    c3.metric("Estimasi Posisi Baru", f"Rp {trade_size:,.2f}", f"~{qty_est:.6f} {symbol.split('/')[0]}")
    
    # Tombol Aksi Transaksi Paper Trading Manual
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Simulasikan Transaksi BUY", use_container_width=True):
            success, msg = execute_paper_trade(symbol, "BUY", latest_close, trade_size)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    with btn_col2:
        if st.button("Simulasikan Transaksi SELL (Tutup Posisi)", use_container_width=True):
            success, msg = execute_paper_trade(symbol, "SELL", latest_close, trade_size)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    
    # Tabs Informasi Detail
    tab_chart, tab_explain, tab_pos, tab_hist = st.tabs([
        "Grafik TradingView", 
        "Penjelasan Sinyal AI", 
        "Posisi Terbuka", 
        "Riwayat Transaksi"
    ])
    
    with tab_chart:
        st.subheader(f"Grafik Harga Live TradingView ({symbol})")
        tv_symbol = f"BINANCE:{symbol.replace('/', '')}"
        tradingview_html = f"""
        <div class="tradingview-widget-container" style="height:500px;width:100%">
          <iframe 
            src="https://s.tradingview.com/widgetembed/?symbol={tv_symbol}&interval=15&theme=dark&style=1&timezone=Asia%2FJakarta&symboledit=1&saveimage=1&toolbarbg=F1F3F6" 
            style="width: 100%; height: 500px; border: none; border-radius: 10px;">
          </iframe>
        </div>
        """
        components.html(tradingview_html, height=520)
        
    with tab_explain:
        st.subheader("Analisis Alasan Keputusan Sinyal AI")
        reasons = explain_signal(latest_row, model)
        
        if prediction == 1:
            st.success(f"**ALASAN SINYAL BUY (Probabilitas Naik: {prob[1]*100:.1f}%)**")
        else:
            st.warning(f"**ALASAN SINYAL HOLD / SELL (Probabilitas Turun: {prob[0]*100:.1f}%)**")
            
        for r in reasons:
            st.info(f"• {r}")
            
    with tab_pos:
        st.subheader("Daftar Posisi Terbuka Saat Ini")
        if open_pos_list:
            st.table(pd.DataFrame(open_pos_list))
        else:
            st.info("Belum ada posisi terbuka. Jalankan simulasi BUY di atas untuk membuka posisi.")
            
    with tab_hist:
        st.subheader("Riwayat Transaksi Paper Trading")
        if port["history"]:
            st.table(pd.DataFrame(port["history"]))
        else:
            st.info("Belum ada riwayat transaksi.")

except Exception as e:
    st.error(f"Gagal memuat dashboard: {e}")

if auto_refresh:
    time.sleep(15)
    st.rerun()
