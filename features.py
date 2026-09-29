import pandas as pd
import pandas_ta as ta

def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menerima DataFrame OHLCV (kolom: timestamp, open, high, low, close, volume).
    Menghasilkan indikator teknikal: RSI_14, SMA_20, SMA_50, MACD_12_26_9.
    Membersihkan baris NaN.
    """
    df = df.copy()
    
    # Menghitung RSI
    df['RSI_14'] = ta.rsi(df['close'], length=14)
    
    # Menghitung Simple Moving Average (SMA)
    df['SMA_20'] = ta.sma(df['close'], length=20)
    df['SMA_50'] = ta.sma(df['close'], length=50)
    
    # Menghitung MACD
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        df['MACD_12_26_9'] = macd.iloc[:, 0]
        df['MACDh_12_26_9'] = macd.iloc[:, 1]
        df['MACDs_12_26_9'] = macd.iloc[:, 2]
        
    # Menghapus baris NaN hasil kalkulasi window indikator
    df_clean = df.dropna().reset_index(drop=True)
    return df_clean

if __name__ == "__main__":
    # Dummy test
    dummy_data = {
        'timestamp': range(100),
        'open': [100 + i for i in range(100)],
        'high': [105 + i for i in range(100)],
        'low': [95 + i for i in range(100)],
        'close': [102 + i for i in range(100)],
        'volume': [1000 for _ in range(100)]
    }
    df_dummy = pd.DataFrame(dummy_data)
    df_featured = generate_features(df_dummy)
    print("Jumlah baris setelah indikator:", len(df_featured))
    print(df_featured.tail())
