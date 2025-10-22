#!/usr/bin/env python3
"""
Test TweetDataRegistry interaction with PROPER WAITING for transaction confirmation
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from registry_interaction import TweetDataRegistry

load_dotenv()

def wait_for_transaction(registry, tx_hash, timeout=120):
    """Wait for transaction to be mined"""
    print(f"\n⏳ Waiting for transaction to be mined...")
    print(f"   TX: {tx_hash}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            receipt = registry.w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt['status'] == 1:
                    print(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
                    return True
                else:
                    print(f"❌ Transaction failed!")
                    return False
        except:
            pass
        
        elapsed = int(time.time() - start_time)
        print(f"   Waiting... {elapsed}s", end='\r')
        time.sleep(5)
    
    print(f"\n⚠️  Timeout after {timeout}s")
    return False


def test_store_tweet():
    """Test storing a tweet to the registry"""
    print("=" * 70)
    print("TEST 1: Store Tweet to Registry")
    print("=" * 70)
    
    # Initialize registry
    registry = TweetDataRegistry()
    
    # Create mock tweet data
    mock_tweet = {
        "tweetURL": "https://x.com/elonmusk/status/1977281341264740625",
        "tweetId": "1977281341264740625",
        "user": "Elon Musk",
        "handle": "elonmusk",
        "verified": True,
        "content": "This is a test tweet about Bitcoin going to the moon! 🚀",
        "timestamp": int(datetime.now().timestamp()),
        "likes": 150,
        "retweets": 25,
        "replies": 10,
        "controversyScore": 45,  # 45%
        "deletionLikelihood": 30,  # 30%
        "ecosystem": "BTC",
        "ipfsScreenshotCID": "QmTtmUJzCqYHptdQjMxiTQWEpLB8Fv9pQuRsegCAD96wH5",
        "ipfsDataCID": "Qmez6Si8Cbodcj6d4vvJMM4e6FMMy6qKAXkNb5oGqdKxGM",
        "filecoinRootCID": "bafyTestRoot789",
        "filecoinDealId": "12345",
        "submitter": "0xa341b0F69359482862Ed4422c6057cd59560D9E4",
    }
    
    print("\n📝 Storing tweet...")
    print(f"   URL: {mock_tweet['tweetURL']}")
    print(f"   User: @{mock_tweet['handle']}")
    print(f"   Content: {mock_tweet['content'][:50]}...")
    print(f"   Ecosystem: {mock_tweet['ecosystem']}")
    print(f"   Controversy: {mock_tweet['controversyScore']}%")
    
    try:
        tx_hash = registry.store_tweet(mock_tweet)
        
        if tx_hash:
            print(f"\n📤 Transaction submitted: {tx_hash}")
            
            # CRITICAL: Wait for confirmation
            if wait_for_transaction(registry, tx_hash):
                print(f"\n✅ SUCCESS! Tweet stored on-chain")
                print(f"   Explorer: https://filfox.info/en/message/{tx_hash}")
                return True, registry
            else:
                print(f"\n❌ Transaction failed to confirm")
                return False, registry
        else:
            print("\n⚠️  Tweet already exists")
            return True, registry
    
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_query_by_url(registry):
    """Test querying tweet by URL"""
    print("\n" + "=" * 70)
    print("TEST 2: Query Tweet by URL")
    print("=" * 70)
    
    test_url = "https://x.com/elonmusk/status/1977281341264740625"
    print(f"\n🔍 Querying: {test_url}")
    
    # Add small delay to ensure blockchain state is updated
    time.sleep(2)
    
    try:
        tweet = registry.get_tweet_by_url(test_url)
        
        if tweet:
            print("\n✅ FOUND!")
            print(f"   User: @{tweet['handle']}")
            print(f"   Content: {tweet['content'][:80]}...")
            print(f"   Likes: {tweet['likes']}")
            print(f"   Ecosystem: {tweet['ecosystem']}")
            print(f"   IPFS Screenshot: {tweet['ipfsScreenshotCID']}")
            print(f"   Filecoin Root: {tweet['filecoinRootCID']}")
            return True
        else:
            print("\n❌ NOT FOUND - Transaction may not be confirmed yet")
            return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_by_cid(registry):
    """Test querying tweet by CID (reverse lookup)"""
    print("\n" + "=" * 70)
    print("TEST 3: Query Tweet by CID (Reverse Lookup)")
    print("=" * 70)
    
    test_cid = "QmTtmUJzCqYHptdQjMxiTQWEpLB8Fv9pQuRsegCAD96wH5"
    print(f"\n🔍 Querying CID: {test_cid}")
    
    try:
        tweet = registry.get_tweet_by_cid(test_cid)
        
        if tweet:
            print("\n✅ FOUND via CID reverse lookup!")
            print(f"   URL: {tweet['tweetURL']}")
            print(f"   User: @{tweet['handle']}")
            print(f"   Content: {tweet['content'][:80]}...")
            return True
        else:
            print("\n❌ NOT FOUND")
            return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_get_all_cids(registry):
    """Test getting all CIDs"""
    print("\n" + "=" * 70)
    print("TEST 4: Get All CIDs")
    print("=" * 70)
    
    print("\n📦 Fetching all CIDs...")
    
    try:
        cids = registry.get_all_cids(offset=0, limit=10)
        
        if cids:
            print(f"\n✅ Found {len(cids)} CIDs:")
            for i, cid in enumerate(cids, 1):
                print(f"   {i}. {cid}")
                print(f"      Gateway: https://gateway.pinata.cloud/ipfs/{cid}")
            return True
        else:
            print("\n⚠️  No CIDs found yet")
            return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_total_count(registry):
    """Test getting total count"""
    print("\n" + "=" * 70)
    print("TEST 5: Get Total Count")
    print("=" * 70)
    
    try:
        count = registry.get_total_count()
        print(f"\n📊 Total tweets stored: {count}")
        return count > 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_by_ecosystem(registry):
    """Test querying tweets by ecosystem"""
    print("\n" + "=" * 70)
    print("TEST 6: Query Tweets by Ecosystem")
    print("=" * 70)
    
    ecosystem = "BTC"
    print(f"\n🔍 Querying ecosystem: {ecosystem}")
    
    try:
        tweets = registry.get_tweets_by_ecosystem(ecosystem, offset=0, limit=5)
        
        if tweets:
            print(f"\n✅ Found {len(tweets)} tweets about {ecosystem}:")
            for i, tweet in enumerate(tweets, 1):
                print(f"   {i}. @{tweet['handle']}: {tweet['content'][:60]}...")
            return True
        else:
            print(f"\n⚠️  No tweets found for ecosystem {ecosystem}")
            return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all registry tests with proper waiting"""
    print("\n" + "=" * 70)
    print("🧪 TWEET DATA REGISTRY - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test 1: Store tweet (and wait for confirmation)
    success, registry = test_store_tweet()
    results.append(("Store Tweet", success))
    
    if not registry:
        print("\n❌ Cannot continue tests - registry initialization failed")
        return False
    
    # Give blockchain a moment to propagate
    print("\n⏳ Waiting 10 seconds for blockchain state to propagate...")
    time.sleep(10)
    
    # Test 2: Query by URL
    results.append(("Query by URL", test_query_by_url(registry)))
    
    # Test 3: Query by CID
    results.append(("Query by CID", test_query_by_cid(registry)))
    
    # Test 4: Get all CIDs
    results.append(("Get All CIDs", test_get_all_cids(registry)))
    
    # Test 5: Get total count
    results.append(("Get Total Count", test_get_total_count(registry)))
    
    # Test 6: Query by ecosystem
    results.append(("Query by Ecosystem", test_query_by_ecosystem(registry)))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)