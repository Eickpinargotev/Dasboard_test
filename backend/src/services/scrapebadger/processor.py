import json
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo


class ScrapebadgerProcessor:
    def __init__(self, config):
        self.config = config
        self.local_tz = ZoneInfo(config.timezone)

    def build_today_query(self):
        today = datetime.now(self.local_tz).date()
        tomorrow = today + timedelta(days=1)
        accounts_query = " OR ".join(self.config.target_accounts)
        return f"({accounts_query}) since:{today.isoformat()} until:{tomorrow.isoformat()}"

    def parse_api_response(self, data):
        if not isinstance(data, dict):
            return []
        items = data.get("data") or []
        return items if isinstance(items, list) else []

    def process_item(self, item):
        if not isinstance(item, dict):
            return None

        created_at = item.get("created_at")
        created_dt = self.parse_datetime(created_at)
        if not created_dt or created_dt.astimezone(self.local_tz).date() != datetime.now(self.local_tz).date():
            return None

        text = item.get("full_text") or item.get("text") or ""
        matched_accounts = self.detect_matched_accounts(item, text)
        if not matched_accounts:
            return None

        place = item.get("place") or {}
        username = item.get("username") or ""
        tweet_id = str(item.get("id") or "")

        return {
            "id": tweet_id,
            "source": "twitter",
            "content_type": "tweet",
            "text": text,
            "created_at": created_dt.isoformat(),
            "url": f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else "",
            "username": username,
            "user_name": item.get("user_name") or "",
            "user_location": item.get("user_location") or "",
            "mentioned_accounts": json.dumps(matched_accounts, ensure_ascii=False),
            "matched_account": matched_accounts[0],
            "sentiment": "",
            "sentiment_model": "",
            "sentiment_analyzed_at": "",
            "place_id": place.get("id", "") if isinstance(place, dict) else "",
            "place_name": place.get("name", "") if isinstance(place, dict) else "",
            "place_full_name": place.get("full_name", "") if isinstance(place, dict) else "",
            "place_country": place.get("country", "") if isinstance(place, dict) else "",
            "place_country_code": place.get("country_code", "") if isinstance(place, dict) else "",
            "place_type": place.get("place_type", "") if isinstance(place, dict) else "",
            "favorite_count": item.get("favorite_count", 0),
            "retweet_count": item.get("retweet_count", 0),
            "reply_count": item.get("reply_count", 0),
            "quote_count": item.get("quote_count", 0),
            "view_count": item.get("view_count", 0),
            "raw_json": json.dumps(item, ensure_ascii=False),
        }

    def parse_datetime(self, value):
        if not value:
            return None
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return None

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt

    def detect_matched_accounts(self, item, text):
        mentions = []
        for mention in item.get("user_mentions") or []:
            if isinstance(mention, dict) and mention.get("username"):
                mentions.append(f"@{mention['username']}".lower())

        lower_text = text.lower()
        matches = []
        for account in self.config.target_accounts:
            account_lower = account.lower()
            if account_lower in mentions or account_lower in lower_text:
                matches.append(account)
        return matches
