#!/usr/bin/env python3
"""
TweetDataRegistry Interaction Module - COMPLETE VERSION
Store and query tweet data on Filecoin mainnet
"""

import os
import json
import logging
from typing import Dict, List, Optional
from web3 import Web3
from dotenv import load_dotenv

import config

load_dotenv()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class TweetDataRegistry:
    """Interact with TweetDataRegistry contract on Filecoin"""
    
    def __init__(self,
                 rpc_url: str = None,
                 private_key: str = None,
                 contract_address: str = None):
        """Initialize registry interaction"""
        self.rpc_url = rpc_url or config.FILECOIN_MAINNET_RPC
        self.private_key = private_key or config.FILECOIN_PRIVATE_KEY
        self.contract_address = contract_address or os.getenv("TWEET_REGISTRY_CONTRACT")
        
        if not self.contract_address:
            raise ValueError("TWEET_REGISTRY_CONTRACT not configured in .env")
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC: {self.rpc_url}")
        
        # Load account
        self.account = self.w3.eth.account.from_key(self.private_key)
        
        # Load contract
        self.contract = self._load_contract()
        
        logger.info("✅ Tweet Registry initialized")
        logger.info(f"   Contract: {self.contract_address}")
        logger.info(f"   Account: {self.account.address}")
    
    def _load_contract(self):
        """Load the TweetDataRegistry contract"""
        abi_paths = [
            "./artifacts/TweetDataRegistry.sol/TweetDataRegistry.json",
            "./TweetDataRegistry.json",
            "./abi/TweetDataRegistry.json"
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
            raise FileNotFoundError("TweetDataRegistry ABI not found")
        
        address = self.w3.to_checksum_address(self.contract_address)
        return self.w3.eth.contract(address=address, abi=abi)
    
    def store_tweet(self, tweet_data_dict: Dict) -> Optional[str]:
        """
        Store processed tweet data on-chain using nested struct format.
        
        Args:
            tweet_data_dict: Dictionary containing all tweet data
        
        Returns:
            Transaction hash or None if already exists
        """
        logger.info(f"📝 Storing tweet on-chain...")
        logger.info(f"   URL: {tweet_data_dict.get('tweetURL', 'N/A')}")
        
        # Create tweet hash
        tweet_url = tweet_data_dict['tweetURL']
        tweet_hash = self.w3.keccak(text=tweet_url)
        
        # Check if already exists
        try:
            exists = self.contract.functions.exists(tweet_hash).call()
            if exists:
                logger.warning(f"   Tweet already stored on-chain")
                return None
        except Exception as e:
            logger.debug(f"Exists check failed: {e}")
        
        # Prepare nested structs matching the contract
        identity = (
            tweet_hash,
            tweet_data_dict.get('tweetURL', ''),
            tweet_data_dict.get('tweetId', ''),
            tweet_data_dict.get('user', ''),
            tweet_data_dict.get('handle', ''),
            tweet_data_dict.get('verified', False)
        )
        
        content = tweet_data_dict.get('content', '')
        
        metrics = (
            tweet_data_dict.get('timestamp', 0),
            tweet_data_dict.get('likes', 0),
            tweet_data_dict.get('retweets', 0),
            tweet_data_dict.get('replies', 0),
            tweet_data_dict.get('controversyScore', 0),
            tweet_data_dict.get('deletionLikelihood', 0)
        )
        
        storage_data = (
            tweet_data_dict.get('ipfsScreenshotCID', ''),
            tweet_data_dict.get('ipfsDataCID', ''),
            tweet_data_dict.get('filecoinRootCID', ''),
            tweet_data_dict.get('filecoinDealId', ''),
            tweet_data_dict.get('ecosystem', 'UNKNOWN')
        )
        
        submitter = tweet_data_dict.get('submitter', self.account.address)
        
        # Build transaction with dynamic gas
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        tx_params = {
            "from": self.account.address,
            "nonce": nonce,
            "chainId": self.w3.eth.chain_id,
        }
        
        # Estimate gas
        try:
            estimated_gas = self.contract.functions.storeTweet(
                identity, content, metrics, storage_data, submitter
            ).estimate_gas(tx_params)
            gas_limit = int(estimated_gas * 1.3)
            logger.info(f"   Estimated gas: {estimated_gas:,} → Using: {gas_limit:,}")
        except Exception as e:
            gas_limit = 5_000_000
            logger.warning(f"   Could not estimate gas ({e}), using fallback: {gas_limit:,}")
        
        # Get gas price
        try:
            base_gas_price = self.w3.eth.gas_price
            gas_price = int(base_gas_price * 1.5)
            logger.info(f"   Gas price: {self.w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
        except:
            gas_price = self.w3.to_wei(50, "gwei")
        
        tx_params["gas"] = gas_limit
        tx_params["gasPrice"] = gas_price
        
        # Build and send transaction
        tx = self.contract.functions.storeTweet(
            identity, content, metrics, storage_data, submitter
        ).build_transaction(tx_params)
        
        logger.info("   Signing and sending transaction...")
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        tx_hash_hex = tx_hash.hex()
        logger.info(f"✅ Transaction sent: {tx_hash_hex}")
        logger.info(f"   Explorer: https://filfox.info/en/message/{tx_hash_hex}")
        
        return tx_hash_hex
    
    def get_tweet_by_url(self, tweet_url: str) -> Optional[Dict]:
        """Query tweet by URL"""
        try:
            result = self.contract.functions.getTweetByURL(tweet_url).call()
            return self._parse_tweet_data(result)
        except:
            return None
    
    def get_tweet_by_cid(self, cid: str) -> Optional[Dict]:
        """Query tweet by any CID (reverse lookup)"""
        try:
            result = self.contract.functions.getTweetByCID(cid).call()
            return self._parse_tweet_data(result)
        except:
            return None
    
    def get_all_cids(self, offset: int = 0, limit: int = 100) -> List[str]:
        """Get all CIDs from stored tweets"""
        logger.info(f"Fetching CIDs (offset: {offset}, limit: {limit})...")
        
        tweet_hashes = self.contract.functions.getAllTweetHashes(offset, limit).call()
        
        cids = []
        for tweet_hash in tweet_hashes:
            try:
                tweet = self.contract.functions.getTweet(tweet_hash).call()
                tweet_dict = self._parse_tweet_data(tweet)
                
                if tweet_dict['ipfsScreenshotCID']:
                    cids.append(tweet_dict['ipfsScreenshotCID'])
                if tweet_dict['ipfsDataCID']:
                    cids.append(tweet_dict['ipfsDataCID'])
                if tweet_dict['filecoinRootCID']:
                    cids.append(tweet_dict['filecoinRootCID'])
            except Exception as e:
                logger.error(f"Error fetching tweet {tweet_hash.hex()}: {e}")
        
        return cids
    
    def get_tweets_by_user(self, handle: str, offset: int = 0, limit: int = 10) -> List[Dict]:
        """Get all tweets by a user"""
        tweet_hashes = self.contract.functions.getTweetsByUser(handle, offset, limit).call()
        
        tweets = []
        for tweet_hash in tweet_hashes:
            try:
                result = self.contract.functions.getTweet(tweet_hash).call()
                tweets.append(self._parse_tweet_data(result))
            except:
                pass
        
        return tweets
    
    def get_tweets_by_ecosystem(self, ecosystem: str, offset: int = 0, limit: int = 10) -> List[Dict]:
        """Get all tweets by ecosystem"""
        tweet_hashes = self.contract.functions.getTweetsByEcosystem(ecosystem, offset, limit).call()
        
        tweets = []
        for tweet_hash in tweet_hashes:
            try:
                result = self.contract.functions.getTweet(tweet_hash).call()
                tweets.append(self._parse_tweet_data(result))
            except:
                pass
        
        return tweets
    
    def get_total_count(self) -> int:
        """Get total number of stored tweets"""
        return self.contract.functions.getTotalCount().call()
    
    def _parse_tweet_data(self, tweet_data) -> Dict:
        """Parse nested struct from contract into flat dictionary"""
        identity, content, metrics, storage_data, meta = tweet_data
        
        return {
            # Identity
            "tweetHash": identity[0].hex(),
            "tweetURL": identity[1],
            "tweetId": identity[2],
            "user": identity[3],
            "handle": identity[4],
            "verified": identity[5],
            # Content
            "content": content,
            # Metrics
            "timestamp": metrics[0],
            "likes": metrics[1],
            "retweets": metrics[2],
            "replies": metrics[3],
            "controversyScore": metrics[4],
            "deletionLikelihood": metrics[5],
            # Storage
            "ipfsScreenshotCID": storage_data[0],
            "ipfsDataCID": storage_data[1],
            "filecoinRootCID": storage_data[2],
            "filecoinDealId": storage_data[3],
            "ecosystem": storage_data[4],
            # Meta
            "submitter": meta[0],
            "processor": meta[1],
            "processedAt": meta[2],
        }


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Interact with TweetDataRegistry contract')
    parser.add_argument('command', choices=['count', 'cids', 'get-url', 'get-cid', 'user', 'ecosystem'])
    parser.add_argument('--url', help='Tweet URL')
    parser.add_argument('--cid', help='CID to lookup')
    parser.add_argument('--handle', help='User handle')
    parser.add_argument('--ecosystem', help='Ecosystem name')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=10)
    
    args = parser.parse_args()
    
    registry = TweetDataRegistry()
    
    if args.command == 'count':
        count = registry.get_total_count()
        print(f"📊 Total tweets stored: {count}")
    
    elif args.command == 'cids':
        cids = registry.get_all_cids(offset=args.offset, limit=args.limit)
        print(f"\n📦 CIDs (offset: {args.offset}, showing: {len(cids)}):")
        for cid in cids:
            print(f"   {cid}")
            print(f"   Gateway: https://gateway.pinata.cloud/ipfs/{cid}")
    
    elif args.command == 'get-url':
        if not args.url:
            print("❌ --url required")
            return
        tweet = registry.get_tweet_by_url(args.url)
        if tweet:
            print(json.dumps(tweet, indent=2))
        else:
            print("❌ Tweet not found")
    
    elif args.command == 'get-cid':
        if not args.cid:
            print("❌ --cid required")
            return
        tweet = registry.get_tweet_by_cid(args.cid)
        if tweet:
            print(json.dumps(tweet, indent=2))
        else:
            print("❌ Tweet not found")
    
    elif args.command == 'user':
        if not args.handle:
            print("❌ --handle required")
            return
        tweets = registry.get_tweets_by_user(args.handle, args.offset, args.limit)
        print(f"\n👤 Tweets by @{args.handle}: {len(tweets)}")
        for tweet in tweets:
            print(f"   {tweet['content'][:80]}...")
    
    elif args.command == 'ecosystem':
        if not args.ecosystem:
            print("❌ --ecosystem required")
            return
        tweets = registry.get_tweets_by_ecosystem(args.ecosystem, args.offset, args.limit)
        print(f"\n💎 Tweets about {args.ecosystem}: {len(tweets)}")
        for tweet in tweets:
            print(f"   {tweet['content'][:80]}...")


if __name__ == "__main__":
    main()