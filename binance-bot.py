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
buy_price = None

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

def calculate_stop_loss_threshold(high_prices, low_prices, close_prices, period=14):
    atr = talib.ATR(np.array(high_prices), np.array(low_prices), np.array(close_prices), timeperiod=period)
    average_atr = np.mean(atr[-period:])
    average_close_price = np.mean(close_prices[-period:])
    stop_loss_threshold_percentage = (1 - (average_atr / average_close_price)) * 100
    return stop_loss_threshold_percentage

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

def detect_slowly_melt_up(short_ma, long_ma, threshold):
    return short_ma > long_ma and (short_ma - long_ma) < threshold

def detect_bull_flag_consolidation(close_prices, upper_band, lower_band, middle_band):
    price_range = np.ptp(close_prices[-10:])
    band_range = upper_band[-1] - lower_band[-1]
    return price_range < band_range and middle_band[-1] > middle_band[-2]

def main():
    in_position = False
    global buy_price

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
        current_price = close_prices[-1]
        # Define a strong trend threshold
        strong_trend_adx_threshold = 25

        stop_loss_threshold_percentage = calculate_stop_loss_threshold(high_prices, low_prices, close_prices)
               
        print(f"Short MA: {short_ma}, Long MA: {long_ma}, Trend:{trend}, RSI: {rsi}, adx: {adx}")
        print(f"Trend:{trend}, RSI: {rsi}")
        print(f"ADX - Direction Strength Index: {adx}")
        print("Stop loss threshold: {:.2f}%".format(stop_loss_threshold_percentage)) 

        if short_ma > long_ma and rsi < 30 and trend == 'uptrend' and adx >= strong_trend_adx_threshold:
            print("Buying signal detected")
            if not in_position:
                balance = exchange.fetch_balance()['USDT']['free']
                amount_to_buy = balance * 0.99  # Use 99% of balance to account for fees
                if amount_to_buy > 10:  # Binance minimum order size is around 10 USDT
                    order = exchange.create_market_buy_order(symbol, amount_to_buy / ohlcv[-1][4])
                    print(f"Bought {symbol} at ${current_price}")
                    buy_price = current_price
                    in_position = True
        elif short_ma < long_ma and rsi > 70 and trend == 'downtrend' and adx >= strong_trend_adx_threshold:
            print("Selling signal detected")
            if in_position:
                amount_to_sell = exchange.fetch_balance()[symbol.split('/')[0]]['free']
                print(f"Balance: {amount_to_sell}")
                if amount_to_sell > 0:
                    order = exchange.create_market_sell_order(symbol, amount_to_sell)
                    print(f"Sold {symbol} at ${current_price}")
                    buy_price = None
                    in_position = False

        if buy_price and in_position and current_price <= buy_price * stop_loss_threshold_percentage:
        # Sell the asset immediately
            print("Stop-loss triggered. Sell signal detected.")
            amount_to_sell = exchange.fetch_balance()[symbol.split('/')[0]]['free']
            print(f"Balance: {amount_to_sell}")
            if amount_to_sell > 0:
                order = exchange.create_market_sell_order(symbol, amount_to_sell)
                print(f"Stopped-out {symbol} at ${current_price}")
                buy_price = None
                in_position = False

        slowly_melt_up = detect_slowly_melt_up(short_ma, long_ma, threshold=50)
        if slowly_melt_up:
            print("Slowly melt-up detected")

        # Add bull flag consolidation detection
        upper, middle, lower = talib.BBANDS(close_prices, timeperiod=20)
        bull_flag_consolidation = detect_bull_flag_consolidation(close_prices, upper, lower, middle)
        if bull_flag_consolidation:
            print("Bull flag consolidation detected")            

        time.sleep(60 * 60)  # Sleep for an hour

if __name__ == '__main__':
    main()
