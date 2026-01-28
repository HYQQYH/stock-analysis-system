"""
Market-related API Routes
"""
import akshare as ak
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta

from app.schemas.market import (
    MarketIndexData,
    MarketSentiment,
    FundFlowData,
    LimitUpStock,
    MarketActivity
)
from app.schemas.common import ApiResponse, HttpStatus
from app.services.indicator_calculator import IndicatorCalculator

router = APIRouter(prefix="/api/v1/market", tags=["Market"])
indicator_calculator = IndicatorCalculator()


@router.get("/index", response_model=ApiResponse[dict])
async def get_market_index(
    kline_type: str = Query("day", description="K-line type: day/week/month"),
    days: int = Query(60, ge=1, le=365, description="Number of days")
):
    """
    Get Shanghai Composite Index (上证指数) data
    
    - **kline_type**: K-line type - day/week/month
    - **days**: Number of days to retrieve
    """
    try:
        # Map kline_type to akshare period
        period_map = {
            "day": "daily",
            "week": "weekly",
            "month": "monthly"
        }
        period = period_map.get(kline_type.lower(), "daily")
        
        # Calculate date range
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        # Fetch Shanghai Composite Index data (000001)
        df = ak.stock_zh_index_daily(
            symbol="sh000001",
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            return ApiResponse(
                code=HttpStatus.OK,
                message="未找到大盘数据",
                data=None
            )
        
        # Convert DataFrame to list of MarketIndexData
        index_data = []
        for _, row in df.iterrows():
            index_point = MarketIndexData(
                trade_date=row.get('date'),
                open_price=float(row.get('open', 0)),
                high_price=float(row.get('high', 0)),
                low_price=float(row.get('low', 0)),
                close_price=float(row.get('close', 0)),
                volume=int(row.get('volume', 0)),
                amount=float(row.get('amount', 0))
            )
            index_data.append(index_point)
        
        # Sort by date descending
        index_data.sort(key=lambda x: x.trade_date, reverse=True)
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data={
                "index_code": "000001",
                "index_name": "上证指数",
                "kline_type": kline_type,
                "data": index_data
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取大盘数据失败: {str(e)}"
        )


@router.get("/sentiment", response_model=ApiResponse[MarketSentiment])
async def get_market_sentiment(
    date: str = Query(None, description="Date in YYYYMMDD format (default: latest)")
):
    """
    Get market sentiment data
    
    - **date**: Optional date in YYYYMMDD format
    """
    try:
        # Set default date to today
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        # Fetch market activity data
        df = ak.stock_market_activity_legu()
        
        if df.empty:
            return ApiResponse(
                code=HttpStatus.OK,
                message="未找到市场情绪数据",
                data=None
            )
        
        # Convert DataFrame to dictionary
        activity_data = df.set_index('item')['value'].to_dict()
        
        # Calculate sentiment score
        rise_count = int(activity_data.get('上涨', 0))
        fall_count = int(activity_data.get('下跌', 0))
        flat_count = int(activity_data.get('平盘', 0))
        total_count = rise_count + fall_count + flat_count
        
        sentiment_score = (rise_count / total_count * 100) if total_count > 0 else 50
        bull_bear_ratio = (rise_count / fall_count) if fall_count > 0 else 0
        
        # Create sentiment data
        sentiment = MarketSentiment(
            trade_date=datetime.strptime(date, "%Y%m%d").date(),
            index_code="000001",
            sentiment_score=round(sentiment_score, 2),
            bull_bear_ratio=round(bull_bear_ratio, 2),
            rise_fall_count={
                "rise": rise_count,
                "fall": fall_count,
                "flat": flat_count
            },
            volume_ratio=None  # TODO: Calculate from actual volume data
        )
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=sentiment
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取市场情绪数据失败: {str(e)}"
        )


@router.get("/fund-flow", response_model=ApiResponse[FundFlowData])
async def get_market_fund_flow(
    date: str = Query(None, description="Date in YYYYMMDD format (default: latest)")
):
    """
    Get market fund flow data
    
    - **date**: Optional date in YYYYMMDD format
    """
    try:
        # Fetch fund flow data
        df = ak.stock_market_fund_flow()
        
        if df.empty:
            return ApiResponse(
                code=HttpStatus.OK,
                message="未找到资金流向数据",
                data=None
            )
        
        # Get the latest data or specific date
        if date:
            # Find data for specific date
            df_filtered = df[df['日期'] == date]
            if df_filtered.empty:
                raise HTTPException(
                    status_code=HttpStatus.NOT_FOUND,
                    detail=f"未找到日期为 {date} 的资金流向数据"
                )
            latest_data = df_filtered.iloc[0]
        else:
            # Get latest data
            latest_data = df.iloc[0]
        
        # Create fund flow data
        fund_flow = FundFlowData(
            trade_date=latest_data.get('日期'),
            sh_close_price=latest_data.get('上证-收盘价'),
            sh_change_pct=latest_data.get('上证-涨跌幅'),
            sz_close_price=latest_data.get('深证-收盘价'),
            sz_change_pct=latest_data.get('深证-涨跌幅'),
            main_net_inflow=latest_data.get('主力净流入-净额'),
            main_net_inflow_ratio=latest_data.get('主力净流入-净占比'),
            super_large_net_inflow=latest_data.get('超大单净流入-净额'),
            super_large_net_inflow_ratio=latest_data.get('超大单净流入-净占比'),
            large_net_inflow=latest_data.get('大单净流入-净额'),
            large_net_inflow_ratio=latest_data.get('大单净流入-净占比'),
            medium_net_inflow=latest_data.get('中单净流入-净额'),
            medium_net_inflow_ratio=latest_data.get('中单净流入-净占比'),
            small_net_inflow=latest_data.get('小单净流入-净额'),
            small_net_inflow_ratio=latest_data.get('小单净流入-净占比')
        )
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=fund_flow
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取资金流向数据失败: {str(e)}"
        )


@router.get("/limit-up", response_model=ApiResponse[dict])
async def get_limit_up_pool(
    date: str = Query(None, description="Date in YYYYMMDD format (default: today)")
):
    """
    Get limit-up stock pool (涨停股池)
    
    - **date**: Optional date in YYYYMMDD format
    """
    try:
        # Set default date to today
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        # Fetch limit-up stock pool
        df = ak.stock_zt_pool_em(date=date)
        
        if df.empty:
            return ApiResponse(
                code=HttpStatus.OK,
                message=f"未找到日期为 {date} 的涨停股池",
                data={
                    "trade_date": datetime.strptime(date, "%Y%m%d").date(),
                    "stocks": []
                }
            )
        
        # Convert DataFrame to list of LimitUpStock
        limit_up_stocks = []
        for _, row in df.iterrows():
            stock = LimitUpStock(
                stock_code=row.get('代码'),
                stock_name=row.get('名称'),
                change_pct=row.get('涨跌幅'),
                latest_price=row.get('最新价'),
                turnover_amount=row.get('成交额'),
                circulation_market_value=row.get('流通市值'),
                total_market_value=row.get('总市值'),
                turnover_rate=row.get('换手率'),
                limit_up_funds=row.get('封单资金'),
                first_limit_time=row.get('首次封板时间'),
                last_limit_time=row.get('最后封板时间'),
                burst_count=row.get('炸板次数'),
                limit_up_stats=row.get('涨停统计'),
                continuous_limit_count=row.get('连板数'),
                industry=row.get('所属行业')
            )
            limit_up_stocks.append(stock)
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data={
                "trade_date": datetime.strptime(date, "%Y%m%d").date(),
                "total_count": len(limit_up_stocks),
                "stocks": limit_up_stocks
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取涨停股池失败: {str(e)}"
        )