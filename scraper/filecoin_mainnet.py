#!/usr/bin/env python3
"""
Filecoin Mainnet Storage via Storacha (w3up.storage)
Complete implementation for mainnet storage using Storacha API.
DOES NOT modify existing testnet functionality.
"""

import os
import sys
import json
import logging
import subprocess
import requests
from pathlib import Path
from typing import Tuple, Optional, Dict

from dotenv import load_dotenv
import config

load_dotenv()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class FilecoinMainnetStorage:
    """
    Handles storage to Filecoin mainnet via Storacha (w3up).
    No custom deal contracts - Storacha handles everything.
    """
    
    def __init__(self, space_did: str = None, pinata_jwt: str = None):
        """
        Initialize Filecoin mainnet storage.
        
        Args:
            space_did: Storacha space DID (defaults to config)
            pinata_jwt: Pinata JWT for IPFS pinning (defaults to config)
        """
        self.space_did = space_did or config.STORACHA_SPACE_DID
        self.pinata_jwt = pinata_jwt or config.PINATA_JWT
        
        if not self.space_did:
            raise ValueError("STORACHA_SPACE_DID not configured")
        if not self.pinata_jwt:
            raise ValueError("PINATA_JWT not configured")
        
        logger.info(f"✅ Filecoin Mainnet Storage initialized")
        logger.info(f"   Space DID: {self.space_did}")
    
    def pin_to_pinata(self, file_path: str) -> str:
        """
        Pin a file to IPFS via Pinata.
        Returns the CID.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {"Authorization": f"Bearer {self.pinata_jwt}"}
        
        logger.info(f"📤 Pinning to IPFS: {file_path}")
        
        with open(file_path, "rb") as fp:
            files = {"file": (Path(file_path).name, fp)}
            response = requests.post(url, headers=headers, files=files)
        
        response.raise_for_status()
        cid = response.json()["IpfsHash"]
        
        logger.info(f"📦 Pinned to IPFS: {cid}")
        logger.info(f"   Gateway URL: https://gateway.pinata.cloud/ipfs/{cid}")
        
        return cid
    
    def _check_command_exists(self, cmd: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def make_car(self, file_path: str) -> Tuple[str, str, str, int]:
        """
        Create a CAR file from the input file.
        
        Returns:
            (root_cid, car_cid, car_path, car_size)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check dependencies
        if not self._check_command_exists("ipfs"):
            raise EnvironmentError(
                "IPFS CLI not installed. Install from: https://docs.ipfs.tech/install/command-line/"
            )
        
        if not self._check_command_exists("ipfs-car"):
            raise EnvironmentError(
                "ipfs-car not installed. Install with: npm install -g ipfs-car"
            )
        
        logger.info(f"🗂️  Creating CAR file for: {file_path}")
        
        # Step 1: Add to IPFS to get root CID
        logger.debug("Step 1/3: Adding to IPFS...")
        result = subprocess.run(
            ["ipfs", "add", "-Q", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        root_cid = result.stdout.strip()
        logger.info(f"   Root CID: {root_cid}")
        
        # Step 2: Export DAG to CAR
        car_path = f"{file_path}.car"
        logger.debug(f"Step 2/3: Exporting to CAR: {car_path}")
        
        with open(car_path, "wb") as out:
            subprocess.run(
                ["ipfs", "dag", "export", root_cid],
                stdout=out,
                check=True
            )
        
        # Step 3: Get CAR CID
        logger.debug("Step 3/3: Computing CAR CID...")
        result = subprocess.run(
            ["ipfs-car", "hash", car_path],
            capture_output=True,
            text=True,
            check=True
        )
        car_cid = result.stdout.strip()
        
        # Get CAR size
        car_size = Path(car_path).stat().st_size
        
        logger.info(f"✅ CAR file ready:")
        logger.info(f"   Root CID: {root_cid}")
        logger.info(f"   CAR CID: {car_cid}")
        logger.info(f"   Size: {car_size:,} bytes")
        
        return root_cid, car_cid, car_path, car_size
    
    def _get_storacha_headers(self) -> Dict[str, str]:
        """
        Generate fresh UCAN tokens for Storacha API.
        Returns headers dict for requests.
        """
        logger.debug("Generating Storacha UCAN tokens...")
        
        cmd = [
            "w3", "bridge", "generate-tokens", self.space_did,
            "-c", "store/add",
            "-c", "upload/add",
            "-c", "deal/add",
            "-j"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            tokens = json.loads(result.stdout)
            
            return {
                "X-Auth-Secret": tokens["X-Auth-Secret"],
                "Authorization": tokens["Authorization"]
            }
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate UCAN tokens: {e.stderr}")
            raise RuntimeError("Make sure w3 CLI is installed: npm install -g @web3-storage/w3cli")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse UCAN tokens: {e}")
            raise
    
    def upload_car(self, root_cid: str, car_cid: str, car_path: str, car_size: int) -> Dict:
        """
        Upload CAR file to Storacha.
        
        Steps:
        1. Call store/add to allocate space
        2. PUT the CAR file if needed
        3. Call upload/add to register shards
        
        Returns:
            Response dictionary from Storacha
        """
        logger.info(f"⬆️  Uploading CAR to Storacha...")
        
        # Step 1: store/add
        headers = self._get_storacha_headers()
        
        store_body = {
            "tasks": [[
                "store/add",
                self.space_did,
                {
                    "link": {"/": car_cid},
                    "size": car_size
                }
            ]]
        }
        
        logger.debug("Step 1/3: Calling store/add...")
        response = requests.post(
            "https://up.storacha.network/bridge",
            headers=headers,
            json=store_body
        )
        response.raise_for_status()
        store_result = response.json()
        
        # Check for errors
        out = store_result[0]["p"]["out"]
        if "error" in out:
            error_msg = out["error"].get("message", json.dumps(out["error"]))
            logger.error(f"❌ store/add failed: {error_msg}")
            raise RuntimeError(f"Storacha store/add failed: {error_msg}")
        
        ok = out.get("ok", {})
        
        # Step 2: Upload CAR if needed
        if ok.get("url"):
            logger.info("Step 2/3: Uploading CAR to allocated space...")
            
            upload_headers = ok.get("headers", {}) or {}
            upload_headers.setdefault("Content-Length", str(car_size))
            
            with open(car_path, "rb") as f:
                upload_response = requests.put(
                    ok["url"],
                    headers=upload_headers,
                    data=f
                )
            upload_response.raise_for_status()
            logger.info("   ✅ CAR uploaded")
        
        elif ok.get("status") == "done":
            logger.info("Step 2/3: 🔁 CAR already stored - skipping upload")
        
        else:
            logger.warning(f"Step 2/3: ⚠️  Unexpected store/add response")
        
        # Step 3: upload/add (register shards)
        logger.debug("Step 3/3: Calling upload/add...")
        
        headers = self._get_storacha_headers()
        upload_body = {
            "tasks": [[
                "upload/add",
                self.space_did,
                {
                    "root": {"/": root_cid},
                    "shards": [{"/": car_cid}]
                }
            ]]
        }
        
        response = requests.post(
            "https://up.storacha.network/bridge",
            headers=headers,
            json=upload_body
        )
        response.raise_for_status()
        
        logger.info("✅ CAR registered on Storacha")
        
        return response.json()
    
    def create_deal(self, root_cid: str, car_cid: str, 
                   miner: str = None, duration: int = None) -> Dict:
        """
        Create a Filecoin storage deal via Storacha.
        
        Args:
            root_cid: Root CID of the data
            car_cid: CAR file CID
            miner: Optional specific miner to use
            duration: Optional deal duration in epochs
        
        Returns:
            Deal response from Storacha
        """
        logger.info(f"🎯 Creating Filecoin deal...")
        
        headers = self._get_storacha_headers()
        
        deal_payload = {
            "root": {"/": root_cid},
            "car": {"/": car_cid}
        }
        
        if miner:
            deal_payload["miner"] = miner
            logger.info(f"   Requested miner: {miner}")
        
        if duration:
            deal_payload["duration"] = duration
            logger.info(f"   Requested duration: {duration} epochs")
        
        deal_body = {
            "tasks": [[
                "deal/add",
                self.space_did,
                deal_payload
            ]]
        }
        
        response = requests.post(
            "https://up.storacha.network/bridge",
            headers=headers,
            json=deal_body
        )
        response.raise_for_status()
        deal_result = response.json()
        
        logger.info(f"✅ Deal created")
        logger.debug(f"Deal response: {json.dumps(deal_result, indent=2)}")
        
        return deal_result
    
    def store_file(self, file_path: str, 
                   miner: str = None, 
                   duration: int = None) -> Dict:
        """
        Complete storage pipeline for a file.
        
        Steps:
        1. Pin to IPFS (Pinata)
        2. Create CAR file
        3. Upload to Storacha
        4. Create Filecoin deal
        
        Returns:
            Dictionary with all CIDs and metadata
        """
        logger.info(f"🚀 Starting Filecoin mainnet storage pipeline")
        logger.info(f"   File: {file_path}")
        
        # 1. Pin to IPFS
        ipfs_cid = self.pin_to_pinata(file_path)
        
        # 2. Create CAR
        root_cid, car_cid, car_path, car_size = self.make_car(file_path)
        
        # 3. Upload to Storacha
        upload_result = self.upload_car(root_cid, car_cid, car_path, car_size)
        
        # 4. Create deal
        deal_result = self.create_deal(root_cid, car_cid, miner=miner, duration=duration)
        
        # Extract deal ID if available
        deal_id = None
        try:
            deal_id = deal_result[0]["p"]["out"].get("dealId")
        except (KeyError, IndexError, TypeError):
            logger.warning("⚠️  Could not extract dealId from response")
        
        # Clean up CAR file
        try:
            os.remove(car_path)
            logger.debug(f"Cleaned up CAR file: {car_path}")
        except Exception as e:
            logger.warning(f"Could not remove CAR file: {e}")
        
        result = {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "ipfs_cid": ipfs_cid,
            "root_cid": root_cid,
            "car_cid": car_cid,
            "car_size": car_size,
            "deal_id": deal_id,
            "storacha_space": self.space_did,
            "ipfs_gateway_url": f"https://gateway.pinata.cloud/ipfs/{ipfs_cid}",
            "storacha_url": f"https://{root_cid}.ipfs.w3s.link",
        }
        
        logger.info("✅ Storage pipeline complete!")
        logger.info(f"   IPFS CID: {ipfs_cid}")
        logger.info(f"   Root CID: {root_cid}")
        if deal_id:
            logger.info(f"   Deal ID: {deal_id}")
        
        return result


def main():
    """CLI entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Store files on Filecoin mainnet via Storacha')
    parser.add_argument('--file', required=True, help='File to store')
    parser.add_argument('--miner', help='Specific miner to use (optional)')
    parser.add_argument('--duration', type=int, help='Deal duration in epochs (optional)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    # Validate config
    is_valid, missing = config.validate_config()
    if not is_valid:
        logger.error("❌ Missing required configuration:")
        for key in missing:
            logger.error(f"   - {key}")
        sys.exit(1)
    
    # Initialize storage
    try:
        storage = FilecoinMainnetStorage()
    except Exception as e:
        logger.error(f"❌ Failed to initialize storage: {e}")
        sys.exit(1)
    
    # Store file
    try:
        result = storage.store_file(
            args.file,
            miner=args.miner,
            duration=args.duration
        )
        
        print("\n" + "=" * 60)
        print("STORAGE RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60)
    
    except Exception as e:
        logger.error(f"❌ Storage failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()