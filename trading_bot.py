import ccxt
import time
import talib
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

symbol = 'BTC/USDT'
timeframe = '1h'
moving_avg_short = 50
moving_avg_long = 200

# Initialize the Binance exchange object
exchange = ccxt.binanceus({
    'apiKey': api_key,
    'secret': secret_key,
    'enableRateLimit': True,
    'rateLimit': 1200,
})

def get_rsi(close_prices, period=14):
    close_prices_np = np.array(close_prices, dtype=float)
    rsi = talib.RSI(close_prices_np, timeperiod=period)
    return rsi

def get_moving_average(history, window):
    return sum(history[-window:]) / window

def main():
    in_position = True

    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
        close_prices = [x[4] for x in ohlcv]

        short_ma = get_moving_average(close_prices, moving_avg_short)
        long_ma = get_moving_average(close_prices, moving_avg_long)
        rsi = get_rsi(close_prices)[-1]

        print(f"Short MA: {short_ma}, Long MA: {long_ma}, RSI: {rsi}")

        if short_ma > long_ma and rsi < 30:
            print("Buying signal detected")
            if not in_position:
                balance = exchange.fetch_balance()['USDT']['free']
                amount_to_buy = balance * 0.99  # Use 99% of balance to account for fees
                if amount_to_buy > 10:  # Binance minimum order size is around 10 USDT
                    order = exchange.create_market_buy_order(symbol, amount_to_buy / ohlcv[-1][4])
                    print(f"Bought {symbol}")
                    in_position = True
        elif short_ma < long_ma and rsi > 70:
            print("Selling signal detected")
            if in_position:
                amount_to_sell = exchange.fetch_balance()[symbol.split('/')[0]]['free']
                print(f"Balance: {amount_to_sell}")
                if amount_to_sell > 0:
                    order = exchange.create_market_sell_order(symbol, amount_to_sell)
                print(f"Sold {symbol}")
                in_position = False

        time.sleep(60 * 60)  # Sleep for an hour

if __name__ == '__main__':
    main()
