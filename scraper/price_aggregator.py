#!/usr/bin/env python3
"""
Price Aggregator - Multi-source price feed with fallback hierarchy.
Combines FTSO, CoinGecko, and other sources for reliable price data.
This is a NEW module that extends ftso_price.py without replacing it.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime

import requests
from dotenv import load_dotenv

import config

# Try to import ftso_price for backward compatibility
try:
    import ftso_price
    FTSO_AVAILABLE = True
except ImportError:
    FTSO_AVAILABLE = False
    logging.warning("ftso_price module not available")

load_dotenv()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class PriceAggregator:
    """
    Multi-source cryptocurrency price aggregator with fallback hierarchy.
    
    Priority order:
    1. FTSO (Flare Time Series Oracle) - for supported assets
    2. CoinGecko API - most comprehensive
    3. Binance API - high liquidity pairs
    4. Cached prices - fallback if all sources fail
    """
    
    def __init__(self, 
                 coingecko_api_key: str = None,
                 binance_api_key: str = None):
        """
        Initialize price aggregator.
        
        Args:
            coingecko_api_key: CoinGecko API key (optional, for higher rate limits)
            binance_api_key: Binance API key (optional)
        """
        self.coingecko_api_key = coingecko_api_key or config.COINGECKO_API_KEY
        self.binance_api_key = binance_api_key or config.BINANCE_API_KEY
        
        # Price cache to avoid excessive API calls
        self.price_cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds
        
        logger.info("✅ Price Aggregator initialized")
        logger.info(f"   FTSO available: {FTSO_AVAILABLE}")
        logger.info(f"   CoinGecko API key: {'Yes' if self.coingecko_api_key else 'No'}")
        logger.info(f"   Binance API key: {'Yes' if self.binance_api_key else 'No'}")
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached price is still valid"""
        if symbol not in self.price_cache:
            return False
        
        cached_time = self.price_cache[symbol].get("timestamp", 0)
        return (time.time() - cached_time) < self.cache_ttl
    
    def _get_from_ftso(self, symbol: str) -> Optional[Tuple[float, str]]:
        """
        Try to get price from FTSO.
        
        Returns:
            (price, timestamp) or None
        """
        if not FTSO_AVAILABLE:
            return None
        
        try:
            # FTSO uses testXXX format, try both formats
            test_symbol = f"test{symbol}" if not symbol.startswith("test") else symbol
            
            price, timestamp = ftso_price.get_price_for(test_symbol)
            logger.debug(f"FTSO price for {symbol}: ${price:.4f}")
            return price, timestamp
        
        except Exception as e:
            logger.debug(f"FTSO lookup failed for {symbol}: {e}")
            return None
    
    def _get_from_coingecko(self, symbol: str) -> Optional[Tuple[float, str]]:
        """
        Get price from CoinGecko API.
        
        Returns:
            (price, timestamp) or None
        """
        try:
            # Get CoinGecko ID from config
            token_info = config.get_token_info(symbol)
            coingecko_id = token_info.get("coingecko_id")
            
            if not coingecko_id:
                logger.debug(f"No CoinGecko ID for {symbol}")
                return None
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coingecko_id,
                "vs_currencies": "usd",
                "include_last_updated_at": "true"
            }
            
            headers = {}
            if self.coingecko_api_key:
                headers["x-cg-pro-api-key"] = self.coingecko_api_key
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if coingecko_id in data:
                price = data[coingecko_id]["usd"]
                timestamp_unix = data[coingecko_id].get("last_updated_at", time.time())
                timestamp = datetime.utcfromtimestamp(timestamp_unix).isoformat() + "Z"
                
                logger.debug(f"CoinGecko price for {symbol}: ${price:.4f}")
                return price, timestamp
            
            return None
        
        except Exception as e:
            logger.debug(f"CoinGecko lookup failed for {symbol}: {e}")
            return None
    
    def _get_from_binance(self, symbol: str) -> Optional[Tuple[float, str]]:
        """
        Get price from Binance API.
        
        Returns:
            (price, timestamp) or None
        """
        try:
            # Binance uses pairs like BTCUSDT
            pair = f"{symbol}USDT"
            
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": pair}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            price = float(data["price"])
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            logger.debug(f"Binance price for {symbol}: ${price:.4f}")
            return price, timestamp
        
        except Exception as e:
            logger.debug(f"Binance lookup failed for {symbol}: {e}")
            return None
    
    def get_price(self, symbol: str, use_cache: bool = True) -> Dict[str, any]:
        """
        Get price for a cryptocurrency symbol with fallback hierarchy.
        
        Args:
            symbol: Token symbol (e.g., "BTC", "ETH")
            use_cache: Whether to use cached prices
        
        Returns:
            {
                "symbol": str,
                "price": float,
                "timestamp": str,
                "source": str,  # Which source provided the price
                "success": bool
            }
        """
        symbol = symbol.upper()
        
        # Check cache first
        if use_cache and self._is_cache_valid(symbol):
            logger.debug(f"Using cached price for {symbol}")
            return self.price_cache[symbol]
        
        # Try sources in priority order
        sources = [
            ("FTSO", self._get_from_ftso),
            ("CoinGecko", self._get_from_coingecko),
            ("Binance", self._get_from_binance),
        ]
        
        for source_name, source_func in sources:
            try:
                result = source_func(symbol)
                if result:
                    price, timestamp = result
                    
                    response = {
                        "symbol": symbol,
                        "price": price,
                        "timestamp": timestamp,
                        "source": source_name,
                        "success": True
                    }
                    
                    # Update cache
                    response["timestamp_unix"] = time.time()
                    self.price_cache[symbol] = response
                    
                    logger.info(f"✅ Price for {symbol}: ${price:.4f} (source: {source_name})")
                    return response
            
            except Exception as e:
                logger.debug(f"Error fetching from {source_name}: {e}")
                continue
        
        # All sources failed
        logger.warning(f"⚠️  Could not fetch price for {symbol} from any source")
        
        return {
            "symbol": symbol,
            "price": 0.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "none",
            "success": False,
            "error": "All price sources failed"
        }
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, Dict]:
        """
        Get prices for multiple symbols efficiently.
        
        Args:
            symbols: List of token symbols
        
        Returns:
            Dict mapping symbol -> price info
        """
        logger.info(f"Fetching prices for {len(symbols)} symbols...")
        
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_price(symbol)
            time.sleep(0.1)  # Small delay to avoid rate limits
        
        successful = sum(1 for r in results.values() if r["success"])
        logger.info(f"✅ Successfully fetched {successful}/{len(symbols)} prices")
        
        return results
    
    def get_price_with_metadata(self, symbol: str) -> Dict:
        """
        Get price along with token metadata from config.
        
        Returns:
            Combined price and metadata dict
        """
        price_info = self.get_price(symbol)
        metadata = config.get_token_info(symbol)
        
        return {
            **price_info,
            "chain": metadata.get("chain", "Unknown"),
            "coingecko_id": metadata.get("coingecko_id", ""),
        }
    
    def clear_cache(self):
        """Clear the price cache"""
        self.price_cache.clear()
        logger.info("Price cache cleared")


# Singleton instance for efficiency
_aggregator = None

def get_aggregator() -> PriceAggregator:
    """Get or create the global aggregator instance"""
    global _aggregator
    if _aggregator is None:
        _aggregator = PriceAggregator()
    return _aggregator


def get_price(symbol: str) -> Dict:
    """
    Convenience function for getting a single price.
    
    Returns price info dict with source and timestamp.
    """
    aggregator = get_aggregator()
    return aggregator.get_price(symbol)


def get_multiple_prices(symbols: list) -> Dict[str, Dict]:
    """
    Convenience function for getting multiple prices.
    """
    aggregator = get_aggregator()
    return aggregator.get_multiple_prices(symbols)


def main():
    """CLI testing interface"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Get cryptocurrency prices from multiple sources')
    parser.add_argument('--symbol', help='Single symbol to lookup (e.g., BTC)')
    parser.add_argument('--symbols', help='Comma-separated symbols (e.g., BTC,ETH,SOL)')
    parser.add_argument('--all', action='store_true', help='Get prices for all supported tokens')
    parser.add_argument('--no-cache', action='store_true', help='Bypass cache')
    
    args = parser.parse_args()
    
    if not args.symbol and not args.symbols and not args.all:
        parser.error("Provide --symbol, --symbols, or --all")
    
    aggregator = PriceAggregator()
    
    if args.symbol:
        result = aggregator.get_price(args.symbol, use_cache=not args.no_cache)
        
        print("\n" + "=" * 60)
        print("PRICE LOOKUP")
        print("=" * 60)
        
        if result["success"]:
            print(f"Symbol: {result['symbol']}")
            print(f"Price: ${result['price']:.4f}")
            print(f"Source: {result['source']}")
            print(f"Timestamp: {result['timestamp']}")
        else:
            print(f"❌ Failed to fetch price for {args.symbol}")
            if "error" in result:
                print(f"Error: {result['error']}")
        
        print("=" * 60)
    
    elif args.symbols or args.all:
        if args.all:
            symbols = list(config.SUPPORTED_TOKENS.keys())
        else:
            symbols = [s.strip().upper() for s in args.symbols.split(",")]
        
        results = aggregator.get_multiple_prices(symbols)
        
        print("\n" + "=" * 60)
        print(f"PRICE LOOKUP - {len(symbols)} SYMBOLS")
        print("=" * 60)
        
        # Sort by success then by price
        sorted_results = sorted(
            results.items(),
            key=lambda x: (not x[1]["success"], -x[1].get("price", 0))
        )
        
        for symbol, result in sorted_results:
            if result["success"]:
                print(f"{symbol:6} ${result['price']:12,.4f}  [{result['source']}]")
            else:
                print(f"{symbol:6} {'N/A':>12}  [failed]")
        
        print("=" * 60)
        
        successful = sum(1 for r in results.values() if r["success"])
        print(f"Success rate: {successful}/{len(symbols)} ({successful/len(symbols)*100:.1f}%)")
        print("=" * 60)


if __name__ == "__main__":
    main()