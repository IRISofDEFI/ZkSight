"""Kraken exchange adapter"""
import logging
from typing import List
from datetime import datetime

from ..exchange_base import ExchangeAdapter
from ..exchange_types import MarketData, OrderBookData, TradeData


logger = logging.getLogger(__name__)


class KrakenAdapter(ExchangeAdapter):
    """Kraken exchange API adapter"""
    
    @property
    def exchange_name(self) -> str:
        return "kraken"
    
    @property
    def base_url(self) -> str:
        return "https://api.kraken.com"
    
    @property
    def ws_url(self) -> str:
        return "wss://ws.kraken.com"
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Convert ZEC/USD to XZECUSD format.
        
        Args:
            symbol: Standard symbol (e.g., "ZEC/USD")
            
        Returns:
            Kraken symbol format (e.g., "XZECUSD" or "ZECUSD")
        """
        # Kraken uses X prefix for some currencies
        base, quote = symbol.split("/")
        
        # Map common symbols
        symbol_map = {
            "BTC": "XBT",
            "ZEC": "ZEC",
            "USD": "USD",
            "EUR": "EUR"
        }
        
        base = symbol_map.get(base, base)
        quote = symbol_map.get(quote, quote)
        
        return f"{base}{quote}"
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """
        Get ticker data from Kraken.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Market data
        """
        kraken_symbol = self.normalize_symbol(symbol)
        
        data = await self._request(
            method="GET",
            endpoint="/0/public/Ticker",
            params={"pair": kraken_symbol}
        )
        
        if data.get("error"):
            raise Exception(f"Kraken API error: {data['error']}")
        
        # Kraken returns data with the pair name as key
        ticker_key = list(data["result"].keys())[0]
        ticker = data["result"][ticker_key]
        
        return MarketData(
            symbol=symbol,
            exchange=self.exchange_name,
            timestamp=datetime.now(),
            price=float(ticker["c"][0]),  # Last trade closed
            volume_24h=float(ticker["v"][1]),  # 24h volume
            bid=float(ticker["b"][0]),  # Best bid
            ask=float(ticker["a"][0]),  # Best ask
            high_24h=float(ticker["h"][1]),  # 24h high
            low_24h=float(ticker["l"][1]),  # 24h low
            change_24h=None  # Calculate from open if needed
        )
    
    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBookData:
        """
        Get order book from Kraken.
        
        Args:
            symbol: Trading pair symbol
            depth: Number of price levels (max 500)
            
        Returns:
            Order book data
        """
        kraken_symbol = self.normalize_symbol(symbol)
        
        data = await self._request(
            method="GET",
            endpoint="/0/public/Depth",
            params={"pair": kraken_symbol, "count": depth}
        )
        
        if data.get("error"):
            raise Exception(f"Kraken API error: {data['error']}")
        
        # Kraken returns data with the pair name as key
        book_key = list(data["result"].keys())[0]
        book = data["result"][book_key]
        
        bids = [(float(price), float(volume)) for price, volume, _ in book["bids"]]
        asks = [(float(price), float(volume)) for price, volume, _ in book["asks"]]
        
        return OrderBookData(
            symbol=symbol,
            exchange=self.exchange_name,
            timestamp=datetime.now(),
            bids=bids,
            asks=asks
        )
    
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
        """
        Get recent trades from Kraken.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of trades (max 1000)
            
        Returns:
            List of recent trades
        """
        kraken_symbol = self.normalize_symbol(symbol)
        
        data = await self._request(
            method="GET",
            endpoint="/0/public/Trades",
            params={"pair": kraken_symbol, "count": limit}
        )
        
        if data.get("error"):
            raise Exception(f"Kraken API error: {data['error']}")
        
        # Kraken returns data with the pair name as key
        trades_key = list(data["result"].keys())[0]
        trades_data = data["result"][trades_key]
        
        trades = []
        for trade in trades_data:
            price, volume, timestamp, side, *_ = trade
            
            trades.append(TradeData(
                symbol=symbol,
                exchange=self.exchange_name,
                timestamp=datetime.fromtimestamp(float(timestamp)),
                price=float(price),
                volume=float(volume),
                side="buy" if side == "b" else "sell"
            ))
        
        return trades
