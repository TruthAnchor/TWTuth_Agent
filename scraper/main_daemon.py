#!/usr/bin/env python3
"""
Main Daemon - Orchestrates the complete tweet scraping and storage flow.
This is the central coordinator that ties everything together.

Flow:
1. Poll IP_Deposit contract for new tweet submissions
2. Scrape the submitted tweet
3. Analyze with AI (controversy + sentiment)
4. Store to Filecoin mainnet via Storacha
5. Store metadata on-chain to TweetDataRegistry
6. Optionally resubmit if highly controversial
"""

import os
import sys
import time
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from dotenv import load_dotenv

# Import all our modules
import config
from contract_poller import ContractPoller
from filecoin_mainnet import FilecoinMainnetStorage
from huggingface_sentiment import HuggingFaceSentimentAnalyzer
from ecosystem_classifier import EcosystemClassifier
from price_aggregator import PriceAggregator
from tweet_submitter import TweetSubmitter
from registry_interaction import TweetDataRegistry

# Import AI analysis (existing)
from ai_analysis import analyze_tweet

load_dotenv()

# Ensure log directory exists before setting up logging
Path(config.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TweetStorageDaemon:
    """
    Main daemon that coordinates tweet scraping, analysis, and storage.
    """
    
    def __init__(self):
        """Initialize all components"""
        logger.info("=" * 70)
        logger.info("INITIALIZING TWEET STORAGE DAEMON")
        logger.info("=" * 70)
        
        # Validate configuration
        is_valid, missing = config.validate_config()
        if not is_valid:
            logger.error("❌ Missing required configuration:")
            for key in missing:
                logger.error(f"   - {key}")
            raise ValueError("Configuration incomplete")
        
        # Initialize components
        logger.info("\n🔧 Initializing components...")
        
        try:
            self.poller = ContractPoller()
            logger.info("✅ Contract poller ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize poller: {e}")
            raise
        
        try:
            self.storage = FilecoinMainnetStorage()
            logger.info("✅ Filecoin storage ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize storage: {e}")
            raise
        
        try:
            self.sentiment_analyzer = HuggingFaceSentimentAnalyzer()
            logger.info("✅ Sentiment analyzer ready")
        except Exception as e:
            logger.warning(f"⚠️  Sentiment analyzer unavailable: {e}")
            self.sentiment_analyzer = None
        
        try:
            self.classifier = EcosystemClassifier()
            logger.info("✅ Ecosystem classifier ready")
        except Exception as e:
            logger.warning(f"⚠️  Ecosystem classifier unavailable: {e}")
            self.classifier = None
        
        try:
            self.price_aggregator = PriceAggregator()
            logger.info("✅ Price aggregator ready")
        except Exception as e:
            logger.warning(f"⚠️  Price aggregator unavailable: {e}")
            self.price_aggregator = None
        
        try:
            self.submitter = TweetSubmitter()
            logger.info("✅ Tweet submitter ready")
        except Exception as e:
            logger.warning(f"⚠️  Tweet submitter unavailable: {e}")
            self.submitter = None
        
        try:
            self.registry = TweetDataRegistry()
            logger.info("✅ On-chain registry ready")
        except Exception as e:
            logger.warning(f"⚠️  On-chain registry unavailable: {e}")
            self.registry = None
        
        # Ensure data directories exist
        Path(config.DATA_DIR).mkdir(parents=True, exist_ok=True)
        Path(config.TWEETS_DIR).mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "tweets_processed": 0,
            "tweets_stored": 0,
            "tweets_registered": 0,
            "tweets_resubmitted": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        # Shutdown flag
        self.shutdown_requested = False
        
        logger.info("\n✅ All components initialized successfully")
        logger.info("=" * 70)
    
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("\n⛔ Shutdown signal received")
        self.shutdown_requested = True
    
    def scrape_single_tweet(self, tweet_url: str) -> Optional[Dict]:
        """
        Scrape a single tweet using the existing scraper.
        This will use the twitter_scraper module.
        
        For now in test mode, returns mock data.
        In production, will integrate with real scraper.
        """
        logger.info(f"📱 Scraping tweet: {tweet_url}")
        
        # TODO: Integrate with actual twitter_scraper
        # from twitter_scraper import Twitter_Scraper
        # scraper = Twitter_Scraper(...)
        # result = scraper.scrape_single_tweet(tweet_url)
        
        # Mock data for now
        return {
            "url": tweet_url,
            "content": "Sample tweet content for testing",
            "user": "Test User",
            "handle": "@testuser",
            "timestamp": datetime.utcnow().isoformat(),
            "verified": False,
            "likes": "0",
            "retweets": "0",
            "replies": "0",
            "tweet_id": tweet_url.split("/")[-1],
            "ipfs_screenshot": ""
        }
    
    def analyze_tweet_content(self, tweet_data: Dict) -> Dict:
        """
        Perform comprehensive AI analysis on tweet.
        
        Returns:
            {
                "controversy_score": float,
                "sentiment": dict,
                "ecosystem": dict,
                "combined_score": float
            }
        """
        content = tweet_data.get("content", "")
        
        logger.info("🤖 Analyzing tweet content...")
        
        # Original AI analysis (deletion likelihood)
        deletion_score, analysis_text = analyze_tweet(content)
        logger.info(f"   Deletion likelihood: {deletion_score:.2%}")
        
        # Enhanced sentiment analysis
        sentiment = None
        if self.sentiment_analyzer:
            try:
                sentiment = self.sentiment_analyzer.analyze_multimodal(content)
                controversy_from_sentiment = self.sentiment_analyzer.get_controversy_score(content)
                logger.info(f"   Sentiment controversy: {controversy_from_sentiment:.2%}")
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
        
        # Ecosystem classification
        ecosystem = None
        if self.classifier:
            try:
                ecosystem = self.classifier.classify_tweet(content)
                logger.info(f"   Ecosystem: {ecosystem['token']} ({ecosystem['confidence']:.2%})")
            except Exception as e:
                logger.warning(f"Ecosystem classification failed: {e}")
        
        # Combined controversy score (weighted average)
        combined_score = deletion_score
        if sentiment:
            combined_score = (deletion_score * 0.6) + (sentiment.get("controversy_score", 0) * 0.4)
        
        return {
            "deletion_likelihood": deletion_score,
            "analysis_text": analysis_text,
            "sentiment": sentiment,
            "ecosystem": ecosystem,
            "combined_controversy": combined_score
        }
    
    def store_to_filecoin(self, tweet_data: Dict, analysis: Dict) -> Dict:
        """
        Store tweet data to Filecoin mainnet.
        
        Returns:
            Storage result with CIDs
        """
        logger.info("💾 Storing to Filecoin mainnet...")
        
        # Create a comprehensive data file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"tweet_{timestamp}.json"
        filepath = os.path.join(config.DATA_DIR, filename)
        
        # Combine tweet data and analysis
        full_data = {
            "tweet": tweet_data,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat(),
            "controversy_score": analysis["combined_controversy"]
        }
        
        # Add price data if available
        if self.price_aggregator and analysis.get("ecosystem"):
            token = analysis["ecosystem"]["token"]
            if token != "UNKNOWN":
                try:
                    price_info = self.price_aggregator.get_price(token)
                    full_data["price"] = price_info
                except Exception as e:
                    logger.warning(f"Could not fetch price: {e}")
        
        # Write to file
        import json
        with open(filepath, 'w') as f:
            json.dump(full_data, f, indent=2)
        
        logger.info(f"   Data file: {filepath}")
        
        # Store to Filecoin
        storage_result = self.storage.store_file(filepath)
        
        # Don't clean up local file - keep it for queries
        # os.remove(filepath)
        
        return storage_result
    
    def store_on_chain(self, tweet_data: Dict, analysis: Dict, storage_result: Dict, submitter: str = None) -> Optional[str]:
        """
        Store tweet metadata on-chain to TweetDataRegistry.
        
        Returns:
            Transaction hash or None
        """
        if not self.registry:
            logger.warning("⚠️  Registry not available, skipping on-chain storage")
            return None
        
        logger.info("📝 Storing metadata on-chain...")
        
        try:
            # Extract IPFS screenshot CID from URL
            ipfs_screenshot_cid = ""
            if tweet_data.get("ipfs_screenshot"):
                ipfs_screenshot_cid = tweet_data["ipfs_screenshot"].split("/")[-1]
            
            # Prepare data matching contract structure
            on_chain_data = {
                # Identity
                "tweetHash": self.registry.w3.keccak(text=tweet_data.get("url", "")).hex(),
                "tweetURL": tweet_data.get("url", ""),
                "tweetId": tweet_data.get("tweet_id", ""),
                "user": tweet_data.get("user", ""),
                "handle": tweet_data.get("handle", ""),
                "verified": tweet_data.get("verified", False),
                
                # Content
                "content": tweet_data.get("content", ""),
                
                # Metrics
                "timestamp": int(datetime.now().timestamp()),
                "likes": self._safe_int(tweet_data.get("likes", "0")),
                "retweets": self._safe_int(tweet_data.get("retweets", "0")),
                "replies": self._safe_int(tweet_data.get("replies", "0")),
                "controversyScore": int(analysis["combined_controversy"] * 100),
                "deletionLikelihood": int(analysis.get("deletion_likelihood", 0) * 100),
                
                # Storage
                "ipfsScreenshotCID": ipfs_screenshot_cid,
                "ipfsDataCID": storage_result.get("ipfs_cid", ""),
                "filecoinRootCID": storage_result.get("root_cid", ""),
                "filecoinDealId": str(storage_result.get("deal_id", "")),
                "ecosystem": analysis.get("ecosystem", {}).get("token", "UNKNOWN"),
                
                # Meta
                "submitter": submitter or "0x0000000000000000000000000000000000000000",
            }
            
            tx_hash = self.registry.store_tweet(on_chain_data)
            
            if tx_hash:
                logger.info(f"✅ Stored on-chain: {tx_hash}")
                self.stats["tweets_registered"] += 1
                return tx_hash
            else:
                logger.warning("⚠️  Tweet already registered on-chain")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to store on-chain: {e}", exc_info=True)
            return None
    
    def _safe_int(self, value) -> int:
        """Safely convert value to int"""
        try:
            if isinstance(value, str):
                # Remove commas and non-numeric chars
                value = ''.join(c for c in value if c.isdigit())
            return int(value) if value else 0
        except:
            return 0
    
    def process_tweet_event(self, event: Dict):
        """
        Process a single tweet submission event.
        
        This is the main workflow:
        1. Extract tweet URL
        2. Scrape tweet
        3. Analyze with AI
        4. Store to Filecoin
        5. Store metadata on-chain
        6. Resubmit if highly controversial
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"📬 PROCESSING NEW TWEET EVENT")
        logger.info("=" * 70)
        
        try:
            # Extract tweet URL
            tweet_url = self.poller.extract_tweet_url(event)
            if not tweet_url:
                logger.error("❌ Could not extract tweet URL from event")
                self.stats["errors"] += 1
                return
            
            logger.info(f"Tweet URL: {tweet_url}")
            logger.info(f"Depositor: {event['depositor']}")
            logger.info(f"Amount: {event['ip_amount']} wei")
            
            # Step 1: Scrape tweet
            tweet_data = self.scrape_single_tweet(tweet_url)
            if not tweet_data:
                logger.error("❌ Failed to scrape tweet")
                self.stats["errors"] += 1
                return
            
            self.stats["tweets_processed"] += 1
            
            # Step 2: AI Analysis
            analysis = self.analyze_tweet_content(tweet_data)
            controversy = analysis["combined_controversy"]
            
            logger.info(f"\n📊 ANALYSIS SUMMARY:")
            logger.info(f"   Combined Controversy: {controversy:.2%}")
            if analysis.get("sentiment"):
                logger.info(f"   Sentiment: {analysis['sentiment']['combined_label']}")
            if analysis.get("ecosystem"):
                logger.info(f"   Ecosystem: {analysis['ecosystem']['token']}")
            
            # Step 3: Store to Filecoin
            storage_result = self.store_to_filecoin(tweet_data, analysis)
            self.stats["tweets_stored"] += 1
            
            logger.info(f"\n✅ STORAGE COMPLETE:")
            logger.info(f"   IPFS CID: {storage_result['ipfs_cid']}")
            logger.info(f"   Root CID: {storage_result['root_cid']}")
            logger.info(f"   Deal ID: {storage_result.get('deal_id', 'pending')}")
            
            # Step 4: Store on-chain
            registry_tx = self.store_on_chain(
                tweet_data, 
                analysis, 
                storage_result,
                submitter=event.get('depositor')
            )
            
            if registry_tx:
                logger.info(f"\n✅ ON-CHAIN REGISTRATION:")
                logger.info(f"   TX Hash: {registry_tx}")
                logger.info(f"   Explorer: https://filfox.info/en/message/{registry_tx}")
            
            # Step 5: Resubmit if extremely controversial
            if self.submitter and controversy >= config.AUTO_SUBMIT_THRESHOLD:
                logger.info(f"\n🔄 RESUBMITTING (controversy {controversy:.2%} >= {config.AUTO_SUBMIT_THRESHOLD:.2%})")
                try:
                    tx_hash = self.submitter.submit_tweet(tweet_url, controversy)
                    logger.info(f"   Resubmission TX: {tx_hash}")
                    self.stats["tweets_resubmitted"] += 1
                except Exception as e:
                    logger.error(f"❌ Resubmission failed: {e}")
            
            logger.info("=" * 70)
        
        except Exception as e:
            logger.error(f"❌ Error processing tweet: {e}", exc_info=True)
            self.stats["errors"] += 1
    
    def print_stats(self):
        """Print daemon statistics"""
        runtime = datetime.utcnow() - self.stats["start_time"]
        
        logger.info("\n" + "=" * 70)
        logger.info("DAEMON STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Runtime: {runtime}")
        logger.info(f"Tweets processed: {self.stats['tweets_processed']}")
        logger.info(f"Tweets stored: {self.stats['tweets_stored']}")
        logger.info(f"Tweets registered on-chain: {self.stats['tweets_registered']}")
        logger.info(f"Tweets resubmitted: {self.stats['tweets_resubmitted']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 70)
    
    def run(self):
        """
        Main daemon loop.
        Polls for events and processes them continuously.
        """
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        logger.info("\n🚀 DAEMON STARTED")
        logger.info(f"Polling interval: {config.POLL_INTERVAL} seconds")
        logger.info(f"Auto-submit threshold: {config.AUTO_SUBMIT_THRESHOLD:.2%}")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while not self.shutdown_requested:
                # Poll for new events
                events = self.poller.poll_once()
                
                # Process each event
                for event in events:
                    if self.shutdown_requested:
                        break
                    
                    self.process_tweet_event(event)
                
                # Print stats periodically
                if self.stats["tweets_processed"] > 0 and self.stats["tweets_processed"] % 10 == 0:
                    self.print_stats()
                
                # Wait before next poll
                if not self.shutdown_requested:
                    time.sleep(config.POLL_INTERVAL)
        
        except KeyboardInterrupt:
            logger.info("\n⛔ Interrupted by user")
        
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
        
        finally:
            self.print_stats()
            logger.info("\n👋 Daemon stopped")


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Tweet Storage Daemon - Polls contract and stores controversial tweets'
    )
    parser.add_argument('--once', action='store_true', help='Process one cycle and exit')
    parser.add_argument('--test-event', help='Test with a mock event (tweet URL)')
    
    args = parser.parse_args()
    
    try:
        daemon = TweetStorageDaemon()
        
        if args.test_event:
            # Test mode with mock event
            logger.info("🧪 TEST MODE")
            mock_event = {
                "tweet_hash": "0x" + "00" * 32,
                "depositor": "0x0000000000000000000000000000000000000000",
                "recipient": "0x0000000000000000000000000000000000000000",
                "ip_amount": 1000000000000000,
                "validation": args.test_event,
                "timestamp": datetime.utcnow().isoformat()
            }
            daemon.process_tweet_event(mock_event)
        
        elif args.once:
            # Poll once and exit
            logger.info("🔍 SINGLE POLL MODE")
            events = daemon.poller.poll_once()
            logger.info(f"Found {len(events)} events")
            for event in events:
                daemon.process_tweet_event(event)
            daemon.print_stats()
        
        else:
            # Run continuously
            daemon.run()
    
    except Exception as e:
        logger.error(f"❌ Daemon failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()