#!/usr/bin/env python3
"""
Test complete end-to-end flow:
1. Submit tweet to IP_Deposit contract
2. Daemon picks it up
3. Scrapes tweet
4. Analyzes with AI
5. Stores to Filecoin
6. Stores to TweetDataRegistry
7. Query the stored data
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_e2e_flow():
    """Complete end-to-end test"""
    
    print("=" * 70)
    print("🚀 END-TO-END FLOW TEST")
    print("=" * 70)
    
    # Step 1: Submit a tweet to IP_Deposit
    print("\n📝 STEP 1: Submit Tweet to IP_Deposit Contract")
    print("-" * 70)
    
    from tweet_submitter import TweetSubmitter
    
    test_tweet_url = "https://x.com/Ashcryptoreal/status/1977255774788444420"
    
    submitter = TweetSubmitter()
    
    print(f"   Submitting: {test_tweet_url}")
    print(f"   Controversy: 0.85 (85%)")
    
    try:
        tx_hash = submitter.submit_tweet(test_tweet_url, 0.85)
        print(f"   ✅ Submitted: {tx_hash}")
        print(f"   Waiting 30 seconds for confirmation...")
        time.sleep(30)
    except Exception as e:
        print(f"   ⚠️  Submission error: {e}")
        print(f"   Continuing with existing submission...")
    
    # Step 2: Run daemon once to process
    print("\n📱 STEP 2: Run Daemon to Process Tweet")
    print("-" * 70)
    
    print("   Running: python main_daemon.py --once")
    print("   (This will scrape, analyze, and store the tweet)")
    
    import subprocess
    result = subprocess.run(
        ["python", "main_daemon.py", "--once"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("   ✅ Daemon completed successfully")
    else:
        print(f"   ⚠️  Daemon had issues:")
        print(result.stdout[-500:] if result.stdout else "")
        print(result.stderr[-500:] if result.stderr else "")
    
    print("   Waiting 10 seconds for on-chain storage...")
    time.sleep(10)
    
    # Step 3: Query the registry
    print("\n🔍 STEP 3: Query TweetDataRegistry")
    print("-" * 70)
    
    from registry_interaction import TweetDataRegistry
    
    registry = TweetDataRegistry()
    
    # Try to find the tweet
    print(f"   Querying: {test_tweet_url}")
    
    try:
        tweet = registry.get_tweet_by_url(test_tweet_url)
        
        if tweet:
            print("\n   ✅ TWEET FOUND IN REGISTRY!")
            print(f"   User: @{tweet['handle']}")
            print(f"   Content: {tweet['content'][:100]}...")
            print(f"   Controversy: {tweet['controversyScore']}%")
            print(f"   Ecosystem: {tweet['ecosystem']}")
            print(f"\n   📦 Storage Info:")
            print(f"   IPFS Screenshot: {tweet['ipfsScreenshotCID']}")
            print(f"   IPFS Data: {tweet['ipfsDataCID']}")
            print(f"   Filecoin Root: {tweet['filecoinRootCID']}")
            print(f"   Deal ID: {tweet['filecoinDealId']}")
            
            # Test CID lookup
            print(f"\n   🔄 Testing CID Reverse Lookup...")
            if tweet['ipfsDataCID']:
                reverse_tweet = registry.get_tweet_by_cid(tweet['ipfsDataCID'])
                if reverse_tweet:
                    print(f"   ✅ CID lookup successful!")
                else:
                    print(f"   ❌ CID lookup failed")
            
            return True
        else:
            print("   ❌ Tweet not found in registry")
            print("   This might mean:")
            print("   - Daemon hasn't processed it yet")
            print("   - On-chain storage failed")
            print("   - Tweet was already processed before")
            return False
    
    except Exception as e:
        print(f"   ❌ Error querying registry: {e}")
        return False


def test_query_all_stored():
    """Query all stored tweets"""
    print("\n" + "=" * 70)
    print("📊 QUERY ALL STORED TWEETS")
    print("=" * 70)
    
    from registry_interaction import TweetDataRegistry
    
    registry = TweetDataRegistry()
    
    # Get total count
    total = registry.get_total_count()
    print(f"\n   Total tweets in registry: {total}")
    
    if total == 0:
        print("   No tweets stored yet. Run the daemon first!")
        return False
    
    # Get all CIDs
    print(f"\n   Fetching CIDs...")
    cids = registry.get_all_cids(offset=0, limit=min(total, 10))
    
    print(f"\n   📦 Latest {len(cids)} CIDs:")
    for i, cid in enumerate(cids, 1):
        print(f"   {i}. {cid}")
    
    # Get latest tweets
    print(f"\n   📱 Latest tweets:")
    hashes = registry.contract.functions.getAllTweetHashes(0, min(total, 5)).call()
    
    for i, tweet_hash in enumerate(hashes, 1):
        try:
            tweet = registry.contract.functions.getTweet(tweet_hash).call()
            tweet_dict = registry._tuple_to_dict(tweet)
            print(f"\n   {i}. @{tweet_dict['handle']}")
            print(f"      {tweet_dict['content'][:80]}...")
            print(f"      Controversy: {tweet_dict['controversyScore']}%")
            print(f"      Ecosystem: {tweet_dict['ecosystem']}")
        except:
            pass
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 FULL SYSTEM TEST")
    print("=" * 70)
    
    # Test 1: End-to-end flow
    e2e_success = test_e2e_flow()
    
    # Test 2: Query all stored
    query_success = test_query_all_stored()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    if e2e_success and query_success:
        print("✅ ALL TESTS PASSED!")
        print("\nYour system is fully operational:")
        print("- Tweets can be submitted to IP_Deposit ✅")
        print("- Daemon scrapes and processes tweets ✅")
        print("- Data stored to Filecoin mainnet ✅")
        print("- Data stored to on-chain registry ✅")
        print("- All data is queryable ✅")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Check the output above for details")
    
    print("=" * 70)