#!/usr/bin/env python3
"""
Tweet Submitter - Backend submits high-controversy tweets to IP_Deposit contract.
This is a NEW module for the backend to trigger storage of controversial tweets.
"""

import os
import sys
import json
import logging
from typing import Dict, Optional
from datetime import datetime

from web3 import Web3
from dotenv import load_dotenv

import config

load_dotenv()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class TweetSubmitter:
    """
    Submits high-controversy tweets to the IP_Deposit contract
    so they can be picked up by the polling daemon and stored to Filecoin.
    """
    
    def __init__(self,
                 rpc_url: str = None,
                 private_key: str = None,
                 contract_address: str = None,
                 submission_fee_wei: int = 0):
        """
        Initialize tweet submitter.
        
        Args:
            rpc_url: Filecoin RPC endpoint
            private_key: Private key for signing transactions
            contract_address: IP_Deposit contract address
            submission_fee_wei: Amount to send with each submission (in wei)
        """
        self.rpc_url = rpc_url or config.FILECOIN_MAINNET_RPC
        self.private_key = private_key or config.FILECOIN_PRIVATE_KEY
        self.contract_address = contract_address or config.IP_DEPOSIT_CONTRACT
        self.submission_fee = submission_fee_wei or 1000000000000000  # 0.001 FIL default
        
        if not self.rpc_url:
            raise ValueError("FILECOIN_MAINNET_RPC not configured")
        if not self.private_key:
            raise ValueError("FILECOIN_PRIVATE_KEY not configured")
        if not self.contract_address:
            raise ValueError("IP_DEPOSIT_CONTRACT not configured")
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC: {self.rpc_url}")
        
        # Load account
        self.account = self.w3.eth.account.from_key(self.private_key)
        
        # Load contract
        self.contract = self._load_contract()
        
        logger.info("✅ Tweet Submitter initialized")
        logger.info(f"   RPC: {self.rpc_url}")
        logger.info(f"   Account: {self.account.address}")
        logger.info(f"   Contract: {self.contract_address}")
        logger.info(f"   Submission fee: {self.submission_fee} wei")
    
    def _load_contract(self):
        """Load the IP_Deposit contract"""
        # Try to load ABI
        abi_paths = [
            "./artifacts/IP_Deposit.sol/IP_Deposit.json",
            "./IP_Deposit.json",
            "./abi/IP_Deposit.json"
        ]
        
        abi = None
        for path in abi_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    contract_json = json.load(f)
                    abi = contract_json.get("abi", contract_json)
                break
        
        if abi is None:
            # Minimal ABI for depositIP function
            logger.warning("⚠️  Using minimal ABI - deploy full contract JSON for complete functionality")
            abi = [{
                "inputs": [
                    {"name": "recipient", "type": "address"},
                    {"name": "validation", "type": "string"},
                    {"name": "proof", "type": "bytes"},
                    {"name": "collectionAddress", "type": "address"},
                    {"name": "collectionConfig", "type": "tuple", "components": [
                        {"name": "handle", "type": "string"},
                        {"name": "mintPrice", "type": "uint256"},
                        {"name": "maxSupply", "type": "uint256"},
                        {"name": "royaltyReceiver", "type": "address"},
                        {"name": "royaltyBP", "type": "uint96"}
                    ]},
                    {"name": "tweetHash", "type": "bytes32"},
                    {"name": "licenseTermsConfig", "type": "tuple", "components": [
                        {"name": "defaultMintingFee", "type": "uint256"},
                        {"name": "currency", "type": "address"},
                        {"name": "royaltyPolicy", "type": "address"},
                        {"name": "transferable", "type": "bool"},
                        {"name": "expiration", "type": "uint256"},
                        {"name": "commercialUse", "type": "bool"},
                        {"name": "commercialAttribution", "type": "bool"},
                        {"name": "commercialRevShare", "type": "uint256"},
                        {"name": "commercialRevCeiling", "type": "uint256"},
                        {"name": "derivativesAllowed", "type": "bool"},
                        {"name": "derivativesAttribution", "type": "bool"},
                        {"name": "derivativesApproval", "type": "bool"},
                        {"name": "derivativesReciprocal", "type": "bool"},
                        {"name": "derivativeRevCeiling", "type": "uint256"},
                        {"name": "uri", "type": "string"}
                    ]},
                    {"name": "licenseMintParams", "type": "tuple", "components": [
                        {"name": "licenseTermsId", "type": "uint256"},
                        {"name": "licensorIpId", "type": "address"},
                        {"name": "receiver", "type": "address"},
                        {"name": "amount", "type": "uint256"},
                        {"name": "maxMintingFee", "type": "uint256"},
                        {"name": "maxRevenueShare", "type": "uint256"}
                    ]},
                    {"name": "coCreators", "type": "tuple[]", "components": [
                        {"name": "name", "type": "string"},
                        {"name": "wallet", "type": "address"}
                    ]}
                ],
                "name": "depositIP",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }]
        
        address = self.w3.to_checksum_address(self.contract_address)
        return self.w3.eth.contract(address=address, abi=abi)
    
    def submit_tweet(self,
                     tweet_url: str,
                     controversy_score: float,
                     metadata: Optional[Dict] = None) -> str:
        """
        Submit a tweet to the contract for storage.
        
        Args:
            tweet_url: Full URL to the tweet
            controversy_score: AI-calculated controversy score (0-1)
            metadata: Optional additional metadata
        
        Returns:
            Transaction hash
        """
        logger.info(f"📝 Submitting tweet to contract...")
        logger.info(f"   URL: {tweet_url}")
        logger.info(f"   Controversy: {controversy_score:.2%}")
        
        # Create tweet hash (keccak256 of URL)
        tweet_hash = self.w3.keccak(text=tweet_url)
        
        # Build transaction parameters
        recipient = self.account.address  # Backend is recipient
        validation = tweet_url  # Store URL in validation field
        proof = bytes()  # Empty proof for now
        
        # Empty structs (can be filled in later if needed)
        collection_address = "0x0000000000000000000000000000000000000000"
        collection_config = ("", 0, 0, collection_address, 0)
        
        license_terms_config = (
            0,  # defaultMintingFee
            collection_address,  # currency
            collection_address,  # royaltyPolicy
            False,  # transferable
            0,  # expiration
            False,  # commercialUse
            False,  # commercialAttribution
            0,  # commercialRevShare
            0,  # commercialRevCeiling
            False,  # derivativesAllowed
            False,  # derivativesAttribution
            False,  # derivativesApproval
            False,  # derivativesReciprocal
            0,  # derivativeRevCeiling
            ""  # uri
        )
        
        license_mint_params = (
            0,  # licenseTermsId
            collection_address,  # licensorIpId
            recipient,  # receiver
            0,  # amount
            0,  # maxMintingFee
            0  # maxRevenueShare
        )
        
        co_creators = []  # Empty list
        
        # Build transaction - ESTIMATE GAS FIRST to avoid failures
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        # Build the transaction object for gas estimation
        tx_params = {
            "from": self.account.address,
            "value": self.submission_fee,
            "nonce": nonce,
            "chainId": self.w3.eth.chain_id,
        }
        
        # Estimate gas with safety margin
        try:
            logger.debug("Estimating gas requirement...")
            estimated_gas = self.contract.functions.depositIP(
                recipient,
                validation,
                proof,
                collection_address,
                collection_config,
                tweet_hash,
                license_terms_config,
                license_mint_params,
                co_creators
            ).estimate_gas(tx_params)
            
            # Add 20% safety margin to prevent out-of-gas errors
            gas_limit = int(estimated_gas * 1.2)
            logger.info(f"   Estimated gas: {estimated_gas:,} → Using: {gas_limit:,} (with 20% buffer)")
            
        except Exception as e:
            # If estimation fails, use a very high but safe gas limit
            gas_limit = 10_000_000  # 10M gas - should be enough for any transaction
            logger.warning(f"   Could not estimate gas ({e}), using fallback: {gas_limit:,}")
        
        # Get current gas price with multiplier for faster inclusion
        try:
            base_gas_price = self.w3.eth.gas_price
            # Use 1.5x base gas price for faster inclusion
            gas_price = int(base_gas_price * 1.5)
            logger.info(f"   Gas price: {self.w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
        except:
            # Fallback gas price
            gas_price = self.w3.to_wei(50, "gwei")
            logger.warning(f"   Using fallback gas price: 50 Gwei")
        
        # Add gas parameters to transaction
        tx_params["gas"] = gas_limit
        tx_params["gasPrice"] = gas_price
        
        # Build final transaction
        tx = self.contract.functions.depositIP(
            recipient,
            validation,
            proof,
            collection_address,
            collection_config,
            tweet_hash,
            license_terms_config,
            license_mint_params,
            co_creators
        ).build_transaction(tx_params)
        
        # Sign and send
        logger.info("   Signing and sending transaction...")
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        tx_hash_hex = tx_hash.hex()
        logger.info(f"✅ Transaction sent: {tx_hash_hex}")
        logger.info(f"   Tweet hash: {tweet_hash.hex()}")
        logger.info(f"   Explorer: https://filfox.info/en/message/{tx_hash_hex}")
        
        return tx_hash_hex
    
    def should_submit(self, controversy_score: float) -> bool:
        """
        Determine if a tweet should be submitted based on controversy score.
        
        Args:
            controversy_score: Score from 0-1
        
        Returns:
            True if should submit
        """
        threshold = config.AUTO_SUBMIT_THRESHOLD
        should = controversy_score >= threshold
        
        if should:
            logger.info(f"✅ Score {controversy_score:.2%} >= threshold {threshold:.2%} - will submit")
        else:
            logger.debug(f"Score {controversy_score:.2%} < threshold {threshold:.2%} - skipping")
        
        return should
    
    def submit_if_controversial(self,
                               tweet_url: str,
                               controversy_score: float,
                               metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Submit tweet only if it exceeds controversy threshold.
        
        Returns:
            Transaction hash if submitted, None otherwise
        """
        if self.should_submit(controversy_score):
            return self.submit_tweet(tweet_url, controversy_score, metadata)
        return None


# Singleton instance
_submitter = None

def get_submitter() -> TweetSubmitter:
    """Get or create the global submitter instance"""
    global _submitter
    if _submitter is None:
        _submitter = TweetSubmitter()
    return _submitter


def submit_tweet(tweet_url: str, controversy_score: float, metadata: Dict = None) -> str:
    """
    Convenience function for submitting a single tweet.
    """
    submitter = get_submitter()
    return submitter.submit_tweet(tweet_url, controversy_score, metadata)


def submit_if_controversial(tweet_url: str, controversy_score: float, metadata: Dict = None) -> Optional[str]:
    """
    Convenience function for conditional submission.
    """
    submitter = get_submitter()
    return submitter.submit_if_controversial(tweet_url, controversy_score, metadata)


def main():
    """CLI testing interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Submit tweets to IP_Deposit contract')
    parser.add_argument('--url', required=True, help='Tweet URL')
    parser.add_argument('--score', type=float, required=True, help='Controversy score (0-1)')
    parser.add_argument('--force', action='store_true', help='Submit regardless of threshold')
    
    args = parser.parse_args()
    
    # Validate config
    is_valid, missing = config.validate_config()
    if not is_valid:
        logger.error("❌ Missing required configuration:")
        for key in missing:
            logger.error(f"   - {key}")
        sys.exit(1)
    
    try:
        submitter = TweetSubmitter()
        
        if args.force:
            tx_hash = submitter.submit_tweet(args.url, args.score)
            print(f"\n✅ Submitted (forced): {tx_hash}")
        else:
            tx_hash = submitter.submit_if_controversial(args.url, args.score)
            if tx_hash:
                print(f"\n✅ Submitted: {tx_hash}")
            else:
                print(f"\n⏭️  Skipped (score {args.score:.2%} below threshold {config.AUTO_SUBMIT_THRESHOLD:.2%})")
    
    except Exception as e:
        logger.error(f"❌ Submission failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()