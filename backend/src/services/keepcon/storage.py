import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class KeepconStorage:
    columns = [
        "id",
        "source",
        "content_type",
        "text",
        "created_at",
        "url",
        "social_user_id",
        "username",
        "user_name",
        "keepcon_sentiment",
        "sentiment",
        "ai_sentiment",
        "ai_location",
        "ai_sentiment_model",
        "ai_sentiment_analyzed_at",
        "tags",
        "review_status",
        "moderation_decision",
        "last_operator",
        "last_operation_date",
        "updated_at",
        "attention_status",
        "profile_id",
        "profile_location",
        "profile_link",
        "followers_count",
        "is_influencer",
    ]

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.data_dir = os.path.dirname(csv_path)
        os.makedirs(self.data_dir, exist_ok=True)

    def save_data(self, new_data):
        if not new_data:
            return 0
        
        df_new = pd.DataFrame(new_data).fillna("")
        df_new = self._ensure_columns(df_new)
        
        if os.path.exists(self.csv_path):
            df_existing = self.load_data()
            df_combined = pd.concat([df_existing, df_new], ignore_index=True).drop_duplicates(subset=['id'], keep='last')
        else:
            df_existing = pd.DataFrame(columns=self.columns)
            df_combined = df_new
            
        # Ensure created_at is datetime so we can sort
        df_combined['created_at_dt'] = pd.to_datetime(df_combined['created_at'], errors="coerce", utc=True)
        df_combined = df_combined.sort_values(by='created_at_dt', ascending=False)
        df_combined = df_combined.drop(columns=['created_at_dt'])
        df_combined = self._ensure_columns(df_combined)
        
        df_combined.to_csv(self.csv_path, index=False)
        
        new_count = len(df_combined) - len(df_existing)
        return max(new_count, 0)

    def load_data(self):
        if not os.path.exists(self.csv_path):
            return pd.DataFrame(columns=self.columns)
        df = pd.read_csv(self.csv_path, dtype=str).fillna("")
        return self._ensure_columns(df)

    def analysis_map(self):
        df = self.load_data()
        existing = {}
        if df.empty:
            return existing

        for _, row in df.iterrows():
            item_id = row.get("id")
            if item_id and row.get("ai_sentiment"):
                existing[str(item_id)] = {
                    "ai_sentiment": row.get("ai_sentiment", ""),
                    "ai_location": row.get("ai_location", ""),
                    "ai_sentiment_model": row.get("ai_sentiment_model", ""),
                    "ai_sentiment_analyzed_at": row.get("ai_sentiment_analyzed_at", ""),
                }
        return existing

    def _ensure_columns(self, df):
        for column in self.columns:
            if column not in df.columns:
                if column == "keepcon_sentiment" and "sentiment" in df.columns:
                    df[column] = df["sentiment"]
                elif column == "sentiment" and "keepcon_sentiment" in df.columns:
                    df[column] = df["keepcon_sentiment"]
                elif column == "attention_status":
                    df[column] = df.apply(self._derive_attention_status, axis=1)
                elif column == "is_influencer":
                    df[column] = df.get("followers_count", "").apply(self._is_influencer) if "followers_count" in df.columns else False
                elif column == "followers_count":
                    df[column] = 0
                else:
                    df[column] = ""

        if "keepcon_sentiment" in df.columns:
            df["keepcon_sentiment"] = df["keepcon_sentiment"].replace("", pd.NA).fillna(df["sentiment"]).fillna("unknown")
        if "sentiment" in df.columns:
            df["sentiment"] = df["sentiment"].replace("", pd.NA).fillna(df["keepcon_sentiment"]).fillna("unknown")
        df["attention_status"] = df.apply(self._derive_attention_status, axis=1)
        df["followers_count"] = df["followers_count"].replace("", "0")
        df["is_influencer"] = df["is_influencer"].apply(lambda value: str(value).lower() in {"true", "1", "yes"})
        df["ai_location"] = df["ai_location"].apply(self._clean_location)
        return df[self.columns]

    def _derive_attention_status(self, row):
        status = str(row.get("review_status", "") or "").strip().lower()
        decision = str(row.get("moderation_decision", "") or "").strip().lower()
        last_operator = str(row.get("last_operator", "") or "").strip().lower()
        has_human_touch = bool(row.get("last_operation_date")) or last_operator not in {"", "robot"}
        closed_values = {"closed", "cerrado", "resolved", "resuelto", "done", "finalized", "finished", "close", "solved"}
        open_values = {"not_reviewed", "pending", "unread", "new", "open"}
        if status in closed_values or decision in closed_values:
            return "cerrado"
        if status in open_values and not has_human_touch:
            return "sin_atender"
        if status or has_human_touch:
            return "en_atencion"
        return "sin_atender"

    def _is_influencer(self, value):
        try:
            return int(float(str(value).replace(",", "").strip() or 0)) > 5000
        except Exception:
            return False

    def _clean_location(self, value):
        parts = [
            part.strip()
            for part in str(value or "").split(",")
            if part.strip() and part.strip().lower() not in {"null", "none", "unknown", "unrecognized"}
        ]
        return ", ".join(parts)
