"""Coinbase exchange adapter"""
import logging
from typing import List
from datetime import datetime

from ..exchange_base import ExchangeAdapter
from ..exchange_types import MarketData, OrderBookData, TradeData


logger = logging.getLogger(__name__)


class CoinbaseAdapter(ExchangeAdapter):
    """Coinbase exchange API adapter"""
    
    @property
    def exchange_name(self) -> str:
        return "coinbase"
    
    @property
    def base_url(self) -> str:
        return "https://api.exchange.coinbase.com"
    
    @property
    def ws_url(self) -> str:
        return "wss://ws-feed.exchange.coinbase.com"
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Convert ZEC/USD to ZEC-USD format.
        
        Args:
            symbol: Standard symbol (e.g., "ZEC/USD")
            
        Returns:
            Coinbase symbol format (e.g., "ZEC-USD")
        """
        return symbol.replace("/", "-")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """
        Get ticker data from Coinbase.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Market data
        """
        coinbase_symbol = self.normalize_symbol(symbol)
        
        # Get ticker
        ticker = await self._request(
            method="GET",
            endpoint=f"/products/{coinbase_symbol}/ticker"
        )
        
        # Get 24hr stats
        stats = await self._request(
            method="GET",
            endpoint=f"/products/{coinbase_symbol}/stats"
        )
        
        return MarketData(
            symbol=symbol,
            exchange=self.exchange_name,
            timestamp=datetime.fromisoformat(ticker["time"].replace("Z", "+00:00")),
            price=float(ticker["price"]),
            volume_24h=float(stats.get("volume", 0)),
            bid=float(ticker.get("bid", 0)),
            ask=float(ticker.get("ask", 0)),
            high_24h=float(stats.get("high", 0)),
            low_24h=float(stats.get("low", 0)),
            change_24h=None  # Coinbase doesn't provide this directly
        )
    
    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBookData:
        """
        Get order book from Coinbase.
        
        Args:
            symbol: Trading pair symbol
            depth: Number of price levels (1, 2, or 3 for Coinbase)
            
        Returns:
            Order book data
        """
        coinbase_symbol = self.normalize_symbol(symbol)
        
        # Coinbase uses level parameter: 1=best bid/ask, 2=top 50, 3=full book
        level = 2 if depth <= 50 else 3
        
        data = await self._request(
            method="GET",
            endpoint=f"/products/{coinbase_symbol}/book",
            params={"level": level}
        )
        
        bids = [(float(price), float(size)) for price, size, _ in data.get("bids", [])]
        asks = [(float(price), float(size)) for price, size, _ in data.get("asks", [])]
        
        # Limit to requested depth
        bids = bids[:depth]
        asks = asks[:depth]
        
        return OrderBookData(
            symbol=symbol,
            exchange=self.exchange_name,
            timestamp=datetime.now(),
            bids=bids,
            asks=asks
        )
    
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
        """
        Get recent trades from Coinbase.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of trades (max 100 per request)
            
        Returns:
            List of recent trades
        """
        coinbase_symbol = self.normalize_symbol(symbol)
        
        data = await self._request(
            method="GET",
            endpoint=f"/products/{coinbase_symbol}/trades",
            params={"limit": min(limit, 100)}
        )
        
        trades = []
        for trade in data:
            trades.append(TradeData(
                symbol=symbol,
                exchange=self.exchange_name,
                timestamp=datetime.fromisoformat(trade["time"].replace("Z", "+00:00")),
                price=float(trade["price"]),
                volume=float(trade["size"]),
                side=trade["side"]
            ))
        
        return trades
