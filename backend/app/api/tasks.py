"""API endpoints to trigger scheduled data collection tasks manually."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.tasks import runner

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/collect/market-summary", summary="Collect market summary now")
def collect_market_summary():
    try:
        runner.collect_market_summary()
        return JSONResponse(status_code=200, content={"status": "ok", "task": "market_summary"})
    except Exception as e:
        logger.exception("collect_market_summary failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/limit-up", summary="Collect limit-up pool now")
def collect_limit_up():
    try:
        runner.collect_limit_up_pool()
        return {"status": "ok", "task": "limit_up"}
    except Exception as e:
        logger.exception("collect_limit_up failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/index-kline", summary="Collect index kline now")
def collect_index_kline():
    try:
        runner.collect_index_kline()
        return {"status": "ok", "task": "index_kline"}
    except Exception as e:
        logger.exception("collect_index_kline failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/cleanup", summary="Run cache cleanup now")
def cache_cleanup():
    try:
        runner.clean_expired_cache()
        return {"status": "ok", "task": "cache_cleanup"}
    except Exception as e:
        logger.exception("cache_cleanup failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/persist/klines", summary="Persist cached klines now")
def persist_klines():
    try:
        runner.persist_cached_klines()
        return {"status": "ok", "task": "persist_klines"}
    except Exception as e:
        logger.exception("persist_klines failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
