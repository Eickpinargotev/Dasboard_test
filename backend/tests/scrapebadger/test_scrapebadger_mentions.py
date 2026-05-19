import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


API_URL = "https://scrapebadger.com/v1/twitter/tweets/advanced_search"
TARGET_ACCOUNTS = ["@NetlifeEcuador", "@CNT_ECU", "@TuentiEC", "@MovistarEC"]
LOCAL_TZ = ZoneInfo("America/Guayaquil")
COUNT = 20
LIVE_TEST_ENV = "SCRAPEBADGER_LIVE_TEST"


def load_env_values():
    values = {}
    env_path = Path(__file__).resolve().parents[3] / ".env"

    if env_path.exists():
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


def build_today_query(now=None):
    today = (now or datetime.now(LOCAL_TZ)).date()
    tomorrow = today + timedelta(days=1)
    accounts_query = " OR ".join(TARGET_ACCOUNTS)
    return f"({accounts_query}) since:{today.isoformat()} until:{tomorrow.isoformat()}"


def request_latest_mentions(api_key, query):
    params = {
        "query": query,
        "query_type": "Latest",
        "count": COUNT,
    }
    url = f"{API_URL}?{urlencode(params)}"
    request = Request(url, headers={"x-api-key": api_key, "Accept": "application/json"})

    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"ScrapeBadger returned HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise AssertionError(f"Could not reach ScrapeBadger: {exc.reason}") from exc


def parse_tweet_datetime(value):
    if not value:
        return None

    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def is_today_local(tweet):
    created_at = parse_tweet_datetime(tweet.get("created_at"))
    if not created_at:
        return False
    return created_at.astimezone(LOCAL_TZ).date() == datetime.now(LOCAL_TZ).date()


def mentioned_usernames(tweet):
    mentions = tweet.get("user_mentions") or []
    usernames = []
    for mention in mentions:
        if isinstance(mention, dict) and mention.get("username"):
            usernames.append(f"@{mention['username']}".lower())
    return usernames


def detect_matched_accounts(tweet):
    text = f"{tweet.get('full_text') or ''} {tweet.get('text') or ''}".lower()
    mentions = mentioned_usernames(tweet)
    matches = []

    for account in TARGET_ACCOUNTS:
        account_lower = account.lower()
        if account_lower in mentions or account_lower in text:
            matches.append(account)

    return matches


def validate_tweet_shape(tweet):
    assert isinstance(tweet, dict), "Each tweet must be an object."
    assert tweet.get("id"), "Tweet is missing id."
    assert tweet.get("text") or tweet.get("full_text"), f"Tweet {tweet.get('id')} is missing text/full_text."
    assert tweet.get("created_at"), f"Tweet {tweet.get('id')} is missing created_at."

    for optional_key in [
        "username",
        "user_name",
        "user_mentions",
        "place",
        "favorite_count",
        "retweet_count",
        "reply_count",
        "quote_count",
        "view_count",
    ]:
        assert optional_key in tweet, f"Tweet {tweet.get('id')} is missing expected key {optional_key}."


def test_build_today_query_uses_local_date_window():
    fixed_now = datetime(2026, 5, 14, 9, 30, tzinfo=LOCAL_TZ)

    query = build_today_query(fixed_now)

    assert "@NetlifeEcuador OR @CNT_ECU OR @TuentiEC OR @MovistarEC" in query
    assert "since:2026-05-14" in query
    assert "until:2026-05-15" in query


def test_detect_matched_accounts_from_mentions_and_text():
    tweet = {
        "text": "Hola @MovistarEC, necesito ayuda.",
        "full_text": None,
        "user_mentions": [{"username": "CNT_ECU"}],
    }

    assert detect_matched_accounts(tweet) == ["@CNT_ECU", "@MovistarEC"]


def test_scrapebadger_latest_mentions_live():
    env_values = load_env_values()

    if env_values.get(LIVE_TEST_ENV) != "1":
        raise unittest.SkipTest(
            f"Set {LIVE_TEST_ENV}=1 to run the live Scrapebadger test. "
            "Skipped to avoid consuming credits accidentally."
        )

    api_key = env_values.get("SCRAPEBADGER_API")
    assert api_key, "SCRAPEBADGER_API is required for the live test."
    assert env_values.get("OPENAI_API"), "OPENAI_API must exist for the future sentiment step."

    query = build_today_query()
    status, payload = request_latest_mentions(api_key, query)

    assert status == 200
    assert isinstance(payload, dict), "ScrapeBadger response must be an object."
    assert "data" in payload, "Response is missing data."
    assert "next_cursor" in payload, "Response is missing next_cursor."

    tweets = payload.get("data") or []
    assert isinstance(tweets, list), "Response data must be a list or null."
    assert len(tweets) <= COUNT, f"Expected at most {COUNT} tweets."

    today_tweets = [tweet for tweet in tweets if is_today_local(tweet)]
    for tweet in today_tweets:
        validate_tweet_shape(tweet)
        tweet["matched_accounts"] = detect_matched_accounts(tweet)

    print("\nScrapeBadger live test summary:")
    print(f"- Query: {query}")
    print(f"- Returned tweets: {len(tweets)}")
    print(f"- Tweets from today ({LOCAL_TZ.key}): {len(today_tweets)}")
    print("- API key: present, not printed")
    print("- OpenAI key: present, not used")


if __name__ == "__main__":
    try:
        test_scrapebadger_latest_mentions_live()
    except unittest.SkipTest as exc:
        print(f"SKIPPED: {exc}")
        sys.exit(0)
