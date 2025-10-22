#!/usr/bin/env python3
"""
Ecosystem Classifier - Uses LLM to identify which blockchain/token tweets reference.
This is a NEW module that extends ai_coin_identifier.py without replacing it.
"""

import logging
from typing import List, Dict, Optional
import json

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

import config

load_dotenv()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class EcosystemClassifier:
    """
    LLM-based classifier for identifying blockchain ecosystems and tokens
    mentioned in tweets. Supports mainnet tokens.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the ecosystem classifier.
        
        Args:
            openai_api_key: OpenAI API key (defaults to config)
        """
        self.api_key = openai_api_key or config.OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model="gpt-4",
            temperature=0.1  # Low temperature for consistent classification
        )
        
        # Build supported tokens list from config
        self.supported_tokens = list(config.SUPPORTED_TOKENS.keys())
        
        logger.info(f"✅ Ecosystem Classifier initialized")
        logger.info(f"   Supporting {len(self.supported_tokens)} tokens")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with supported tokens"""
        tokens_str = ", ".join(self.supported_tokens)
        
        return f"""You are a cryptocurrency ecosystem classifier. Your job is to analyze tweets and identify which cryptocurrency or blockchain they primarily discuss.

SUPPORTED TOKENS: {tokens_str}

RULES:
1. Return ONLY the token symbol (e.g., "BTC", "ETH", "SOL")
2. Choose the token that is MOST prominently discussed
3. If multiple tokens mentioned equally, choose the first one
4. If no supported token is clearly mentioned, return "UNKNOWN"
5. Be case-insensitive but return uppercase symbols
6. Consider common variations (e.g., "Ethereum" → "ETH", "Bitcoin" → "BTC")
7. Look for: $SYMBOL, token names, chain names, ecosystem references

EXAMPLES:
- "Just bought more Bitcoin!" → BTC
- "$ETH to the moon 🚀" → ETH
- "Solana NFTs are amazing" → SOL
- "I love Ethereum and Polygon" → ETH (first mentioned)
- "DeFi is the future" → UNKNOWN (no specific token)

Respond with ONLY the token symbol or UNKNOWN. No explanation."""
    
    def classify_tweet(self, tweet_text: str) -> Dict[str, any]:
        """
        Classify a single tweet.
        
        Args:
            tweet_text: The tweet content to classify
        
        Returns:
            {
                "token": str,  # Token symbol or "UNKNOWN"
                "confidence": float,  # 0-1
                "ecosystem": str,  # Chain name
                "metadata": dict  # Additional info from config
            }
        """
        if not tweet_text or not tweet_text.strip():
            return {
                "token": "UNKNOWN",
                "confidence": 0.0,
                "ecosystem": "Unknown",
                "metadata": {}
            }
        
        system_prompt = self._build_system_prompt()
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Classify this tweet:\n\n{tweet_text}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            token = response.content.strip().upper()
            
            # Validate response
            if token not in self.supported_tokens and token != "UNKNOWN":
                logger.warning(f"LLM returned unsupported token: {token}, defaulting to UNKNOWN")
                token = "UNKNOWN"
            
            # Get metadata from config
            metadata = config.get_token_info(token) if token != "UNKNOWN" else {}
            
            # Calculate confidence based on token presence in text
            confidence = self._calculate_confidence(tweet_text, token)
            
            result = {
                "token": token,
                "confidence": confidence,
                "ecosystem": metadata.get("chain", "Unknown"),
                "metadata": metadata
            }
            
            logger.debug(f"Classified: {token} (confidence: {confidence:.2f})")
            
            return result
        
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {
                "token": "UNKNOWN",
                "confidence": 0.0,
                "ecosystem": "Unknown",
                "metadata": {},
                "error": str(e)
            }
    
    def _calculate_confidence(self, text: str, token: str) -> float:
        """
        Calculate confidence score based on token presence and context.
        
        Returns:
            Float between 0-1
        """
        if token == "UNKNOWN":
            return 0.0
        
        text_lower = text.lower()
        token_lower = token.lower()
        
        # Get token metadata
        metadata = config.get_token_info(token)
        chain = metadata.get("chain", "").lower()
        
        score = 0.0
        
        # Direct symbol mention ($BTC, BTC, etc.)
        if f"${token_lower}" in text_lower:
            score += 0.5
        elif token_lower in text_lower:
            score += 0.3
        
        # Chain name mention
        if chain and chain in text_lower:
            score += 0.3
        
        # Common variations
        variations = {
            "BTC": ["bitcoin", "btc"],
            "ETH": ["ethereum", "eth", "ether"],
            "SOL": ["solana", "sol"],
            "ADA": ["cardano", "ada"],
            "DOT": ["polkadot", "dot"],
            "AVAX": ["avalanche", "avax"],
            "MATIC": ["polygon", "matic"],
            "POL": ["polygon", "pol"],
        }
        
        if token in variations:
            for var in variations[token]:
                if var in text_lower:
                    score += 0.2
                    break
        
        return min(1.0, score)
    
    def classify_batch(self, tweet_texts: List[str]) -> List[Dict]:
        """
        Classify multiple tweets efficiently.
        
        Args:
            tweet_texts: List of tweet contents
        
        Returns:
            List of classification results
        """
        logger.info(f"Classifying {len(tweet_texts)} tweets...")
        results = [self.classify_tweet(text) for text in tweet_texts]
        
        # Summary statistics
        token_counts = {}
        for result in results:
            token = result["token"]
            token_counts[token] = token_counts.get(token, 0) + 1
        
        logger.info(f"Classification summary: {token_counts}")
        
        return results
    
    def group_by_ecosystem(self, tweets_with_metadata: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group tweets by their ecosystem.
        
        Args:
            tweets_with_metadata: List of dicts with 'text' and other fields
        
        Returns:
            Dict mapping token -> list of tweets
        """
        groups = {}
        
        for tweet_data in tweets_with_metadata:
            text = tweet_data.get("text", tweet_data.get("content", ""))
            
            classification = self.classify_tweet(text)
            token = classification["token"]
            
            if token not in groups:
                groups[token] = []
            
            # Add classification to tweet data
            tweet_data["classification"] = classification
            groups[token].append(tweet_data)
        
        logger.info(f"Grouped into {len(groups)} ecosystems")
        for token, tweets in groups.items():
            logger.info(f"   {token}: {len(tweets)} tweets")
        
        return groups


# Singleton instance for efficiency
_classifier = None

def get_classifier() -> EcosystemClassifier:
    """Get or create the global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = EcosystemClassifier()
    return _classifier


def classify_tweet(tweet_text: str) -> Dict:
    """
    Convenience function for classifying a single tweet.
    
    Returns classification with token, ecosystem, and confidence.
    """
    classifier = get_classifier()
    return classifier.classify_tweet(tweet_text)


def classify_batch(tweet_texts: List[str]) -> List[Dict]:
    """
    Convenience function for classifying multiple tweets.
    """
    classifier = get_classifier()
    return classifier.classify_batch(tweet_texts)


def main():
    """CLI testing interface"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Classify cryptocurrency tweets by ecosystem')
    parser.add_argument('--text', help='Single tweet to classify')
    parser.add_argument('--file', help='File with tweets (one per line)')
    parser.add_argument('--batch', action='store_true', help='Process file as batch')
    
    args = parser.parse_args()
    
    if not args.text and not args.file:
        parser.error("Provide --text or --file")
    
    # Validate config
    is_valid, missing = config.validate_config()
    if not is_valid:
        logger.error("❌ Missing required configuration:")
        for key in missing:
            logger.error(f"   - {key}")
        sys.exit(1)
    
    classifier = EcosystemClassifier()
    
    if args.text:
        result = classifier.classify_tweet(args.text)
        
        print("\n" + "=" * 60)
        print("ECOSYSTEM CLASSIFICATION")
        print("=" * 60)
        print(f"Text: {args.text}")
        print(f"\nToken: {result['token']}")
        print(f"Ecosystem: {result['ecosystem']}")
        print(f"Confidence: {result['confidence']:.2%}")
        if result.get('metadata'):
            print(f"Chain: {result['metadata'].get('chain', 'N/A')}")
        print("=" * 60)
    
    elif args.file:
        with open(args.file, 'r') as f:
            tweets = [line.strip() for line in f if line.strip()]
        
        if args.batch:
            results = classifier.classify_batch(tweets)
        else:
            results = [classifier.classify_tweet(t) for t in tweets]
        
        print("\n" + "=" * 60)
        print(f"CLASSIFIED {len(tweets)} TWEETS")
        print("=" * 60)
        
        for i, (tweet, result) in enumerate(zip(tweets, results), 1):
            print(f"\n{i}. {tweet[:60]}...")
            print(f"   → {result['token']} ({result['confidence']:.0%})")
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        token_counts = {}
        for result in results:
            token = result['token']
            token_counts[token] = token_counts.get(token, 0) + 1
        
        for token, count in sorted(token_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{token}: {count} tweets")
        
        print("=" * 60)


if __name__ == "__main__":
    main()