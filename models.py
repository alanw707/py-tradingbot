from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Price(Base):
    __tablename__ = 'prices'

    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    timestamp = Column(DateTime)
    price = Column(Float)
    rsi = Column(Float)
    short_ma = Column(Float)
    long_ma = Column(Float)
    trend = Column(String)
    adx = Column(Float)
    stop_loss_threshold_percentage = Column(Float)

    def __repr__(self):
        return f"<Price(symbol={self.symbol}, timestamp={self.timestamp}, price={self.price}, rsi={self.rsi}, short_ma={self.short_ma}, long_ma={self.long_ma}, trend={self.trend}, adx={self.adx}, stop_loss_threshold_percentage={self.stop_loss_threshold_percentage})>"


class Signal(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)    
    trade_type = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    stop_out_price = Column(Float, nullable=False)
