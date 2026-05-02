"""
Stock-related API Routes
"""
import akshare as ak
from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime, timedelta

from app.schemas.stocks import (
    StockSearchRequest,
    StockSearchResponse,
    StockInfo,
    StockKlineResponse,
    StockIndicatorsResponse,
    StockCompanyInfo
)
from app.schemas.common import ApiResponse, ErrorCode, HttpStatus
from app.services.indicator_calculator import IndicatorCalculator

router = APIRouter(prefix="/stocks", tags=["Stocks"])
indicator_calculator = IndicatorCalculator()


@router.post("/search", response_model=ApiResponse[StockSearchResponse])
async def search_stocks(request: StockSearchRequest):
    """
    Search for stocks by code or name
    
    - **keyword**: Stock code (6 digits) or stock name
    """
    try:
        search_term = request.keyword
        
        if not search_term:
            return ApiResponse(
                code=HttpStatus.BAD_REQUEST,
                message="必须提供搜索关键词",
                data=None
            )
        
        # TODO: Implement actual search logic from database or data source
        # For now, return mock data
        # In production, this would query the stock_info table or use akshare
        
        # Check if search term is a 6-digit stock code
        if search_term.isdigit() and len(search_term) == 6:
            # It's a stock code
            code = search_term
            exchange = "SH" if code.startswith("6") else "SZ"
            
            # TODO: Fetch real stock info from database
            mock_stock = StockInfo(
                stock_code=code,
                stock_name=f"股票{code}",
                exchange=exchange,
                industry="未知",
                listing_date=None
            )
            return ApiResponse(
                code=0,
                message="success",
                data=StockSearchResponse(stocks=[mock_stock])
            )
        else:
            # It's a stock name - search logic would go here
            # For now, return empty list
            return ApiResponse(
                code=0,
                message="success",
                data=StockSearchResponse(stocks=[])
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"搜索股票失败: {str(e)}"
        )


@router.get("/{code}/kline", response_model=ApiResponse[StockKlineResponse])
async def get_stock_kline(
    code: str,
    kline_type: str = Query("day", description="K-line type: day/week/month"),
    start_date: str = Query(None, description="Start date (YYYYMMDD)"),
    end_date: str = Query(None, description="End date (YYYYMMDD)")
):
    """
    Get stock K-line data
    
    - **code**: Stock code (6 digits)
    - **kline_type**: K-line type - day/week/month
    - **start_date**: Optional start date in YYYYMMDD format
    - **end_date**: Optional end date in YYYYMMDD format
    """
    try:
        # Validate stock code
        if len(code) != 6 or not code.isdigit():
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="股票代码格式错误，应为6位数字"
            )
        
        # Map kline_type to akshare period
        period_map = {
            "day": "daily",
            "week": "weekly",
            "month": "monthly"
        }
        period = period_map.get(kline_type.lower(), "daily")
        
        # Set default date range (last 60 days)
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
        
        # Fetch K-line data from akshare
        df = ak.stock_zh_a_hist(
            symbol=code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
        
        if df.empty:
            return ApiResponse(
                code=HttpStatus.OK,
                message="未找到K线数据",
                data=None
            )
        
        # Convert DataFrame to list of KlineData
        from app.schemas.stocks import KlineData
        kline_data = []
        for _, row in df.iterrows():
            kline = KlineData(
                trade_date=row.get('日期'),
                open_price=float(row.get('开盘', 0)),
                high_price=float(row.get('最高', 0)),
                low_price=float(row.get('最低', 0)),
                close_price=float(row.get('收盘', 0)),
                volume=int(row.get('成交量', 0)),
                amount=float(row.get('成交额', 0)),
                percentage_change=float(row.get('涨跌幅', 0)) if '涨跌幅' in row else None,
                turnover=float(row.get('换手率', 0)) if '换手率' in row else None
            )
            kline_data.append(kline)
        
        # Sort by date descending
        kline_data.sort(key=lambda x: x.trade_date, reverse=True)
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=StockKlineResponse(
                stock_code=code,
                kline_type=kline_type,
                data=kline_data
            )
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取K线数据失败: {str(e)}"
        )


@router.get("/{code}/indicators", response_model=ApiResponse[StockIndicatorsResponse])
async def get_stock_indicators(
    code: str,
    kline_type: str = Query("day", description="K-line type: day/week/month"),
    days: int = Query(30, ge=1, le=365, description="Number of days")
):
    """
    Get stock technical indicators (MACD, KDJ, RSI)
    
    - **code**: Stock code (6 digits)
    - **kline_type**: K-line type - day/week/month
    - **days**: Number of days to analyze (1-365)
    """
    try:
        # Validate stock code
        if len(code) != 6 or not code.isdigit():
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="股票代码格式错误，应为6位数字"
            )
        
        # Map kline_type to akshare period
        period_map = {
            "day": "daily",
            "week": "weekly",
            "month": "monthly"
        }
        period = period_map.get(kline_type.lower(), "daily")
        
        # Calculate date range
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")
        
        # Fetch K-line data
        df = ak.stock_zh_a_hist(
            symbol=code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
        
        if df.empty or len(df) < 30:
            return ApiResponse(
                code=HttpStatus.OK,
                message="数据不足，无法计算技术指标",
                data=None
            )

        # Calculate technical indicators
        indicators_df = indicator_calculator.calculate_all_indicators(df)
        
        # Convert to response format
        from app.schemas.stocks import TechnicalIndicator
        indicator_data = []
        for _, row in indicators_df.iterrows():
            values = {}
            # Add MACD values
            if 'DIF' in indicators_df.columns:
                values['macd'] = float(row.get('DIF', 0))
                values['signal'] = float(row.get('DEA', 0))
                values['histogram'] = float(row.get('MACD', 0))
            # Add KDJ values
            if 'K' in indicators_df.columns:
                values['k'] = float(row.get('K', 50))
                values['d'] = float(row.get('D', 50))
                values['j'] = float(row.get('J', 50))
            # Add RSI values
            if 'RSI' in indicators_df.columns:
                values['rsi'] = float(row.get('RSI', 50))
            
            tech_indicator = TechnicalIndicator(
                trade_date=row.get('日期'),
                values=values
            )
            indicator_data.append(tech_indicator)
        
        # Sort by date descending
        indicator_data.sort(key=lambda x: x.trade_date, reverse=True)
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=StockIndicatorsResponse(
                stock_code=code,
                kline_type=kline_type,
                indicators=indicator_data
            )
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取技术指标失败: {str(e)}"
        )


@router.get("/{code}/info", response_model=ApiResponse[StockCompanyInfo])
async def get_stock_company_info(code: str):
    """
    Get stock company basic information
    
    - **code**: Stock code (6 digits)
    """
    try:
        # Validate stock code
        if len(code) != 6 or not code.isdigit():
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="股票代码格式错误，应为6位数字"
            )
        
        # Add exchange prefix
        exchange = "SH" if code.startswith("6") else "SZ"
        symbol = f"{exchange}{code}"
        
        # Fetch company info from akshare
        df = ak.stock_individual_basic_info_xq(symbol=symbol)
        
        if df.empty:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail="未找到公司信息"
            )
        
        # Convert DataFrame to dictionary
        company_data = df.set_index('item')['value'].to_dict()
        
        company_info = StockCompanyInfo(
            stock_code=code,
            stock_name=company_data.get('org_short_name_cn'), # 股票简称
            short_name=company_data.get('org_short_name_cn'), # 股票简称
            main_business=company_data.get('main_operation_business'), # 主要业务及产品
            industry=company_data.get('affiliate_industry').get("ind_name"), # 所属行业
            region=company_data.get('provincial_name'), # 所属地区
            company_intro=company_data.get('org_cn_introduction') # 公司简介
        )
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=company_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取公司信息失败: {str(e)}"
        )