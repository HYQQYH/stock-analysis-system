"""Data collection service wrapping akshare calls"""
from typing import Optional
import logging
import time

import pandas as pd

import akshare as ak

logger = logging.getLogger(__name__)


class DataCollector:
    """Wrapper around akshare data access with simple retry handling."""

    def __init__(self, retry: int = 3, backoff: float = 1.0):
        self.retry = retry
        self.backoff = backoff

    def _call_with_retry(self, func, *args, **kwargs):
        last_exc = None
        for i in range(self.retry):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                logger.warning("akshare call failed (attempt %s/%s): %s", i + 1, self.retry, e)
                time.sleep(self.backoff * (i + 1))
        logger.error("akshare call failed after %s attempts: %s", self.retry, last_exc)
        raise last_exc

    def fetch_kline_data(self, code: str, period: str = "daily", start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """Fetch K-line (historical) data for a stock or index.

        code: stock code like '600000' or index like 'sh000001'
        period: currently supports 'daily', 'weekly', 'monthly'
        start/end: optional date strings accepted by akshare
        """
        # Map period to akshare function parameters if needed
        try:
            if period in ("daily", "day"):
                df = self._call_with_retry(ak.stock_zh_a_hist, symbol=code, start_date=start, end_date=end)
            elif period in ("weekly", "week"):
                df = self._call_with_retry(ak.stock_zh_a_hist, symbol=code, adjust="qfq", period="weekly")
            elif period in ("monthly", "month"):
                df = self._call_with_retry(ak.stock_zh_a_hist, symbol=code, adjust="qfq", period="monthly")
            else:
                raise ValueError("Unsupported period: %s" % period)
        except TypeError:
            # Some akshare versions have different signatures; try generic call
            df = self._call_with_retry(ak.stock_zh_a_hist, code)

        if not isinstance(df, pd.DataFrame):
            # Try to coerce
            df = pd.DataFrame(df)
        return df

    def fetch_limit_up_pool(self) -> pd.DataFrame:
        """Fetch today's limit-up stock pool."""
        df = self._call_with_retry(ak.stock_zt_pool_em)
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
        return df

    def fetch_market_fund_flow(self) -> pd.DataFrame:
        """Fetch market fund flow data."""
        df = self._call_with_retry(ak.stock_market_fund_flow)
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
        return df

    def fetch_market_sentiment(self) -> pd.DataFrame:
        """A simple wrapper to collect market sentiment related series.

        This may combine multiple akshare endpoints in the future.
        """
        # For now return fund flow as a proxy
        return self.fetch_market_fund_flow()
