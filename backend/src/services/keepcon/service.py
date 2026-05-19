import os
import json
import logging
import pandas as pd
import pytz
import time
from datetime import datetime, timedelta, timezone
from .ai_analysis import KeepconAIAnalyzer
from .config import KeepconConfig
from .client import KeepconClient
from .processor import KeepconProcessor
from .storage import KeepconStorage

logger = logging.getLogger(__name__)

class KeepconService:
    def __init__(self):
        self.config = KeepconConfig()
        self.client = KeepconClient(self.config)
        self.processor = KeepconProcessor(self.config)
        self.ai_analyzer = KeepconAIAnalyzer(self.config)
        
        # Determine CSV path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        csv_path = os.path.join(base_dir, 'data', 'keepcon_data.csv')
        self.storage = KeepconStorage(csv_path)
        self.sync_state_path = os.path.join(base_dir, 'data', 'keepcon_sync_state.json')
        self.refresh_diagnostics_path = os.path.join(base_dir, 'data', 'keepcon_refresh_diagnostics.jsonl')

    def fetch_data_from_api(self, from_date, to_date, mode="created", existing_by_id=None, analyze_ai=True):
        started = time.perf_counter()
        all_results = []
        profile_cache = {}
        existing_analysis = self.storage.analysis_map()
        existing_profiles = self._existing_profile_map()
        next_page_token = None
        pages = 0
        profile_calls = 0
        keepcon_duration_ms = 0
        profile_duration_ms = 0
        
        while True:
            keepcon_started = time.perf_counter()
            if mode == "updated":
                response_data = self.client.search_content_by_updated_at(from_date, to_date, next_page_token)
            else:
                response_data = self.client.search_content(from_date, to_date, next_page_token)
            keepcon_duration_ms += int((time.perf_counter() - keepcon_started) * 1000)
            if not response_data:
                break
            pages += 1
                
            items = self.processor.parse_api_response(response_data)
            if not items:
                break
                
            for item in items:
                processed = self.processor.process_item(item)
                if processed:
                    item_id = str(processed["id"])
                    previous = (existing_by_id or {}).get(item_id)
                    is_existing = previous is not None
                    if processed["id"] in existing_analysis:
                        processed.update(existing_analysis[processed["id"]])
                    profile_key = (processed.get("source"), processed.get("social_user_id"))
                    if profile_key[1]:
                        if is_existing and previous is not None and self._has_profile_data(previous):
                            processed.update(self._profile_fields_from_row(previous))
                        elif profile_key in existing_profiles:
                            processed.update(existing_profiles[profile_key])
                        elif self._should_fetch_profile(processed, item, is_existing):
                            if profile_key not in profile_cache:
                                profile_started = time.perf_counter()
                                profile_cache[profile_key] = self.client.get_profile(*profile_key)
                                profile_duration_ms += int((time.perf_counter() - profile_started) * 1000)
                                profile_calls += 1
                            processed = self.processor.enrich_with_profile(processed, profile_cache[profile_key])
                    all_results.append(processed)
            
            # Check for next page
            if isinstance(response_data, dict):
                next_page_token = response_data.get("next_page_token")
            else:
                next_page_token = None
                
            if not next_page_token:
                break

        if analyze_ai:
            ai_analysis = self._analyze_records(all_results)
        else:
            ai_analysis = self._empty_ai_analysis()

        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "records": all_results,
            "pages": pages,
            "profile_calls": profile_calls,
            "diagnostics": {
                "mode": mode,
                "records": len(all_results),
                "pages": pages,
                "keepcon_duration_ms": keepcon_duration_ms,
                "profile_calls": profile_calls,
                "profile_duration_ms": profile_duration_ms,
                "ai": ai_analysis["stats"],
                "duration_ms": duration_ms,
            },
        }

    def refresh_latest(self, days_filter=1):
        """Fetch latest Keepcon records for the active period and update mutable status fields."""
        started = time.perf_counter()
        now = datetime.now()
        from_date = now - timedelta(days=days_filter)
        diagnostics = {"stages": {}}
        sync_state = self._load_sync_state()
        created_from = self._parse_datetime(sync_state.get("last_created_at_sync")) or from_date
        updated_from = self._parse_datetime(sync_state.get("last_updated_at_sync"))
        logger.info(f"Refreshing Keepcon data from {from_date} to {now}...")
        load_started = time.perf_counter()
        existing_df = self.storage.load_data()
        diagnostics["stages"]["load_csv_ms"] = int((time.perf_counter() - load_started) * 1000)
        existing_by_id = {}
        if not existing_df.empty:
            existing_by_id = {
                str(row.get("id")): row
                for _, row in existing_df.iterrows()
                if row.get("id")
            }

        created_started = time.perf_counter()
        created_result = self.fetch_data_from_api(created_from, now, mode="created", existing_by_id=existing_by_id, analyze_ai=False)
        diagnostics["stages"]["created_fetch_ms"] = int((time.perf_counter() - created_started) * 1000)
        updated_result = {"records": [], "pages": 0, "profile_calls": 0}
        if updated_from:
            updated_started = time.perf_counter()
            updated_result = self.fetch_data_from_api(updated_from, now, mode="updated", existing_by_id=existing_by_id, analyze_ai=False)
            diagnostics["stages"]["updated_fetch_ms"] = int((time.perf_counter() - updated_started) * 1000)
        else:
            diagnostics["stages"]["updated_fetch_ms"] = 0
        if self.client.last_error:
            raise RuntimeError(self.client.last_error)

        results = self._merge_records(created_result["records"], updated_result["records"])
        ai_started = time.perf_counter()
        ai_analysis = self._analyze_records(results)
        diagnostics["stages"]["ai_analysis_ms"] = int((time.perf_counter() - ai_started) * 1000)
        count_started = time.perf_counter()
        update_counts = self._count_update_types(existing_by_id, results)
        diagnostics["stages"]["count_updates_ms"] = int((time.perf_counter() - count_started) * 1000)
        save_started = time.perf_counter()
        new_count = self.storage.save_data(results)
        diagnostics["stages"]["save_csv_ms"] = int((time.perf_counter() - save_started) * 1000)
        duration_ms = int((time.perf_counter() - started) * 1000)
        diagnostics["created"] = created_result["diagnostics"]
        diagnostics["updated"] = updated_result.get("diagnostics", {
            "mode": "updated",
            "records": 0,
            "pages": 0,
            "keepcon_duration_ms": 0,
            "profile_calls": 0,
            "profile_duration_ms": 0,
            "ai": {"pending_records": 0, "chunks": 0, "analyzed_records": 0, "duration_ms": 0},
            "duration_ms": 0,
        })
        diagnostics["ai"] = ai_analysis["stats"]
        diagnostics["totals"] = {
            "keepcon_duration_ms": diagnostics["created"]["keepcon_duration_ms"] + diagnostics["updated"]["keepcon_duration_ms"],
            "profile_duration_ms": diagnostics["created"]["profile_duration_ms"] + diagnostics["updated"]["profile_duration_ms"],
            "ai_duration_ms": diagnostics["ai"]["duration_ms"],
            "ai_pending_records": diagnostics["ai"]["pending_records"],
            "ai_chunks": diagnostics["ai"]["chunks"],
            "duration_ms": duration_ms,
        }
        self._save_sync_state({
            "last_created_at_sync": now.isoformat(),
            "last_updated_at_sync": now.isoformat(),
            "last_successful_refresh_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(
            "Refresh complete. Added %s new, status %s, metadata %s, profile %s. Diagnostics: %s",
            new_count,
            update_counts["status_updates"],
            update_counts["metadata_updates"],
            update_counts["profile_updates"],
            diagnostics,
        )
        response = {
            "new_records": new_count,
            **update_counts,
            "updated_records": update_counts["status_updates"] + update_counts["metadata_updates"] + update_counts["profile_updates"],
            "fetched_records": len(results),
            "created_pages": created_result["pages"],
            "updated_pages": updated_result["pages"],
            "profile_calls": created_result["profile_calls"] + updated_result["profile_calls"],
            "duration_ms": duration_ms,
            "diagnostics": diagnostics,
            "last_successful_refresh_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_refresh_diagnostics(response)
        return response

    def get_dashboard_data(self, days_filter=1, sentiment_filter=None, source_filter=None, influencer_filter=None):
        now = datetime.now(pytz.utc)
        df = self.storage.load_data()
        
        target_oldest_time = now - timedelta(days=days_filter)
        
        # Check if we need to backfill
        needs_backfill = False
        if df.empty:
            needs_backfill = True
        else:
            df['created_at_dt'] = pd.to_datetime(df['created_at'], errors="coerce", utc=True)
            oldest_record_time = df['created_at_dt'].min()
            if pd.isna(oldest_record_time) or oldest_record_time > target_oldest_time:
                needs_backfill = True
        
        if needs_backfill:
            logger.info(f"Backfilling data for {days_filter} days...")
            fetch_start = target_oldest_time.replace(tzinfo=None)
            fetch_end = datetime.now()
            
            results = self.fetch_data_from_api(fetch_start, fetch_end)
            if results["records"]:
                self.storage.save_data(results["records"])
                df = self.storage.load_data()
        
        if df.empty:
            return []

        df['created_at_dt'] = pd.to_datetime(df['created_at'], errors="coerce", utc=True)
        df = df.dropna(subset=["created_at_dt"])
        
        # Apply filters
        mask = df['created_at_dt'] >= target_oldest_time
        filtered_df = df[mask].copy()
            
        if source_filter and source_filter.lower() != 'todas':
            filtered_df = filtered_df[filtered_df['source'].str.lower() == source_filter.lower()]

        if influencer_filter and influencer_filter.lower() != 'todos':
            wants_influencer = influencer_filter.lower() in {"influencer", "influencers", "true", "si", "sí"}
            filtered_df = filtered_df[filtered_df["is_influencer"].apply(self._truthy) == wants_influencer]

        missing_ai_records = filtered_df[filtered_df["ai_sentiment"].fillna("") == ""].to_dict(orient="records")
        ai_results = self.ai_analyzer.analyze_missing(missing_ai_records)
        if ai_results:
            self._persist_ai_results(ai_results)
            for item_id, analysis in ai_results.items():
                item_mask = filtered_df["id"].astype(str) == str(item_id)
                for field, value in analysis.items():
                    filtered_df.loc[item_mask, field] = value

        if sentiment_filter and sentiment_filter.lower() != 'todos':
            sentiment = sentiment_filter.lower()
            effective_sentiment = filtered_df["ai_sentiment"].replace("", pd.NA).fillna(filtered_df["keepcon_sentiment"])
            if sentiment in {"no sentiment", "sin sentimiento"}:
                filtered_df = filtered_df[effective_sentiment.fillna("").str.lower().isin(["", "no sentiment", "unknown"])]
            else:
                filtered_df = filtered_df[effective_sentiment.fillna("").str.lower() == sentiment]
            
        # Sort
        filtered_df = filtered_df.sort_values(by='created_at_dt', ascending=False)
        
        # Relative time helper
        def relative_time(dt_str):
            try:
                dt = pd.to_datetime(dt_str)
                # Ensure dt is tz-aware for comparison if now is tz-aware
                if dt.tzinfo is None:
                    dt = pytz.utc.localize(dt)
                diff = now - dt
                if diff.days > 0:
                    return f"Hace {diff.days} día{'s' if diff.days > 1 else ''}"
                elif diff.seconds >= 3600:
                    hours = diff.seconds // 3600
                    return f"Hace {hours} hora{'s' if hours > 1 else ''}"
                elif diff.seconds >= 60:
                    minutes = diff.seconds // 60
                    return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
                else:
                    return "Hace unos segundos"
            except:
                return dt_str
                
        filtered_df['relative_time'] = filtered_df['created_at'].apply(relative_time)
        filtered_df = filtered_df.drop(columns=['created_at_dt'])
        filtered_df = filtered_df.fillna("")
        
        return filtered_df.to_dict(orient='records')

    def build_metrics(self, data):
        total = len(data)
        metrics = {
            "total": total,
            "negatives": self._count_sentiment(data, "ai_sentiment", "negative"),
            "positives": self._count_sentiment(data, "ai_sentiment", "positive"),
            "neutral": self._count_sentiment(data, "ai_sentiment", "neutral"),
            "no_sentiment": sum(1 for item in data if (item.get("ai_sentiment") or "").lower() in {"", "no sentiment", "unknown"}),
            "keepcon_negatives": self._count_sentiment(data, "keepcon_sentiment", "negative"),
            "keepcon_positives": self._count_sentiment(data, "keepcon_sentiment", "positive"),
            "keepcon_neutral": self._count_sentiment(data, "keepcon_sentiment", "neutral"),
            "keepcon_no_sentiment": sum(1 for item in data if (item.get("keepcon_sentiment") or "").lower() in {"", "no sentiment", "unknown"}),
            "sin_atender": self._count_status(data, "sin_atender"),
            "en_atencion": self._count_status(data, "en_atencion"),
            "cerrados": self._count_status(data, "cerrado"),
            "influencers": sum(1 for item in data if self._truthy(item.get("is_influencer"))),
            "with_ai_location": sum(1 for item in data if str(item.get("ai_location") or "").strip()),
        }

        source_aliases = {"twitter": "x", "facebook": "fb", "instagram": "ig"}
        metrics["status_by_source"] = {}
        for source, alias in source_aliases.items():
            source_items = [item for item in data if (item.get("source") or "").lower() == source]
            metrics[f"{alias}_mentions"] = len(source_items)
            metrics[f"{alias}_sin_atender"] = self._count_status(source_items, "sin_atender")
            metrics[f"{alias}_en_atencion"] = self._count_status(source_items, "en_atencion")
            metrics[f"{alias}_cerrados"] = self._count_status(source_items, "cerrado")
            metrics["status_by_source"][source] = {
                "total": len(source_items),
                "sin_atender": metrics[f"{alias}_sin_atender"],
                "en_atencion": metrics[f"{alias}_en_atencion"],
                "cerrados": metrics[f"{alias}_cerrados"],
            }

        metrics["executive"] = self._build_executive_metrics(data)
        metrics["sync"] = self._load_sync_state()
        return metrics

    def diagnose_content(self, content_id, created_at=None):
        created_dt = self._parse_datetime(created_at) if created_at else None
        if not created_dt:
            created_dt = self._find_created_at_for_content(content_id)
        if not created_dt:
            created_dt = datetime.now()

        created_from = created_dt - timedelta(minutes=30)
        created_to = created_dt + timedelta(minutes=30)
        updated_from = datetime.now() - timedelta(days=1)
        updated_to = datetime.now()

        diagnostics = {
            "content_id": content_id,
            "created_at": created_dt.isoformat(),
            "content_get": self._diagnose_get_content(content_id),
            "created_at_search": self._diagnose_search_content(
                {
                    "sources": ["twitter", "facebook", "instagram"],
                    "content_types": self.config.allowed_content_types,
                    "created_at_from": created_from.strftime("%Y-%m-%dT%H:%M:%S"),
                    "created_at_to": created_to.strftime("%Y-%m-%dT%H:%M:%S"),
                },
                content_id,
            ),
            "updated_at_search": self._diagnose_search_content(
                {
                    "sources": ["twitter", "facebook", "instagram"],
                    "content_types": self.config.allowed_content_types,
                    "updated_at_from": updated_from.strftime("%Y-%m-%dT%H:%M:%S"),
                    "updated_at_to": updated_to.strftime("%Y-%m-%dT%H:%M:%S"),
                },
                content_id,
            ),
        }
        return diagnostics

    def get_refresh_diagnostics(self, limit=10):
        if not os.path.exists(self.refresh_diagnostics_path):
            return []
        try:
            with open(self.refresh_diagnostics_path, "r", encoding="utf-8") as file_obj:
                lines = [line.strip() for line in file_obj if line.strip()]
            entries = []
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return entries
        except Exception as exc:
            logger.warning("Could not read Keepcon refresh diagnostics: %s", exc)
            return []

    def _count_sentiment(self, data, field, sentiment):
        return sum(1 for item in data if (item.get(field) or "").lower() == sentiment)

    def _count_status(self, data, status):
        return sum(1 for item in data if (item.get("attention_status") or "").lower() == status)

    def _truthy(self, value):
        return str(value).lower() in {"true", "1", "yes"}

    def _existing_profile_map(self):
        df = self.storage.load_data()
        if df.empty:
            return {}

        existing = {}
        profile_fields = [
            "profile_id",
            "profile_location",
            "profile_link",
            "followers_count",
            "is_influencer",
        ]
        for _, row in df.iterrows():
            key = (row.get("source"), row.get("social_user_id"))
            if not key[0] or not key[1] or key in existing:
                continue
            if not self._has_profile_data(row):
                continue
            existing[key] = {field: row.get(field, "") for field in profile_fields}
        return existing

    def _has_profile_data(self, row):
        return any(
            str(row.get(field, "") or "").strip()
            for field in ("profile_id", "profile_location", "profile_link", "followers_count")
        )

    def _profile_fields_from_row(self, row):
        return {
            "profile_id": row.get("profile_id", ""),
            "profile_location": row.get("profile_location", ""),
            "profile_link": row.get("profile_link", ""),
            "followers_count": row.get("followers_count", "0"),
            "is_influencer": self._truthy(row.get("is_influencer")),
        }

    def _should_fetch_profile(self, processed, raw_item, is_existing):
        if is_existing:
            return False
        user = (raw_item.get("content") or {}).get("user") or {}
        if user.get("followers") not in (None, ""):
            return False
        return self._is_high_risk_record(processed)

    def _is_high_risk_record(self, item):
        tags = self._parse_tags(item.get("tags"))
        tag_text = " ".join(tags).lower()
        risk_terms = ("neg", "reclamo", "internet", "facturacion", "facturación", "legal", "estafa", "atencion", "atención")
        return (
            str(item.get("ai_sentiment") or item.get("keepcon_sentiment") or item.get("sentiment") or "").lower() == "negative"
            or any(term in tag_text for term in risk_terms)
        )

    def _count_mutable_updates(self, existing_by_id, results):
        mutable_fields = {
            "review_status",
            "moderation_decision",
            "last_operator",
            "last_operation_date",
            "updated_at",
            "attention_status",
            "followers_count",
            "is_influencer",
        }
        updated_count = 0
        for item in results:
            previous = existing_by_id.get(str(item.get("id")))
            if previous is None:
                continue
            for field in mutable_fields:
                old_value = str(previous.get(field, "") or "")
                new_value = str(item.get(field, "") or "")
                if old_value != new_value:
                    updated_count += 1
                    break
        return updated_count

    def _count_update_types(self, existing_by_id, results):
        status_fields = {"review_status", "moderation_decision", "last_operator", "last_operation_date", "attention_status"}
        profile_fields = {"followers_count", "is_influencer"}
        metadata_fields = {"updated_at"}
        counts = {"status_updates": 0, "metadata_updates": 0, "profile_updates": 0}
        for item in results:
            previous = existing_by_id.get(str(item.get("id")))
            if previous is None:
                continue
            changed_status = self._changed_any(previous, item, status_fields)
            changed_profile = self._changed_any(previous, item, profile_fields)
            changed_metadata = self._changed_any(previous, item, metadata_fields)
            if changed_status:
                counts["status_updates"] += 1
            if changed_profile:
                counts["profile_updates"] += 1
            if changed_metadata and not changed_status and not changed_profile:
                counts["metadata_updates"] += 1
        return counts

    def _changed_any(self, previous, item, fields):
        for field in fields:
            old_value = str(previous.get(field, "") or "")
            new_value = str(item.get(field, "") or "")
            if old_value != new_value:
                return True
        return False

    def _merge_records(self, *record_groups):
        merged = {}
        for records in record_groups:
            for record in records:
                if record.get("id"):
                    merged[str(record["id"])] = record
        return list(merged.values())

    def _empty_ai_analysis(self):
        return {
            "results": {},
            "stats": {
                "pending_records": 0,
                "chunks": 0,
                "analyzed_records": 0,
                "duration_ms": 0,
            },
        }

    def _analyze_records(self, records):
        missing_ai = [item for item in records if not item.get("ai_sentiment")]
        ai_analysis = self.ai_analyzer.analyze_missing_with_stats(missing_ai)
        ai_results = ai_analysis["results"]
        for item in records:
            item_id = str(item.get("id") or "")
            if item_id in ai_results:
                item.update(ai_results[item_id])
        return ai_analysis

    def _append_refresh_diagnostics(self, response):
        try:
            os.makedirs(os.path.dirname(self.refresh_diagnostics_path), exist_ok=True)
            entry = {
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "new_records": response.get("new_records", 0),
                "updated_records": response.get("updated_records", 0),
                "fetched_records": response.get("fetched_records", 0),
                "created_pages": response.get("created_pages", 0),
                "updated_pages": response.get("updated_pages", 0),
                "profile_calls": response.get("profile_calls", 0),
                "duration_ms": response.get("duration_ms", 0),
                "diagnostics": response.get("diagnostics", {}),
            }
            with open(self.refresh_diagnostics_path, "a", encoding="utf-8") as file_obj:
                file_obj.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("Could not append Keepcon refresh diagnostics: %s", exc)

    def _persist_ai_results(self, ai_results):
        if not ai_results:
            return
        df = self.storage.load_data()
        if df.empty:
            return
        for item_id, analysis in ai_results.items():
            mask = df["id"].astype(str) == str(item_id)
            for field, value in analysis.items():
                df.loc[mask, field] = value
        self.storage.save_data(df.to_dict(orient="records"))

    def _find_created_at_for_content(self, content_id):
        df = self.storage.load_data()
        if df.empty:
            return None
        matches = df[df["id"].astype(str) == str(content_id)]
        if matches.empty:
            return None
        return self._parse_datetime(matches.iloc[0].get("created_at"))

    def _parse_datetime(self, value):
        try:
            parsed = pd.to_datetime(value, errors="coerce", utc=True)
            if pd.isna(parsed):
                return None
            return parsed.to_pydatetime().replace(tzinfo=None)
        except Exception:
            return None

    def _load_sync_state(self):
        if not os.path.exists(self.sync_state_path):
            return {}
        try:
            with open(self.sync_state_path, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_sync_state(self, state):
        os.makedirs(os.path.dirname(self.sync_state_path), exist_ok=True)
        with open(self.sync_state_path, "w", encoding="utf-8") as file_obj:
            json.dump(state, file_obj, indent=2, ensure_ascii=False)

    def _parse_tags(self, value):
        if isinstance(value, list):
            return [str(item) for item in value]
        try:
            parsed = json.loads(value or "[]")
            return [str(item) for item in parsed] if isinstance(parsed, list) else []
        except Exception:
            return [part.strip() for part in str(value or "").split(",") if part.strip()]

    def _build_executive_metrics(self, data):
        total = len(data)
        negative_items = [item for item in data if (item.get("ai_sentiment") or "").lower() == "negative"]
        negative_rate = round((len(negative_items) / total) * 100) if total else 0
        critical_tags = {
            "internet": ("internet", "producto_internet"),
            "atencion": ("atencion", "atención", "respuesta", "resolucion", "resolución"),
            "facturacion": ("facturacion", "facturación", "cobro"),
            "legal": ("legal", "estafa"),
            "imagen": ("imageninstitucional", "credibilidad"),
        }
        tag_counts = {key: 0 for key in critical_tags}
        all_tags = []
        for item in data:
            tags = self._parse_tags(item.get("tags"))
            all_tags.extend(tags)
            tag_text = " ".join(tags).lower()
            for key, terms in critical_tags.items():
                if any(term in tag_text for term in terms):
                    tag_counts[key] += 1

        user_counts = {}
        for item in negative_items:
            username = item.get("username") or item.get("user_name") or "usuario"
            key = (username, item.get("source") or "", item.get("followers_count") or "0")
            user_counts[key] = user_counts.get(key, 0) + 1
        repeated_negative_users = [
            {"username": user, "source": source, "followers_count": followers, "negative_mentions": count}
            for (user, source, followers), count in sorted(user_counts.items(), key=lambda entry: entry[1], reverse=True)
            if count >= 2
        ][:5]

        negative_influencers = [
            {
                "username": item.get("username") or item.get("user_name") or "usuario",
                "source": item.get("source") or "",
                "followers_count": item.get("followers_count") or "0",
                "text": item.get("text") or "",
            }
            for item in negative_items
            if self._truthy(item.get("is_influencer"))
        ][:5]

        by_source_sentiment = {}
        for source in ("twitter", "facebook", "instagram"):
            source_items = [item for item in data if (item.get("source") or "").lower() == source]
            by_source_sentiment[source] = {
                "total": len(source_items),
                "negative": sum(1 for item in source_items if (item.get("ai_sentiment") or "").lower() == "negative"),
                "neutral": sum(1 for item in source_items if (item.get("ai_sentiment") or "").lower() == "neutral"),
                "positive": sum(1 for item in source_items if (item.get("ai_sentiment") or "").lower() == "positive"),
                "no_sentiment": sum(1 for item in source_items if (item.get("ai_sentiment") or "").lower() in {"", "no sentiment", "unknown"}),
            }

        return {
            "negative_rate": negative_rate,
            "risk_active": len(negative_items),
            "negative_influencers_count": len(negative_influencers),
            "negative_influencers": negative_influencers,
            "repeated_negative_users": repeated_negative_users,
            "critical_tags": tag_counts,
            "by_source_sentiment": by_source_sentiment,
        }

    def _diagnose_get_content(self, content_id):
        item = self.client.get_content(content_id)
        return {
            "error": self.client.last_error if not item else "",
            "item": self._safe_content_fields(item) if item else None,
        }

    def _diagnose_search_content(self, payload, content_id):
        items = []
        errors = []
        next_page_token = None
        pages = 0
        while True:
            response_data = self.client.search_content_payload(payload, next_page_token)
            pages += 1
            if response_data is None:
                errors.append(self.client.last_error)
                break
            page_items = self.processor.parse_api_response(response_data)
            items.extend(page_items)
            next_page_token = response_data.get("next_page_token") if isinstance(response_data, dict) else None
            if not next_page_token:
                break

        matches = [item for item in items if str(item.get("id")) == str(content_id)]
        return {
            "payload": payload,
            "pages": pages,
            "items_found": len(items),
            "matches_found": len(matches),
            "errors": errors,
            "matches": [self._safe_content_fields(item) for item in matches[:5]],
        }

    def _safe_content_fields(self, item):
        if not item:
            return {}
        processed = self.processor.process_item(item)
        keys = [
            "id",
            "source",
            "content_type",
            "sentiment",
            "review_status",
            "moderation_decision",
            "last_operator",
            "last_operation_date",
            "updated_at",
            "status",
            "ticket",
            "case",
            "attention",
        ]
        content = item.get("content") or {}
        user = content.get("user") or {}
        return {
            "fields": {key: item.get(key) for key in keys if key in item},
            "available_keys": sorted(item.keys()),
            "content": {
                "createdat": content.get("createdat"),
                "username": user.get("username"),
                "text": content.get("text"),
            },
            "derived_attention_status": (processed or {}).get("attention_status", ""),
        }
