"""
Analysis-related API Routes
Implements async task execution for stock analysis
"""
import uuid
import hashlib
import asyncio
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisCreateResponse,
    AnalysisDetail,
    AnalysisHistoryItem,
    AnalysisStatus
)
from app.schemas.common import (
    ApiResponse,
    PaginatedResponse,
    HttpStatus,
    ErrorCode
)

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])

# In-memory storage for analysis tasks (in production, use Redis or database)
analysis_tasks: Dict[str, dict] = {}
ANALYSIS_TIMEOUT = 120  # seconds


async def run_analysis_task(analysis_id: str, request: AnalysisRequest):
    """
    Background task to run stock analysis
    This simulates AI analysis - in production, this would call LLM services
    """
    try:
        # Update status to running
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.RUNNING
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()
        
        # Simulate analysis delay (in production, this would call LLM API)
        await asyncio.sleep(5)
        
        # Prepare input data summary
        input_data = {
            "stock_code": request.stock_code,
            "analysis_mode": request.analysis_mode,
            "kline_type": request.kline_type,
            "sector_names": request.sector_names,
            "include_news": request.include_news
        }
        
        # Calculate input hash for deduplication
        input_str = str(input_data).encode('utf-8')
        input_hash = hashlib.sha256(input_str).hexdigest()[:32]
        
        # Simulate AI analysis result
        # In production, this would be the actual LLM response
        mock_analysis_result = f"""
基于{request.analysis_mode}模式对股票{request.stock_code}的分析：

技术面分析：
- MACD指标显示买入信号，DIF线上穿DEA线
- KDJ指标处于超买区域，短期存在回调风险
- RSI指标为68，处于强势区域
- 均线系统呈多头排列，中期趋势向好

基本面分析：
- 公司基本面稳健，财务状况良好
- 所属行业景气度较高
- 近期有重大利好消息

市场情绪分析：
- 大盘整体情绪偏暖
- 市场赚钱效应明显
- 资金面相对充裕

投资建议：
- 建议适量买入
- 目标价位：12.50元
- 止损位：10.80元
- 持仓期限：3-5个交易日
- 风险等级：中

风险提示：
- 注意大盘回调风险
- 关注成交量变化
- 谨慎控制仓位
        """.strip()
        
        # Mock trading advice
        from app.schemas.analysis import TradingAdvice, AnalysisResult
        trading_advice = TradingAdvice(
            direction="买入",
            target_price=12.50,
            stop_loss=10.80,
            take_profit=15.00,
            holding_period=3,
            risk_level="中"
        )
        
        # Create analysis result
        result = AnalysisResult(
            analysis_result=mock_analysis_result,
            trading_advice=trading_advice,
            confidence_score=0.78,
            llm_model="智谱GLM",
            prompt_version="v1.0",
            input_hash=input_hash
        )
        
        # Update task with results
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.COMPLETED
        analysis_tasks[analysis_id]["analysis_time"] = datetime.utcnow()
        analysis_tasks[analysis_id]["input_data"] = input_data
        analysis_tasks[analysis_id]["result"] = result
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()
        
    except asyncio.CancelledError:
        # Task was cancelled
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.FAILED
        analysis_tasks[analysis_id]["error_message"] = "Analysis task was cancelled"
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()
    except Exception as e:
        # Task failed
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.FAILED
        analysis_tasks[analysis_id]["error_message"] = str(e)
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()


@router.post("", response_model=ApiResponse[AnalysisCreateResponse])
async def create_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Create a stock analysis task (executes asynchronously)
    
    The API immediately returns an analysis_id and pending status.
    The actual analysis runs in the background.
    Use GET /api/v1/analysis/{analysis_id} to query the result.
    
    - **stock_code**: Stock code (6 digits)
    - **analysis_mode**: Analysis mode
    - **kline_type**: K-line type (day/week/month)
    - **sector_names**: Optional sector names for context
    - **include_news**: Whether to include news in analysis
    """
    try:
        # Validate stock code
        if len(request.stock_code) != 6 or not request.stock_code.isdigit():
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="股票代码格式错误，应为6位数字"
            )
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Create task entry
        task = {
            "analysis_id": analysis_id,
            "stock_code": request.stock_code,
            "analysis_mode": request.analysis_mode.value,
            "status": AnalysisStatus.PENDING,
            "analysis_time": None,
            "input_data": None,
            "result": None,
            "error_message": None,
            "created_at": created_at,
            "updated_at": created_at,
            "request": request
        }
        
        analysis_tasks[analysis_id] = task
        
        # Add background task
        background_tasks.add_task(run_analysis_task, analysis_id, request)
        
        # Return immediate response
        response = AnalysisCreateResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PENDING,
            created_at=created_at
        )
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="Analysis task created successfully",
            data=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"创建分析任务失败: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=ApiResponse[AnalysisDetail])
async def get_analysis_result(analysis_id: str):
    """
    Get analysis result or task status
    
    Supports polling to check the status and retrieve results.
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        # Check if task exists
        if analysis_id not in analysis_tasks:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"未找到分析任务: {analysis_id}"
            )
        
        task = analysis_tasks[analysis_id]
        
        # Check for timeout
        if task["status"] in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
            elapsed_seconds = (datetime.utcnow() - task["created_at"]).total_seconds()
            if elapsed_seconds > ANALYSIS_TIMEOUT:
                # Task timed out
                task["status"] = AnalysisStatus.TIMEOUT
                task["error_message"] = f"Analysis timeout after {ANALYSIS_TIMEOUT} seconds"
                task["updated_at"] = datetime.utcnow()
        
        # Build response
        from app.schemas.analysis import AnalysisResult
        detail = AnalysisDetail(
            analysis_id=task["analysis_id"],
            stock_code=task["stock_code"],
            analysis_mode=task["analysis_mode"],
            status=task["status"],
            analysis_time=task["analysis_time"],
            input_data=task["input_data"],
            result=task["result"],
            error_message=task["error_message"],
            created_at=task["created_at"],
            updated_at=task["updated_at"]
        )
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取分析结果失败: {str(e)}"
        )


@router.get("/history", response_model=ApiResponse[PaginatedResponse[AnalysisHistoryItem]])
async def get_analysis_history(
    stock_code: Optional[str] = Query(None, description="Filter by stock code"),
    status_filter: Optional[AnalysisStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get analysis history
    
    - **stock_code**: Optional filter by stock code
    - **status_filter**: Optional filter by status
    - **page**: Page number (starts from 1)
    - **page_size**: Items per page (1-100)
    """
    try:
        # Filter tasks
        filtered_tasks = list(analysis_tasks.values())
        
        if stock_code:
            filtered_tasks = [t for t in filtered_tasks if t["stock_code"] == stock_code]
        
        if status_filter:
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status_filter]
        
        # Sort by created_at descending
        filtered_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Pagination
        total = len(filtered_tasks)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = filtered_tasks[start_idx:end_idx]
        
        # Convert to response format
        history_items = [
            AnalysisHistoryItem(
                analysis_id=item["analysis_id"],
                stock_code=item["stock_code"],
                analysis_mode=item["analysis_mode"],
                status=item["status"],
                analysis_time=item["analysis_time"],
                confidence_score=item["result"].confidence_score if item["result"] else None,
                created_at=item["created_at"]
            )
            for item in page_items
        ]
        
        paginated_response = PaginatedResponse[AnalysisHistoryItem](
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
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取分析历史失败: {str(e)}"
        )


@router.delete("/{analysis_id}", response_model=ApiResponse[dict])
async def delete_analysis(analysis_id: str):
    """
    Delete an analysis record
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        # Check if task exists
        if analysis_id not in analysis_tasks:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"未找到分析任务: {analysis_id}"
            )
        
        # Delete task
        del analysis_tasks[analysis_id]
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="Analysis deleted successfully",
            data={"analysis_id": analysis_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"删除分析记录失败: {str(e)}"
        )