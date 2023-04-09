import os
from dotenv import load_dotenv
import numpy as np
from trading_signals import (
    detect_bull_flag_breakout, detect_golden_cross, fetch_historical_prices,
    calculate_stop_loss_threshold, get_sma_trend, get_adx, get_rsi, get_sma,
    detect_slowly_melt_up, detect_bull_flag_consolidation
)
from trading_operations import (
    init_exchange
)


load_dotenv()

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

symbol = 'BTC/USDT'
timeframe = '30m'
moving_avg_short = 50
moving_avg_long = 200
exchange = init_exchange(api_key, secret_key)

def backtest():
    in_position = False
    buy_price = None
    short_ma = None
    long_ma = None
    total_gain = 1.0  # Initialize total gain to 1 (100%)

    high_prices, low_prices, close_prices = fetch_historical_prices(exchange, symbol, timeframe,1000)
    high_prices = np.array(high_prices)
    low_prices = np.array(low_prices)
    close_prices = np.array(close_prices)

    print(f"close prices:{len(close_prices)}")
    for i in range(moving_avg_long, len(close_prices)):        
        current_price = close_prices[i]

        if i >= moving_avg_short:
            short_ma = get_sma(close_prices[:i], moving_avg_short)
            long_ma = get_sma(close_prices[:i], moving_avg_long)
            rsi = get_rsi(close_prices[:i])[-1]
            trend = get_sma_trend(close_prices[:i])
            adx = get_adx(high_prices[:i], low_prices[:i], close_prices[:i])

        strong_trend_adx_threshold = 25

        if(i>=20):
            # stop_loss_threshold_percentage = calculate_stop_loss_threshold(high_prices, low_prices, close_prices)
            stop_loss_threshold_percentage = 0.95 
            # calculate_stop_loss_threshold(high_prices[:i], low_prices[:i], close_prices[:i], 20) / 100
            # print(f"Current BTC Price: ${current_price}")       
            # print(f"Short MA: {short_ma[-1]}, Long MA: {long_ma[-1]}")
            # print(f"Trend:{trend}")
            # print(f"RSI: {rsi}")
            # print(f"ADX: {adx}")
            #print("Stop-loss threshold: {:.2f}%".format(stop_loss_threshold_percentage)) 

        
        if short_ma is not None and long_ma is not None:
            # Buy signal
            if short_ma[-1] > long_ma[-1] and rsi < 30 and trend == 'uptrend':
                if not in_position:
                    buy_price = current_price
                    in_position = True
                    print(f"Bought {symbol} at ${buy_price}")

            # Sell signal
            elif short_ma[-1] < long_ma[-1] and rsi > 70 and trend == 'downtrend':
                if in_position:
                    sell_price = current_price
                    in_position = False
                    gain = sell_price / buy_price
                    total_gain *= gain
                    print(f"Sold {symbol} at ${sell_price}, Gain: {gain:.2%}")

        # Stop-loss signal
        if in_position and current_price <= buy_price * stop_loss_threshold_percentage:
            sell_price = current_price
            in_position = False
            gain = sell_price / buy_price
            total_gain *= gain
            print(f"Stopped-out {symbol} at ${sell_price}, Loss: {-gain + 1:.2%}")

    if in_position:
        # Sell at the last price if still in position
        sell_price = close_prices[-1]
        gain = sell_price / buy_price
        total_gain *= gain
        print(f"Sold {symbol} at ${sell_price}, Gain: {gain:.2%}")

    overall_gain_loss = total_gain - 1
    print(f"Overall Gain/Loss: {overall_gain_loss:.2%}")

if __name__ == '__main__':
    backtest()
