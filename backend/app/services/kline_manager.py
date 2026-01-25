"""K-line data manager: cache-first strategy with Redis and persistence to DB."""
from typing import Optional, List
import logging
import hashlib

import pandas as pd

from app.db.redis_cache import get_redis_client, cache_key_builder
from app.db.database import SessionLocal
from app.models.models import StockKlineData, KlineTypeEnum

logger = logging.getLogger(__name__)


DEFAULT_TTL = 60 * 60 * 24  # 24 hours


def _df_to_dictlist(df: pd.DataFrame) -> List[dict]:
    return df.reset_index().to_dict(orient="records")


def _hash_input(code: str, period: str, data: pd.DataFrame) -> str:
    payload = f"{code}:{period}:{len(data)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class KlineManager:
    def __init__(self, redis_ttl: int = DEFAULT_TTL):
        self.redis = get_redis_client()
        self.redis_ttl = redis_ttl

    def cache_kline_data(self, code: str, period: str, data: pd.DataFrame) -> bool:
        key = cache_key_builder("kline", code, f"period:{period}")
        try:
            payload = _df_to_dictlist(data)
            meta = {"hash": _hash_input(code, period, data), "count": len(payload)}
            stored = {"meta": meta, "data": payload}
            return self.redis.set_json(key, stored, ttl=self.redis_ttl)
        except Exception as e:
            logger.error("Failed to cache kline data for %s: %s", code, e)
            return False

    def save_kline_to_db(self, code: str, period: str, data: pd.DataFrame) -> int:
        """Persist k-line data to DB. Returns number of rows upserted."""
        session = SessionLocal()
        upserted = 0
        try:
            # Normalize column names to expected ones
            df = data.copy()
            # Try common column names mapping
            col_map = {}
            for c in df.columns:
                lc = c.lower()
                if "date" in lc or "日期" in lc:
                    col_map[c] = "trade_date"
                elif "open" in lc or "开" in lc:
                    col_map[c] = "open_price"
                elif "high" in lc or "高" in lc:
                    col_map[c] = "high_price"
                elif "low" in lc or "低" in lc:
                    col_map[c] = "low_price"
                elif "close" in lc or "收" in lc:
                    col_map[c] = "close_price"
                elif "volume" in lc or "成交量" in lc:
                    col_map[c] = "volume"
                elif "amount" in lc or "金额" in lc:
                    col_map[c] = "amount"
            df = df.rename(columns=col_map)

            for _, row in df.iterrows():
                kwargs = dict(
                    stock_code=code,
                    kline_type=period if period in KlineTypeEnum.__members__ else period,
                    trade_date=row.get("trade_date"),
                    open_price=row.get("open_price", 0.0) or 0.0,
                    high_price=row.get("high_price", 0.0) or 0.0,
                    low_price=row.get("low_price", 0.0) or 0.0,
                    close_price=row.get("close_price", 0.0) or 0.0,
                    volume=int(row.get("volume") or 0),
                    amount=float(row.get("amount") or 0.0),
                    percentage_change=float(row.get("pct_chg") or 0.0) if "pct_chg" in row else 0.0,
                    turnover=float(row.get("turnover") or 0.0),
                )

                # Check existence
                exists = session.query(StockKlineData).filter_by(
                    stock_code=code, trade_date=kwargs["trade_date"], kline_type=kwargs["kline_type"]
                ).first()
                if exists:
                    # update fields
                    for k, v in kwargs.items():
                        setattr(exists, k, v)
                else:
                    obj = StockKlineData(**kwargs)
                    session.add(obj)
                upserted += 1

            session.commit()
            return upserted
        except Exception as e:
            session.rollback()
            logger.error("Failed to save kline to DB for %s: %s", code, e)
            raise
        finally:
            session.close()

    def get_kline_data(self, code: str, period: str, days: Optional[int] = None) -> pd.DataFrame:
        key = cache_key_builder("kline", code, f"period:{period}")
        try:
            cached = self.redis.get_json(key)
            if cached and "data" in cached:
                df = pd.DataFrame(cached["data"])
                if days:
                    df = df.tail(days)
                return df
        except Exception:
            logger.warning("Failed to read from Redis, falling back to DB for %s", code)

        # Fallback to DB
        session = SessionLocal()
        try:
            q = session.query(StockKlineData).filter_by(stock_code=code, kline_type=period).order_by(StockKlineData.trade_date.desc())
            if days:
                q = q.limit(days)
            rows = q.all()
            if not rows:
                return pd.DataFrame()
            records = [
                {
                    "trade_date": r.trade_date,
                    "open_price": r.open_price,
                    "high_price": r.high_price,
                    "low_price": r.low_price,
                    "close_price": r.close_price,
                    "volume": r.volume,
                    "amount": r.amount,
                }
                for r in rows
            ]
            return pd.DataFrame(records)
        finally:
            session.close()
