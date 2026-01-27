"""Tests for data processing service."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.services.data_processor import DataProcessor


@pytest.fixture
def processor():
    """Create a DataProcessor instance for testing."""
    return DataProcessor()


@pytest.fixture
def sample_kline_data():
    """Create sample K-line data for testing with valid OHLC relationships."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Generate base prices
    base_prices = 10.0 + np.random.rand(100) * 5
    
    # Ensure valid OHLC: high >= max(open, close), low <= min(open, close)
    open_price = base_prices
    close_price = base_prices + np.random.rand(100) * 2 - 1  # Close near open
    high_price = np.maximum(open_price, close_price) + np.random.rand(100) * 2
    low_price = np.minimum(open_price, close_price) - np.random.rand(100) * 2
    
    data = {
        'trade_date': dates,
        'open_price': open_price,
        'high_price': high_price,
        'low_price': low_price,
        'close_price': close_price,
        'volume': np.random.randint(1000000, 10000000, 100),
        'amount': np.random.rand(100) * 100000000,
    }
    return pd.DataFrame(data)


@pytest.fixture
def dirty_kline_data():
    """Create dirty K-line data with duplicates and missing values."""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    data = {
        'trade_date': dates,
        'open_price': [10.0] * 20 + [np.nan] * 10 + [12.0] * 20,
        'high_price': [12.0] * 20 + [13.0] * 10 + [14.0] * 20,
        'low_price': [8.0] * 20 + [7.0] * 10 + [9.0] * 20,
        'close_price': [10.0] * 20 + [np.nan] * 5 + [11.0] * 25,
        'volume': [1000000] * 40 + [np.nan] * 10,
        'amount': [50000000] * 45 + [np.nan] * 5,
    }
    df = pd.DataFrame(data)
    
    # Add duplicate rows
    df = pd.concat([df, df.iloc[5:10]], ignore_index=True)
    
    return df


@pytest.fixture
def raw_column_data():
    """Create data with raw column names from akshare."""
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    data = {
        '日期': dates,
        '开盘': 10.0 + np.random.rand(30) * 5,
        '最高': 12.0 + np.random.rand(30) * 5,
        '最低': 8.0 + np.random.rand(30) * 5,
        '收盘': 10.0 + np.random.rand(30) * 5,
        '成交量': np.random.randint(1000000, 10000000, 30),
        '成交额': np.random.rand(30) * 100000000,
    }
    return pd.DataFrame(data)


class TestDataProcessor:
    """Test suite for DataProcessor class."""
    
    def test_clean_kline_data_removes_duplicates(self, processor, dirty_kline_data):
        """Test that cleaning removes duplicate rows."""
        before_count = len(dirty_kline_data)
        cleaned = processor.clean_kline_data(dirty_kline_data)
        after_count = len(cleaned)
        
        # Should have removed 5 duplicate rows
        assert after_count < before_count
        assert after_count == before_count - 5
    
    def test_clean_kline_data_fills_missing_values(self, processor, dirty_kline_data):
        """Test that cleaning fills missing values."""
        cleaned = processor.clean_kline_data(dirty_kline_data)
        
        # Check no NaN values in price columns
        assert cleaned['open_price'].isna().sum() == 0
        assert cleaned['close_price'].isna().sum() == 0
        
        # Check no NaN values in numeric columns
        assert cleaned['volume'].isna().sum() == 0
        assert cleaned['amount'].isna().sum() == 0
    
    def test_clean_kline_data_removes_invalid_dates(self, processor):
        """Test that cleaning removes rows with invalid dates."""
        dates = ['2024-01-01', 'invalid_date', '2024-01-03']
        data = {
            'trade_date': dates,
            'open_price': [10.0, 11.0, 12.0],
            'high_price': [12.0, 13.0, 14.0],
            'low_price': [8.0, 9.0, 10.0],
            'close_price': [10.0, 11.0, 12.0],
        }
        df = pd.DataFrame(data)
        
        cleaned = processor.clean_kline_data(df)
        
        # Should have removed the row with invalid date
        assert len(cleaned) == 2
        assert all(isinstance(d, (pd.Timestamp, datetime)) for d in cleaned['trade_date'])
    
    def test_clean_kline_data_sorts_by_date(self, processor, sample_kline_data):
        """Test that cleaning sorts data by date."""
        # Shuffle the data
        shuffled = sample_kline_data.sample(frac=1).reset_index(drop=True)
        
        cleaned = processor.clean_kline_data(shuffled)
        
        # Check if sorted
        assert cleaned['trade_date'].is_monotonic_increasing
    
    def test_clean_kline_data_empty_dataframe_raises_error(self, processor):
        """Test that cleaning an empty DataFrame raises ValueError."""
        with pytest.raises(ValueError, match="Input DataFrame is empty"):
            processor.clean_kline_data(pd.DataFrame())
    
    def test_normalize_kline_data_renames_columns(self, processor, raw_column_data):
        """Test that normalization renames columns to standard names."""
        normalized = processor.normalize_kline_data(raw_column_data)
        
        # Check that standard columns exist
        assert 'trade_date' in normalized.columns
        assert 'open_price' in normalized.columns
        assert 'high_price' in normalized.columns
        assert 'low_price' in normalized.columns
        assert 'close_price' in normalized.columns
        
        # Check that old columns don't exist
        assert '日期' not in normalized.columns
        assert '开盘' not in normalized.columns
    
    def test_normalize_kline_data_converts_types(self, processor, raw_column_data):
        """Test that normalization converts data types."""
        normalized = processor.normalize_kline_data(raw_column_data)
        
        # Check date type
        assert pd.api.types.is_datetime64_any_dtype(normalized['trade_date'])
        
        # Check numeric types
        assert pd.api.types.is_numeric_dtype(normalized['open_price'])
        assert pd.api.types.is_numeric_dtype(normalized['high_price'])
        assert pd.api.types.is_numeric_dtype(normalized['low_price'])
        assert pd.api.types.is_numeric_dtype(normalized['close_price'])
        assert pd.api.types.is_numeric_dtype(normalized['volume'])
        assert pd.api.types.is_numeric_dtype(normalized['amount'])
    
    def test_normalize_kline_data_validates_ohlc(self, processor):
        """Test that normalization validates OHLC relationships."""
        # Create data with invalid OHLC (high < low)
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = {
            'trade_date': dates,
            'open_price': [10.0] * 10,
            'high_price': [8.0] * 10,  # Invalid: should be >= open and close
            'low_price': [12.0] * 10,  # Invalid: should be <= open and close
            'close_price': [11.0] * 10,
        }
        df = pd.DataFrame(data)
        
        normalized = processor.normalize_kline_data(df)
        
        # Check that high >= low for all rows
        assert (normalized['high_price'] >= normalized['low_price']).all()
    
    def test_normalize_kline_data_ensures_non_negative_volume(self, processor):
        """Test that normalization ensures volume and amount are non-negative."""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = {
            'trade_date': dates,
            'open_price': [10.0] * 10,
            'high_price': [12.0] * 10,
            'low_price': [8.0] * 10,
            'close_price': [10.0] * 10,
            'volume': [-100, -200, 300, 400, 500, 600, 700, 800, 900, 1000],
            'amount': [-1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],
        }
        df = pd.DataFrame(data)
        
        normalized = processor.normalize_kline_data(df)
        
        # Check that all values are non-negative
        assert (normalized['volume'] >= 0).all()
        assert (normalized['amount'] >= 0).all()
    
    def test_normalize_kline_data_missing_required_columns_raises_error(self, processor):
        """Test that normalization with missing required columns raises ValueError."""
        data = {
            'trade_date': ['2024-01-01'],
            'open_price': [10.0],
            # Missing high_price, low_price, close_price
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            processor.normalize_kline_data(df)
    
    def test_calculate_time_range(self, processor, sample_kline_data):
        """Test time range calculation."""
        result = processor.calculate_time_range('600000', 'daily', sample_kline_data)
        
        assert result['code'] == '600000'
        assert result['period'] == 'daily'
        assert result['start_date'] is not None
        assert result['end_date'] is not None
        assert result['days_count'] == 100
        assert result['start_date'] < result['end_date']
    
    def test_calculate_time_range_empty_dataframe(self, processor):
        """Test time range calculation with empty DataFrame."""
        result = processor.calculate_time_range('600000', 'daily', None)
        
        assert result['code'] == '600000'
        assert result['period'] == 'daily'
        assert result['start_date'] is None
        assert result['end_date'] is None
        assert result['days_count'] == 0
    
    def test_validate_data_completeness_perfect_data(self, processor, sample_kline_data):
        """Test validation with perfect data."""
        report = processor.validate_data_completeness(sample_kline_data)
        
        assert report['is_valid'] is True
        assert report['completeness_score'] >= 95.0
        assert len(report['issues']) == 0
        assert report['total_rows'] == 100
    
    def test_validate_data_completeness_missing_values(self, processor, dirty_kline_data):
        """Test validation with missing values."""
        report = processor.validate_data_completeness(dirty_kline_data)
        
        assert report['completeness_score'] < 100.0
        assert len(report['missing_data']) > 0
        assert 'close_price' in report['missing_data'] or 'volume' in report['missing_data']
    
    def test_validate_data_completeness_with_expected_days(self, processor, sample_kline_data):
        """Test validation with expected days parameter."""
        report = processor.validate_data_completeness(sample_kline_data, expected_days=100)
        
        assert report['is_valid'] is True
    
    def test_validate_data_completeness_wrong_expected_days(self, processor, sample_kline_data):
        """Test validation with wrong expected days."""
        report = processor.validate_data_completeness(sample_kline_data, expected_days=150)
        
        assert report['completeness_score'] < 100.0
        assert any('mismatch' in issue.lower() for issue in report['issues'])
    
    def test_validate_data_completeness_empty_dataframe(self, processor):
        """Test validation with empty DataFrame."""
        report = processor.validate_data_completeness(pd.DataFrame())
        
        assert report['is_valid'] is False
        assert report['completeness_score'] == 0.0
        assert 'empty' in report['issues'][0].lower()
    
    def test_validate_data_completeness_invalid_ohlc(self, processor):
        """Test validation with invalid OHLC data."""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = {
            'trade_date': dates,
            'open_price': [10.0] * 10,
            'high_price': [8.0] * 10,  # Invalid: high < low
            'low_price': [12.0] * 10,  # Invalid: low > high
            'close_price': [10.0] * 10,
        }
        df = pd.DataFrame(data)
        
        report = processor.validate_data_completeness(df)
        
        assert report['completeness_score'] < 100.0
        assert any('ohlc' in issue.lower() or 'high < low' in issue.lower() for issue in report['issues'])
    
    def test_validate_data_completeness_zero_prices(self, processor):
        """Test validation with zero prices."""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = {
            'trade_date': dates,
            'open_price': [0.0] * 5 + [10.0] * 5,
            'high_price': [12.0] * 10,
            'low_price': [8.0] * 10,
            'close_price': [10.0] * 10,
        }
        df = pd.DataFrame(data)
        
        report = processor.validate_data_completeness(df)
        
        assert report['completeness_score'] < 100.0
        assert any('zero' in issue.lower() for issue in report['issues'])
    
    def test_validate_data_completeness_recommendations(self, processor, dirty_kline_data):
        """Test that validation provides recommendations."""
        report = processor.validate_data_completeness(dirty_kline_data)
        
        if not report['is_valid']:
            assert len(report['recommendations']) > 0
            assert all(isinstance(rec, str) for rec in report['recommendations'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])