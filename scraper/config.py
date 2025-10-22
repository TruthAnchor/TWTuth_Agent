#!/usr/bin/env python3
"""
Centralized configuration for the tweet scraping and Filecoin storage system.
This file does NOT modify any existing functionality - it only provides new configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# FILECOIN MAINNET CONFIGURATION
# ============================================================================

FILECOIN_MAINNET_RPC = os.getenv("FILECOIN_MAINNET_RPC", "https://api.node.glif.io/rpc/v1")
FILECOIN_PRIVATE_KEY = os.getenv("FILECOIN_PRIVATE_KEY")  # For submitting tweets
FILECOIN_WALLET_ADDRESS = os.getenv("FILECOIN_WALLET_ADDRESS")

# ============================================================================
# CONTRACT ADDRESSES (YOU WILL PROVIDE AFTER DEPLOYMENT)
# ============================================================================

# Main contract where users submit tweets with fees
IP_DEPOSIT_CONTRACT = os.getenv("IP_DEPOSIT_CONTRACT", "")  # You'll deploy and provide this

# Optional: Registry contract for tracking datasets
DATASET_REGISTRY_CONTRACT = os.getenv("DATASET_REGISTRY_CONTRACT", "")

# ============================================================================
# STORACHA (W3UP) CONFIGURATION FOR MAINNET
# ============================================================================

STORACHA_SPACE_DID = os.getenv("W3UP_SPACE_DID")  # Your existing space DID
STORACHA_PROOF_PATH = os.getenv("W3UP_PROOF_PATH", "./proof.ucan")  # Path to proof file

# ============================================================================
# IPFS / PINATA CONFIGURATION (UNCHANGED)
# ============================================================================

PINATA_JWT = os.getenv("PINATA_JWT")
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_API_SECRET = os.getenv("PINATA_API_SECRET")

# ============================================================================
# AI MODEL CONFIGURATION
# ============================================================================

# OpenAI for LangChain agents (existing)
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# Hugging Face for enhanced sentiment analysis (new)
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# Model names
FINBERT_MODEL = "ProsusAI/finbert"
TWITTER_SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# ============================================================================
# CONTROVERSY THRESHOLDS
# ============================================================================

# Threshold for backend to auto-submit controversial tweets (0.0 - 1.0)
AUTO_SUBMIT_THRESHOLD = float(os.getenv("AUTO_SUBMIT_THRESHOLD", "0.75"))

# Minimum confidence score to trust AI analysis
MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.6"))

# ============================================================================
# POLLING CONFIGURATION
# ============================================================================

# How often to poll the contract for new events (seconds)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))

# Maximum number of blocks to look back on each poll
MAX_BLOCK_RANGE = int(os.getenv("MAX_BLOCK_RANGE", "1000"))

# Path to store last processed block number
LAST_BLOCK_FILE = os.getenv("LAST_BLOCK_FILE", "./data/last_block.txt")

# ============================================================================
# PRICE FEED CONFIGURATION
# ============================================================================

# CoinGecko API (free tier)
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")  # Optional, for higher rate limits

# Binance API (optional)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Existing FTSO configuration (testnet - keep for backward compatibility)
COSTON2_RPC_URL = os.getenv("COSTON2_RPC_URL")
FTSO_CONSUMER_ADDRESS = os.getenv("FTSO_CONSUMER_ADDRESS")

# ============================================================================
# SUPPORTED ECOSYSTEMS (MAINNET TOKENS)
# ============================================================================

SUPPORTED_TOKENS = {
    "BTC": {"chain": "Bitcoin", "coingecko_id": "bitcoin"},
    "ETH": {"chain": "Ethereum", "coingecko_id": "ethereum"},
    "SOL": {"chain": "Solana", "coingecko_id": "solana"},
    "ADA": {"chain": "Cardano", "coingecko_id": "cardano"},
    "DOT": {"chain": "Polkadot", "coingecko_id": "polkadot"},
    "AVAX": {"chain": "Avalanche", "coingecko_id": "avalanche-2"},
    "MATIC": {"chain": "Polygon", "coingecko_id": "matic-network"},
    "POL": {"chain": "Polygon", "coingecko_id": "matic-network"},
    "LINK": {"chain": "Ethereum", "coingecko_id": "chainlink"},
    "UNI": {"chain": "Ethereum", "coingecko_id": "uniswap"},
    "ATOM": {"chain": "Cosmos", "coingecko_id": "cosmos"},
    "XRP": {"chain": "Ripple", "coingecko_id": "ripple"},
    "DOGE": {"chain": "Dogecoin", "coingecko_id": "dogecoin"},
    "LTC": {"chain": "Litecoin", "coingecko_id": "litecoin"},
    "XLM": {"chain": "Stellar", "coingecko_id": "stellar"},
    "ALGO": {"chain": "Algorand", "coingecko_id": "algorand"},
    "FIL": {"chain": "Filecoin", "coingecko_id": "filecoin"},
    "ARB": {"chain": "Arbitrum", "coingecko_id": "arbitrum"},
    "BNB": {"chain": "BNB Chain", "coingecko_id": "binancecoin"},
    "USDC": {"chain": "Multi-chain", "coingecko_id": "usd-coin"},
    "USDT": {"chain": "Multi-chain", "coingecko_id": "tether"},
    "XDC": {"chain": "XDC Network", "coingecko_id": "xdce-crowd-sale"},
    "FLR": {"chain": "Flare", "coingecko_id": "flare-networks"},
}

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

# Directory for storing scraped data before upload
DATA_DIR = os.getenv("DATA_DIR", "./data")
TWEETS_DIR = os.getenv("TWEETS_DIR", "./tweets")
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "./artifacts")

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/daemon.log")

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_config():
    """
    Validates that all required configuration is present.
    Returns (is_valid, missing_keys)
    """
    required_keys = {
        "FILECOIN_PRIVATE_KEY": FILECOIN_PRIVATE_KEY,
        "IP_DEPOSIT_CONTRACT": IP_DEPOSIT_CONTRACT,
        "STORACHA_SPACE_DID": STORACHA_SPACE_DID,
        "PINATA_JWT": PINATA_JWT,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }
    
    missing = [k for k, v in required_keys.items() if not v]
    
    return len(missing) == 0, missing


def get_token_info(symbol: str) -> dict:
    """
    Get metadata for a token symbol.
    Returns dict with chain, coingecko_id, etc.
    """
    return SUPPORTED_TOKENS.get(symbol.upper(), {})


def is_mainnet_ready() -> bool:
    """Check if we have all mainnet configuration"""
    return bool(
        FILECOIN_MAINNET_RPC
        and FILECOIN_PRIVATE_KEY
        and IP_DEPOSIT_CONTRACT
        and STORACHA_SPACE_DID
    )


# ============================================================================
# EXPORT ALL
# ============================================================================

__all__ = [
    # Filecoin
    "FILECOIN_MAINNET_RPC",
    "FILECOIN_PRIVATE_KEY",
    "FILECOIN_WALLET_ADDRESS",
    # Contracts
    "IP_DEPOSIT_CONTRACT",
    "DATASET_REGISTRY_CONTRACT",
    # Storacha
    "STORACHA_SPACE_DID",
    "STORACHA_PROOF_PATH",
    # IPFS
    "PINATA_JWT",
    "PINATA_API_KEY",
    "PINATA_API_SECRET",
    # AI
    "OPENAI_API_KEY",
    "HUGGINGFACE_API_KEY",
    "FINBERT_MODEL",
    "TWITTER_SENTIMENT_MODEL",
    # Thresholds
    "AUTO_SUBMIT_THRESHOLD",
    "MIN_CONFIDENCE_THRESHOLD",
    # Polling
    "POLL_INTERVAL",
    "MAX_BLOCK_RANGE",
    "LAST_BLOCK_FILE",
    # Prices
    "COINGECKO_API_KEY",
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    # Legacy
    "COSTON2_RPC_URL",
    "FTSO_CONSUMER_ADDRESS",
    # Tokens
    "SUPPORTED_TOKENS",
    # Storage
    "DATA_DIR",
    "TWEETS_DIR",
    "ARTIFACTS_DIR",
    # Logging
    "LOG_LEVEL",
    "LOG_FILE",
    # Helpers
    "validate_config",
    "get_token_info",
    "is_mainnet_ready",
]


if __name__ == "__main__":
    print("Configuration Module - Validation Report")
    print("=" * 60)
    
    is_valid, missing = validate_config()
    
    if is_valid:
        print("✅ All required configuration present")
    else:
        print("❌ Missing required configuration:")
        for key in missing:
            print(f"   - {key}")
    
    print(f"\nMainnet ready: {is_mainnet_ready()}")
    print(f"Supported tokens: {len(SUPPORTED_TOKENS)}")
    print(f"Auto-submit threshold: {AUTO_SUBMIT_THRESHOLD}")