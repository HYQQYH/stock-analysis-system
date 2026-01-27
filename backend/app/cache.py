"""Cache management module with decorators and utilities."""
import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime, timedelta

from app.db.redis_cache import get_redis_client

logger = logging.getLogger(__name__)


# Cache key naming conventions
class CacheKeys:
    """Standard cache key patterns."""
    
    # K-line data
    KLINE = "kline"
    KLINE_PATTERN = "kline:*"
    
    # Indicators
    INDICATOR = "indicator"
    INDICATOR_PATTERN = "indicator:*"
    
    # Market data
    MARKET_SENTIMENT = "market:sentiment"
    MARKET_FUND_FLOW = "market:fund_flow"
    MARKET_ACTIVITY = "market:activity"
    MARKET_PATTERN = "market:*"
    
    # Limit up pool
    LIMIT_UP = "limit_up"
    LIMIT_UP_PATTERN = "limit_up:*"
    
    # Analysis results
    ANALYSIS = "analysis"
    ANALYSIS_PATTERN = "analysis:*"
    
    # Stock info
    STOCK_INFO = "stock:info"
    STOCK_INFO_PATTERN = "stock:info:*"
    
    # News
    NEWS = "news"
    NEWS_PATTERN = "news:*"


def build_cache_key(prefix: str, *args, **kwargs) -> str:
    """Build a standardized cache key.
    
    Args:
        prefix: Key prefix (e.g., 'kline', 'indicator')
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
        
    Returns:
        Formatted cache key
    """
    parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if arg is not None:
            parts.append(str(arg))
    
    # Add keyword arguments in sorted order for consistency
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        for key, value in sorted_kwargs:
            if value is not None:
                parts.append(f"{key}:{value}")
    
    return ":".join(parts)


def hash_args(*args, **kwargs) -> str:
    """Create a hash from function arguments for use in cache keys.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        SHA256 hash string
    """
    # Convert args and kwargs to a stable string representation
    args_str = json.dumps(
        {
            "args": args,
            "kwargs": kwargs
        },
        sort_keys=True,
        default=str
    )
    return hashlib.sha256(args_str.encode()).hexdigest()[:16]


def cache_result(prefix: str = None, ttl: int = 3600, 
                 key_builder: Callable = None, 
                 skip_args: List[int] = None,
                 cache_none: bool = False):
    """Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix. If None, uses function name.
        ttl: Time to live in seconds (default: 1 hour)
        key_builder: Custom function to build cache key. If None, uses default builder.
        skip_args: Indices of positional args to skip in key generation
        cache_none: Whether to cache None results (default: False)
        
    Usage:
        @cache_result(ttl=1800)
        def get_stock_data(code: str, period: str):
            # Expensive operation
            return data
    """
    def decorator(func: Callable):
        # Use function name as prefix if not provided
        actual_prefix = prefix if prefix else func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            redis = get_redis_client()
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Filter out skipped args
                filtered_args = [arg for i, arg in enumerate(args) 
                                if not skip_args or i not in skip_args]
                
                # Build key from function name and arguments
                arg_hash = hash_args(*filtered_args, **kwargs)
                cache_key = build_cache_key(actual_prefix, arg_hash)
            
            # Try to get from cache
            try:
                cached_value = redis.get_json(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_value
            except Exception as e:
                logger.warning(f"Error reading from cache: {e}")
            
            # Execute function if not in cache
            try:
                result = func(*args, **kwargs)
                
                # Cache the result
                if result is not None or cache_none:
                    try:
                        # Convert result to JSON-serializable format
                        if hasattr(result, 'to_dict'):  # For SQLAlchemy models
                            cache_value = result.to_dict()
                        elif hasattr(result, '__dict__'):  # For objects
                            cache_value = result.__dict__
                        elif isinstance(result, (list, dict, str, int, float, bool)):
                            cache_value = result
                        else:
                            # For other types, try to convert to string
                            cache_value = str(result)
                        
                        redis.set_json(cache_key, cache_value, ttl=ttl)
                        logger.debug(f"Cached result for key: {cache_key} (TTL: {ttl}s)")
                    except Exception as e:
                        logger.warning(f"Error caching result: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error executing function {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern.
    
    Args:
        pattern: Redis key pattern (e.g., 'kline:*', 'market:*')
        
    Returns:
        Number of keys deleted
    """
    redis = get_redis_client()
    
    try:
        count = redis.delete_pattern(pattern)
        logger.info(f"Invalidated {count} cache keys matching pattern: {pattern}")
        return count
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")
        return 0


def invalidate_stock_cache(stock_code: str) -> int:
    """Invalidate all cache keys for a specific stock.
    
    Args:
        stock_code: Stock code (e.g., '600000')
        
    Returns:
        Number of keys deleted
    """
    patterns = [
        f"kline:{stock_code}:*",
        f"indicator:{stock_code}:*",
        f"analysis:*:{stock_code}:*",
    ]
    
    total_deleted = 0
    for pattern in patterns:
        total_deleted += invalidate_cache(pattern)
    
    logger.info(f"Invalidated {total_deleted} cache keys for stock: {stock_code}")
    return total_deleted


def get_cache_stats(pattern: str = "*") -> Dict[str, Any]:
    """Get statistics about cached data.
    
    Args:
        pattern: Key pattern to match (default: all keys)
        
    Returns:
        Dictionary with cache statistics
    """
    redis = get_redis_client()
    client = redis.client
    
    try:
        keys = client.keys(pattern)
        
        if not keys:
            return {
                "total_keys": 0,
                "pattern": pattern,
                "keys": []
            }
        
        # Get TTL for each key
        stats = {
            "total_keys": len(keys),
            "pattern": pattern,
            "sample_keys": keys[:10] if len(keys) > 10 else keys,
            "expired_count": 0,
            "non_expired_count": 0
        }
        
        # Sample TTL information
        ttl_info = {}
        for key in keys[:20]:  # Sample first 20 keys
            ttl = client.ttl(key)
            if ttl == -2:  # Key doesn't exist
                pass
            elif ttl == -1:  # Key has no expiration
                ttl_info[key] = "no_expiration"
                stats["non_expired_count"] += 1
            else:
                ttl_info[key] = f"{ttl}s"
                stats["non_expired_count"] += 1
        
        stats["sample_ttl"] = ttl_info
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "error": str(e),
            "pattern": pattern
        }


def clear_all_cache() -> bool:
    """Clear all cache keys (use with caution!).
    
    Returns:
        True if successful, False otherwise
    """
    redis = get_redis_client()
    
    try:
        result = redis.clear_all()
        logger.warning("All cache keys cleared")
        return result
    except Exception as e:
        logger.error(f"Error clearing all cache: {e}")
        return False


class CachePreheater:
    """Cache preheating utility for warming up cache with frequently accessed data."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.preheat_tasks = []
    
    def add_task(self, func: Callable, *args, **kwargs):
        """Add a preheating task.
        
        Args:
            func: Function to execute for preheating
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function
        """
        self.preheat_tasks.append({
            'func': func,
            'args': args,
            'kwargs': kwargs
        })
    
    def preheat_cache(self, ttl: int = 3600) -> Dict[str, Any]:
        """Execute all preheating tasks.
        
        Args:
            ttl: Default TTL for preheated data
            
        Returns:
            Summary of preheating results
        """
        results = {
            'total_tasks': len(self.preheat_tasks),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Starting cache preheating with {len(self.preheat_tasks)} tasks")
        
        for i, task in enumerate(self.preheat_tasks):
            func = task['func']
            args = task['args']
            kwargs = task['kwargs']
            
            try:
                logger.info(f"Executing preheat task {i+1}/{len(self.preheat_tasks)}: {func.__name__}")
                
                # Execute the function (which should use @cache_result decorator)
                result = func(*args, **kwargs)
                
                # If the function doesn't use @cache_result, manually cache the result
                if result is not None:
                    # Build cache key
                    cache_key = build_cache_key(
                        func.__name__,
                        *args[1:],  # Skip 'self' if present
                        **kwargs
                    )
                    
                    try:
                        self.redis.set_json(cache_key, result, ttl=ttl)
                    except Exception as e:
                        logger.warning(f"Error caching result for {func.__name__}: {e}")
                
                results['successful'] += 1
                logger.info(f"Preheat task {i+1} completed successfully")
                
            except Exception as e:
                results['failed'] += 1
                error_msg = f"Task {i+1} ({func.__name__}) failed: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Cache preheating completed: {results['successful']}/{results['total_tasks']} tasks successful")
        
        return results
    
    def clear_tasks(self):
        """Clear all preheating tasks."""
        self.preheat_tasks.clear()
        logger.info("Preheating tasks cleared")


# Global preheater instance (lazy initialization)
_preheater = None


def get_cache_preheater() -> CachePreheater:
    """Get the global cache preheater instance."""
    global _preheater
    if _preheater is None:
        _preheater = CachePreheater()
    return _preheater


def async_cache_invalidate(func: Callable):
    """Decorator to automatically invalidate related cache after function execution.
    
    This is a placeholder for future async invalidation logic.
    For now, it just logs the invalidation.
    
    Usage:
        @async_cache_invalidate
        def update_stock_data(code: str, data: dict):
            # Update database
            pass
            
            # Cache for stock_code will be invalidated automatically
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Extract stock code from args or kwargs for invalidation
            stock_code = None
            
            # Try to get stock_code from first argument (if it's a string)
            if args and isinstance(args[1], str) and args[1].isdigit():
                stock_code = args[1]
            
            # Or from kwargs
            if not stock_code and 'stock_code' in kwargs:
                stock_code = kwargs['stock_code']
            elif not stock_code and 'code' in kwargs:
                stock_code = kwargs['code']
            
            if stock_code:
                invalidate_stock_cache(stock_code)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in cache invalidation wrapper for {func.__name__}: {e}")
            raise
    
    return wrapper