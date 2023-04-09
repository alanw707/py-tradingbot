from datetime import datetime
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
from database import init_database, log_price, log_signal, log_trade, get_last_trade
from trade_orge import TradeOgre

load_dotenv()

api_key = os.environ.get('TRADEORGE_API_KEY')
secret_key = os.environ.get('TRADEORGE_SECRET')

binance_api_key = os.environ.get('BINANCE_API_KEY')
binance_secret_key = os.environ.get('BINANCE_SECRET_KEY')

database_url = 'sqlite:///trading_bot.db'  # Change this to your preferred database URL

symbol = 'KAS/USDT'
timeframe = '30m'
moving_avg_short = 50
moving_avg_long = 200
buy_price = None
stop_out_price = None
take_profit_price = None

# Initialize the Binance exchange object
exchange = TradeOgre(api_key,secret_key)

binance_exchange = init_exchange(binance_api_key, binance_secret_key)

# Initialize the database and create a session
Session = init_database(database_url)
session = Session()

def main():
    
    global buy_price, stop_out_price, take_profit_price
    last_trade = get_last_trade(session, symbol)

    # Set the in_position value based on the last trade
    in_position = False

    if last_trade and last_trade.trade_type == 'buy':
        in_position = True
        buy_price = last_trade.price
        stop_out_price = last_trade.stop_out_price
        

    while True:
        ohlcv = binance_exchange.fetch_ohlcv(symbol, timeframe)
        close_prices = [x[4] for x in ohlcv]
        current_timestamp = datetime.now()        

        short_ma = get_sma(close_prices, moving_avg_short)
        long_ma = get_sma(close_prices, moving_avg_long)
        rsi = get_rsi(close_prices)[-1]
        trend = get_sma_trend(close_prices)
         
         # Fetch historical prices
        high_prices, low_prices, close_prices = fetch_historical_prices(exchange, symbol)
        high_prices = np.array(high_prices)
        low_prices = np.array(low_prices)
        close_prices = np.array(close_prices)
        stop_loss_threshold_percentage = calculate_stop_loss_threshold(high_prices, low_prices, close_prices)
        take_profit_percentage = (100 - stop_loss_threshold_percentage) * 2
        # Get the ADX value
        high_prices, low_prices, close_prices = fetch_historical_prices(exchange, symbol,timeframe)
        high_prices = np.array(high_prices)
        low_prices = np.array(low_prices)
        close_prices = np.array(close_prices)
        adx = get_adx(high_prices, low_prices, close_prices)

        current_price = close_prices[-1]

        strong_trend_adx_threshold = 25
        
        print(f"{current_timestamp}")
        if last_trade:
            print(f"In-position: {in_position}, trade.price: {last_trade.price}, trade.type: {last_trade.trade_type}, stop-loss: {last_trade.stop_out_price}")

        print(f"Current BTC Price: ${current_price}")       
        print(f"Short MA: {short_ma[-1]}, Long MA: {long_ma[-1]}")
        print(f"Trend:{trend}")
        print(f"RSI: {rsi}")
        print(f"ADX: {adx}")        
        print("Stop-loss precentage: {:.2f}%".format(100 - stop_loss_threshold_percentage))
        print("Take-profit percentage: {:.2f}%".format(take_profit_percentage))
                
        log_price(session, current_timestamp, symbol, current_price,rsi,short_ma,long_ma,trend,adx,stop_loss_threshold_percentage)
        
        slowly_melt_up = detect_slowly_melt_up(short_ma[-1], long_ma[-1], threshold=50)
        if slowly_melt_up:
            print("Slowly melt-up detected")
            log_signal(session, current_timestamp, symbol, 'Slowly melt-up detected') 
        
        # Add bull flag consolidation detection
        upper, middle, lower = talib.BBANDS(close_prices, timeperiod=20)
        bull_flag_consolidation = detect_bull_flag_consolidation(close_prices, upper, lower, middle)
        if bull_flag_consolidation:
            print("Bull flag consolidation detected") 
            log_signal(session, current_timestamp, symbol, 'bull_flag_consolidation')               

        if detect_bull_flag_breakout(high_prices, low_prices, close_prices):
            print("Bull flag breakout detected")
            log_signal(session, current_timestamp, symbol, 'bull_flag_breakout')    

        if detect_golden_cross(short_ma, long_ma):
            print("Golden cross detected")
            log_signal(session, current_timestamp, symbol, 'golden_cross')      

        if short_ma[-1] > long_ma[-1]  and rsi < 30 and trend == 'uptrend' and adx > strong_trend_adx_threshold:
            print("Buying signal detected")
            if not in_position:
                balance = exchange.fetch_balance()['USDT']['free']
                amount_to_buy = balance * 0.99  # Use 99% of balance to account for fees
                if amount_to_buy > 10:
                    order = buy_order(exchange, symbol, amount_to_buy / ohlcv[-1][4])
                    if order:
                        print(f"Bought {symbol} at ${order['price']}")
                        buy_price = order['price']
                        stop_out_price =  buy_price * ((100 - stop_loss_threshold_percentage) / 100)
                        take_profit_price = buy_price * ((100 + take_profit_percentage) / 100)
                        in_position = True                        
                        log_trade(session, current_timestamp, symbol, 'buy', order['price'], amount_to_buy / ohlcv[-1][4],stop_out_price,take_profit_price)
        elif short_ma[-1] < long_ma[-1]  and rsi > 70 and trend == 'downtrend' and current_price >= take_profit_price:
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
                        log_trade(session, current_timestamp, symbol, 'sell', order['price'], amount_to_sell)
                                        
        if buy_price and in_position and current_price <= stop_out_price:
            # Sell the asset immediately if price fall below stop_loss
            print(f"Stop-loss triggered @${buy_price * (stop_loss_threshold_percentage / 100)}")
            amount_to_sell = exchange.fetch_balance()[symbol.split('/')[0]]['free']
            print(f"Balance: {amount_to_sell}")
            if amount_to_sell > 0:
                order = sell_order(exchange, symbol, amount_to_sell)
                if order:
                    print(f"Stopped-out {symbol} at ${order['price']}")
                    buy_price = None
                    in_position = False
                    # Log the trade into the database
                    log_trade(session, current_timestamp, symbol, 'sell', order['price'], amount_to_sell)

        time.sleep(60 * 15)     

if __name__ == '__main__':
    main()

