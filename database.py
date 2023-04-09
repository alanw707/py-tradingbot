from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Price, Signal, Trade

def init_database(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

def log_price(session, timestamp, symbol, price, rsi,short_ma,long_ma,trend,adx,stop_loss_threshold_percentage):    
    price_entry = Price(
        symbol=symbol,
        timestamp=timestamp,
        price=price,
        rsi=rsi,
        short_ma=short_ma[-1],
        long_ma=long_ma[-1],
        trend=trend,
        adx=adx,
        stop_loss_threshold_percentage=stop_loss_threshold_percentage
    )     
    session.add(price_entry)
    session.commit()

def log_signal(session, timestamp, symbol, signal_type):
    signal_entry = Signal(timestamp=timestamp, symbol=symbol, signal_type=signal_type)
    session.add(signal_entry)
    session.commit()

def log_trade(session, timestamp, symbol, trade_type, price, amount, stop_out_amount=0):
    trade_entry = Trade(timestamp=timestamp, symbol=symbol, trade_type=trade_type, price=price, amount=amount, stop_out_amount=stop_out_amount)
    session.add(trade_entry)
    session.commit()

def get_last_trade(session, symbol):
    last_trade = session.query(Trade).filter(Trade.symbol == symbol).order_by(Trade.timestamp.desc()).first()
    return last_trade

