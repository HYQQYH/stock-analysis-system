"""Scheduled data collection tasks using APScheduler."""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from app.services.data_collector import DataCollector
from app.services.kline_manager import KlineManager
from app.db.redis_cache import get_redis_client

logger = logging.getLogger(__name__)


class TaskRunner:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.collector = DataCollector()
        self.kmanager = KlineManager()
        self.redis = get_redis_client()
        self.executor = ThreadPoolExecutor(max_workers=4)


    def collect_market_summary(self):
        logger.info("Running market summary collection at %s", datetime.utcnow())
        try:
            fund_flow = self.collector.fetch_market_fund_flow()
            # Cache fund flow
            self.redis.set_json("market:fund_flow", {"data": fund_flow.reset_index().to_dict(orient="records")}, ttl=60 * 60 * 24)
            logger.info("Market fund flow cached, rows=%s", len(fund_flow) if hasattr(fund_flow, 'shape') else 0)

            sentiment = self.collector.fetch_market_sentiment()
            self.redis.set_json("market:sentiment", {"data": sentiment.reset_index().to_dict(orient="records")}, ttl=60 * 60 * 24)
        except Exception as e:
            logger.exception("Market summary collection failed: %s", e)

    def collect_limit_up_pool(self):
        logger.info("Collecting limit-up pool at %s", datetime.utcnow())
        try:
            pool = self.collector.fetch_limit_up_pool()
            self.redis.set_json("market:limit_up", {"data": pool.reset_index().to_dict(orient="records")}, ttl=60 * 60 * 24)
            logger.info("Limit-up pool cached, rows=%s", len(pool) if hasattr(pool, 'shape') else 0)
        except Exception as e:
            logger.exception("Limit-up pool collection failed: %s", e)

    def collect_index_kline(self):
        logger.info("Collecting index kline at %s", datetime.utcnow())
        try:
            # example: sh index '000001' in akshare may be represented differently; attempt common codes
            df = self.collector.fetch_kline_data("000001", period="daily")
            # cache index kline
            self.redis.set_json("market:sh_index:kline", {"data": df.reset_index().to_dict(orient="records")}, ttl=60 * 60 * 24)
            logger.info("Index kline cached, rows=%s", len(df) if hasattr(df, 'shape') else 0)
        except Exception as e:
            logger.exception("Index kline collection failed: %s", e)

    def clean_expired_cache(self):
        logger.info("Running cache cleanup at %s", datetime.utcnow())
        try:
            # In this simple implementation we do not scan TTLs; provide a pattern delete hook
            removed = self.redis.delete_pattern("kline:*:old*")
            logger.info("Cache cleanup removed keys: %s", removed)
        except Exception:
            logger.exception("Cache cleanup failed")

    def persist_cached_klines(self):
        """Scan cached kline keys and persist them to DB asynchronously."""
        logger.info("Persisting cached klines to DB at %s", datetime.utcnow())
        try:
            keys = self.redis.client.keys("kline:*")
            if not keys:
                logger.info("No cached klines found to persist")
                return

            futures = []
            for key in keys:
                try:
                    cached = self.redis.get_json(key)
                    if not cached or "data" not in cached:
                        continue
                    df = pd.DataFrame(cached.get("data"))
                    # Submit save job
                    fut = self.executor.submit(self.kmanager.save_kline_to_db, key.split(":")[1], key.split(":")[2].replace('period:', ''), df)
                    futures.append((key, fut))
                except Exception:
                    logger.exception("Failed to schedule persist for key %s", key)

            for key, fut in futures:
                try:
                    result = fut.result(timeout=30)
                    logger.info("Persisted key %s rows=%s", key, result)
                    # mark persisted
                    try:
                        self.redis.set_json(f"{key}:persisted", {"rows": result})
                    except Exception:
                        logger.exception("Failed to mark persisted for %s", key)
                except Exception:
                    logger.exception("Persist task for %s failed", key)

        except Exception:
            logger.exception("persist_cached_klines failed")

    def schedule_jobs(self):
        # Daily after market close 17:00 collect index, sentiment, limit-up
        self.scheduler.add_job(self.collect_market_summary, CronTrigger(hour=17, minute=0))
        self.scheduler.add_job(self.collect_limit_up_pool, CronTrigger(hour=17, minute=0))
        # Persist cached klines every minute (configurable)
        self.scheduler.add_job(self.persist_cached_klines, 'interval', minutes=1)
        # 17:30 collect additional per-stock basics (not implemented here)
        # Daily 09:30 cleanup cache
        self.scheduler.add_job(self.clean_expired_cache, CronTrigger(hour=9, minute=30))

    def start(self):
        self.schedule_jobs()
        self.scheduler.start()
        logger.info("Task scheduler started")

    def shutdown(self):
        self.scheduler.shutdown(wait=False)
        logger.info("Task scheduler stopped")


runner = TaskRunner()

def start_scheduler():
    runner.start()

def stop_scheduler():
    runner.shutdown()
