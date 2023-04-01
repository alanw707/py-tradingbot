# trading_operations.py
import ccxt

def init_exchange(api_key, secret_key):
    exchange = ccxt.binanceus({
        'apiKey': api_key,
        'secret': secret_key,
        'enableRateLimit': True,
        'rateLimit': 1200,
    })
    return exchange

def buy_order(exchange, symbol, amount_to_buy):
    try:
        order = exchange.create_market_buy_order(symbol, amount_to_buy)
        print(f"Bought {symbol} at ${order['price']}")
        return order
    except Exception as e:
        print(f"Error placing buy order: {e}")
        return None
    
def sell_order(exchange, symbol, amount_to_sell):
    try:
        order = exchange.create_market_sell_order(symbol, amount_to_sell)
        print(f"Sold {symbol} at ${order['price']}")
        return order
    except Exception as e:
        print(f"Error placing sell order: {e}")
        return None
    

# def short_sell_order():
#     ...

# def cover_short_order():
#     ...
