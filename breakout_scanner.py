"""
Breakout Scanner untuk VibeTrade AI.
Mencari koin yang "sideways dulu, lalu berpotensi meledak".

Beda dengan screener lama (screener.py):
- Screener lama: ambil koin dengan volume 24 jam terbesar -> jatuhnya
  hampir selalu ke BTC / ETH / SOL, koin besar yang jarang naik 2x.
- Scanner ini: cari koin yang harganya lama mendatar (range sempit),
  lalu volume tiba-tiba melonjak dan harga menembus resistance.

Cara kerja, 2 tahap supaya tidak boros request ke exchange:
  Tahap 1 (ticker, 1 request): saring semua pair USDT dari volume
  dan perubahan harga 24 jam.
  Tahap 2 (OHLCV harian, maks. 60 koin): hitung 4 sinyal untuk
  koin yang lolos tahap 1, lalu beri skor 0-100.

4 sinyal (total 100 poin):
  1. Lonjakan volume (30 poin): volume hari ini / rata-rata volume
     14 hari terakhir. >= 2x dapat poin penuh.
  2. Breakout (30 poin): harga penutupan hari ini menembus harga
     tertinggi 14 hari sebelumnya.
  3. Sideways / kompresi (20 poin): range harga 14 hari terakhir
     sempit, misal (tertinggi - terendah) / terendah < 25%.
     Makin sempit, makin besar poinnya.
  4. Momentum (20 poin): harga di atas rata-rata 20 hari (SMA20)
     dan SMA20 di atas SMA50.

Koin yang sudah naik terlalu jauh hari ini (> 30%) sengaja dibuang:
itu biasanya sudah di puncak, bukan awal ledakan.

PAPER ONLY: file ini hanya memindai dan mencetak kandidat.
Tidak ada order, tidak ada create_order, tidak memakai API key.
Enrichment CoinGecko opsional dan gratis (tanpa API key): setelah
scan, market cap / rank / perubahan 7 hari / jarak dari ATH diambil
untuk top 5 saja, lalu skor disesuaikan +10/-10. Kalau CoinGecko
gagal atau rate limit, scanner tetap jalan tanpa data itu.
Jalankan:  python breakout_scanner.py
           python breakout_scanner.py --no-enrich
           python breakout_scanner.py --exchange tokocrypto --quote IDR
           python breakout_scanner.py --top 10 --max-check 60
"""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import ccxt
import pandas as pd

# ---- Pengaturan, boleh diubah Len ----
QUOTE = "USDT"                 # pair yang dipindai, misal USDT di Binance
EXCHANGE_NAME = "binance"      # "binance" untuk pilihan terbanyak, "tokocrypto" untuk IDR
MIN_VOLUME_24H_USD = 500_000   # volume 24 jam minimal, supaya likuid dan tidak susah jual
MAX_CHECK = 40                 # maks. koin yang dicek OHLCV-nya per scan (hemat request)
TOP_N = 5                      # jumlah kandidat yang ditampilkan
MIN_SCORE = 60                 # skor minimal supaya masuk daftar kandidat

# Batas perubahan harga 24 jam di tahap 1.
# Di bawah 2%: belum ada tanda-tanda bergerak.
# Di atas 30%: kemungkinan sudah meledak duluan, jangan kejar.
CHANGE_MIN_PCT = 2.0
CHANGE_MAX_PCT = 30.0

LOOKBACK_DAYS = 14             # berapa hari ke belakang untuk range dan volume rata-rata
VOLUME_SPIKE = 2.0             # volume hari ini >= 2x rata-rata = lonjakan
MAX_RANGE_PCT = 25.0           # range 14 hari di bawah 25% = sideways / terkompresi

# Token yang dibuang: stablecoin dan token leverage (naik-turun 3x).
SKIP_BASES = {"USDT", "USDC", "FDUSD", "TUSD", "DAI", "USDP", "BUSD"}
SKIP_SUFFIXES = ("UP", "DOWN", "BULL", "BEAR", "3L", "3S", "5L", "5S")


def create_exchange(name):
    """Buat exchange CCXT publik, tanpa API key."""
    cls = getattr(ccxt, name)
    if name == "binance":
        # data-api.binance.vision adalah endpoint data publik Binance,
        # dipakai juga oleh screener lama di repo (lewat Tokocrypto).
        # Berguna kalau api.binance.com diblokir dari lokasi VM.
        return cls({
            "enableRateLimit": True,
            "urls": {"api": {
                "public": "https://data-api.binance.vision/api/v3",
                "private": "https://data-api.binance.vision/api/v3",
            }},
        })
    return cls({"enableRateLimit": True})


def _is_skippable(symbol):
    base = symbol.split("/")[0]
    if not base.isalnum():
        return True
    if base in SKIP_BASES:
        return True
    return any(base.endswith(suffix) for suffix in SKIP_SUFFIXES)


def stage1_tickers(exchange, quote, min_volume):
    """Tahap 1: saring dari ticker saja. Kembalikan list dict kandidat awal."""
    tickers = exchange.fetch_tickers()
    # Filter status: hanya pair yang aktif diperdagangkan.
    # Contoh nyata 8 Nov 2026: BNX/USDT statusnya BREAK, harganya beku
    # dan bid/ask 0, tapi ticker/24hr tetap mencantumkannya, jadi tanpa
    # filter ini scanner bisa membelinya. Kalau market list tidak bisa
    # dibaca (misalnya CCXT gagal di VM ini), scan lanjut tanpa filter
    # dan log peringatan, supaya tidak mati total karena satu cek.
    active = None
    try:
        markets = exchange.fetch_markets()
        active = {m["symbol"] for m in markets if m.get("active")}
    except Exception as e:
        print(f"[SCAN] Peringatan: tidak bisa cek status pair ({e}), lanjut tanpa filter status.")
    out = []
    for symbol, t in tickers.items():
        if not symbol.endswith("/" + quote):
            continue
        if active is not None and symbol not in active:
            continue
        if _is_skippable(symbol):
            continue
        volume = t.get("quoteVolume") or 0
        change = t.get("percentage") or 0
        price = t.get("last") or 0
        if price <= 0 or volume < min_volume:
            continue
        if not (CHANGE_MIN_PCT <= change <= CHANGE_MAX_PCT):
            continue
        out.append({
            "symbol": symbol,
            "price": price,
            "change_24h_pct": round(change, 2),
            "volume_24h": round(volume, 2),
        })
    # Cek yang volumenya paling besar dulu, supaya scan selesai lebih cepat.
    out.sort(key=lambda x: x["volume_24h"], reverse=True)
    return out


def _sma(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def score_coin(exchange, symbol, live_price=None):
    """Tahap 2: hitung 4 sinyal dari candle harian. Kembalikan dict + skor, atau None.

    PERBAIKAN BUG TENGAH MALAM (2026-11-08):
    Candle harian terakhir SELALU belum selesai. Jam 00:00-01:00 UTC
    volumenya hampir nol, jadi rasio volume jatuh ke 0,1x dan scan
    menghasilkan 0 kandidat padahal koinnya sedang bergerak.
    Karena itu semua perhitungan di sini memakai candle yang SUDAH
    TUTUP saja (candle terakhir dibuang). Breakout memakai harga
    live dari ticker (live_price), bukan close candle yang belum
    selesai. Dengan begitu hasil scan tidak tergantung jam berapa
    scanner dijalankan.
    """
    try:
        # Ambil 61 candle: 60 untuk SMA50 + 1 candle hari ini yang akan dibuang.
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1d", limit=61)
    except Exception as e:
        print(f"[SCAN] {symbol}: gagal ambil candle ({e})")
        return None
    if len(ohlcv) < LOOKBACK_DAYS + 3:
        return None

    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    # Buang candle hari ini yang belum selesai. Sisanya adalah candle tutup.
    closed = df.iloc[:-1]
    closes = closed["close"].tolist()
    volumes = closed["volume"].tolist()
    highs = closed["high"].tolist()
    lows = closed["low"].tolist()

    last_close = closes[-1]  # close hari terakhir yang sudah tutup
    # Tertinggi 14 hari SEBELUM hari terakhir yang sudah tutup.
    prev_high = max(highs[-(LOOKBACK_DAYS + 1):-1])
    low_14 = min(lows[-LOOKBACK_DAYS:])
    high_14 = max(highs[-LOOKBACK_DAYS:])
    range_pct = (high_14 - low_14) / low_14 * 100 if low_14 > 0 else 999
    # Volume hari terakhir yang sudah tutup vs rata-rata 14 hari sebelumnya.
    avg_volume = sum(volumes[-(LOOKBACK_DAYS + 1):-1]) / LOOKBACK_DAYS
    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 0
    sma20 = _sma(closes, 20)
    sma50 = _sma(closes, 50)

    # Harga untuk breakout: harga live kalau ada, kalau tidak pakai close terakhir.
    breakout_price = live_price if live_price else last_close

    score = 0
    reasons = []

    # 1. Lonjakan volume, maks 30 poin.
    vol_points = min(30, int(30 * volume_ratio / VOLUME_SPIKE)) if volume_ratio > 0 else 0
    if volume_ratio >= VOLUME_SPIKE:
        vol_points = 30
    score += vol_points
    if vol_points >= 20:
        reasons.append(f"volume {volume_ratio:.1f}x rata-rata")

    # 2. Breakout, maks 30 poin. Pakai harga live, bukan close candle
    # yang belum selesai.
    breakout_pct = (breakout_price - prev_high) / prev_high * 100 if prev_high > 0 else 0
    if breakout_price >= prev_high:
        score += 30
        reasons.append(f"tembus resistance {prev_high:,.4g} (+{breakout_pct:.1f}%)")
    elif breakout_price >= prev_high * 0.98:
        score += 15
        reasons.append("mendekati resistance 14 hari")

    # 3. Sideways / kompresi, maks 20 poin. Makin sempit makin bagus.
    if range_pct <= MAX_RANGE_PCT:
        comp_points = int(20 * (1 - range_pct / MAX_RANGE_PCT)) + 5
        score += min(20, comp_points)
        reasons.append(f"sideways 14 hari, range {range_pct:.1f}%")
    # Kalau range lebar, tidak ada poin kompresi: koin itu sudah liar duluan.

    # 4. Momentum, maks 20 poin. Pakai harga live juga.
    if sma20 and breakout_price > sma20:
        score += 10
        reasons.append("harga di atas SMA20")
    if sma20 and sma50 and sma20 > sma50:
        score += 10
        reasons.append("SMA20 di atas SMA50")

    return {
        "symbol": symbol,
        "price": breakout_price,
        "volume_ratio": round(volume_ratio, 2),
        "range_14d_pct": round(range_pct, 1),
        "breakout_pct": round(breakout_pct, 2),
        "score": int(score),
        "reasons": reasons,
    }


def scan_explosive(exchange_name=EXCHANGE_NAME, quote=QUOTE,
                   min_volume=MIN_VOLUME_24H_USD, max_check=MAX_CHECK,
                   top_n=TOP_N, min_score=MIN_SCORE):
    """Jalankan scan lengkap. Kembalikan list kandidat terurut berdasarkan skor."""
    exchange = create_exchange(exchange_name)
    print(f"[SCAN] Exchange: {exchange_name}, pair: */{quote}, "
          f"volume minimal 24 jam: {min_volume:,.0f}")
    stage1 = stage1_tickers(exchange, quote, min_volume)
    print(f"[SCAN] Tahap 1 lolos: {len(stage1)} koin "
          f"(naik {CHANGE_MIN_PCT}-{CHANGE_MAX_PCT}% dalam 24 jam)")
    if not stage1:
        print("[SCAN] Tidak ada koin yang lolos tahap 1. Coba longgarkan batas change/volume.")
        return []

    results = []
    for cand in stage1[:max_check]:
        scored = score_coin(exchange, cand["symbol"], live_price=cand["price"])
        if scored is None:
            continue
        scored["change_24h_pct"] = cand["change_24h_pct"]
        scored["volume_24h"] = cand["volume_24h"]
        if scored["score"] >= min_score:
            results.append(scored)
        # Jeda kecil supaya tidak kena rate limit.
        time.sleep(0.1)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


# ---- Enrichment CoinGecko (opsional, tanpa API key) ----
# Dipanggil SETELAH scan, hanya untuk top 5, supaya hemat request.
# CoinGecko gratis dibatasi kira-kira 5-15 request/menit, jadi kita
# cuma pakai 1-2 request per scan, dengan jeda 1,2 detik.
#
# PERINGATAN PENTING: satu simbol bisa dipakai banyak koin.
# Contoh nyata saat diuji: "ONE" di CoinGecko bisa berarti ONEchain
# (market cap $56 jt) atau Harmony (market cap $31 jt, ini yang
# ada di Binance). Kalau salah pilih, market cap-nya salah total.
# Karena itu ada peta override di bawah. Kalau scanner menemukan
# koin baru yang simbolnya ambigu, tambahkan id CoinGecko-nya di sini.
# Cari id-nya di coingecko.com, contoh: harmony, act-i-the-ai-prophecy.
COINGECKO_ID_OVERRIDES = {
    "ONE": "harmony",              # Binance ONE = Harmony, bukan ONEchain
    "ACT": "act-i-the-ai-prophecy",
    "MET": "meteora",
}
COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def _coingecko_get(path, params):
    url = COINGECKO_BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def enrich_with_coingecko(results):
    """Tambahkan market cap, rank, perubahan 7 hari, dan jarak dari ATH.

    Mengubah skor: market cap $10-500 jt dapat +10 (masih ada ruang
    naik 2x tapi cukup likuid), $500 jt-2 M dapat +5, di atas $5 M
    dapat -10 (susah naik 2x cepat), di bawah $5 jt dapat -10
    (terlalu kecil / berisiko). FDV lebih dari 3x market cap diberi
    peringatan dilusi. Skor akhir dibatasi 0-100.
    Kalau CoinGecko gagal / rate limit, kembalikan hasil apa adanya
    dan jangan matikan scanner.
    """
    if not results:
        return results
    try:
        ids, symbols = [], []
        for r in results:
            base = r["symbol"].split("/")[0].upper()
            if base in COINGECKO_ID_OVERRIDES:
                ids.append(COINGECKO_ID_OVERRIDES[base])
            else:
                symbols.append(base.lower())
        rows = []
        if ids:
            rows += _coingecko_get("/coins/markets", {
                "vs_currency": "usd", "ids": ",".join(ids),
                "price_change_percentage": "7d",
            })
            time.sleep(1.2)
        if symbols:
            rows += _coingecko_get("/coins/markets", {
                "vs_currency": "usd", "symbols": ",".join(symbols),
                "price_change_percentage": "7d",
            })
    except urllib.error.HTTPError as e:
        print(f"[COINGECKO] Gagal (HTTP {e.code}, kemungkinan rate limit). "
              "Lanjut tanpa data market cap.")
        return results
    except Exception as e:
        print(f"[COINGECKO] Gagal ({e}). Lanjut tanpa data market cap.")
        return results

    by_symbol = {}
    for c in rows:
        by_symbol[c["symbol"].upper()] = c
    for r in results:
        base = r["symbol"].split("/")[0].upper()
        c = by_symbol.get(base)
        if not c:
            r["coingecko_note"] = "market cap tidak ketemu di CoinGecko (simbol ambigu?)"
            continue
        mcap = c.get("market_cap") or 0
        fdv = c.get("fully_diluted_valuation") or 0
        r["coingecko_id"] = c.get("id")
        r["coingecko_name"] = c.get("name")
        r["market_cap_usd"] = mcap
        r["market_cap_rank"] = c.get("market_cap_rank")
        r["change_7d_pct"] = c.get("price_change_percentage_7d_in_currency")
        r["ath_change_pct"] = c.get("ath_change_percentage")
        r["fdv_mcap_ratio"] = round(fdv / mcap, 2) if mcap > 0 and fdv else None
        bonus, notes = 0, []
        if 10_000_000 <= mcap <= 500_000_000:
            bonus = 10
            notes.append("market cap $10-500 jt: masih ada ruang naik")
        elif 500_000_000 < mcap <= 2_000_000_000:
            bonus = 5
        elif mcap > 5_000_000_000:
            bonus = -10
            notes.append("market cap > $5 M: susah naik 2x cepat")
        elif 0 < mcap < 5_000_000:
            bonus = -10
            notes.append("market cap < $5 jt: terlalu kecil / berisiko")
        if r["fdv_mcap_ratio"] and r["fdv_mcap_ratio"] > 3:
            notes.append(f"FDV {r['fdv_mcap_ratio']}x market cap: banyak suplai belum beredar")
            bonus -= 5
        r["score"] = max(0, min(100, int(r["score"]) + bonus))
        r["coingecko_note"] = "; ".join(notes) if notes else ""
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def main():
    parser = argparse.ArgumentParser(description="Breakout scanner VibeTrade AI")
    parser.add_argument("--exchange", default=EXCHANGE_NAME)
    parser.add_argument("--quote", default=QUOTE)
    parser.add_argument("--min-volume", type=float, default=MIN_VOLUME_24H_USD)
    parser.add_argument("--max-check", type=int, default=MAX_CHECK)
    parser.add_argument("--top", type=int, default=TOP_N)
    parser.add_argument("--min-score", type=int, default=MIN_SCORE)
    parser.add_argument("--enrich", action="store_true", default=True,
                        help="Tambahkan data market cap dari CoinGecko (default: aktif)")
    parser.add_argument("--no-enrich", dest="enrich", action="store_false",
                        help="Lewati CoinGecko, scan hanya dari data exchange")
    args = parser.parse_args()

    results = scan_explosive(
        exchange_name=args.exchange, quote=args.quote,
        min_volume=args.min_volume, max_check=args.max_check,
        top_n=args.top, min_score=args.min_score,
    )
    print()
    if args.enrich:
        print("[COINGECKO] Mengambil data market cap untuk kandidat teratas...")
        results = enrich_with_coingecko(results)
    if not results:
        print("Tidak ada kandidat breakout hari ini. Itu normal, "
              "scanner ini memang sengaja ketat supaya tidak banyak false alarm.")
        print("Coba lagi besok, atau turunkan --min-score ke 50.")
        return
    print(f"=== Kandidat breakout (top {len(results)}) ===")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['symbol']}  skor {r['score']}/100  "
              f"harga {r['price']:,.4g}  +{r['change_24h_pct']}% (24 jam)")
        print(f"   Alasan: {'; '.join(r['reasons']) if r['reasons'] else '-'}")
        print(f"   Volume: {r['volume_ratio']}x rata-rata, "
              f"range 14 hari: {r['range_14d_pct']}%, "
              f"breakout: {r['breakout_pct']:+.1f}%")
        if r.get("market_cap_usd"):
            ch7 = r.get("change_7d_pct")
            ath = r.get("ath_change_pct")
            print(f"   CoinGecko: {r.get('coingecko_name')} (#{r.get('market_cap_rank')}) "
                  f"market cap ${r['market_cap_usd']:,.0f}"
                  + (f", 7 hari: {ch7:+.1f}%" if ch7 is not None else "")
                  + (f", dari ATH: {ath:.1f}%" if ath is not None else "")
                  + (f", FDV/mcap: {r.get('fdv_mcap_ratio')}x" if r.get("fdv_mcap_ratio") else ""))
            if r.get("coingecko_note"):
                print(f"   Catatan: {r['coingecko_note']}")
        elif r.get("coingecko_note"):
            print(f"   CoinGecko: {r['coingecko_note']}")
    print()
    print("Ingat: ini kandidat, bukan jaminan naik 2x. Cek dulu berita/listing, "
          "pastikan koinnya ada di exchange tempat kamu trading, dan selalu "
          "pakai stop-loss kalau nanti masuk dengan uang asli.")


if __name__ == "__main__":
    main()
