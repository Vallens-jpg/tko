def explain_signal(latest_row, model=None):
    """
    Menganalisis alasan teknikal kenapa model AI mengeluarkan sinyal BUY atau HOLD/SELL.
    Mengembalikan daftar poin penjelasan kuantitatif.
    """
    rsi = latest_row['RSI_14'].values[0]
    sma20 = latest_row['SMA_20'].values[0]
    sma50 = latest_row['SMA_50'].values[0]
    macd = latest_row['MACD_12_26_9'].values[0]
    macdh = latest_row['MACDh_12_26_9'].values[0] if 'MACDh_12_26_9' in latest_row.columns else 0
    
    reasons = []
    
    # 1. Analisis RSI
    if rsi < 30:
        reasons.append(f"RSI (14) bernilai {rsi:.2f} (Oversold < 30): Pasar jenuh jual, berpotensi terjadi pembalikan arah naik (bullish reversal).")
    elif rsi > 70:
        reasons.append(f"RSI (14) bernilai {rsi:.2f} (Overbought > 70): Pasar jenuh beli, berisiko mengalami koreksi penurunan harga.")
    else:
        reasons.append(f"RSI (14) bernilai {rsi:.2f} (Netral 30-70): Momentum harga berada di area konsolidasi normal.")
        
    # 2. Analisis Moving Average Crossover
    if sma20 > sma50:
        reasons.append(f"SMA 20 (Rp {sma20:,.2f}) berada di atas SMA 50 (Rp {sma50:,.2f}): Tren jangka pendek berada dalam fase naik (Uptrend / Golden Cross).")
    else:
        reasons.append(f"SMA 20 (Rp {sma20:,.2f}) berada di bawah SMA 50 (Rp {sma50:,.2f}): Tren jangka pendek berada dalam fase turun (Downtrend / Death Cross).")
        
    # 3. Analisis MACD
    if macdh > 0:
        reasons.append(f"Histogram MACD bernilai positif ({macdh:.4f}): Terjadi peningkatan dorongan pembeli (bullish momentum).")
    else:
        reasons.append(f"Histogram MACD bernilai negatif ({macdh:.4f}): Terjadi peningkatan tekanan penjual (bearish momentum).")
        
    # 4. Feature Importance Random Forest
    if model is not None and hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        feature_names = ['RSI_14', 'SMA_20', 'SMA_50', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']
        available_pairs = []
        for name, imp in zip(feature_names, importances):
            available_pairs.append((name, imp))
        if available_pairs:
            top_feat = sorted(available_pairs, key=lambda x: x[1], reverse=True)[0]
            reasons.append(f"Bobot Utama Random Forest: Indikator {top_feat[0]} menjadi faktor paling berpengaruh ({top_feat[1]*100:.1f}%) dalam prediksi AI saat ini.")
            
    return reasons
