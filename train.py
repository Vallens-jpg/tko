import os
import ccxt
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

import config
from features import generate_features
from screener import get_potential_tokens, create_exchange

def fetch_historical_ohlcv(symbol=config.SYMBOL, timeframe=config.TIMEFRAME, limit=1000):
    print(f"[TRAIN] Mengunduh {limit} candle OHLCV untuk {symbol} ({timeframe})...")
    exchange = create_exchange()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def train_model(use_screener=False):
    # 1. Gunakan screener jika diaktifkan, jika tidak default ke config.SYMBOL (BTC/IDR)
    if use_screener:
        potential_tokens = get_potential_tokens()
        target_symbol = potential_tokens[0] if potential_tokens else config.SYMBOL
    else:
        target_symbol = config.SYMBOL
    
    print(f"[TRAIN] Memulai pelatihan model ML untuk simbol: {target_symbol}")
    
    # 2. Fetch data historis
    df_raw = fetch_historical_ohlcv(symbol=target_symbol, timeframe=config.TIMEFRAME, limit=1000)
    
    # Simpan dataset mentah
    os.makedirs(config.DATA_DIR, exist_ok=True)
    raw_csv_path = os.path.join(config.DATA_DIR, f"{target_symbol.replace('/', '_')}_raw.csv")
    df_raw.to_csv(raw_csv_path, index=False)
    print(f"[TRAIN] Data mentah disimpan di: {raw_csv_path}")
    
    # 3. Generate fitur indikator
    df_features = generate_features(df_raw)
    
    # 4. Buat variabel target (1 jika close berikutnya > close sekarang, 0 jika tidak)
    df_features['target'] = (df_features['close'].shift(-1) > df_features['close']).astype(int)
    
    # Drop baris terakhir karena target shift(-1) akan NaN
    df_features = df_features.dropna().reset_index(drop=True)
    
    feature_cols = ['RSI_14', 'SMA_20', 'SMA_50', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']
    available_features = [col for col in feature_cols if col in df_features.columns]
    
    X = df_features[available_features]
    y = df_features['target']
    
    # 5. Train-test split tanpa shuffle untuk menjaga urutan waktu (time-series)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # 6. Latih Random Forest Classifier
    model = RandomForestClassifier(max_depth=5, n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 7. Evaluasi model
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[TRAIN EVALUATION] Akurasi Model: {acc * 100:.2f}%")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # 8. Simpan model .pkl
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    joblib.dump(model, config.MODEL_PATH)
    print(f"[TRAIN] Model berhasil disimpan di: {config.MODEL_PATH}")

if __name__ == "__main__":
    train_model(use_screener=False)
