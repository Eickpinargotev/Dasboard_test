import json
import logging

logger = logging.getLogger(__name__)

SENTIMENT_VALUES = {"positive", "negative", "neutral", "no sentiment", "unknown"}

class KeepconProcessor:
    def __init__(self, config):
        self.config = config

    def parse_api_response(self, data):
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items", data.get("data", data.get("results", [])))
            if not items and "0" in data:
                items = [data[k] for k in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else 9999) if k.isdigit()]
        else:
            items = []
        
        return items

    def process_item(self, item):
        item_id = item.get("id")
        content = item.get("content", {})
        text = content.get("text", "") or ""
        user = content.get("user", {}) or {}
        
        username = user.get("username")
        user_name = user.get("name")
        
        # Keep only the user's original interaction, not Claro's own posts or replies.
        if str(content.get("own_content", "")).lower() == "true":
            return None

        lower_username = (username or "").lower()
        lower_user_name = (user_name or "").lower()
        
        if any(acc in lower_username for acc in self.config.official_accounts) or \
           any(acc in lower_user_name for acc in self.config.official_accounts):
            return None

        keepcon_sentiment = (item.get("sentiment") or "unknown").lower()
        if keepcon_sentiment not in SENTIMENT_VALUES:
            keepcon_sentiment = "unknown"

        review_status = self._first_present(
            item,
            "review_status",
            "status",
            ("ticket", "status"),
            ("case", "status"),
            ("attention", "status"),
        )
        moderation_decision = self._first_present(item, "moderation_decision", ("moderation", "decision"))
        last_operator = self._first_present(item, "last_operator", ("last_operation", "operator"), ("review", "operator"))
        last_operation_date = self._first_present(
            item,
            "last_operation_date",
            "closed_at",
            "resolved_at",
            ("ticket", "closed_at"),
            ("ticket", "resolved_at"),
            ("last_operation", "date"),
        )
        followers = self._safe_int(user.get("followers"))

        return {
            "id": item_id,
            "source": item.get("source"),
            "content_type": item.get("content_type"),
            "text": text,
            "created_at": content.get("createdat"), # ISO 8601 string
            "url": content.get("url"),
            "social_user_id": user.get("id"),
            "username": username,
            "user_name": user_name,
            "keepcon_sentiment": keepcon_sentiment,
            "sentiment": keepcon_sentiment,
            "tags": json.dumps(item.get("tags", [])),
            "review_status": review_status or "",
            "moderation_decision": moderation_decision or "",
            "last_operator": last_operator or "",
            "last_operation_date": last_operation_date or "",
            "updated_at": item.get("updated_at") or "",
            "attention_status": self.map_attention_status(
                review_status,
                moderation_decision,
                last_operator,
                last_operation_date,
            ),
            "profile_id": "",
            "profile_location": user.get("location") or "",
            "profile_link": "",
            "followers_count": followers,
            "is_influencer": followers > self.config.influencer_threshold,
            "ai_sentiment": "",
            "ai_location": "",
            "ai_sentiment_model": "",
            "ai_sentiment_analyzed_at": "",
        }

    def enrich_with_profile(self, record, profile):
        if not record or not profile:
            return record

        social_users = profile.get("social_users") or []
        source = str(record.get("source") or "").lower()
        social_user_id = str(record.get("social_user_id") or "")
        selected = None

        for social_user in social_users:
            if str(social_user.get("social_network_id") or "") == social_user_id:
                selected = social_user
                break
        if not selected:
            for social_user in social_users:
                if str(social_user.get("type") or "").lower() == source:
                    selected = social_user
                    break
        if not selected and social_users:
            selected = social_users[0]

        followers = self._safe_int((selected or {}).get("followers"))
        record.update({
            "profile_id": profile.get("id") or "",
            "profile_location": (selected or {}).get("location") or "",
            "profile_link": (selected or {}).get("link") or "",
            "followers_count": followers,
            "is_influencer": followers > self.config.influencer_threshold,
        })
        return record

    def map_attention_status(self, review_status, moderation_decision=None, last_operator=None, last_operation_date=None):
        status = str(review_status or "").strip().lower()
        decision = str(moderation_decision or "").strip().lower()
        has_human_touch = bool(last_operation_date) or str(last_operator or "").strip().lower() not in {"", "robot"}

        closed_values = {"closed", "cerrado", "resolved", "resuelto", "done", "finalized", "finished", "close", "solved"}
        open_values = {"not_reviewed", "pending", "unread", "new", "open"}
        if status in closed_values or decision in closed_values:
            return "cerrado"
        if status in open_values and not has_human_touch:
            return "sin_atender"
        if status or has_human_touch:
            return "en_atencion"
        return "sin_atender"

    def _first_present(self, item, *paths):
        for path in paths:
            current = item
            if isinstance(path, tuple):
                for key in path:
                    current = current.get(key) if isinstance(current, dict) else None
            else:
                current = item.get(path)
            if current not in (None, ""):
                return current
        return ""

    def _safe_int(self, value):
        try:
            return int(float(str(value).replace(",", "").strip()))
        except Exception:
            return 0
