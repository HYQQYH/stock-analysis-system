import pandas as pd
import pytest

from app.services.data_collector import DataCollector


def test_data_collector_methods_exist():
    dc = DataCollector(retry=1, backoff=0.1)
    assert hasattr(dc, "fetch_kline_data")
    assert hasattr(dc, "fetch_limit_up_pool")
    assert hasattr(dc, "fetch_market_fund_flow")
    assert hasattr(dc, "fetch_market_sentiment")


def test_call_with_retry_raises_on_failure():
    dc = DataCollector(retry=2, backoff=0.01)

    def fail_func(*a, **k):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        dc._call_with_retry(fail_func)


def test_fetch_kline_coerce_to_dataframe(monkeypatch):
    dc = DataCollector(retry=1, backoff=0.01)

    def fake_hist(symbol=None, **kwargs):
        return {"日期": ["2026-01-01"], "开盘": [10.0], "收盘": [10.5]}

    monkeypatch.setattr("akshare.stock_zh_a_hist", fake_hist, raising=False)

    df = dc.fetch_kline_data("600000")
    assert isinstance(df, pd.DataFrame)
