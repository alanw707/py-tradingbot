import numpy as np
import talib

def detect_bull_flag_breakout(high_prices, low_prices, close_prices, period=14):
    high_prices_np = np.array(high_prices)
    low_prices_np = np.array(low_prices)
    #close_prices_np = np.array(close_prices)
    highest_high = talib.MAX(high_prices_np, timeperiod=period)
    lowest_low = talib.MIN(low_prices_np, timeperiod=period)

    breakout = False
    flagpole_detected = False

    for i in range(period - 1, len(close_prices) - 1):
        if close_prices[i] > highest_high[i - period + 1]:
            flagpole_detected = True
            break

    if flagpole_detected:
        consolidation_range = highest_high[-1] - lowest_low[-1]
        breakout_threshold = highest_high[-1] + (consolidation_range * 0.25)

        if close_prices[-1] > breakout_threshold:
            breakout = True
    return breakout

def detect_golden_cross(short_sma, long_sma):
    if short_sma[-2] <= long_sma[-2] and short_sma[-1] > long_sma[-1]:
        return True
    return False

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

def get_sma(close_prices, period):
    close_prices_np = np.array(close_prices)
    return talib.SMA(close_prices_np, timeperiod=period)

def detect_slowly_melt_up(short_ma, long_ma, threshold):
    return short_ma > long_ma and (short_ma - long_ma) < threshold

def detect_bull_flag_consolidation(close_prices, upper_band, lower_band, middle_band):
    price_range = np.ptp(close_prices[-10:])
    band_range = upper_band[-1] - lower_band[-1]
    return price_range < band_range and middle_band[-1] > middle_band[-2]
