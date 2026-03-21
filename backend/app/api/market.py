"""
Market-related API Routes
"""
import akshare_proxy_patch

akshare_proxy_patch.install_patch("101.201.173.125", "", 30)

import logging
import uuid
import akshare as ak
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.schemas.market import (
    MarketIndexData,
    MarketSentiment,
    FundFlowData,
    LimitUpStock,
    MarketActivity
)
from app.schemas.common import ApiResponse, HttpStatus, PaginatedResponse
from app.services.indicator_calculator import IndicatorCalculator
from app.services.ai_analyzer import analyze_market, MarketAnalysisResult
from app.db.database import get_db
from app.models.models import AnalysisHistory as AnalysisHistoryModel, AnalysisStatusEnum

router = APIRouter(prefix="/market", tags=["Market"])
indicator_calculator = IndicatorCalculator()


logger = logging.getLogger(__name__)


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
        import pandas as pd
        # Map kline_type to akshare period
        period_map = {
            "day": "daily",
            "week": "weekly",
            "month": "monthly"
        }
        period = period_map.get(kline_type.lower(), "daily")
        
        # Calculate date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        end_date = pd.Timestamp(end_date)
        start_date = pd.Timestamp(start_date)
        
        # Fetch Shanghai Composite Index data (000001)
        df = ak.stock_zh_index_daily(
            symbol="sh000001"
        )
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        logger.info(f"Fetched {len(df)} rows for Shanghai Composite Index from {start_date} to {end_date}")
        logger.info(df.head())
        
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
                amount=float(row.get('amount', 0)) # 接口无 amount 字段，默认为0
            )
            index_data.append(index_point)
        
        # Sort by date ascending (oldest first, newest last for K-line chart)
        index_data.sort(key=lambda x: x.trade_date, reverse=False)
        
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
        logger.info(f"Fetched market activity data for sentiment calculation")
        logger.info(df.head())
        
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
    date: str = Query(None, description="Date in YYYY-MM-DD format (default: latest)")
):
    """
    Get market fund flow data

    - **date**: Optional date in YYYY-MM-DD format
    """
    try:
        # Fetch fund flow data
        df = ak.stock_market_fund_flow()
        logger.info(f"Fetched market fund flow data")
        logger.info(df.head())  
        
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
                return ApiResponse(
                    code=HttpStatus.OK,
                    message=f"未找到日期为 {date} 的资金流向数据",
                    data=None
                )
            latest_data = df_filtered.iloc[0]
        else:
            # Get latest data
            latest_data = df.tail(1).iloc[0]
        
        latest_data = latest_data.to_dict()
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
        logger.info(f"Fetched limit-up stock pool for date {date}")
        logger.info(df.head())
        
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
            # Convert time strings from '092500' format to '09:25:00' format
            def format_time(time_str):
                if time_str and isinstance(time_str, str) and len(time_str) == 6 and time_str.isdigit():
                    return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
                return None
            
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
                first_limit_time=format_time(row.get('首次封板时间')),
                last_limit_time=format_time(row.get('最后封板时间')),
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


@router.get("/analysis", response_model=ApiResponse[dict])
async def get_market_analysis(
    kline_type: str = Query("day", description="K-line type: day/week/month"),
    days: int = Query(30, ge=7, le=90, description="Number of days for analysis"),
    save_result: bool = Query(True, description="Whether to save analysis result to database"),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered market analysis (技术指标分析)
    
    This endpoint analyzes the Shanghai Composite Index using AI:
    - Technical indicators (MACD, KDJ, RSI, Moving Averages)
    - Trend analysis (short/medium/long term)
    - Support/Resistance levels
    - Market sentiment assessment
    - Investment recommendations
    
    Returns analysis_content in markdown format for elegant display.
    
    - **kline_type**: K-line type - day/week/month
    - **days**: Number of days for analysis (7-90)
    - **save_result**: Whether to save the result to database for history
    """
    # Generate unique analysis_id
    analysis_id = str(uuid.uuid4())
    
    try:
        import pandas as pd
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch index K-line data
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df is None or df.empty:
            return ApiResponse(
                code=HttpStatus.OK,
                message="未找到大盘数据",
                data=None
            )
        
        # Normalize and filter data
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        df = df.sort_values('date')
        
        if df.empty:
            return ApiResponse(
                code=HttpStatus.OK,
                message="指定时间范围内无数据",
                data=None
            )
        
        # Calculate technical indicators
        try:
            indicators = indicator_calculator.calculate_all_indicators(df)
        except Exception as e:
            logger.warning(f"Failed to calculate indicators: {e}")
            indicators = None
        
        # Fetch additional market data for AI analysis
        fund_flow_data = ""
        limit_up_count = 0
        limit_down_count = 0
        
        try:
            # Get fund flow info
            ff_df = ak.stock_market_fund_flow()
            if ff_df is not None and not ff_df.empty:
                latest_ff = ff_df.iloc[0]
                main_inflow = latest_ff.get('主力净流入-净额', 0)
                fund_flow_data = f"主力净流入: {main_inflow}亿" if main_inflow else ""
        except Exception as e:
            logger.warning(f"Failed to fetch fund flow: {e}")
        
        try:
            # Get limit-up/down counts
            activity_df = ak.stock_market_activity_legu()
            if activity_df is not None and not activity_df.empty:
                activity_dict = activity_df.set_index('item')['value'].to_dict()
                limit_up_count = int(activity_dict.get('涨停', 0))
                limit_down_count = int(activity_dict.get('跌停', 0))
        except Exception as e:
            logger.warning(f"Failed to fetch market activity: {e}")
        
        # Run AI market analysis
        logger.info("Starting AI market analysis...")
        ai_result = analyze_market(
            index_code="000001",
            index_name="上证指数",
            kline_data=df,
            indicators_data=indicators,
            fund_flow_data=fund_flow_data,
            limit_up_count=limit_up_count,
            limit_down_count=limit_down_count,
            days=days
        )
        
        # Save to database if requested
        logger.info(f"[Market Analysis] save_result={save_result}, ai_result.success={ai_result.success}")
        if save_result and ai_result.success:
            try:
                # Parse trading advice from analysis content or create empty advice
                trading_advice_dict = {
                    "direction": "",
                    "target_price": None,
                    "stop_loss": None,
                    "take_profit": None,
                    "holding_period": None,
                    "risk_level": ""
                }
                
                # Extract direction from trend (simplified mapping)
                if ai_result.trend in ["上涨", "看涨", "上行"]:
                    trading_advice_dict["direction"] = "买入"
                elif ai_result.trend in ["下跌", "看跌", "下行"]:
                    trading_advice_dict["direction"] = "卖出"
                else:
                    trading_advice_dict["direction"] = "持有"
                
                # Normalize sentiment_score to fit database constraints (max 9.99)
                # The sentiment_score from AI is 0-100, scale it to 0-9.99
                normalized_sentiment = min(ai_result.sentiment_score / 10, 9.99) if ai_result.sentiment_score else None
                
                # Normalize confidence_score to fit database constraints (max 9.99)
                # The confidence_score from AI is 0-1, scale it to 0-9.99
                normalized_confidence = min(ai_result.confidence_score * 10, 9.99) if ai_result.confidence_score else None
                
                # Create analysis history record
                analysis_record = AnalysisHistoryModel(
                    analysis_id=analysis_id,
                    stock_code="000001",  # Index code
                    analysis_type="index",
                    analysis_mode="大盘技术分析",
                    analysis_time=datetime.fromisoformat(ai_result.analysis_time.replace('Z', '+00:00')) if ai_result.analysis_time else datetime.now(),
                    kline_type=kline_type,
                    analysis_result=ai_result.analysis_content,
                    trading_advice=trading_advice_dict,
                    sentiment_score=normalized_sentiment,
                    confidence_score=normalized_confidence,
                    llm_model=ai_result.llm_model,
                    status=AnalysisStatusEnum.COMPLETED,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.add(analysis_record)
                db.commit()
                logger.info(f"[Market Analysis {analysis_id}] Analysis result saved to database successfully")
                
            except Exception as e:
                logger.error(f"[Market Analysis] Failed to save analysis to database: {e}", exc_info=True)
                db.rollback()
                # Continue returning result even if save fails
        
        # Build response data
        response_data = {
            "analysis_id": analysis_id,  # Include analysis_id in response
            "index_code": "000001",
            "index_name": "上证指数",
            "kline_type": kline_type,
            "days": days,
            "analysis_time": ai_result.analysis_time,
            "trend": ai_result.trend,
            "support_levels": ai_result.support_levels,
            "resistance_levels": ai_result.resistance_levels,
            "sentiment_score": ai_result.sentiment_score,
            "confidence_score": ai_result.confidence_score,
            "llm_provider": ai_result.llm_provider,
            "llm_model": ai_result.llm_model,
            "token_usage": ai_result.token_usage,
            "analysis_content": ai_result.analysis_content,
            "success": ai_result.success,
            "error_message": ai_result.error_message
        }
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=response_data)
        
    except Exception as e:
        logger.error(f"Market analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"大盘分析失败: {str(e)}"
        )


@router.get("/analysis/history", response_model=ApiResponse[PaginatedResponse[dict]])
async def get_market_analysis_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get market analysis history from database
    
    - **page**: Page number (starts from 1)
    - **page_size**: Items per page (1-100)
    """
    try:
        # First, let's check ALL records to help debug
        all_records = db.query(AnalysisHistoryModel).all()
        logger.info(f"[Market Analysis History] Total records in DB: {len(all_records)}")
        
        # Check what analysis_type values exist
        analysis_types = set()
        stock_codes = set()
        for r in all_records:
            analysis_types.add(r.analysis_type)
            stock_codes.add(r.stock_code)
        logger.info(f"[Market Analysis History] Unique analysis_types: {analysis_types}")
        logger.info(f"[Market Analysis History] Unique stock_codes: {stock_codes}")
        
        # Query index analysis records (analysis_type = 'index')
        # Also allow records with stock_code = '000001' as fallback
        query = db.query(AnalysisHistoryModel).filter(
            (AnalysisHistoryModel.analysis_type == 'index') | 
            (AnalysisHistoryModel.stock_code == '000001')
        )
        
        # Get total count
        total = query.count()
        logger.info(f"[Market Analysis History] Matching records: {total}")
        
        # Get paginated results sorted by created_at descending
        items = query.order_by(
            AnalysisHistoryModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        logger.info(f"[Market Analysis History] Found {len(items)} items for page {page}")
        
        # Convert to response format
        history_items = []
        for item in items:
            history_items.append({
                "analysis_id": item.analysis_id,
                "stock_code": item.stock_code,
                "analysis_mode": item.analysis_mode or "大盘技术分析",
                "status": item.status.value if hasattr(item.status, 'value') else str(item.status),
                "analysis_time": item.analysis_time,
                "confidence_score": item.confidence_score,
                "created_at": item.created_at,
                "kline_type": item.kline_type
            })
        
        paginated_response = PaginatedResponse[dict](
            total=total,
            page=page,
            page_size=page_size,
            data=history_items
        )
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=paginated_response
        )
        
    except Exception as e:
        logger.error(f"Failed to get market analysis history: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取大盘分析历史失败: {str(e)}"
        )


@router.get("/analysis/{analysis_id}", response_model=ApiResponse[dict])
async def get_market_analysis_result(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific market analysis result from database
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        # Check if task exists
        task = db.query(AnalysisHistoryModel).filter(
            AnalysisHistoryModel.analysis_id == analysis_id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"未找到分析任务: {analysis_id}"
            )
        
        # Build response
        response_data = {
            "analysis_id": task.analysis_id,
            "stock_code": task.stock_code,
            "analysis_mode": task.analysis_mode or "大盘技术分析",
            "kline_type": task.kline_type,
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            "analysis_time": task.analysis_time,
            "confidence_score": task.confidence_score,
            "llm_model": task.llm_model,
            "analysis_result": task.analysis_result,
            "trading_advice": task.trading_advice,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get market analysis result: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取分析结果失败: {str(e)}"
        )


@router.delete("/analysis/{analysis_id}", response_model=ApiResponse[dict])
async def delete_market_analysis(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a market analysis record from database
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        # Check if task exists
        task = db.query(AnalysisHistoryModel).filter(
            AnalysisHistoryModel.analysis_id == analysis_id,
            AnalysisHistoryModel.analysis_type == 'index'
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"未找到分析任务: {analysis_id}"
            )
        
        # Delete task
        db.delete(task)
        db.commit()
        logger.info(f"[Market Analysis {analysis_id}] Analysis record deleted from database")
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="分析记录已删除",
            data={"analysis_id": analysis_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete market analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"删除分析记录失败: {str(e)}"
        )
