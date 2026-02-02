"""
Analysis-related API Routes
Implements async task execution for stock analysis with real AI analysis
"""
import uuid
import hashlib
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from app.services.analysis_pipeline import run_stock_analysis_pipeline
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisCreateResponse,
    AnalysisDetail,
    AnalysisHistoryItem,
    AnalysisStatus,
    AnalysisResult,
    TradingAdvice
)
from app.schemas.common import (
    ApiResponse,
    PaginatedResponse,
    HttpStatus,
    ErrorCode
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# In-memory storage for analysis tasks (in production, use Redis or database)
analysis_tasks: Dict[str, dict] = {}
ANALYSIS_TIMEOUT = 300  # seconds (increased for real AI analysis)


def convert_pipeline_result_to_analysis_result(pipeline_result) -> AnalysisResult:
    """Convert pipeline result to API AnalysisResult format"""
    if pipeline_result is None:
        return None
    
    # Extract trading advice from AI result
    trading_advice = None
    if hasattr(pipeline_result, 'trading_advice') and pipeline_result.trading_advice:
        ta = pipeline_result.trading_advice
        trading_advice = TradingAdvice(
            direction=ta.direction if hasattr(ta, 'direction') else None,
            target_price=ta.target_price if hasattr(ta, 'target_price') else None,
            stop_loss=ta.stop_loss if hasattr(ta, 'stop_loss') else None,
            take_profit=ta.take_profit if hasattr(ta, 'take_profit') else None,
            holding_period=ta.holding_period if hasattr(ta, 'holding_period') else None,
            risk_level=ta.risk_level if hasattr(ta, 'risk_level') else None
        )
    
    # Extract confidence score
    confidence_score = None
    llm_model = None
    if hasattr(pipeline_result, 'confidence_score'):
        confidence_score = pipeline_result.confidence_score
    if hasattr(pipeline_result, 'llm_provider'):
        llm_model = pipeline_result.llm_provider
    
    # Use analysis content as the result
    analysis_text = ""
    if hasattr(pipeline_result, 'analysis_content') and pipeline_result.analysis_content:
        analysis_text = pipeline_result.analysis_content
    elif hasattr(pipeline_result, 'to_dict'):
        # Serialize the whole result
        analysis_text = str(pipeline_result.to_dict())
    
    return AnalysisResult(
        analysis_result=analysis_text,
        trading_advice=trading_advice,
        confidence_score=confidence_score,
        llm_model=llm_model,
        prompt_version="v1.0",
        input_hash=None  # Will be calculated separately
    )


def map_analysis_mode(api_mode: str) -> str:
    """Map API analysis mode to pipeline analysis mode"""
    mode_mapping = {
        "基础面技术面综合分析": "综合分析",
        "波段交易分析": "波段交易",
        "短线T+1分析": "短线T+1",
        "涨停反包分析": "涨停反包",
        "投机套利分析": "投机套利",
        "公司估值分析": "公司估值"
    }
    return mode_mapping.get(api_mode, "短线T+1")


async def run_analysis_task(analysis_id: str, request: AnalysisRequest):
    """
    Background task to run real stock analysis using AI pipeline
    """
    try:
        # Update status to running
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.RUNNING
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()
        
        logger.info(f"[Analysis {analysis_id}] Starting real AI analysis for stock {request.stock_code}")
        
        # Prepare input data summary
        input_data = {
            "stock_code": request.stock_code,
            "analysis_mode": request.analysis_mode.value,
            "kline_type": request.kline_type,
            "sector_names": request.sector_names,
            "include_news": request.include_news
        }
        
        # Calculate input hash for deduplication
        input_str = str(input_data).encode('utf-8')
        input_hash = hashlib.sha256(input_str).hexdigest()[:32]
        
        # Convert API mode to pipeline mode
        pipeline_mode = map_analysis_mode(request.analysis_mode.value)
        
        # Get sector names if provided
        sector_name = request.sector_names[0] if request.sector_names else None
        
        # Run the real analysis pipeline (this is synchronous, run in executor)
        loop = asyncio.get_event_loop()
        pipeline_result = await loop.run_in_executor(
            None,
            run_stock_analysis_pipeline,
            request.stock_code,
            sector_name,
            pipeline_mode
        )
        
        logger.info(f"[Analysis {analysis_id}] Pipeline completed: success={pipeline_result.success}")
        
        # Convert pipeline result to API format
        api_result = None
        if pipeline_result.success and pipeline_result.result:
            # Extract AI analysis result
            ai_result = pipeline_result.result.ai_result
            if ai_result:
                trading_advice = None
                if ai_result.trading_advice:
                    trading_advice = TradingAdvice(
                        direction=ai_result.trading_advice.direction if hasattr(ai_result.trading_advice, 'direction') else None,
                        target_price=ai_result.trading_advice.target_price if hasattr(ai_result.trading_advice, 'target_price') else None,
                        stop_loss=ai_result.trading_advice.stop_loss if hasattr(ai_result.trading_advice, 'stop_loss') else None,
                        take_profit=ai_result.trading_advice.take_profit if hasattr(ai_result.trading_advice, 'take_profit') else None,
                        holding_period=ai_result.trading_advice.holding_period if hasattr(ai_result.trading_advice, 'holding_period') else None,
                        risk_level=ai_result.trading_advice.risk_level if hasattr(ai_result.trading_advice, 'risk_level') else None
                    )
                
                api_result = AnalysisResult(
                    analysis_result=ai_result.analysis_content or "",
                    trading_advice=trading_advice,
                    confidence_score=ai_result.confidence_score,
                    llm_model=ai_result.llm_provider or "Unknown",
                    prompt_version="v1.1",
                    input_hash=input_hash
                )
            else:
                # Fallback if no AI result
                api_result = AnalysisResult(
                    analysis_result="AI analysis completed but no detailed result available",
                    confidence_score=0.5,
                    llm_model="Unknown",
                    prompt_version="v1.1",
                    input_hash=input_hash
                )
        
        # Update task with results
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.COMPLETED
        analysis_tasks[analysis_id]["analysis_time"] = datetime.utcnow()
        analysis_tasks[analysis_id]["input_data"] = input_data
        analysis_tasks[analysis_id]["result"] = api_result
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()
        analysis_tasks[analysis_id]["pipeline_log"] = pipeline_result.execution_log
        analysis_tasks[analysis_id]["cache_keys"] = pipeline_result.result.data_cache_keys if pipeline_result.result else []
        
        logger.info(f"[Analysis {analysis_id}] Analysis completed successfully")
        
    except asyncio.CancelledError:
        # Task was cancelled
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.FAILED
        analysis_tasks[analysis_id]["error_message"] = "Analysis task was cancelled"
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()
        logger.warning(f"[Analysis {analysis_id}] Analysis task was cancelled")
    except Exception as e:
        # Task failed
        error_msg = str(e)
        logger.error(f"[Analysis {analysis_id}] Analysis failed: {error_msg}", exc_info=True)
        analysis_tasks[analysis_id]["status"] = AnalysisStatus.FAILED
        analysis_tasks[analysis_id]["error_message"] = error_msg
        analysis_tasks[analysis_id]["updated_at"] = datetime.utcnow()


@router.post("", response_model=ApiResponse[AnalysisCreateResponse])
async def create_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Create a stock analysis task (executes asynchronously)
    
    The API immediately returns an analysis_id and pending status.
    The actual analysis runs in the background using real AI.
    Use GET /api/v1/analysis/{analysis_id} to query the result.
    
    - **stock_code**: Stock code (6 digits)
    - **analysis_mode**: Analysis mode (基础面技术面综合分析/波段交易分析/短线T+1分析/涨停反包分析/投机套利分析/公司估值分析)
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
        
        # Add background task to run real AI analysis
        background_tasks.add_task(run_analysis_task, analysis_id, request)
        
        # Return immediate response
        response = AnalysisCreateResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PENDING,
            created_at=created_at
        )
        
        logger.info(f"[Analysis {analysis_id}] Analysis task created for stock {request.stock_code}")
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="分析任务已创建，正在后台执行AI分析",
            data=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create analysis task: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"创建分析任务失败: {str(e)}"
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
        history_items = []
        for item in page_items:
            confidence_score = None
            if item["result"]:
                confidence_score = item["result"].confidence_score if hasattr(item["result"], 'confidence_score') else None
            
            history_items.append(
                AnalysisHistoryItem(
                    analysis_id=item["analysis_id"],
                    stock_code=item["stock_code"],
                    analysis_mode=item["analysis_mode"],
                    status=item["status"],
                    analysis_time=item["analysis_time"],
                    confidence_score=confidence_score,
                    created_at=item["created_at"]
                )
            )
        
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
        logger.error(f"Failed to get analysis history: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取分析历史失败: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=ApiResponse[AnalysisDetail])
async def get_analysis_result(analysis_id: str):
    """
    Get analysis result or task status
    
    Supports polling to check the status and retrieve results.
    Returns the complete AI analysis report when completed.
    
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
                task["error_message"] = f"分析超时，已超过 {ANALYSIS_TIMEOUT} 秒"
                task["updated_at"] = datetime.utcnow()
                logger.warning(f"[Analysis {analysis_id}] Analysis timed out")
        
        # Build response
        detail = AnalysisDetail(
            analysis_id=task["analysis_id"],
            stock_code=task["stock_code"],
            analysis_mode=task["analysis_mode"],
            status=task["status"],
            analysis_time=task["analysis_time"],
            input_data=task.get("input_data"),
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
        logger.error(f"Failed to get analysis result: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取分析结果失败: {str(e)}"
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
        logger.info(f"[Analysis {analysis_id}] Analysis record deleted")
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="分析记录已删除",
            data={"analysis_id": analysis_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"删除分析记录失败: {str(e)}"
        )


@router.get("/{analysis_id}/pipeline-log", response_model=ApiResponse[dict])
async def get_analysis_pipeline_log(analysis_id: str):
    """
    Get the detailed pipeline execution log for an analysis
    
    This provides step-by-step execution details including:
    - Data collection steps
    - Indicator calculation
    - Caching operations
    - AI analysis details
    - Timing information
    
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
        pipeline_log = task.get("pipeline_log", {})
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data={
                "analysis_id": analysis_id,
                "pipeline_log": pipeline_log,
                "cache_keys": task.get("cache_keys", [])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline log: {e}", exc_info=True)
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"获取执行日志失败: {str(e)}"
        )
