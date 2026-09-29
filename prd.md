# Product Requirements Document (PRD): VibeTrade AI

**Nama Proyek:** VibeTrade AI - Micro Capital Bot
**Status:** MVP (Minimum Viable Product) - Phase 1 (Local Building & Paper Trading)
**Platform Exchange:** Tokocrypto (via CCXT)
**Modal Awal:** Rp 100.000 (BIDR)
**Ukuran Transaksi (Trade Size):** ~Rp 21.000 (BIDR) per posisi

## 1. Latar Belakang & Tujuan
Membangun *Proof of Concept* (PoC) sistem *algorithmic trading* berbasis *Machine Learning*. Sistem ini dirancang spesifik untuk beroperasi di ruang lingkup modal mikro (Rp 100.000) di *exchange* Tokocrypto, yang memungkinkan pemecahan transaksi dengan minimum order ~Rp 20.000. 

Fokus saat ini adalah **Fase 1 (Local Development & Paper Trading)**: Membangun sistem di komputer lokal dan menguji ketajaman prediksi AI tanpa menggunakan uang sungguhan, sebelum nantinya di-*deploy* ke cloud (GCP) untuk *live trading* 24/7.

## 2. Fitur Utama (Core Features)
1. **Historical Data Ingestion:** Menarik data OHLCV (Open, High, Low, Close, Volume) masa lalu secara stabil menggunakan API Tokocrypto tanpa terkena *rate limit*.
2. **Offline Model Training:** Memiliki *pipeline* khusus untuk melatih algoritma *Random Forest Classifier* menggunakan indikator teknikal (RSI, MACD, SMA) dan menyimpannya sebagai file `.pkl`.
3. **Live Inference Engine:** Membaca kondisi pasar *live* berdasarkan *timeframe* (misal: 15 menit), meracik fitur secara *real-time*, dan meminta prediksi probabilitas (BUY/SELL/HOLD) dari model `.pkl`.
4. **Paper Trading Mode:** Menyimulasikan eksekusi transaksi di terminal (mencetak log BUY/SELL hipotetis) untuk mengevaluasi performa AI tanpa memanggil API *create_order* yang sebenarnya.
5. **Micro-Risk Management (Persiapan Live):** 
   * Pembatasan transaksi maksimal ~Rp 21.000 per sinyal.
   * Pengecekan saldo minimum sebelum melakukan simulasi/eksekusi BUY.

## 3. Arsitektur Sistem & Tech Stack
Sistem menggunakan arsitektur *Modular Monolith*, memisahkan antara *Data Science Pipeline* (pelatihan AI) dan *Execution Engine* (bot trading).

**Tech Stack:**
*   **Bahasa:** Python 3.10+
*   **Koneksi Market:** `ccxt` (modul `tokocrypto`)
*   **Data Processing:** `pandas`, `pandas-ta`
*   **Machine Learning:** `scikit-learn` (RandomForest), `joblib`
*   **Environment Setup:** `python-dotenv`

## 4. Struktur Folder (Untuk AI Context IDE)
Struktur ini wajib dipatuhi agar modul terisolasi dengan baik:

vibetrade-ai/
├── data/                   # Menyimpan dataset mentah (.csv) hasil unduhan
├── models/                 # Menyimpan file .pkl (contoh: rf_model_v1.pkl)
├── docs/                   
│   └── DESIGN.md           # File PRD ini
├── config.py               # Mengelola kredensial API dan parameter global
├── features.py             # Logic pandas-ta untuk indikator teknikal
├── train.py                # Pipeline untuk download data & melatih model AI
├── bot.py                  # Skrip utama live inference & paper trading
├── requirements.txt        # ccxt, pandas, pandas-ta, scikit-learn, python-dotenv
├── .env                    # (IGNORE GIT) API_KEY & API_SECRET Tokocrypto
└── .gitignore              # Mengabaikan .env, /data, /models, dan __pycache__

## 5. Penjelasan Modul Inti

*   **`config.py`**: Memuat `.env`. Mendefinisikan konstanta global: `SYMBOL = 'BTC/BIDR'`, `TIMEFRAME = '15m'`, `TRADE_SIZE_IDR = 21000`.
*   **`features.py`**: Memiliki fungsi `generate_features(df)` yang menerima Pandas DataFrame OHLCV. Menggunakan `pandas-ta` untuk memproduksi kolom tambahan: `RSI_14`, `SMA_20`, `SMA_50`, `MACD_12_26_9`. Membersihkan nilai `NaN` (drop).
*   **`train.py`**: Skrip *offline*. Mengambil 1000-2000 *candle* dari CCXT. Memanggil `generate_features()`. Membuat kolom `target` (Label 1 jika close selanjutnya naik, Label 0 jika turun). Membagi data (`train_test_split` dengan `shuffle=False`), melatih `RandomForestClassifier(max_depth=5)`, mengevaluasi akurasi, dan mengekspor model via `joblib`.
*   **`bot.py`**: Skrip operasional dengan *infinite loop*. Siklus:
    1. Fetch 100 candle terbaru.
    2. Jalankan `generate_features()`.
    3. Load model menggunakan `joblib`.
    4. Ambil prediksi untuk baris data paling akhir.
    5. Jika BUY/SELL, cetak ke console (Paper Trading).
    6. `time.sleep()` sesuai durasi *timeframe* sebelum mengulang loop.