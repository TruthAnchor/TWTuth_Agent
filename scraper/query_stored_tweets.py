#!/usr/bin/env python3
"""
Query and retrieve stored tweets from various sources:
1. Local data/ directory (JSON files)
2. IPFS via Pinata gateway
3. Storacha (w3up) storage
4. Contract events (what was submitted)
"""

import os
import sys
import json
import glob
from datetime import datetime
from typing import List, Dict, Optional
import requests
from pathlib import Path

from dotenv import load_dotenv
import config
from contract_poller import ContractPoller

load_dotenv()


class StoredTweetQuery:
    """Query and retrieve stored tweet data from multiple sources"""
    
    def __init__(self):
        self.data_dir = Path(config.DATA_DIR)
        self.pinata_jwt = config.PINATA_JWT
    
    def list_local_tweets(self, limit: int = None) -> List[Dict]:
        """
        List all tweets stored locally in data/ directory.
        
        Returns:
            List of tweet metadata dicts sorted by timestamp (newest first)
        """
        json_files = glob.glob(str(self.data_dir / "tweet_*.json"))
        
        tweets = []
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    data['local_file'] = file_path
                    tweets.append(data)
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
        
        # Sort by timestamp (newest first)
        tweets.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        if limit:
            tweets = tweets[:limit]
        
        return tweets
    
    def get_tweet_by_cid(self, cid: str) -> Optional[Dict]:
        """
        Retrieve tweet data from IPFS using CID.
        
        Args:
            cid: IPFS CID (root_cid or ipfs_cid)
        
        Returns:
            Tweet data dict or None
        """
        gateways = [
            f"https://gateway.pinata.cloud/ipfs/{cid}",
            f"https://{cid}.ipfs.w3s.link",
            f"https://ipfs.io/ipfs/{cid}",
        ]
        
        for gateway in gateways:
            try:
                print(f"📡 Trying gateway: {gateway}")
                response = requests.get(gateway, timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"   Failed: {e}")
                continue
        
        print(f"❌ Could not retrieve CID: {cid}")
        return None
    
    def list_pinata_pins(self, limit: int = 10) -> List[Dict]:
        """
        List files pinned to Pinata.
        
        Returns:
            List of pinned files with metadata
        """
        if not self.pinata_jwt:
            print("❌ PINATA_JWT not configured")
            return []
        
        url = "https://api.pinata.cloud/data/pinList"
        headers = {"Authorization": f"Bearer {self.pinata_jwt}"}
        params = {
            "status": "pinned",
            "pageLimit": limit,
            "includeCount": True
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("rows", [])
        
        except Exception as e:
            print(f"❌ Error listing Pinata pins: {e}")
            return []
    
    def list_contract_submissions(self, limit: int = 100) -> List[Dict]:
        """
        Query contract events to see what tweets were submitted.
        
        Returns:
            List of submission events
        """
        try:
            poller = ContractPoller()
            
            # Get recent blocks
            current_block = poller.w3.eth.block_number
            from_block = max(0, current_block - limit * 10)  # Approximate
            
            events = poller.get_new_events(from_block=from_block, to_block=current_block)
            
            return events
        
        except Exception as e:
            print(f"❌ Error querying contract: {e}")
            return []
    
    def search_by_content(self, keyword: str) -> List[Dict]:
        """
        Search local tweets by content keyword.
        
        Args:
            keyword: Search term
        
        Returns:
            Matching tweets
        """
        all_tweets = self.list_local_tweets()
        keyword_lower = keyword.lower()
        
        matches = []
        for tweet in all_tweets:
            tweet_content = tweet.get('tweet', {}).get('content', '').lower()
            if keyword_lower in tweet_content:
                matches.append(tweet)
        
        return matches
    
    def search_by_user(self, username: str) -> List[Dict]:
        """
        Search local tweets by username.
        
        Args:
            username: Twitter username (with or without @)
        
        Returns:
            Matching tweets
        """
        all_tweets = self.list_local_tweets()
        username = username.lstrip('@').lower()
        
        matches = []
        for tweet in all_tweets:
            tweet_user = tweet.get('tweet', {}).get('user', '').lower()
            tweet_handle = tweet.get('tweet', {}).get('handle', '').lower().lstrip('@')
            
            if username in tweet_user or username in tweet_handle:
                matches.append(tweet)
        
        return matches
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about stored tweets.
        
        Returns:
            Stats dict
        """
        tweets = self.list_local_tweets()
        
        if not tweets:
            return {
                "total_tweets": 0,
                "total_size_bytes": 0,
            }
        
        total_size = sum(
            os.path.getsize(t['local_file']) 
            for t in tweets 
            if 'local_file' in t
        )
        
        ecosystems = {}
        for tweet in tweets:
            ecosystem = tweet.get('analysis', {}).get('ecosystem', {}).get('token', 'UNKNOWN')
            ecosystems[ecosystem] = ecosystems.get(ecosystem, 0) + 1
        
        avg_controversy = sum(
            tweet.get('controversy_score', 0) 
            for tweet in tweets
        ) / len(tweets) if tweets else 0
        
        return {
            "total_tweets": len(tweets),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "ecosystems": ecosystems,
            "average_controversy": round(avg_controversy, 3),
            "oldest": tweets[-1].get('timestamp') if tweets else None,
            "newest": tweets[0].get('timestamp') if tweets else None,
        }
    
    def export_to_csv(self, output_file: str = "stored_tweets_export.csv"):
        """
        Export all stored tweets to CSV.
        
        Args:
            output_file: Output CSV filename
        """
        import csv
        
        tweets = self.list_local_tweets()
        
        if not tweets:
            print("❌ No tweets to export")
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'timestamp',
                'url',
                'user',
                'handle',
                'content',
                'controversy_score',
                'ecosystem',
                'ipfs_cid',
                'root_cid',
                'deal_id',
                'ipfs_gateway_url',
                'storacha_url'
            ])
            
            # Rows
            for tweet in tweets:
                tweet_data = tweet.get('tweet', {})
                analysis = tweet.get('analysis', {})
                
                writer.writerow([
                    tweet.get('timestamp', ''),
                    tweet_data.get('url', ''),
                    tweet_data.get('user', ''),
                    tweet_data.get('handle', ''),
                    tweet_data.get('content', '')[:200],  # Truncate long content
                    tweet.get('controversy_score', 0),
                    analysis.get('ecosystem', {}).get('token', 'UNKNOWN'),
                    # These come from Filecoin storage result
                    tweet.get('ipfs_cid', ''),
                    tweet.get('root_cid', ''),
                    tweet.get('deal_id', ''),
                    tweet.get('ipfs_gateway_url', ''),
                    tweet.get('storacha_url', ''),
                ])
        
        print(f"✅ Exported {len(tweets)} tweets to {output_file}")


def main():
    """CLI interface for querying stored tweets"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Query and retrieve stored tweets from IPFS/Filecoin'
    )
    
    parser.add_argument(
        'command',
        choices=['list', 'get', 'search', 'stats', 'export', 'pinata', 'contract'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--cid',
        help='IPFS CID to retrieve (for "get" command)'
    )
    
    parser.add_argument(
        '--keyword',
        help='Keyword to search for (for "search" command)'
    )
    
    parser.add_argument(
        '--user',
        help='Username to search for (for "search" command)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Limit number of results'
    )
    
    parser.add_argument(
        '--output',
        default='stored_tweets_export.csv',
        help='Output file for export command'
    )
    
    args = parser.parse_args()
    
    query = StoredTweetQuery()
    
    if args.command == 'list':
        print(f"\n📋 LOCAL STORED TWEETS (limit: {args.limit})")
        print("=" * 80)
        
        tweets = query.list_local_tweets(limit=args.limit)
        
        if not tweets:
            print("No tweets found locally")
        else:
            for i, tweet in enumerate(tweets, 1):
                tweet_data = tweet.get('tweet', {})
                print(f"\n{i}. {tweet.get('timestamp', 'Unknown time')}")
                print(f"   User: {tweet_data.get('user', 'Unknown')}")
                print(f"   Content: {tweet_data.get('content', '')[:100]}...")
                print(f"   Controversy: {tweet.get('controversy_score', 0):.2%}")
                print(f"   IPFS: {tweet.get('ipfs_cid', 'N/A')}")
                print(f"   Root CID: {tweet.get('root_cid', 'N/A')}")
    
    elif args.command == 'get':
        if not args.cid:
            print("❌ --cid required for 'get' command")
            sys.exit(1)
        
        print(f"\n📡 RETRIEVING FROM IPFS: {args.cid}")
        print("=" * 80)
        
        data = query.get_tweet_by_cid(args.cid)
        
        if data:
            print("\n✅ Retrieved successfully!")
            print(json.dumps(data, indent=2))
        else:
            print("\n❌ Failed to retrieve")
    
    elif args.command == 'search':
        if args.keyword:
            print(f"\n🔍 SEARCHING FOR: {args.keyword}")
            print("=" * 80)
            matches = query.search_by_content(args.keyword)
        elif args.user:
            print(f"\n🔍 SEARCHING FOR USER: @{args.user}")
            print("=" * 80)
            matches = query.search_by_user(args.user)
        else:
            print("❌ --keyword or --user required for 'search' command")
            sys.exit(1)
        
        if matches:
            print(f"\nFound {len(matches)} matches:\n")
            for i, tweet in enumerate(matches[:args.limit], 1):
                tweet_data = tweet.get('tweet', {})
                print(f"{i}. @{tweet_data.get('handle', 'unknown')}: {tweet_data.get('content', '')[:80]}...")
        else:
            print("No matches found")
    
    elif args.command == 'stats':
        print("\n📊 STATISTICS")
        print("=" * 80)
        
        stats = query.get_statistics()
        
        print(f"Total Tweets: {stats['total_tweets']}")
        print(f"Total Size: {stats['total_size_mb']} MB")
        print(f"Average Controversy: {stats['average_controversy']:.2%}")
        print(f"\nEcosystems:")
        for token, count in stats.get('ecosystems', {}).items():
            print(f"  {token}: {count} tweets")
        print(f"\nDate Range:")
        print(f"  Oldest: {stats.get('oldest', 'N/A')}")
        print(f"  Newest: {stats.get('newest', 'N/A')}")
    
    elif args.command == 'export':
        print(f"\n💾 EXPORTING TO CSV")
        print("=" * 80)
        query.export_to_csv(args.output)
    
    elif args.command == 'pinata':
        print(f"\n📌 PINATA PINS (limit: {args.limit})")
        print("=" * 80)
        
        pins = query.list_pinata_pins(limit=args.limit)
        
        if pins:
            for i, pin in enumerate(pins, 1):
                print(f"\n{i}. CID: {pin['ipfs_pin_hash']}")
                print(f"   Size: {pin['size']} bytes")
                print(f"   Date: {pin['date_pinned']}")
                if pin.get('metadata', {}).get('name'):
                    print(f"   Name: {pin['metadata']['name']}")
        else:
            print("No pins found")
    
    elif args.command == 'contract':
        print(f"\n📜 CONTRACT SUBMISSIONS (recent {args.limit} blocks)")
        print("=" * 80)
        
        events = query.list_contract_submissions(limit=args.limit)
        
        if events:
            for i, event in enumerate(events, 1):
                print(f"\n{i}. Block: {event['block_number']}")
                print(f"   Depositor: {event['depositor']}")
                print(f"   Tweet URL: {event.get('validation', 'N/A')}")
                print(f"   TX: {event['transaction_hash']}")
        else:
            print("No submissions found")


if __name__ == "__main__":
    main()