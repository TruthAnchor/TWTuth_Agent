#!/usr/bin/env python3
"""
Enhanced sentiment analysis using Hugging Face models.
This is a NEW module that complements existing AI analysis without replacing it.
"""

import logging
from typing import Dict, List, Tuple, Optional
import warnings

# Import config
import config

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class HuggingFaceSentimentAnalyzer:
    """
    Multi-model sentiment analysis using Hugging Face transformers.
    Combines financial sentiment (FinBERT) with general Twitter sentiment.
    """
    
    def __init__(self, use_api: bool = False):
        """
        Initialize sentiment analyzer.
        
        Args:
            use_api: If True, use HF API. If False, load models locally.
        """
        self.use_api = use_api or bool(config.HUGGINGFACE_API_KEY)
        
        if self.use_api:
            logger.info("Using Hugging Face API for sentiment analysis")
            self._init_api()
        else:
            logger.info("Loading local Hugging Face models...")
            self._init_local()
    
    def _init_api(self):
        """Initialize API-based inference"""
        import requests
        self.api_key = config.HUGGINGFACE_API_KEY
        
        if not self.api_key:
            logger.warning("⚠️  HUGGINGFACE_API_KEY not set - falling back to local models")
            self.use_api = False
            self._init_local()
            return
        
        self.api_url_finbert = f"https://api-inference.huggingface.co/models/{config.FINBERT_MODEL}"
        self.api_url_twitter = f"https://api-inference.huggingface.co/models/{config.TWITTER_SENTIMENT_MODEL}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        logger.info(f"✅ API initialized")
    
    def _init_local(self):
        """Initialize local model loading"""
        try:
            from transformers import pipeline
            
            logger.info(f"Loading FinBERT: {config.FINBERT_MODEL}")
            self.finbert = pipeline(
                "sentiment-analysis",
                model=config.FINBERT_MODEL,
                device=-1  # CPU
            )
            
            logger.info(f"Loading Twitter sentiment: {config.TWITTER_SENTIMENT_MODEL}")
            self.twitter_sentiment = pipeline(
                "sentiment-analysis",
                model=config.TWITTER_SENTIMENT_MODEL,
                device=-1  # CPU
            )
            
            logger.info("✅ Local models loaded")
        
        except ImportError:
            logger.error("❌ transformers not installed. Install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise
    
    def _query_api(self, url: str, text: str) -> Dict:
        """Query Hugging Face API"""
        import requests
        
        response = requests.post(
            url,
            headers=self.headers,
            json={"inputs": text}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
    
    def analyze_financial_sentiment(self, text: str) -> Dict:
        """
        Analyze financial sentiment using FinBERT.
        
        Returns:
            {
                "label": "positive" | "negative" | "neutral",
                "score": float,
                "all_scores": {...}
            }
        """
        try:
            if self.use_api:
                result = self._query_api(self.api_url_finbert, text)
                if result and isinstance(result, list):
                    result = result[0]
            else:
                result = self.finbert(text[:512])[0]  # Truncate to model max length
            
            return {
                "label": result["label"].lower(),
                "score": result["score"],
                "model": "finbert"
            }
        
        except Exception as e:
            logger.error(f"Financial sentiment analysis failed: {e}")
            return {"label": "neutral", "score": 0.5, "model": "finbert", "error": str(e)}
    
    def analyze_twitter_sentiment(self, text: str) -> Dict:
        """
        Analyze general Twitter sentiment using RoBERTa.
        
        Returns:
            {
                "label": "positive" | "negative" | "neutral",
                "score": float
            }
        """
        try:
            if self.use_api:
                result = self._query_api(self.api_url_twitter, text)
                if result and isinstance(result, list):
                    result = result[0]
            else:
                result = self.twitter_sentiment(text[:512])[0]
            
            # Normalize label names
            label = result["label"].lower()
            if "pos" in label:
                label = "positive"
            elif "neg" in label:
                label = "negative"
            else:
                label = "neutral"
            
            return {
                "label": label,
                "score": result["score"],
                "model": "twitter-roberta"
            }
        
        except Exception as e:
            logger.error(f"Twitter sentiment analysis failed: {e}")
            return {"label": "neutral", "score": 0.5, "model": "twitter-roberta", "error": str(e)}
    
    def analyze_multimodal(self, text: str) -> Dict:
        """
        Combine both models for comprehensive sentiment analysis.
        
        Returns:
            {
                "financial": {...},
                "twitter": {...},
                "combined_label": "positive" | "negative" | "neutral",
                "combined_score": float,
                "confidence": float
            }
        """
        financial = self.analyze_financial_sentiment(text)
        twitter = self.analyze_twitter_sentiment(text)
        
        # Sentiment to numeric mapping
        sentiment_map = {
            "positive": 1.0,
            "neutral": 0.0,
            "negative": -1.0
        }
        
        # Calculate weighted average
        fin_value = sentiment_map[financial["label"]] * financial["score"]
        twt_value = sentiment_map[twitter["label"]] * twitter["score"]
        
        # Weight financial sentiment slightly higher for crypto content
        combined_value = (fin_value * 0.6) + (twt_value * 0.4)
        
        # Determine combined label
        if combined_value > 0.2:
            combined_label = "positive"
        elif combined_value < -0.2:
            combined_label = "negative"
        else:
            combined_label = "neutral"
        
        # Calculate confidence (agreement between models)
        agreement = 1.0 if financial["label"] == twitter["label"] else 0.5
        avg_confidence = (financial["score"] + twitter["score"]) / 2
        confidence = agreement * avg_confidence
        
        return {
            "financial": financial,
            "twitter": twitter,
            "combined_label": combined_label,
            "combined_score": (combined_value + 1) / 2,  # Normalize to 0-1
            "confidence": confidence,
            "text_length": len(text)
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts efficiently"""
        return [self.analyze_multimodal(text) for text in texts]
    
    def get_controversy_score(self, text: str) -> float:
        """
        Estimate controversy based on sentiment extremity.
        Controversial = strong sentiment + low confidence OR mixed signals.
        
        Returns:
            Float between 0-1 (higher = more controversial)
        """
        analysis = self.analyze_multimodal(text)
        
        # Factors that indicate controversy:
        # 1. Strong sentiment (very positive or very negative)
        # 2. Disagreement between models
        # 3. High-confidence extreme sentiment
        
        sentiment_extremity = abs(analysis["combined_score"] - 0.5) * 2  # 0-1
        disagreement = 1.0 - analysis["confidence"]  # Higher when models disagree
        
        # Keywords that often appear in controversial content
        controversy_keywords = [
            "scam", "fraud", "rug", "dump", "crash", "moon", "lambos",
            "ponzi", "shitcoin", "pump", "fud", "manipulation", "insider"
        ]
        
        text_lower = text.lower()
        keyword_score = sum(1 for kw in controversy_keywords if kw in text_lower) / len(controversy_keywords)
        
        # Combine factors
        controversy = (
            sentiment_extremity * 0.4 +
            disagreement * 0.3 +
            keyword_score * 0.3
        )
        
        return min(1.0, controversy)


# Singleton instance for efficiency
_analyzer = None

def get_analyzer() -> HuggingFaceSentimentAnalyzer:
    """Get or create the global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = HuggingFaceSentimentAnalyzer()
    return _analyzer


def analyze_tweet_sentiment(text: str) -> Dict:
    """
    Convenience function for analyzing a single tweet.
    
    Returns complete sentiment analysis with controversy score.
    """
    analyzer = get_analyzer()
    analysis = analyzer.analyze_multimodal(text)
    analysis["controversy_score"] = analyzer.get_controversy_score(text)
    return analysis


def main():
    """CLI testing interface"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Analyze tweet sentiment')
    parser.add_argument('--text', help='Text to analyze')
    parser.add_argument('--file', help='File with tweets (one per line)')
    parser.add_argument('--api', action='store_true', help='Use HF API instead of local models')
    
    args = parser.parse_args()
    
    if not args.text and not args.file:
        parser.error("Provide --text or --file")
    
    analyzer = HuggingFaceSentimentAnalyzer(use_api=args.api)
    
    if args.text:
        result = analyzer.analyze_multimodal(args.text)
        controversy = analyzer.get_controversy_score(args.text)
        
        print("\n" + "=" * 60)
        print("SENTIMENT ANALYSIS")
        print("=" * 60)
        print(f"Text: {args.text[:100]}...")
        print(f"\nFinancial: {result['financial']['label']} ({result['financial']['score']:.3f})")
        print(f"Twitter: {result['twitter']['label']} ({result['twitter']['score']:.3f})")
        print(f"\nCombined: {result['combined_label']} ({result['combined_score']:.3f})")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Controversy: {controversy:.3f}")
        print("=" * 60)
    
    elif args.file:
        with open(args.file, 'r') as f:
            texts = [line.strip() for line in f if line.strip()]
        
        print(f"\nAnalyzing {len(texts)} tweets...")
        results = analyzer.analyze_batch(texts)
        
        print("\n" + "=" * 60)
        print("BATCH RESULTS")
        print("=" * 60)
        
        for i, (text, result) in enumerate(zip(texts, results), 1):
            controversy = analyzer.get_controversy_score(text)
            print(f"\n{i}. {text[:50]}...")
            print(f"   Sentiment: {result['combined_label']} ({result['combined_score']:.2f})")
            print(f"   Controversy: {controversy:.2f}")
        
        print("=" * 60)


if __name__ == "__main__":
    main()