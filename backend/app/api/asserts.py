"""Asserts API - 提供asserts文件夹的内容浏览"""

import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.schemas.common import ApiResponse, HttpStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asserts", tags=["Asserts"])

# asserts文件夹路径
ASSERTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "asserts"


class FileItem(BaseModel):
    """文件项"""
    name: str
    path: str
    is_dir: bool
    size: int = 0


class AssertsStructureResponse(BaseModel):
    """asserts目录结构响应"""
    summary_dates: List[str]
    output_files: List[str]


class FileContent(BaseModel):
    """文件内容响应"""
    name: str
    path: str
    content: str
    content_type: str
    size: int


@router.get("/structure", response_model=ApiResponse[AssertsStructureResponse])
async def get_asserts_structure():
    """
    获取asserts目录结构
    返回summary中的日期列表和output中的文件列表
    """
    try:
        summary_dates = []
        output_files = []
        
        # 获取summary目录下的日期文件夹
        summary_dir = ASSERTS_DIR / "summary"
        if summary_dir.exists():
            for item in sorted(summary_dir.iterdir()):
                if item.is_dir():
                    summary_dates.append(item.name)
        
        # 获取output目录下的文件
        output_dir = ASSERTS_DIR / "output"
        if output_dir.exists():
            for item in sorted(output_dir.iterdir()):
                if item.is_file() and item.suffix == ".md":
                    output_files.append(item.name)
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=AssertsStructureResponse(
                summary_dates=summary_dates,
                output_files=output_files
            )
        )
    except Exception as e:
        logger.error(f"获取asserts目录结构失败: {e}")
        return ApiResponse(
            code=HttpStatus.INTERNAL_SERVER_ERROR,
            message=f"获取目录结构失败: {str(e)}",
            data=None
        )


@router.get("/files", response_model=ApiResponse[List[FileItem]])
async def get_asserts_files(
    folder: Optional[str] = Query(None, description="文件夹路径: summary/日期 或 output")
):
    """
    获取指定文件夹下的文件列表
    folder: summary/20260309 或 output
    """
    try:
        if folder:
            target_dir = ASSERTS_DIR / folder
        else:
            target_dir = ASSERTS_DIR
        
        if not target_dir.exists():
            return ApiResponse(
                code=HttpStatus.NOT_FOUND,
                message=f"文件夹不存在: {folder}",
                data=None
            )
        
        files = []
        for item in sorted(target_dir.iterdir()):
            files.append(FileItem(
                name=item.name,
                path=str(item.relative_to(ASSERTS_DIR)),
                is_dir=item.is_dir(),
                size=item.stat().st_size if item.is_file() else 0
            ))
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=files
        )
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return ApiResponse(
            code=HttpStatus.INTERNAL_SERVER_ERROR,
            message=f"获取文件列表失败: {str(e)}",
            data=None
        )


@router.get("/content", response_model=ApiResponse[FileContent])
async def get_file_content(
    path: str = Query(..., description="文件路径: summary/20260309/xxx.txt 或 output/xxx.md")
):
    """
    获取指定文件的内容
    """
    try:
        target_file = ASSERTS_DIR / path
        
        if not target_file.exists():
            return ApiResponse(
                code=HttpStatus.NOT_FOUND,
                message=f"文件不存在: {path}",
                data=None
            )
        
        if not target_file.is_file():
            return ApiResponse(
                code=HttpStatus.BAD_REQUEST,
                message=f"不是文件: {path}",
                data=None
            )
        
        # 根据文件扩展名确定content-type
        content_type = "text/plain"
        if target_file.suffix == ".md":
            content_type = "text/markdown"
        elif target_file.suffix == ".txt":
            content_type = "text/plain; charset=utf-8"
        
        # 读取文件内容
        content = target_file.read_text(encoding="utf-8")
        
        return ApiResponse(
            code=HttpStatus.OK,
            message="success",
            data=FileContent(
                name=target_file.name,
                path=path,
                content=content,
                content_type=content_type,
                size=target_file.stat().st_size
            )
        )
    except Exception as e:
        logger.error(f"读取文件内容失败: {e}")
        return ApiResponse(
            code=HttpStatus.INTERNAL_SERVER_ERROR,
            message=f"读取文件内容失败: {str(e)}",
            data=None
        )


@router.get("/download")
async def download_file(
    path: str = Query(..., description="文件路径")
):
    """
    下载指定文件
    """
    try:
        target_file = ASSERTS_DIR / path
        
        if not target_file.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {path}")
        
        if not target_file.is_file():
            raise HTTPException(status_code=400, detail=f"不是文件: {path}")
        
        return FileResponse(
            path=str(target_file),
            filename=target_file.name,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
