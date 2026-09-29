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



# Konfigurasi Direktori dan Path File
DATA_DIR = "data"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "rf_model_v1.pkl")
