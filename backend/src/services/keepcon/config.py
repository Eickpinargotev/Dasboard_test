import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class KeepconConfig:
    def __init__(self):
        values = self._load_env_values()

        self.token = values.get("KEEPCON_TOKEN") or values.get("token")
        self.account_number = values.get("KEEPCON_ACCOUNT_NUMBER") or values.get("account_number")
        self.openai_api_key = values.get("OPENAI_API") or values.get("OPENAI_API_KEY")
        self.openai_model = values.get("KEEPCON_OPENAI_MODEL", "gpt-4.1-nano")
        self.openai_url = values.get("OPENAI_URL", "https://api.openai.com/v1/chat/completions")
        self.openai_sync_chunk_size = int(values.get("KEEPCON_OPENAI_SYNC_CHUNK_SIZE", 10))
        self.influencer_threshold = int(values.get("KEEPCON_INFLUENCER_THRESHOLD", 5000))
        
        self.base_url = f"https://api.keepcon.com/accounts/{self.account_number}/content/search"
        self.profiles_url = f"https://api.keepcon.com/accounts/{self.account_number}/profiles"
        self.allowed_content_types = [
            "tweet", "retweet", "quote", 
            "fb-comment", "fb-post", 
            "ig-comment", "ig-media", "ig-image", "ig-story", "ig-video"
        ]
        self.official_accounts = ["claroecua", "claro ecuador", "claroecuador"]

    def _load_env_values(self):
        values = {}
        for parent in Path(__file__).resolve().parents:
            env_path = parent / ".env"
            if not env_path.exists():
                continue
            with env_path.open("r", encoding="utf-8") as env_file:
                for raw_line in env_file:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    separator = "=" if "=" in line else ":" if ":" in line else None
                    if not separator:
                        continue
                    key, value = line.split(separator, 1)
                    values[key.strip()] = value.strip().strip('"').strip("'")
            break

        values.update({key: value for key, value in os.environ.items() if value})
        return values
