import ccxt
import pandas as pd
import config

def create_exchange():
    return ccxt.tokocrypto({
        'enableRateLimit': True,
        'urls': {
            'api': {
                'rest': {
                    'binance': 'https://data-api.binance.vision/api/v3',
                    'public': 'https://www.tokocrypto.com',
                    'private': 'https://www.tokocrypto.com'
                }
            }
        }
    })

def get_potential_tokens():
    """
    Memindai seluruh ticker dari Tokocrypto via CCXT.
    Memfilter koin berdasarkan QUOTE_CURRENCY (IDR) dan MIN_24H_VOLUME_IDR.
    Mengembalikan daftar simbol koin potensial teratas.
    """
    try:
        exchange = create_exchange()
        tickers = exchange.fetch_tickers()
        
        potential_list = []
        for symbol, data in tickers.items():
            if symbol.endswith("/" + config.QUOTE_CURRENCY):
                volume_24h = data.get('quoteVolume', 0) or 0
                change_24h = data.get('percentage', 0) or 0
                
                if volume_24h >= config.MIN_24H_VOLUME_IDR:
                    potential_list.append({
                        'symbol': symbol,
                        'volume_24h': volume_24h,
                        'change_24h': change_24h
                    })
                    
        df = pd.DataFrame(potential_list)
        if df.empty:
            print(f"[SCREENER] Tidak ada koin yang memenuhi kriteria volume. Fallback ke {config.SYMBOL}")
            return [config.SYMBOL]
            
        df = df.sort_values(by='volume_24h', ascending=False)
        top_tokens = df['symbol'].head(config.TOP_N_POTENTIAL).tolist()
        print(f"[SCREENER] Koin potensial terpilih: {top_tokens}")
        return top_tokens
    except Exception as e:
        print(f"[SCREENER WARNING] Gagal memindai koin: {e}. Fallback ke {config.SYMBOL}")
        return [config.SYMBOL]

if __name__ == "__main__":
    tokens = get_potential_tokens()
    print("Hasil Scan:", tokens)
