"""Test script for indicator calculation, storage, and caching"""
import logging
import sys
from datetime import datetime, timedelta
import os

# Add backend app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from app.services.indicator_calculator import IndicatorCalculator
from app.services.indicator_manager import IndicatorManager
from app.services.data_collector import DataCollector
from app.db.database import SessionLocal, init_db
from app.db.redis_cache import get_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_kline_data(rows=120):
    """Create synthetic K-line data for testing"""
    # Generate dates (last 120 trading days)
    dates = pd.date_range(end=datetime.now(), periods=rows, freq='D')
    
    # Generate synthetic OHLCV data with some randomness
    np.random.seed(42)  # For reproducible results
    
    base_price = 10.0
    returns = np.random.normal(0.001, 0.02, rows)
    prices = base_price * (1 + returns).cumprod()
    
    # Create DataFrame with OHLCV data
    data = {
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, rows)),
        'high': prices * (1 + np.random.uniform(0, 0.02, rows)),
        'low': prices * (1 + np.random.uniform(-0.02, 0, rows)),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, rows),
        'amount': prices * np.random.randint(1000000, 10000000, rows),
        'change_pct': returns * 100,
        'turnover': np.random.uniform(1, 10, rows)
    }
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def test_indicator_calculation():
    """Test 1: Indicator Calculation"""
    logger.info("=" * 60)
    logger.info("TEST 1: Indicator Calculation")
    logger.info("=" * 60)
    
    # Create test data
    kline_df = create_test_kline_data(120)
    logger.info(f"Created test K-line data with {len(kline_df)} rows")
    logger.info(f"Columns: {kline_df.columns.tolist()}")
    logger.info(f"\nFirst 3 rows:\n{kline_df.head(3)}")
    
    # Initialize calculator
    calculator = IndicatorCalculator()
    
    # Test MACD calculation
    logger.info("\n--- Testing MACD Calculation ---")
    macd_df = calculator.calculate_macd(kline_df)
    logger.info(f"MACD DataFrame columns: {macd_df.columns.tolist()}")
    macd_cols = [col for col in macd_df.columns if col.startswith('MACD_')]
    logger.info(f"MACD indicator columns: {macd_cols}")
    logger.info(f"\nLast 5 MACD values:\n{macd_df[macd_cols].tail()}")
    
    # Test KDJ calculation
    logger.info("\n--- Testing KDJ Calculation ---")
    kdj_df = calculator.calculate_kdj(kline_df)
    logger.info(f"KDJ DataFrame columns: {kdj_df.columns.tolist()}")
    kdj_cols = [col for col in kdj_df.columns if col.startswith('KDJ_')]
    logger.info(f"KDJ indicator columns: {kdj_cols}")
    logger.info(f"\nLast 5 KDJ values:\n{kdj_df[kdj_cols].tail()}")
    
    # Test RSI calculation
    logger.info("\n--- Testing RSI Calculation ---")
    rsi_df = calculator.calculate_rsi(kline_df)
    logger.info(f"RSI DataFrame columns: {rsi_df.columns.tolist()}")
    rsi_cols = [col for col in rsi_df.columns if col.startswith('RSI_')]
    logger.info(f"RSI indicator columns: {rsi_cols}")
    logger.info(f"\nLast 5 RSI values:\n{rsi_df[rsi_cols].tail()}")
    
    # Test all indicators at once
    logger.info("\n--- Testing All Indicators Calculation ---")
    all_df = calculator.calculate_all_indicators(kline_df)
    logger.info(f"All indicators DataFrame shape: {all_df.shape}")
    indicator_cols = [col for col in all_df.columns if col.startswith(('MACD_', 'KDJ_', 'RSI_'))]
    logger.info(f"Total indicator columns: {len(indicator_cols)}")
    logger.info(f"Indicator columns: {indicator_cols}")
    
    # Validate indicators
    logger.info("\n--- Validating Indicators ---")
    validation = calculator.validate_indicators(all_df)
    logger.info(f"Validation result: {'PASSED' if validation['valid'] else 'FAILED'}")
    if validation['issues']:
        logger.warning("Validation issues:")
        for issue in validation['issues']:
            logger.warning(f"  - {issue}")
    else:
        logger.info("All indicators are within expected ranges!")
    
    # Check RSI range (0-100)
    if 'RSI_14' in all_df.columns:
        rsi_values = all_df['RSI_14'].dropna()
        logger.info(f"RSI range: [{rsi_values.min():.2f}, {rsi_values.max():.2f}]")
        logger.info(f"RSI mean: {rsi_values.mean():.2f}")
    
    # Check KDJ K and D range (0-100)
    if 'KDJ_K' in all_df.columns:
        k_values = all_df['KDJ_K'].dropna()
        logger.info(f"KDJ_K range: [{k_values.min():.2f}, {k_values.max():.2f}]")
    
    logger.info("\n✓ TEST 1 COMPLETED: Indicator calculation successful")
    return all_df


def test_database_storage(indicators_df):
    """Test 2: Database Storage"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Database Storage")
    logger.info("=" * 60)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize indicator manager
        manager = IndicatorManager(db=db)
        
        # Test saving indicators
        test_code = "600001"  # Test stock code
        test_period = "day"
        
        logger.info(f"Saving indicators for {test_code} ({test_period})...")
        save_result = manager.save_indicators(test_code, test_period, indicators_df)
        
        if save_result:
            logger.info("✓ Indicators saved to database successfully")
        else:
            logger.error("✗ Failed to save indicators to database")
            return False
        
        # Test retrieving indicators from database
        logger.info("\nRetrieving indicators from database...")
        retrieved_df = manager.get_indicators(test_code, test_period, from_cache=False, db=db)
        
        if retrieved_df is not None:
            logger.info(f"✓ Retrieved {len(retrieved_df)} indicator records from database")
            logger.info(f"Retrieved columns: {retrieved_df.columns.tolist()}")
            logger.info(f"\nLast 3 retrieved records:\n{retrieved_df.tail(3)}")
        else:
            logger.error("✗ Failed to retrieve indicators from database")
            return False
        
        # Verify data integrity
        logger.info("\nVerifying data integrity...")
        original_cols = set(indicators_df.columns)
        retrieved_cols = set(retrieved_df.columns)
        indicator_cols = original_cols.intersection(retrieved_cols)
        logger.info(f"Matching columns: {len(indicator_cols)}")
        
        if len(indicator_cols) > 0:
            logger.info("✓ Database storage and retrieval successful")
            return True
        else:
            logger.error("✗ Data integrity check failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during database storage test: {e}")
        return False
    finally:
        db.close()


def test_redis_caching(indicators_df):
    """Test 3: Redis Caching"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Redis Caching")
    logger.info("=" * 60)
    
    try:
        # Initialize indicator manager (without DB session for cache-only test)
        manager = IndicatorManager()
        
        # Test caching indicators
        test_code = "600002"
        test_period = "day"
        
        logger.info(f"Caching indicators for {test_code} ({test_period})...")
        cache_result = manager.cache_indicators(test_code, test_period, indicators_df, ttl=3600)
        
        if cache_result:
            logger.info("✓ Indicators cached to Redis successfully")
        else:
            logger.error("✗ Failed to cache indicators to Redis")
            return False
        
        # Test retrieving from cache
        logger.info("\nRetrieving indicators from Redis...")
        cached_df = manager._get_from_cache(test_code, test_period)
        
        if cached_df is not None:
            logger.info(f"✓ Retrieved indicators from cache ({len(cached_df)} records)")
            logger.info(f"Cached columns: {cached_df.columns.tolist()}")
            logger.info(f"\nLast 3 cached records:\n{cached_df.tail(3)}")
        else:
            logger.error("✗ Failed to retrieve indicators from cache")
            return False
        
        # Test cache invalidation
        logger.info("\nTesting cache invalidation...")
        deleted = manager.invalidate_cache(test_code, test_period)
        logger.info(f"✓ Cache invalidated: {deleted} key(s) deleted")
        
        # Verify cache is cleared
        logger.info("\nVerifying cache is cleared...")
        cleared_df = manager._get_from_cache(test_code, test_period)
        if cleared_df is None:
            logger.info("✓ Cache successfully cleared")
        else:
            logger.error("✗ Cache not properly cleared")
            return False
        
        logger.info("\n✓ TEST 3 COMPLETED: Redis caching successful")
        return True
        
    except Exception as e:
        logger.error(f"Error during Redis caching test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow():
    """Test 4: Full Workflow (Calculate -> Save -> Cache -> Retrieve)"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Full Workflow Integration")
    logger.info("=" * 60)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create test data
        kline_df = create_test_kline_data(120)
        
        # Initialize calculator and manager
        calculator = IndicatorCalculator()
        manager = IndicatorManager(db=db)
        
        test_code = "600003"
        test_period = "week"
        
        # Step 1: Calculate indicators
        logger.info(f"\nStep 1: Calculating indicators for {test_code}...")
        indicators_df = calculator.calculate_all_indicators(kline_df)
        logger.info(f"✓ Calculated {len(indicators_df)} indicator records")
        
        # Step 2: Save to database
        logger.info(f"\nStep 2: Saving indicators to database...")
        save_result = manager.save_indicators(test_code, test_period, indicators_df)
        if save_result:
            logger.info("✓ Saved to database")
        else:
            logger.error("✗ Failed to save to database")
            return False
        
        # Step 3: Cache to Redis
        logger.info(f"\nStep 3: Caching indicators to Redis...")
        cache_result = manager.cache_indicators(test_code, test_period, indicators_df)
        if cache_result:
            logger.info("✓ Cached to Redis")
        else:
            logger.error("✗ Failed to cache to Redis")
            return False
        
        # Step 4: Retrieve from cache (should hit cache first)
        logger.info(f"\nStep 4: Retrieving from cache (should hit cache)...")
        cached_df = manager.get_indicators(test_code, test_period, from_cache=True, db=db)
        if cached_df is not None:
            logger.info(f"✓ Retrieved from cache ({len(cached_df)} records)")
        else:
            logger.error("✗ Failed to retrieve from cache")
            return False
        
        # Step 5: Invalidate cache and retrieve from database
        logger.info(f"\nStep 5: Invalidating cache and retrieving from database...")
        manager.invalidate_cache(test_code, test_period)
        db_df = manager.get_indicators(test_code, test_period, from_cache=True, db=db)
        if db_df is not None:
            logger.info(f"✓ Retrieved from database after cache miss ({len(db_df)} records)")
        else:
            logger.error("✗ Failed to retrieve from database")
            return False
        
        # Step 6: Get latest indicators
        logger.info(f"\nStep 6: Getting latest 3 indicators...")
        latest_df = manager.get_latest_indicators(test_code, test_period, n=3, db=db)
        if latest_df is not None:
            logger.info(f"✓ Retrieved latest {len(latest_df)} indicators")
            logger.info(f"\nLatest indicators:\n{latest_df}")
        else:
            logger.error("✗ Failed to get latest indicators")
            return False
        
        logger.info("\n✓ TEST 4 COMPLETED: Full workflow successful")
        return True
        
    except Exception as e:
        logger.error(f"Error during full workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Main test runner"""
    logger.info("\n" + "=" * 60)
    logger.info("INDICATOR SYSTEM TEST SUITE")
    logger.info("=" * 60)
    
    test_results = []
    
    # Test 1: Indicator Calculation
    try:
        indicators_df = test_indicator_calculation()
        test_results.append(("Indicator Calculation", "PASSED" if indicators_df is not None else "FAILED"))
    except Exception as e:
        logger.error(f"Test 1 failed with exception: {e}")
        test_results.append(("Indicator Calculation", "FAILED"))
        indicators_df = None
    
    # Test 2: Database Storage (only if Test 1 passed)
    if indicators_df is not None:
        try:
            result = test_database_storage(indicators_df)
            test_results.append(("Database Storage", "PASSED" if result else "FAILED"))
        except Exception as e:
            logger.error(f"Test 2 failed with exception: {e}")
            test_results.append(("Database Storage", "FAILED"))
    else:
        test_results.append(("Database Storage", "SKIPPED"))
    
    # Test 3: Redis Caching (only if Test 1 passed)
    if indicators_df is not None:
        try:
            result = test_redis_caching(indicators_df)
            test_results.append(("Redis Caching", "PASSED" if result else "FAILED"))
        except Exception as e:
            logger.error(f"Test 3 failed with exception: {e}")
            test_results.append(("Redis Caching", "FAILED"))
    else:
        test_results.append(("Redis Caching", "SKIPPED"))
    
    # Test 4: Full Workflow
    try:
        result = test_full_workflow()
        test_results.append(("Full Workflow", "PASSED" if result else "FAILED"))
    except Exception as e:
        logger.error(f"Test 4 failed with exception: {e}")
        test_results.append(("Full Workflow", "FAILED"))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    for test_name, result in test_results:
        status_symbol = "✓" if result == "PASSED" else "✗" if result == "FAILED" else "○"
        logger.info(f"{status_symbol} {test_name}: {result}")
    
    passed = sum(1 for _, r in test_results if r == "PASSED")
    total = len(test_results)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)