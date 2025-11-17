"""Binance exchange adapter"""
import logging
from typing import List, Optional
from datetime import datetime

from ..exchange_base import ExchangeAdapter
from ..exchange_types import MarketData, OrderBookData, TradeData


logger = logging.getLogger(__name__)


class BinanceAdapter(ExchangeAdapter):
    """Binance exchange API adapter"""
    
    @property
    def exchange_name(self) -> str:
        return "binance"
    
    @property
    def base_url(self) -> str:
        return "https://api.binance.com"
    
    @property
    def ws_url(self) -> str:
        return "wss://stream.binance.com:9443/ws"
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Convert ZEC/USD to ZECUSDT format.
        
        Args:
            symbol: Standard symbol (e.g., "ZEC/USD")
            
        Returns:
            Binance symbol format (e.g., "ZECUSDT")
        """
        return symbol.replace("/", "").replace("USD", "USDT")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """
        Get 24hr ticker data from Binance.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Market data
        """
        binance_symbol = self.normalize_symbol(symbol)
        
        data = await self._request(
            method="GET",
            endpoint="/api/v3/ticker/24hr",
            params={"symbol": binance_symbol}
        )
        
        return MarketData(
            symbol=symbol,
            exchange=self.exchange_name,
            timestamp=datetime.fromtimestamp(data["closeTime"] / 1000),
            price=float(data["lastPrice"]),
            volume_24h=float(data["volume"]),
            bid=float(data["bidPrice"]),
            ask=float(data["askPrice"]),
            high_24h=float(data["highPrice"]),
            low_24h=float(data["lowPrice"]),
            change_24h=float(data["priceChangePercent"])
        )
    
    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBookData:
        """
        Get order book from Binance.
        
        Args:
            symbol: Trading pair symbol
            depth: Number of price levels (max 5000)
            
        Returns:
            Order book data
        """
        binance_symbol = self.normalize_symbol(symbol)
        
        data = await self._request(
            method="GET",
            endpoint="/api/v3/depth",
            params={"symbol": binance_symbol, "limit": depth}
        )
        
        bids = [(float(price), float(qty)) for price, qty in data["bids"]]
        asks = [(float(price), float(qty)) for price, qty in data["asks"]]
        
        return OrderBookData(
            symbol=symbol,
            exchange=self.exchange_name,
            timestamp=datetime.now(),
            bids=bids,
            asks=asks
        )
    
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
        """
        Get recent trades from Binance.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of trades (max 1000)
            
        Returns:
            List of recent trades
        """
        binance_symbol = self.normalize_symbol(symbol)
        
        data = await self._request(
            method="GET",
            endpoint="/api/v3/trades",
            params={"symbol": binance_symbol, "limit": limit}
        )
        
        trades = []
        for trade in data:
            trades.append(TradeData(
                symbol=symbol,
                exchange=self.exchange_name,
                timestamp=datetime.fromtimestamp(trade["time"] / 1000),
                price=float(trade["price"]),
                volume=float(trade["qty"]),
                side="buy" if trade["isBuyerMaker"] else "sell"
            ))
        
        return trades
