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


def fetch_historical_prices(exchange, symbol, timeframe='1d', limit=50):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    high_prices = [x[2] for x in ohlcv]
    low_prices = [x[3] for x in ohlcv]
    close_prices = [x[4] for x in ohlcv]
    return high_prices, low_prices, close_prices

def get_atr(high, low, close, period=14):
    atr = talib.ATR(high, low, close, timeperiod=period)
    return atr

def get_sma_trend(close_prices, period_short=50, period_long=200):
    short_sma = talib.SMA(np.array(close_prices), timeperiod=period_short)
    long_sma = talib.SMA(np.array(close_prices), timeperiod=period_long)

    if short_sma[-1] > long_sma[-1]:
        return 'uptrend'
    elif short_sma[-1] < long_sma[-1]:
        return 'downtrend'
    else:
        return 'sideways'

def get_adx(high_prices, low_prices, close_prices, period=14):
    adx = talib.ADX(np.array(high_prices), np.array(low_prices), np.array(close_prices), timeperiod=period)
    return adx[-1]

def get_rsi(close_prices, period=14):
    close_prices_np = np.array(close_prices, dtype=float)
    rsi = talib.RSI(close_prices_np, timeperiod=period)
    return rsi

def get_moving_average(history, window):
    return sum(history[-window:]) / window

def main():
    in_position = False

    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
        close_prices = [x[4] for x in ohlcv]

        short_ma = get_moving_average(close_prices, moving_avg_short)
        long_ma = get_moving_average(close_prices, moving_avg_long)
        rsi = get_rsi(close_prices)[-1]
        trend = get_sma_trend(close_prices)
         # Get the ADX value
         # Fetch historical prices
        high_prices, low_prices, close_prices = fetch_historical_prices(exchange, symbol)
        high_prices = np.array(high_prices)
        low_prices = np.array(low_prices)
        close_prices = np.array(close_prices)
        adx = get_adx(high_prices, low_prices, close_prices)
        # Define a strong trend threshold
        strong_trend_adx_threshold = 25

        atr = get_atr(high_prices, low_prices, close_prices)
# Calculate the average ATR over the last 14 periods (1 hour timeframe)
        average_atr = np.mean(atr[-14:])

# Set the stop-loss threshold as a multiple of the average ATR
        stop_loss_multiple = 2  # Adjust this value based on your risk tolerance
        stop_loss_threshold = average_atr * stop_loss_multiple

        
        print(f"Short MA: {short_ma}, Long MA: {long_ma}, Trend:{trend}, RSI: {rsi}, Stop-loss threshold: {stop_loss_threshold}, adx: {adx}")

        if short_ma > long_ma and rsi < 30 and trend == 'uptrend' and adx >= strong_trend_adx_threshold:
            print("Buying signal detected")
            if not in_position:
                balance = exchange.fetch_balance()['USDT']['free']
                amount_to_buy = balance * 0.99  # Use 99% of balance to account for fees
                if amount_to_buy > 10:  # Binance minimum order size is around 10 USDT
                    order = exchange.create_market_buy_order(symbol, amount_to_buy / ohlcv[-1][4])
                    print(f"Bought {symbol}")
                    in_position = True
        elif short_ma < long_ma and rsi > 70 and trend == 'downtrend' and adx >= strong_trend_adx_threshold:
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
