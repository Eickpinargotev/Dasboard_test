import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.api.routers import keepcon_router, scrapebadger_router
from src.services.keepcon import KeepconService
from src.services.scrapebadger import ScrapebadgerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Claro Social Dashboard API",
    description="API for Keepcon Integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(keepcon_router.router, prefix="/api/v1/keepcon", tags=["Keepcon"])
app.include_router(scrapebadger_router.router, prefix="/api/v1/scrapebadger", tags=["Scrapebadger"])

@app.on_event("startup")
def start_scheduler():
    import os
    scheduler = BackgroundScheduler()
    keepcon_service = KeepconService()
    scrapebadger_service = ScrapebadgerService()
    
    interval_seconds = int(os.getenv("REFRESH_INTERVAL_SECONDS", 300))
    scrapebadger_interval_seconds = int(os.getenv("SCRAPEBADGER_REFRESH_INTERVAL_SECONDS", 86400))
    
    # Run the refresh job based on environment variable
    scheduler.add_job(
        func=keepcon_service.refresh_latest,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id='keepcon_refresh_job',
        name=f'Fetch latest Keepcon data every {interval_seconds} seconds',
        replace_existing=True
    )
    scheduler.add_job(
        func=scrapebadger_service.refresh_latest,
        trigger=IntervalTrigger(seconds=scrapebadger_interval_seconds),
        id='scrapebadger_refresh_job',
        name=f'Fetch latest Scrapebadger data every {scrapebadger_interval_seconds} seconds',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Background scheduler started. Keepcon will refresh every {interval_seconds} seconds.")
    logger.info(
        "Background scheduler started. Scrapebadger will refresh every %s seconds.",
        scrapebadger_interval_seconds,
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "keepcon-dashboard"}
