import logging

import requests

logger = logging.getLogger(__name__)


class ScrapebadgerClient:
    def __init__(self, config):
        self.config = config

    def advanced_search(self, query):
        if not self.config.api_key:
            logger.error("No Scrapebadger API key found.")
            return None

        params = {
            "query": query,
            "query_type": "Latest",
            "count": self.config.count,
        }
        headers = {
            "Accept": "application/json",
            "x-api-key": self.config.api_key,
        }

        try:
            response = requests.get(self.config.base_url, params=params, headers=headers, timeout=45)
            if response.status_code != 200:
                logger.error("Scrapebadger API error: %s - %s", response.status_code, response.text)
                return {"error": response.text, "status_code": response.status_code}
            return response.json()
        except Exception as exc:
            logger.error("Error during Scrapebadger API request: %s", exc)
            return {"error": str(exc), "status_code": None}
