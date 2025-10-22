from registry_interaction import TweetDataRegistry
from pathlib import Path
import config

w3 = TweetDataRegistry().w3
current = w3.eth.block_number
safe_start = max(0, current - 200)  # ~100 minutes at ~30s/block
Path(config.LAST_BLOCK_FILE).parent.mkdir(parents=True, exist_ok=True)
Path(config.LAST_BLOCK_FILE).write_text(str(safe_start))
print("Set last_block to:", safe_start, "(current:", current, ")")