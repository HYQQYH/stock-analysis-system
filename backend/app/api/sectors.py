"""
Sector-related API Routes
Provides sector list for dropdown selection
"""
import logging
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.redis_cache import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sectors", tags=["Sectors"])

# Cache key and TTL (24 hours = 86400 seconds)
SECTORS_CACHE_KEY = "sector:concept:names"
SECTORS_CACHE_TTL = 86400

# Path to fallback sector file
SECTOR_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "asserts", "sector_ths.txt")


class SectorItem(BaseModel):
    """Sector item model"""
    name: str


class SectorsResponse(BaseModel):
    """Response model for sectors list"""
    sectors: List[str]
    total: int


def fetch_sectors_from_akshare() -> List[str]:
    """
    Fetch concept sector names from akshare
    
    Returns:
        List of sector names
    """
    try:
        import akshare as ak
        
        # Get concept sector names from tonghuashun (同花顺)
        df = ak.stock_board_concept_name_ths()
        
        if df is not None and not df.empty:
            # The 'name' column contains the sector names
            if 'name' in df.columns:
                sectors = df['name'].tolist()
                sectors = [s.strip() for s in sectors if s and s.strip()]
                logger.info(f"Fetched {len(sectors)} sectors from akshare (column: name)")
                return
            # Fallback to 'name' column
            elif 'name' in df.columns:
                sectors = df['name'].tolist()
                sectors = [s.strip() for s in sectors if s and s.strip()]
                logger.info(f"Fetched {len(sectors)} sectors from akshare (column: name)")
                return sectors
            else:
                logger.warning(f"akshare returned DataFrame without expected columns: {df.columns.tolist()}")
                return []
        else:
            logger.warning("akshare returned empty DataFrame")
            return []
            
    except Exception as e:
        logger.error(f"Failed to fetch sectors from akshare: {e}")
        return []


def get_sectors_from_file() -> List[str]:
    """
    Get sector list from fallback file
    
    Returns:
        List of sector names from file
    """
    try:
        if os.path.exists(SECTOR_FILE_PATH):
            with open(SECTOR_FILE_PATH, 'r', encoding='utf-8') as f:
                sectors = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(sectors)} sectors from file: {SECTOR_FILE_PATH}")
            return sectors
        else:
            logger.warning(f"Sector file not found: {SECTOR_FILE_PATH}")
            return []
    except Exception as e:
        logger.error(f"Failed to read sector file: {e}")
        return []


def get_sectors_with_cache() -> List[str]:
    """
    Get sectors list - simplified version that directly returns file content
    
    Returns:
        List of sector names
    """
    # Direct approach: return file content
    sectors = get_sectors_from_file()
    
    if sectors:
        logger.info(f"Returning {len(sectors)} sectors from file")
        return sectors
    
    # If file doesn't work, try akshare
    logger.warning("File not found, trying akshare...")
    sectors = fetch_sectors_from_akshare()
    
    if sectors:
        logger.info(f"Returning {len(sectors)} sectors from akshare")
        return sectors
    
    # Return empty list if everything fails
    logger.error("All sources failed - returning empty list")
    return []


def get_default_sectors() -> List[str]:
    """
    Get default sector list as fallback
    
    Returns:
        List of default sector names
    """
    # Try to get from file first
    sectors = get_sectors_from_file()
    if sectors:
        return sectors
    
    # Fallback to hardcoded list if file doesn't exist
    return [
        "人工智能",
        "新能源汽车",
        "芯片",
        "光伏",
        "储能",
        "锂电池",
        "医疗器械",
        "创新药",
        "云计算",
        "大数据",
        "5G",
        "物联网",
        "工业互联网",
        "数字经济",
        "生物医药",
        "新材料",
        "碳中和",
        "氢能源",
        "半导体",
        "消费电子",
    ]


@router.get("", response_model=SectorsResponse)
async def get_sectors():
    """
    Get concept sector list for dropdown selection
    
    Returns a list of sector names that can be used for stock analysis.
    The list is cached in Redis for 24 hours.
    
    Returns:
        SectorsResponse with list of sector names
    """
    try:
        sectors = get_sectors_with_cache()
        
        return SectorsResponse(
            sectors=sectors,
            total=len(sectors)
        )
        
    except Exception as e:
        logger.error(f"Failed to get sectors: {e}", exc_info=True)
        # Return default sectors on error
        sectors = get_default_sectors()
        return SectorsResponse(
            sectors=sectors,
            total=len(sectors)
        )


@router.post("/refresh", response_model=SectorsResponse)
async def refresh_sectors():
    """
    Force refresh sectors list from akshare
    
    This endpoint bypasses the cache and fetches fresh data from akshare.
    
    Returns:
        SectorsResponse with refreshed list of sector names
    """
    try:
        # Delete cache first
        redis_client = get_redis_client()
        redis_client.delete(SECTORS_CACHE_KEY)
        
        # Fetch fresh data
        sectors = fetch_sectors_from_akshare()
        
        if not sectors:
            sectors = get_default_sectors()
        
        # Store in cache
        import json
        redis_client.set(SECTORS_CACHE_KEY, json.dumps(sectors, ensure_ascii=False), SECTORS_CACHE_TTL)
        
        return SectorsResponse(
            sectors=sectors,
            total=len(sectors)
        )
        
    except Exception as e:
        logger.error(f"Failed to refresh sectors: {e}", exc_info=True)
        sectors = get_default_sectors()
        return SectorsResponse(
            sectors=sectors,
            total=len(sectors)
        )
