# Scrapebadger Mentions Test

This document captures the contract for the first controlled Scrapebadger connection test. The test is intentionally gated so it does not consume credits unless explicitly enabled.

## Endpoint

- Method: `GET`
- URL: `https://scrapebadger.com/v1/twitter/tweets/advanced_search`
- Authentication: `x-api-key` header using `SCRAPEBADGER_API`
- Query params:
  - `query`: `(@NetlifeEcuador OR @CNT_ECU OR @TuentiEC OR @MovistarEC) since:YYYY-MM-DD until:YYYY-MM-DD`
  - `query_type`: `Latest`
  - `count`: `20`

The test does not send `cursor`, so it only fetches the first page. One successful execution should consume 1 Scrapebadger credit according to the Twitter API pricing documentation.

## Running The Live Test

The test is skipped by default to avoid accidental credit usage.

```bash
SCRAPEBADGER_LIVE_TEST=1 python3 backend/tests/scrapebadger/test_scrapebadger_mentions.py
```

Expected environment values in `.env`:

- `SCRAPEBADGER_API`: required for the live request.
- `OPENAI_API`: checked for the future sentiment step, but not used by this test.

The test never prints secrets.

## Response Shape To Validate

Expected top-level response:

```json
{
  "data": [],
  "next_cursor": null
}
```

Useful tweet fields for the dashboard:

- `id`: stable unique tweet ID. This should be the dedupe key and the key used to avoid recalculating sentiment.
- `text` or `full_text`: tweet content to display and later analyze.
- `created_at`: tweet timestamp. The test keeps only tweets from the current day in `America/Guayaquil`.
- `username` and `user_name`: author identity.
- `user_mentions`: preferred source for detecting which tracked account was mentioned.
- `place`: optional location object.
- `user_location`: profile location returned by Scrapebadger; use as fallback when `place` is null.
- `favorite_count`, `retweet_count`, `reply_count`, `quote_count`, `view_count`: engagement fields.

Location fields expected inside `place`, when Twitter provides them:

- `id`
- `full_name`
- `name`
- `country`
- `country_code`
- `place_type`

Tweets often have `place: null`; the dashboard should treat location as optional and prefer `user_location` as a softer location signal.

## Matching Accounts

The test detects `matched_accounts` with this priority:

1. Inspect `user_mentions[*].username`.
2. Fall back to a case-insensitive search in `text` and `full_text`.

Tracked accounts:

- `@NetlifeEcuador`
- `@CNT_ECU`
- `@TuentiEC`
- `@MovistarEC`

## Future CSV Contract

The production integration should write cleaned history to `backend/data/scrapebadger_data.csv`. Recommended columns:

- `id`
- `source`
- `content_type`
- `text`
- `created_at`
- `url`
- `username`
- `user_name`
- `user_location`
- `mentioned_accounts`
- `matched_account`
- `sentiment`
- `sentiment_model`
- `sentiment_analyzed_at`
- `place_id`
- `place_name`
- `place_full_name`
- `place_country`
- `place_country_code`
- `place_type`
- `raw_json`

Sentiment should be calculated later with OpenAI using exactly `gpt-4.1-nano`. If a tweet ID already exists with sentiment in the CSV, it should not be analyzed again.

## Refresh Defaults

For the future service implementation, use a dedicated refresh interval:

```text
SCRAPEBADGER_REFRESH_INTERVAL_SECONDS=86400
```

Manual refresh should fetch only the latest 20 tweets for today and should not paginate.
