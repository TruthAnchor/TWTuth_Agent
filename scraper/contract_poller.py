#!/usr/bin/env python3
"""
Contract Poller - Monitors IP_Deposit contract for new tweet submissions.
This is a NEW module that does NOT interfere with existing scraping functionality.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from web3 import Web3
from web3.contract import Contract
from dotenv import load_dotenv

# Import our new config (doesn't touch existing code)
import config

load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ContractPoller:
    """
    Polls the IP_Deposit contract for DepositProcessed events.
    Extracts tweet information and triggers appropriate actions.
    """
    
    def __init__(self, 
                 rpc_url: str = None,
                 contract_address: str = None,
                 poll_interval: int = None,
                 start_block: int = None):
        """
        Initialize the contract poller.
        
        Args:
            rpc_url: Filecoin RPC endpoint (defaults to config)
            contract_address: IP_Deposit contract address (defaults to config)
            poll_interval: Seconds between polls (defaults to config)
            start_block: Block to start polling from (defaults to latest)
        """
        self.rpc_url = rpc_url or config.FILECOIN_MAINNET_RPC
        self.contract_address = contract_address or config.IP_DEPOSIT_CONTRACT
        self.poll_interval = poll_interval or config.POLL_INTERVAL
        
        # Validate configuration
        if not self.rpc_url:
            raise ValueError("FILECOIN_MAINNET_RPC not set in config")
        if not self.contract_address:
            raise ValueError("IP_DEPOSIT_CONTRACT not set in config")
        
        # Initialize Web3
        logger.info(f"Connecting to Filecoin RPC: {self.rpc_url}")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC: {self.rpc_url}")
        
        logger.info(f"✅ Connected to Filecoin (Chain ID: {self.w3.eth.chain_id})")
        
        # Load contract ABI
        self.contract = self._load_contract()
        
        # Block tracking
        self.last_processed_block = start_block or self._get_last_processed_block()
        logger.info(f"Starting from block: {self.last_processed_block}")
    
    def _load_contract(self) -> Contract:
        """Load the IP_Deposit contract ABI and create contract instance"""
        # Try to load from artifacts directory
        abi_paths = [
            "./artifacts/IP_Deposit.sol/IP_Deposit.json",
            "./IP_Deposit.json",
            "./abi/IP_Deposit.json"
        ]
        
        abi = None
        for path in abi_paths:
            if os.path.exists(path):
                logger.info(f"Loading ABI from: {path}")
                with open(path, 'r') as f:
                    contract_json = json.load(f)
                    abi = contract_json.get("abi", contract_json)
                break
        
        if abi is None:
            # Fallback: minimal ABI for DepositProcessed event
            logger.warning("⚠️  Using minimal fallback ABI - deploy full contract JSON for complete functionality")
            abi = [{
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "ipAmount", "type": "uint256"},
                    {"indexed": True, "name": "tweetHash", "type": "bytes32"},
                    {"indexed": True, "name": "depositor", "type": "address"},
                    {"indexed": False, "name": "recipient", "type": "address"},
                    {"indexed": False, "name": "validation", "type": "string"},
                    {"indexed": False, "name": "proof", "type": "bytes"},
                ],
                "name": "DepositProcessed",
                "type": "event"
            }]
        
        address = self.w3.to_checksum_address(self.contract_address)
        contract = self.w3.eth.contract(address=address, abi=abi)
        
        logger.info(f"✅ Contract loaded: {address}")
        return contract
    
    def _get_last_processed_block(self) -> int:
        """Get the last processed block from file, or use current block"""
        block_file = Path(config.LAST_BLOCK_FILE)
        
        if block_file.exists():
            try:
                with open(block_file, 'r') as f:
                    block = int(f.read().strip())
                    logger.info(f"Resuming from saved block: {block}")
                    return block
            except Exception as e:
                logger.warning(f"Could not read last block file: {e}")
        
        # Default to current block - 100 (to catch recent events)
        current = self.w3.eth.block_number
        start = max(0, current - 100)
        logger.info(f"Starting from block: {start} (current: {current})")
        return start
    
    def _save_last_processed_block(self, block_number: int):
        """Save the last processed block to file"""
        block_file = Path(config.LAST_BLOCK_FILE)
        block_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(block_file, 'w') as f:
            f.write(str(block_number))
    
    def get_new_events(self, from_block: int = None, to_block: int = None) -> List[Dict]:
        """
        Fetch new DepositProcessed events from the contract.
        
        Args:
            from_block: Starting block (defaults to last processed)
            to_block: Ending block (defaults to latest)
        
        Returns:
            List of event dictionaries
        """
        if from_block is None:
            from_block = self.last_processed_block + 1
        
        if to_block is None:
            to_block = self.w3.eth.block_number
        
        # Limit range to avoid RPC timeouts
        if to_block - from_block > config.MAX_BLOCK_RANGE:
            to_block = from_block + config.MAX_BLOCK_RANGE
        
        if from_block > to_block:
            return []
        
        logger.debug(f"Fetching events from block {from_block} to {to_block}")
        
        try:
            # Use get_logs instead of create_filter (Filecoin mainnet doesn't support filters)
            # This is the proper way to query events on Filecoin
            events = self.contract.events.DepositProcessed.get_logs(
                from_block=from_block,
                to_block=to_block
            )
            
            if events:
                logger.info(f"📬 Found {len(events)} new deposit event(s)")
            
            return [self._parse_event(e) for e in events]
        
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []
    
    def _parse_event(self, event) -> Dict:
        """Parse a DepositProcessed event into a clean dictionary"""
        args = event['args']
        
        # Decode tweetHash to tweet URL if it's a keccak256 hash
        tweet_hash = args['tweetHash'].hex()
        
        parsed = {
            'block_number': event['blockNumber'],
            'transaction_hash': event['transactionHash'].hex(),
            'tweet_hash': tweet_hash,
            'depositor': args['depositor'],
            'recipient': args['recipient'],
            'ip_amount': args['ipAmount'],
            'validation': args.get('validation', ''),
            'proof': args.get('proof', b'').hex() if args.get('proof') else '',
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Try to extract more fields if available in ABI
        optional_fields = [
            'collectionAddress', 'collectionConfig', 'licenseTermsConfig',
            'licenseMintParams', 'coCreators'
        ]
        
        for field in optional_fields:
            if field in args:
                parsed[field] = args[field]
        
        return parsed
    
    def extract_tweet_url(self, event: Dict) -> Optional[str]:
        """
        Extract tweet URL from event data.
        The validation field should contain the tweet URL.
        """
        validation = event.get('validation', '')
        
        # Check if validation contains a tweet URL
        if 'twitter.com' in validation or 'x.com' in validation:
            return validation.strip()
        
        # Could also try to reconstruct from proof or other fields
        logger.warning(f"Could not extract tweet URL from event: {event['tweet_hash']}")
        return None
    
    def poll_once(self) -> List[Dict]:
        """
        Perform one polling cycle.
        Returns list of new events found.
        """
        try:
            current_block = self.w3.eth.block_number
            events = self.get_new_events(to_block=current_block)
            
            if events:
                # Update last processed block
                self.last_processed_block = current_block
                self._save_last_processed_block(current_block)
                
                logger.info(f"✅ Processed up to block {current_block}")
            
            return events
        
        except Exception as e:
            logger.error(f"Error in poll cycle: {e}", exc_info=True)
            return []
    
    def poll_forever(self, callback=None):
        """
        Poll continuously until interrupted.
        
        Args:
            callback: Function to call with each new event: callback(event_dict)
        """
        logger.info(f"🔄 Starting continuous polling (interval: {self.poll_interval}s)")
        logger.info(f"Monitoring contract: {self.contract_address}")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                events = self.poll_once()
                
                if events and callback:
                    for event in events:
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"Error in event callback: {e}", exc_info=True)
                
                # Wait before next poll
                time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            logger.info("\n⛔ Polling stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in polling loop: {e}", exc_info=True)
            raise


def example_callback(event: Dict):
    """Example callback function for processing events"""
    logger.info(f"🆕 New tweet deposit:")
    logger.info(f"   Tweet Hash: {event['tweet_hash']}")
    logger.info(f"   Depositor: {event['depositor']}")
    logger.info(f"   Amount: {event['ip_amount']} wei")
    logger.info(f"   TX: {event['transaction_hash']}")
    
    tweet_url = event.get('validation', '')
    if tweet_url:
        logger.info(f"   Tweet URL: {tweet_url}")
        # This is where you'd trigger the scraper
        # scraper.scrape_single_tweet(tweet_url)


def main():
    """CLI entry point for testing the poller"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Poll IP_Deposit contract for new tweets')
    parser.add_argument('--start-block', type=int, help='Block to start from')
    parser.add_argument('--interval', type=int, help='Polling interval in seconds')
    parser.add_argument('--once', action='store_true', help='Poll once and exit')
    
    args = parser.parse_args()
    
    # Validate configuration
    is_valid, missing = config.validate_config()
    if not is_valid:
        logger.error("❌ Missing required configuration:")
        for key in missing:
            logger.error(f"   - {key}")
        sys.exit(1)
    
    # Initialize poller
    try:
        poller = ContractPoller(
            start_block=args.start_block,
            poll_interval=args.interval
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize poller: {e}")
        sys.exit(1)
    
    # Run
    if args.once:
        events = poller.poll_once()
        logger.info(f"Found {len(events)} events")
        for event in events:
            example_callback(event)
    else:
        poller.poll_forever(callback=example_callback)


if __name__ == "__main__":
    main()