import json
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


class ScrapebadgerSentimentAnalyzer:
    def __init__(self, config):
        self.config = config

    def analyze_missing(self, tweets):
        pending = [
            {"id": item["id"], "text": item.get("text", "")}
            for item in tweets
            if item.get("id") and not item.get("sentiment")
        ]
        if not pending:
            return {}

        if not self.config.openai_api_key:
            logger.warning("No OpenAI API key found. Leaving pending sentiments empty.")
            return {}

        prompt = (
            "Clasifica el sentimiento de estos tweets en espanol. "
            "Responde solo JSON valido con esta forma: "
            '{"results":[{"id":"tweet-id","sentiment":"positive|negative|neutral|no sentiment"}]}. '
            "Usa negative si expresa queja, falla, molestia o reclamo; "
            "positive si expresa satisfaccion o recomendacion; neutral para menciones informativas; "
            "no sentiment si el texto no tiene suficiente contenido para inferir postura."
        )
        payload = {
            "model": self.config.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps({"tweets": pending}, ensure_ascii=False)},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.config.openai_url, json=payload, headers=headers, timeout=60)
            if response.status_code != 200:
                logger.error("OpenAI sentiment error: %s - %s", response.status_code, response.text)
                return {}

            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            now = datetime.now(timezone.utc).isoformat()
            sentiments = {}

            for result in parsed.get("results", []):
                tweet_id = str(result.get("id", ""))
                sentiment = str(result.get("sentiment", "neutral")).lower()
                if sentiment not in {"positive", "negative", "neutral", "no sentiment"}:
                    sentiment = "no sentiment"
                if tweet_id:
                    sentiments[tweet_id] = {
                        "sentiment": sentiment,
                        "sentiment_model": self.config.openai_model,
                        "sentiment_analyzed_at": now,
                    }

            return sentiments
        except Exception as exc:
            logger.error("Error during OpenAI sentiment request: %s", exc)
            return {}
