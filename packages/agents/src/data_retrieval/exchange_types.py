"""Type definitions for exchange data"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MarketData(BaseModel):
    """Market data for a trading pair"""
    symbol: str = Field(description="Trading pair symbol (e.g., ZEC/USD)")
    exchange: str = Field(description="Exchange name")
    timestamp: datetime = Field(description="Data timestamp")
    price: float = Field(description="Current price")
    volume_24h: float = Field(description="24-hour trading volume")
    bid: Optional[float] = Field(default=None, description="Best bid price")
    ask: Optional[float] = Field(default=None, description="Best ask price")
    high_24h: Optional[float] = Field(default=None, description="24-hour high")
    low_24h: Optional[float] = Field(default=None, description="24-hour low")
    change_24h: Optional[float] = Field(default=None, description="24-hour price change percentage")


class OrderBookData(BaseModel):
    """Order book snapshot"""
    symbol: str = Field(description="Trading pair symbol")
    exchange: str = Field(description="Exchange name")
    timestamp: datetime = Field(description="Snapshot timestamp")
    bids: list[tuple[float, float]] = Field(description="Bid prices and volumes")
    asks: list[tuple[float, float]] = Field(description="Ask prices and volumes")
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread"""
        if self.bids and self.asks:
            return self.asks[0][0] - self.bids[0][0]
        return 0.0
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price"""
        if self.bids and self.asks:
            return (self.bids[0][0] + self.asks[0][0]) / 2
        return 0.0


class TradeData(BaseModel):
    """Individual trade data"""
    symbol: str = Field(description="Trading pair symbol")
    exchange: str = Field(description="Exchange name")
    timestamp: datetime = Field(description="Trade timestamp")
    price: float = Field(description="Trade price")
    volume: float = Field(description="Trade volume")
    side: str = Field(description="Trade side: buy or sell")
