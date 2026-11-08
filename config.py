import os
from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Kredensial API Tokocrypto
API_KEY = os.getenv("TOKOCRYPTO_API_KEY", "")
API_SECRET = os.getenv("TOKOCRYPTO_API_SECRET", "")

# Konfigurasi Pasar dan Trading
SYMBOL = "BTC/IDR"
TIMEFRAME = "15m"
TRADE_SIZE_IDR = 21000

# Konfigurasi Pemindaian Koin Potensial (Coin Screener)
MIN_24H_VOLUME_IDR = 500_000_000  # Minimum volume 24j Rp 500 Juta IDR
QUOTE_CURRENCY = "IDR"            # Currency penyaring
TOP_N_POTENTIAL = 3               # Jumlah token teratas

# Konfigurasi Breakout Scanner (breakout_scanner.py)
# Default: Tokocrypto / IDR supaya harga dan ukuran posisi Rp tetap
# cocok dengan portfolio.py dan model yang dilatih di BTC/IDR.
# Untuk memindai Binance / USDT, ubah ke "binance" / "USDT" dan
# BREAKOUT_MIN_VOLUME ke 500_000 (USD) -- tapi ingat, itu mode
# eksperimen: ukuran posisi Rp dan model BTC tidak langsung cocok
# untuk pair USDT, jadi tetap paper trading saja.
BREAKOUT_EXCHANGE = "tokocrypto"
BREAKOUT_QUOTE = "IDR"
BREAKOUT_MIN_VOLUME = 500_000_000  # Rp 500 jt / 24 jam (atau $500 rb kalau USDT)
BREAKOUT_TOP_N = 3
BREAKOUT_MIN_SCORE = 60
BREAKOUT_RESCAN_HOURS = 4  # Scan ulang tiap 4 jam, bukan tiap loop 15 detik
BREAKOUT_ENRICH = False  # True = tambah market cap CoinGecko (lebih lambat)



# Konfigurasi Direktori dan Path File
DATA_DIR = "data"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "rf_model_v1.pkl")
