from typing import Optional

from fastapi import APIRouter, Query

from src.services.scrapebadger import ScrapebadgerService

router = APIRouter()
service = ScrapebadgerService()


@router.get("/data")
def get_scrapebadger_data(
    sentiment: Optional[str] = Query(None, description="Filtro de sentimiento"),
    account: Optional[str] = Query(None, description="Filtro de cuenta mencionada"),
    location: Optional[str] = Query(None, description="Filtro de ubicacion"),
):
    try:
        data = service.get_dashboard_data(
            sentiment_filter=sentiment,
            account_filter=account,
            location_filter=location,
        )
        filters = service.available_filters()
        metrics = {
            "total": len(data),
            "negatives": sum(1 for item in data if item.get("sentiment") == "negative"),
            "positives": sum(1 for item in data if item.get("sentiment") == "positive"),
            "neutral": sum(1 for item in data if item.get("sentiment") == "neutral"),
            "no_sentiment": sum(
                1
                for item in data
                if item.get("sentiment") in ("", "no sentiment", "unknown")
            ),
            "with_location": sum(
                1
                for item in data
                if item.get("place_full_name") or item.get("place_name") or item.get("user_location")
            ),
        }
        return {"status": "success", "metrics": metrics, "filters": filters, "data": data}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "metrics": {}, "filters": {}, "data": []}


@router.post("/refresh")
def refresh_scrapebadger_data():
    try:
        result = service.refresh_latest()
        status = "error" if result.get("status_code") else "success"
        return {"status": status, **result}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
