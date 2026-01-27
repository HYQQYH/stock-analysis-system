"""Data processing service for cleaning, normalizing, and validating stock data."""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataProcessor:
    """Data processing utilities for stock market data."""
    
    # Standard column names for K-line data
    STANDARD_COLUMNS = [
        'trade_date',
        'open_price',
        'high_price',
        'low_price',
        'close_price',
        'volume',
        'amount'
    ]
    
    # Common column name mappings from different data sources
    COLUMN_MAPPINGS = {
        # Date columns
        '日期': 'trade_date',
        'date': 'trade_date',
        'Date': 'trade_date',
        
        # Open columns
        '开盘': 'open_price',
        'open': 'open_price',
        'Open': 'open_price',
        
        # High columns
        '最高': 'high_price',
        'high': 'high_price',
        'High': 'high_price',
        
        # Low columns
        '最低': 'low_price',
        'low': 'low_price',
        'Low': 'low_price',
        
        # Close columns
        '收盘': 'close_price',
        'close': 'close_price',
        'Close': 'close_price',
        
        # Volume columns
        '成交量': 'volume',
        'volume': 'volume',
        'Volume': 'volume',
        
        # Amount columns
        '成交额': 'amount',
        'amount': 'amount',
        'Amount': 'amount',
        
        # Percentage change
        '涨跌幅': 'percentage_change',
        'pct_chg': 'percentage_change',
        'change_pct': 'percentage_change',
        
        # Turnover
        '换手率': 'turnover',
        'turnover': 'turnover',
    }
    
    def __init__(self):
        """Initialize DataProcessor."""
        self.required_columns = ['trade_date', 'open_price', 'high_price', 'low_price', 'close_price']
        self.optional_columns = ['volume', 'amount', 'percentage_change', 'turnover']
    
    def clean_kline_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean K-line data by removing duplicates and handling missing values.
        
        Args:
            df: Raw K-line DataFrame from data source
            
        Returns:
            Cleaned DataFrame
            
        Raises:
            ValueError: If DataFrame is empty or required columns are missing
        """
        if df is None or len(df) == 0:
            raise ValueError("Input DataFrame is empty")
        
        logger.info("Cleaning K-line data: %d rows before cleaning", len(df))
        
        # Make a copy to avoid modifying original
        df_cleaned = df.copy()
        
        # Step 1: Remove duplicate rows based on all columns
        before_dedup = len(df_cleaned)
        df_cleaned = df_cleaned.drop_duplicates()
        duplicates_removed = before_dedup - len(df_cleaned)
        
        if duplicates_removed > 0:
            logger.info("Removed %d duplicate rows", duplicates_removed)
        
        # Step 2: Handle missing values in price columns
        price_columns = ['open_price', 'high_price', 'low_price', 'close_price']
        for col in price_columns:
            if col in df_cleaned.columns:
                # Forward fill for price data (use previous day's price)
                df_cleaned[col] = df_cleaned[col].ffill()
                # If still NaN, use backward fill
                df_cleaned[col] = df_cleaned[col].bfill()
                # If still NaN (all rows missing), fill with 0
                df_cleaned[col] = df_cleaned[col].fillna(0)
        
        # Step 3: Handle volume and amount columns
        numeric_columns = ['volume', 'amount', 'percentage_change', 'turnover']
        for col in numeric_columns:
            if col in df_cleaned.columns:
                # Fill missing numeric values with 0
                df_cleaned[col] = df_cleaned[col].fillna(0)
        
        # Step 4: Handle missing dates - if trade_date is missing, try to infer
        if 'trade_date' in df_cleaned.columns:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(df_cleaned['trade_date']):
                df_cleaned['trade_date'] = pd.to_datetime(df_cleaned['trade_date'], errors='coerce')
            
            # Remove rows with invalid dates
            before_date_clean = len(df_cleaned)
            df_cleaned = df_cleaned.dropna(subset=['trade_date'])
            dates_removed = before_date_clean - len(df_cleaned)
            
            if dates_removed > 0:
                logger.warning("Removed %d rows with invalid dates", dates_removed)
        
        # Step 5: Remove rows where all price columns are 0
        if all(col in df_cleaned.columns for col in price_columns):
            before_zero = len(df_cleaned)
            mask = (df_cleaned[price_columns] == 0).all(axis=1)
            df_cleaned = df_cleaned[~mask]
            zero_rows_removed = before_zero - len(df_cleaned)
            
            if zero_rows_removed > 0:
                logger.warning("Removed %d rows with all zero prices", zero_rows_removed)
        
        # Step 6: Sort by date
        if 'trade_date' in df_cleaned.columns:
            df_cleaned = df_cleaned.sort_values('trade_date').reset_index(drop=True)
        
        logger.info("Cleaning completed: %d rows after cleaning", len(df_cleaned))
        
        return df_cleaned
    
    def normalize_kline_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize data format and field names to standard format.
        
        Args:
            df: DataFrame with raw column names
            
        Returns:
            DataFrame with standardized column names and data types
            
        Raises:
            ValueError: If DataFrame cannot be normalized
        """
        if df is None or len(df) == 0:
            raise ValueError("Input DataFrame is empty")
        
        logger.info("Normalizing K-line data columns")
        
        df_normalized = df.copy()
        
        # Step 1: Rename columns to standard names
        rename_dict = {}
        for col in df_normalized.columns:
            # Direct mapping
            if col in self.COLUMN_MAPPINGS:
                rename_dict[col] = self.COLUMN_MAPPINGS[col]
            # Case-insensitive mapping
            else:
                col_lower = col.lower()
                for original, standard in self.COLUMN_MAPPINGS.items():
                    if col_lower == original.lower():
                        rename_dict[col] = standard
                        break
        
        if rename_dict:
            df_normalized = df_normalized.rename(columns=rename_dict)
            logger.debug("Renamed %d columns: %s", len(rename_dict), list(rename_dict.keys())[:5])
        
        # Step 2: Ensure required columns exist
        missing_required = [col for col in self.required_columns if col not in df_normalized.columns]
        if missing_required:
            raise ValueError(f"Missing required columns: {missing_required}")
        
        # Step 3: Standardize data types
        # Date column
        if 'trade_date' in df_normalized.columns:
            df_normalized['trade_date'] = pd.to_datetime(df_normalized['trade_date'], errors='coerce')
        
        # Numeric columns
        numeric_cols = ['open_price', 'high_price', 'low_price', 'close_price', 
                       'volume', 'amount', 'percentage_change', 'turnover']
        for col in numeric_cols:
            if col in df_normalized.columns:
                df_normalized[col] = pd.to_numeric(df_normalized[col], errors='coerce')
        
        # Step 4: Validate OHLC relationship (high >= open, high >= close, low <= open, low <= close)
        if all(col in df_normalized.columns for col in ['open_price', 'high_price', 'low_price', 'close_price']):
            # Correct OHLC inconsistencies
            df_normalized['high_price'] = df_normalized[['high_price', 'open_price', 'close_price']].max(axis=1)
            df_normalized['low_price'] = df_normalized[['low_price', 'open_price', 'close_price']].min(axis=1)
        
        # Step 5: Ensure volume and amount are non-negative
        if 'volume' in df_normalized.columns:
            df_normalized['volume'] = df_normalized['volume'].abs()
        if 'amount' in df_normalized.columns:
            df_normalized['amount'] = df_normalized['amount'].abs()
        
        logger.info("Normalization completed")
        
        return df_normalized
    
    def calculate_time_range(self, code: str, period: str, df: Optional[pd.DataFrame] = None) -> Dict[str, str]:
        """Calculate the time range of data for a stock.
        
        Args:
            code: Stock code
            period: K-line period (day, week, month)
            df: Optional DataFrame to analyze. If None, just returns empty range.
            
        Returns:
            Dictionary with 'start_date', 'end_date', 'days_count' keys
        """
        result = {
            'code': code,
            'period': period,
            'start_date': None,
            'end_date': None,
            'days_count': 0
        }
        
        if df is None or len(df) == 0:
            logger.warning("No data provided for time range calculation: %s (%s)", code, period)
            return result
        
        try:
            # Ensure trade_date column exists
            if 'trade_date' not in df.columns:
                logger.warning("trade_date column not found in DataFrame for %s", code)
                return result
            
            # Convert to datetime if needed
            dates = pd.to_datetime(df['trade_date'])
            
            # Calculate range
            start_date = dates.min()
            end_date = dates.max()
            days_count = len(dates)
            
            result.update({
                'start_date': start_date.strftime('%Y-%m-%d') if pd.notna(start_date) else None,
                'end_date': end_date.strftime('%Y-%m-%d') if pd.notna(end_date) else None,
                'days_count': days_count
            })
            
            logger.info("Time range for %s (%s): %s to %s (%d days)", 
                       code, period, result['start_date'], result['end_date'], days_count)
            
        except Exception as e:
            logger.error("Error calculating time range for %s: %s", code, e)
        
        return result
    
    def validate_data_completeness(self, df: pd.DataFrame, 
                                   expected_days: Optional[int] = None,
                                   allow_missing: bool = True) -> Dict:
        """Validate data completeness and generate a validation report.
        
        Args:
            df: DataFrame to validate
            expected_days: Expected number of trading days. If None, no check.
            allow_missing: Whether to allow missing values in optional columns
            
        Returns:
            Dictionary with validation results including:
            - is_valid: boolean indicating overall validity
            - completeness_score: percentage of data completeness (0-100)
            - missing_data: details about missing data
            - issues: list of validation issues found
            - recommendations: list of recommendations
        """
        report = {
            'is_valid': True,
            'completeness_score': 100.0,
            'missing_data': {},
            'issues': [],
            'recommendations': [],
            'total_rows': len(df) if df is not None else 0
        }
        
        if df is None or len(df) == 0:
            report['is_valid'] = False
            report['completeness_score'] = 0.0
            report['issues'].append("DataFrame is empty")
            report['recommendations'].append("Data source returned no data")
            return report
        
        try:
            # Check 1: Required columns presence
            missing_required = [col for col in self.required_columns if col not in df.columns]
            if missing_required:
                report['is_valid'] = False
                report['completeness_score'] -= 20.0
                report['issues'].append(f"Missing required columns: {missing_required}")
                report['recommendations'].append(f"Ensure data source provides: {missing_required}")
            
            # Check 2: Date column continuity (check for large gaps)
            if 'trade_date' in df.columns and len(df) > 1:
                dates = pd.to_datetime(df['trade_date']).sort_values()
                date_gaps = dates.diff().dt.days
                
                # Flag gaps larger than 7 days (more than a week)
                large_gaps = date_gaps[date_gaps > 7]
                if len(large_gaps) > 0:
                    report['issues'].append(f"Found {len(large_gaps)} large date gaps (>7 days)")
                    report['completeness_score'] -= min(10.0, len(large_gaps) * 2)
            
            # Check 3: Missing values in columns
            total_cells = len(df) * len(df.columns)
            missing_cells = df.isnull().sum().sum()
            
            if missing_cells > 0:
                missing_percent = (missing_cells / total_cells) * 100
                
                # Detail missing data by column
                for col in df.columns:
                    missing_count = df[col].isnull().sum()
                    if missing_count > 0:
                        report['missing_data'][col] = {
                            'count': int(missing_count),
                            'percentage': float((missing_count / len(df)) * 100)
                        }
                
                # Check if required columns have missing values
                for col in self.required_columns:
                    if col in df.columns and df[col].isnull().any():
                        if not allow_missing:
                            report['is_valid'] = False
                        report['issues'].append(f"Required column '{col}' has missing values")
                
                report['completeness_score'] -= missing_percent * 0.5
                report['recommendations'].append(f"Fill or impute missing values ({missing_percent:.1f}% missing)")
            
            # Check 4: Expected data count
            if expected_days is not None and len(df) != expected_days:
                diff = abs(len(df) - expected_days)
                report['issues'].append(f"Data count mismatch: expected {expected_days} days, got {len(df)}")
                report['completeness_score'] -= min(20.0, (diff / expected_days) * 100)
                report['recommendations'].append(f"Verify data retrieval returned expected {expected_days} records")
            
            # Check 5: Zero or negative prices
            if all(col in df.columns for col in ['open_price', 'high_price', 'low_price', 'close_price']):
                price_cols = ['open_price', 'high_price', 'low_price', 'close_price']
                for col in price_cols:
                    zero_count = (df[col] == 0).sum()
                    if zero_count > 0:
                        report['issues'].append(f"Column '{col}' has {zero_count} zero values")
                        report['completeness_score'] -= min(10.0, zero_count / len(df) * 100)
                
                negative_count = (df[price_cols] < 0).sum().sum()
                if negative_count > 0:
                    report['issues'].append(f"Price columns have {negative_count} negative values")
                    report['completeness_score'] -= min(15.0, negative_count / len(df) * 100)
                    report['recommendations'].append("Check data source for negative price anomalies")
            
            # Check 6: Inconsistent OHLC (high < low, etc.)
            if all(col in df.columns for col in ['open_price', 'high_price', 'low_price', 'close_price']):
                invalid_ohlc = (df['high_price'] < df['low_price']).sum()
                if invalid_ohlc > 0:
                    report['issues'].append(f"Found {invalid_ohlc} rows with invalid OHLC (high < low)")
                    report['completeness_score'] -= min(10.0, invalid_ohlc / len(df) * 100)
            
            # Ensure completeness score is between 0 and 100
            report['completeness_score'] = max(0.0, min(100.0, report['completeness_score']))
            
            # Final validity check
            if report['completeness_score'] < 70.0:
                report['is_valid'] = False
                report['recommendations'].append("Data completeness below 70%, consider re-fetching data")
            
        except Exception as e:
            logger.error("Error during data validation: %s", e)
            report['is_valid'] = False
            report['issues'].append(f"Validation error: {str(e)}")
        
        logger.info("Data validation completed: score=%.1f, valid=%s, issues=%d", 
                   report['completeness_score'], report['is_valid'], len(report['issues']))
        
        return report