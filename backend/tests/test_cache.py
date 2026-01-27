"""Tests for cache management module."""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from app.cache import (
    cache_result,
    invalidate_cache,
    invalidate_stock_cache,
    get_cache_stats,
    clear_all_cache,
    build_cache_key,
    hash_args,
    CacheKeys,
    CachePreheater,
    get_cache_preheater
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    with patch('app.cache.get_redis_client') as mock:
        redis_mock = Mock()
        mock.return_value = redis_mock
        yield redis_mock


class TestCacheKeyBuilding:
    """Test cache key building functions."""
    
    def test_build_cache_key_with_prefix(self):
        """Test building cache key with prefix."""
        key = build_cache_key("kline", "600000", "daily")
        assert key == "kline:600000:daily"
    
    def test_build_cache_key_with_kwargs(self):
        """Test building cache key with keyword arguments."""
        key = build_cache_key("indicator", code="600000", type="MACD")
        assert key == "indicator:code:600000:type:MACD"
    
    def test_build_cache_key_with_none(self):
        """Test that None values are skipped."""
        key = build_cache_key("kline", "600000", None, period="daily")
        assert key == "kline:600000:period:daily"
    
    def test_hash_args_consistency(self):
        """Test that hash_args produces consistent results."""
        args1 = ("600000", "daily")
        kwargs1 = {"limit": 100}
        
        args2 = ("600000", "daily")
        kwargs2 = {"limit": 100}
        
        hash1 = hash_args(*args1, **kwargs1)
        hash2 = hash_args(*args2, **kwargs2)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of SHA256
    
    def test_hash_args_order_independence(self):
        """Test that kwargs order doesn't affect hash."""
        hash1 = hash_args("600000", a=1, b=2, c=3)
        hash2 = hash_args("600000", c=3, a=1, b=2)
        
        assert hash1 == hash2


class TestCacheDecorator:
    """Test cache_result decorator."""
    
    def test_cache_result_first_call_executes_function(self, mock_redis):
        """Test that first call executes function and caches result."""
        mock_redis.get_json.return_value = None  # Cache miss
        
        call_count = 0
        
        @cache_result(prefix="test", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result = expensive_function(5)
        
        # Function should be called once
        assert call_count == 1
        assert result == 10
        
        # Result should be cached
        mock_redis.set_json.assert_called_once()
    
    def test_cache_result_second_call_from_cache(self, mock_redis):
        """Test that second call returns from cache."""
        mock_redis.get_json.return_value = {"value": 20}  # Cache hit
        
        call_count = 0
        
        @cache_result(prefix="test", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result = expensive_function(10)
        
        # Function should not be called (from cache)
        assert call_count == 0
        assert result == {"value": 20}
        
        # Should not set cache (already cached)
        mock_redis.set_json.assert_not_called()
    
    def test_cache_result_with_custom_ttl(self, mock_redis):
        """Test that custom TTL is used."""
        mock_redis.get_json.return_value = None
        
        @cache_result(prefix="test", ttl=300)
        def expensive_function(x):
            return x * 2
        
        expensive_function(5)
        
        # Check that TTL is 300 (may be positional or keyword arg)
        call_args = mock_redis.set_json.call_args
        if len(call_args[0]) > 2:
            assert call_args[0][2] == 300
        elif 'ttl' in call_args[1]:
            assert call_args[1]['ttl'] == 300
    
    def test_cache_result_with_custom_prefix(self, mock_redis):
        """Test that custom prefix is used."""
        mock_redis.get_json.return_value = None
        
        @cache_result(prefix="custom_prefix", ttl=60)
        def expensive_function(x):
            return x * 2
        
        expensive_function(5)
        
        # Check that prefix is in key
        set_json_call = mock_redis.set_json.call_args
        cache_key = set_json_call[0][0]
        assert cache_key.startswith("custom_prefix")
    
    def test_cache_result_with_none_result(self, mock_redis):
        """Test that None results are not cached by default."""
        mock_redis.get_json.return_value = None
        
        @cache_result(prefix="test", ttl=60, cache_none=False)
        def function_returning_none(x):
            return None
        
        result = function_returning_none(5)
        
        assert result is None
        mock_redis.set_json.assert_not_called()
    
    def test_cache_result_with_none_result_cached(self, mock_redis):
        """Test that None results are cached when cache_none=True."""
        mock_redis.get_json.return_value = None
        
        @cache_result(prefix="test", ttl=60, cache_none=True)
        def function_returning_none(x):
            return None
        
        function_returning_none(5)
        
        # Should cache None
        mock_redis.set_json.assert_called_once()
    
    def test_cache_result_skip_args(self, mock_redis):
        """Test that skip_args parameter works."""
        mock_redis.get_json.return_value = None
        
        @cache_result(prefix="test", ttl=60, skip_args=[0])
        def expensive_function(self, x):
            return x * 2
        
        # Simulate method call with self
        class Dummy:
            pass
        dummy = Dummy()
        
        expensive_function(dummy, 5)
        
        # Check that first arg (self) was skipped
        set_json_call = mock_redis.set_json.call_args
        cache_key = set_json_call[0][0]
        assert "Dummy" not in cache_key


class TestCacheInvalidation:
    """Test cache invalidation functions."""
    
    def test_invalidate_cache_by_pattern(self, mock_redis):
        """Test invalidating cache by pattern."""
        mock_redis.delete_pattern.return_value = 5
        
        count = invalidate_cache("kline:*")
        
        assert count == 5
        mock_redis.delete_pattern.assert_called_once_with("kline:*")
    
    def test_invalidate_cache_error_handling(self, mock_redis):
        """Test error handling in invalidate_cache."""
        mock_redis.delete_pattern.side_effect = Exception("Redis error")
        
        count = invalidate_cache("kline:*")
        
        # Should return 0 on error
        assert count == 0
    
    def test_invalidate_stock_cache(self, mock_redis):
        """Test invalidating cache for specific stock."""
        mock_redis.delete_pattern.return_value = 3
        
        count = invalidate_stock_cache("600000")
        
        # Should call invalidate_cache multiple times
        assert mock_redis.delete_pattern.call_count == 3
        # Total deleted should be sum of all patterns
        assert count == 9  # 3 patterns * 3 keys each
    
    def test_clear_all_cache(self, mock_redis):
        """Test clearing all cache."""
        mock_redis.clear_all.return_value = True
        
        result = clear_all_cache()
        
        assert result is True
        mock_redis.clear_all.assert_called_once()


class TestCacheStats:
    """Test cache statistics functions."""
    
    def test_get_cache_stats_with_keys(self, mock_redis):
        """Test getting cache stats with keys."""
        mock_redis.client.keys.return_value = ["kline:600000:daily", "indicator:600000:MACD"]
        mock_redis.client.ttl.side_effect = [3600, -1]  # 1 hour TTL, no expiration
        
        stats = get_cache_stats("kline:*")
        
        assert stats['total_keys'] == 2
        assert 'sample_keys' in stats
        assert len(stats['sample_keys']) == 2
    
    def test_get_cache_stats_empty(self, mock_redis):
        """Test getting cache stats when no keys match."""
        mock_redis.client.keys.return_value = []
        
        stats = get_cache_stats("nonexistent:*")
        
        assert stats['total_keys'] == 0
        assert stats['keys'] == []
    
    def test_get_cache_stats_error_handling(self, mock_redis):
        """Test error handling in get_cache_stats."""
        mock_redis.client.keys.side_effect = Exception("Redis error")
        
        stats = get_cache_stats("kline:*")
        
        assert 'error' in stats


class TestCachePreheater:
    """Test cache preheating functionality."""
    
    def test_add_preheat_task(self, mock_redis):
        """Test adding preheating tasks."""
        with patch('app.cache.get_redis_client') as mock:
            mock.return_value = mock_redis
            preheater = CachePreheater()
        
        def dummy_task(x):
            return x * 2
        
        preheater.add_task(dummy_task, 5)
        
        assert len(preheater.preheat_tasks) == 1
    
    def test_preheat_cache_success(self, mock_redis):
        """Test successful cache preheating."""
        with patch('app.cache.get_redis_client') as mock:
            mock.return_value = mock_redis
            preheater = CachePreheater()
        
        def task1(x):
            return x * 2
        
        def task2(x):
            return x * 3
        
        preheater.add_task(task1, 5)
        preheater.add_task(task2, 10)
        
        results = preheater.preheat_cache(ttl=3600)
        
        assert results['total_tasks'] == 2
        assert results['successful'] == 2
        assert results['failed'] == 0
        assert 'timestamp' in results
    
    def test_preheat_cache_with_failure(self, mock_redis):
        """Test preheating with task failures."""
        with patch('app.cache.get_redis_client') as mock:
            mock.return_value = mock_redis
            preheater = CachePreheater()
        
        def success_task(x):
            return x * 2
        
        def failing_task(x):
            raise ValueError("Task failed")
        
        preheater.add_task(success_task, 5)
        preheater.add_task(failing_task, 10)
        
        results = preheater.preheat_cache()
        
        assert results['successful'] == 1
        assert results['failed'] == 1
        assert len(results['errors']) == 1
    
    def test_clear_tasks(self, mock_redis):
        """Test clearing preheating tasks."""
        with patch('app.cache.get_redis_client') as mock:
            mock.return_value = mock_redis
            preheater = CachePreheater()
        
        def dummy_task(x):
            return x * 2
        
        preheater.add_task(dummy_task, 5)
        preheater.add_task(dummy_task, 10)
        
        assert len(preheater.preheat_tasks) == 2
        
        preheater.clear_tasks()
        
        assert len(preheater.preheat_tasks) == 0
    
    def test_get_global_preheater(self, mock_redis):
        """Test getting global preheater instance."""
        with patch('app.cache.get_redis_client') as mock:
            mock.return_value = mock_redis
            # Reset global preheater
            import app.cache
            app.cache._preheater = None
            preheater = get_cache_preheater()
        
        assert isinstance(preheater, CachePreheater)


class TestCacheKeys:
    """Test CacheKeys constants."""
    
    def test_cache_keys_constants(self):
        """Test that CacheKeys constants are defined."""
        assert hasattr(CacheKeys, 'KLINE')
        assert hasattr(CacheKeys, 'INDICATOR')
        assert hasattr(CacheKeys, 'MARKET_SENTIMENT')
        assert hasattr(CacheKeys, 'LIMIT_UP')
        assert hasattr(CacheKeys, 'ANALYSIS')
        
        # Check pattern constants
        assert hasattr(CacheKeys, 'KLINE_PATTERN')
        assert hasattr(CacheKeys, 'INDICATOR_PATTERN')
        assert hasattr(CacheKeys, 'MARKET_PATTERN')


class TestCacheIntegration:
    """Integration tests for cache functionality."""
    
    def test_cache_miss_then_hit(self, mock_redis):
        """Test cache miss followed by cache hit."""
        mock_redis.get_json.side_effect = [None, {"value": 20}]
        
        call_count = 0
        
        @cache_result(prefix="test", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call - cache miss
        result1 = expensive_function(10)
        assert call_count == 1
        assert result1 == 20
        
        # Second call - cache hit
        result2 = expensive_function(10)
        assert call_count == 1  # Still 1, not called again
        assert result2 == {"value": 20}
    
    def test_different_args_different_cache(self, mock_redis):
        """Test that different arguments produce different cache entries."""
        mock_redis.get_json.return_value = None
        
        call_count = 0
        
        @cache_result(prefix="test", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        expensive_function(5)
        expensive_function(10)
        
        # Both should execute and cache separately
        assert call_count == 2
        assert mock_redis.set_json.call_count == 2
    
    def test_cache_key_uniqueness(self, mock_redis):
        """Test that different functions produce different cache keys."""
        mock_redis.get_json.return_value = None
        
        @cache_result(prefix="func1", ttl=60)
        def func1(x):
            return x * 2
        
        @cache_result(prefix="func2", ttl=60)
        def func2(x):
            return x * 3
        
        func1(5)
        func2(5)
        
        # Get the cache keys from set_json calls
        keys = [call[0][0] for call in mock_redis.set_json.call_args_list]
        
        # Keys should be different
        assert len(keys) == 2
        assert keys[0] != keys[1]
        assert "func1" in keys[0]
        assert "func2" in keys[1]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])