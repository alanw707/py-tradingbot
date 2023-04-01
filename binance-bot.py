import time
import talib
import numpy as np
import os
from dotenv import load_dotenv
from trading_signals import (
    detect_bull_flag_breakout, detect_golden_cross, fetch_historical_prices,
    calculate_stop_loss_threshold, get_sma_trend, get_adx, get_rsi, get_sma,
    detect_slowly_melt_up, detect_bull_flag_consolidation
)
from trading_operations import (
    init_exchange, buy_order, sell_order
)

load_dotenv()

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

symbol = 'BTC/USDT'
timeframe = '30m'
moving_avg_short = 50
moving_avg_long = 200
buy_price = None

# Initialize the Binance exchange object
exchange = init_exchange(api_key, secret_key)

def main():
    in_position = False
    global buy_price, in_short_position

    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
        close_prices = [x[4] for x in ohlcv]

        short_ma = get_sma(close_prices, moving_avg_short)
        long_ma = get_sma(close_prices, moving_avg_long)
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

        print(f"Current Price: ${current_price}")       
        print(f"Short MA: {short_ma[-1]}, Long MA: {long_ma[-1]}")
        print(f"Trend:{trend}, RSI: {rsi}")
        print(f"ADX - direction strength: {adx}")
        print("Stop loss threshold: {:.2f}%".format(stop_loss_threshold_percentage)) 

        slowly_melt_up = detect_slowly_melt_up(short_ma[-1], long_ma[-1], threshold=50)
        if slowly_melt_up:
            print("Slowly melt-up detected")
        # Add bull flag consolidation detection
        upper, middle, lower = talib.BBANDS(close_prices, timeperiod=20)
        bull_flag_consolidation = detect_bull_flag_consolidation(close_prices, upper, lower, middle)
        if bull_flag_consolidation:
            print("Bull flag consolidation detected")            

        if detect_bull_flag_breakout(high_prices, low_prices, close_prices):
            print("Bull flag breakout detected")
        # Add your buy order logic here
        if detect_golden_cross(short_ma, long_ma):
            print("Golden cross detected")

        if short_ma[-1] > long_ma[-1]  and rsi < 30 and trend == 'uptrend' and adx >= strong_trend_adx_threshold:
            print("Buying signal detected")
            if not in_position:
                balance = exchange.fetch_balance()['USDT']['free']
                amount_to_buy = balance * 0.99  # Use 99% of balance to account for fees
                if amount_to_buy > 10:  # Binance minimum order size is around 10 USDT
                    order = buy_order(exchange, symbol, amount_to_buy / ohlcv[-1][4])
                    if order:
                        print(f"Bought {symbol} at ${order['price']}")
                        buy_price = order['price']
                        in_position = True
        elif short_ma[-1] < long_ma[-1]  and rsi > 70 and trend == 'downtrend' and adx >= strong_trend_adx_threshold:
            print("Selling signal detected")
            if in_position:
                amount_to_sell = exchange.fetch_balance()[symbol.split('/')[0]]['free']
                print(f"Balance: {amount_to_sell}")
                if amount_to_sell > 0:
                    order = sell_order(exchange, symbol, amount_to_sell)
                    if order:
                        print(f"Sold {symbol} at ${order['price']}")
                        buy_price = None
                        in_position = False

        if buy_price and in_position and current_price <= buy_price * stop_loss_threshold_percentage:
        # Sell the asset immediately
            print("Stop-loss triggered. Sell signal detected.")
            amount_to_sell = exchange.fetch_balance()[symbol.split('/')[0]]['free']
            print(f"Balance: {amount_to_sell}")
            if amount_to_sell > 0:
                order = sell_order(exchange, symbol, amount_to_sell)
                if order:
                    print(f"Stopped-out {symbol} at ${order['price']}")
                    buy_price = None
                    in_position = False       

        time.sleep(60 * 30)  # Sleep for 30 minutes

if __name__ == '__main__':
    main()
