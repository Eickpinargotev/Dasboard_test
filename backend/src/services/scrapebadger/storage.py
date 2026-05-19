import os
import json

import pandas as pd


class ScrapebadgerStorage:
    columns = [
        "id",
        "source",
        "content_type",
        "text",
        "created_at",
        "url",
        "username",
        "user_name",
        "user_location",
        "mentioned_accounts",
        "matched_account",
        "sentiment",
        "sentiment_model",
        "sentiment_analyzed_at",
        "place_id",
        "place_name",
        "place_full_name",
        "place_country",
        "place_country_code",
        "place_type",
        "favorite_count",
        "retweet_count",
        "reply_count",
        "quote_count",
        "view_count",
        "raw_json",
    ]

    def __init__(self, csv_path):
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    def load_data(self):
        if not os.path.exists(self.csv_path):
            return pd.DataFrame(columns=self.columns)
        df = pd.read_csv(self.csv_path, dtype=str).fillna("")
        for column in self.columns:
            if column not in df.columns:
                df[column] = ""
        if "raw_json" in df.columns:
            df["user_location"] = df.apply(self._fill_user_location, axis=1)
        return df

    def sentiment_map(self):
        df = self.load_data()
        if df.empty or "id" not in df.columns:
            return {}

        existing = {}
        for _, row in df.iterrows():
            sentiment = row.get("sentiment", "")
            if row.get("id") and sentiment:
                existing[str(row["id"])] = {
                    "sentiment": sentiment,
                    "sentiment_model": row.get("sentiment_model", ""),
                    "sentiment_analyzed_at": row.get("sentiment_analyzed_at", ""),
                }
        return existing

    def save_data(self, new_data):
        if not new_data:
            return 0

        df_new = pd.DataFrame(new_data).fillna("")
        for column in self.columns:
            if column not in df_new.columns:
                df_new[column] = ""
        if os.path.exists(self.csv_path):
            df_existing = pd.read_csv(self.csv_path, dtype=str).fillna("")
            existing_len = len(df_existing)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=["id"], keep="last")
        else:
            existing_len = 0
            df_combined = df_new

        df_combined["created_at_dt"] = pd.to_datetime(df_combined["created_at"], errors="coerce", utc=True)
        df_combined = df_combined.sort_values(by="created_at_dt", ascending=False)
        df_combined = df_combined.drop(columns=["created_at_dt"])
        df_combined.to_csv(self.csv_path, index=False)

        return max(len(df_combined) - existing_len, 0)

    def _fill_user_location(self, row):
        if row.get("user_location"):
            return row.get("user_location")
        try:
            raw = json.loads(row.get("raw_json", "{}"))
            return raw.get("user_location") or ""
        except Exception:
            return ""
