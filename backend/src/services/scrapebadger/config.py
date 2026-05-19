import os
from pathlib import Path


class ScrapebadgerConfig:
    def __init__(self):
        values = self._load_env_values()

        self.api_key = values.get("SCRAPEBADGER_API")
        self.openai_api_key = values.get("OPENAI_API")
        self.openai_model = "gpt-4.1-nano"
        self.base_url = "https://scrapebadger.com/v1/twitter/tweets/advanced_search"
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.count = int(values.get("SCRAPEBADGER_COUNT", 20))
        self.refresh_interval_seconds = int(values.get("SCRAPEBADGER_REFRESH_INTERVAL_SECONDS", 86400))
        self.target_accounts = ["@NetlifeEcuador", "@CNT_ECU", "@TuentiEC", "@MovistarEC"]
        self.timezone = values.get("SCRAPEBADGER_TIMEZONE", "America/Guayaquil")

    def _load_env_values(self):
        values = {}
        env_path = None
        for parent in Path(__file__).resolve().parents:
            candidate = parent / ".env"
            if candidate.exists():
                env_path = candidate
                break

        if env_path:
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

        values.update({key: value for key, value in os.environ.items() if value})
        return values
