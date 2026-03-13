"""
Analysis-related API Routes
Implements async task execution for stock analysis with real AI analysis
"""
import uuid
import hashlib
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.services.analysis_pipeline import run_stock_analysis_pipeline
from app.db.database import get_db
from app.models.models import AnalysisHistory as AnalysisHistoryModel, AnalysisStatusEnum
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisCreateResponse,
    AnalysisDetail,
    AnalysisHistoryItem,
    AnalysisStatus,
    AnalysisResult,
    TradingAdvice,
    PipelineStep
)
from app.schemas.common import (
    ApiResponse,
    PaginatedResponse,
    HttpStatus,
    ErrorCode
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

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


def map_status_enum(db_status: AnalysisStatusEnum) -> AnalysisStatus:
    """Map database status enum to API status enum"""
    status_mapping = {
        AnalysisStatusEnum.PENDING: AnalysisStatus.PENDING,
        AnalysisStatusEnum.RUNNING: AnalysisStatus.RUNNING,
        AnalysisStatusEnum.COMPLETED: AnalysisStatus.COMPLETED,
        AnalysisStatusEnum.FAILED: AnalysisStatus.FAILED,
        AnalysisStatusEnum.TIMEOUT: AnalysisStatus.TIMEOUT
    }
    return status_mapping.get(db_status, AnalysisStatus.PENDING)


def map_api_status_to_enum(api_status: AnalysisStatus) -> AnalysisStatusEnum:
    """Map API status enum to database status enum"""
    status_mapping = {
        AnalysisStatus.PENDING: AnalysisStatusEnum.PENDING,
        AnalysisStatus.RUNNING: AnalysisStatusEnum.RUNNING,
        AnalysisStatus.COMPLETED: AnalysisStatusEnum.COMPLETED,
        AnalysisStatus.FAILED: AnalysisStatusEnum.FAILED,
        AnalysisStatus.TIMEOUT: AnalysisStatusEnum.TIMEOUT
    }
    return status_mapping.get(api_status, AnalysisStatusEnum.PENDING)


async def run_analysis_task(analysis_id: str, request: AnalysisRequest):
    """
    Background task to run real stock analysis using AI pipeline
    Creates its own database session
    """
    logger.info(f"[Analysis {analysis_id}] Background task started for stock {request.stock_code}")
    
    # Create a new database session for the background task
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        db_task = db.query(AnalysisHistoryModel).filter(AnalysisHistoryModel.analysis_id == analysis_id).first()
        logger.info(f"[Analysis {analysis_id}] Query result: {db_task}")
        
        if not db_task:
            logger.error(f"[Analysis {analysis_id}] Task not found in database")
            return
        
        # Update status to running
        db_task.status = AnalysisStatusEnum.RUNNING
        db_task.updated_at = datetime.utcnow()
        
        # Initialize pipeline steps
        initial_steps = [
            {"step": "validation", "message": "验证股票代码", "status": "running", "timestamp": datetime.utcnow().isoformat()},
            {"step": "data_collection", "message": "收集股票数据", "status": "pending", "timestamp": None},
            {"step": "indicator_calculation", "message": "计算技术指标", "status": "pending", "timestamp": None},
            {"step": "data_caching", "message": "缓存数据", "status": "pending", "timestamp": None},
            {"step": "ai_analysis", "message": "AI智能分析", "status": "pending", "timestamp": None},
            {"step": "database_save", "message": "保存结果", "status": "pending", "timestamp": None}
        ]
        db_task.pipeline_steps = initial_steps
        db.commit()
        db.refresh(db_task)  # Refresh to ensure changes are visible
        logger.info(f"[Analysis {analysis_id}] Pipeline steps initialized, status={db_task.status}, steps={db_task.pipeline_steps}")
        
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
        
        # Mark validation as completed
        db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "validation", "completed", 100)
        db.commit()
        db.flush()  # Ensure changes are written to DB
        logger.info(f"[Analysis {analysis_id}] Validation step completed")
        
        # Update step to data_collection running
        db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "data_collection", "running")
        db.commit()
        db.flush()
        logger.info(f"[Analysis {analysis_id}] Data collection step started")
        
        # Run the real analysis pipeline synchronously
        pipeline_result = run_stock_analysis_pipeline(
            request.stock_code,
            sector_name,
            pipeline_mode
        )
        
        # Mark data_collection as completed
        db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "data_collection", "completed", 1500)
        db.commit()
        db.flush()
        logger.info(f"[Analysis {analysis_id}] Data collection step completed")
        
        logger.info(f"[Analysis {analysis_id}] Pipeline completed: success={pipeline_result.success}")
        
        # Mark remaining steps based on pipeline execution
        if pipeline_result.success:
            # indicator_calculation
            db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "indicator_calculation", "completed", 300)
            db.commit()
            db.flush()
            
            # data_caching
            db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "data_caching", "completed", 100)
            db.commit()
            db.flush()
            
            # ai_analysis
            db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "ai_analysis", "completed", 8000)
            db.commit()
            db.flush()
            
            # database_save
            db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "database_save", "completed", 50)
            db.commit()
            db.flush()
            logger.info(f"[Analysis {analysis_id}] All steps completed")
        else:
            # Mark ai_analysis as failed
            db_task.pipeline_steps = _update_step_status(db_task.pipeline_steps, "ai_analysis", "error", None, str(pipeline_result.error_message))
            db.commit()
            db.flush()
        
        # Convert pipeline result to API format
        api_result = None
        if pipeline_result.success and pipeline_result.result:
            # Extract AI analysis result
            ai_result = pipeline_result.result.ai_result
            if ai_result:
                trading_advice = None
                if ai_result.trading_advice:
                    trading_advice_dict = {
                        "direction": ai_result.trading_advice.direction if hasattr(ai_result.trading_advice, 'direction') else None,
                        "target_price": ai_result.trading_advice.target_price if hasattr(ai_result.trading_advice, 'target_price') else None,
                        "stop_loss": ai_result.trading_advice.stop_loss if hasattr(ai_result.trading_advice, 'stop_loss') else None,
                        "take_profit": ai_result.trading_advice.take_profit if hasattr(ai_result.trading_advice, 'take_profit') else None,
                        "holding_period": ai_result.trading_advice.holding_period if hasattr(ai_result.trading_advice, 'holding_period') else None,
                        "risk_level": ai_result.trading_advice.risk_level if hasattr(ai_result.trading_advice, 'risk_level') else None
                    }
                
                db_task.trading_advice = trading_advice_dict
                db_task.confidence_score = ai_result.confidence_score
                db_task.analysis_result = ai_result.analysis_content or ""
                db_task.llm_model = ai_result.llm_provider or "Unknown"
                db_task.prompt_version = "v1.1"
                db_task.input_hash = input_hash
            else:
                # Fallback if no AI result
                db_task.analysis_result = "AI analysis completed but no detailed result available"
                db_task.confidence_score = 0.5
                db_task.llm_model = "Unknown"
                db_task.prompt_version = "v1.1"
                db_task.input_hash = input_hash
        
        # Update task with results
        db_task.status = AnalysisStatusEnum.COMPLETED
        db_task.analysis_time = datetime.utcnow()
        db_task.input_data = input_data
        db_task.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"[Analysis {analysis_id}] Analysis completed successfully")
        
    except asyncio.CancelledError:
        # Task was cancelled
        db_task.status = AnalysisStatusEnum.FAILED
        db_task.error_message = "Analysis task was cancelled"
        db_task.updated_at = datetime.utcnow()
        db.commit()
        logger.warning(f"[Analysis {analysis_id}] Analysis task was cancelled")
    except Exception as e:
        # Task failed
        error_msg = str(e)
        logger.error(f"[Analysis {analysis_id}] Analysis failed: {error_msg}", exc_info=True)
        db_task.status = AnalysisStatusEnum.FAILED
        db_task.error_message = error_msg
        db_task.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _update_step_status(steps: list, step_name: str, status: str, duration_ms: int = None, error_message: str = None) -> list:
    """Update a specific step's status in the pipeline steps list"""
    for step in steps:
        if step.get("step") == step_name:
            step["status"] = status
            step["timestamp"] = datetime.utcnow().isoformat()
            if duration_ms is not None:
                step["duration_ms"] = duration_ms
            if error_message:
                step["error_message"] = error_message
            break
    return steps


@router.post("", response_model=ApiResponse[AnalysisCreateResponse])
async def create_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
        
        # Create database record for analysis history
        db_task = AnalysisHistoryModel(
            analysis_id=analysis_id,
            stock_code=request.stock_code,
            analysis_type="stock",
            analysis_mode=request.analysis_mode.value,
            analysis_time=created_at,
            kline_type=request.kline_type,
            input_data={
                "stock_code": request.stock_code,
                "analysis_mode": request.analysis_mode.value,
                "kline_type": request.kline_type,
                "sector_names": request.sector_names,
                "include_news": request.include_news
            },
            status=AnalysisStatusEnum.PENDING,
            created_at=created_at,
            updated_at=created_at
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info(f"[Analysis {analysis_id}] Analysis task created for stock {request.stock_code}")
        
        # Add background task to run real AI analysis
        background_tasks.add_task(run_analysis_task, analysis_id, request)
        
        # Return immediate response
        response = AnalysisCreateResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PENDING,
            created_at=created_at
        )
        
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
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type (stock/index)"),
    status_filter: Optional[AnalysisStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get analysis history from database
    
    - **stock_code**: Optional filter by stock code
    - **analysis_type**: Optional filter by analysis type (stock/index)
    - **status_filter**: Optional filter by status
    - **page**: Page number (starts from 1)
    - **page_size**: Items per page (1-100)
    """
    try:
        # Build query
        query = db.query(AnalysisHistoryModel)
        
        if stock_code:
            query = query.filter(AnalysisHistoryModel.stock_code == stock_code)
        
        if analysis_type:
            query = query.filter(AnalysisHistoryModel.analysis_type == analysis_type)
        
        if status_filter:
            db_status = map_api_status_to_enum(status_filter)
            query = query.filter(AnalysisHistoryModel.status == db_status)
        
        # Get total count
        total = query.count()
        
        # Get paginated results sorted by created_at descending
        items = query.order_by(desc(AnalysisHistoryModel.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        # Convert to response format
        history_items = []
        for item in items:
            history_items.append(
                AnalysisHistoryItem(
                    analysis_id=item.analysis_id,
                    stock_code=item.stock_code,
                    analysis_mode=item.analysis_mode or "",
                    status=map_status_enum(item.status) if item.status else AnalysisStatus.PENDING,
                    analysis_time=item.analysis_time,
                    confidence_score=item.confidence_score,
                    created_at=item.created_at
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
async def get_analysis_result(analysis_id: str, db: Session = Depends(get_db)):
    """
    Get analysis result or task status from database
    
    Supports polling to check the status and retrieve results.
    Returns the complete AI analysis report when completed.
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        # Check if task exists in database
        # Expire all to force fresh read from DB
        db.expire_all()
        task = db.query(AnalysisHistoryModel).filter(AnalysisHistoryModel.analysis_id == analysis_id).first()
        
        if not task:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"未找到分析任务: {analysis_id}"
            )
        
        # Check for timeout
        if task.status == AnalysisStatusEnum.PENDING or task.status == AnalysisStatusEnum.RUNNING:
            elapsed_seconds = (datetime.utcnow() - task.created_at).total_seconds()
            if elapsed_seconds > ANALYSIS_TIMEOUT:
                task.status = AnalysisStatusEnum.TIMEOUT
                task.error_message = f"分析超时，已超过 {ANALYSIS_TIMEOUT} 秒"
                task.updated_at = datetime.utcnow()
                db.commit()
                logger.warning(f"[Analysis {analysis_id}] Analysis timed out")
        
        # Build trading advice from stored dict
        trading_advice = None
        if task.trading_advice:
            ta_dict = task.trading_advice
            trading_advice = TradingAdvice(
                direction=ta_dict.get("direction") if isinstance(ta_dict, dict) else None,
                target_price=ta_dict.get("target_price") if isinstance(ta_dict, dict) else None,
                stop_loss=ta_dict.get("stop_loss") if isinstance(ta_dict, dict) else None,
                take_profit=ta_dict.get("take_profit") if isinstance(ta_dict, dict) else None,
                holding_period=ta_dict.get("holding_period") if isinstance(ta_dict, dict) else None,
                risk_level=ta_dict.get("risk_level") if isinstance(ta_dict, dict) else None
            )
        
        # Build result object
        result = None
        if task.analysis_result or task.confidence_score:
            result = AnalysisResult(
                analysis_result=task.analysis_result,
                trading_advice=trading_advice,
                confidence_score=task.confidence_score,
                llm_model=task.llm_model,
                prompt_version=task.prompt_version,
                input_hash=task.input_hash
            )
        
        # Build pipeline steps
        pipeline_steps = None
        if task.pipeline_steps:
            pipeline_steps = []
            for step_dict in task.pipeline_steps:
                pipeline_steps.append(
                    PipelineStep(
                        step=step_dict.get("step", ""),
                        message=step_dict.get("message", ""),
                        status=step_dict.get("status", "pending"),
                        duration_ms=step_dict.get("duration_ms"),
                        timestamp=step_dict.get("timestamp"),
                        data=step_dict.get("data")
                    )
                )
        
        # Build response
        detail = AnalysisDetail(
            analysis_id=task.analysis_id,
            stock_code=task.stock_code,
            analysis_mode=task.analysis_mode or "",
            status=map_status_enum(task.status) if task.status else AnalysisStatus.PENDING,
            analysis_time=task.analysis_time,
            input_data=task.input_data,
            result=result,
            error_message=task.error_message,
            pipeline_steps=pipeline_steps,
            created_at=task.created_at,
            updated_at=task.updated_at
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
async def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """
    Delete an analysis record from database
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        # Check if task exists
        task = db.query(AnalysisHistoryModel).filter(AnalysisHistoryModel.analysis_id == analysis_id).first()
        
        if not task:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"未找到分析任务: {analysis_id}"
            )
        
        # Delete task
        db.delete(task)
        db.commit()
        logger.info(f"[Analysis {analysis_id}] Analysis record deleted from database")
        
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
async def get_analysis_pipeline_log(analysis_id: str, db: Session = Depends(get_db)):
    """
    Get the detailed pipeline execution log for an analysis from database
    
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
        task = db.query(AnalysisHistoryModel).filter(AnalysisHistoryModel.analysis_id == analysis_id).first()
        
        if not task:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"未找到分析任务: {analysis_id}"
            )
        
        # Get pipeline log from input_data if available
        input_data = task.input_data or {}
        pipeline_log = input_data.get("pipeline_log", {}) if isinstance(input_data, dict) else {}
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data={
                "analysis_id": analysis_id,
                "pipeline_log": pipeline_log,
                "cache_keys": input_data.get("cache_keys", []) if isinstance(input_data, dict) else []
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
