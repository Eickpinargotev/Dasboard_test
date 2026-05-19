import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from .client import ScrapebadgerClient
from .config import ScrapebadgerConfig
from .processor import ScrapebadgerProcessor
from .sentiment import ScrapebadgerSentimentAnalyzer
from .storage import ScrapebadgerStorage

logger = logging.getLogger(__name__)


class ScrapebadgerService:
    def __init__(self):
        self.config = ScrapebadgerConfig()
        self.client = ScrapebadgerClient(self.config)
        self.processor = ScrapebadgerProcessor(self.config)
        self.sentiment = ScrapebadgerSentimentAnalyzer(self.config)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        csv_path = os.path.join(base_dir, "data", "scrapebadger_data.csv")
        self.storage = ScrapebadgerStorage(csv_path)

    def refresh_latest(self):
        query = self.processor.build_today_query()
        logger.info("Refreshing Scrapebadger data with query: %s", query)
        response_data = self.client.advanced_search(query)

        if not response_data:
            return {"new_records": 0, "fetched": 0, "message": "No response from Scrapebadger."}
        if response_data.get("error"):
            return {
                "new_records": 0,
                "fetched": 0,
                "message": response_data.get("error"),
                "status_code": response_data.get("status_code"),
            }

        existing_sentiments = self.storage.sentiment_map()
        items = self.processor.parse_api_response(response_data)
        processed = []

        for item in items:
            record = self.processor.process_item(item)
            if not record:
                continue
            if record["id"] in existing_sentiments:
                record.update(existing_sentiments[record["id"]])
            processed.append(record)

        missing_sentiments = [item for item in processed if not item.get("sentiment")]
        sentiment_results = self.sentiment.analyze_missing(missing_sentiments)
        for item in processed:
            if item["id"] in sentiment_results:
                item.update(sentiment_results[item["id"]])

        new_count = self.storage.save_data(processed)
        return {
            "new_records": new_count,
            "fetched": len(items),
            "processed": len(processed),
            "query": query,
            "message": f"Se sincronizaron {new_count} nuevos registros desde Scrapebadger.",
        }

    def get_dashboard_data(self, sentiment_filter=None, account_filter=None, location_filter=None):
        df = self.storage.load_data()
        if df.empty:
            return []

        df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        df = df.dropna(subset=["created_at_dt"])
        today = datetime.now(ZoneInfo(self.config.timezone)).date()
        df = df[df["created_at_dt"].dt.tz_convert(self.config.timezone).dt.date == today].copy()

        if sentiment_filter and sentiment_filter.lower() != "todos":
            sentiment = sentiment_filter.lower()
            if sentiment in {"no sentiment", "sin sentimiento"}:
                df = df[df["sentiment"].fillna("").str.lower().isin(["", "no sentiment", "unknown"])]
            else:
                df = df[df["sentiment"].str.lower() == sentiment]

        if account_filter and account_filter.lower() != "todas":
            df = df[df["mentioned_accounts"].apply(lambda value: self._contains_account(value, account_filter))]

        if location_filter and location_filter.lower() != "todas":
            location = location_filter.lower()
            df = df[
                df["place_full_name"].str.lower().str.contains(location, na=False)
                | df["place_name"].str.lower().str.contains(location, na=False)
                | df["place_country"].str.lower().str.contains(location, na=False)
                | df["user_location"].str.lower().str.contains(location, na=False)
            ]

        df = df.sort_values(by="created_at_dt", ascending=False)
        now = datetime.now(ZoneInfo(self.config.timezone))
        df["relative_time"] = df["created_at_dt"].apply(lambda dt: self._relative_time(dt, now))
        df = df.drop(columns=["created_at_dt"])
        if "raw_json" in df.columns:
            df = df.drop(columns=["raw_json"])
        return df.fillna("").to_dict(orient="records")

    def available_filters(self):
        df = self.storage.load_data()
        accounts = set(self.config.target_accounts)
        locations = set()

        if not df.empty:
            for value in df.get("mentioned_accounts", []):
                try:
                    accounts.update(json.loads(value))
                except Exception:
                    pass
            for column in ["place_full_name", "place_name", "place_country"]:
                if column in df.columns:
                    locations.update(v for v in df[column].dropna().unique() if str(v).strip())
            if "user_location" in df.columns:
                locations.update(v for v in df["user_location"].dropna().unique() if str(v).strip())

        return {"accounts": sorted(accounts), "locations": sorted(locations)}

    def _contains_account(self, value, account):
        try:
            return account in json.loads(value)
        except Exception:
            return account.lower() in str(value).lower()

    def _relative_time(self, dt, now):
        local_dt = dt.tz_convert(self.config.timezone).to_pydatetime()
        diff = now - local_dt
        if diff.days > 0:
            return f"Hace {diff.days} dia{'s' if diff.days > 1 else ''}"
        if diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Hace {hours} hora{'s' if hours > 1 else ''}"
        if diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
        return "Hace unos segundos"
